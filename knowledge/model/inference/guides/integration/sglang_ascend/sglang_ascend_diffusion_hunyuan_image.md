---
type: Guide
title: SGLang Diffusion HunyuanImage3：NPU多输出和MoE归约所有权
description: 说明NPU顺序输出策略及Ascend finalize内部聚合与共享MLP已归约的边界，防止重复集合通信。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/hunyuan_image3.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/configs/pipeline_configs/hunyuan_image3.py
  role: implementation
created_at: '2026-11-08T12:27:28Z'
updated_at: '2026-11-08T12:27:28Z'
platforms: []
---

# SGLang Diffusion HunyuanImage3：NPU多输出和MoE归约所有权

## 多输出和并行

HunyuanImage3配置在NPU选择顺序多输出，DiT与AR阶段的batch和缓存需按实际流水线配合，不能照搬GPU一次大batch路径。NPU适配包含MoE的通信所有权：Ascend finalize已在内部聚合专家输出，共享MLP down projection也已完成all-reduce；调用侧不能为“对齐GPU逻辑”再归约一遍，否则会改变数值。

## 适配步骤

先定位实际MoE runner/finalize和共享专家并行组，再追踪输出是否全量或shard；保证每条贡献只归约一次。分别验证纯共享、路由专家和二者合并，核对多rank与单rank参考；多输出测试要检查cache重置与样本顺序。关闭部分融合可用于定位，但不能省掉必要的通信。

本卡是模型集成reference，不声明完整专家kernel闭包；源码注释与调用关系是证据，本次没有启动HCCL、模型或测量性能，硬件范围不外推。
