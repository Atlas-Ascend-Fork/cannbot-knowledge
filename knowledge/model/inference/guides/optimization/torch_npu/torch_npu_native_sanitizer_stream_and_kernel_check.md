---
type: Guide
title: NPU Sanitizer：TORCH_NPU_SANITIZER 双模式流/算子检查与边界
description: 记录 stream 模式数据竞争与 record_stream 缺失检测、kernel 模式 ACL 栈回溯的启用门槛、回调链、两版差异与成本，不把无报错当流语义正确的证明。
tags:
- task.debugging
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_sanitizer.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_stream_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_kernel_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_npu_trace.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/optional_features.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/PyCallbackTrigger.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/PyCallbackTrigger.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/NPUTrace.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/NPUTrace.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_sanitizer.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_sanitizer_record_stream.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_sanitizer.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_stream_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_kernel_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_npu_trace.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/PyCallbackTrigger.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/PyCallbackTrigger.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/NPUTrace.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/NPUTrace.cpp
  role: implementation
created_at: '2026-11-12T04:15:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPU Sanitizer：TORCH_NPU_SANITIZER 双模式流/算子检查与边界

## 固定版本与证据范围

主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的两版实现结构差异较大，本卡分开描述，不宣称两版行为一致。来源只有源码与仓内测试，没有产品矩阵，draft、platforms为空；本次为静态阅读，未运行任何测试、未创建设备Tensor或进程组，无新增verified。

## 启用门槛与模式选择

`TORCH_NPU_SANITIZER`只要出现在环境变量（不校验取值）即触发import时启用：主线经`torch_npu/_init/core/optional_features.py`的`_enable_sanitizer_if_needed`，发布在`torch_npu/__init__.py`末尾同条件调用`enable_npu_sanitizer()`。因此环境变量必须在`import torch_npu`之前设置；`ASCEND_OPP_DEBUG_PATH`同样在模块构造时读取。

模式由`ASCEND_OPP_DEBUG_PATH`取值是否非空（truthiness）决定：非空进入KERNEL模式，未设置或空字符串进入STREAM模式——只设置该键但取值为空不会进入KERNEL。KERNEL模式还要求`KernelPathManager`构造后`cwd/opp_debug_path`存在且`enable_kernel_check`成功（边界见下节），否则返回False、整个sanitizer不激活（`_activate_npu_trace`不执行），**不会自动降级回STREAM模式**；两版enable路径同构（`_kernel_check.py`两版逐字节一致）。主线`_sanitizer.py`保留了`check_record_stream`（取值`'1'`才为True）字段，但当前主线代码没有消费者，不据此推断取值门槛。

## KERNEL模式：OPP调试目录与ACL栈回溯

`KernelPathManager`在构造时先以`flock(opp_debug.lock, LOCK_EX|LOCK_NB)`串行化执行构建：源`ASCEND_OPP_PATH`、`ASCEND_OPP_DEBUG_PATH`或其kernel目录缺失时只记日志并跳过，拿不到锁只告警并跳过；随后**无条件**设置`ASCEND_LAUNCH_BLOCKING=1`（同步执行，使finish回调能带回当次栈）并把进程`ASCEND_OPP_PATH`改写到`cwd/opp_debug_path`。构建成功时把OPP整树拷贝到`cwd/opp_debug_path`（权限0o750），并将其中`built-in/op_impl/ai_core/tbe/kernel`替换为指向`ASCEND_OPP_DEBUG_PATH`下同名kernel目录的符号链接；`atexit`注册的`clear_debug_env`在锁内删除调试目录，解锁后再删除锁文件，但不恢复原环境变量取值。ACL start/finish执行回调打印`[sanitizer](pid)`前缀的算子名，finish时输出反向整理后的Python调用栈。

成本与失效边界：依赖真实OPP与调试kernel目录存在且可写，整树拷贝有磁盘成本；`ASCEND_LAUNCH_BLOCKING=1`使算子串行执行，性能影响显著；它只回溯Python侧调用栈，不dump算子内部状态，也不检测设备端内存越界。目录缺失或拿不到锁时构建被跳过，但环境变量改动已经发生且不回退——即使enable最终返回False（sanitizer未激活），进程的`ASCEND_LAUNCH_BLOCKING`/`ASCEND_OPP_PATH`已被改写；`enable_kernel_check`在构造后只检查`opp_debug_path`存在，不能证明是本次调用构建的（目录预先存在时跳过构建也能通过），而锁文件创建失败等超出捕获范围的构造异常会向上传播，不是所有构建失败都安静返回False。

## STREAM模式：数据竞争与record_stream两条检测线

STREAM模式复用`torch.cuda._sanitizer`的EventHandler协议，通过`TorchDispatchMode`拦截全部aten调度；参数解析只统计NPU Tensor，factory（`new_*`/`*_like`）与仅别名读的参数视为metadata-only不计真实访问，读写/输出按`data_ptr()`记录，另收集`untyped_storage().data_ptr()`。检测分两条线：

- **数据竞争**：dispatch模式先执行func、再检查该次访问，发现错误打印后抛`CUDASanitizerErrors`——错误是launch之后的事后诊断，不阻止该次执行。
- **record_stream缺失**：推迟到Tensor释放或手动`flush_record_stream_warnings()`时判定，避免“launch后先同步再释放”的正确模式被误报。判定规则：某跨流使用流未被`record_stream`记录，且创建流对该流同步水位低于使用发生时的seq_num（用`>= usage_seq_num`区分真实同步与流创建继承的初始状态），报`MissingRecordStreamError`，含分配栈、使用算子与使用栈、已记录流集合。因此**反向等待只覆盖此前的使用**；修复方向是`tensor.record_stream(stream)`或释放前创建流`wait_stream`/`wait_event`，设备级`synchronize()`覆盖所有方向。

`record_stream`/`eraseStream`不在Python层解析，而由C++分配器链路回调（`NPUCachingAllocator`的malloc/free/recordStream/eraseStream/eraseStreamWithBlockPtr、事件与同步点，及pluggable allocator同型打点），以storage data_ptr为键，view与本体互认；通信work释放流后eraseStream移除对应记录。测试守卫以源码字符串断言这些打点存在，包括`MULTI_STREAM_MEMORY_REUSE=3`的块指针擦除路径。

## 测试矩阵与已知缺口

`test_sanitizer_record_stream.py`给出两轴矩阵：无同步→竞争且需record_stream；仅usage.wait(creation)→无竞争但仍需record_stream；仅creation.wait(usage)→可能有竞争但不需要record_stream；双向同步或设备同步→两者都免；record_stream→竞争线不豁免但record_stream线免。测试另覆盖view/slice按storage归并、重分配不继承旧记录、释放时错误留存于`record_stream_errors`。csrc为外部事件write/wait预留了两个回调槽位，但仓内无触发点，且其引用的Python注册表名与`_npu_trace.py`实际命名不一致（若被触发只会记ERROR日志）；不把预留槽当已生效能力。上述测试本次均未运行。

## 发布版差异

发布STREAM模式直接使用`torch.cuda._sanitizer.EventHandler`，**只有数据竞争检测，没有record_stream追踪**；`enable_npu_sanitizer`先执行`apply_sanitizer_patch()`（`torch.Tensor.is_cuda ← is_npu`，主线已删除该patch）；dispatch模式对`adaptive_avg_pool2d/batch_norm/log_softmax/nll_loss/to`额外打开AutogradFunctionality dispatch key（主线改为metadata-only与storage级处理，不再需要该清单）。C++侧发布把CONCRETE_TRACE_NPU宏内联在头文件，主线拆到.cpp并引入`NPUTraceCallbacks`函数表，新增record/erase stream回调并让`__del__`容错。native trace初始化经C++`call_once`进程级一次；该幂等只属于native层——Python`enable()`先执行stream/kernel setup（进入dispatch模式、注册全部回调）之后才检查`self.enabled`，重复enable会重复执行Python侧setup。

## 成本与适用边界

TorchDispatchMode使每个算子多一轮Python往返，C++触发点每次获取GIL并`import torch_npu.utils._npu_trace`，开销显著，仅用于调试。覆盖面限于Python dispatch可见的aten操作与C++打点事件：dispatch模式对图捕获**不做排除**——捕获期从Python发起、仍经dispatch的aten操作对模式可见；不可见的是图回放、已降算子的执行与不经dispatch、无C++打点的自定义C++内部访问。它不是设备端memcheck类工具。多解释器场景`setTrace`只注册第一个。运行“无报错”不证明流语义正确，只证明未检测到上述两类模式。

- [record_stream 擦除接口](../../../apis/torch_npu/erase_stream.md)
- [分配器流回收与释放顺序](torch_npu_native_stream_queue_drain_and_synchronization.md)
- [自定义分配器与 IPC](torch_npu_custom_allocator_and_ipc.md)
- [TorchAir 多流死锁检测（图级另一工具）](torchair_multistream_deadlock_check.md)
- [HCCL 飞行记录器（另一诊断面）](../../../../training/guides/torch_npu_flight_recorder_analysis.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_sanitizer.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_stream_check.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_kernel_check.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_npu_trace.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/optional_features.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/PyCallbackTrigger.h)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/PyCallbackTrigger.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/NPUTrace.h)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/sanitizer/NPUTrace.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_sanitizer.py)（example）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_sanitizer_record_stream.py)（example）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation，定向阅读触发点）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_sanitizer.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_stream_check.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_kernel_check.py)（implementation，与主线逐字节一致）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_npu_trace.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，定向阅读启用段）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/PyCallbackTrigger.h)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/PyCallbackTrigger.cpp)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/NPUTrace.h)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/sanitizer/NPUTrace.cpp)（implementation）
