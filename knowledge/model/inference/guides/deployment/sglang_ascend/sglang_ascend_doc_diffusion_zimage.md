---
type: Guide
title: SGLang Diffusion Z-Image-Turbo：A2/A3资源与CFG成本
description: 说明小模型标准设备配置、8步与Turbo默认无负分支，以及缓存近似和未验证组合。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/TongyiMAI/z-image-turbo.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Z-Image/Z-Image-Turbo.mdx
  role: constraint
created_at: '2026-11-08T12:33:43Z'
updated_at: '2026-11-08T12:33:43Z'
platforms:
- a2
- a3
---

# SGLang Diffusion Z-Image-Turbo：A2/A3资源与CFG成本

## 平台和参数

生成器A2标准1设备，A3为2设备/TP2/SP1，单节点资源上限为2；精确HTTP组合仍未验证。cookbook A3也用num-gpus2、TP2、SP1，来源报告单请求2.43秒、20请求总49.08秒，这些是来源历史数据，本次没有复测，也不推为所有输入保证。

Z-Image-Turbo为8次模型评估的生成checkpoint。其guidance采用positive+guidance_scale*(positive-negative)，正guidance启用CFG；默认guidance_scale=0，不执行negative分支，缺negative prompt时才使用空字符串。不能仅因其他Diffusion模型常用CFG就默认增加第二分支。

## 缓存、内存和验证

Cache-DiT复用/预测步间状态，可能改变输出，参数需和基准一并记录；CPU offload可降低设备驻留但增加搬运，文本encoder的TP限制按模型实际配置核对。先无缓存固定seed、分辨率和8步验收，再单独开启缓存、CFG和offload，分别记录质量、延迟与内存。来源没有证明所有LoRA/HTTP组合已在NPU验收，本次不运行模型。
