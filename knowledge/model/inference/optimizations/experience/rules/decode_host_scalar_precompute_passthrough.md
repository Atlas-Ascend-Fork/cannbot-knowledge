---
type: Optimization
title: 消除 decode/生成热路径每步重复的 host 侧算子入参准备（scale / seq-length / 量化 scale：预算一次 + 透传/缓存复用）
description: 消除 decode/生成热路径每步重复的 host 侧算子入参准备（scale / seq-length / 量化 scale：预算一次 + 透传/缓存复用）。decode 逐 token / 生成多步推理时延偏高，profiling 看到频繁的下发中断（dispatch interruption）+ device 等待，或热路径里有 host 端标量运算 / .item() / 反复构造小张量 .npu()。 通用症结：每前向重复做、但在稳态内容不变的 host 侧算子入参准备（标量 scale、seq-length 小张量、量化 scale）是可去除的固定开销——它落在 host、每层/每步触发，造成下发中断与 H2D 强同步。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/305
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/110
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/206
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a2
---

# 消除 decode/生成热路径每步重复的 host 侧算子入参准备（scale / seq-length / 量化 scale：预算一次 + 透传/缓存复用）

## 适用场景
- decode 逐 token / 生成多步推理时延偏高，profiling 看到频繁的下发中断（dispatch interruption）+ device 等待，或热路径里有 host 端标量运算 / `.item()` / 反复构造小张量 `.npu()`。
- 通用症结：**每前向重复做、但在稳态内容不变的 host 侧算子入参准备**（标量 scale、seq-length 小张量、量化 scale）是可去除的固定开销——它落在 host、每层/每步触发，造成下发中断与 H2D 强同步。

## 规则（可迁移手段）
把每前向不变的 host 侧准备「上提/预算一次 + 透传或缓存复用」，只在 prefill（首帧/变长）分支才现算：
1. **config 固定的常量在 init 预算 + 改签名透传**：如 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md)（FA/FIA）默认每次在 CPU 自算 `scale = 1/sqrt(d)`，而 `d`（head_dim）在 config 固定 → init 时算好 `scale` 存成员、改 FA 封装签名让它**吃传入的 scale**（底层 `npu_fused_infer_attention_score`），不再每次自算。
2. **每步不变的标量用 `.item()` 提到 pipeline 入口算一次**：热路径里从 device 取标量（如从 timestep-scatter-index 取 `causal_len`）是强同步 H2D；若该标量在整段 `__call__` 内一经确定即不变，把 `.item()` 提到 `__call__` 开头算一次、写入 `model_kwargs` 逐层透传，消除每层每步的重复 H2D 同步。
3. **decode 每步现算的固定小张量改为复用调用方入参**：反模式是每次注意力调用前无条件 `actual_seq_qlen = torch.tensor([...], dtype=torch.int32).npu()`——decode 每步都 host 造 list、建 int32 张量、`.npu()` 触发 H2D。该张量在 decode 每步内容固定，默认复用调用方传入的 `actual_seq_lengths_q`，只在 prefill 分支现算：
   ```python
   actual_seq_qlen = actual_seq_lengths_q
   if is_prefill:
       actual_seq_qlen = torch.tensor([q_len + i * q_len for i in range(bsz)], dtype=torch.int32).npu()
       actual_seq_lengths_kv = torch.tensor([q_len for _ in range(bsz)], dtype=torch.int32).npu()
   ```
4. **每前向不变的量化 scale 惰性预算缓存、别重算**：[mla-prolog](../../../concepts/kernels/mla_prolog.md) v3 + per-tensor int8 KV cache（C8，见 [w8a8c8](../../../concepts/quantization/w8a8c8.md)）的倒数 `quant_scale_ckv` 是每前向不变的常量 → 用 `is None` 守卫在首次（prefill）算一次后缓存，后续 prefill/decode 复用，**避免每前向重算** `reciprocal().repeat().view().to(device)`。并且**别给算子传冗余形状**：per-tensor 量化整张 cache 共用单值，mla_prolog 的 `quant_scale_ckv` 只需 **1 元素**倒数 scale；传 2 维 `repeat` 版会触发多余 slice（只有 `npu_kv_rmsnorm_rope_cache_v2` 的 `c_kv_scale` 才需 2 维）。

## 判断准则
- 凡 decode/生成热路径里每前向现算、且在稳态不变的 host 侧标量/小张量/量化 scale，优先「一次算好 + 透传 / 缓存复用」，把现算限制在 prefill 变长分支；顺带避免给融合算子传冗余形状触发多余 slice。收益方向明确（去下发中断 + H2D 同步），但下列证据未给量化数字。

## 参考实现及其约束
- FA scale + `.item()` 上提参考 HunyuanImage-3.0 的 DiT 生成 pipeline（Atlas A2/A3，多步/多层生成）；seq-length 复用参考 Kimi-K2 / DeepSeek 风格 [mla](../../../concepts/modules/mla.md) 建模；量化 scale 预算参考 DeepSeek-R1 的 mla_prolog v3 + C8 路径。这些是各自参考实现的落点，手法本身与模型无关。

## 相关经验

- 另见 [推理输入预处理（host 侧）两类坑：大 batch 分词 host OOM + 逐 batch .item() 同步 / 逐次整数算术](inference_preprocess_hotpath_host.md)。


## Evidence
- `diff 事实`（@f4a8014a8db0）：FA 封装改为吃入参 `scale`、init 预算 `fa_scale`、FA forward 删内部 `.item()`；pipeline `__call__` 开头新增 `timestep_index = ...item()` 写 `model_kwargs`。
- `diff 事实`（@6e613e759b01a7edd69b2bfbfef3766df16a981a）：`DeepseekAttention` 首个 hunk 命中「decode 复用 `actual_seq_lengths_q`、仅 prefill 现算」改法。
- `diff 事实` + `维护者确认`（@1a16834994ef）：`is None` 守卫惰性缓存 scale、两算子分别收 1 元素 / 2 维 scale；维护者确认「per-tensor 只需 1 值、传 2 维引入多余 slice」，作者以 "no slice" 修复。
- 溯源下探：[cann-recipes-infer-pr-305-feat-hunyuanimage-3-0-supports-moe-ep-and-the-performance-is-optimized](https://gitcode.com/cann/cann-recipes-infer/merge_requests/305)、[cann-recipes-infer-pr-110-refactor-modify-mla-prolog-cache-mode-pa-nz-convert-nz-support-fused-inf](https://gitcode.com/cann/cann-recipes-infer/merge_requests/110)、[cann-recipes-infer-pr-206-fix-ds-r1-replace-non-standard-inplace-ops-with-standard-ops](https://gitcode.com/cann/cann-recipes-infer/merge_requests/206)

<!-- cannbot:related:start -->
## 相关

- [把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写](../../../guides/experience/interventions/graph_break_elimination_host_sync_unsupported_ops.md)（`related`）：host 侧入参预算复用见 ［decode-host-scalar-precompute-passthrough］(../../../optimizations/experience/rules/decode_host_scalar_precompute_passthrough.md)；通用症结：**每前向重复做、但在稳态内容不变的 host 侧算子入参准备**（标量 scale、seq-length 小张量、量化 scale）是可去除的固定开销——它落在 host、每层/每步触发，造成下发中断与 H2D 强同步。。图安全指南要求移除 forward 的 host 依赖，规则页把稳态不变的 scale、seq-length 和量化 scale 上提并透传，给出该要求的性能化实现。
<!-- cannbot:related:end -->
