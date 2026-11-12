---
type: Guide
title: SGLang 昇腾多模型 MoE 的路由语义与空批次
description: 保留 AFMoE、ERNIE4、DBRX、Xverse、DeepSeek、SDAR 与 Step3.5 的 NPU 路由和缩放差异。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/afmoe.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/ernie4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/dbrx.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/xverse_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/sdar_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/step3p5.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾多模型 MoE 的路由语义与空批次

## 路由与激活的模型参数

AFMoE 在 NPU 把 expert_bias 传成 correction_bias，并显式设置 scoring_func 和 apply_routed_scaling_factor_on_output；sigmoid 的 renormalize 与 softmax 情况不同，不能只复制 top-k 值。ERNIE4 只接受 SiLU，NPU 的 correction_bias 需 squeeze 掉第 0 维，满足一维输入要求。

DBRX、Xverse 和旧 DeepSeek 选择 fused_moe_npu，而不是 GPU Triton fused_moe。它们仍有自己的权重打包、gate 与 shared expert 构造；仅看到 NPU 方法选择不证明所有量化 checkpoint 和并行组合可用。

SDAR 和 Step3.5 在 deepep 或 ascend_fuseep 时进入 forward_deepep。空 token rank 使用 empty_topk_output，但仍调用 experts 参与 collective，不能为了避开空 GEMM 把整个 MoE 提前返回。Step3.5 按 need_fp32_gate 计算 router，并在 shared output 汇合处只施加一次 routed_scaling_factor；shared expert 在含 ascend_fuseep 的通信场景采用 replicated 分组。

## 迁移与验证

逐项核对 score、bias、renormalize、scaling 与 shared/routed 分组，再验证 TopK IDs/weights、空 DP rank、最终 logits。错误的重复缩放可能没有 shape 报错；以逐 expert 参考汇合定位。更改后端需要匹配加载布局并重建通信状态。本卡汇总模型入口差异，没有声称通用 fused_moe_npu 覆盖所有模型特性或实测收益。
