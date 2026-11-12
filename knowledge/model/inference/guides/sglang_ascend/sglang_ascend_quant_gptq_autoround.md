---
type: Guide
title: SGLang 昇腾 GPTQ 与 AutoRound 的解包和 TP 精度边界
description: 说明 GPTQ v1/v2 零点差异、desc_act 限制及4-bit专家负 scale 修正对 TP shard 的要求。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/gptq_kernels.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/gptq/gptq.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/gptq/schemes/gptq_linear.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/gptq/schemes/gptq_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/auto_round.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾 GPTQ 与 AutoRound 的解包和 TP 精度边界

## Dense 与专家的实际适配

NPU 注册 GPTQAscendConfig，激活支持 FP16/BF16。Dense 的 `desc_act=True` 明确不支持；加载 qweight `[K/pack,N]`、group qzeros 与 scales 后解包 nibble，减去 `2^(bits-1)`；只有非 gptq_v2 零点才额外加一。4-bit 权重经 npu_convert_weight_to_int4pack，其他位宽使用解包 INT8，计算由 npu_weight_quant_batchmatmul 完成。

MoE 选 Ascend WNA16 kernels。仅在 weight_bits==4 分支执行负 scale 修正：翻转对应量化权重并取 scale 绝对值，对 -(-8)=8 超出 4-bit 上界的值截到 7。但只有 `groups*group_size` 与实际 K shard 对齐时才做修正；TP 分片不匹配会告警并跳过，存在精度风险，源码建议改 TP 或使用 DeepEP，不能把告警当无关日志。其他位宽分支仅保存解包权重，不执行该负scale修正或K shard不匹配告警。

AutoRound 先按 packing_format/backend 分派：含 gptq 时进入 apply_gptq_quant_layer，含 awq 时走另一条 apply_awq_quant_layer。仅前一 GPTQ 路线的 NPU 分支为每 layer 保留 bits、group_size、sym 并选择 GPTQAscendConfig；16-bit 层保留未量化方法，该 GPTQ/NPU 路线不改走 GPU Marlin，不能推广到所有 AutoRound 格式。

## 验证与回退

转换前确认 GPTQ 版本、desc_act、零点与 group_size，再逐 rank 核对真实 K shard。至少比较负 scale、边界 nibble、不同 TP 和 MoE expert 的输出及 logits。量化误差、截断与 TP 不匹配是不同问题；先消除 mismatch 再评估压缩收益。回退通过重新加载匹配参数或全精度 checkpoint，本次未执行量化精度或性能测试。
