---
type: Guide
title: torch_npu 主线 inductor 规约/Welford 测试契约：VarMean 结构断言、NumelList 契约、连续 sum 布局、持久规约阈值、掩码与扫描代码生成
description: 记录主线 test/_inductor 中 welford_reduction_structure 族 13 个文件（共 1549 行）的测试侧契约：test_var_mean 的 9 组 run_and_get_code 结构断言（simd welford 单载入/无计数累加/尾掩码/动态图不回退 native layer_norm/复用输入原位变异）、NumelList 展平乘积比较与哈希、_use_contiguous_sum_layout 的打包形状、should_use_persistent_reduction 的 64 项 fp16 水位与 950 高负载阈值、掩码消去条件、associative_scan 的环载维与轴掩码、符号 stride 序比较的进程级恢复。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_var_mean.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_kernel_features.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_contiguous_sum_layout.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_persistent_reduction_threshold.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_range_split_compatibility.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_symbolic_stride_comparison.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_reduction_mask_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_upcast_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_scan_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_reduction_compile.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_split_loop.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_sum.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_sum_add.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/testutils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/version_mark.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/npu_kernel_features.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/_sizevars.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_patch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
created_at: '2026-11-12T14:52:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 inductor 规约/Welford 测试契约：VarMean 结构断言、NumelList 契约、连续 sum 布局、持久规约阈值、掩码与扫描代码生成

## 固定版本与适用范围

主线 pin（ac0e1564）`test/_inductor` 的 welford_reduction_structure 族 13 个文件全文静态阅读（共 1549 行）：test_var_mean（414）、test_npu_kernel_features（95）、test_contiguous_sum_layout（140）、test_persistent_reduction_threshold（116）、test_range_split_compatibility（40）、test_symbolic_stride_comparison（107）、test_reduction_mask_codegen（113）、test_upcast_codegen（36）、test_scan_codegen（189）、test_reduction_compile（76）、test_split_loop（30）、test_sum（95）、test_sum_add（39）。另读共享基建 `testutils.py`（31 行）与 `test/version_mark.py`（135 行，无尾随换行）以锚定 `_generate_tensor` 与版本门语义。同目录其余测试文件的验收契约由[precompile 流水线卡](torch_npu_main_inductor_precompile_pipeline.md)、[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)、[costmodel 与调试 autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)与[缓存 autotune 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)持有；[动态形状分组测试卡](torch_npu_main_inductor_dynamic_shapes_grouping_tests.md)与本文同族。只提炼**测试断言的期望面**；实现语义归各实现卡。全部静态阅读，未运行任何测试；draft、platforms 为空。

## 版本门与共享基建

`@runIfVersion(max="2.13")`（version_mark.py `:95-135`）只做**区间相交**判断：声明区间与 CI 目标区间（`set_ci_version_range` 或 `CI_VERSION_MIN`/`CI_VERSION_MAX`）不相交才 skip；两个区间端点都是闭的，`None` 表示无界。它同时被 CI 用 AST 做文件级过滤——即 `max="2.13"` 声明的是"该用例在 torch ≤2.13 的 CI 目标下运行"，不是"实现只在 2.13 可用"。`testutils._generate_tensor`（testutils.py `:20-31`）：浮点走 `torch.randn(...)*2000`（floatPOSIFLAG 时为 `1000*rand`），整型走 `randint(0,2000)`——比标准 randn 大两个量级的幅度，配 `atol=1e-1,rtol=1e-1` 的族内宽容差；本族少数用例另用 `atol=2e-4/1e-3`。

## `TestVarMean`：Welford SIMD 代码生成的结构断言（test_var_mean.py 全文）

开关：`npu_config.enable_welford`（config.py `:191`，env `TORCHINDUCTOR_ENABLE_WELFORD` 缺省 "0"）在各用例内保存-改写-恢复，配 `torch._dynamo.reset()`；`is_ascend950`（config.py `:40`）做 950 专属 skip。编译选项统一传 `unroll_reductions_threshold: 1`（部分加 `aggressive_fusion: True`）。

| 用例 | 断言的期望 | 边界 |
| --- | --- | --- |
| `test_reduction_cases_shapes`（`:17-32`） | `@skip("skip ci codegen error")` 的数值 parametrize | 纯 op_calc compare，归实现卡数值面，本卡不重复 |
| `test_welford_enabled`（`:34-55`） | 仅数值等价（atol/rtol 1e-1） | 无结构断言 |
| `test_welford_does_not_change_standalone_var_codegen`（`:57-85`） | enable_welford=True 下，独立 mean/var+normalize **不得**出现 `triton_helpers.welford_reduce` / `welford(` | Welford 降级只经融合调度替换，standalone 规约不换写法——与调度卡 welford 门互证 |
| `test_welford_simd_codegen`（`:87-139`） | permute→contiguous→view(381,80,64) 的 F.layer_norm（末维 64）生成代码必须同时含 `for x1_loop_offset in range(`、`X1BLOCK_SUB`、`_acc_sum = tl.zeros([`+`, 1], tl.float32)`、`axis=1, keep_dims=True`、`npu_kernel_type': 'simd'`、`'vectorized_welford_axis':`、`_mask = True`；必须**不含** `for loop_r`、`_acc_count = tl.zeros`、`_acc_count += tl.where`；`code.count("tl.load(in_ptr0")` **恰为 1**；rsqrt 出现位置严格晚于 `axis=1, keep_dims=True` 的规约 | 单次载入、无独立计数累加、统计后归一——Welford 向量化路径的完整字面指纹 |
| `test_dynamic_single_layer_norm_welford_fused`（`:141-164`） | dynamic=True + mark_dynamic(0, min=1, max=4094)，fp16 hidden=512：代码**不得**含 `triton_poi_fused_native_layer_norm` | 动态形状下 Welford 融合路径生效、不回退 native kernel |
| `test_welford_full_static_mutation_hazard`（`:166-268`） | 复用 pre_norm 的多层图 + `config.patch("triton.codegen_upcast_to_fp32", False)`：断言输出有限、`mutated_arg_names': ['in_out_ptr`（原位变异）、**不含** `vectorized_welford_axis`；950 另断言 `npu_kernel_type': 'simd'`；并用 actual[0] 重算 normalized 与 actual[1] 对齐（1e-2） | 全静态路径与 simd 向量化路径不同：变异复用优先于轴向量化；变异不改变归一化输入的取值一致性 |
| `test_welford_numerical_above_persistent_threshold`（`:270-299`） | 950 专属；(200,5036) fp16 数值等价 | 超持久阈值的形态面，数值-only |
| `test_welford_simd_low_precision_codegen`（`:301-335`） | 950 专属；fp16/bf16 仍含 `vectorized_welford_axis`+`simd` | 低精度回退在 950 仍走向量化 Welford |
| `test_welford_simd_codegen_disabled`（`:337-366`） | enable_welford=False → 不含 `vectorized_welford_axis` | 负向对照 |
| `test_welford_simd_tail_codegen`（`:368-408`） | (8,8,81,8)→view(8,81,64)：81 不可整除，尾掩码必居其一：`if 81 % X1BLOCK_SUB != 0:` 或 `x1_mask = x1 < min(X1BLOCK+x1_offset, x1_numel)`；无 `for loop_r`、无 `_acc_count`、单次 `tl.load(in_ptr0` | 非整除尾处理在向量化路径内完成，不落回计数式循环 |

`vectorized_welford_axis` 的生产端在 triton.py `:1559`（`_select_vectorized_welford_axis`，`:1066/:1074` 初始化与门，`:1938-1941` 参与排序）——本卡仅锚定归属，函数体归实现卡。

## `NumelList` 单元契约（test_npu_kernel_features.py 全文）

`NumelList([2,3,4])`（npu_kernel_features.py `:1-20`，Tuple 子类，调度卡已读该窗）：`numels()==24`；`__eq__` 与标量比较按展平乘积（`==24` 真、`==25` 假）；`__lt__/__le__/__gt__/__ge__` 同为展平乘积比较（`[2,3,4] < [3,4,5]`、`< 25` 真、`< 24` 假、`<= 24` 真含相等、`<= 23` 假）；`% 5 == 4`、`/ 2 == 12.0`、`// 2 == 12`、`*2` 与反向 `2*` 均 48、`+2` 与反向均 26；`hash` 与内容一致、与整数 hash **不同**（`hash(numel_list1) != hash(24)`）——NumelList 可作字典键与 sympy 表达式中的"乘积语义标量"，但不与整数全等。这些是调度器 `_canonical_group_size`/Welford 分组比较的数学底座（实现归调度卡）。

## 连续 sum 布局（test_contiguous_sum_layout.py 全文）

`_use_contiguous_sum_layout`（triton.py `:3953`）的类外契约（`object.__new__` 半实例）：

- 规约轴被外部 x 轴隔开（`("r2","r3","x5")` 值轴 + `("r2","x4","r3","x5")` 解析序）→ 连续布局成立；`dense_size_str()` 把规约块**打包相乘**：`[X5BLOCK_SUB, R3BLOCK_SUB * R2BLOCK_SUB]`，`reduction_dim()==1`、`triton_tensor_ndim()==2`、`reduction_resize("s",1)=="s.reshape(1, 1, X5BLOCK_SUB)"`。
- 多个保留 x 轴保持自身顺序：`[X0BLOCK_SUB, X3BLOCK_SUB, R2BLOCK_SUB * R1BLOCK_SUB]`，dim=2、ndim=3。
- `inside_reduction=False` 时 `dense_size_list()` 变 `["1","1","X5BLOCK_SUB"]`，但 `dense_size_str` 保持同形——规约轴不出现在非规约段打包形状之外。
- 单独/标量规约、旧相邻编址（`("r0","x1","r2")` 解析序 `("r0","r2","x1")`）保持旧布局（`[R0BLOCK_SUB* X1BLOCK_SUB* R2BLOCK_SUB]` 等），`reduction_resize` 退化为 `triton_helpers.promote_to_tensor(s)`。
- **非 sum 规约全部排除**：max/min/argmax/argmin/welford_reduce/prod、sum+max 混合、sum+welford_reduce 混合、空 reductions → `_use_contiguous_sum_layout()` 假且 `is_contiguous_reduction()` 假、ndim=1——连续布局是 sum 专属优化，welford 不进入。
- 构造函数用 `features.node_schedule` 而非 `node_schedule`（`:104-107` 删属性仍成立）。
- 设备用例 `TestContiguousSumLayoutNPU`：bias 梯度形态 `reshape→permute→reshape→sum(0)→(+广播消费)`，动态/静态 ×63/64 ×消费与否，atol 2e-4。

## 持久规约阈值（test_persistent_reduction_threshold.py 全文）

`should_use_persistent_reduction`（triton.py `:1139`）的类外契约：

- **水位边界**：64 个 fp16 逐项读（恰 64）+ `NumelList((32,64))` reduction_numel → 持久成立；65 个逐项读 + reduction_numel 2048 → 不成立。混入**一个 fp32**（其余 fp16）→ 即便 64 项也不成立——水位按输入字节数而非项数。
- `_estimate_reduction_input_bytes`（triton.py `:1114`）：去重（`input` 与重复读只计一次）、跨下标变体计两次（`input@0`+`input@1`）、被中间节点写出的 buffer（`intermediate`）不计、epilogue 段（DisableReduction/EnableReduction 之间）不计、unspec 标量（`scalar` int64）不计 → 2048×2×4。
- **950 专属高负载阈值**：is_ascend950=True 时 81 个 fp32 读 + reduction_numel 1024 仍持久、2048 不持久；is_ascend950=False 时 2048 不持久——950 放宽高读数下的字节水位。
- **符号未证时保持既有阈值**：`reduction_numel=Min(s0,4096)`、patch `staticly_known_leq` 仅在 limit≥4096 才真（即水位未证）→ 仍持久——未证明的符号不切换阈值方向。
- 前提统一 patch：`triton.persistent_reductions=True`、`triton.multi_kernel=False`、cooperative_reduction=False。

## 掩码消去与规约块覆盖（test_reduction_mask_codegen.py 全文）

`IterationRangesEntryNPUIndex._codegen_mask` + `filter_masks`（triton.py `:4094`）：

- `R1BLOCK_SUB = 1 << (length-1).bit_length()`（unified：SIMT_ONLY/SIMD_SIMT_MIX 取下一个 2 的幂；SIMD/SIMT_TEMPLATE 直取 length）；`length == block` 时 `codegen_static_numels`（triton.py `:2558`）产生 `R1BLOCK_SUB: tl.constexpr = {block}`，掩码集被 `filter_masks` 清空并写 `r1_mask = True`/`r1_1_mask = True`；不等时保留 `r1_mask = r1 < r1_numel`。
- 未证情形掩码一律保留：长度为符号/0、非持久、`is_vectorized_split`、`optimize_mask=False`。
- 分裂轴整覆盖：`set_reduction_runtime_blocks_to_numel`（triton_heuristics.py `:3393`）把所有候选 Config 的 `R1BLOCK` 与 `split_blocks` **强制改写为规约全长**（1/64/512 全变 197/256）；此后恰等长掩码消去，197 仍保留 `min(R1BLOCK+r1_offset` 形。
- `filter_masks` 只清**字符串名掩码**；`TritonCSEVariable` 语义掩码原样存活。

## 符号 stride 序比较（test_symbolic_stride_comparison.py 全文）

`Layout._stride_expr_ge_or_false` 被 `patch_simplify`（`_sizevars.py :42`，经 `_statically_known_stride_multiple_of` `:17`）替换后的契约：

- 线性/平方、多项式（含 expand 与未展开）都能判序；静态值含 0；**无 hint 依赖**：unbacked symint 的复合式判序在 `optimization_hint` 被 patch 成 AssertionError 时仍完成（回归 pytorch/pytorch@93879b11e3b5）。
- 回退 guard 不含负指数 Pow、以 `Mod` 表达并可被 PythonPrinter 打出 `%`。
- `restore_inductor_baseline`（lowering_patch.py `:297`）恢复后 `_stride_expr_ge_or_false` 是普通 staticmethod 描述符、无 `_torch_npu_integer_strides` 标记；再 `patch_simplify` 重新带上标记——进程级注册表的恢复语义经 subprocess 隔离验证。

## 扫描、升浮点与同族数值面（其余四件全文）

- **test_scan_codegen**（`:189`）：`kernel.scan`（triton.py `:1648`）持久路径广播形状到 dense 形、fp16 升 fp32、helper `_triton_helper_fn_add` 接受 CSE 值；环载（非持久）路径用 `triton_helpers.select_one` 取**真实规约维**（`dim={r 维}, keep_dims=True`）、`tl.full` 填充、偏移 `loop_{axis} * {AXIS}BLOCK_SUB`（分裂轴再加 `{axis}_offset + (...)`）；扫描结果保留必需轴掩码（持久且恰整除才无 r 掩码）。NPU 用例：非 2 幂双轴 cumsum、整型默认/显式 dtype、out 变体——代码必含 `tl.associative_scan` 且**不含** `torch.ops.aten.cumsum.`（cumsum 不走 aten 回退）。
- **test_upcast_codegen**（`:36`）：`triton.codegen_upcast_to_fp32` True/False 两种取值下 fp16/bf16 `torch.abs` 生成代码都含 `.to(tl.float32)`——该开关不删除 abs 的升浮点写法，只控制算术升浮点面。
- **test_reduction_compile**（`:76`）：文件头 `os.environ.setdefault("TORCHINDUCTOR_NPU_BACKEND", "default")` + `_InductorNpuRegistry._loaded_backend` 非 default 即整类 skip——`make_reduction` 替换只对默认（Triton）子后端生效；docstring 记录回归史：旧替换签名缺 `strict_reduction` 形参，上游 sum_ lowering 无条件传入即 TypeError（修复面归 lowering 卡，此处只记测试侧门与回归描述）；全量 sum/mean 的"无关调度器缺陷"按文件声明另行跟踪，不在本卡范围。
- **test_split_loop/test_sum/test_sum_add**（`:30/:95/:39`）：split 尾循环数值面（gelu(a+b)，非整除形状）；`test_sum_1d_dynamic_shape` 用 12 个跨桶尺寸（8..999983）单 kernel 动态复用不重编译，同款再开 `enable_symbolic_shape_group_autotune=True` 走桶化路径——与分组测试卡互证；sum+add 的跨 dim 广播消费 atol 1e-1。

## 相邻卡边界

[Welford 调度卡](torch_npu_main_inductor_scheduling_welford_and_fusion.md)（调度器三级门/NumelList 分组/create_tiling r 前缀——本卡是其测试侧配对）；[precompile 流水卡](torch_npu_main_inductor_precompile_pipeline.md)（`NPUKernelType.compile_mode`/TTIR-only 编译族）；[precompile 流水线卡](torch_npu_main_inductor_precompile_pipeline.md)、[基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)、[costmodel 与调试 autotuner 卡](torch_npu_main_inductor_runtime_costmodel_and_debug_autotuners.md)与[缓存 autotune 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（同目录测试的 UB 重试/开关分派/costmodel/符号分组验收契约）；[动态形状分组测试卡](torch_npu_main_inductor_dynamic_shapes_grouping_tests.md)；[配置解析卡](torch_npu_inductor_config_parsing.md)（npu_config 开关面）；[CostModel 与形状分组](torch_npu_inductor_costmodel_and_shape_groups.md)；[缓存 autotune 补丁卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)。

## 失效边界与静态口径

- 本卡全部为测试文件静态阅读，**未运行任何测试**；"契约"指断言与实现的语义对应，不等于当前可跑或通过（依赖设备、torch 版本与 `runIfVersion` 门）。
- `X1BLOCK_SUB`/`R1BLOCK_SUB` 尾掩码字面、桶尺寸、950 阈值均为 ac0e1564 的**期望值**，随版本可变，以实现源码为准。
- 半实例（`object.__new__`）钉类外接口；`V.set_graph_handler(SimpleNamespace(...))` 的 mock 图只覆盖被测分支，不证明完整 kernel 构造路径。
- 实现符号（`_select_vectorized_welford_axis`、`scan`、`should_use_persistent_reduction` 等）仅 rg 锚定归属，函数体归各实现卡，本卡不重述其内部算法。
- 本卡事实不外推发布版（负向 rg：发布版无 Welford 调度面）。

## Evidence

- [test/_inductor/test_var_mean.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_var_mean.py)（primary；`:1-414` 全文）
- [test/_inductor/test_npu_kernel_features.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_kernel_features.py)（primary；`:1-95` 全文）
- [test/_inductor/test_contiguous_sum_layout.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_contiguous_sum_layout.py)（primary；`:1-140` 全文）
- [test/_inductor/test_persistent_reduction_threshold.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_persistent_reduction_threshold.py)（primary；`:1-116` 全文）
- [test/_inductor/test_range_split_compatibility.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_range_split_compatibility.py)（primary；`:1-40` 全文；`is_compatible` 四组拒绝、CantSplit expr=6/remaining=4、三组索引重建 15\*i0+5\*i1+i2）
- [test/_inductor/test_symbolic_stride_comparison.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_symbolic_stride_comparison.py)（primary；`:1-107` 全文）
- [test/_inductor/test_reduction_mask_codegen.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_reduction_mask_codegen.py)（primary；`:1-113` 全文）
- [test/_inductor/test_upcast_codegen.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_upcast_codegen.py)（primary；`:1-36` 全文）
- [test/_inductor/test_scan_codegen.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_scan_codegen.py)（primary；`:1-189` 全文）
- [test/_inductor/test_reduction_compile.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_reduction_compile.py)（primary；`:1-76` 全文）
- [test/_inductor/test_split_loop.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_split_loop.py)（primary；`:1-30` 全文）
- [test/_inductor/test_sum.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_sum.py)（primary；`:1-95` 全文）
- [test/_inductor/test_sum_add.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_sum_add.py)（primary；`:1-39` 全文）
- [test/_inductor/testutils.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/testutils.py)（implementation；`:1-31` 全文，共享张量生成与形状表）
- [test/version_mark.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/version_mark.py)（implementation；`:1-135` 全文，runIfVersion 区间相交语义）
- [主线 codegen/triton.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/triton.py)（implementation；rg def 锚 `:987/:1114/:1139/:1648/:2558/:3108/:3953/:3983/:4003/:4013/:4048/:4094/:1559`、`vectorized_welford_axis` 锚 `:518/:1066/:1074/:1938-1941`；函数体归实现卡）
- [主线 codegen/npu_kernel_features.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/npu_kernel_features.py)（implementation；`:1-20` NumelList 定义窗，调度卡已读，本卡仅引用）
- [主线 codegen/_sizevars.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/_sizevars.py)（implementation；rg 锚 `:17/:42/:59`，patch 面）
- [主线 lowering_patch.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_patch.py)（implementation；rg 锚 `:297` restore_inductor_baseline）
- [主线 runtime/triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py)（implementation；rg 锚 `:3393` set_reduction_runtime_blocks_to_numel）
- [主线 _inductor/config.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation；rg 锚 `:40` is_ascend950、`:191` enable_welford、`:205` enable_welford_post_reduction_reuse）
