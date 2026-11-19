---
type: Guide
title: torch_npu 主线符号分组构造：_build_grouped_meta、分桶推导与代表形状纯函数
description: 记录主线 codegen/split_tiling.py 的 _build_grouped_meta 构造族：模板门、轴分类、桶边界常量与静态因子缩放、elementwise 负载的访问签名分类、GroupedKernelMeta 装配与降级函数；以及 runtime/symbolic_grouping.py 的代表形状纯函数（build_group_representatives 的 radix 解码与可达组、evaluate_grouped_benchmark_expr 小语言、payload 序列化严格性与零消费负证据）。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_symbolic_grouping.py
  role: evidence
created_at: '2026-11-12T12:38:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线符号分组构造：`_build_grouped_meta`、分桶推导与代表形状纯函数

## 固定版本与适用范围

主线 pin（ac0e1564）。本卡持有符号分组构造期实现：`split_tiling.py` 头部常量 `:1-55`、门与轴分类 `:341-460`、特征/分桶族 `:462-961`（即 `_build_grouped_meta` `:865-916` 及其全部直接被调函数）；`symbolic_grouping.py` 的代表形状与纯函数 `:197-430`、`:517-590`（`symbolic_grouping.py` 其余窗口——门/桶/编码 `:1-196` 与 footprint 求值 `:431-520`——的结论见[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)符号分组节）。挂接点与 codegen 门链（`apply_group_rewrite_if_needed` split_tiling.py`:325-339`、codegen/triton.py`:1992-2011`/`:2476-2496`）亦由[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)持有；运行期消费类 `NPUSymbolicGroupedAutotuner`（triton_heuristics.py `:2430-3163`）由[分组 autotuner 类体卡](torch_npu_main_inductor_symbolic_grouped_autotuner.md)持有。文档契约（单动态轴、回退条件、显存预算）由[CostModel 与分组指南](torch_npu_inductor_costmodel_and_shape_groups.md)与[动态形状指南](torch_npu_inductor_dynamic_shape_choices.md)持有，本卡只钉源码实现。发布 pin（f3ecfe4a）无任何分组符号：全树 rg `symbolic_grouping|GroupFeatureSpec|GroupedKernelMeta|_build_grouped_meta|build_group_representatives|apply_group_rewrite` 零命中（负证据，含 torchnpugen/ 与 test/）；但发布版**自有**简化版 `codegen/split_tiling.py`（283 行，无分组改写、无 `select_no_loop_axis`、多 `find_possible_permutes`，由 `codegen/scheduling.py:448-450` 消费），与主线 1087 行版本不是同一实现。纯静态阅读；draft、platforms 为空。

## 构造门与轴分类（split_tiling.py `:327-460`）

`select_split_tiling_axis`（`:327-330`）→ `apply_group_rewrite_if_needed`（`:332-339`）：`enable_symbolic_shape_group_autotune` 关 → meta=None；`_is_grouped_template_enabled`（`:348-350`，模板名 ∈ `npu_config.symbolic_group_allow_templates`）不满足 → None；两者都过才调 `_build_grouped_meta()`。模板名（`:341-346`）：persistent_reduction → reduction → pointwise。轴分类 `_classify_split_axes`（`:352-360`）：split 轴按 `sympy.Integer` 判静态/动态。主轴选择 `_select_primary_group_axis`（`:362-368`）：动态 split 轴中 `sorted_axis` 序最前者。无动态 split 轴时的两条被调（docstring 原义要点）：`_dynamic_reduction_tiling_axis`（`:371-386`）要求**恰好一个**动态 r 前缀轴且它不在 split 轴里（A5 无跨核 combine，grid>1 会覆写输出，故 grid==1）；`_dynamic_pointwise_tiling_axis`（`:388-409`）要求恰好一个动态轴、被 tiling 不被 split、且 `_pointwise_layout_kind` 非 None。布局判别（`:411-460`）：对每个访存索引按轴取 stride 系数，缺轴记 broadcast、多个 stride 阶记 transpose，二者并发记 transpose_broadcast，否则 None；stride 非整数先试 `optimization_hint` 再放弃该索引。

## 特征与分桶推导（`:462-961`）

桶边界常量（注释给出设计理由，本卡按字面记录）：`_REDUCTION_BUCKETS=(8192,)`、`_OUTER_BUCKETS=(256,)`（`:489-490`，桶按组乘积分界、闭桶调上界、开尾调 `max boundary × 2`）；带静态轴的 outer 组用 `_outer_buckets_with_static_axes()`（`:503-506`，`vector_core × 1..5`——按核数对齐使桶内 sub-blocks 一致）；整核归约 `_FULL_REDUCTION_BUCKETS=(64,256,1024,4096,8192)`（`:519`）。静态因子 `_static_group_factor`（`:530-536`）把边界按组内静态轴乘积缩放（`:538-551`，否则开尾代表值除尽静态因子会把动态轴塌成 1）。

`_build_group_features`（`:631-714`）产出的特征（`GroupFeatureSpec(name, source, axis_names, boundaries)`）：

| 门槛 | 动作（特征） | 边界 |
| --- | --- | --- |
| 归约模板且 outer 轴有动态轴（`:647-659`） | `"outer"`/`outer_product`，桶经静态因子缩放（有静态轴时换宽桶） | 只给**含动态轴**的组建特征——静态组乘积恒定，分桶只会造不可达组 id（注释原义） |
| 归约模板且 reduction 轴有动态轴（`:660-674`） | `"reduction"`/`reduction_product`；`owns_whole_kernel`（无 outer 轴且无 split 轴，`:661`）用 `_FULL_REDUCTION_BUCKETS`，否则 `(8192,)` | grid==1 时 tile 是桶能调的唯一东西，单边界太粗（注释原义） |
| workload 为 `"elementwise"`（`:676-692`） | `_default_dynamic_axis_feature`；不可构造则退全轴特征，桶 `(vector_core*4096,)` | 单动态轴限制：`len(dynamic_split_axes)>1` → None（`:562-563`） |
| pointwise 布局 broadcast/transpose_broadcast（`:693-700`） | 主轴 `"axis"` 源，桶 `(16,64,256,1024,4096)` | 转置广播共用 broadcast 桶 |
| pointwise 布局 transpose（`:702-710`） | 主轴 `"axis"` 源，桶 `(64,128,256,512)` | — |
| 其余 pointwise（`:711-714`） | `_default_dynamic_axis_feature` 或空元组（→ 构造失败） | 空特征即 `_build_grouped_meta` 返回 None |

`_default_dynamic_axis_feature`（`:553-629`）：下界 `max(4KB//dtype_bytes//tiling_product, next_pow2(2*vector_core))`、上界 `max(prefix_product×128, next_pow2(8*vector_core), ceil(4096×vector_core/tiling_product))`；动态轴后有静态 split 轴则前插 `next_pow2(vector_core//2)` 边界；`_add_wide_group_midpoints`（`:28-38`）在相邻边界比 ≥4 时插一个 `min(next_pow2(下界×8), next_pow2((上界+1)//2))` 中点。特征轴名只含（前缀静态轴 + 动态轴）（`:587-623` 注释：split 轴保持 split 角色、被排除出分类乘积）。

`"elementwise"` 负载判定族（`:716-863`）：每个 scheduler 节点都要能分类，任一失败整体放弃。分类门槛（`:769-806`）：无副作用/别名/变异；body 不含 `masked/scan/sort/rand/randn/load_seed`（`:760-762`）；写全为 `MemoryDep` 且不带 index_exprs；写访问签名（`_make_access_signature` `:724-737`：间接或带 mode 的依赖 → None；索引减 offset、变量 alpha 重命名后化简）全等；无读 → body 全为 `constant/store/output` 且有 constant 才记 `neutral_constant`；有读 → 读全 `MemoryDep` 且与写签名全等才记 `direct`。最终 `_classify_group_workload`（`:841-863`）还要求：全节点签名互相全等、neutral 输出全部被组内某节点消费（`:808-823`）、存在至少一个外部 direct 读（`:825-839`）——**pointwise 模板专属**，其他模板直接 None。

`_build_grouped_meta`（`:865-916`）装配：有动态 split 轴 → 主轴（None 即失败）；secondary 动态轴 `_downgrade_split_axes`（`:918-930`，置 `is_split_axis=False`、重排、重编号 `split_order`——**修改 kernel 状态而非仅元数据**）；pointwise 且单动态轴 → `_downgrade_suffix_static_split_axes`（`:932-958`，动态轴前的 split 总量 hint ≥ `num_vector_core` 才把后缀静态 split 轴也降级）。`runtime_block_arg_names` = 每个 split 轴 `f"{name.upper()}BLOCK"`（`:882-884`、`:895-897`）。无动态 split 轴 → 归约/pointwise 主轴选择（见上）；`primary_axis` None → 整体放弃。特征为空 → None；否则 `GroupedKernelMeta(enabled=True, template, workload, primary_group_axis=名, static_split_axes=名, secondary_runtime_symbolic_axes=名, group_features, runtime_block_arg_names)`（`:907-916`）。

## 代表形状与纯函数（symbolic_grouping.py `:197-430`、`:517-590`）

`build_group_representatives`（`:203-354`）：

- 同一轴名出现在多个特征 → `UnsupportedGroupedPlan`（`:215-222`）。
- 桶语义（`:224-232`）：`bucket_bounds` 返回 `(lower, upper)` 对——bucket 0 为 `(0, b0)`，bucket k 为 `(b_{k-1}, b_k)`，开尾桶 `upper=None`。可达特征区间由 pure 静态判据决定（`:279` 拒绝 `feature_value <= lower` 或 `> upper`）：**`(lower, upper]`（上闭下开）**，开尾桶只要求 `> lower`。代表值（`:234-238`）：闭桶取上界 `upper` 本身，开尾取 `lower×2`。
- `representative_for_feature`（`:240-292`）：`"axis"/"primary_axis"` 源要求恰好一个轴名（否则 raise）；`"outer_product"/"reduction_product"` 源把特征轴分成静态（查 `axis_static_values`，非正值 raise）与符号轴——**多于一个符号轴 raise**；纯静态组特征值 = 静态因子，可达判据为 `lower < feature_value <= upper`（开尾桶无上界拒绝，`:276-281`），不满足则该组 None；有符号轴时目标值 = 上界或 `max(lower+1, lower×2)`，符号轴值 = `ceil(目标/静态因子)`。
- 组 id radix 解码（`:294-320`）：`group_id` 逐特征按 `len(buckets)+1` 进制拆桶号；未列出的轴补静态值或 1。`group_id_count = Π(len(buckets)+1)`（`:322-324`）；对**每个** group id 构造代表，可达集 = 非 None 者，全不可达 → `UnsupportedGroupedPlan`（`:334-335`）；plan 附 `benchmark_feature_inputs_by_group` 与 `benchmark_axis_values_by_group`（`:345-353`）。调用点：codegen/triton.py`:2476` `_disable_grouped_autotune_if_unsupported` 用它试构造（消费锚 `:2470-2500`）。

`evaluate_grouped_benchmark_expr`（`:357-399`）：const / axis_name（环境缺名 raise）/ mul / add / floordiv（二元且除数非零）的小语言；`runtime_arg_index` 显式 raise「grouped codegen 期间不可界」——被 `estimate_grouped_benchmark_footprint`（`:458/:462/:470`）消费。`required_storage_numel`（`:402-420`）：`1 + Σ(dim-1)×stride`，零尺寸 → 0，负 size/stride raise。`_grouped_benchmark_dtype_itemsize`（`:423-428`）：`"torch.X"` 字符串经 `getattr(torch, ...)` 解析，非 `torch.dtype` raise。

payload 序列化（`:519-524`、`:527-590`）：`serialize_grouped_plan`/`deserialize_grouped_plan` 分别转 `GroupedKernelMeta.to_payload()/from_payload()`（from_payload 的已知字段读取语义见[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)）；`_require_*` 族对 name/source/axis_names/buckets 等做严格类型检查（TypeError；`workload` 只接受 None|"elementwise"，ValueError）；`_require_int_tuple` 用 `isinstance(item, int)`——Python 语义下 bool 可作 int 通过（静态记录）。**负证据**：`serialize_grouped_plan`/`deserialize_grouped_plan` 在主线全树（含 torchnpugen/ 与 test/）除定义处外零命中，本 pin 内无消费者。

## 纯函数验收契约（test_symbolic_grouping.py）

该测试文件（306 行全文静态阅读，未运行；带 `@runIfVersion(max="2.13")` 版本门——该门只出现在 `test/_inductor/` 根目录测试文件）钉死：

| 契约 | 断言 | 边界 |
| --- | --- | --- |
| `required_storage_numel`（`:34-51`） | `(8,10)/(10,1)→80`、`(3,4)/(8,1)→20`（最小存储而非 numel 直乘）、stride 0 轴与 numel 0 边界；rank 不匹配 → `UnsupportedGroupedPlan("rank mismatch")`、负 stride → `UnsupportedGroupedPlan("negative benchmark tensor stride")` | **失效关闭**：布局非法即抛，不估算 |
| 表达式小语言（`:54-61`） | `evaluate_grouped_benchmark_expr` 的 add/mul/const/axis_name 组合 `(x0×10)+3 = 83` | |
| 运行期不可界（`:114-132`） | `size_exprs` 含 `runtime_arg_index` → `UnsupportedGroupedPlan("runtime_arg_index cannot be bounded")`，footprint 不给估值 | codegen 侧显式拒绝，运行期消费端（分组 autotuner 类体卡）另持 `runtime_arg_index` 合法形态 |

预算守门与 footprint 口径的测试断言由[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)『测试验收契约』节持有（被测对象是 codegen 侧门链）。

## 失效边界与静态口径

- `_num_vector_core()`（`:23-25`）经 config 惰性属性从设备/`NPU_DEVICE_LIMIT` 解析；`vector_core` 数值不在本卡验证，桶常量的设备适配性是静态推导。
- 降级函数改写 `kernel.split_axis` 是构造期的真实 codegen 状态变化；本卡未执行任何构造路径验证其对生成代码的实际影响。
- 运行期 `get_group_id` 的分组归属/零桶语义不由本构造窗口证明：本卡只覆盖构造期代表与可达集推导，不据 `(lower, upper]` 构造区间推断运行期分组边界行为。
- `_axis_static_length`（`:521-528`）的 `optimization_hint` 失败回 1；静态长度推导失败时特征边界仍可构造（保宧行为），不代表形状真实分布。
- `split_tiling.py` 的常规 split/tiling 选择面（`:56-326`）与尾部（`:962-1087`）由[主线 split_tiling 轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)持有；`test_symbolic_grouping.py` 的预算守门/端到端用例归[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)。
- 本卡全部结论来自两 pin 静态阅读；未运行任何分桶、代表构造或 benchmark 路径。

## Evidence

- [主线 codegen/split_tiling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/split_tiling.py)（primary；读窗 `:1-55`、`:325-961`）
- [主线 runtime/symbolic_grouping.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/symbolic_grouping.py)（primary；读窗 `:197-430`、`:517-590`；`:1-196` 与 `:431-520` 的结论见[补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)符号分组节）
- [主线 codegen/triton.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py)（implementation；`:2470-2500` 消费锚）
- [test_symbolic_grouping.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_symbolic_grouping.py)（evidence；全文 306 行静态阅读，纯函数断言见『验收契约』节）
