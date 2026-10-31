---
type: Optimization
title: MLA / DSA C8：写入、打包与反量化须成对
description: 以当前R1和V3.2-Exp实现说明C8的分离/打包布局、scale方向、packed FIA和现行量化SFA调用。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:51:46Z'
platforms:
- a3
---

# MLA / DSA C8：写入、打包与反量化须成对

## R1：分离NoPE/RoPE

当前R1以INT8保存NoPE latent，RoPE保持模型dtype。Prefill的npu_kv_rmsnorm_rope_cache_v2接c_kv_scale=ckv_scale倒数；Decode的npu_mla_prolog_v3同样接quant_scale_ckv=倒数，weight_quant_mode按线性A8选择2或0，KV量化mode为1；启用A8和C8时query_quant_mode为1。

Decode FIA v2用ckv_scale原值反量化key/value，并传Q侧dequant scale、query_quant_mode=3；当前packed接口为TND_NTD，不能继续抄BSND旧代码。C8模型还检查enable_mla_prolog=True。线性量化与缓存量化要分别核对，不从标签推导全部投影都量化。

## V3.2-Exp：动态分块打包

Prefill/Decode均用npu_mla_prolog_v3。只量化q_b投影时weight_quant_mode=1，并向Indexer传pertoken_scale；缓存INT8时另设kv_cache_quant_mode=3、query_quant_mode=0、ckvkr_repo_mode=1、quant_scale_repo_mode=1、tile_size=128及k_nope_clip_alpha。

NoPE buffer打包latent、RoPE和scale，末维示例512+64×2+16=656字节；独立RoPE只占位。非量化的(512+64)×2=1152字节到656约减少43.1%，不是完整KV一律减半，且未含Indexer Key与scale缓存。

当前C8读端是torch_npu.npu_kv_quant_sparse_flash_attention，**旧npu_sparse_flash_attention_antiquant名称已不适用**。Q将q_nope/q_pe拼成contiguous张量，key/value_quant_mode=2、quant_scale_repo_mode=1、tile_size=128、rope_head_dim=64；scale随KV打包，不额外传key/value scale。非C8才分别传query_rope/key_rope。

Indexer Key量化是独立Per-Token-Head路径，scale每slot一个标量，scatter目标view(-1,1)。CP先恢复全序，再分别写全局临时计算cache与持久cache；不能继续按旧rope列表narrow和连续batch写法接线。详见[CP写入](mla_prolog_zigzag_cp_kv_write.md)。

## 验收和边界

检查实际checkpoint quantization_config、模块dtype、所有scale方向、打包布局、slot_mapping与算子参数；覆盖Prefill/Decode、CP1/CP>1及量化开关。C8时PyPTO LI分派会回到量化AscendC LI，但PyPTO IndexerProlog仍有单独的INT8 Decode门控，不能把“PyPTO”整体一律禁用。

来源模型README明确A3；不从旧算子版本讨论推导950支持或最低CANN版本。不同模型/内核mode数值不能互换，本次无NPU复测。


## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
