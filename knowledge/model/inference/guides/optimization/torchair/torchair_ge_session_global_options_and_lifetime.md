---
type: Guide
title: GE全局选项与Session生命周期
description: 区分Python选项子集缓存、C++单例初始化与分层Finalize，解释配置修改和重新初始化的实际边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/session.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/hdc_channel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/hdc_channel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/npu_wrapper.cpp
  role: implementation
created_at: '2026-11-10T12:26:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE全局选项与Session生命周期

## 版本和证据范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的Python初始化辅助函数和C++ Session消费者。下述选项子集检查、设备缓存、Session初始化与分层Finalize行为在两版相同；不将主线新增调试接口或信号处理扩展到发布版。没有设备及多线程实验，平台范围未知，保持draft与空平台。

## 多个编译配置共享全局初始化状态

_try_get_global_init_compile_option首次把非空global_options对象直接记入_GLOBAL_COMPILE_OPTION；未提供或空字典则记为空字典。后续传None可以复用已记录选项；传字典时，每个键和值必须已经存在且相同，允许相同子集，不允许追加新键或修改值。检查的是global_compile_options，不是每张图的所有compile选项。

因此，先以空全局选项初始化，再试图为另一张图加入全局选项，会在Python辅助函数处报错。不能将这种失败归为第二张图的算子不支持。该缓存保留字典对象引用，没有防御性副本；调用方不应把原字典的后续修改视为受支持的Session热更新机制。

initialize_graph_engine随后构造独立options字典，加入ge.exec.deviceId、ge_run_with_torch_npu，再update全局算子编译配置。这一步的HF32和确定性字段覆盖同名用户全局字段。HF32字符串按conv、matmul顺序拼接；确定性布尔值和deterministicLevel来自当时Torch/TorchNPU状态。未加载torch_npu时，该辅助函数写allow_hf32=10、ge.deterministic=1和deterministicLevel=0；这是这条初始化分支的值，不是所有后端和算子的默认合同。

_get_device_id在首次取值后缓存设备号：已加载torch_npu时取current_device，否则取ASCEND_DEVICE_ID、默认0。之后更改当前设备或环境变量，不会令该辅助函数重新读取设备。这个进程内缓存不构成一套多设备Session切换接口。

## C++初始化不会重新应用后续选项

InitializeGraphEngine经NpuConcreteGraph::InitializeResource进入Session::GetInstance单例。Session::Initialize在锁外和锁内检查initialized_；已经初始化就返回已有status_，不比较或重放新options。因此，Python每次重新采集HF32/确定性字段，不等于C++ GE全局配置会随之改变；每图配置和运行期配置仍须沿各自消费者核对。

首次初始化把ge_run_with_torch_npu保存在本地标志，把ge_dump_with_acl_config交给ACL dump配置，其余选项交给GEInitialize。它要求设备ID，创建GE Session前补入ge.session_device_id，并在创建后调用aclrtSetDevice恢复指定设备。GetGeFunc用dlopen打开libge_runner.so并按dlsym结果判断FastLoadGraph/FastExecuteGraph能力；能力来自实际加载符号，不由本卡给出固定CANN支持矩阵。

initialized_也不是成功状态的充分证明：若GEInitialize失败、后续步骤仍走到函数尾部，status_保留错误但initialized_置True，后续Initialize/EnsureInitialized继续返回该错误。提前失败路径未必到达这个赋值。本卡只指出这条具体状态边界，没有执行故障注入，也不声称任意初始化错误都已自动回滚或重试。

## Finalize是Session级操作

Python finalize_graph_engine先torch._dynamo.reset，再调用C++ Finalize，随后卸载静态kernel。该函数没有清空_GLOBAL_COMPILE_OPTION或_cached_device_id。因此，Finalize之后再次调用初始化辅助函数，并不自动获得一组全新的Python全局选项与设备缓存。C++ Finalize也没有把status_重置为Success，不能把它当成已验证的初始化失败恢复配方。

Session尚未初始化时，C++ Finalize直接成功返回；已初始化时先尝试aclrtSynchronizeDevice，同步错误只记日志，然后结束dump、清initialized_、销毁全局GE Session、停止stdout通道并关闭libge_runner句柄。是否调用进程级ge::GEFinalize由ge_run_with_torch_npu决定：与TorchNPU共用时跳过GEFinalize，仍会销毁TorchAir自己的GE Session和句柄。若已初始化AOE，再执行其Finalize。它没有给每张图维护引用计数，不能把这一操作视为仅卸载一个模型。

定位跨模型配置冲突时，应先区分Python全局选项子集拒绝、C++已初始化复用、每图compile选项和运行期选项，再检查调用与Finalize顺序。性能评估也应把Session初始化/设备同步与稳态图执行分开；这里没有测量收益或承诺Finalize后显存全部归还驱动。

- [Python首次运行与编译时序](torchair_ge_runtime_binding_and_first_call.md)
- [C++图编译选项与编译成本](torchair_cpp_compile_options_and_summary.md)
- [外部分配器及图内存释放边界](torchair_ge_external_allocator_feature_memory.md)

## Evidence

- [主线初始化辅助函数](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py)：25–57、117–162。
- [发布初始化辅助函数](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py)：24–56、59–103。
- [主线Session](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp)：19–21、37–177；[发布Session](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp)：19–21、37–173。
- [主线Session成员与能力判断](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/session.h)：55–73、98–112；[资源桥接](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp)：186–192；[Python/C++入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp)：271–281。

## DeviceStdout通道：启动门槛、HDC worker与停止顺序

native GE的stdout通道由`hdc_channel.cpp`的`DeviceStdout`单例承载。启动面有两个：`Session::AddGraph`在EnsureInitialized后由IsGraphNeedLogChannel遍历待加图全部节点，任一节点type等于`PrintV2`才以`TNG_RETURN_IF_ERROR(StartStdoutChannel(device_index_))`启动，Start失败会中止本次AddGraph；另有Python绑定`InitDeviceStdoutChannel`（释放GIL后调用同一入口）作为主动启动面。停止面挂在Session::Finalize：销毁全局GE Session之后调用StopStdoutChannel(device_index_)，源码注释标记为所有图运行结束后停止。两个pin的该文件除空白格式外逐token相同，以下行为对两版一致。

### 单例绑定首个设备

GetInstance(device)是函数内static：首次调用的device成为进程唯一实例的设备，之后传入其它设备号不创建新实例，通道仍绑首设备。StopStdoutChannel(device)同样只按这个单例转发，参数设备不参与选择。

### Channel与接收循环

通道以acltdtCreateChannelWithCapacity(device, "_npu_log", 2)创建，容量2。worker线程先aclrtSetDevice(device_)（返回值被忽略）再进入循环，循环条件是atomic running_；每次acltdtReceiveTensor超时参数1000，任何失败、空指针或超时都返回空ChannelData，循环静默继续，不区分超时与错误、无退避。dataset所有权是RAII的：ChannelData析构调acltdtDestroyDataset，Move()转移指针后置空。打印只处理dtype为ACL_STRING且data非空、data_len非零的条目，以`std::cerr << ... << std::endl`输出——设备侧PrintV2文本最终落在宿主机stderr；其它dtype条目被静默丢弃。线程退出前aclrtResetDevice(device_)，返回值同样被忽略。

### Stop顺序与不可重用的running_

Stop先置running_=false，再销毁TDT通道（源码注释"tdt need destroy for relive block"：销毁通道本身被用作解除worker阻塞的手段），然后join worker、reset两个指针；析构函数再次调用Stop。Start的幂等检查是worker_!=nullptr，不校验running_状态；running_只在构造时初始化为true，Start不恢复。因此Stop之后再Start会通过空指针检查、创建新通道和新线程，但running_仍为false，新worker进入循环立即退出。以上均为静态读码观察：通道与数据集由本地RAII封装经acltdt*接口管理，未做运行期并发或TDT内部行为验证。

## 实现来源

- [主线hdc_channel](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/hdc_channel.cpp)（implementation）：1–195。
- [发布hdc_channel](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/hdc_channel.cpp)（implementation）：1–195；与主线除空白格式外逐token相同。
- [主线session调用区](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp)（implementation）：21–43、125–199。
- [发布session调用区](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp)（implementation）：122–196。
- [主线Python绑定入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp)（implementation，扩大范围）：284–295；绑定注册另见主线[核心pybind模块](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/npu_wrapper.cpp)（implementation）：28–41。
