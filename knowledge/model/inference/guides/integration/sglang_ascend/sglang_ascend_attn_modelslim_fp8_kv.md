---
type: Guide
title: SGLang Ascend ModelSlim MLA FP8：动态Q与共享latent缩放
description: 说明Q_FP8_DYNAMIC_KV_FP8的arch35/MLA守卫、逐层声明和静态K scale约束，以及动态Q、BF16 RoPE与FIA
  v2的配合。
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_q_fp8_dynamic_kv_fp8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/modelslim.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_preprocess.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/deepseek_v2_attention_mla_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_kv_cache.py
  role: implementation
created_at: '2026-11-08T12:07:54Z'
updated_at: '2026-11-08T12:28:53Z'
platforms: []
aliases:
- Q_FP8_DYNAMIC_KV_FP8
- ModelSlimQFP8DynamicKVFP8Scheme
---

# SGLang Ascend ModelSlim MLA FP8：动态Q与共享latent缩放

## 启用前提

此scheme只接受 `fp8_e4m3` KV cache配置，create_weights明确要求NPU arch35（错误信息称A5），并且get_cache_layout拒绝非MLA。这里保留架构守卫，不以A5别名推导所有Ascend硬件支持；未建立完整产品型号证据，平台保持未知。

ModelSlim配置在cache为auto/bf16/bfloat16时不安装KV scheme。显式量化cache要求每个attention层都能解析到FA量化声明，支持的quant_type为 `Q_FP8_DYNAMIC_KV_FP8`；FLOAT/ignore层不能与量化层共享同一池，缺失逐层metadata或未知格式均直接报错。可回退auto使用BF16缓存。

## 缓存与参数

layout为mla_fp8：本地KV head=1，key latent维为kv_lora_rank且dtype FP8 e4m3fn，value字段实际保存qk_rope_head_dim的BF16 RoPE。MLA QK与PV共享fa_k的latent C，导出的fa_v只是兼容信息，不能独立套第二套V缩放。

fa_k.scale与offset参数均为[1,1] FP32。未加载scale时记录warning并采用1；加载的scale必须有限且严格大于0，非零offset拒绝。定义 `C_dequant=C_fp8*k_scale`，量化使用 `k_inv_scale=1/k_scale`。_quantize在FP32输入上调用npu_quantize、axis=-2、div_mode=False，不原地破坏prefill仍需要的BF16 latent；已FP8输入直接复用。RoPE字段转换为BF16。

Q按最后一维展开成二维做npu_dynamic_quant至FP8，再还原原shape，scale恢复为前导维+[1]并转FP32。反量化K时显式添加singleton轴，避免head数恰等于D时广播歧义，输出回compute_dtype。

## 与attention和融合预处理配合

模型层传递query动态scale，并对BF16 q_pe除以sq*sc；FIA v2对QK应用sq*sc、对PV应用sc，配套参数不能只启用一半。MLAProlog与fused norm/RoPE/cache写都使用inverse K scale；prefix展开先dequantize缓存再kv_b投影。head补齐的query descale填1，计算后截回真实head。

检查顺序是逐层声明→架构/MLA守卫→scale与offset→pool layout→Q/RoPE补偿→prefill/decode/verify一致性。建议测试缺scale、非法offset、FLOAT混层、prefix命中和不同query head数；未执行这些运行检查，不声称量化精度或吞吐收益已验证。

## 补充调用与验证边界

KV scheme基类创建参数时附加modelslim_loaded=False；loader严格检查loaded_weight dtype与声明一致，再调用default_weight_loader并标记已加载。默认scale=1与“真实加载了1”因此可区分。布局bytes_per_token按本地head数×(key_dim×key元素字节+value_dim×value元素字节)计算；它不包含额外allocator所有权或动态scale buffer，不能当总显存估算。
