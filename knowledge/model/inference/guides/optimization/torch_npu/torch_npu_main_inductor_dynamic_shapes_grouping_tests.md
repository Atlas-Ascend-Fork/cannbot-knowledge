---
type: Guide
title: torch_npu 主线 inductor 动态形状分组测试契约：elementwise 负载分类、布局 kind 与 launch policy
description: 记录主线 test/_inductor/test_inductor_dynamic_shapes.py（314 行全文）的测试侧契约：group_workload 的 elementwise/None 分类（广播、独立 full、跨步重排均非 elementwise 但仍成组）、_pointwise_layout_kind 的 transpose/broadcast 判定与 _build_grouped_meta 的静态 split 轴/运行期块名/桶表（64-512 与 16-4096 两种）、默认 pointwise 特征按 vector core 推桶的公式、build_grouped_launch_policy 的静态块 grid_target=1 契约、_dynamic_pointwise_tiling_axis 单动态轴要求。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_inductor_dynamic_shapes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
created_at: '2026-11-12T13:41:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 inductor 动态形状分组测试契约：elementwise 负载分类、布局 kind 与 launch policy

## 固定版本与适用范围

主线 pin（ac0e1564）`test/_inductor/test_inductor_dynamic_shapes.py`（314 行全文）。同目录其余四个测试文件的验收契约分布持有：UB 重试见[precompile 流水线卡](torch_npu_main_inductor_precompile_pipeline.md)，开关分派与符号分组守门见[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)与[缓存 autotune 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)，costmodel 见[costmodel 与调试 autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)。模块级 `torch_npu.npu.is_available()` 为假即 `unittest.SkipTest`（`:22-23`）；全部用例带 `@runIfVersion(max="2.13")` 版本门。本卡只提炼**测试断言的实现契约**，被测实现归各实现卡：`SplitTiling._pointwise_layout_kind/_build_grouped_meta/_build_group_features/_dynamic_pointwise_tiling_axis`（split_tiling `:411/:865/:631/:388`，实现面归[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)与[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)）、`build_grouped_launch_policy`（triton_heuristics `:3728`，归[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)）、`group_workload` 元数据生产（triton.py `:1998/:2013/:2117`）。测试未运行（静态阅读）；draft、platforms 为空。

## `TestSymbolicGroupElementwise`：elementwise 负载分类（`:38-141`）

setUp 强制 `npu_config.enable_symbolic_shape_group_autotune = True`（保存旧值，tearDown 恢复并 `torch._dynamo.reset()`，`:44-50`）。`_run_and_check`（`:53-82`）：两套输入首维不同时对当前输入 `torch._dynamo.mark_dynamic(current, 0)`；eager 与 `torch.compile(backend="inductor")` 产物在两套形状上都要数值一致；然后在生成代码里断言同时含 `'group_enabled': True`、`'group_template': 'pointwise'` 与 `'group_workload': {expected!r}`——**expected=None 的用例同样要求代码成组**（元数据写 `'group_workload': None`），即负载分类只改 workload 标签、不改变是否成组。

| 用例 | 函数形态 | 期望 workload |
| --- | --- | --- |
| `test_basic_elementwise_workload`（`:84-97`） | `relu(x + y) * 0.5`，同形 (257,1031)/(263,1031) | `"elementwise"` |
| `test_broadcast_is_not_elementwise_workload`（`:99-107`） | `relu(x + bias) * 0.5`，bias (1031,) 广播 | `None`（仍成组） |
| `test_consumed_full_is_elementwise_workload`（`:109-117`） | `full_like` 结果被 `relu(x + generated)` 消费 | `"elementwise"` |
| `test_standalone_full_is_not_elementwise_workload`（`:119-126`） | 仅 `full_like(x, 2.0)` | `None` |
| `test_strided_reindex_is_not_elementwise_workload`（`:128-141`） | `relu(x[:, ::2] + y)` 跨步视图 | `None` |

分类实现（`_classify_group_workload`，split_tiling `:841`，实现归分组构造/轴选择卡）被钉的边界：广播、独立常量产生节点、非连续重排都排除出 elementwise；被消费的常量产生节点不破坏 elementwise。

## `TestPointwiseSymbolicGrouping`：布局 kind、meta 字段与桶表（`:144-306`）

半实例 `object.__new__(SplitTiling)` + SimpleNamespace kernel（类外契约风格）：

| 契约 | 断言 | 边界 |
| --- | --- | --- |
| transpose 判定（`:145-177`） | 轴 x0 静态 128（split）+ x1 动态 s0（tiling），indexing 成对 `[x1 + 128*x0, x0 + s1*x1]` → `_pointwise_layout_kind() == "transpose"`；meta：`primary_group_axis="x1"`、`static_split_axes=("x0",)`、`runtime_block_arg_names=("X0BLOCK",)`、特征 `source="axis"`、`axis_names=("x1",)`、**buckets `(64, 128, 256, 512)`** | 桶表在 `sizevars.size_hint/optimization_hint` patch 为 64 下取得（`V` patch 到 split_tiling 模块）；即 transpose 轴特征桶是 hint 的 1×/2×/4×/8× 阶梯 |
| broadcast 判定（`:179-210`） | indexing `[x0, x0 + 128*x1]` → `"broadcast"`；meta 特征 `name="pointwise_broadcast_axis"`、**buckets `(16, 64, 256, 1024, 4096)`**；`_build_group_features(None, tiling_axis, "transpose_broadcast")` 组合后仍保留该广播轴特征与同桶表 | 广播轴桶表是 16→4096 的 ×4 阶梯，独立于 sizevars hint |
| 默认 pointwise 特征（`:212-252`） | 单动态轴 `_build_group_features(None, axis, dynamic_split_axes=(axis,))` → 恰一特征 `name="pointwise"`、`source="outer_product"`、`axis_names=("x0",)`；**桶表按 vector core 公式**：`lower = max(1024, next_power_of_2(2*vc))`、`upper = max(next_power_of_2(8*vc), 4096*vc)`，`upper//lower > 8` 时再插 `min(next_power_of_2(lower*8), next_power_of_2((upper+1)//2))`，去重排序 | `next_power_of_2` 经 split_tiling 模块取自 torch 上游 `runtime_utils`（split_tiling `:8` import）；`num_vector_core` 是 config 的 PEP 562 惰性属性（config `:128-134`，fork 编译子进程安全） |
| 纯 pointwise 不走 tiling 后备（`:254-271`） | 单条 indexing `[x1 + 128*x0]`（无成对转置结构）→ `_build_grouped_meta()` 返回 None | 成组要求特定布局结构，不是所有动态 pointwise 都建 meta |
| launch policy 静态块契约（`:273-290`） | patch `triton_heuristics.config_to_dict` 返回 `{"kwargs": {"X0BLOCK": 32, "X1BLOCK_SUB": 64}}` 后 `build_grouped_launch_policy(group_id=0, cfg=object(), runtime_block_arg_names=("X0BLOCK",), group_features=(), primary_group_axis="x1", primary_feature_index=0, axis_env={"x0": 128, "x1": 64}, npu_num_vector_core=32)` → `static_blocks == (("X0BLOCK", 32),)`、`runtime_block_rules == ()`、**`grid_target == 1`** | 主组轴 x1 在 axis_env 是静态 64：静态切分轴的块保持常量、无运行期规则、网格目标 1；`X1BLOCK_SUB` 不出现在 policy（子块不进 static_blocks/runtime 规则面）。policy 数学归 launch policy 卡 `:3728-3850` |
| tiling 后备单动态轴（`:292-306`） | 两个动态 tiling 轴、无 split 轴 → `_dynamic_pointwise_tiling_axis()` 返回 None | 动态 pointwise tiling 后备只在恰一动态轴时可用（与 docs 契约"单一动态轴"互证，见[动态形状选择卡](torch_npu_inductor_dynamic_shape_choices.md)） |

## 相邻卡边界

[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)（`_pointwise_layout_kind` 所在文件的常规选择面与发布版对照）；[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)（`_build_grouped_meta` 构造族实现 `:631/:865`）；[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)（`build_grouped_launch_policy` 实现体）；[NPUSymbolicGroupedAutotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)（plan 消费端）；[precompile 流水线卡](torch_npu_main_inductor_precompile_pipeline.md)、[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)、[costmodel 与调试 autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)与[缓存 autotune 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（同目录另四件测试文件的 UB 重试/开关分派/costmodel/符号分组守门验收契约）；[动态形状选择卡](torch_npu_inductor_dynamic_shape_choices.md)（docs 契约面）；[CostModel 与分组指南](torch_npu_inductor_costmodel_and_shape_groups.md)。

## 失效边界与静态口径

- 本卡全部为测试文件静态阅读，**未运行任何测试**；断言与实现的"对应"仅指语义契合，不等于测试当前可跑或通过（依赖设备、torch 版本与 `runIfVersion(max="2.13")` 门）。
- 桶表 `(64,128,256,512)`、`(16,64,256,1024,4096)` 与 vector-core 公式是该测试在 ac0e1564 的**期望值**，随版本可能变化，以实现源码为准；transpose 桶依赖 sizevars hint 的推断（1×/2×/4×/8× 阶梯）是从期望值+patch 值归纳，未对照桶生成实现体反推。
- 半实例（`object.__new__`）钉的是类外接口契约，不覆盖 `__init__` 依赖；`test_tiling_primary_keeps_static_grid_block` mock 了 `config_to_dict`，不覆盖真实 cfg 序列化路径。
- `group_workload` 生产端（triton.py `:1998/:2013/:2117`）只做锚级 rg 定位，本体不在本卡逐行范围；发布 pin 无分组符号（负向 rg），本卡事实不外推发布版。

## Evidence

- [test/_inductor/test_inductor_dynamic_shapes.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_inductor_dynamic_shapes.py)（primary；`:1-314` 全文）
- [主线 codegen/split_tiling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py)（implementation；被测符号 def 锚 `:388/:411/:631/:865/:841` 与 `next_power_of_2` import `:8`，rg 定位；函数体归[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)与[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)读窗）
- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（implementation；`build_grouped_launch_policy` def 锚 `:3728`，函数体归[分组配置/launch policy 卡](torch_npu_main_inductor_grouped_config_and_launch_policy.md)读窗）
- [主线 _inductor/config.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation；`enable_symbolic_shape_group_autotune` 锚 `:377`；惰性核数窗 `:120-134`）
- [主线 codegen/triton.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py)（implementation；`group_workload` 生产锚 `:1998/:2013/:2117`、开关门 `:2200`，`:2196-2202` 定向核对；周边函数体不在本卡范围）
