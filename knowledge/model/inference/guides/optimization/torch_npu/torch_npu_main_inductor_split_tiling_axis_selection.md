---
type: Guide
title: torch_npu 主线 split_tiling 常规轴选择：split/tiling/no_loop 原则、最低维推导与比较工具
description: 记录主线 codegen/split_tiling.py 的非分组选择面（分组构造族之外的常规选择面，与分组构造卡拼合即为该文件全文）：select_split_axis 的五条原则与停止条件（符号分组提前停、核数覆盖 80% 效率门、三轴上限、动态全规约保 grid==1）、select_tiling_axis 的低维/规约轴覆盖、select_no_loop_axis 的 4KB 阈值与动态轴排除、find_lowest_dimension 的全索引 stride-1 判定、should_outer_reduce_me 的 split_axis 类型改写、convert/less_than/great_than 的 backed_var 代换；附发布版 283 行简化版对照。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/split_tiling.py
  role: implementation
created_at: '2026-11-12T13:18:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 `split_tiling` 常规轴选择：split/tiling/no_loop 原则、最低维推导与比较工具

## 固定版本与适用范围

主线 pin（ac0e1564）`codegen/split_tiling.py`（1087 行）。分组构造族（`:325-961`）与头部常量（`:1-55`）归[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)，挂接点窗（`:100-135`、`:325-345`）同在其读窗。本卡覆盖其余常规选择面：`:56-99`（工具函数）、`:136-330`（三大选择器与总入口）、`:962-1087`（尾部 outer-reduce/最低维/比较工具），两卡拼合即为该文件全文。调用点：主线 `codegen/triton.py:1540-1542`（`SplitTiling(self)` + `select_split_tiling_axis()` + 回填 `load_store_indexing`）与 `:1556`（`select_no_loop_axis()`，rg 锚）。发布 pin（f3ecfe4a）**自有另一份** `codegen/split_tiling.py`（283 行、12283 字节，见『发布版对照』与[发布版 SplitTiling 函数卡](torch_npu_release_inductor_split_tiling_functions.md)）。纯静态阅读；draft、platforms 为空。

## Split 轴选择（`select_split_axis` `:103-200`）

五条原则为源码注释原义（`:98-102`）：①先维度合并再切分（降维降低选择复杂性）；②切分轴尽量选高维轴（load/store 线性度好）；③规约轴和低维轴不作切分轴，但高维规约融合算子且高维尺寸 ≥64KB、其他维度不足以切分时可考虑；④切分轴总 numel 超过 aicore 总数，数量最好不超过 3（triton 最多三维发射）；⑤含 cat 算子时尾轴不切分。

停止条件（`:124-150`）：**符号分组提前停**——`enable_symbolic_shape_group_autotune` 且已有 split 轴且是规约 kernel 且有动态 split 轴且只剩低维候选（`:128-134`）；`optimization_hint(current_numels)` 抛 TypeError（动态 numel 无法估值）时退化为轴数下限（≤2 轴要 ≥1、否则 ≥2）；否则要求 `val >= vector_core` 且 `val // ceil(val/vector_core) > vector_core × 0.8`（核数覆盖且均分效率 >80%）；split 轴数达 3 即停。选择循环（`:164-176`）：先「非规约+非低维」，再「非规约+允许低维」，每轮 count+1，>10 轮 break（规约轴永不进常规循环）。**动态全规约保 grid==1**（`:178-196` 注释原义）：无 split 轴且全部轴是规约轴且至少一轴动态时**不补选**——把规约轴设为 grid split 轴会得到 grid>1 而无跨核 combine（A5），覆写标量输出；留空 split_axis（按运行期 numel 循环 + 尾 mask），覆盖纯 1D `[n]` 与带额外静态规约维的 `[n, 1024]`。最终 `sort(reverse=True, key=self.key)` 并编号 `split_order`。

`key`（`:74-83`）：`w/v/t` 前缀轴排最高（`"zz"+name`）；`ModularIndexing` 表达式轴排更低（`name[0]+"0"+...`，低于 floor_dir 注释原义）；其余按名。

## Tiling 轴选择（`select_tiling_axis` `:208-276`）

原则注释原义（`:202-205`）：①load/store 索引表达式中的低维轴都要成为 tiling 轴；②规约轴要成为 tiling 轴；③多维规约只有规约轴可被选为 tiling 轴；④tiling 轴覆盖 total numel 的 80%。停止条件（`:212-239`）：`numof_reduction_axis() > 1` 且全部规约轴已是 tiling 轴且**非** contiguous_reduction（`:56-72`：多个规约轴的 dim 序号连续才算 contiguous；golden var list 缺失时现场选择）即停。`select_tiling` 两轮语义不同：`(low_dim=True, reduction=True)` 轮内 `if low_dim or reduction: continue`（`:257`）使「补最长轴」分支对**每个轴都跳过**，只做低维/规约标记；`(low_dim=False, reduction=False)` 轮（`:270`，停止条件未满足时循环调用）才走到最长轴分支——但 `longest = axis`（`:260`）取的是**当前遍历轴**而非真正的最长维搜索（注释里被注释掉的 `find_longest_dimension(check_in_tiling=True)` 调用是其意图痕迹，源码字面事实），每轴处理后查停止条件，count>10 break。末尾同 key 排序 + `tiling_order` 编号。

## No-loop 轴选择（`select_no_loop_axis` `:282-325`）

原则注释原义（`:278-281`）：优先 low_dims tiling 轴；不够再从 tiling 轴选其他轴；所有轴空间预估 ≤4KB 无需 loop；动态 shape 轴不做该优化。实现：low_dims 轴按长度排序（静态 `(0, length)`、动态 `(1, default_sort_key)`——动态排最后）；dtype 字节取**首个 split 轴**的 dtype（无 split 轴用 float32）；`stop_loop`（`:298-310`）：规约/split/已 no_loop 轴跳过；**动态轴直接视为溢出返回**（不标记 no_loop）；累乘 numel × dtype_byte > 4KB 即停，否则标 `is_no_loop_axis`。persistent_reduction 时先累乘规约轴 numel 作为初始值。入口 `select_split_tiling_axis`（`:327-330`）= split → tiling → `apply_group_rewrite_if_needed`（分组挂接，归[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)）。

## 尾部：outer-reduce、最低维与比较工具（`:962-1087`）

- `should_outer_reduce_me`（`:961-971`）：高阶规约且轴长 >32768 且 `x.is_loop` 时置 `should_outer_reduce=True` 并 `self.kernel.split_axis = x`——**把 split_axis 从列表改写成单个轴对象**（类型变化，后续消费端须兼容两种形态；注释 `:960` 自述双规约轴只 outer 一个时此逻辑不工作）。
- `find_lowest_dimension`（`:985-1054`）：`construct_low_dim`（`:986-1013`）对每个索引的 `as_coefficients_dict` 逐符号取轴——系数为 1 且该 key 恰一个自由符号 → 低维，否则高维；**`low_dims = low_dims - high_dims`**（同一轴在任何索引里非 stride-1 即整个排除，注释示例 `x0`/`x0 + 128*y0` 中 x0 有效）；low_dims 为空时 warning 并回退未差集的 low_dims。索引收集：`inside_reduction` 先只收 in-pointer 读索引（buffer 名不在节点名集合才算 in-pointer，`:1029`），再对非规约节点收 STORE/STORE_REDUCTION 写索引（`:1041-1052`）；间接索引经 `substitube_indirect_index` 替换（源码拼写如此）。
- `find_longest_dimension`/`is_lowest_dimension`（`:973-983`）；比较工具 `convert/less_than/great_than/ge_than`（`:1056-1087`）：非 Integer 表达式先 `subs(V.graph.sizevars.backed_var_to_val)` 再比，int 与 sympy.Integer 单侧提升对齐。

## 发布版对照（f3ecfe4a `codegen/split_tiling.py`，283 行）

发布版是**简化前身**，不是同一文件：无 `select_no_loop_axis`、无分组改写（`apply_group_rewrite`/`_build_grouped_meta` 等分组符号在发布全树零命中）；**多** `find_possible_permutes`（`__init__` 即算 `possible_need_permute`：多个 low-dim 轴在不同索引中顺序不一致则可能需 permute——主线版无此函数）；`total_split_numels` 直接用 `x.length`（主线版经 `get_length_val` 做 backed_var 代换）。消费点不同：发布版由 `codegen/scheduling.py:448-450` 在 scheduling 期调用，主线版由 `codegen/triton.py:1540-1556` 在 kernel codegen 期调用。`should_outer_reduce_me`/`key`/split 五原则注释两侧同源。

## 失效边界与静态口径

- 停止条件的 `optimization_hint` 估值、`vector_core` 数值、4KB/80%/32768 阈值的设备适配性均为静态记录，未运行验证；`_num_vector_core` 来源见[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)失效边界。
- `select_tiling` 的「补最长轴」分支被 `continue` 屏蔽是字面事实；其是否为上游意图不在本卡判断范围。
- `should_outer_reduce_me` 的调用方（`kernel` 侧 outer-reduce 流程）不在本卡范围；split_axis 类型改写的全部下游消费端未逐一核对。
- 与[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)的边界：其覆盖 `:1-55` 与 `:325-961`；本卡覆盖 `:56-99`、`:136-330`、`:962-1087`；`:100-135` 为挂接点窗，归[分组构造卡](torch_npu_main_inductor_grouped_meta_construction.md)读窗。
- 本卡全部结论来自两 pin 静态阅读；未运行任何轴选择。

## Evidence

- [主线 codegen/split_tiling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py)（primary；`:56-155`、`:156-330`、`:958-1087` 读窗）
- [主线 codegen/triton.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py)（implementation；消费锚 `:1540-1542`、`:1556`，rg 定位）
- [发布版 codegen/split_tiling.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/split_tiling.py)（implementation；`:1-72` 全文结构与 `:73/123/197/272` def 索引对照；发布版消费锚 `codegen/scheduling.py:448-450`）
