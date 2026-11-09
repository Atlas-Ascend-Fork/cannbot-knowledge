---
type: Guide
title: vLLM Ascend 950 Draft FlashAttn：设备长度、plan缓存与输出缓冲
description: 限定GLM DFlash2和MiniMax-M3 DSpark的CANN FlashAttn选路，按device长度构建metadata并将plan限制在当前group/step，保留output原位契约。
tags:
- task.implementation
- topic.attention
- topic.speculative_decoding
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/fa_v1.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
created_at: '2026-10-29T11:32:34Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:32:34Z'
---

# vLLM Ascend 950 Draft FlashAttn：设备长度、plan缓存与输出缓冲


## 整条选路条件

固定ceac1a2b；此路径依赖950/A5的DEVICE_LENGTH_FLASH_ATTN能力，区别于[FA3训推一致性](vllm_ascend_fa3_training_consistency.md)。PCP保持分布式backend；本地backend_key必须为非MLA、非sparse、非compress，Q为FP16/BF16、KV为未量化类型，且没有DCP、MM prefix、RSWA、batch invariance或per-head quant scales。

实际target/draft和live loader tag也必须匹配：GLM glm_moe_dsa + DFlash2DraftModel的dflash_head且draft enforce_eager；或MiniMax-M3目标 + Qwen3DSparkModel的dspark_head。V2加载draft仍持有target model_config，不能仅按目标架构替换target自己的Attention，也不能把所有DFlash/DSpark模型都改用此backend。

## 以设备长度为真值

AscendFlashAttentionMetadataBuilder从common metadata的device query_start_loc和seq_lens构造本步元数据，裁到真实请求/token数量；拒绝采样后CPU mirrors可能陈旧，不能用旧长度重建plan。

forward首次把Q边界限制到[0,query token数]并cummax，KV长度至少1，以处理dummy边界；同一metadata在层间复用这对device长度。slot mapping及真实token计数仍需正确，dummy修正不表示任意错误真实长度可被接受。

## plan的缓存寿命

flash_attn_plans用heads、KV heads、head dim、window及layout作key；这些key不含每步长度，因此缓存必须只共享在同一Attention group与draft step的metadata内，不能提升为跨step全局字典。metadata算子与实际flash_attn消费同一attrs：TND query/output，KV依use_bnsd为PA_BNBD或PA_BBND，mask_mode为0无mask、3causal、4sliding window。

sliding window左边界为window-1；causal window右边界0。仅非零mask_mode才传mask，sinks与softmax_scale另行保留。调用位于attention_transfer_window中，不能为复用plan绕过既有传输fence。

## 输出与验证

CANN返回新tensor，但vLLM调用方提供并持有output缓冲，必须copy到output对应有效行并返回该缓冲。只返回新tensor可能破坏调用者的图/别名协议，即便数值单测看似一致。

按实际target/draft/tag和最终backend验收拒绝后长度、多步、dummy请求、变shape、window、layout及输出buffer identity，再加入图/传输。依赖只在使用该backend的worker里惰性导入，包缺失不能用另一个同名FA实现掩盖。未满足门控时保留原backend；本次未加载CANN扩展、运行draft或测性能。
