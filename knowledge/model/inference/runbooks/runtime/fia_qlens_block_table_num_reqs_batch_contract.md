---
type: Runbook
title: FIA/qlens 的 block_table 首维 / num_reqs / TND seq-len 须等实际 batch：被 SP-padding 或整缓冲首维打破 → 算子 shape 校验失败
description: 昇腾 FIA / qlens 融合 attention 算子（npu_fused_infer_attention_score、torch_npu._npu_flash_attention_qlens）对分页 KV 的 block_table 首维、请求数 num_reqs、以及 TND 布局下序列长度末元素有严格 shape 契约，三者须等于本次前向的实际 batch（query_lens.shape[0]）；Ascend 950 校验尤严（num_reqs 必须等于 block_table.shape[0]）。三个信号打破该不变量：(A) FlashComm1/SP 为满足 FIA TND 约束对 num_tokens/num_reqs 做 padding，但门控只判 pcp_size==1 漏判 dcp，与 decode/prefill context-parallel（DCP/PCP）切分布局重叠致 serve 报错，修法收紧为 pcp_size*dcp_size==1；(B) SP-padding 补出的 num_reqs_padded 多补 1 但 block_table 未同步 unpad，eagle drafter eager 分支 attention 校验失败，修法按 num_reqs_padded 对 block_table_tensor 做 _adjust_tensor unpad；(C) PrefillCacheHit 路径把 hybrid kv groups 撑大首维的整块 block_tables 缓冲透传 qlens 算子，修法 block_tables[:batch_size,:] 按实际 batch 切片。通用判据：SP-padding 或整缓冲透传动过 block_table/num_reqs/TND seq-len 后须核对是否仍等实际 batch，症状为下发/校验阶段 shape 不匹配而非精度异常。落点均在 vllm-ascend（model_runner_v1.py execute_model、spec_decode/eagle_proposer.py、attention/attention_v1.py）。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.graph_execution
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/7673
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/7986
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/1297
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# FIA/qlens 的 block_table 首维 / num_reqs / TND seq-len 须等实际 batch：被 SP-padding 或整缓冲首维打破 → 算子 shape 校验失败

## 适用场景

昇腾 [FIA](../../concepts/kernels/fused_infer_attention_score.md) 系列融合 attention 算子（`npu_fused_infer_attention_score` 及 flash-attention 的 qlens 变体 `torch_npu._npu_flash_attention_qlens`）对**分页 KV 的 `block_table` 首维、请求数 `num_reqs`、以及 TND 布局下的序列长度末元素**都有严格的形状契约：它们必须与本次前向的**实际 batch / 实际 token 数**一致。契约本身是算子固有输入约束（尤其在 Ascend 950 上校验更严），并非某个模型或某个 PR 独有；只要 attention 前向路径上有一层给这些量做了**对不上实际 batch 的填充或整缓冲透传**，算子就会在下发/校验阶段因维度不匹配报错，还没进真正的计算。

核对时先按下述三种来源定位落在哪一类：

- **序列并行填充溢出到不该进的路径**：`enable_sp`（FlashComm1/SP）为满足 FIA 的 TND 布局约束而对 `num_tokens`/`num_reqs` 做 padding，但门控没排除 decode/prefill context-parallel（DCP/PCP），SP-padding 与 CP 的切分布局重叠。
- **SP-padding 补出的 num_reqs 未同步 unpad 到 block_table**：投机解码 drafter 的 attention 用到被 SP 多补 1 的 `num_reqs_padded`，而 `block_table` 首维没跟着调整，950 FIA 严格校验 `num_reqs == block_table.shape[0]` 直接失败。
- **整块 block_table 缓冲首维大于实际 batch**：prefix-cache 命中路径直接把整块已分配的块表缓冲透传给 qlens 算子，缓冲首维（行数）大于本次请求的实际 batch。

三者的通用修法都是**把交给算子的 block_table / num_reqs 收敛到实际 batch**：按实际 batch 切片、对齐 padding、或收紧门控不让填充进错误路径。

## 信号 → 根因 → 修法

### 信号 A：SP-padding 与 context-parallel 重叠 → serve 报错 / 不可预测 padding

- **信号**：在 vllm-ascend 上同时开启 FlashComm1/SP（`enable_sp()==True`）与 decode/prefill context parallel（`dcp_size>1` 或 `pcp_size>1`）时，serve 报错或出现不可预测的 padding 行为；非 MLA 模型（dense，如 Qwen2.5）尤其。
- **触发条件**：`execute_model` 中有一个只应在 graph FULL 或 SP 场景进入的 `num_tokens` 令牌填充分支，进分支后调 `_pad_query_start_loc_for_fia` 对 `query_start_loc`/`num_reqs_padded` 做 padding。该函数唯一目的是满足 **FIA 的 TND 布局约束**：TND 布局下 `hidden_states` 首维必须等于 `actual_seq_lengths_q` 的末元素。
- **根因**：修复前门控只检查 `pcp_size == 1`（带 `# TODO: fix this`），**漏判 `dcp_size`**。DCP 会改变 token/请求在各 rank 上的切分布局，与 SP 为满足 FIA TND 约束所做的 `num_tokens`/`num_reqs` padding 相互重叠、不再一致。仓内 release notes 独立记录同类已知问题（DeepSeek-v3.2 场景「PCP & DCP do not yet work with FlashComm1」，可致 serve error）佐证 FC1 与 context-parallel 的重叠会产生不可预测行为。
- **修法**：把门控收紧为要求 pcp 与 dcp **都关闭**（乘积为 1），即 SP+FIA TND 填充仅在两个 CP 维都为 1 时才允许进入：

```python
if (
    cudagraph_mode == CUDAGraphMode.FULL
    or (enable_sp() and not self.model_config.use_mla)
    and self.pcp_size * self.dcp_size == 1   # 修复前为 pcp_size == 1，漏判 dcp
):
```

DCP（或 PCP）开启时即使 SP 打开也不再进 SP+FIA 令牌填充分支，避免 FIA TND padding 与 CP 布局重叠。分支内逻辑不变（`_pad_query_start_loc_for_fia` 满足 TND 约束；`enable_sp() and num_tokens_padded==num_tokens_unpadded` 时回滚 dummy request 的 `num_reqs_padded`）。回归覆盖：4 卡 DCP e2e（`decode_context_parallel_size=2, enable_expert_parallel=True, block_size=128`）叠加 `compilation_config={"pass_config": {"enable_sp": True}}`，覆盖 SP+DCP 组合。

### 信号 B：SP-padding 补出的 num_reqs 未同步到 block_table → 950 FIA 校验 num_reqs==block_table 首维失败

- **信号**：Ascend 950（atlas-950）上，`enable_sp` + 投机解码 eagle/eagle3 + eager 模式（非图模式）+ 非 MLA + `pcp_size*dcp_size==1` 组合下，drafter 模型的 attention 计算失败于 FIA 算子的形状校验。
- **触发条件**：`enable_sp` 下 model runner 里 `_pad_query_start_loc_for_fia` 会对 `num_tokens` 做 padding，某些场景补齐后的 `num_reqs_padded` 比原始请求数**多 1**；但 `vllm_ascend/attention/utils` 里既有的 unpad 方法**不支持对 block_table 做 unpad**。于是开 eagle 时 drafter attention 的请求数与 `block_table` 首维不一致。
- **根因**：**Ascend 950 的 FIA 算子校验更严，要求「请求数 num_reqs 必须等于 block_table 第一维」**。这是 FIA 在 950 上的固有输入契约，与具体模型无关——在 950 上组合 SP-padding + eagle + FIA 都会撞同一维度不匹配。
- **修法**：在 drafter 的 eager 分支，对 `block_table_tensor` 按 `num_reqs_padded` 做 unpad（`_adjust_tensor`），使其首维与 FIA 期望的请求数对齐：

```python
num_reqs_padded = common_attn_metadata.num_reqs
# padding 由 model runner 的 _pad_query_start_loc_for_fia 施加，eager 模式需在此 unpad 保持兼容
if (enable_sp() and not self.vllm_config.model_config.use_mla) and self.pcp_size * self.dcp_size == 1:
    common_attn_metadata.block_table_tensor = self._adjust_tensor(
        common_attn_metadata.block_table_tensor, num_reqs_padded
    )
```

修复后 `block_table` 首维与 `num_reqs` 对齐，绕过 950 FIA 严格校验，eager 模式下 SP + eagle 的 drafter attention 正常计算。（合并态门控为无参 `enable_sp()` + `not use_mla` + `pcp_size*dcp_size==1`；reviewer 曾建议再加 `method=="eagle3"` 门控，但未体现在合并 diff 中。）

### 信号 C：整块 block_table 缓冲首维大于实际 batch → qlens 算子 shape 报错

- **信号**：同时开 prefix-cache（eager 或非 eager 均可）与 Ascend Scheduler，发送两个完全相同的请求即可复现——命中 `AscendAttentionState.PrefillCacheHit` 状态时，`torch_npu._npu_flash_attention_qlens` 抛 shape 错误。该场景触发门槛低、影响面广。
- **触发条件**：PrefillCacheHit 分支原先直接把 `attn_metadata.block_tables`（整块已分配的块表缓冲）作为 `block_table` 传给 qlens 算子。该缓冲首维（行数）由 hybrid kv groups 引入的 shape 撑大，大于本次请求的实际 batch（`query_lens` 的条数）。
- **根因**：qlens 融合 attention 需要 `block_table` 的首维与本次请求的**实际 batch 一致**；整缓冲首维过大即触发 shape 不匹配。
- **修法**：传参前按实际 batch 切片块表（`query_lens.shape[0]` 即实际 batch 条数）：

```python
compress_mask = attn_metadata.attn_mask
batch_size = attn_metadata.query_lens.shape[0]
block_table = attn_metadata.block_tables[:batch_size, :]   # 原为整块 attn_metadata.block_tables
torch_npu._npu_flash_attention_qlens(
    query=query, key_cache=self.key_cache, value_cache=self.value_cache,
    block_table=block_table, mask=compress_mask,
    seq_len=attn_metadata.query_lens, context_lens=attn_metadata.seq_lens,
    num_kv_heads=self.num_kv_heads, num_heads=self.num_heads,
    scale_value=self.scale, out=output)
```

切掉块表缓冲中超出实际 batch 的多余行后 shape 与算子期望对齐，不再报错。

## 通用判据（运行时可复用）

给 FIA/qlens 系列 attention 算子传 `block_table` / `num_reqs` / TND seq-len 时，凡这三个量被下述任一层动过，都要核对是否仍等于**实际 batch**：

- **序列并行（SP / FlashComm1）填充**：SP 为满足 FIA TND 约束会 pad `num_tokens`/`num_reqs`；确认它 (1) 没进不该进的路径（context-parallel 开启时应被 `pcp_size*dcp_size==1` 门控挡住），(2) 补出的 `num_reqs_padded` 已同步 unpad 到 `block_table`（尤其 950 严格校验 `num_reqs==block_table.shape[0]`）。
- **整缓冲透传**：任何直接把整块已分配缓冲（block_tables / hybrid kv groups 撑大的 shape）交给算子的路径，先按实际 batch 切片 `[:batch_size, :]`，`batch_size = query_lens.shape[0]`。

症状统一表现为**下发/校验阶段的 shape 不匹配报错或不可预测 padding**，不是运行时精度异常；逐项核对后收敛到实际 batch 即可。

## 参考实现及其约束

三处均在 vllm-project/vllm-ascend（vLLM 的昇腾 NPU 后端），落点各异：

- 信号 A：`vllm_ascend/worker/model_runner_v1.py::execute_model` 的令牌填充分支门控（`_pad_query_start_loc_for_fia` 在 L558-596，其注释确证为满足 FIA TND 布局约束）。源覆盖 Qwen2.5 dense / DeepSeek-v3.2 已知问题。
- 信号 B：`vllm_ascend/spec_decode/eagle_proposer.py::_propose` 的 eager 分支；根因为 950 FIA 严格校验 num_reqs==block_table 首维。限定 atlas-950 + SP-padding + eagle + eager。
- 信号 C：`vllm_ascend/attention/attention_v1.py::forward` 的 PrefillCacheHit 分支调 `torch_npu._npu_flash_attention_qlens`。触发条件为 prefix-cache + Ascend Scheduler + 相同请求。

这些是**这三条具体路径当前的 shape 契约与门控事实**，属该参考实现的约束；「block_table 首维 / num_reqs / TND seq-len 须等实际 batch」这一算子级不变量可迁移，但「950 校验更严」「hybrid kv groups 撑大缓冲首维」等是各来源的具体成因，不外推为整个昇腾栈通用律。三者均未给出前后性能/精度数字。

## 相关经验

- FIA 变长实参形态随后端不同（host list vs Tensor）：[fia-actual-seq-lengths-kv-backend-type](fia_actual_seq_lengths_kv_backend_type.md)。
- FIA MLA 无量化路径的 group_num 硬约束：[fia-mla-noquant-group-num-power-of-two](../compilation/fia_mla_noquant_group_num_power_of_two.md)。
- 非 PA 路径 Q/KV 布局一致性约束（同为「attention 算子输入契约传错就在下发前失败」）：[sfaa-nonpa-qkv-layout-constraint](../../optimizations/experience/rules/sfaa_nonpa_qkv_layout_constraint.md)。
- MTP/投机解码上线前置约束：[mtp-speculative-decode-graph-mode-prereqs](mtp_speculative_decode_graph_mode_prereqs.md)。

## 相关概念页

- [fused-infer-attention-score](../../concepts/kernels/fused_infer_attention_score.md) — FIA 融合 attention 算子（含 qlens 变体）。
- [mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md) — 投机解码 / eagle drafter（信号 B 触发场景）。
- [context-parallel](../../concepts/parallelism/context_parallel.md) — decode/prefill context parallel（DCP/PCP，信号 A 门控维度）。

## Evidence

- **信号 A**（`diff 事实`，vllm-ascend `@11e0583474434de15a8968b7fe76a8d5da40f6e7`）：`model_runner_v1.py` L1285-1300 门控条件由 `pcp_size==1` 改为 `pcp_size*dcp_size==1`；`_pad_query_start_loc_for_fia`（L558-596）注释确证其为满足 FIA TND 布局约束的 padding；release notes L144 独立记录 PCP & DCP 与 FlashComm1 不兼容。
  - 溯源下探：[vllm-ascend-pr-7673-bugfix-support-flashcomm1-dcp-for-qwen](https://github.com/vllm-project/vllm-ascend/pull/7673)（sha 11e0583474434de15a8968b7fe76a8d5da40f6e7）。
- **信号 B**（`diff 事实`，vllm-ascend `@c9423d19ce4a674f46ebf210dab4248035a66148`）：`eagle_proposer.py::_propose` eager 分支新增按 `num_reqs_padded` 对 `block_table_tensor` 做 unpad（`_adjust_tensor`）；根因（950 FIA 严格校验 num_reqs==block_table 首维）为 PR 描述披露、非独立复测。
  - 溯源下探：[vllm-ascend-pr-7986-bugfix-unpad-block-table-when-enable-sp-and-eagle3-in-eager-mode](https://github.com/vllm-project/vllm-ascend/pull/7986)（sha c9423d19ce4a674f46ebf210dab4248035a66148）。
- **信号 C**（`diff 事实`，vllm-ascend merge commit `105d2df0348a24be88a3031962320cc5bab75e49`）：`attention_v1.py::forward` PrefillCacheHit 分支新增 `batch_size = attn_metadata.query_lens.shape[0]` 与 `block_table = attn_metadata.block_tables[:batch_size, :]`，传入 qlens 的 block_table 由整缓冲改为切片值；触发条件（prefix-cache + Ascend Scheduler + 相同请求）为源自述、非独立复测；已 backport 到 v0.9.1 分支。
  - 溯源下探：[vllm-ascend-pr-1297-v0-9-1-fix-fix-block-table-shape](https://github.com/vllm-project/vllm-ascend/pull/1297)（sha 105d2df0348a24be88a3031962320cc5bab75e49）。