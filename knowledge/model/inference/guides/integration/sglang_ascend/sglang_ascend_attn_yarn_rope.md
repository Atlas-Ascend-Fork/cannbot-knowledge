---
type: Guide
title: SGLang Ascend DeepSeek YaRN RoPE：双表扩展、局部旋转与缩放
description: 说明DeepseekScalingRotaryEmbedding在NPU同时维护半宽cache与完整cos/sin表，扩容时保持mscale和dtype一致，并仅旋转rotary段。
tags:
- task.implementation
- topic.attention
- topic.long_context
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/rope_variant.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/base.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/factory.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/yarn.py
  role: constraint
created_at: '2026-11-08T12:08:00Z'
updated_at: '2026-11-09T04:31:35Z'
platforms: []
aliases:
- YaRN NPU
- npu_interleave_rope
---

# SGLang Ascend DeepSeek YaRN RoPE：双表扩展、局部旋转与缩放

## 两套表必须同步

本卡仅描述factory中deepseek_yarn对应的DeepseekScalingRotaryEmbedding。普通yarn对应YaRNScalingRotaryEmbedding，只维护cos_sin_cache并继承基类forward_npu分派，不采用本卡的双表与npu_interleave_rope前向。

DeepSeek YaRN基础cache由freqs.cos/sin乘mscale后拼接；NPU额外维护full-width cos_cached_total/sin_cached_total。长位置扩展先调用共享YaRN cache扩展，再把新行cos/sin重复成完整宽度追加到NPU表，并匹配既有表dtype/device；只扩基础cache会让NPU读取越界或旧角度。

get_cos_sin_cache按positions加可选offset取当前行，添加两个广播维并转query dtype。NPU forward将Q/K的rotary部分reshape成[T,heads,1,rotary_dim]，分别调用npu_interleave_rope，再接回未旋转pass部分。head_size大于rotary_dim时不能旋转整个head。

## 适配与验收

加载模型时核对scaling factor、mscale与rotary风格，长上下文开始前预扩表以避免图中产生新存储；使用offset、partial rotary和超初始max_position的样例比较native/NPU输出。不同RoPE变体有各自形状及风格限制，不能因DeepSeek YaRN有专用forward_npu推导普通yarn或所有variant均可调用同一融合接口。

双表占用更多内存，换取运行时直接gather与原生旋转；实际误差和收益需对同一权重、上下文长度测量。本次未执行扩表或真机测试，芯片支持范围保持未知。
