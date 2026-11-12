---
type: Guide
title: SGLang Diffusion Wan2.1：昇腾型号、变体与缓存基准
description: 说明1.3B/14B的生成器资源选择及A3历史TP2/SP2四设备配置，避免跨配置计算缓存收益。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/Wan/wan21.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Wan/Wan2.1.mdx
  role: constraint
created_at: '2026-11-08T12:33:44Z'
updated_at: '2026-11-08T12:33:44Z'
platforms:
- a2
- a3
---

# SGLang Diffusion Wan2.1：昇腾型号、变体与缓存基准

## 资源按模型变体确定

生成器含T2V14B、T2V1.3B、I2V14B。小模型A2非fast为1设备；大模型普通配置TP2/SP1，A3为2设备而A2为4设备。选8设备fast时大模型TP2/SP4，小模型TP4；fast使用LASER。num-gpus计算NPU die数，A3卡数需另除2。

cookbook历史A3大模型为4设备、TP2/SP2、LASER，与生成器普通A3两设备配置不同。该历史单请求T2V14B的无缓存1282.90秒和显式Cache-DiT413.88秒都属于来源配置，不能归给另一个recipe或宣称任意画面无损加速。缓存参数为FN2/BN1/warmup4/RDT0.4/MC4/Taylor order2。

## 使用与边界

精确HTTP生成器组合均未验证。先确定T2V/I2V条件、权重、分辨率/帧数/步数、并行与后端，单请求验收后才启用缓存与LoRA；LoRA需对应变体，选项存在不等于NPU质量通过。记录cache命中与输出连贯性，失败回到相同拓扑的无缓存LASER/FA基线。本次没有执行模型或比较质量。
