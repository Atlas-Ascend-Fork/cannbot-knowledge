---
type: Guide
title: SGLang Diffusion FLUX昇腾配置：版本与资源计数
description: 区分FLUX1/FLUX2的A2/A3生成器配置、旧A3基准和未验证HTTP组合。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/BlackForestLabs/flux.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/FLUX/FLUX.mdx
  role: constraint
created_at: '2026-11-08T12:33:43Z'
updated_at: '2026-11-08T12:33:43Z'
platforms:
- a2
- a3
---

# SGLang Diffusion FLUX昇腾配置：版本与资源计数

## 选择checkpoint与拓扑

生成器区分FLUX.1与FLUX.2。FLUX1的A2标准配置为1设备，A3为2设备/TP2；FLUX2的A2也使用2设备/TP2。Ulysses与Ring均为1，不能把num-gpus字面误读为物理A3卡数：A3一张卡暴露两个die。单节点资源校验需要精确匹配所选recipe。

cookbook中FLUX.1-dev的A3示例是num-gpus2、TP2、SP1；并发20的历史表只成功18/20，不能将其吞吐当全请求成功的稳定服务能力。生成器各HTTP组合仍标unverified/verified=false，与历史命令测量是不同证据。

## 使用与验收

先准备匹配checkpoint与平台运行时，检查实际配置、请求分辨率/步数与输出路径；从单请求开始，记录加载峰值、生成质量和成功率，再提高并发。FLUX2与FLUX1的文本/VAE组成和资源不同，不能只替换model-path沿用性能数值。若出现OOM先减少并发或选择对应资源recipe，性能比较应固定模型、seed、步数和缓存。本次没有执行生成或基准，保留draft。
