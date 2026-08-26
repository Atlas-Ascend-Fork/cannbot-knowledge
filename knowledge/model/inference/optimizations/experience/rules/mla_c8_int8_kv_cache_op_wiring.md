---
type: Optimization
title: MLA / DSA 上 C8（int8 KV cache）的算子接线：打包布局 + prolog·SFA·FIA 走量化变体 + 单 scale 驱动
description: MLA / DSA 上 C8（int8 KV cache）的算子接线：打包布局 + prolog·SFA·FIA 走量化变体 + 单 scale 驱动。要给 mla / dsa 结构上 C8（int8 KV cache）再省一半 KV 显存 / 搬运时。难点不在「把 cache dtype 改成 int8」，而在写 cache、mla-prolog、sparse-flash-attention / fused-infer-attention-score 三处要一致地插入同一套量化 / 反量化。踩错任一处，要么算子消费不了 int8 KV，要么对 None 调 .narrow 直接崩。C8 与线性投影的 A8W8 权重量化是两条正交量化轴，可独立开关。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/82
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/53
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/417
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA / DSA 上 C8（int8 KV cache）的算子接线：打包布局 + prolog·SFA·FIA 走量化变体 + 单 scale 驱动

## 适用场景

要给 [mla](../../../concepts/modules/mla.md) / [dsa](../../../concepts/modules/dsa.md) 结构上 C8（int8 KV cache）再省一半 KV 显存 / 搬运时。难点不在「把 cache dtype 改成 int8」，而在写 cache、[mla-prolog](../../../concepts/kernels/mla_prolog.md)、[sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) / [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) 三处要**一致地**插入同一套量化 / 反量化。踩错任一处，要么算子消费不了 int8 KV，要么对 `None` 调 `.narrow` 直接崩。C8 与线性投影的 A8W8 权重量化是两条正交量化轴，可独立开关。

## 只量化 nope、rope 保 16 位；单 scale 双向驱动

- **只压缩 KV 潜向量（nope）量化，rope 分量保持模型 dtype**：MLA 只缓存低秩压缩潜向量 + rope 分量，nope cache 用 int8，rope cache 保持 bf16。
- **同一个逐张量 `ckv_scale` 贯穿全程**：写 cache 端传其倒数（量化写入），反量化端传原值。写 cache 的 `npu_kv_rmsnorm_rope_cache` 收 `reciprocal(ckv_scale)`；`npu_mla_prolog_v2/v3` 的 `quant_scale_ckv`、FIA 的 `dequant_scale_key/value` 收 `ckv_scale` 原值。
- **decode 注意力必须走 FIA v2**：C8 时 `query_quant_mode=3`、`dequant_scale_query` 带 q 侧 scale、`dequant_scale_key/value = ckv_scale`；非 C8 时全部 scale 传 `None`、`query_quant_mode=0`。FIA v1 无法消费 int8 KV（v2 同时覆盖 bf16 路径，v1 可整段被 v2 取代）。

## 打包成单张 int8 buffer + rope_cache=None → None-guard（失败签名）

当 KV 交给 SFA / MLA-Prolog 融合算子时，C8 下算子**不吃分离的 nope / rope 两张 cache**，要一张已把 nope、rope 与反量化 scale 拼好的 int8 buffer：

- 末维 = `kv_lora_rank + qk_rope_head_dim*2 + scale_段`（DeepSeek-V3.2-Exp 为 `512 + 64*2 + 4*4 = 656`，与 [gather-selection-kv-cache](../../../concepts/kernels/gather_selection_kv_cache.md) 的 `MAX_KV_CACHE_DIM=656` 独立一致）。非 C8 时 nope / rope 分离、dtype = 模型 dtype。
- **配对的独立 rope_cache 置 `None`** → 下游一切对 rope cache 做 `.narrow` / `.view` 的地方都必须加 None-guard（`v.narrow(...) if v is not None else None`），否则对 `None` 调 `.narrow` / `.view` 直接崩。CP prefill 镜像同理（`cp_tmp` 的 rope cache 也是 `None`）。
- NZ 布局下 int8 KV 按 `factor=2` 打包（`k_nope` view 末维 = `KV_CACHE_NZ_DIM(16) * factor`，见 [weight-nz](../../../concepts/techniques/weight_nz.md)）。
- **Indexer key 反量化 scale 每 slot 一个标量**，scatter 目标末维必须为 1（`view(-1, 1)`，不是 `view(-1, head_dim)`）；按 head_dim 展平会错位。

## SFA 切 antiquant 变体、query 打包

- C8 分支调 `npu_sparse_flash_attention_antiquant`（算子内反量化 int8 KV），非 C8 调 `npu_sparse_flash_attention`。
- C8 下把 rope 分量 cat 进单一 contiguous query（`q = cat([q_nope, q_pe], -1).contiguous()`），用 `rope_head_dim` 告知算子 rope 段位置；`key/value_dequant_scale = None`（scale 随打包 KV 携带）。⚠️ 把 `query_rope` / `key_rope` 从两 path 共用基础入参里挪出、**只在非 C8 分支设**，否则会误传给 antiquant 变体。

## prefill 也必须迁到融合 MLA-Prolog（勿只改 decode）

常见误判是「C8 只需改 decode」。实则 **prefill 也写 KV cache**，而手工 prefill 路径（`npu_kv_rmsnorm_rope_cache_v2` + 手工 q 投影 / absorb + `npu_interleave_rope`）产出的是 bf16 KV cache，落不成 int8 C8 cache。要把路由从「只有 C8-decode 用 v3」放宽为「decode / prefill 一律走 `npu_mla_prolog_v3`」，prefill / decode 共用一份入参 dict 打通 int8 写路径。C8 还需给 v3 追加量化入参 + 一个 nope 量化 clip alpha（`k_nope_clip_alpha`）。

## 参考实现：torch 无原生 dtype 的 KV 量化路径（TensorWrapper 带 acl dtype）

给 AscendC 自定义算子（如 [sparse-attn-sharedkv](../../../concepts/kernels/sparse_attn_sharedkv.md) 的 QSAS `aclnnKvQuantSparseAttnSharedkv`）新增一种 **torch 没有原生 dtype** 的低精度 KV 量化格式（如 hif8 / [ascend-950](../../../concepts/platforms/ascend_950.md) 的 HiFloat8）时，不能靠张量自身 dtype 传量化语义——把 acl dtype「带外」附到张量上再传给 aclnn 分发宏：用 `make_wrapper(tensor, ACL_HIFLOAT8)` 生成 `{tensor, dtype}` 的 `TensorWrapper`，以整数 `kv_quant_mode` 门控该路径（如 `==10` 走 hif8，其它 mode 走原直传路径），optional 张量先 `has_value()` 取值 / 缺失用 undefined 顶替**再包 wrapper**；下游 `ConvertType` 从 `wrapper.dtype` 取出 acl dtype 应用到 `aclTensor`。

## 参考实现及其约束

参考 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) / DeepSeek-R1 的 `DeepseekIndexerAttention`。量化 mode 数值、`MlaPrologV3` 各 `*_quant_mode` / `tile_size` 的必需取值属算子规格、后续可能变动，此处不定合约。版本前置：MLA C8-on-aclgraph 的 FIA v2 需 CANN 8.3.RC1.alpha003 起。相关约束：C8 KVCache 与 PyPTO 版 Lightning Indexer 当前互斥，见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)；量化选层原则见 [dsa-quant-layer-selection](dsa_quant_layer_selection.md)，MoE 权重进一步降位见 [moe-role-based-precision-allocation](moe_role_based_precision_allocation.md)。

## Evidence

- `diff 事实`（@b88d340c272f）：`ckv_scale` / `npu_kv_rmsnorm_rope_cache(c_kv_scale=recip)` / `npu_mla_prolog_v2(quant_scale_ckv)` / `npu_fused_infer_attention_score_v2(query_quant_mode=3)` / `dtype_nope=int8` / NZ `factor=2` 逐处对上。
- `diff 事实`（@3aad9baf029c）：打包末维公式、`rope_cache=None` + 下游 None-guard、indexer scale `view(-1,1)`、SFA 切 antiquant + cat query + scale=None、prefill/decode 统一路由到 v3、C8 追加 clip alpha。
- `diff 事实`（@a34ce8e16efb）：QSAS 的 `make_wrapper` + `kv_quant_mode==10` 门控 + `ACL_HIFLOAT8` 经 `TensorWrapper` 带外传递 + `ConvertType` 读 `tensor_r.dtype`。
- 版本前置 CANN 8.3.RC1.alpha003：README bump（diff）+ 维护者确认双证。
- 溯源下探：
  - [cann-recipes-infer-pr-82-feat-add-deepseek-r1-c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/82)
  - [cann-recipes-infer-pr-53-feat-support-sfa-c8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/53)
  - [cann-recipes-infer-pr-417-feat-qsas-support-hif8-kv-quant](https://gitcode.com/cann/cann-recipes-infer/merge_requests/417)
