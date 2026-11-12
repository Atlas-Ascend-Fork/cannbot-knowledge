---
type: Optimization
title: SGLang 昇腾 AWQ 的 nibble 重排与全精度回退
description: 说明 AWQ Dense 快路径条件、零点与 nibble 转换、MoE WNA16 适配和回退显存代价。
tags:
- task.optimization
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/awq_kernels.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/awq/awq.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/awq/schemes/awq_linear.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/awq/schemes/awq_moe.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾 AWQ 的 nibble 重排与全精度回退

## 格式转换机制

AWQ Dense loader 使用 qweight `[K,N/pack]`、qzeros `[K/group,N/pack]` 与 group scales；TP 的 input shard 需满足 group_size 整除，output shard 满足 pack factor。NPU Dense快路径后处理按`[0,4,1,5,2,6,3,7]`重排nibble，并执行`XOR 0x88888888`；附近部分历史注释与实际操作矛盾，应以该固定版本实现为准。

快路径要求 group_size 符合代码谓词：0，或 32 的倍数且 `32<=group_size<K`；从 K 与 scale 组数推导的实际正 group_size 需单独检查。快路径将零点转换为反量化 offset，调用 npu_weight_quant_batchmatmul，BF16 bias 先转 FP32。

不满足快路径时直接提取unsigned nibble，以(weight-zero)*scale反量化、不执行该XOR，加载后形成完整BF16 `[N,K]`权重，推理用 F.linear 并删除原量化存储；此时 GGUF/AWQ 文件小不等于 NPU 常驻权重仍小。AWQ MoE 限 4 bit，w13/w2 同步进行 nibble/zero 转换，通过 NPU WNA16 kernel 和 Ascend runner，不能调用 GPU Marlin。

## 验证与回退

先记录导出 group_size、对称性、TP、快/慢路径，再比较已知 nibble 与零点样例、层输出和 logits。检查 fallback 可能增加的常驻显存与加载峰值。要回退须重新加载全精度或对应原 AWQ 权重，不能对已 repack 的参数重复执行转换。本卡没有型号或收益泛化。
