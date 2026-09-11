---
type: Runbook
title: MLA / MLA-Prolog + Paged KV cache 部署的精度对齐要点
description: MLA / MLA-Prolog + Paged KV cache 部署的精度对齐要点。在昇腾上给 MLA 模型启用 MLA-Prolog 融合算子（npu_mla_prolog_v3）+ Paged Attention 压缩 KV cache，遇到精度对不上 baseline。MLA 的压缩 KV cache 被多条写入路径共用、NZ 分形布局随 dtype 变、缩放约定跨路径要一致、融合本身还会引入非 bit-exact——下面五个点是最常见的精度分叉源。CP 场景下 prefill 的两段式 KV 写另见 mla-prolog-zigzag-cp-kv-write。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/153
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA / MLA-Prolog + Paged KV cache 部署的精度对齐要点

## 适用场景

在昇腾上给 [MLA](../../concepts/modules/mla.md) 模型启用 [MLA-Prolog](../../concepts/kernels/mla_prolog.md) 融合算子（`npu_mla_prolog_v3`）+ [Paged Attention](../../concepts/techniques/npu_graph_mode.md) 压缩 KV cache，遇到精度对不上 baseline。MLA 的压缩 KV cache 被多条写入路径共用、NZ 分形布局随 dtype 变、缩放约定跨路径要一致、融合本身还会引入非 bit-exact——下面五个点是最常见的精度分叉源。CP 场景下 prefill 的两段式 KV 写另见 [mla-prolog-zigzag-cp-kv-write](../../optimizations/experience/rules/mla_prolog_zigzag_cp_kv_write.md)。

## 1. prefill 的 cache_mode 要按 CP 规模选 PA_BSND / PA_NZ

FA 读取（[npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md)）要求 KV cache 为 NZ 布局，但开启上下文并行（`cp_size > 1`）时，mla_prolog 需先把 K 写进 CP 临时缓存、经 all-gather 跨 cp_group 汇聚、再由 scatter 写回真正分页缓存并转 PA_NZ。因此 prefill 的 `cache_mode` 不能硬编码 `PA_NZ`，须按 cp_size 选：

```python
# FA need NZ cache, but if cp_size > 1, mla_prolog need PA_BSND and scatter will enable cache to PA_NZ
cache_mode = "PA_BSND" if self.cp_size > 1 else "PA_NZ"
```

decode 路径不含 CP 分支，`cache_mode` 恒为 `PA_NZ`。硬编码 `PA_NZ` 而开 CP 会破精度。

## 2. NZ 分形小 z 维随 KV cache dtype 取值（BF16=16 / C8=32）

NZ（分形）布局的分形小 z 尺寸与 dtype 相关：BF16=16，INT8=32。把 `KV_CACHE_NZ_DIM` 硬编码为 16（对 BF16 正确）后，一旦开 [C8](../../concepts/quantization/w8a8c8.md)（INT8）KV cache，`.view(...)` 会按错误分形维切分张量→KV 读写错位→精度异常。修法：随 dtype 缩放。

```python
factor = 2 if self.kv_cache_c8 else 1      # C8 触发 factor 2
KV_CACHE_NZ_DIM = 16 * factor
k_nope = k_nope.view(block_num, kv_num, self.kv_lora_rank // KV_CACHE_NZ_DIM, block_size, KV_CACHE_NZ_DIM)
```

FA 读侧与 CP 回写侧（`npu_scatter_pa_kv_cache`）两处 view 站点都要用同一 dtype-aware 分形维。

## 3. 一份压缩 KV cache 被多写入路径共用时，cache 存未缩放值、scale 施加在 query 侧

MLA 压缩 KV 常由框架 PA 统一管理，同一 cache 池被 prefill 写入（`npu_kv_rmsnorm_rope_cache`）和 decode 写入（`npu_mla_prolog_v3`）两条不同算子共用。若两条路径给 cache 施加的 scale 不一致（旧实现 decode 把 KV-LoRA scale 折进 cache、prefill 写未缩放 cache），同一序列的 prefill-slot 与 decode-slot 尺度错位、FA 回读施加不一致缩放→精度错误。统一约定：**cache 一律存未缩放值，把可交换的 KV 缩放全部移到 query 端**。

```python
q_nope, q_pe = npu_mla_prolog_v3(..., qc_qr_scale=float(self.mla_scale_q_lora), kc_scale=1.0)  # kc_scale=1.0 → cache 未缩放
q_nope = q_nope * self.mla_scale_kv_lora     # KV-LoRA scale 改施加在 query 输出侧
```

这样跨 prefill/decode 写入路径不必逐一对齐缩放常数。

## 4. softmax_scale 的 YaRN mscale 仅在 rope_type≠default 时生效（否则静默丢弃）

MLA 的 `softmax_scale = qk_head_dim ** -0.5`，YaRN 修正只在 `rope_type != "default"` 分支叠加 `mscale²`。若配置里设了 `mscale_all_dim`（意图开 YaRN 缩放）却把 `rope_type` 留成 `default`，`mscale` 被**静默忽略**、`softmax_scale` 保持无 YaRN 修正值→与训练期不一致的注意力缩放→精度偏差。护栏做法：`rope_type=default` 但设了 `mscale_all_dim` 时发 `RuntimeWarning`，提示与训练期配置核对。期望 `mscale_all_dim` 影响注意力缩放时，必须同时把 `rope_type` 设为非 `default`。

## 5. 启用 MLA-Prolog 融合会引入 BF16 累加顺序差异（非 bit-exact）

把 q/kv 的 prolog 计算合成单 kernel 能降 decode 延迟（A3 上一实测约 −6%，5.86→5.49 ms/token），但 fused kernel 的累加顺序与 legacy 显式 absorb 路径不同，会引入 BF16 累加漂移：前若干 decode token 与 baseline 逐字一致、之后 borderline logits 的 argmax 翻转，输出语义连贯但**非 bit-exact**。在 pre-multiply weight 与 kernel 内 scale 两条缩放路径上均能复现同一漂移点，说明分叉来自 fused kernel 累加顺序而非配置 bug。**含义**：按「语义等价 + 同精度等级」验收，不要求 bit-exact；需严格逐字复现的场景关掉融合（yaml `custom_params.enable_mla_prolog: false` 回退 legacy absorb）或切 FP32。

## 参考实现及其约束

- 陷阱 1/2 参考实现：cann-recipes-infer 的 Kimi-K2-Thinking（`modeling_deepseek.py` 的 `DeepseekAttention`，「使能 PA_NZ mla_prolog 带来的精度问题」修复）。
- 陷阱 3/4/5 参考实现：cann-recipes-infer 的 LongCat-Flash-Lite（`modeling_longcat_flash_lite.py`，`kv_lora_rank=512` / `qk_rope_head_dim=64`，A3 8 卡）。
- 边界：具体开关名、`factor 2`、`qc_qr_scale/kc_scale` 参数是这些参考实现的形态；「cache_mode 随 CP、分形维随 dtype、cache 存未缩放值、YaRN 须配 rope_type、融合非 bit-exact」的对齐思想适用于 MLA 压缩 KV + PA + 多写入路径类部署，不外推到非 MLA / 非 PA 场景。

## Evidence

- diff 事实 + reviewer 确认（@ef0387836d77）：`cp_size>1→PA_BSND/else PA_NZ`（prefill-only）；`KV_CACHE_NZ_DIM=16*factor`（C8 factor 2），reviewer 评论「KV_CACHE_NZ_DIM 在 C8 的时候是 32」。溯源下探 [cann-recipes-infer-pr-153-fix-kimi-k2-thinking-enable-pa-nz-mla-prolog](https://gitcode.com/cann/cann-recipes-infer/merge_requests/153)
- diff 事实 + 仓自报（@895615c）：`kc_scale=1.0` + `q_nope *= mla_scale_kv_lora` 的未缩放 cache 约定；`softmax_scale` 仅 `rope_type≠default` 乘 mscale²、新增 `elif mscale_all_dim` warning（PR 内 CANN 审查独立列出 YaRN 参数一致性）。溯源下探 [cann-recipes-infer-pr-462-refactor-longcat-flash-lite-tnd-pa-npugraph-ex-mc2-ep-decode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)
- diff 事实 + 仓自报（@8fd8db72）：`npu_mla_prolog_v3` 融合调用 + `enable_mla_prolog` 回退开关为 diff 事实；−6% / 5.86→5.49 ms、逐 token 分歧点为优化报告仓自报（含双缩放路径复现），无独立复测。溯源下探 [cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)