---
type: Optimization
title: SGLang ascend_fuseep 的通信计算融合与权重模式
description: 说明 fused_deep_moe 绕过 dispatcher、BF16 通信以及两种权重布局的加载和回退约束。
tags:
- task.optimization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/fuseep.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang ascend_fuseep 的通信计算融合与权重模式

## 场景与机制

`ascend_fuseep` 的 forward 直接调用 forward_fuseep，绕过普通 dispatcher 的 dispatch/combine；尽管构造了 StandardDispatcher，它在此路径不会执行。融合内部借助 DeepEP low-latency buffer 完成路由、通信和专家计算，不能把普通 hook 的 scale/metadata 契约直接叠加到它。

通信字节估算固定 `_PARAMS_BYTES=2` 且实际采用 BF16；此实现不提供 FP16 communication。模式 1 对 w13 做 64 元素分块布局，scale 按 128 范围重排为 FP32，w2 使用 NZ 与 FP32 scale。模式 2 对权重 NZ 转换，把 FP32 scale 的 INT32 bit pattern 扩宽存入 INT64，并 squeeze offsets；不是普通的 FP32→INT64 数值转换。

## 启用、成本与回退

所述权重后处理入口位于 NPUW8A8Int8MoEMethod，仅针对该 W8A8 INT8 方法；其他量化方法没有调用此入口，forward 又只按后端进入融合路径，因此任意量化 checkpoint 并不自动具备这些布局。加载前选定融合模式及对应 W8A8 INT8 checkpoint，检查 w13/w2 后处理只执行一次，并确认 fused_deep_moe 实际接收的两组 weights/scales 与模式匹配。w13_weight_offset/w2_weight_offset 仅在后处理中 squeeze 并保存属性，forward_fuseep 没有把 offsets 传入融合调用，不能视为该路径已消费。模式 2 在复制新权重后 resize 旧 storage 到零释放内存，这使后处理成为加载阶段的存储变换，不能在线切旗标恢复原布局。

目标是减少显式通信与计算阶段的调度开销；融合也收紧激活和权重格式要求，并占用通信 buffer。比较同模型普通 DeepEP 路径的 logits、专家输出与实际 decode 延迟，不能把上游 kernel 的命名作为收益证据。回退需重启并重新加载原 checkpoint 和未融合 backend。

## 下层接口参考

- [DeepEP 融合专家计算接口](../../apis/deepep/deepep_fused_deep_moe.md)
