---
type: Guide
title: torch_npu 主线分组候选计划构造：triton_config_npu_index_grouped 与 launch policy 数学
description: 记录主线 runtime/triton_heuristics.py 的分组配置生成链：triton_config_npu_index 的 group_enabled 分发与 extra_launcher_args 拒绝、_triton_config_npu_index_grouped 的特征参数索引/代表 size hints 上的 legacy 候选生成/变体去重/policy 逐候选构造与计划装配、build_grouped_launch_policy 的主轴 tiling 分支与 split 分支（prior_programs、开桶核数目标、representative_numel+max_grid 规则）、resolve_grouped_runtime_block 的 ceildiv 块值数学。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py
  role: evidence
created_at: '2026-11-12T13:18:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线分组候选计划构造：`_triton_config_npu_index_grouped` 与 launch policy 数学

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/triton_heuristics.py`。本卡持有分组配置生成链：`triton_config_npu_index` 分发头（`:3414-3442`）、`_triton_config_npu_index_grouped`（`:3444-3649`）、`build_grouped_launch_policy`（`:3728-3850`）、`resolve_grouped_runtime_block`（`:3853-3890`），另定向读 `strip_runtime_blocks_from_cfg`（`:3980-3997`，legacy 段内）。该链产出的 `grouped_candidate_plan` 由[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)在运行期消费；代表/桶语义由[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)持有；非分组 `build_candidate_plan`（`:3683-3726`）由[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)持有；`_triton_config_npu_index_legacy` 主体（`:3893-4129`）由[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)持有。发布 pin（f3ecfe4a）全树 rg `grouped_candidate_plan|_triton_config_npu_index_grouped|build_grouped_launch_policy|resolve_grouped_runtime_block` 零命中（负证据，含 test/）；主线侧 `test/_inductor/test_inductor_dynamic_shapes.py:277` 调用 `build_grouped_launch_policy`，其测试契约由[动态形状分组测试卡](torch_npu_main_inductor_dynamic_shapes_grouping_tests.md)承载。纯静态阅读；draft、platforms 为空。

## 分发门（`:3414-3442`）

`triton_config_npu_index(size_hints, inductor_meta, ...)`：`inductor_meta["group_enabled"]` 真 → **先拒绝 `extra_launcher_args`**（raise：当前自动生成 Triton 分组 autotune 流不支持该路径）再进 `_triton_config_npu_index_grouped`；否则落 `_triton_config_npu_index_legacy`。

## `_triton_config_npu_index_grouped`（`:3444-3649`）

1. **特征参数索引**（`:3451-3485`）：每个轴的 `{axis}_numel` 必须在 `triton_meta["signature"]` 里（缺则 raise）；每个特征的源只接受 `primary_axis/axis/outer_product/reduction_product`（v1），`axis` 类源要求恰好一轴。产出 `feature_arg_indices`（供运行期取特征值）与 `axis_arg_indices`（供运行期取轴 numel）。
2. **代表重构造**（`:3487-3499`）：再跑一次 `build_group_representatives`；抛 `UnsupportedGroupedPlan` 时转 raise「invalid grouped autotune plan reached runtime config; the current grouped codegen guard should have rejected this plan earlier」——**运行期兜底是 fail-closed**，依赖 codegen 侧守卫（[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md) `:2476`）先拒。
3. **主轴块名**（`:3500-3509`）：`primary_group_axis` 缺失 raise；`{AXIS}BLOCK` 可以**合法缺席** `runtime_block_arg_names`——主轴是规约 TILING 轴时按 `R0BLOCK_SUB` 逐变体分桶、无 grid block，grid 来自静态非规约 split 轴（注释原义，`build_grouped_launch_policy` 两形态都处理、此处不设守卫）。
4. **逐组候选生成**（`:3511-3589`）：`base_size_hints` 按轴名取 `size_hints`（缺省 1），叠加该组 `benchmark_axis_env` 得**代表 size hints**；每个可达组调 `_triton_config_npu_index_legacy(代表 size hints, ...)` 生成 legacy 配置——**分组候选 = 在每个代表形状上跑一遍常规配置生成器**。每个 legacy cfg 经 `strip_runtime_blocks_from_cfg`（剥离 runtime block 键、镜像 `split_blocks`，`:3980-3997`）后按 `repr(config_to_dict(...))` 去重为编译变体（`v{idx}`）；每个 (组, 变体) 生成 policy（`p{group}_{variant}`，legacy 配置数 >1 时再缀 `_{variant_idx}`——同一变体在不同组/不同枚举位可有不同 policy）；候选去重键 `(variant_id, static_blocks, runtime_block_rules, grid_target)`（`:3569-3577`）；候选 id `g{group}_c{idx}`，`full_config` 保留完整 legacy cfg 字典。
5. **计划装配**（`:3591-3648`）：variants/variant_order/candidate_entries/group_to_candidates/policies/runtime_block_append_order/group_id_count/reachable+unreachable_group_ids/group_features/axis+feature_arg_indices/feature_sources/benchmark_{feature_inputs,axis_values}_by_group/ordered-tensor-size-workspace-extra_launcher arg_specs（后五类 spec 直接从 inductor_meta 透传）；写回 `inductor_meta["grouped_candidate_plan"]`（cpp wrapper 侧消费锚 `cpp_wrapper_npu.py:113/389/424`）；`log.info` 汇总组数/可达数/候选数/每组候选数。返回值只有 `variant_configs`（编译用变体配置，去重后的）——**legacy 配置的全量信息在 plan 而不在返回值**。

## `build_grouped_launch_policy`（`:3728-3850`）

输入：`group_id`、完整 legacy cfg、runtime_block_arg_names、group_features、`primary_group_axis`、`primary_feature_index`（`find_primary_feature_index` symbolic_grouping `:176-184`）、该组 `axis_env`、`npu_num_vector_core`。

| 分支 | 条件 | 产出 |
| --- | --- | --- |
| 主轴为 TILING 轴 | `primary_block_name not in runtime_block_arg_names` | **无 runtime 规则**：`static_blocks` = cfg 中全部 runtime block 键值，`runtime_block_rules=()`，`grid_target=1`（注释原义：grid==1 横跨主轴，任何 grid 并行来自静态非规约 split 轴；纯标量规约空 static_blocks 与部分规约带静态 split 轴两形态都覆盖） |
| 主轴为 split 轴 | 其余 | 先累积 `prior_programs = Π ceil(axis_env[非主 split 轴] / static_block)`（缺轴 raise）；主块/主 subblock（`{AXIS}BLOCK_SUB`）缺失或非正 raise；**开桶组**（`is_open_bucket_group`，主特征桶号 == len(buckets)）`grid_target = max(1, num_vector_core // prior_programs)`，**闭桶组** `grid_target = max(1, ceil(代表轴 numel / 主静态块))`；单条 runtime 规则 `(主块名, (("op","ceildiv"), ("axis_name",主轴), ("block_sub",主sub块)))`，主特征名 ∈ {pointwise, elementwise_numel, outer, reduction} 时追加 `("representative_numel", 代表轴 numel)` 与 `("max_grid", max(1, num_vector_core // prior_programs))`——注释原义：主轴是唯一 grid 并行来源，缺它则代表以下的形状都继承代表的 grid、每个 program 走代表的行数而非自己的 |

## `resolve_grouped_runtime_block`（`:3853-3890`）

运行期块值数学（Python 侧实现；cpp wrapper 生成代码内 emit 同名 C++ 函数，`cpp_wrapper_npu.py:257/319`）：`expected_grid<=0`/`block_sub<=0` raise；`axis_numel<=0` → 1；`total_subblock_num = ceil(axis_numel / block_sub)`。**小于代表**（`representative_numel`/`max_grid` 都给出且 `axis_numel < representative_numel`）：`program_subblock_num = ceil(total_subblock_num / max(1,max_grid))`，返回 `program_subblock_num × block_sub`——小形状可以用比代表更多的 program，同时 BLOCK 保持对齐编译期 BLOCK_SUB（注释原义）。**否则**：`program_subblock_num = ceil(total_subblock_num / expected_grid)`，`effective_grid = ceil(total_subblock_num / program_subblock_num)`，返回 `ceil(axis_numel / effective_grid)`。

## 计划一致性验收契约（test_autotune_switch.py）

`TestAutotuneCandidateGeneration` 的 grouped 用例（静态阅读，未运行）钉死计划内部一致性：候选的 `variant_id`/`policy_id` 必在 plan 的 `variants`/`policies`、`selection_key == 组号`、`sum(len(g)) == len(candidate_entries)`（`g` 为按组收集的候选表）；四种 max 旗标/env 组合、`autotune_pointwise` 开关与各 kernel_type（simt_only/simt_template/simd_simt_mix）下 grouped 与非 grouped 候选集均与基线全等（`hash_configs` 相等，断言依赖 torch 上游 `hash_configs`）。

## 失效边界与静态口径

- `npu_num_vector_core` 取调用时的 `npu_config.num_vector_core`（设备/`NPU_DEVICE_LIMIT` 惰性解析，数值未验证）；policy 里的 `grid_target`/`max_grid` 由此推导，设备更换后不重算（静态口径）。
- `variant_idx` 缀入 policy_id 意味着同一编译变体可携带多个 policy/候选（不同组的代表形状不同）；候选去重键含 policy 内容（static_blocks/rules/grid_target），完全相同的 (变体, 策略) 只留一个。
- 代表 size hints 进入 `_triton_config_npu_index_legacy` 后的候选枚举细节由[legacy 候选生成卡](torch_npu_main_inductor_legacy_config_and_decorator_entries.md)持有；本卡只持「分组候选 = 代表形状上的 legacy 生成」这一调用事实与分组侧装配。
- `config_to_dict`/`config_from_dict`/`write`/`split_aot_inductor_output_path` 为外部 helper，未逐行读；`find_primary_feature_index` 主轴不在特征中时 ValueError（symbolic_grouping `:176-184`），本链上层是否总是先构造特征未验证。
- 本卡全部结论来自两 pin 静态阅读；未运行任何配置生成或 policy 计算。

## Evidence

- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（primary；读窗 `:3414-3442`、`:3444-3649`、`:3728-3850`、`:3853-3890`，定向 `:3975-3998`）
- [主线 runtime/symbolic_grouping.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py)（implementation；`build_group_representatives` `:203-354`、`find_primary_feature_index` `:176-184`、`is_open_bucket_group` `:186-196`）
- [主线 codegen/cpp_wrapper_npu.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/cpp_wrapper_npu.py)（implementation；rg 消费锚 `:113`/`:257`/`:319`/`:389`/`:424`，主体未读）
- [test_autotune_switch.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_switch.py)（evidence；全文 531 行静态阅读，计划一致性断言见『验收契约』）
