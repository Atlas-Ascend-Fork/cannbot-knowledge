---
type: Guide
title: torch_npu 主线 legacy 候选生成与五个装饰器入口
description: 记录主线 runtime/triton_heuristics.py 的 _triton_config_npu_index_legacy 主体（fasta/TileGenerator 二选一、SIMD_SIMT_MIX 双遍 extend、零配置回退、split_axis/split_blocks 镜像注入、requires_no_linear_block_remap 重映射、set_reduction_runtime_blocks_to_numel 与 brutal_prune 收尾）与 pointwise/reduction/persistent_reduction/template/foreach 五个装饰器入口的参数、门槛与 HeuristicType 去向。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton_combo_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py
  role: evidence
created_at: '2026-11-12T13:41:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 legacy 候选生成与五个装饰器入口

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py`（4160 行）的候选生成主体与装饰器入口：`_triton_config_npu_index_legacy` 主体（`:3893-3977`，含收尾三件 `:3378-3412`）与五个装饰器入口（`:3999-4129`）。入口的生成侧发射契约（模块别名绑定、`_get_heuristic`、combo/template 发射）归[发射卡](torch_npu_main_inductor_decorator_emission_consumers.md)；决策树 autotuner 选择归[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；`triton_config_npu_index` 分发门与分组路径在代表形状上回调本主体（`:3537`）归[分组配置卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)；TileGenerator/FastATileGenerator 下降本体归[TileGenerator 下降卡](torch_npu_release_flat_inductor_tile_generator_descents.md)；precompile 串/并行门归[precompile 卡](torch_npu_main_inductor_precompile_pipeline.md)。发布 pin（f3ecfe4a）`find torch_npu -name triton_heuristics.py` 零命中；发布版对应入口（`pointwise_npu_index` 等，`:1177-1396` 薄包装、回退 `Config num_warps=1, num_stages=1`）归[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)。纯静态阅读；draft、platforms 为空。

## legacy 候选生成主体（`:3893-3968`）

头部（`:3900-3913`）：`num_warps=1`、`num_stages=2`（`:3900-3901`）**只被零配置回退的 Config 使用**，正常路径的 num_warps/num_stages 由生成器输出自带；必选键 `split_axis/tiling_axis/low_dims/split_axis_dtype/axis_names/dual_reduction` 直取（`:3903-3909`，缺即 KeyError），`no_loop_axis` 唯一可选（`.get` 缺省 `[]`，`:3905`）；`triton_meta["signature"]` 在 `:3910` 无条件索引——`:3911` 的 `if triton_meta is not None` 是**死守卫**（None 到不了该行）；`input_ptr_num` 按签名键名含子串 `'ptr'` 计数；`npu_kernel_type` 缺省 `"simd"`（`:3912`）；`size_hints` 被覆写为按 `axis_names` 对齐的 list（`.get` 缺省 1，`:3913`）——**实参必须是 mapping**（生成侧 `get_size_hints` 多轴返回 dict；空 range tree 返回 list 的形态若与 axis_names 非空同时出现会 AttributeError，该组合未在静态上排除）。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `_use_fasta_autotune(inductor_meta, is_reduction or is_persistent_reduction)` 为真（`:3915`） | 函数内延迟 `from .fasta_autotune import FastATileGenerator`（`:3916`）构造并 `configs = descend_split_tiling()`（赋值，`:3917-3922`） | 第二实参是两种规约标志的 OR：pointwise 恒 False、reduction/persistent_reduction/foreach 恒 True；门槛条件本体归[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（决策树 row 2） |
| 否则构造 `TileGenerator`（`:3924-3928`） | `npu_kernel_type == SIMD_SIMT_MIX` 时：同一 tile_generator 先 `set_kernel_type(SIMT_ONLY)` extend 一遍结果、再 `set_kernel_type(SIMT_TEMPLATE)` extend 一遍（`:3929-3933`）——混合候选是两段序列的**拼接**；其余 kernel_type 单次 `configs = descend_split_tiling()`（`:3935`） | 下降算法与预算归[TileGenerator 下降卡](torch_npu_release_flat_inductor_tile_generator_descents.md) |
| `configs` 为空（`:3937`） | 零配置回退：split 轴 `{AXIS}BLOCK = size_hints[x]`、tiling 轴 `{AXIS}BLOCK_SUB = size_hints[x]`，两类都空时 `{"dummy": 1}`；`Config(cfg, num_warps=1, num_stages=2)` 追加（`:3938-3946`） | 主线 `num_stages=2`，发布版同位置是 `num_warps=1, num_stages=1`（发布版接线卡） |
| 恒定（生成后） | 镜像注入：对每条 cfg 按 split_axis 顺序取 `cfg.kwargs["{AXIS}BLOCK"]` 组 `split_blocks`，随后注入 `split_axis`、`split_blocks` 两个 tuple kwargs（`:3948-3955`）——**运行期 BLOCK 值镜像进 split_blocks** | 块名缺失即 KeyError：回退路径保证覆盖所有 split 轴名；生成器输出契约归 TileGenerator 下降卡。strip helper `:3994-3996` 注释原义 "legacy tiling configs mirror runtime BLOCK values in split_blocks" 即此镜像；分组路径按该事实在 strip 时连弹 `split_blocks`（[分组配置卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)） |

## 收尾三件（`:3378-3412` 与 `:3970-3977`）

| 门槛 | 动作 | 边界 |
| --- | --- | --- |
| env `FAST_RUN_WITH_MAX_TILING_NUM`（默认 `"-1"`，int 失败按 -1）解析出 `max_num > 0` 且候选更多（`:3378-3387`） | `configs = configs[-max_num:]`——**保尾部**丢头部，debug 日志记裁剪后数量（`:3388-3390`） | 非正数（含解析失败）恒不裁剪 |
| `runtime_block_arg_names` 非空（`:3393-3396`） | `set_reduction_runtime_blocks_to_numel`：轴名以 `"r"` 开头且 `{AXIS}BLOCK` ∈ runtime_block_arg_names 的 cfg 键被整体置为 `size_hints[axis]`（=轴 numel，`:3398-3406`）；随后若 cfg 有 `split_blocks` 则按当前 BLOCK 值重算镜像（`:3408-3412`） | 轴名前缀是字符串判据 `"r"`，非规约标志推导 |
| `inductor_meta.get("requires_no_linear_block_remap") is True`（严格 True，`:3970-3972`） | `_remap_fallback_block_subs`：每条 cfg 的每个 `"_SUB"` 后缀键值搬到 `removesuffix("_SUB")` 键名（已存在同名键则**后写覆盖**）、弹出原键（`:3973-3977`） | 同一 flag 在 `_precompile_config` 另并入 `enable_auto_blockify: True`（[precompile 卡](torch_npu_main_inductor_precompile_pipeline.md) `:1212-1220`）；truthy 非 True（如 1）不触发 |

`logging.debug` 记 kernel_name 与候选计数（`:3962-3964`）；`return configs`（`:3968`）。

## 五个装饰器入口（`:3999-4129`）

全部先经 `triton_config_npu_index` 分发（`:3415-3442`：`group_enabled` 真先拒 `extra_launcher_args` 再进分组，否则进本卡 legacy 主体），再落 `cached_autotune` 的五分支决策树（[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)）。发射侧如何把 `@triton_heuristics.{heuristics}` 写进生成代码见[发射卡](torch_npu_main_inductor_decorator_emission_consumers.md)。

| 入口 | 关键参数 | 动作 | 失败/版本边界 |
| --- | --- | --- | --- |
| `pointwise`（`:3999-4017`） | `tile_hint=None`、`min_elem_per_thread=0` **收下即弃** | `triton_config_npu_index(size_hints, inductor_meta, triton_meta)` 产候选 → `cached_autotune(..., HeuristicType.POINTWISE, filename)` | 生成侧确实传入这两个参数（发射卡 `:2528-2541`），但不参与本函数任何行为 |
| `reduction`（`:4019-4048`） | `reduction_hint` | **原地写 `inductor_meta["reduction_hint"]`**（`:4028`）；`triton_meta is None` → `raise RuntimeError("assert triton_meta is not None")`（`:4029-4030`）；`is_reduction=True` → `HeuristicType.REDUCTION` | 五入口中唯一硬前置失败；docstring 原义 "args to @triton.heuristics()"；候选以 `[*configs]` 单元素展开传入 |
| `persistent_reduction`（`:4050-4075`） | `reduction_hint` | 同样原地写 reduction_hint；`is_reduction=True` 且 `is_persistent_reduction=True` → `HeuristicType.PERSISTENT_REDUCTION`；configs 直传 | **无** `triton_meta` None 检查（与 reduction 的静默差异） |
| `template`（`:4078-4104`） | `num_consumer_groups`、`num_buffers_warp_spec`、`**kwargs` 全部吞掉 | `cached_autotune(None, [triton.Config({}, num_stages=…, num_warps=…)], triton_meta, inductor_meta, HeuristicType.TEMPLATE, filename)`——**size_hints 恒 None**，单条空 kwargs Config 携带 num_warps/num_stages | 本仓发射面不传 filename（发射卡 `:1203-1211`），形参保持默认 None；上游兼容参数仅占位 |
| `foreach`（`:4107-4128`） | `num_warps` **收下即弃** | 与 persistent_reduction 同参产候选（`is_reduction=True`、`is_persistent_reduction=True`，`:4113-4119`）→ `cached_autotune(size_hints, configs, ..., HeuristicType.TEMPLATE)` | HeuristicType 复用 TEMPLATE 但**保留 size_hints**：precompile 侧据此区分——`is_template = TEMPLATE 且 size_hints is None`，template 恒串行、foreach 保 vector configs 并行（`:843-848` 注释原义，[precompile 卡](torch_npu_main_inductor_precompile_pipeline.md)） |

## 候选生成稳定性验收契约（test_autotune_switch.py）

`TestAutotuneCandidateGeneration`（静态阅读，未运行）钉死：`triton_config_npu_index` 在四种 max 旗标/env 组合、`autotune_pointwise` 开关、grouped 与非 grouped、simt_only/simt_template/simd_simt_mix 各 kernel_type 下候选集与基线全等（`hash_configs` 相等；断言依赖 torch 上游 `hash_configs`）；`simt_only` 的 num_warps 恒 `{8,16,32,64}`、非 simt_only 的 multibuffer 恒 `{False,True}`（这两个集合值是测试期望值，随版本可能变化，以源码为准）——即 max-autotune 开关只影响是否启用额外生成路径，不缩水既有候选。grouped 计划内部一致性断言由[分组配置卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)持有。

## 失效边界与静态口径

- 本卡不持有：决策树条件（补丁链卡）、TileGenerator/FastATileGenerator 下降本体（TileGenerator 下降卡）、分组候选计划构造与 strip helper（分组配置卡）、precompile 并行语义（precompile 卡）、发射契约（发射卡）——只互链。
- `reduction_hint` 的原地写入意味着装饰器执行时会修改生成代码持有的 inductor_meta 字面量；该值的下游消费未在本卡范围。
- 发布 pin 无 `runtime/` 目录，五个入口全部主线独有；不与发布版 `pointwise_npu_index` 等薄包装互推。
- 纯静态阅读：未运行任何配置生成、autotune 或编译；候选多少/优劣不做量化判断。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:3893-3977`、`:3999-4129`；定向 `:3378-3412`、`:843-848`、`:3415-3442`）
- 消费锚 rg 实查：`codegen/triton.py:57/:80/:911/:1006`、`triton_combo_kernel.py:64-68/:126-137`、`select_algorithm.py:1203-1211`（详见[发射卡](torch_npu_main_inductor_decorator_emission_consumers.md)）。
- 发布 pin 负证据：`find torch_npu -name "triton_heuristics.py"` 零命中（实查）。
- canonical 去重 rg：`_remap_fallback_block_subs|set_reduction_runtime_blocks_to_numel` 零命中；`_triton_config_npu_index_legacy` 其余仅边界提及（[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)/[TileGenerator 下降卡](torch_npu_release_flat_inductor_tile_generator_descents.md)）。
- [test_autotune_switch.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py)（evidence；全文 531 行静态阅读，候选生成断言见『验收契约』节）
