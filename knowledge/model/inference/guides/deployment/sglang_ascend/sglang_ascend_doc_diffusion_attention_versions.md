---
type: Guide
title: SGLang Diffusion NPU注意力文档：旧SDPA与新FA路线
description: 对比旧文档NPU仅SDPA和新版本Ring FA、组件/角色覆盖及NPU稀疏后端，保留版本边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/attention_backends.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/sglang-diffusion/attention-backends.mdx
  role: primary
created_at: '2026-11-08T12:33:42Z'
updated_at: '2026-11-08T12:37:01Z'
platforms: []
---

# SGLang Diffusion NPU注意力文档：旧SDPA与新FA路线

## 先确认来源版本

旧sgl-docs提交的attention-backends页明确NPU总是torch_sdpa，平台表将fa的NPU列为No；选择顺序为全局强制、CLI、自动。新sglang提交的attention_backends页则说明NPU Ring使用FA、其他默认SDPA，且加入Ascend FA、LASER、BlockSparse、RainFusion与组件/角色覆盖。这是两个固定版本的能力差异，不能用旧表否定新实现，也不能把新后端倒灌为旧版本支持。

## 新版选择与依赖

全局强制优先，随后组件角色.self/.cross、组件、CLI、模型/层默认、自动探测。CLI对DiT严格；encoder/VAE可用兼容默认回退，显式组件覆盖通常严格，未到达任何对应层也失败。稀疏cross统一回到兼容dense；模型要求的正确性后端继续保留。FA3/FA4只是参数解析别名，NPU实际实现由平台决定，不能按GPU代际理解。

LASER、BlockSparse、RainFusion依赖attentions（可随sgl-kernel-npu安装）；FA使用TorchNPU，不要求安装CUDA flash-attn。LASER短序列<2048回退SDPA。attention-backend-config接受文件、JSON或键值，但模型metadata/shape仍须满足。GPU的Sage/SubBlock/VSA-H3、AMD gfx950不等于Ascend 950支持。

## 验收与回退

先打印每个组件与角色最终类，覆盖self/cross、Ring所需LSE和packed varlen，再比较SDPA/FA基线。文档的autotune验证平台是SM90/SM12x，不能推为NPU自动调优已经验收。依赖缺失或不兼容显式配置应按实际错误处理，不能静默将其当优化生效。本次仅对齐文档与固定实现，无真机结果。

## 配套知识

[Ascend FA实现](../../integration/sglang_ascend/sglang_ascend_diffusion_ascend_fa.md)；[LASER实现](../../integration/sglang_ascend/sglang_ascend_diffusion_laser.md)；[块稀疏实现](../../integration/sglang_ascend/sglang_ascend_diffusion_block_sparse.md)；[RainFusion实现](../../integration/sglang_ascend/sglang_ascend_diffusion_rain.md)。
