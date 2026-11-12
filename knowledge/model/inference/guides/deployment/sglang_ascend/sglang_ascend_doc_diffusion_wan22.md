---
type: Guide
title: SGLang Diffusion Wan2.2：级联变体、8设备LASER与验收
description: 说明A14B和TI2V5B不同资源公式、来源A3 TP2/SP4配置及缓存并发结果的负载边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/Wan/wan22.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Wan/Wan2.2.mdx
  role: constraint
created_at: '2026-11-08T12:33:44Z'
updated_at: '2026-11-09T04:30:33Z'
platforms:
- a2
- a3
---

# SGLang Diffusion Wan2.2：级联变体、8设备LASER与验收

## 变体与并行

Wan2.2区分T2V-A14B、I2V-A14B及TI2V-5B。5B普通配置TP1，A2一设备/A3两设备，SP随设备数；fast八设备为SP8。A14B普通TP2/SP1，A3两设备/A2四设备；fast八设备为TP2/SP4，并选择LASER。A14B的双transformer和5B的单transformer不能共享权重重打包假设。固定cookbook还明确提示TI2V-5B用于图生视频存在已知质量问题；I2V质量优先时应选 `Wan-AI/Wan2.2-I2V-A14B-Diffusers`，不能只按设备资源选择5B。

cookbook A3大模型用8设备（4物理卡）、TP2/SP4、LASER；单请求无缓存历史214.50秒。缓存表却是并发20、20请求、总4384.65秒，不能拿总时长与单请求数值直接计算缓存加速比。生成器精确HTTP组合仍unverified，历史表不自动验证每种变体、LoRA或输入。

## 接入与验收

按变体准备完整Diffusers结构；量化的Wan原生权重需通过对应wan_repack转换，不把A14B和5B模型类型混用。先无缓存固定seed、采样、帧数和分辨率验收，再开启Cache-DiT、量化、LoRA和并行，每次记录实际执行参数与成功率。多卡通信与级联切换可增加Host/NPU峰值，本次未运行模型或基准。
