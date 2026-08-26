# 位置编码 ACLNN 算子

本目录保存位置编码及相关融合类 ACLNN 算子知识。

- [ApplyRotaryPosEmb A2/A3](apply_rotary_pos_emb.md)：ApplyRotaryPosEmb 算子在 A2/A3 平台的 ACLNN 实现，用于对输入张量应用旋转位置编码。
- [ApplyRotaryPosEmb A5](apply_rotary_pos_emb_a5.md)：ApplyRotaryPosEmb 算子在 A5 平台的 ACLNN 实现，用于对输入张量应用旋转位置编码。
- [NormRopeConcat A5](norm_rope_concat_a5.md)：NormRopeConcat 算子在 A5 平台的 ACLNN 实现，用于融合归一化、RoPE 与 Q/K/V 拼接。
- [NormRopeConcatGrad A2/A3](norm_rope_concat_grad.md)：NormRopeConcatGrad 算子在 A2/A3 平台的 ACLNN 实现，用于计算归一化、RoPE 与拼接融合过程的反向梯度。
- [NormRopeConcatGrad A5](norm_rope_concat_grad_a5.md)：NormRopeConcatGrad 算子在 A5 平台的 ACLNN 实现，用于计算归一化、RoPE 与拼接融合过程的反向梯度。
- [QkvRmsNormRopeCache A2/A3](qkv_rms_norm_rope_cache.md)：QkvRmsNormRopeCache 算子在 A2/A3 平台的 ACLNN 实现，用于融合 QKV 拆分、RMSNorm、RoPE 与 KV Cache 写入。
- [RopeWithSinCosCache A2/A3](rope_with_sin_cos_cache.md)：RopeWithSinCosCache 算子在 A2/A3 平台的 ACLNN 实现，用于复用正余弦缓存并对输入应用 RoPE。
- [RopeWithSinCosCache A5](rope_with_sin_cos_cache_a5.md)：RopeWithSinCosCache 算子在 A5 平台的 ACLNN 实现，用于复用正余弦缓存并对输入应用 RoPE。
- [RotaryPositionEmbedding A2/A3](rotary_position_embedding.md)：RotaryPositionEmbedding 算子在 A2/A3 平台的 ACLNN 实现，用于对 Q/K 等张量执行可选旋转矩阵驱动的位置编码。
