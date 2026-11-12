---
type: Guide
title: SGLang Diffusion Qwen-Image：A3两种并行配置的证据差别
description: 保留生成器TP1/SP2与cookbook TP2/SP1不一致、A2资源及未验证HTTP组合边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/Qwen/qwen-image.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Qwen-Image/Qwen-Image.mdx
  role: constraint
created_at: '2026-11-08T12:33:43Z'
updated_at: '2026-11-08T12:33:43Z'
platforms:
- a2
- a3
---

# SGLang Diffusion Qwen-Image：A3两种并行配置的证据差别

## 同版本中的两组配置

生成器A2标准为1设备；A3为2设备、TP1/SP2。cookbook的A3基准启动却是2设备、TP2/SP1，两组并行轴不同，不能用同一36.26秒表证明生成器配置已测。A3的2设备相当于一张双die物理卡；输入资源仍按visible device计数。

生成器的NVFP4选项对NVIDIA限定，不得带入A2/A3；所有当前精确HTTP资源组合保留unverified=true、verified=false。cookbook并发20表只成功8/20，不能当稳定并发20能力，也不能据此计算完整工作负载吞吐。

## 接入与验收

按所选版本分别记录TP、SP、交换方式、encoder/VAE驻留、分辨率、步数和模型revision。从单请求验证文字/图像质量和峰值，再逐步增加并发；比较两拓扑需在相同请求与成功率下重新测量。编辑/分层模型具有不同条件与AR组件，不能只替换checkpoint名就共享配置。当前卡蒸馏两份来源的冲突并保留待验证边界，本次未运行。
