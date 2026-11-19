---
type: Guide
title: 主线 FlexAttention NPU 模板族：包装上游模板、网格封顶与紧凑 mask 预处理
description: 固定提交下 _inductor/kernel/flexattention_template.py 1846 行全文本体：三上游模板同名重注册、14 个 NPU 模板与 grid 函数、编译选项预设、LSE log2 数值契约与 tasklist 拆分/归并源。
tags:
- task.optimization
- topic.attention
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flexattention_template.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_template.py
  role: implementation
created_at: '2026-11-12T17:10:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 FlexAttention NPU 模板族：包装上游模板、网格封顶与紧凑 mask 预处理

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `torch_npu/_inductor/kernel/flexattention_template.py`（1846 行）全文静态阅读；发布 pin `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 无 `_inductor/kernel/` 目录，整族为主线能力（负向 rg）。本卡补模板本体；派发/静态门槛由[前向派发卡](torch_npu_flex_attention_forward_dispatch.md)、[mask 内存路径卡](torch_npu_flex_attention_mask_memory_paths.md)、[tasklist 运行时卡](../../../../training/guides/torch_npu_flex_attention_dkdv_tasklist_runtime.md)、[后向路由卡](../../../../training/guides/torch_npu_flex_attention_backward_routes_and_gradients.md)与[测试卡](torch_npu_main_inductor_flex_attention_tests.md)持有，不重述。未编译、未运行、未创建 block mask。

## 上游模板包装与版本回退

文件头两级 ImportError 回退：`torch._inductor.kernel.flex.flex_attention` → `torch._inductor.kernel.flex_attention`（SymbolicGridFn/前反向模板），`flex.flex_decoding` → `flex_decoding`，两级均失败时 SymbolicGridFn 退化为恒等装饰器（:3-29）。`_wrap_upstream_template`（:84-95）把上游模板 `__dict__` 原样搬到新 NPUTritonTemplate、清空 manual_output_buffer、置 npu_extra_name 与空编译选项，再以**同名**写回 `TritonTemplate.all_templates`——同名重注册即定向覆盖上游选择条目；三个包装对象分别是 flex_attention_template（fwd_main）、flex_attention_backward_template（bwd_main）、flex_decoding_template（fwd_decode）（:870-881）。包装不复制 kernel 源，模板体仍是上游定义；[测试卡](torch_npu_main_inductor_flex_attention_tests.md)的 `_wrap_upstream_template(` 结构断言与此配对。

## 14 个 NPU 模板与 grid 契约

| 模板（name / npu_extra_name） | grid | 要点 |
|---|---|---|
| flex_attention_fwd_mask_out / fwd_main | `flex_attention_in_loop_grid` | `(min(total_tiles, NUM_CUBE_CORE),1,1)`，total_tiles=cdiv(Q_LEN,BLOCK_M)*Z*HQ（:820-826） |
| flex_attention_fwd_mask_out_all_sparse / fwd_sparse | 同上 | 同 ABI/源码，编译变体关 HAS_FULL_BLOCKS（:899-907） |
| flex_attention_compact_offsets / mask_offsets | `compact_offsets_grid`=(1,1,1) | 单 program 持 carry 的有界扫描（:831-833） |
| flex_attention_compact_mapping / mask_mapping | `compact_mapping_grid` | `max(1,min(row_count,NUM_VECTOR_CORE))`（:836-839） |
| flex_attention_fwd_mask_compact / fwd_compact | `compact_sparse_mask_grid` | `max(1,min(actual_blocks*NUM_Q_SUB*NUM_KV_SUB, NUM_VECTOR_CORE))`（:847-858） |
| flex_attention_fwd_workspace_offsets / fwd_ws_offsets | (1,1,1) | manual_output_buffer="arg_Q_OFFSETS"（:930-936） |
| flex_attention_fwd_workspace_mask_compact / fwd_ws_compact | 同 fwd_compact | 精确分配变体（下节） |
| flex_attention_bwd_mask_compact / bwd_compact | 同 fwd_compact | manual_output_buffer="arg_SPARSE_MASK"（:945-951） |
| flex_attention_bwd_mask_pos / bwd_mask_pos | `sparse_mask_block_pos_grid` | `max(1,min(actual_blocks,NUM_VECTOR_CORE))`（:861-867/:953-958） |
| flex_attention_bwd_dq_mask_out / bwd_dq | `flex_attention_backward_dq_grid` | `(meta["DQ_LAUNCH_PROGRAMS"],1,1)`（:961-965/:1808-1814） |
| flex_attention_bwd_dkdv_mask_out / bwd_dkdv | `flex_attention_backward_dkdv_grid` | `(meta["LAUNCH_PROGRAMS"],1,1)`（:968-972/:1816-1822） |
| flex_attention_bwd_dkdv_tasklist / bwd_tasklist | 同上 | WORK_ITEMS/TASK_OFFSETS 驱动（:1824-1830） |
| flex_attention_bwd_dkdv_tasklist_no_split / bwd_task_nosplit | 同上 | 同源码 + TASKLIST_NO_SPLIT 变体（:1832-1838） |
| flex_attention_bwd_dkdv_reduce / bwd_reduce | 同上 | 拆分 partial 归并（:1840-1846） |

grid 分工是结构事实：主前向/反向按 **Cube 核数**封顶，mask 预处理按 **Vector 核数**封顶且下限 1 program，offsets 扫描恒单 program。

## 编译选项预设（:37-81）

- `_FWD_COMPILE_OPTIONS`：enable_ubuf_saving/unit_flag、set_workspace_multibuffer=4、limit_auto_multi_buffer_buffer="no-limit"、hfusion_enable_multiple_consumer_fusion、multibuffer=False、tile_mix_vector/cube_loop=0、buf_slot_num_of_veccore=3/crosscore=2、intra/inter_cache_num=3/2（注释：Triton-Ascend 选项合并前的兼容名）、enable_cross_if_fusion/enable_buffer_insert_optimization/enable_ub_refine_opt。
- `_BWD_DQ_COMPILE_OPTIONS`：no-limit、no-l0c、veccore 3/crosscore 2、enable_select_analysis=False。
- `_BWD_DKDV_COMPILE_OPTIONS`：unit_flag、no-l0c、veccore 2/crosscore 1、intra/inter 2/1。

三套预设均为生成代码的编译器开关面，其运行收益未验证；不据预设推导任何必然融合/加速。

## 前向 mask-out kernel 结构（:583-748）

持久 CTA 形态：`for tile_id in range(tl.program_id(0), NUM_Q_TILES*ZQ*HQ, tl.num_programs(0))`。GQA 映射 off_hkv=off_hq//GQA_SHARED_HEADS、off_zkv=off_zq%ZKV；B>1 时 B=1 block-mask 以取模广播（sparse_idx_z=off_zq%SPARSE_Z，:616-619）。`TORCHINDUCTOR_FLEXATTENTION_MASKOUT` jinja 开关二选一：开启时从预计算 SPARSE_MASK（int8）按 flat_blk+局部偏移加载（:430-465），关闭时内联 mask_mod subgraph_1 并按 q_len/kv_len 边界收窄（:466-477）。`HAS_FULL_BLOCKS` 双层：partial 块经 forward_inner_sparse_mask_direct_index 逐 KV 块直索引（block_n_end=min(kv_num_blocks*SPARSE_KV_MULTIPLE, max(cdiv(KV_LEN,BLOCK_N),1))），full 块走 forward_block_mn_full 免 mask（:668-719）。数值：`qk=tl.dot(q,trans(k),input_precision="ieee")`；m_ij 取 propagate_nan=ALL 的行最大；ROWS_GUARANTEED_SAFE 不成立时 -inf 行压 0；l_i==0 行归一前置 1。**LSE 以 log2 存**（`lse*1.4426950408889634`，:732-736），OUTPUT_MAX 可选输出 m_i。

## 紧凑 mask 预处理链（:105-390/:909-958）

- offsets 扫描：`SCAN_TILE_ROWS` 有界分片 cumsum，carry 由单 program 跨片携带，TOTAL_BLOCKS 标量由该 program 独占写（无原子/初始化，:112-127）；workspace 变体单块 cumsum 且 Q_OFFSETS 以 manual_output_buffer 传入（:238-256）。
- mapping：FLAT_TO_ROW/FLAT_TO_BLK 按 num_programs 跨行循环写（:131-166）。
- 物化：compute_sparse_mask_kernel_compact 按 actual_blocks*NUM_Q_SUB*NUM_KV_SUB 条目经 mask_mod subgraph_0 生成 int8 mask，store_mask=q/k 边界；bwd 变体存 `mask_mod_output & store_mask`（:169-235/:281-348）。
- block_pos 反向索引：kv_block → flat_blk 写 SPARSE_MASK_BLOCK_POS（:350-390）。
- **精确分配变体** `compute_fwd_workspace_mask_compact`（:259-278）以三段 `.replace()` 从物化源派生：actual_blocks 改为 `Q_OFFSETS[last_row]+last_count` 现场读数（workspace 映射缓冲保留 C 槽、其 shape 不得当作活块数——注释原义），m/n 钳到 q_len-1/kv_len-1。字符串派生意味着两变体共享源文本，改物化源会隐式改变 workspace 变体。

## 反向 dq/dkdv（:975-1494）

- dq（qmajor）：持久任务循环 `for task_id in range(pid, DQ_NUM_TASKS, num_core)`；**LSE 消费侧统一 `lse*0.6931471805599453` 回自然底并把 -inf 归 0**（:1054-1057）；partial 块按 Q_OFFSETS+blk_pos 取 flat_blk 读 mask，full 块注释明示免 mask；`dq*=SM_SCALE` 在循环外统一施加（:1160），PRESCALE_QK 时不在此再乘；SAFE_HEAD_DIM 决定 store mask 是否含头维检查。
- dkdv：任务按 NUM_KV_BLOCKS*ZQ*HKV 划分，GQA 内层 off_g 循环；hi=min(sparse_q_num_blocks*SPARSE_Q_MULTIPLE, max(cdiv(Q_LEN,BLOCK_M1),1))。partial 块经 SPARSE_MASK_BLOCK_POS 反查 flat_blk，`safe_partial_block_idx=tl.maximum(partial_block_idx,0)` 且 mask 条件并上 `partial_block_idx>=0`（负哨兵块整体置 -inf，:1364-1389）；DV/DK 均 `tl.atomic_add` 累加，dk 仅 PRESCALE_QK 时乘 SM_SCALE。

## tasklist 拆分源与归并（:1496-1742/:1744-1806）

`_FLEX_ATTENTION_BACKWARD_DKDV_HELPERS_MARKER/SOURCE` 以字符串 `index()` 从 dkdv_only_source 切出 `bwd_dkdv_block_mn` 起的 helpers 段并拼接到 tasklist 源尾——helpers 跨模板复用靠源码文本拼接而非 import。tasklist kernel 按 meta_id 读 TASK_OFFSETS 区间，逐 WORK_ITEMS 5 元组（off_hkv/kv_start_block/sub_id/split_count/is_split）执行；`off_zq/off_zkv/sparse_idx_z` 被显式置零（:1554-1556，批次维折叠进工作项的前提）；`TASKLIST_NO_SPLIT` 变体去掉 is_split 分支直写 DV；拆分时写 DK_PARTIAL/DV_PARTIAL（sub_id*PARTIAL_DK/DV_STRIDE）。reduce kernel 按 SPLIT_BASES 3 元组对 split_count 个 partial 求和写回 DK/DV。运行时判据/缓存/UB 筛选见[tasklist 运行时卡](../../../../training/guides/torch_npu_flex_attention_dkdv_tasklist_runtime.md)，此处只记模板侧合同。

## triton_experimental 适配层（252 行）

`triton_experimental/flex_attention/flex_attention_template.py` 从本文件 import 源码串、grid 与编译选项（:10-31）；`ExperimentalTemplateKernel.jit_lines` 把默认装饰器 `@triton_heuristics.template(` 整体替换为 `@npu_triton_heuristics.template(`，替换前断言 marker 恰出现一次（默认模板装饰器变化即 RuntimeError，:33-40）；`_experimental_def_kernel` 用 AST 复制 NPUTritonTemplateKernel.def_kernel 并在 import 行追加 `from torch_npu._inductor.triton_experimental import npu_triton_heuristics`（:43-55）——该行即测试卡的 EXPERIMENTAL_MARKER 字面量。适配层不复制 kernel 源，源文本与本卡上述各节同源共享。

## 边界

全部为模板源码合同：模板被选择、编译成功、数值正确性、NUM_CUBE_CORE/NUM_VECTOR_CORE 实际取值、tasklist 拆分是否被采纳均未运行验证；发布 pin 无此文件，不外推发布行为。本卡不覆盖 flex_attention.py/flex_attention_dispatch.py（既有卡持有）。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flexattention_template.py)（primary）：全文 1846 行
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_template.py)（implementation）：全文 252 行
