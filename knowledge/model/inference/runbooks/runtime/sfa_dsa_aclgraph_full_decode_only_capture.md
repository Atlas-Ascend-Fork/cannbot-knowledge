---
type: Runbook
title: 稀疏注意力接 aclgraph FULL_DECODE_ONLY 全图 decode：申报级别与 metadata 切片口径的两类捕获失败
description: 稀疏注意力（SFA/DSA，MLA 家族稀疏变体，如 DeepSeek-V3.2）接昇腾 aclgraph 全图 decode 捕获（CUDAGraphMode.FULL_DECODE_ONLY）时的两类图捕获失败签名，根因均系于「图捕获要求每次 replay 张量 shape 固定」契约。信号一：注意力后端 get_cudagraph_support() 只申报 AttentionCGSupport.UNIFORM_SINGLE_TOKEN_DECODE（仅捕获 query_len==1 纯单 token decode），叠加 MTP 投机解码后 query_len=1+num_speculative_tokens>1 的 uniform 批落在可捕获集合外，算子无法编译进图；修法是改申报 UNIFORM_BATCH（捕获 query 长度一致的批，含 spec-decode），与同仓 MLA 后端 mla_v1.py 对齐。信号二：attention metadata builder 用随请求波动的真实 num_actual_tokens 切 slot_mapping/positions/sin/cos，或 builder 与 forward 两侧切片口径不一致（num_input_tokens vs num_actual_tokens），触发 infer shape error；修法是 builder 统一按 padded 长度 num_input_tokens 切片、sin/cos in-place 写进预分配固定长度缓冲、cum_query_lens/seq_lens 改用 device 常驻张量、forward 侧移除 [:num_actual_tokens] 二次切片、model runner 对 query_start_loc 做 uniform-decode padding、把 SpecDecoding 纳入 build_for_graph_capture 分支。附正交约束：enable_sfa_cp（FlashComm1）与 FULL_DECODE_ONLY 互斥。参考实现在 vllm-ascend 的 sfa_v1.py / mla_v1.py / model_runner_v1.py。
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5679
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/4706
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 稀疏注意力接 aclgraph FULL_DECODE_ONLY 全图 decode：申报级别与 metadata 切片口径的两类捕获失败

## 适用场景

把一个稀疏注意力模型（[SFA / DSA](../../concepts/kernels/sparse_flash_attention.md)，即 MLA 家族的稀疏变体，如 DeepSeek-V3.2）接到昇腾 aclgraph 的**全图 decode 捕获**（[npu 图模式](../../concepts/techniques/npu_graph_mode.md)的 `CUDAGraphMode.FULL_DECODE_ONLY`）时，会撞到两类不同的捕获失败，都源于「图捕获要求每次 replay 的张量 shape 固定不变」这一契约：

1. **算子进不了图**——注意力后端向图捕获机制申报的支持级别太窄，覆盖不到 decode 批的真实 query 形态（尤其叠加 [MTP 投机解码](../../concepts/techniques/mtp_speculative_decoding.md)时 query_len>1）。
2. **infer shape error**——metadata builder 用随请求波动的真实 token 数去切张量，与捕获态固定 shape 不符；或 builder 与 forward 两侧切片口径不一致。

若你正在观测到「同时开 MTP + full_decode_only 后算子无法编译进图」或「decode 全图捕获路径下 infer shape errors」，本页给出两个信号的根因与修法。

## 信号一：get_cudagraph_support 申报级别太窄 → 算子进不了图

**信号 / 症状**：把某注意力后端接入 `FULL_DECODE_ONLY` 图模式、并同时开启 MTP 投机解码后，算子无法被编译进图（operators cannot be compiled into the graph）。纯单 token decode（不开 MTP）时正常，一开 MTP 就失效。

**触发条件**：`compilation_config.cudagraph_mode == CUDAGraphMode.FULL_DECODE_ONLY` **且** 开启 MTP（multi-token prediction / 投机解码）。

**根因**：注意力后端通过 `get_cudagraph_support()` 向图捕获机制**申报本后端支持捕获哪一类批**。上游枚举 `AttentionCGSupport` 的语义是固有契约：

| 申报级别 | 含义 |
|---|---|
| `UNIFORM_SINGLE_TOKEN_DECODE` | 仅当批内所有 `query_len == 1`（纯单 token decode）时支持图捕获 |
| `UNIFORM_BATCH` | 批内 query 长度**一致**即支持图捕获，可用于 spec-decode——即 `decodes 为 1 + num_speculative_tokens` |

MTP / 投机解码下每个 decode 请求的 `query_len = 1 + num_speculative_tokens`（>1）。这些批是 uniform（长度一致）但**非单 token**；若后端只申报 `UNIFORM_SINGLE_TOKEN_DECODE`，这些 MTP decode 批就落在可图捕获集合之外，算子进不了图。

**修法**：让该注意力后端的 `get_cudagraph_support()` 申报 `UNIFORM_BATCH` 而非 `UNIFORM_SINGLE_TOKEN_DECODE`——放开对更大范围 uniform 批（含 MTP 的多 token uniform decode 批）的图捕获：

```python
-        return AttentionCGSupport.UNIFORM_SINGLE_TOKEN_DECODE
+        return AttentionCGSupport.UNIFORM_BATCH
```

排查约定：在昇腾上要让某注意力后端在 `FULL_DECODE_ONLY` 图模式下**同时支持 MTP** 时，先确认该后端 `get_cudagraph_support()` 申报的是 `UNIFORM_BATCH`；否则 MTP 的 `query_len>1` uniform decode 批不会被图捕获。

## 信号二：metadata 按真实 token 数切片 → infer shape error

**信号 / 症状**：SFA / DSA 走 aclgraph 全图 decode 捕获时报 infer shape errors；典型触发是 `num_input_tokens != num_actual_tokens`（即批被 pad 到捕获 batch size）时。

**触发条件**：decode 阶段 pad 到捕获 batch size（`num_input_tokens` 为固定的 padded 长度，`num_actual_tokens` 为随请求波动的真实 token 数），且 attention metadata builder 用了 `num_actual_tokens` 去切张量；或 builder 与 forward 两侧切片口径不一致。

**根因**：图捕获要求每次 replay 张量 shape 固定不变。`num_actual_tokens` 随请求波动，`num_input_tokens` 是 pad 到捕获 batch size 后的**固定**长度。builder 若用 `num_actual_tokens` 切 `slot_mapping` / `positions`，或把 `query_start_loc_cpu` / `seq_lens_cpu`（host 常驻）搬到 device 再算 cos/sin，这些长度都随真实 token 数变化，与捕获态固定 shape 冲突。更隐蔽的一类是**两侧口径不一致**：builder 用 `num_input_tokens` 切，而 forward 里 hidden_states 仍按 `num_actual_tokens` 切，二者不相等时即报 shape 错。

**修法**（口径一致 + 按 padded 长度切，这是可迁移的规则本身）：

1. **builder 侧统一改用 `num_input_tokens`（padded 长度）切片**：
   ```python
   slot_mapping   = common_attn_metadata.slot_mapping[:num_input_tokens]
   input_positions = common_attn_metadata.positions[:num_input_tokens].long()
   sin = sin[:num_input_tokens]; cos = cos[:num_input_tokens]
   ```
   sin / cos 优先 **in-place 写进预分配的固定长度缓冲区**，凑不上再退回新张量，让 cos/sin 缓冲在捕获态维持固定 shape：
   ```python
   if cos is not None and num_input_tokens <= cos.shape[0]:
       cos[:num_input_tokens] = new_cos      # 固定缓冲 in-place
   ```
   `cum_query_lens` / `seq_lens` 改用 **device 常驻**张量（`common_attn_metadata.query_start_loc` / `seq_lens`），去掉每步的 host→device 搬运。

2. **forward 侧移除对 hidden_states / output / slot_mapping 的 `[:num_actual_tokens]` 二次切片**，改吃 padded 长度（`num_input_tokens`），使两侧口径一致——这正是消除 builder↔forward shape 冲突的方式。

3. **model runner 侧对齐 uniform-decode padding**：当 `cudagraph_mode.decode_mode() == FULL` 且 uniform_decode 时，对 `query_start_loc` 做 padding（把 `num_reqs` 补到 `num_reqs_padded = num_input_tokens // uniform_decode_query_len`，用等差步长填充尾部），让 builder 无需再自行手工拼接 seq_lens / block_table / query_start_loc 的 padding。

4. **把 SpecDecoding 纳入 build 分支**：`build_for_graph_capture` 让 `AscendAttentionState.SpecDecoding`（原来只有 `DecodeOnly`）也走 `build`，使 MTP 投机解码也能进全图捕获。

## 参考实现及其约束

参考实现在 vllm-ascend（vLLM 昇腾插件）的 `vllm_ascend/attention/sfa_v1.py`（`AscendSFAMetadataBuilder` / `AscendSFAImpl`）与 `vllm_ascend/worker/model_runner_v1.py`（`NPUModelRunner._prepare_inputs`），模型为 DeepSeek-V3.2 走 SFA 路径。信号一的一行修法在 `sfa_v1.py` 的 `get_cudagraph_support()`，与同仓 MLA 后端 `mla_v1.py` 的返回 `UNIFORM_BATCH` 对齐；信号二的切片口径与 padding 对齐在 `sfa_v1.py.build` / `_sfa_preprocess_decode` 与 `model_runner_v1.py`。

约束的可迁移边界：
- `AttentionCGSupport` 枚举语义、「按 padded 长度切 + 两侧口径一致」是**图捕获固定 shape 契约**下的耐久规则，任何在昇腾 aclgraph 全图 decode 下接 MLA / 稀疏注意力（含 MTP）的实现都会撞同一约束。
- 具体文件名、`num_input_tokens` / `num_actual_tokens` 变量名、`UNIFORM_BATCH` 常量、`build_for_graph_capture` 分支是该参考实现（vllm-ascend + DSV3.2）的落地细节，不外推为「所有后端 / 所有图模式」。
- **同后端的一条正交互斥约束**（同属该后端图模式兼容边界，非本修法引入）：`enable_sfa_cp`（FlashComm1，需 `enable_sp()` 且模型有 `index_topk`）与 `CUDAGraphMode.FULL_DECODE_ONLY` **互斥**，会 assert 报 `"FlashComm1 is not compatible with FULL_DECODE_ONLY. Please set graph_mode to 'piecewise' or disable FlashComm1."`

**验证 / rollback**：两处 source 均未给 before→after 性能 / 精度数字（PR 描述 `Test cases needed`），可迁移经验点是上述两条规则本身而非数字。修复后 DSV3.2（SFA）在 vllm-ascend 上可跑 `FULL_DECODE_ONLY` 全图 decode 含 MTP。rollback：把图模式退回 `piecewise` 或不开 MTP（回到 `UNIFORM_SINGLE_TOKEN_DECODE` 覆盖得住的纯单 token decode）。

## 相关经验
- [aclgraph 图捕获前 monkeypatch upstream graph_captu](aclgraph_capture_patch_module_base_vs_mro.md)

## Evidence

- diff 事实 + reviewer 确认（merge sha `8b3a7a9e874c484a28efe89ce25b47e6eb809349`）：`sfa_v1.py` 的 `get_cudagraph_support()` 单行由 `UNIFORM_SINGLE_TOKEN_DECODE` 改为 `UNIFORM_BATCH`，与 `mla_v1.py:276` 已返回 `UNIFORM_BATCH` 对齐；根因据上游 `AttentionCGSupport` docstring（`UNIFORM_BATCH` 明确覆盖 spec-decode 的 `1+num_speculative_tokens`）+ reviewer 确认。溯源下探 [vllm-ascend-pr-5679-bugfix-support-dsv3-2-enable-both-mtp-and-full-decode-only](https://github.com/vllm-project/vllm-ascend/pull/5679)
- diff 事实 + reviewer 确认（merge sha `5b179c53f1669d9dfceeba1ff105423678be7004`）：`sfa_v1.py` 改用 `num_input_tokens` 切片、sin/cos in-place 固定缓冲、forward 侧删除 `[:num_actual_tokens]` 二次切片、`model_runner_v1.py` 的 `query_start_loc` padding 与 cos/sin 缓冲脱离 graph-mode 分配；失败签名（build 与 forward 切片口径不一致 → infer shape errors）由 reviewer 在 `sfa_v1.py:275` 独立佐证。溯源下探 [vllm-ascend-pr-4706-feat-support-deepseek-v3-2-with-full-decode-only-mode](https://github.com/vllm-project/vllm-ascend/pull/4706)

<!-- cannbot:related:start -->
## 相关

- [MTP 投机解码接图模式的前置与坑：独立 decode 入口避免重编译 + FIA GQA 要求 + aclgraph 取舍](mtp_speculative_decode_graph_mode_prereqs.md)（`related`）：MTP 的 ［FIA］(../../concepts/kernels/fused_infer_attention_score.md) 解码分支在 graph mode 下只支持 GQA 布局；在昇腾上要让某注意力后端在 `FULL_DECODE_ONLY` 图模式下**同时支持 MTP** 时，先确认该后端 `get_cudagraph_support()` 申报的是 `UNIFORM_BATCH`；接入 MTP 全图 decode 时，前者要求 FIA 路线先满足 Q/K 头布局，后者要求稀疏注意力后端覆盖多 token uniform batch，两项构成同一次图捕获上线检查的独立必备条件。
<!-- cannbot:related:end -->
