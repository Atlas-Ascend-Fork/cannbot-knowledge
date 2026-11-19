---
type: Guide
title: torch_npu 发布版 SplitTiling 简化实现：split/tiling 选择器函数体、possible_need_permute 与最低维推导
description: 记录发布 pin 独有的 codegen/split_tiling.py（283 行全文）：select_split_axis 的核数/三轴停止条件与两级回退、select_tiling_axis 的多规约停止与 80% 覆盖/permute/max_transpose_dims=2 门槛、should_outer_reduce_me 的 32768 高阶规约轴改写、find_lowest_dimension 的输入 LOAD 索引（含 STORE）收集与 stride-1 系数判定、convert 族用 var_to_val 代换——与主线版的代换键与消费时点差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/split_tiling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/scheduling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py
  role: implementation
created_at: '2026-11-12T13:41:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 SplitTiling 简化实现：split/tiling 选择器函数体、possible_need_permute 与最低维推导

## 固定版本与适用范围

发布 pin（f3ecfe4a）自有 `codegen/split_tiling.py`（283 行）。[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)持其 `:1-72`（类头、`find_possible_permutes`、`key`、`total_split_numels`）与主线↔发布结构对照，本卡覆盖 `:73-283` 函数体，两卡拼合即为该文件全文。消费时点：发布版在 **scheduling 期**由 `codegen/scheduling.py:448-450` 调 `SplitTiling(kernel)` + `select_split_tiling_axis()` 并回填 `kernel.load_store_indexing`（`:440-455` 复核窗），主线版在 kernel codegen 期由 triton.py 调用（结构对照归轴选择卡）。发布版无 `select_no_loop_axis`、无分组符号（负向 rg）；`find_possible_permutes`/`possible_need_permute` 在主线全树零命中（主线独缺）。纯静态阅读；draft、platforms 为空。

## `select_split_axis`（`:73-115`，原则注释 `:69-72`）

门槛→动作：停止条件 `total_split_numels(split_axis) >= num_vector_core` **或** 已选 3 轴（`:77-82`）。逐轴选择先跳过 `prefix == "r"` 的规约轴与 `sorted_order in kernel.low_dims` 的低维轴（`:84-94`，与注释"原则3：规约轴和低维轴不应选为切分轴"对应）；首轮选不到 → 第二轮放开低维限制再选；`count > 10` 熔断防死循环（`:96-108`）。全空且有轴 → 兜底取 `sorted_axis[0]`（`:110-111`）；最后按 `key` 逆序排并写 `split_order`（`:113-115`）。`total_split_numels`（`:64-67`）直接乘 `x.length`——不做主线版 `get_length_val` 的 backed_var 代换（差异锚，见轴选择卡）。

## `select_tiling_axis`（`:123-169`，原则注释 `:117-120`）

- 停止条件一（`:132-134`）：规约轴数 > 1 且全部规约轴已入 tiling → 停（注释：多维规约只有规约轴可作 tiling 轴）。
- 停止条件二（`:136-139`）：`(possible_need_permute or tiling_numel / total_numel >= 0.8) and len(tiling_axis) >= min(max_transpose_dims, len(sorted_axis))`——`max_transpose_dims = 2`（注释原义 "currently, the maximum dim that triton-ascend support is 2"），80% 覆盖率与 permute 疑似都提前收口。
- 选择两轮（`:142-166`）：第一轮 `select_tiling(low_dim=True, reduction=True)` 只收低维轴与规约轴（`:144-149`，原则1/2）；未达停止 → 第二轮 `select_tiling(low_dim=False, reduction=False)`。**注意 `:150-151` 的 `if low_dim or reduction: continue`** 使后续"原则4 取最长轴"分支（`:152-158`）在当前源码形态下**不可达**（`find_longest_dimension` 调用在 `:153` 被注释保留）——长轴补充只作为意图注释存在，实际行为是两轮固定模式 + `count > 10` 熔断。
- 收尾按 `key` 逆序排并写 `tiling_order`（`:167-169`）。

## 外层规约改写与最低维推导（`:171-250`）

- `select_split_tiling_axis`（`:171-173`）：先 split 后 tiling 的总入口。注释 `:175` 自述局限：两个规约轴只需一个外层规约时逻辑失效。
- `should_outer_reduce_me`（`:176-183`）：`kernel.is_higher_order_reduction(True)` 且轴长 `> 32768` 且 `is_loop` → 置 `should_outer_reduce`，并**把 `kernel.split_axis` 从列表整体替换为该轴对象**（`split_axis = x`，类型改写）——主线版同函数在 `:969` 有同型改写（轴选择卡已记），32768 阈值两侧同源。
- `find_longest_dimension`（`:185-191`）/`is_lowest_dimension`（`:194-195`）：纯遍历最长轴与 `low_dims` 成员判定（当前源码里前者只被 `:153` 注释引用）。
- `find_lowest_dimension`（`:197-250`）：先收集索引表达式——规约核只收 **外部输入的 LOAD 索引**（`read_is_inptr` 规则 `:226`：`arg[:3] != 'arg' and arg in buf_names` 时视为节点中间缓冲而排除，即只取 `arg` 开头的外部输入与不在调度图 buffer 名单里的读）；非规约核再补 STORE 与 STORE_REDUCTION 索引（`:237-248`）。`construct_low_dim`（`:198-211`）对每个索引的 `as_coefficients_dict()` 中**系数恰为 `sympy.Integer(1)` 且符号在 range_tree_nodes** 的轴加入 `low_dims`（`:208-210`）——即 stride-1 轴判定。与主线版（全索引 stride-1 判定，轴选择卡 `:961-1087` 尾段）语义同型，但收集面（输入 LOAD 优先、外部输入过滤规则）是发布版特有形态。

## 比较工具与排序键（`:252-283`、`:53-62`）

- `convert`（`:252-268`）：非 Integer 表达式先 `subs(V.graph.sizevars.var_to_val)` 再比；单侧 int 与 `sympy.Integer` 互相提升。`less_than/great_than/ge_than`（`:270-283`）都是 convert 后比较。**主线版用 `backed_var_to_val`**（轴选择卡 `:1056-1087`）——代换键差异是两版最具体的代沟锚。
- `key`（`:53-62`）：`w/v/t` 前缀轴名映射为 `"zz"+name` 排到最后（优先级高于 x/y）；`ModularIndexing` 表达式轴名插 `"0"` 降序（低于 floor_dir）；其余按名。两版同源（轴选择卡已记）。

## 相邻卡边界

[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)（主线版五原则/80% 核数门/三轴上限/no_loop 4KB 阈值 + 两版结构对照，持有 `:1-72` 已读面）；[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)（主线分组改写面，发布版无）；[发布版 TileGenerator 卡](torch_npu_release_flat_inductor_tile_generator_descents.md)（发布 tile_generator.py 是另一消费 family）；[发布版接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（scheduling 消费链语境）。

## 失效边界与静态口径

- 全部为发布 pin 静态源码事实：选择器、最低维推导均未执行；"不可达代码"判断（`:150-158`）按控制流静态读出，未做字节码/AST 级验证，也可能被后续版本改动。
- 80% 覆盖率、`max_transpose_dims=2`、32768、10 轮熔断是发布 pin 的常量事实；主线版对应门限不同（核数 80% 效率门、no_loop 4KB 等），不可互相外推。
- `possible_need_permute` 只作为 tiling 停止条件与调度提示被记录；permute 是否真的发生、如何发生不在本文件（本卡未追 scheduling.py 其余面）。
- 主线↔发布同名函数的行为差异结论限定本卡与轴选择卡已读行段；主线版不在已读行段内的部分（如有）不参与对照。

## Evidence

- [发布版 codegen/split_tiling.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/split_tiling.py)（primary；`:1-283` 全文，`:1-72` 对照面归主线轴选择卡）
- [发布版 codegen/scheduling.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/scheduling.py)（implementation；消费锚 `:448-450`，`:440-455` 复核窗；调度器其余面不在本卡范围）
- [主线 codegen/split_tiling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py)（implementation；对照锚 `:969` split_axis 类型改写、`:1056-1087` convert/backed_var_to_val——归[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)读窗）
