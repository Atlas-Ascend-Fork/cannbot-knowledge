---
type: Guide
title: torch_npu 主线 cpp wrapper 分组延迟调用：DeferredNpuTritonCallWrapper 的 plan 消费、组解析与变体发射
description: 记录主线 _inductor/codegen/cpp_wrapper_npu.py 前半区（:1-521 全读）：CudaKernelParamCache 运行期块参数临时剥除与 extra_launcher_args 数量契约、grouped_candidate_plan 的三个读取端（active variants/load_meta/cubin 文件集合）、特征输入外积表达式发射、桶梯 if/else-if 的混合进制 group_id 编码、resolve_grouped_runtime_block 的 ceildiv 链与 reachable 组 switch 分派、变体级 load/launch 发射与 AOT 嵌入装载差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_wrapper.py
  role: implementation
created_at: '2026-11-12T13:41:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 cpp wrapper 分组延迟调用：DeferredNpuTritonCallWrapper 的 plan 消费、组解析与变体发射

## 固定版本与适用范围

主线 pin（ac0e1564）`_inductor/codegen/cpp_wrapper_npu.py`（1165 行）的**前半区** `:1-521`：模块头 imports、`DTYPE_TO_TA_TYPE`（torch.bool 映射 `int32_t`，注释说明 bf16→float 由 codegen_tensor_item_npu 特殊处理，`:38-43`）与 `DeferredNpuTritonCallWrapper` 全类体（`:45-519`，`@dataclasses.dataclass`，继承上游 `DeferredTritonCallWrapper`）。它由同文件 `CppWrapperNpu._generate_kernel_call_helper` 在 triton kernel 生成后把上游 DeferredTritonCallWrapper **原地替换**进 `_triton_call_wrappers`（`:645-658`，见[姊妹卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)）；plan 与参数的生产端分别是 [NPUSymbolicGroupedAutotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)（load_meta 记录 `:2477-2560`）与 [主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)（save_npu_kernel 写 `:1323-1362` 的 params 键）。注册锚：主线 `_inductor/__init__.py:258/:263`（`NPUCombinedScheduling + NPUPythonWrapperCodeGen + CppWrapperNpu` 三件套）。**发布 pin（f3ecfe4a）无此文件**：发布版自有 863 行 `codegen/cpp_wrapper.py`，其中 `:65` 是同名的 `DeferredNpuTritonCallWrapper`——但是**无基类的独立 dataclass**、`:200` 的 `CppWrapperNpu` 继承 `CppWrapperCpu`（而非主线的 `CppWrapperGpu`）——是另一代实现（行为面见[发布版 cpp wrapper 旧一代实现卡](torch_npu_release_inductor_cpp_wrapper_legacy_codegen.md)，本卡仅锚级核对）；分组符号（`grouped_candidate_plan`/`resolve_grouped_runtime_block` 等）在发布全树零命中（负向 rg）。纯静态阅读；draft、platforms 为空。

## params 剥除与文件面（`:61-131`）

| 步骤 | 动作 | 失败/边界 |
| --- | --- | --- |
| `_patch_runtime_block_params`（`:61-102`） | contextmanager：`multi_kernel_` 前缀先 `MultiKernelCall.lookup_choice` 还原真实 kernel 名；`CudaKernelParamCache.get(kernel_name)` 取 params，缺失 → `RuntimeError("CudaKernelParamCache not populated ...")`；`inductor_meta["runtime_block_arg_names"]` 非空 → 从 `params["def_args"]` 剥除这些名字（**临时改写共享 params dict**）；有 `extra_launcher_args` 且剥除后 def_args 多于原 arg_types → 数量契约 `len(wrapper_def_args) == len(arg_types) - len(extra_launcher_args)`，违反抛 RuntimeError，并把 `arg_types` 临时补 `[SymbolicCallArg] * len(extra_launcher_args)` | `finally` 恢复 original_def_args/arg_types——剥除是作用域内临时态，不落盘 |
| `generate`（`:104-131`） | `config.patch("triton.autotune_at_compile_time", not V.graph.aot_mode)`（todo 注释：cpp_wrapper_npu 暂不支持 lazy compile）后委托 `super().generate(wrapper)`；`group_enabled` → 从 `grouped_candidate_plan` 取 active variants 的 `_grouped_load_meta(...)["cubin_path"]` 集合；`default_cubin_path` 若不在**既有**文件集合、不在 grouped cubin 集合、且已在 additional_files → 移除（分组胜者取代默认 cubin）；否则 cubin_paths 为默认单路径 | 每个 cubin path 逐个 append 进 `V.graph.wrapper_code.additional_files`（入口先快照 existing_files） |

## plan 三个读取端（`:133-173`）

- `_grouped_runtime_block_names`：`grouped_plan["runtime_block_append_order"]` 元组——runtime block 的**发射顺序**由此固定。
- `_grouped_active_variants`：`best_by_group` 为空 → `RuntimeError("... expects best_by_group to be populated")`；取各组胜者 variant_id 的 OrderedSet，按 `variant_order` 保序过滤；为空 → `RuntimeError("... has no active compiled variants")`。
- `_grouped_load_meta`：`grouped_plan["variants"][vid]["load_meta"]`，缺失 → RuntimeError（要求每个 active variant 都有 load_meta；生产端是 NPUSymbolicGroupedAutotuner 的 cpp wrapper load_meta 记录面）。

## 分组发射：特征输入 → group_id → 选择（`:175-342`）

- **特征输入**（`:175-204`）：`feature_arg_indices` 与 `feature_sources` 长度不等 → RuntimeError；每特征取 `def_args` 中对应参数名，`source` 为 `outer_product`/`reduction_product` → `" * ".join(arg_names)` 外积表达式；单参数直取其名；其他多参形态 → `RuntimeError("... expects one axis")`。发射 `int64_t grouped_feature_{i} = {expr};`。
- **group_id 编码**（`:206-239`）：每特征桶梯 `if / else if (grouped_feature_i <= {upper}) grouped_bucket_i = {idx};`——上界**含等号**；链尾 `else grouped_bucket_i = len(buckets);` 即开桶是最后一个下标。混合进制累加 `grouped_group_id += bucket * stride; grouped_group_stride *= len(buckets) + 1`（基数 = 桶数+1）；`group_id_count > 0` 时发射 `grouped_group_id >= {count}` → `throw std::runtime_error("resolved group id out of range")`。这是 symbolic_grouping `bucketize/make_group_id`（Python 侧，归[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)与[NPUSymbolicGroupedAutotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)）的 **cpp 侧孪生实现**。
- **选择**（`:241-342`）：runtime block 先全部 `int64_t {name} = 0;` 零初始化；发射 lambda `resolve_grouped_runtime_block(axis_numel, expected_grid, block_sub)`：`axis_numel <= 0` → 1；否则 `total_subblocks = ceildiv(axis_numel, block_sub)`、`program_subblocks = ceildiv(total_subblocks, expected_grid)`、`effective_grid = ceildiv(total_subblocks, program_subblocks)`、返回 `ceildiv(axis_numel, effective_grid)`。`switch (grouped_group_id)` 只覆盖 `reachable_group_ids`；每 case 要求 `best_by_group[str(group_id)]` 存在（缺 → `RuntimeError("... missing winner ...")`），置 `grouped_variant_index = active_variants.index(variant_id)`；`policy["static_blocks"]` 逐个常量赋值；`policy["runtime_block_rules"]` **只支持 `op == "ceildiv"`**（其他 → RuntimeError），`axis_name` 不在 `axis_arg_indices` → RuntimeError，发射 `{block} = resolve_grouped_runtime_block({axis_arg}, {grid_target}, {block_sub});`；runtime_block_names 中有未赋值块 → RuntimeError；`default:` → `throw ... "resolved an unavailable group"`。Python 侧同名数学归[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)（`:3853-3890`）。

## 变体发射与单 kernel 装载/发射（`:344-521`）

- `_generate_grouped_variant_launch`（`:344-380`）：`switch (grouped_variant_index)`，每 active variant 以 kernel 变量 `grouped_kernel_{variant_id}` 走 `_generate_single_kernel_load` + `_generate_single_kernel_launch`（params = 原 params **合并**该变体 load_meta）；`default` → `throw ... "could not launch selected variant"`。
- `generate_grid`（`:382-419`）：grouped 分支按序调特征输入→group_id→选择；`numels` 取 `params["def_args"]` 中名字含 `_numel` 的项；**非分组**分支把 `params["runtime_blocks"]` dict 逐项发射 `int64_t {name} = {value};` 常量；`GridExprNpu.from_meta_and_set_numel(inductor_meta, params["config"], numels, "cpp")` 生成 grid 表达式（GridExprNpu 语义归[主线 Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)，`def` 锚 `:288-290`）；发射 `grid_0/1/2` 后 `if (grid_0 == 0 || grid_1 == 0 || grid_2 == 0) return;`。
- `generate_load_kernel`（`:421-430`）：grouped → 仅每 active variant 发射 `static void* grouped_kernel_{vid} = nullptr;`（实际装载延迟到 launch 分支内）；非分组 → 单装载。
- `_generate_single_kernel_load`（`:432-458`）：`if (kernel_var == nullptr)` 惰性装载一次。AOT 且 `embed_kernel_binary` → 用 `__{kernel_name}_start` 嵌入符号参数（mangled_name、**mix_mode**、shared_mem）；否则 cubin 路径参数（cubin_path、mangled_name、**mix_mode**、shared_mem、`cubin_dir_`）——注释原义 "add mix_mode into kernel load param"。
- `_generate_single_kernel_launch`（`:476-518`）：call_args **剥除 `triton_meta["constants"]`**（注释：C++ wrapper strips out equal_to_1 constants）；`arg_type_lookup` 对 `runtime_block_arg_names` 缺省补 `SymbolicCallArg`；`is_pure_simt` 与 `enable_simt = "simt" in parallel_mode or is_pure_simt` 均以 `npu_config.is_ascend950`（config `:40`）为门槛；`enable_auto_blockify = not has_auto_blockify_blacklist_op and triton_support_auto_blockify()`（utils `:114`）；args_decl 委托 `wrapper.generate_args_decl`，`kernel_params` 附加 `enable_auto_blockify`（注释：Triton-Ascend 的 auto-blockify 决策同时决定无序 sync-block 锁的参与者数——发射体归[姊妹卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)）；`launch_call` lambda 内联 args_decl + `generate_launch_preparation`，最终 `launchKernel(launch_call, "{kernel_var_name}")`；todo 注释：enable_kernel_profile 未支持。

## 相邻卡边界

[姊妹卡 CppWrapperNpu 类体](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)（`:522-1165`：CATLASS JIT dlopen、args_decl/launch_preparation 发射、设备 include）；[NPUSymbolicGroupedAutotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)（plan/load_meta 生产端）；[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)（grouped_candidate_plan/policy 构造与 Python 侧 resolve 数学）；[主线 precompile 管线卡](torch_npu_main_inductor_precompile_pipeline.md)（save_npu_kernel params 键 `:1323-1362`）；[主线 Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)（GridExprNpu）；[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)（runtime_block_arg_names/feature 生产端）；[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（发布三件套注册与主线类名差异）。

## 失效边界与静态口径

- 全部为静态源码事实：C++ 片段是发射模板文本的记录，未编译验证语法；未生成任何 wrapper。
- `resolve_grouped_runtime_block` 在 Python（归[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)读窗）与 cpp（本卡）是**两条独立实现**，同名同数学是源码事实，未做跨语言数值一致性验证；桶梯 `<=`（上界含）与 Python bucketize `(lower, upper]` 的区间对应是静态读码推断。
- `_patch_runtime_block_params` 对共享 `params` dict 的改写在 finally 恢复；若 `super().generate` 中途抛错，恢复仍执行（contextmanager 语义），但本卡未执行验证。
- params 键取值域由生产端 save_npu_kernel 决定，本卡只记录消费形态；release 无此文件，同名类属另一实现（见[发布版 cpp wrapper 旧一代实现卡](torch_npu_release_inductor_cpp_wrapper_legacy_codegen.md)），不能用本卡反推发布版行为。

## Evidence

- [主线 cpp_wrapper_npu.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py)（primary；`:1-521` 读窗（此前仅 rg 锚 113/257/319/389/424）；`:522-1165` 归姊妹卡）
- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（implementation；锚级：GridExprNpu `:288-290`、save_npu_kernel params 键 `:1323-1362`、`runtime_block_arg_names` 消费 `:309/:420/:469/:585/:665`，均 rg 定位；读窗归各 runtime 实现卡）
- [主线 _inductor/__init__.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation；注册锚 `:258/:263`，rg 定位）
- [发布版 codegen/cpp_wrapper.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_wrapper.py)（implementation；对照锚 `:65` 独立 dataclass DeferredNpuTritonCallWrapper、`:200` CppWrapperNpu(CppWrapperCpu)，sed 核对装饰器/基类行；主体归[发布版 cpp wrapper 旧一代实现卡](torch_npu_release_inductor_cpp_wrapper_legacy_codegen.md)）
