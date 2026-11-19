---
type: Guide
title: torch_npu 发布版 cpp wrapper 旧一代实现：延迟 Triton 调用、C2C 控制地址与 rtKernelLaunch（cpp_wrapper.py 863 行全文）
description: 记录发布 pin 注册的 codegen/cpp_wrapper.py（863 行全文）：无基类 DeferredNpuTritonCallWrapper 的模板包装/等值 1 剔除/懒装载、CppWrapperNpu(CppWrapperCpu) 的 AOTI 头改写与 npu_block 对齐检查、generate_args_decl 的 int/float 变量槽、每发射 rtGetC2cCtrlAddr 与定长 NULL 前导 + rtKernelLaunch ABI——与主线 cpp_wrapper_npu.py 两代同名类的负向 rg 代差锚。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_wrapper.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py
  role: implementation
created_at: '2026-11-12T14:24:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 cpp wrapper 旧一代实现：延迟 Triton 调用、C2C 控制地址与 rtKernelLaunch（cpp_wrapper.py 863 行全文）

## 固定版本与适用范围

发布 pin（f3ecfe4a）的 `codegen/cpp_wrapper.py`（863 行）经 release `__init__.py:53-54` 以 `register_backend_for_device('npu', NPUTritonScheduling, NPUWrapperCodeGen, CppWrapperNpu)` 注册，此前主线两张 cpp wrapper 卡只对它做过锚级 sed（:60-68/:198-201 两代类 lineage），本卡记录其全文行为。两代同名类：发布版 `DeferredNpuTritonCallWrapper` 为**无基类独立 dataclass**、`CppWrapperNpu` 继承 **CppWrapperCpu**（主线版本分别是 DeferredTritonCallWrapper 子类与 CppWrapperGpu 子类），互不推导。纯静态阅读；draft、platforms 为空。

## 两代代差（负向 rg 核对）

对发布注册文件全树负向 rg：`CATLASSCodeCache|dlopen|dlsym|aclrtLaunchKernelWithHostArgs|DYN_UBUF_SIZE|resolve_grouped_runtime_block|best_by_group|grouped_candidate_plan|enable_auto_blockify|aclrtGetHardwareSyncAddr|is_ascend950` 在 `torch_npu/_inductor/codegen/cpp_wrapper.py` **零命中**——CATLASS JIT 装载、TA3.6 packed sync-block-lock 32 位半槽 + aclrtMemcpy、workspace grid 乘积缩放、SIMT DYN_UBUF_SIZE 属性、分组 plan 消费全部是主线 cpp_wrapper_npu.py 独有（主线事实归[主线延迟分组调用卡](torch_npu_main_inductor_cpp_wrapper_deferred_grouped_launch.md)与[主线发射卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)）。发布树 `dlopen` 命中仅在 vendored `ascend_npu_ir/ascend_npu_ir/npu/codegen/cpp_wrapper.py`（另一份 17257 字节文件，dlopen :213，非注册路径，本卡不主张）与 csrc FunctionLoader.cpp。

## 模块层（:1-63）

导入上游 `CudaKernelParamCache`、`get_cpp_wrapper_cubin_path_name`、`CppWrapperCpu`、`MultiKernelCall`、`PythonWrapperCodegen/SymbolicCallArg`、`_align/ALIGN_BYTES`，再取 `npu_config` 与 `config.npu_block as NPU_ALIGN_BYTES`（:27-28，AOT 输入对齐检查的对齐单元）。`checkIfTrue`（:34-37）全树零调用（仅定义）；`cpp_string_literal`（:40-54）做 C 字符串转义，cubin 路径与 mangled_name 进 `loadKernel` 字面量时使用；`UnwrapUnspecArg`（:57-62）是「需要对该张量调 .item()」的 dataclass 标记（dtype 字段）。

## DeferredNpuTritonCallWrapper（:64-198）

| 环节 | 行段 | 静态事实 |
| --- | --- | --- |
| 字段 | :72-75 | wrapper_name/kernel_name/arg_types/kernel_id；**无基类**（主线为 DeferredTritonCallWrapper 子类且携带分组 plan/变体发射，本类没有）。 |
| generate | :77-141 | `multi_kernel_` 前缀先 `MultiKernelCall.lookup_choice`；参数取 `CudaKernelParamCache`（:82）；`extra_launcher_args` 在 def_args 中已存在时把 arg_types 按 SymbolicCallArg 补齐（:87-91）；非 AOT 发 `static <cpp_kernel_type> kernel = nullptr;`、AOT 用 `kernels_.<name>`（:93-101）；tensor-like 参数（torch_dtype/UnwrapUnspecArg）生成 `typename <name>_type_` 模板参，AOT 追加 `kernels_type_`（:103-112）；签名分派 tensor-like→`const T&`、Symbolic/Expr/int→`int64_t`、float、bool，其余 ValueError（:115-125）；尾参 stream_、AOT `kernels_type_& kernels_`、`cubin_dir_` 可选 string（:126-131）；体=generate_grid→generate_load_kernel→generate_launch_kernel（:134-136）；把 cubin 文件追加进 `V.graph.wrapper_code.additional_files` 供打包（:139-141）。 |
| generate_grid | :143-164 | 从 call_args 里含 `_numel` 子串的项收集 numels（:151）；`GridExprNpu.from_meta_and_set_numel(inductor_meta, params["config"], numels, "cpp")`——GridExprNpu 位于发布版 `npu_triton_heuristics.py:189`（与主线 `runtime/triton_heuristics.py` 同名不同文件）；写 `uint32_t grid_0/1/2`，任一维为 0 直接 return（:164，零 grid 早退与主线同型）。 |
| generate_load_kernel | :166-178 | `if (kernel_var == nullptr)` 懒装载：`loadKernel(cubin_path字面量, mangled_name字面量, shared_mem, cubin_dir_)`。 |
| generate_launch_kernel | :180-197 | 从 call_args 剔除 `triton_meta["constants"]` 中的等值 1 常量（注释：C++ wrapper 剥离 equal_to_1，:183-184）；委托 `wrapper.generate_args_decl` 后 `launchKernel(call, "kernel_var_name")`（:187-197）。 |

## CppWrapperNpu(CppWrapperCpu)（:200-863）

- 初始化/建头（:205-339）：`__init__` 置 device、device_codegen（`get_device_op_overrides`）、grid_id 计数、visited_raii_handle、`_triton_call_wrappers` dict（:205-212）；`create` 忽略 is_subgraph/subgraph_name/parent_wrapper/partition_signatures 恒返回新实例（:214-222）。`super_write_header_rewrite`：const graph 不写头；AOT 拼 `aoti_runtime/interface.h`+`model.h` 并把 `interface.cpp` 源整体嵌入（:233-243）；非 AOT 嵌 pybind11 RAIIPyObject + device_utils/utils（:245-284）；公共段**注释掉 `c_shim_npu.h`**（原文 "npu doesn't implement it"，:291-292）、`typedef at::Half half; typedef at::BFloat16 bfloat16_t`、`align()` 对齐到上游 ALIGN_BYTES（:294-301）；torch include 路径存在 extend c_shim 则追加（:304-313）；`profiler_mark_wrapper_call` 或 `cpp.enable_kernel_profile` → `ATen/record_function.h`（:315-322）。`write_header` 追加 unistd/filesystem、abi_compatible_header、kernel_driver（hipify 包装）、`torch_npu/csrc/framework/OpCommand.h` 与 `runtime/runtime/rt.h`（:330-337，后者是 rtGetC2cCtrlAddr/rtKernelLaunch 的头）；`npu_config.aot_inductor.debug_kernel` → `torch/torch.h`（:338-339）。
- AOT 输入对齐与流（:341-374）：`write_get_raw_stream` 用 `AOTI_TORCH_ERROR_CODE_CHECK(aoti_get_stream(...))`；`codegen_inputs` 在 AOT 且 `inputs_to_check` 时按 `NPU_ALIGN_BYTES`（npu_block）做指针位与检查，未对齐 `throw std::runtime_error("<input> is not aligned to N bytes")`（:361-372）——JIT 路径依赖上游 `copy_misaligned_inputs` 隐式拷贝（注释 :354-360）。
- kernel 定义与发射（:376-457）：`define_kernel` 仅在 gpu 且 `triton.autotune_at_compile_time` 时委托 PythonWrapperCodegen 生成 autotune 块，cpu 核回 CppWrapperCpu（:376-392）；`generate` 先为 sorted `src_to_kernel` + `user_defined_kernel_cache` 名发 nullptr 静态声明再 super（:394-410）；用户自定义 Triton kernel 剔除 constexpr 参数后走 `generate_kernel_call(triton=True)`（:412-457）。
- debug 面（:459-544）：`codegen_tensor_item_npu` fp16/bf16 先 item 到原生类型再 `float <s> = float(<tmp>)`、struct 槽 `aligned(4)`；其余直接 item、槽 `aligned(sizeof)`（:459-482，无主线版的 bool 分支）。`codegen_device` 把 `privateuse1` 改写为 `npu` 再用 `cached_torch_device_type_npu`（:484-491）。AOT + `aot_inductor.debug_kernel` 时 `write_wrapper_decl` 建 dump 目录并定义 handle→指针 lambda（:493-515）；`generate_debug_str` 对每个 kernel_id 的张量参数做一次性 handle 解引用，插 `npuSynchronizeDevice()` + `torch::save` 到 `{dump_path}/{kernel_id}_{kernel_name}_{mark}.pt`（:517-544）。
- generate_args_decl 与 launch ABI（:546-692）：`signature2dtype` 表含 `i1→int32_t`、fp16/bf16→float（:573-586）。process_args 分支：UnwrapUnspecArg（非 nvTmaDesc）→ `codegen_tensor_item_npu`；torch_dtype → `reinterpret_cast<cpp_device_ptr>` + debug_kernel 时每名一次 `AtenTensorHandle {arg}_h`；`sympy.Integer/int` → **`int` 变量槽 aligned(4)**（:615-618；主线同位是 TA3.6 packed 结构的 int64/int32 精确槽）；Float/float → float 槽；SymbolicCallArg 且签名在表内 → 显式 dtype 槽（「`auto` 会推出意外类型」注释 :623-635）；否则 TypeError。launch lambda：每次发射内联 `rtError_t ret = rtGetC2cCtrlAddr((uint64_t*)&ffts_addr, &ffts_len); if (ret != RT_ERROR_NONE) return ret;`——**C2C 控制地址逐发射获取、获取失败即整次发射跳过**（:656-660）；`struct __attribute__((packed))` 定长前导 `ffts_addr/sync_block_lock=NULL/workspace_addr=NULL`（均 aligned(8)）+ 变长 args 槽 + `grid_0/1/2` int32 槽（:664-680）；`block_num = grid_0*grid_1*grid_2`（:682）；`rtKernelLaunch(kernel, block_num, &kernel_args, sizeof(kernel_args), NULL, stream_)`（:686）。同步锁槽恒 NULL、无 workspace 缩放、无 host-args/SIMT 分叉——与主线的 aclrtGetHardwareSyncAddr/锁拷贝/工作空间乘积缩放/AclrtLaunchKernelWithHostArgs 是两代 ABI。
- 调用入口（:694-828）：`generate_kernel_call_npu` 在 `autotune_at_compile_time` 且未登记时先走 PythonWrapperCodegen 生成 autotune 块（:709-728）；triton 分支：`prepare_triton_wrapper_args` 归一化后以 `call_{kernel}` 为名**每个 wrapper_name 只登记一次** DeferredNpuTritonCallWrapper（:746-749），call_args 追加 stream（AOT 再追加 `kernels`/`this->cubin_dir_`），发射 `call_<kernel>(args...);`（:759）；非 triton 分支：指针型追加 `.data_ptr()` 强转，`kernels.<name>(..., stream)`（:760-768）。`generate_kernel_call` gpu=False 回 CppWrapperCpu，npu 参数恒等于 gpu（适配注释 :791-795）。
- finalize（:830-860）：`finalize_prefix` 新建 buffer，super 完成后逐个 deferred wrapper `.generate(self)`——**延迟到 autotune 全部结束后才发射包装函数**，再把旧 prefix 拼回（:830-839）；`prepare_triton_wrapper_args`：str 参数按 `should_unwrap_unspec_arg` 换 UnwrapUnspecArg、bool 转 lower、int/float/Symbolic 转 str、其余 `cexpr(simplify)`（:841-860）；`make_zero_buffer` 走 `aoti_torch_zero_`（:862-863）。

## 失效边界与静态口径

- 全部为发布 pin 静态事实：wrapper 生成文本、launch ABI 均未执行；「rtGetC2cCtrlAddr 失败即不发射」按 lambda 控制流读出，真实失败行为未运行验证。
- 两代同名类行为差异只限本卡与主线两张 cpp wrapper 卡已读行段；主线 cpp_wrapper_npu.py 的分组 plan/变体发射/自动化 CATLASS 面不在本卡复述。
- `GridExprNpu` 的 grid 表达式本体（发布 npu_triton_heuristics.py:189 起）本卡只记 import 与调用签名，类体归[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)。
- vendored `ascend_npu_ir/.../cpp_wrapper.py`（dlopen :213）非注册路径，本卡不主张其内容。

## 相邻卡边界

[主线延迟分组调用卡](torch_npu_main_inductor_cpp_wrapper_deferred_grouped_launch.md)与[主线 codegen/发射卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)（主线两代对应面与 CATLASS/packed lock ABI）；[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（注册三元组语境）；[设备算子覆写卡](torch_npu_release_flat_inductor_device_op_overrides.md)（发布侧设备面）；[发布版 split_tiling 函数卡](torch_npu_release_inductor_split_tiling_functions.md)（同期 scheduling 消费面）。

## Evidence

- [发布版 codegen/cpp_wrapper.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_wrapper.py)（primary；`:1-863` 全文，1-220/221-550/551-863 三窗）
- [发布版 npu_triton_heuristics.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py)（implementation；rg 锚 :189 `class GridExprNpu`，类体归[发布版 autotuner 类体卡](torch_npu_release_flat_inductor_autotuner_class_body.md)）
- [发布版 _inductor/__init__.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py)（implementation；rg 锚 :53-54 注册）
- [主线 codegen/cpp_wrapper_npu.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py)（implementation；对照锚——两代同名类差异、负向 rg 主线独有符号清单，主体归[主线延迟分组调用卡](torch_npu_main_inductor_cpp_wrapper_deferred_grouped_launch.md)与[主线发射卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)）
