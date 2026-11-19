---
type: Guide
title: ascend_npu_ir MLIR工具链：编译器驱动、缓存、torch_mlir桥接与C++绑定层
description: 记录torch_npu._inductor.ascend_npu_ir包的静态结构：NpuMlirCompiler/AkgCompiler驱动、CacheManager文件缓存、MLIR/AKG代码生成与wrapper、npu_stream直接注册custom
  op、torch_mlir fx_importer桥接、PythonDispatcher补丁面，并包含csrc/inductor/mlir的C++绑定层（load_kernel_binary装载、common_launch/common_launch_dyn启动与tiling协议）。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/mlir_compiler.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/meta_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/codecache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/codecache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/mlir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/mlir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/akg.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/akg.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/cpp_wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/cpp_wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_stream.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_stream.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/torch_mlir_patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/torch_mlir_patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_patch_deprecated.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_patch_deprecated.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/fake_tensor.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/fake_tensor.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/build_info.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/build_info.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/mlir_binding.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/cpp_common.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/cpp_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/hacl_rt.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/mlir/mlir_binding.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/mlir/cpp_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/mlir/cpp_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/inductor/mlir/hacl_rt.h
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ascend_npu_ir MLIR工具链：编译器驱动、缓存与torch_mlir桥接

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的`torch_npu/_inductor/ascend_npu_ir`包（Inductor的MLIR/AKG编译后端库）；包内8个文件两版字节一致（README.md、build_info.py、cache.py、triton.py、npu/inductor_patch/fake_tensor.py及三个空`__init__.py`），其中4个含事实内容者（cache.py、fake_tensor.py、build_info.py、triton.py）同时固定发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b。静态阅读，未调用akg/mlir编译器。本卡补齐两版对照：等价文件（npu_stream.py、torch_mlir_patch.py，仅行尾空白差异）补绑发布来源；其余差异文件同样补绑发布来源作为分界证据，主线结论默认只适用主线，逐条以「两版差异边界」节为准。DVM调度/wrapper如何消费该库见[DVM融合执行](torch_npu_dvm_mlir_codegen_and_fallback.md)，本卡补库自身结构。整卡draft、platforms为空。本卡增补主线`torch_npu/csrc/inductor/mlir/`四个C++文件（同commit），闭合该路线的装载/启动源级面。四个文件的发布 pin 对照见该节文末。

## 编译器驱动的分层

`MetaCompiler`（npu/meta_compiler.py）是基类：从kernel_meta取dynamic/mutated_indices/kernel_hash/signature/ranks/num_outputs/device_index/traced_graph_hash等，管理multiprocess_compile/no_more_compile/autotune与launchers、fallback_call、非连续输入输出下标。`NpuMlirCompiler`（mlir_compiler.py）继承它：可选导入akg（`importlib.util.find_spec("akg")`，存在才`from akg.kernel import Kernel as MlirKernel`），经`torch_npu._C.mlir.load_kernel_binary`加载编译产物，动态shape路径另有tiling size获取路径，mlir_processed/fx_graph_launcher/mlir_text等状态分段管理。**akg不存在不是错误**：AkgCompiler/AkgScheduling路线（npu/codegen/akg.py，`akg_auto_fallback`编译API）只是不可用，MLIR路线不受影响。codecache.py把NpuMlirCompiler/AkgCompiler接进torch._inductor的AsyncCompile/SubprocPool体系并提供CompiledKernel包装。

## 文件缓存的目录合同

包内自带CacheManager（cache.py）：缓存根为`$TRITON_HOME`（默认`~`）下的`.triton/cache`，另有`.triton/override`与`.triton/dump`三个角色目录；FileCacheManager按key读写单文件与文件组，带锁。**该包复用Triton的目录约定但实现独立**——排障时清`~/.triton/cache`会同时影响两者，目录存在不等于Triton被使用。

## 代码生成与wrapper

`npu/codegen/mlir.py`的NpuMlirKernel（NpuMetaKernel子类）在codegen_kernel前先`scalarize_tensor_ops_on_scalars`，经`npu_cast_to_prim_cast`把torch算子转prim cast，call_kernel把`_uwu_`前缀实参按`MLIR_OPERATOR_MAPPING`映射成表达式后generate_kernel_call；调试路径可生成复现串与fake inputs。`npu/codegen/cpp_wrapper.py`提供cpp launcher（供C++ wrapper路线生成launch代码）。`npu/utils.py`（主线909行）承载MLIRProcessor、get_fx_graph_code、fx_graph_op_types、parse_fx_example_inputs等共享工具。inductor_patch/子包在主线是轻量shim（补丁经`_inductor/lowering_patch.apply_mlir_inductor_patch()`受控安装）——**它们是对torch._inductor内部结构的定点重定向，升级PyTorch时是高脆性面**（发布版的安装机制差异见「两版差异边界」）。

## npu_stream：绕开torch.library.custom_op的注册开销

`npu/npu_stream.py`自带vLLM风格的`direct_register_custom_op`：用`torch.library.Library("npu_stream", "FRAGMENT")`直接define+impl，**绕过torch.library.custom_op的复杂dispatch逻辑**（源注释明确以开销为由），PrivateUse1 dispatch key，schema经infer_schema推断（兼容PyTorch 2.4的旧内部接口）；NPU_STREAMS/NPU_EVENTS全局注册表管理stream/event。操作符生命周期绑定Library对象存活。这是性能敏感路径自己维护的注册通道，不是新的公开API。**该文件两版仅行尾空白差异（451行对451行，24/24顶层符号AST一致），本节结论对发布pin直接适用**。

## torch_mlir桥接与deprecated补丁

`npu/torch_mlir_patch.py`基于torch_mlir的fx_importer/FxImporterHooks把FX图导入MLIR并把sympy表达式转semi-affine表达式（AffineAdd/Mul/Mod/FloorDiv等映射），是MLIR侧看见FX图的入口（**两版仅1处行尾空白差异，结论对发布pin直接适用**）。`npu_patch_deprecated.py`是遗留PythonDispatcher补丁集：embedding_backward拒绝sparse=True（改走dense backward）、contiguous在PythonDispatcher路径clone、以及给全部ProcessGroup追加临时超时的分布式补丁——这些是历史兼容面，名字即警告（sparse拒绝与超时补丁两版一致；发布版另有`_patch_get_system`占位，见边界节）。`npu_lowering.py`注册fallback集（主线含`enable_full_lowering_fallback`环境列表、`fallback_to_aten_mode`，发布版差异见边界节），与lowering_common协作决定哪些op直接回ATen。

包根的`build_info.py`仅声明`ABI_TAG = 0`常量，`triton.py`仅提供no-op的`constexpr()`标记；三个`__init__.py`（包根、npu/、npu/codegen/）为空文件（包结构锚点，无语义内容，两版字节一致）。

## lowering.py补丁面只做了边界采样

`npu/inductor_patch/lowering.py`（主线7298行、发布7439行）是最大的单文件：torch._inductor lowering的NPU补丁总面。本卡只采样了模块头与导入结构，**不声称覆盖其lowering规则集**；该文件的逐规则审阅是独立工作量（两版351个公共符号中316个AST一致、35个规则体差异，结构差异类目见「两版差异边界」）。需要查某个op在MLIR路线的lowering时以该文件实际内容为准，不要从DVM卡或本卡推导。

## C++绑定层：kernel装载与启动

`torch_npu/csrc/inductor/mlir/`四个文件整体处于`#ifndef BUILD_LIBTORCH`守卫内——**libtorch 构建不编译该层**，C++ wrapper/MLIR 启动路线在 libtorch 形态下没有这个入口。装载端 `mlir_binding.cpp` 定义 `torch_npu._C.mlir.load_kernel_binary(func_name, bin_file)`：读二进制（文件大小必须落在 uint32 正区间，TORCH_CHECK），以 `RT_DEV_BINARY_MAGIC_ELF_AIVEC`（0x41415246，ELF/aivector）注册 `rtDevBinaryRegister`，再 `rtFunctionRegister` 并回传一个从 `0xbadbeef` 起进程内单调递增的伪 stub 地址——该地址只作 rtFunctionRegister 的 key，不是可解引用地址；`NpuMlirCompiler` 正是经此入口装 MLIR 产物。启动端 `cpp_common.cpp`：`common_launch` 走 `rtKernelLaunch(func, gridX, args, argsSize, NULL, stream)`，前后按 `profiler::GetTraceLevel()`（-1 关闭 / ≥1 详细）经 `MsprofReportApi`/`MsprofReportCompactInfo` 上报 launch 事件（magicNumber 0x5a5a、taskType 0=AI_CORE、blockDim=gridX）。`common_launch_dyn` 是动态 shape 路径：tiling 参数占据 args 尾部第 5/4 槽位（TilingMemrefAligned/AllocatedOffset），先填 host 指针，执行 `int64_t(*)(void*)` 形态的 host tiling 函数更新 args/tiling_key，再 `aclrtMemcpy` 把 tiling 缓冲 H2D（失败只 `printf` 错误码并继续），替换为 device 指针后**直接调用 `void(*)(uint32_t, void*, void*, void*)` 函数指针**（gridX, nullptr, stream, args），不走 rtKernelLaunch。tiling host/device 与 workspace host/device 各由全局 `MEM_CACHE`/`MEM_WORK_CACHE` 缓存（`aclrtMallocHost`/`aclrtMalloc` + 对应 free 的 unique_ptr）。`opcommand_call` 把 launch 包进 `at_npu::native::OpCommand` 自定义 handler，使 MLIR kernel 启动进入 aclop 语义的算子命令跟踪。`cpp_wrapper.py` 生成的 launcher 模板调用的正是 `common_launch`/`common_launch_dyn`（模板 122/150/334 行）。`hacl_rt.h` 是 vendored 的 CAND runtime C API 声明子集（rtDevBinaryRegister/rtFunctionRegister/rtKernelLaunch/rtKernelLaunchWithFlag 及 `rtArgsEx_t` 的 tiling 字段、RT_DEV_BINARY_MAGIC_* 常量表、rtMalloc/rtMemcpy 系），供生成的 wrapper 代码独立链接，不引入完整 runtime 头。

### C++绑定层的发布 pin 对照（f3ecfe4a）

四个 C++ 文件已做两 pin 机械比对：`mlir_binding.cpp` 全空白折叠后逐字节等价（仅重排版）；`cpp_common.cpp`/`cpp_common.h` 仅 profiling/acl 头 include 改 `third_party/acl/inc/...` 相对路径并重排版，代码语义一致；`hacl_rt.h` 仅注释差异（代码 token 流相同，发布 397 行 vs 主线 416 行为注释/排版差）。本节结论对发布 pin 直接适用，行号引用按各 pin 文件核对。

## 两版差异边界（发布f3ecfe4a对照，静态diff）

本节每条均有两版diff+AST比对证据。除标注「等价」外，正文主线结论默认不外推发布TorchNPU 26.0.0：

| 差异类目 | 主线ac0e1564 | 发布f3ecfe4a |
| --- | --- | --- |
| AKG组织 | AkgCompiler类在mlir_compiler.py；akg.py为31行`akg_auto_fallback`薄路线；`find_spec("akg")`可选探测；codecache.py有AkgScheduling检测分支与`_akg_worker_compile` | AkgCompiler完整类（`__init__/compile/run`）移到akg.py（157行）；mlir_compiler.py无该类、无find_spec探测；codecache.py删Akg路由，`_load_fx_graph`恒构造NpuMlirCompiler；两处`except Exception`在发布为裸`except` |
| NpuMlirCompiler方法面 | 独有`_to_named_op_mlir`、`_should_disable_autotune_for_determinism` | 独有`register_fx_fallback`、`data_dump(_fake)`、`fx_subgraph_dump`、`acc_compare_and_dump`、`run`；另有13个方法体差异（bisheng_compile/compile_mlir/autotune_to_one_config等） |
| codegen/mlir.py | 149行，`_uwu_`实参经共享`MLIR_OPERATOR_MAPPING`映射 | 474行，新增`NpuTritonKernel`、`create_fx_from_snodes_by_traced_graph`、`find_common_positions`；无MLIR_OPERATOR_MAPPING，算子→字符串映射在lowering.py内联为`operator_to_string`（`xvxa`–`xvxh`转义）等表 |
| codegen/cpp_wrapper.py | launcher模板在`ptr_info.dev_ptr`为空错误路径补`Py_DECREF(ret)`与if块括号 | 缺引用计数释放与括号块——错误路径引用计数行为不同（主线已修） |
| codegen/wrapper.py | 238行含`NpuMlirSubgraphPythonWrapperCodegen`类 | 202行无该类；`NpuMlirWrapperCodeGen`两版都有、体差异 |
| inductor_patch安装 | `__init__.py`4行pkgutil `__all__`；补丁经`lowering_patch.apply_mlir_inductor_patch()`受控安装 | `__init__.py`43行导入即接管：逐名覆写`torch._inductor.lowering`函数、合并lowerings表、替换`_maybe_layout_constraints/fallbacks/needs_realized_inputs/foreach_ops`族、`importlib.reload(graph)`、`_patch_scheduler()` |
| sizevars API代差 | `optimization_hint`（scheduler.py）、`int()`转型unroll门（ir.py）、`guarding_hint_or_throw`（lowering.py expand） | 对应位置为`size_hint`（scheduler.py单行差）、`size_hint(reduction_numel)`、`size_hint`——补丁绑定的torch._inductor sizevars方法名随vendored torch版本不同，升级按目标torch核对 |
| inductor_patch/lowering.py | `_has_slice_op`独有；TracedGraph/dump辅助抽到`lowering_common.py`共享；make_reduction复制size列表、按dtype条件组kwargs；expand有cpu短路分支 | 7439行内联`TracedGraph/create_fake_input/merge_fx_graphs/subtract_graph/rsqrt`（与发布lowering_fx.py重复实现）；make_reduction直传；expand无cpu分支；35个规则体差异（delta前列：merge_traced_graphs 58、fetch_graphs 32、process_ir_constant 26） |
| npu_lowering.py | 122行，`enable_full_lowering_fallback`环境列表 | 59行，消费ascend_npu_ir config.py固定29项FALLBACK_LIST；`fallback_to_aten_mode`两版都有 |
| npu_patch_deprecated.py | 58行 | 71行新增`_patch_get_system()`（hash为`json.dumps({})`常量sha256的静态占位）；embedding sparse拒绝/超时补丁一致 |
| npu/utils.py | 909行，独有`fold_sum_cast_to_dtype`与`_NPU_DTYPE_CAST_OPS` | 861行新增`run_once`；MLIRProcessor等10符号体差异，18符号AST一致 |
| 等价确认 | npu_stream.py、torch_mlir_patch.py两版仅行尾空白差异（AST逐符号一致），已补绑发布来源 | 同左 |

## 边界与验证方式

本卡未执行任何编译：akg可选导入、SubprocPool编译、缓存命中、npu_stream注册开销差异都应按实际环境复核（日志确认走MLIR还是AKG、缓存目录实际读写）。inductor_patch与torch内部结构的耦合随PyTorch版本变化，升级后需重新核对该子包。两版行为差异已按「两版差异边界」分节核对（静态diff+AST比对，未运行）；运行级差异（如裸except与except Exception在BaseException上的差别、错误路径引用计数）仍需按目标pin实际复核。；C++绑定层同样只读主线ac0e1564，未实际装载或启动任何kernel，伪 stub 地址方案与tiling槽位协议属固定实现细节，vendored runtime行为以配套CANN为准。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/mlir_compiler.py)（primary）：定向范围1–60；两版diff比对（U0 61 hunks，+309/−318；方法面差见边界表）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/meta_compiler.py)（implementation）：定向范围1–50。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/cache.py)（implementation）：定向范围1–55；两版字节一致。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/codecache.py)（implementation）：定向范围1–55；两版diff比对（U0 36 hunks，+49/−110）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/mlir.py)（implementation）：定向范围1–55；两版diff比对（U0 29 hunks，+427/−102）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/akg.py)（implementation）：全文件31行；发布版157行（类清单diff见边界表）。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_stream.py)（implementation）：定向范围1–45；**两版行尾归一化后逐字节一致，24/24顶层符号AST一致**。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_patch_deprecated.py)（implementation）：定向范围1–58；发布71行（+`_patch_get_system`）。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/lowering.py)（implementation）：仅头部采样1–50；两版类目级diff聚类（U0 80 hunks，+358/−217；316/351公共符号AST一致），边界见正文。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/torch_mlir_patch.py)（implementation）：定向范围1–40；**两版行尾归一化后逐字节一致**。
- [补绑发布来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_stream.py)（implementation）：等价绑定，全文件两版比对（451行，仅行尾空白）。
- [补绑发布来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/torch_mlir_patch.py)（implementation）：等价绑定，全文件两版比对（214行，仅1处行尾空白）。
- [补绑发布来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/wrapper.py)（implementation）：分界绑定，全文件diff（202行，缺`NpuMlirSubgraphPythonWrapperCodegen`）。
- [补绑发布来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/inductor_patch/__init__.py)（implementation）：分界绑定，全文件阅读（43行导入即接管面）。
- [补绑发布来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_lowering.py)（implementation）：分界绑定，全文件阅读（59行，FALLBACK_LIST消费）。
- 其余补绑发布来源（codecache.py、codegen/akg.py、codegen/cpp_wrapper.py、codegen/mlir.py、inductor_patch/ir.py、inductor_patch/lowering.py、inductor_patch/scheduler.py、mlir_compiler.py、npu_patch_deprecated.py、utils.py）：分界绑定，逐文件两版diff+顶层符号AST清点，类目见「两版差异边界」表。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/mlir_binding.cpp)（primary）：读取范围1–68全文（awk口径，末行无换行符；wc=67）。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/cpp_common.cpp)（primary）：读取范围1–182全文。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/cpp_common.h)（implementation）：读取范围1–27全文。
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/mlir/hacl_rt.h)（implementation）：读取范围1–416全文。
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/cpp_wrapper.py)（implementation）：定向核对common_launch/common_launch_dyn调用模板行122、150、334。
