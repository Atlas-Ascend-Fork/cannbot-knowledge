---
type: Guide
title: Inductor 原生 C++ 启动与运行时基座：static launcher 装载发射、fast launch 计划、cxx20 builder 改写与 AOTI model_base
description: 记录主线独有的 static_launcher C++ 运行时（ABI 装包、二进制装载、双发射体、故意不卸载）、_FastNpuLauncher vectorcall、python_wrapper_fast_launch 计划体与发射器、triton_compat 的 C++17→C++20 builder 改写链及 aoti_runtime model_base.h 的 USE_NPU 条件基座。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/runtime.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/runtime.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/bindings.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/fast_launcher.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/csrc/bindings.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/wrapper_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_compat.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runtime/model_base.h
  role: implementation
created_at: '2026-11-12T14:26:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor 原生 C++ 启动与运行时基座：static launcher 装载发射、fast launch 计划、cxx20 builder 改写与 AOTI model_base

## 固定版本与范围

主线 pin（ac0e1564）独有：发布 pin（f3ecfe4a）无 `csrc/inductor/static_launcher/` 目录、无 `_inductor/experimental/python_wrapper_fast_launch/csrc/`、无 `_inductor/triton_compat.py`、无 `csrc/inductor/aoti_runtime/model_base.h`（发布侧为 `aoti_runtime/model.h`，两版布局不可互套）。Python 契约面已由 [静态启动契约卡](torch_npu_experimental_triton_static_launch_contract.md)与 [Planned Fast Launch 卡](torch_npu_inductor_planned_fast_launch.md)覆盖（该契约卡明确「C++ 启动器仍独立」），fast_launch 补丁边界与装饰器发射归[装饰器发射消费卡](torch_npu_main_inductor_decorator_emission_consumers.md)，cpp_wrapper 消费面归[主线 cpp wrapper 发射卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)；本卡覆盖其下的 C++ 层：static_launcher 五文件（runtime.cpp 560 行全文）、python_wrapper_fast_launch 的 bindings.cpp 607 行全文与 wrapper_codegen.py 55 行全文、triton_compat.py 76 行全文、model_base.h 的 USE_NPU 条件段。全部 TU 以 `#ifndef BUILD_LIBTORCH` 包裹（libtorch 构建整体排除）。纯静态阅读：未编译、未加载二进制、未发射任何 kernel、未运行 AOTI 模型；draft、platforms 为空。

## static launcher 的 ABI 装包（BuildPackedLayout）

`StaticNpuKernel::BuildPackedLayout`（runtime.cpp :362-414）把 host 参数编进一块字节缓冲，顺序镜像 Triton-Ascend `driver.py` 生成的 packed struct（注释 :73-79 指 3.2.2 `generate_npu_wrapper_src()` 与 3.6.0 `make_launcher()`）：可选 ffts 指针槽在最前（`targetSupportFfts_`），非 pure SIMT 内核固定保留 `sync_lock*` + `workspace*` 两个指针槽（3.6.0 的 pure SIMT 由尾部 trailing pointers 表达），随后是按 `argKinds` 解析的运行时参数（`ParseArgKind` :32-71 支持 tensor/i8-i64/u8-u64/f32/f64/bool 十二类），再是 `gridX/Y/Z` 三个 int32，最后 `trailingPointerCount`（Load 门槛 ≤3，对应 3.6.0 pure SIMT 的 global_scratch/profile_scratch/DTData 指针）。尺寸用 C++ `sizeof`，指针与 64 位标量对齐 8，其余标量一律对齐 4（含 i8/i16，`ArgAlignment` :110-122 注释原义）；整块缓冲长度再对齐到最大成员对齐值。

## 装载门槛与二进制生命周期

`IsSupported`（:278-280）只探测 `IsExistAclrtLaunchKernelWithHostArgs`。`Load`（:282-353）门槛：支持性、kernel 名非空、`mixMode` 仅 `aiv`/`aic`（分别映射 `ACL_RT_BINARY_MAGIC_ELF_VECTOR_CORE`/`AICORE`）、`sharedMemDynamicSize` ≤ uint32 max、`isPureSimt` 要求 `enableSimt`、trailing ≤3；随后 `NPUGuard` + `aclrtGetCurrentContext`，`aclrtBinaryLoadFromData`（`LAZY_LOAD=0`，显式 magic）→ `aclrtBinaryGetFunction`，任一步失败回滚 `AclrtBinaryUnLoad`；`targetSupportFfts` 再取 `AclrtGetHardwareSyncAddr` 存 `fftsAddress_`，失败同样回滚。`Close`（:504-556）**有意不卸载**：`constexpr bool enableBinaryUnload = false`（:518），注释引 CANN 9.0.0/9.2.0-beta.2 卸载后设备地址复用会执行旧 kernel 代码的缺陷（gitcode.com/cann/runtime/issues/1021），以保留内存为代价把注册/设备代码留到运行时 teardown；若未来启用卸载，路径为 NPUGuard + 上下文切换/恢复，且不做设备级同步（注释：社区 static launcher 的基准同步发生在 autotune 落选者释放之前，被选 launcher 的持有者保持二进制加载）。析构函数吞掉一切异常调 Close（:355-360）。

## 双发射体与入队

`Launch`（:416-434）走 `py::sequence` + `WriteArgument`（:130-173：tensor 参数接受 None→nullptr、PyLong→`PyLong_AsVoidPtr`、其余 `py::cast<at::Tensor>().data_ptr()`；标量走 `py::cast<T>` 写入）。`LaunchFast`（:436-449）走 CPython 底层 `PyObject* const* args` + `WriteFastArgument`（:225-274）：整型走 `PyLong_AsLongLong/AsUnsignedLongLong` 快路径并做目标类型范围校验（越界 `TORCH_CHECK` 失败），非内置数值回退 `py::cast`；浮点走 `PyFloat_AS_DOUBLE` 快路径；tensor 强制 `THPVariable_Check` 且 defined；bool 识别 `Py_True`。公共部分 `LaunchImpl`（:456-502）：`ValidateGrid`（:175-187，三维必须为正、≤ int32 max、乘积 ≤ uint32 max）；打包缓冲零初始化，先写 ffts 地址再写参数和 grid；互斥锁内检查 `closed_` 并 `shared_from_this()` 捕获自持引用，lambda 里按 `enableSimt_` 组 `ACL_RT_LAUNCH_KERNEL_ATTR_DYN_UBUF_SIZE=sharedMemDynamicSize_` 的 launch attr，调 `AclrtLaunchKernelWithHostArgs(functionHandle, blockCount, stream, cfg, packed.data(), packed.size(), nullptr, 0)`，整段经 `OpCommand::RunOpApiV2(kernelName_, launchCall)` 入队。

## _FastNpuLauncher 与绑定面

`fast_launcher.cpp` 定义独立 PyTypeObject `torch_npu._C._FastNpuLauncher`（:94-116，`Py_TPFLAGS_HAVE_VECTORCALL` + `tp_vectorcall_offset`）：`FastNew`（:62-86）只接受一个位置参数（loaded kernel），`pybind11::cast` 出 `shared_ptr<StaticNpuKernel>` 后 `CheckOpen`，把 kernel 与 `nargs` 存进裸 `FastLauncherState*`（tp_alloc 不构造 C++ 成员）；`FastCall`（:36-60）拒绝 kwargs，实参数必须等于 `state->nargs+4`，前 4 个参数为 grid×3+stream 全部走 `PyLong_AsUnsignedLongLong`；`FastDealloc` 删除 state。`bindings.cpp`（:22-65）注册 `_NPUStaticLoadedKernel` 类与 `_StaticNpuLauncher` 四个静态方法 `_is_supported`/`_load_kernel`（十参数）/`_launch_kernel`/`_unload_kernel`，再级联注册 fast launcher；两处注册由 `InitNpuBindings.cpp:269-270` 统一挂进 `torch_npu._C`。Python 消费点：`triton_experimental/static_launcher/compile_result.py:63`、`kernel.py:94`、`fast_launcher.py:21-30`（Python 契约见契约卡）。

## Planned Fast Launch 的 C++ 计划体

`python_wrapper_fast_launch/csrc/bindings.cpp` 自带一套 `TORCH_NPU_REGISTER_LIBRARY(libascendcl)` + `aclrtLaunchKernelWithHostArgs` 符号解析（:29-52，注释：不依赖其他 ACL 接口文件的初始化顺序；static 缓存查到与查不到两种结果，计划请求时才解析、稳态路径无锁）。`MakeFastLaunchPlan`（:467-550）把拒绝前置：runtime 无该 API 直接 `TORCH_CHECK` 失败（Python 侧负缓存并继续用原 Triton launcher，见 planned 卡）；`runtime_arg_count` 哨兵 `SIZE_MAX` 表示全部参数运行期给；`fixed_args` 必须恰好补齐 ABI 缺口且**固定 tensor 参数不支持**（:528-531）；`static_grid` 非空时须为 3 元并预校验、预写入模板与 `staticBlockNum`。计划 ABI 与 static launcher 同构（`BuildPackedLayout` :234-272：ffts 槽、非 pure SIMT 的 sync-lock/workspace 两槽、参数、grid 3×i32、尾部对齐），差别：ffts 地址来自 `rtGetC2cCtrlAddr`（:509-521）而非 `AclrtGetHardwareSyncAddr`；grid 乘积上限是 **uint16 max**（`ValidateGrid` :341-356）而非 static launcher 的 uint32 max——同代两发射体对 grid 规模的上限不对称。`kernelStub` 经 `ExtractPointer`（:311-333）接受 PyCapsule、整数地址或带 `value` 属性对象，`kernelStubOwner` 持有 Python 对象保活。`PackLaunch`/`PackStaticLaunch`（:378-430）从 `packedArgsTemplate` 出发只覆写运行期参数与 grid；`SubmitLaunch`（:432-465）注释明确复用既有 `OpCommand::RunOpApiV2` 队列入口而非每次新建零 IO OpCommand。绑定四个入口：`_NPUInductorFastLaunchPlan`（dynamic_attr）、`_npu_inductor_make_fast_launch_plan`（带全部默认参）、`_npu_inductor_fast_launch_with_plan`、`_npu_inductor_fast_launch_static_with_plan`（:573-605）；Python 消费 `python_wrapper_fast_launch/backend.py:337-345`（getattr 探测，缺失归入 `planned_backend_unavailable` 负缓存）。

## 发射器 wrapper_codegen.py

`FastLaunchWrapperEmitter.emit_triton_call`（:15-52）对每个 callsite 发射：头部 `_npu_fast_launch_metadata_{i} = {metadata!r}` 与可变槽 `_npu_fast_launch_call_{i} = [None]`，正文先取槽内函数，为 None 时 `bind_python_wrapper_kernel_fast(metadata, kernel_name, call_slot=...)` 绑定并回填槽（首调用惰性绑定、后续直接命中），最后以 `call(args..., stream=stream)` 调用。`graph_id` 取 `V.graph.graph_id` → `V.graph.name` → `"graph"` 三级回退（:27-31）。import 注入的门槛（非 cpp_wrapper 且非 compile-time autotune）在 patch.py `write_triton_header_once` 包装内（:59-69），归[装饰器发射消费卡](torch_npu_main_inductor_decorator_emission_consumers.md)，本卡不重复。

## triton_compat 的 cxx20 builder 改写链

`patch_triton_extension_cxx_standard`（triton_compat.py :52-76）：`TorchVersion(torch.__version__) < "2.13"` 直接返回；import `triton.backends.ascend` 的 `driver`/`utils` 失败静默返回；patch 三个命名空间——`vars(utils)`、`vars(driver)`、以及 `backends.get("ascend").driver.__init__.__globals__`（注释 :62-65：Triton 3.2 用 `spec_from_file_location` 发现驱动且不进 `sys.modules`，注册类用的是与常规 import 不同的 globals dict，必须单独 patch，且不初始化惰性运行时驱动/NPU 上下文）。目标函数 `_build_npu_ext`/`_precompile_npu_ext` 包上 `_with_cxx20`（:29-49）：`functools.wraps` 外层按 `signature.bind+apply_defaults` 判断 `kernel_launcher != "torch"` 时走原函数（只改 torch launcher 路径），已标记 `_torch_npu_cxx20` 的跳过（幂等）；被替换执行体用 `types.FunctionType` 克隆**仅该函数自己的 globals**并把 `subprocess` 换成 `_Cxx20Subprocess`（:11-26：`run` 收到 list/tuple argv 时克隆命令并把 `-std=c++17`/`-std=gnu++17` 改写为 `-std=c++20`，不动调用方命令、保留更新的标准）。消费链在 `_inductor/__init__.py`：`_apply_common_patches`（`run_once`，:48-52）调用 patch，四个 backend loader 入口（:126/:143/:180/:411）都会触发；紧随其后的 `_warm_triton_npu_utils_cache`（:64-83）docstring 给出动机：Inductor 编译 sidecar 是独立进程（`TORCH_DEVICE_BACKEND_AUTOLOAD=0`），monkey-patch 够不到，只能提前把 C++20 编好的 `npu_utils.so` 落进 Triton 盘上缓存让 sidecar 命中；否则 sidecar 会用 triton-ascend 硬编码的 `-std=c++17` 编译，对 torch ≥ 2.15 的 C++20-only ATen 头编译失败，之后每次编译都报 "Attempting to use a closed pool"。

## AOTI model_base.h 的 USE_NPU 基座

`model_base.h`（1064 行）是 `AOTInductorModelBase` CRTP 基类（`aoti_runtime/model.h` 只是 include 它并声明生成子类，AOTI 部署面见 [AOTI 部署卡](torch_npu_inductor_aoti_deployment.md)）。USE_NPU 条件段要点：`AOTI_CONST_ALIGNMENT` 64（:301-305）；`AOTI_LOG_LOADING` 宏按 `AOTI_LOG_LOADING` 环境变量打 `[AOTI_LOAD]` 标记（:317-326，S646785 注释：免重编译可 grep）；`RAII_npuMalloc`（:333-352）双路——定义 `AOT_INDUCTOR_USE_CACHING_ALLOCATOR` 时走 `aoti_torch_npu_caching_allocator_raw_alloc/raw_delete`，否则 `aclrtMalloc`（0 字节补 32 字节 padding，注释：aclrtMalloc 不支持 0 字节）+ `ACL_MEM_MALLOC_HUGE_FIRST`。`parse_device_str`（:403-445）接受 `cpu`/`npu`[:idx]，非数字 idx 抛错。构造器（:455-477）：device_idx 为 -1 时 `aclrtSetDevice(0)+aclrtGetDevice` 兜底，析构（:480-489）销毁事件。`run`（:510-537）：`normalize_run_stream` 把 null stream 换成 `aoti_torch_get_current_npu_stream`（:497-505）；首次调用建 `aclrtEvent`，`run_impl` 后 `aclrtRecordEvent`——CPU 版用 bool `run_finished_`，NPU 版是 `std::optional<aclrtEvent>`（:1046-1050），`is_finished`（:925-940）用 `aclrtQueryEventStatus` 且事件未初始化时抛 `"Model NPU event was not initialized"`；`wait_for_completion()` 为空（:944）。`load_constants`（:599-713）：双 blob——主 blob 走 NPU 分配，混合设备常量只允许次设备为 CPU（:649-663 的 TORCH 检查给出 "compiled on GPU but loading on CPU" 提示），H2D 用 `aclrtMemcpy`（`constant_ptr` :741-768），张量句柄经 `aoti_torch_create_tensor_from_blob_npu_v2`（:698-710）。

## 失效边界

- 全部为固定提交静态结论：未验证 `aclrtBinaryLoadFromData` 各 magic 组合、未实测 fast/普通两发射体性能差、未运行 AOTI 模型；`enableBinaryUnload=false` 依据注释引用的外部 issue，本仓未复现该缺陷。
- grid 上限不对称（uint16 max vs uint32 max）与 ffts 地址来源差异（`rtGetC2cCtrlAddr` vs `AclrtGetHardwareSyncAddr`）是两代发射体的源码事实，不推导 CANN 侧语义。
- model_base.h 仅记录 USE_NPU 条件段；`run_const_fold`/pinned staging pool 等与上游共享的段不在本卡范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/runtime.cpp)（primary）：:22-122（ABI 尺寸/对齐）、:130-187、:189-274、:278-360、:362-414、:416-454、:456-502、:504-556（:514-518 卸载关闭与 issue 注释）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/runtime.h)（implementation）：:19-37（枚举与布局结构）、:39-64（类与公共面）、:65-89（私有方法与成员）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/bindings.cpp)（implementation）：:22-65 全文；`InitNpuBindings.cpp:269-270` 调用点。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/static_launcher/fast_launcher.cpp)（implementation）：:16-116 全文。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/csrc/bindings.cpp)（primary）：:29-56（符号解析）、:84-272（计划结构与 ABI）、:274-356（写参数/指针提取/grid 校验）、:358-465（装包与提交）、:467-569（计划构造与两发射入口）、:573-605（绑定）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/experimental/python_wrapper_fast_launch/wrapper_codegen.py)（implementation）：:10-52 全文；`backend.py:337-345` 消费点。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_compat.py)（primary）：:11-76 全文；`_inductor/__init__.py:48-83/:126/:143/:180/:411`。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_runtime/model_base.h)（implementation）：:281-284/:301-305/:317-326/:333-352/:403-445/:455-489/:497-537/:542-558/:599-713/:741-768/:925-944/:1036-1052。
- 发布 pin 负向证据：`f3ecfe4a` 无 static_launcher 目录、python_wrapper_fast_launch/csrc、triton_compat.py、model_base.h（aoti_runtime 为 model.h 布局）；`InitNpuBindings.cpp` 无两注册调用。
