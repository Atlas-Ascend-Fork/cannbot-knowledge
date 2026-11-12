---
type: Guide
title: SGLang Diffusion LTX-2：NPU RMSNorm和全通掩码消除
description: 说明TP1/TP多head归一化区别和仅当encoder mask全通时删除掩码的条件。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/ltx_2.py
  role: primary
created_at: '2026-11-08T12:27:28Z'
updated_at: '2026-11-08T12:27:28Z'
platforms: []
---

# SGLang Diffusion LTX-2：NPU RMSNorm和全通掩码消除

## 触发与机制

LTX-2在NPU且TP=1时使用自定义RMSNorm替代nn.RMSNorm，TP>1仍需跨head的全局统计，不可把每rank局部norm当等价实现。encoder attention mask全为有效位置时可以删除，省去后续小tensor操作；非全通mask必须保留，不能为减少图输入而普遍设None。

判断mask.all()可能带来Host同步，节省的小算子与检查成本应一并测量。接入时分别测试padding与无padding文本、TP1与TP2及不等长请求，核对padding从未参与attention且norm范围正确。

使用固定seed比较输出和质量，再采集norm、mask转换与通信耗时。只有实际模型入口和CI配置的组合可作为测试目标，公共NPU分支不背书所有LTX输入。本次没有运行模型或性能测试。
