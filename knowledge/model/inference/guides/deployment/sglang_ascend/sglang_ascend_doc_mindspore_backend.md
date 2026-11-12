---
type: Guide
title: SGLang MindSpore 后端的安装、运行和版本冲突
description: 合并两仓 MindSpore 文档，保留独立包、模型范围、CANN8.3/8.5冲突和通信/Protobuf排障。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/mindspore_backend.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/supported-models/mindspore_models.mdx
  role: constraint
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/MindSpore%20Models.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/supported-models/mindspore-models.mdx
  role: constraint
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang MindSpore 后端的安装、运行和版本冲突

## 独立后端与支持边界

这些来源描述独立sgl-mindspore包建立在SGLang Ascend安装之上；不能只装普通SGLang就假设MindSpore实现已存在。文档列Qwen3 dense/MoE与DeepSeek V3/R1，不等于完整PyTorch模型清单。来源只称Ascend NPU，没有具体产品表，因此draft空platforms。

同一新仓快照的专门mindspore_backend页仍建议CANN8.3.RC2，supported-models页却写CANN8.5；旧仓主要建议8.3.RC2。它们与当前通用NPU安装页CANN9.1版本组也不同，不能合成“8.3到9.1全部兼容”。必须按独立sgl-mindspore版本、依赖和目标产品重新核对，来源缺少该组合的固定包版本与设备验证。

## 运行契约

Engine或CLI显式设置model_impl=mindspore、device=npu、attention_backend=ascend。单机示例TP1/DP1，分布式示例nnodes2/TP4/DP2；其dist-init-addr使用127.0.0.1只适合示例占位，跨主机必须换成各节点可达的rank0地址并匹配node-rank，不能直接照抄。

ASCEND_RT_VISIBLE_DEVICES限定进程可见设备；SGLang日志级别与MindSpore GLOG_v分别控制框架与后端日志，GLOG_v1为INFO、0为DEBUG。该文档指出当前不支持LCCL模式，特殊环境可用MS_ENABLE_LCCL=off；这是该集成的边界，不能当所有MindSpore/CANN通信的限制。

Protobuf二进制版本不匹配时，PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python是来源给出的兼容路径；它并不修复任意依赖冲突或保证同等性能。验收应同时确认后端选择、权重加载、单请求输出、TP/DP组和多节点连接，再评质量与性能。本次没有安装后端或运行模型。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/mindspore_backend.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/mindspore_backend.mdx)（primary）
- [sglang：docs/docs/supported-models/mindspore_models.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/supported-models/mindspore_models.mdx)（constraint）
- [sgl_docs：docs/hardware-platforms/ascend-npus/MindSpore Models.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/MindSpore%20Models.mdx)（primary）
- [sgl_docs：docs/supported-models/mindspore-models.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/supported-models/mindspore-models.mdx)（constraint）
