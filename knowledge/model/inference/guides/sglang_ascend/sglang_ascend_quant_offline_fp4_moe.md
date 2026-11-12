---
type: Guide
title: SGLang 昇腾离线 FP4 专家与 DSV4 路由守卫
description: 区分 ModelSlim W4A8/W4A4 MXFP4 专家和 DSV4 专用 FP4 方法，保留原始 scale、激活与融合边界。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/fp4_moe_methods.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w4a4_mxfp4_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/modelslim/schemes/modelslim_w4a8_mxfp4_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/unit/npu/quantization/test_fp4_moe_methods.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾离线 FP4 专家与 DSV4 路由守卫

## packed 权重与路由边界

离线 FP4 expert 权重用 uint8 装两个 FP4 值：w13 `[E,2I,H/2]`，w2 `[E,H,I/2]`，每 32 个值一个 raw E8M0 scale。ModelSlim W4A8_MXFP 与 W4A4_MXFP4 分别选择 A8 MXFP8 或 A4 FP4；即使 checkpoint payload 形状相同，激活与 GMM dtype 参数也不相同。

Fp8Config先处理is_fp4_experts且dequant_fp4_to_fp8=True的分支（对应SGLANG_DSV4_FP4_DEQUANT=1）：要求runner为auto并直接返回Fp8MoEMethod，即使arch35且is_dsv4_fp4_experts成立也不进入专用FP4方法。排除该模式后，DSV4专用`NPUW4A8MXFP4FusedMoEMethod`才在arch35且确认is_dsv4_fp4_experts时选中；其他FP4-expert模型走各自fallback。后文专用方法的原始scale加载与auto/ascend runner边界不适用于这个先行反量化分支。该方法只允许 auto/ascend runner，原始 E8M0 scale 不再重量化；scale 初始为零，加载后全零会按缺失 checkpoint 参数名失败，应检查命名映射，不能把其当正常可用尺度。

## 通信与激活

W4A8 正常通信采用 BF16，LL 可以 MXFP8；W4A4 通信 BF16并在两次 GMM 前本地量化 FP4。W4A8 的 plain SwiGLU 可融合 gmm1，但 DSV4 的 swiglu_limit 等语义必须保留，不能以融合名字推断已包含限幅。

先检查 raw scale bytes、配对数与 NZ-before-transpose，再检查 runner、wire dtype 和模型激活参数；用 full-precision baseline 比较专家输出、combine 与 logits。上游 unit/npu 测试使用算子 stub 验证 loading/runner wiring，不代表执行 Device kernel。本次没有运行它或报告吞吐收益。
