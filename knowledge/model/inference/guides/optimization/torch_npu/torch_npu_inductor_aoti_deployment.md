---
type: Guide
title: 950DT AOTInductor部署：打包、Python与C++加载
description: 记录pt2产物、libtorch_npu依赖、动态形状和不叠加Catlass的边界；补两版C++运行时头表面与发布版外置内核执行链。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/aoti/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_package/model_package_loader.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_package/pybind.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/proxy_executor.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor_npu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor_npu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/interface.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/arrayref_tensor.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/scalar_to_tensor.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/utils.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/utils.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/aoti_runtime/interface.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/common.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/cpu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/npu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/cpp_wrapper/device_internal/npu.h
  role: implementation
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950DT AOTInductor部署：打包、Python与C++加载

## 固定契约与部署层次

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的AOTI内置特性页，仅列950DT，不扩大PR或发布基线。AOTInductor处理Export图并生成动态库等部署产物，可供Python/C++加载；和TorchAir导出AIR后ATC编译OM是不同路线。此处只静态审阅，没有导出、打包、编译、加载动态库或运行设备。

## 捕获、编译和加载顺序

先torch.export.export捕获，再torch._inductor.aoti_compile_and_package编译并打包，可用package_path指定model.pt2，省略时产物在系统临时目录。inductor_configs中的max_autotune=True是加大候选调优的样例，不保证总部署时间降低。来源允许在不同训练/推理平台间先export.save/load再目标侧AOT编译，不等于已编译二进制可跨任意环境迁移。

Python侧aoti_load_package返回可调用模型，再传NPU输入。样例以no_grad捕获MLP，输入(8,10)、batch Dim范围1..1024是该例约束，不是所有模型默认可用范围。来源宣称动态图、图下沉叠加、基础/融合/模板/手写算子及自定义解压路径能力，但未给所有组合和解压参数，不据能力条目自行补接口。

## C++运行环境与构建样例

C++使用AOTIModelPackageLoader取得runner，以PrivateUse1构造NPU Tensor并run；需要额外libtorch_npu.so，由build_libtorch_npu.py生成。CMake样例要求至少3.18、C++17，定位Torch/TorchNPU头和库、链接torch_npu及TORCH_LIBRARIES；libtorch_npu路径是占位符，必须与实际构建产物一致。该例通过Python导入查询安装目录，不是完全无Python构建环境的证明，C++运行与构建依赖分别核对。

示例先run一次再用system_clock包住第二次run，没有给设备同步计时协议；不能把打印秒数当作已同步的设备稳态耗时。结果保存、finalize及异常打印也只是示例收尾，不是本次执行记录。

## 明确的兼容限制

当前页明确暂不支持叠加Catlass、仅做功能兼容支持；不能把其他Inductor Catlass优化支持无条件套到AOTI。Cpp运行时动态形状分档的padding/split是另一层能力，受实际恢复语义约束，见[分档接口草稿](shape_handling.md)。

社区已弃用torch._export.aot_compile/aot_load不推荐使用；如使用，来源要求避免同进程多次调用。优先按该固定页的新打包/加载路线核对真实软件栈、输入约束和产物依赖，不从pt2生成成功推定实际加载、输出或性能已验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/aoti/overview.md)（primary）

## C++运行时头表面：两版布局差异

上文契约来自主线特性页；本节以两 pin 源码补齐 C++ 头表面。发布快照 f3ecfe4 在 torch_npu 仓内自带整套 AOTI C++ 运行时：`aoti_package/{model_package_loader,pybind}.h`（加载器与 pybind 声明）、`aoti_runner/model_container_runner.h`（基类，函数指针经 dlopen 符号解析）与 `model_container_runner_npu.{h,cpp}`、`aoti_runtime/{interface,arrayref_tensor,scalar_to_tensor,utils}.h` 等、`aoti_torch/{proxy_executor,oss_proxy_executor,oss_proxy_executor_npu,utils}` 头/源，另有 codegen 侧 `_inductor/codegen/aoti_runtime/interface.cpp`（342 行）。主线 ac0e1564 重构后 torch_npu 不再自带这套面：`aoti_package/` 仅剩 shape_handling，`aoti_runner/` 的运行时实现只保留 33/48 行的 `model_container_runner_npu.{h,cpp}` 薄子类（同目录另有 18/71 行的上游转发薄绑定 `pybind.{h,cpp}`：USE_NPU 下把 `AOTIModelContainerRunnerNpu` 与句柄转换助手绑进 `torch._C._aoti`，include 上游 `torch/csrc/inductor/aoti_runner`、`aoti_torch` 头；本文只说明目录边界，未展开其内部实现，不作为证据来源），其基类 `AOTIModelContainerRunner` 与 `OSSProxyExecutor` 都改用上游 torch 头（主线 `model_container_runner_npu.h:4-5` include `torch/csrc/inductor/aoti_runner/model_container_runner.h` 与 `torch/csrc/inductor/aoti_torch/oss_proxy_executor.h`）；model.so 侧改由 `aoti_include/{common,cpu,npu}.h` 汇总（common.h 组合上游 interface.h 与本仓 aoti_runtime/model.h 并提供 64 字节对齐的 `align()`；npu.h 经 `cpp_wrapper/device_internal/npu.h` 转发到本仓 `aoti_runtime/utils_npu.h` 与 `aoti_torch/generated/c_shim_npu.h`）。主线仓内 rg `OSSProxyExecutor|oss_proxy` 仅命中上述 include 行（find 证实无同名文件）。上文「C++使用AOTIModelPackageLoader」的加载器头只有发布快照在 torch_npu 仓内存在；两版头文件布局不能互相套用，主线对等实现位于上游 torch 源内，不在本卡范围。

## 发布版外置内核执行链：_npu.json→OSSProxyExecutorNpu→Dispatcher

发布版 `AOTIModelContainerRunnerNpu` 以外部后端名 "npu" 注册（`model_container_runner_npu.cpp:82`），`run_impl` 先调 `init_proxy_executor()`（:39-53，`init_flag_` 保证仅一次）：把 model.so 路径去扩展名后拼 `_npu.json`，文件存在才构造 `OSSProxyExecutorNpu(json, false)` 并把指针写入 `proxy_executor_handle_`，否则置 nullptr——外置（fallback/extern）节点执行器是可选伴随文件，不是每个 pt2 包必备。随后 `run_impl` 无条件用 `getCurrentNPUStream()` 覆盖传入的 stream_handle（:55-61）；`run_with_npu_stream` 的 `npu_stream` 形参未被使用，同样取当前流（:63-69）。主线版语义相反：仅当 stream_handle 为 nullptr 才回退当前流，`run_with_npu_stream` 尊重传入流（主线 `model_container_runner_npu.cpp:16-31`）。同名方法两版流语义不同，跨版本迁移部署代码时以各自源码核对。

`OSSProxyExecutorNpu`（481 行）构造时逐项解析 JSON nodes：target 按 `op.overload` 拆分（多于一个点号 TORCH_CHECK 报错）、`Dispatcher::findSchemaOrThrow` 取句柄；静态参数按 schema 类型核对序列化标签（Tensor→as_tensor、Int/SymInt→as_int/as_sym_int、Float/Bool/String/ScalarType/MemoryFormat/Layout 及 List/Optional 变体、as_none 空值；不匹配即 TORCH_CHECK）预填 IValue 栈，未出现且有默认值的参数按 schema 默认值补填（oss_proxy_executor_npu.cpp:12-273）。`call_function`（:376-479）把动态参数（Tensor/Int/ListTensor/ListInt/ListOptionalTensor）从展平数组回填后 `op.callBoxed(stack)` 执行，输出张量（含张量列表）按 schema 写回展平 tensor 数组。与通用 `OSSProxyExecutor`（489 行）raw diff：NPU 变体删除了调用前的两个计数 TORCH_CHECK（输入张量数、整数数），仅保留调用后 `tensor_id == num_tensors` 终检，被删检查使用的 `num_output_tensors` 变量随之闲置（:447）。非 CPU 时两变体都把 `device_` 构造为注释 "Mock a cuda device for now" 的 `c10::Device(CUDA, -1)`（oss_proxy_executor_npu.cpp:326-328），`as_device` 序列化参数与其不一致时仅 VLOG(1) 提示，栈上实际放 `*device_`；该替换对 NPU 算子分发的实际影响未在设备上验证。

## 运行接口契约要点

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `AOTInductorModelContainerCreate(handle, num_models, is_cpu, cubin_dir)` | 转发 `…CreateWithDevice`，设备串 is_cpu ? "cpu" : "npu"（interface.cpp:48-52） | `num_models==0` 在异常宏之外直接 stderr+FAILURE（:58-61）；本表全部来自发布快照 vendored interface.cpp |
| Run/RunSingleThreaded（:81-121） | 先以 `AOTI_VECTOR_SIZE_CHECK` 核对输入/输出数量与 `num_inputs()/num_outputs()` 一致（:92-93、:113-114，不符抛 `std::runtime_error`），再 `AOTINoGradGuard`（:37-45：构造时保存 prev_mode 并关闭 grad，析构还原；注释指明因 AOTInductor 用 at::addmm_out 不支持 requires_grad 参数）后调 run/run_single_threaded | 数量检查位于异常转换宏 `CONVERT_EXCEPTION_TO_ERROR_CODE`（:96、:117）之前：其抛出的异常不被该宏捕获转换；宏只覆盖宏体内（guard+run）的 C++ 异常，写 stderr 后返回 AOTI_RUNTIME_FAILURE，错误码不区分异常类型 |
| RunConstantFolding（:219-229） | 形参只有 container_handle/use_inactive/stream_handle/proxy_executor_handle，没有输入/输出数量参数，也无对应检查；`AOTINoGradGuard` 后调 `run_const_fold` | 同样只有宏体异常经宏转换；输入/输出数量检查路径仅存在于 Run/RunSingleThreaded |
| `AOTInductorModelCreate`（:275-298） | device_str 硬编码 "cpu"（注释：仅用于 CPU 模型）；constant_map_handle 非空逐项 emplace，否则 `load_constants()` | 单模型 run 不含并发/队列/设备管理（interface.h:151-154 注释）；并发 `UpdateConstantsMap` 的顺序由调用方负责（interface.h:165-167 注释） |
| 常量缓冲族（:123-235） | Update/UpdateUserManaged/UpdateInactive/FreeInactive/Swap/ExtractConstantsMap；`use_inactive` 双缓冲语义在 C ABI 与 Runner 类两面对齐（interface.h:101-133、model_container_runner.h:31-42） | user_managed 不接管所有权；validate_full_update 只检查更新覆盖完整性（interface.h:112-117 注释），不是数值校验 |
| model.so ABI 层（aoti_runtime/utils.h、interface.h、arrayref_tensor.h） | 头注释禁止引 aten/c10 头、仅稳定 C ABI shim.h（utils.h:10-13、interface.h:4-7 同款警告）；`RAIIAtenTensorHandle` 偷所有权，`MaybeOwningAtenTensorHandle(user_managed=true)` 经 `aoti_torch_new_tensor_handle` 不偷（utils.h:56-243）；`MiniArrayRef`/`ArrayRefTensor` 带 ABI static_assert（arrayref_tensor.h:134-135、:220-222） | interface.h:29-33 的 device_str 文档注释在固定源码中断句于 "returned by"，保持原文现状不补写语义；ArrayRefTensor 的 `release()` 即 `expensiveCopyToTensor()` 拷贝分配（arrayref_tensor.h:177-179） |
| 宿主侧 aoti_torch/utils.h 与 scalar_to_tensor.h | `resolve_tensor_dispatch_flags` 对 conj/neg 张量先 clone 再进 C-shim（:39-50，注释：直调 native 函数会静默算错）；`assert_inf_and_nan`（:94-104）；异常转错误码走 LOG(ERROR)（:15-25）；scalar_to_tensor 泛型模板直接抛 Unsupported，仅 13 个标量 dtype 特化（scalar_to_tensor.h:8-35） | 宿主进程工具头，不进 model.so ABI 面；`AOTI_RUNTIME_SUCCESS=0`/`FAILURE=1` 整数错误码（aoti_runtime/utils.h:36-38） |

以上全部为两 pin 源码静态直读，未构建、加载或运行任何 pt2 产物；报错路径与流语义未在设备上触发验证。

## 补充来源

- [增补固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_package/model_package_loader.h)（primary，全文 1–40，末行无换行）
- [增补固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_package/pybind.h)（primary，全文 1–7）
- [增补固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner.h)（primary，全文 1–101）
- [增补固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.h)（primary，全文 1–36）
- [增补固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.cpp)（primary，全文 1–85）
- [增补固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/proxy_executor.h)（primary，全文 1–18）
- [增补固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor.h)（primary，全文 1–92）
- [增补固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor.cpp)（primary，全文 1–489）
- [增补固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor_npu.h)（primary，全文 1–37）
- [增补固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/oss_proxy_executor_npu.cpp)（primary，全文 1–481，并与来源 9 做整文件 raw diff）
- [增补固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/interface.h)（primary，全文 1–178）
- [增补固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/arrayref_tensor.h)（primary，全文 1–284）
- [增补固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/scalar_to_tensor.h)（primary，全文 1–37）
- [增补固定来源 15](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_runtime/utils.h)（primary，全文 1–338）
- [增补固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/aoti_torch/utils.h)（primary，全文 1–207）
- [增补固定来源 17](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/aoti_runtime/interface.cpp)（primary，全文 1–342）
- [增补固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/common.h)（primary，全文 1–18）
- [增补固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/cpu.h)（primary，全文 1–4）
- [增补固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_include/npu.h)（primary，全文 1–4）
- [增补固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.h)（primary，全文 1–33）
- [增补固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runner/model_container_runner_npu.cpp)（primary，全文 1–48）
- [增补固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/cpp_wrapper/device_internal/npu.h)（implementation，全文 1–4）
