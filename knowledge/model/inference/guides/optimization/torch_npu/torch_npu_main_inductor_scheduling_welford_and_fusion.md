---
type: Guide
title: torch_npu 主线 inductor 调度器：Welford 节点调度、NumelList 分组、融合判定与候选 tiling
description: 记录主线 codegen/scheduling.py（1050 行全文）：_generate_npu_node_schedule 的主循环/规约闭合/切分点插入、enable_welford 三级门与原始 group extents 重算、group_fn NumelList、create_tiling 非折叠前缀、make_ttir_for_check 的 eval 与删缓存、can_fuse 的 flex/combo/tiling 防融合规则、define_kernel 缓存键与命名、benchmark_fused_nodes 的 .kernel_perf/spills/clone 开销扣除、candidate_tilings stride 打分。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/npu_kernel_features.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/choices.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/scheduling.py
  role: implementation
created_at: '2026-11-12T14:24:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 inductor 调度器：Welford 节点调度、NumelList 分组、融合判定与候选 tiling

## 固定版本与适用范围

主线 pin（ac0e1564）`codegen/scheduling.py` 1050 行全文。发布 pin 同名文件只有 595 行的 scheduling 期 SplitTiling 消费窗（`:440-455` 已读，见[发布版 SplitTiling 函数卡](torch_npu_release_inductor_split_tiling_functions.md)），与本卡的 codegen 期调度器是两代不同面，互不推导。`select_tiling`/`codegen_node_schedule_with_kernel`/`free_buffers_in_scheduler` 为上游 `TritonScheduling` 继承成员，六 pin 外定义，本卡只记消费不记实现。纯静态阅读；draft、platforms 为空。

## Welford 节点调度（:49-201）

`_generate_npu_node_schedule`（:69-155）是 `generate_node_schedule` 的替换实现，入口为三级门（`NPUNoLinearTritonScheduling` :158-173 与 `NPUTritonScheduling` :189-201 两侧同型）：`npu_config.enable_welford` 关 → 上游基线；开但 `contains_welford_group(nodes)` 为假 → 上游基线，且**用 `max(nodes, key=is_reduction)` 重算原始 group extents 覆盖入参 numel/rnumel**（注释 :166-171：调用方可能已做 `_canonical_group_size` 规范化，上游等值检查须对未规范化的节点组）；含 Welford 输出组 → 走本函数。`contains_welford_group`（choices.py:59-65）= 任一节点 `_welford_output_group(allow_unmarked_epilogues=True)` 非 None。

| 局部判定 | 行段 | 语义 |
| --- | --- | --- |
| `same_size` | :77-82 | 相等或 `sizevars.statically_known_equals`。 |
| `fits_in_main_body` | :84-88 | 节点 numel/rnumel 等于主循环组，或节点 numel=主 numel*rnumel 且 rnumel=1（全扁平化覆盖）。 |
| `fits_outside_reduction` | :90-92 | rnumel=1 的节点在 rnumel!=1 时移出规约环。 |
| `expect_improved_memory_usage` | :94-95 | 节点读当前环已用 buffer 即算改善。 |
| `schedule_node_in_loop` | :97-109 | 规约类（SchedulerNode+ComputedBuffer、非 Scan）名字进 `not_ready_yet_nodes`（写延迟登记），否则写集并入 `current_loop_buffer_usage`。 |
| `end_current_reduction_loop` | :111-125 | 尾部 EnableReduction 弹出或补 DisableReduction；`maybe_split_index` 存在则在记号处**插入 DisableReduction/EnableReduction 对**（把主循环切成两段以让后续规约有干净边界）；yield 后追加 EnableReduction、清两集合。 |
| `requires_closing_previous_reduction` | :127-133 | rnumel!=1 且未完成规约与该节点 ancestors 相交，且调度尾是实节点。 |

主循环（:135-155）：主循环体节点在「环内已有 buffer 但新节点不改善内存」时记 `maybe_split_index`（首个此类位置生效，:143-146）；外置节点用规约闭合上下文包裹；不匹配组直接 `NotImplementedError`（:152-154）。

## 分组、tiling 与 kernel 选择（:203-269）

- `group_fn`（:203-213）：list 组扁平化后包成 `NumelList`，空组记 1。`NumelList`（npu_kernel_features.py:8-）是 Tuple 子类：`numels()` 为元素积（reduce），`__eq__/__le__` 按**扁平化元素积**比较——动态 view/cat 的展开与因式分解形态在比较时归一（`_canonical_group_size` :60-66 用 `sizevars.simplify` 做同型规范化，消费于 :489-490/:701-703/:736-738）。
- `create_tiling`（:215-234）：pointwise 前缀取 `["w","v","t","z","y","x"]` 尾段；规约 tiling 折叠为单元素 `NumelList(reduction_tiling).numels()` 配 `"r"` 前缀——与 `candidate_tilings` docstring「npu 与 gpu 的主差异是默认 tiling，npu 需要非折叠 ranges」呼应，但本函数的规约侧反而折叠成单积。
- `create_kernel_choices`（:236-244）：含 scan 算子时强制 `override_cooperative_reduction=False`；始终只产一个 kernel 选择（:244）。
- `make_ttir_for_check`（:246-269）：把 KERNEL_NAME 占位换成 `triton_`；对 src 中含 `inductor_meta` 的行做 `eval()` 提取 dict；置 `force_disable_caches=True` 后 `PyCodeCache.load`；调 `mod.triton_._triton_make_ttir()` 做 DSL 编译性检查；**删缓存文件**（`os.remove(mod.__file__)`，FileNotFoundError 容忍）。

## codegen_node_schedule 与 FX dump（:272-369）

每个 fused kernel 的流程：`select_tiling` → `create_kernel_choices`（单 kernel）→ 逐 kernel `codegen_node_schedule_with_kernel` → `MultiKernel.merge_workspaces_inplace` → 逐 kernel `codegen_kernel()` + **`make_ttir_for_check(src_code)`（每个 kernel 无条件跑一次 DSL 预编译检查，:289）** → `define_kernel`（:309）。`dump_fx_graph` 开时：缓存目录固定为 `TORCHINDUCTOR_CACHE_DIR/traced_fx_graph_cache`；`traced_graph_hash = code_hash(src+traced_graph.code+arg_shapes_str)`、`kernel_graph_hash = code_hash(src+traced_graph.code)`（:296-307）；调用后把 compile kwargs 与 `generate_fx_graph_code` 产物落盘（:331-338）。`is_multi_stream()` 时 `call_kernel` 传 origin_node（:326-329）。`config.nan_asserts` → `codegen_nan_check`；`warn_mix_layout` → `warn_mix_layout(kernels[0].kernel_name)`（:340-343）。intermediate hooks 只对 `live_output_buffers()` 内的节点（:348-367）。结束 `free_buffers`（:369）。

## 模板与 Combo（:371-538）

- `codegen_template`（:371-452）：`FlexAttentionDispatchTemplateBuffer` 走 `codegen_flex_attention_dispatch_template`，且 only_gen_src_code 分支直接 `NotImplementedError`（:376-383）；同时兼容 legacy `<STORE_OUTPUT>` 与 torch 2.10 的 indexed `<STORE_OUTPUT_N>` 子图体（:392-406）与 `finalize_remaining` 钩子收尾（:408-426）；`benchmark_kernel` 配置时拼基准代码（:429-439）。
- combo（:454-538）：`mixed_sizes = combo_kernel_allow_mixed_sizes>1 或 ==1 且 custom_part_algorithm`（:458-460）；逐子核先建 `NPUComboKernel.create_triton_kernel(tiling, features, optimize_mask=not mixed_sizes)`（:494-498），再 `NPUComboKernel.horizontal_partition(custom_algorithm=...)` 分组（:500-506），逐组新建 `NPUComboKernel(triton_kernel_cls, enable_autotune, mixed_sizes, per_subkernel_blocks)` 并以 `create_sub_kernel` 复用子核 tiling（:513-537）。

## define_kernel 命名与缓存（:540-615）

缓存键 `(src_code, kernel_graph_hash)` 命中直接复用名字（:542-551）；未命中时 `fused_name` 截 35 字符、拼 `npu_extra_name`、类别取 `get_kernel_category_by_source_code(src)[:3]`，名字为 `triton_<cat>_<fused>_<suffix>`（:553-566）；`"#pragma CMT"` 改写为 `"#"`（:580）；包装为 `async_compile.triton(<subs_name>, '''src''', device_str='<device.type>')`（:584-588）；元数据注释附 SchedulerNodes 列表，dump_fx_graph 时再附 Graph Module str（:590-603）；`metrics.log_kernel_metadata`（:612-613）。

## benchmark_fused_nodes（:617-696）

`preserve_rng_state` + `torch.npu.device` 下生成基准代码并 `PyCodeCache.load`；`.kernel_perf` 侧车文件缓存毫秒值（:626-649）；编译异常 → `ms=inf` 并缓存（:656-666）；`launchers[0].n_spills>0` → 直接 inf 跳过基准（:668-672）；基准用 `benchmarker.benchmark_gpu(..., device_type='npu')`，且 `mutated_arg_names>0` 时**扣除 clone_args 的开销**（:684-688）——inplace 变异核的融合判定校正。

## can_fuse 融合判定（:751-926）

- foreach 节点交给专用 can_fuse（:757-760）；任一端是 `FlexAttentionDispatchTemplateBuffer` → 不融合（:766-772）；NPU flex 模板 epilogue 不能 load 其他 Triton 模板输出（xindex 不在模板 range tree，:774-797）。
- split scan 与规约冲突只 `why()` 记录原因，**不提前返回**（:799-804），继续走 numel/rnumel 匹配。
- 双规约：numel/rnumel 全等才融合（:806-816）。双方非规约：组不等时若 node2 是模板则按 prologue 节点组匹配（模板前 break，:818-849）；随后仅 `TritonTemplateBuffer` 可融合（:851-860）；`tiling_prevents_pointwise_fusion` 下做三向 `select_tiling` 比较（仅当某 tiling len>2 才要求三方一致，:862-885）。
- pointwise+reduction：`numel1 == numel2*rnumel2` 时要求 node1 全部节点通过 `NPUIndexTritonKernel.is_compatible((numel2, rnumel2), ranges)`（:888-897）；`tiling_prevents_reduction_fusion` 下把合法 tiling 值收进 `valid_tiling_group`（含 NumelList 展开三元组，:902-916）。
- 规约+非规约交换参数递归（:923-926）；`can_fuse_vertical/can_fuse_horizontal` 均为同一函数别名（:928-929）。

## candidate_tilings（:930-1050）

classmethod + `lru_cache(32)`（:931-933）。`tile_ranges` 内：无折叠基线候选 `"none"`（:955-960，注意此处把 `is_pointwise` 布尔字面量传给 `create_partial_tiling` 的 reduction_numel 形参位）；对每个写读依赖取 `stride_hints`，`split = strides.index(1)+1`，split 到尾或后缀全零则跳过（:968-978）；`score = optimization_hint(非零 stride 元素积)`，写依赖 ×2（注释引 ngimel：连续写比读重要）、两段 good_size 各 ×2（:984-999）；**仅当 score ≥ 全 ranges×reduction_ranges 积**才追加折叠候选（:1001-1012）；`complete_partial_tiling` 补齐（:1026-1033）；双侧 ranges 均 ≤1 维直接返回空（:1038-1040）。

## 失效边界与静态口径

- 全部为主线静态事实：调度与融合判定未运行；`why()` 记录不等于运行时决策可观测；benchmark 缓存/inf 语义按字面控制流读出。
- `contains_welford_group` 的 `_welford_output_group` 判定本体在 choices.py（只读 :59-65 入口与 `patch_inductor_choices` 头部 :68-76，`InductorChoices.can_fuse` 补丁体仅部分覆盖）。
- 上游继承成员 `select_tiling` 的实现在六 pin 外，三向比较只记录调用形态。
- `eval()` 提取 inductor_meta 是真实实现（非笔误），其安全性风险不在此评注；静态口径只记录行为。

## 相邻卡边界

[Grid/launcher 卡](torch_npu_main_inductor_grid_and_launcher_generation.md)与[deferred/codegen cpp wrapper 卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)（launch/包装侧）；[flex 前向分发卡](torch_npu_flex_attention_forward_dispatch.md)（FlexAttentionDispatchTemplateBuffer 分发主体）；[DVM 融合卡](torch_npu_dvm_mlir_codegen_and_fallback.md)（dvm 侧调度，与本卡 Triton 调度不同 backend）；[发布版 split_tiling 函数卡](torch_npu_release_inductor_split_tiling_functions.md)与[主线轴选择卡](torch_npu_main_inductor_split_tiling_axis_selection.md)（`select_tiling` 的 NPU SplitTiling 侧对应物为 split_tiling.py，非本文件）。测试侧契约见[归约/Welford 测试契约卡](torch_npu_main_inductor_reduction_welford_tests.md)（test_var_mean.py 结构断言、test_npu_kernel_features.py NumelList 单元契约）与[调度/分区测试契约卡](torch_npu_main_inductor_scheduling_partition_tests.md)（test_overlap_scheduling_npu.py/test_inductor_graph_partition.py 等）。

## Evidence

- [主线 codegen/scheduling.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/scheduling.py)（primary；`:1-245`、`:246-505`、`:506-785`、`:786-930`、`:927-1050` 五窗读）
- [主线 codegen/npu_kernel_features.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/npu_kernel_features.py)（implementation；`NumelList` :8-20 字面读）
- [主线 choices.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/choices.py)（implementation；`contains_welford_group` :59-65 与 patch 头 :68-76 字面读，patch 体仅部分覆盖）
- [发布版 codegen/scheduling.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/scheduling.py)（implementation；两代文件差异对照锚——发布 595 行无本卡 Welford/NumelList/combo/flex 面，仅 :440-455 SplitTiling 消费已读）
