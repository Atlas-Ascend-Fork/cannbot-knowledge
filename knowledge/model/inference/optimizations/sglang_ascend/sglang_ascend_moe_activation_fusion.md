---
type: Optimization
title: SGLang 昇腾专家激活的限幅位置与融合守卫
description: 区分 plain SwiGLU、OAI、SiTU 和 swiglu_limit，说明 group_list 语义与激活量化输出。
tags:
- task.optimization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/activation.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/moe/matmul.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/ascend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang 昇腾专家激活的限幅位置与融合守卫

## 场景与问题信号

MoE logits 漂移或只在特定模型上出错时，应检查 gate/up 顺序和限幅位置。`NPUSwigluWithLimit` 在 FP32 中先截 gate 上界与 up 的正负范围，再对 gate 做 SiLU；StepAndMul 的限制发生在 SiLU 之后，两者不能互换。

DeepEP 的 OAI 激活只有同时传入 alpha 与 limit 才选择对应 swiglu_oai_quant；不传模型参数会走 plain SwiGLU。SiTU 有 beta/linear_beta 约定和纯算子 fallback；950 的 SiTU+MXFP8 融合还需显式环境 opt-in，并要求 clamp 条件，不能仅按 dtype 自动开启。

## 融合与 dtype

Ascend runner的_uses_fused_gmm1先排除SiTU、非MXFP8/W4A8-MXFP4 kernel和正swiglu_limit；剩余NPUMXFP8MoEMethod直接返回True，W4A8-MXFP4还读取kernel.use_fused_gmm1。该守卫没有检查OAI、gemm1_alpha或gemm1_clamp_limit，不能声称已保证plain SwiGLU；融合仅表达plain SiLU且随后跳过独立activation，因此使用前须额外确认模型为plain SwiGLU，并排除未被守卫保护的OAI/StepAndMul参数语义，否则有静态数值风险。grouped swiglu quant 要求 runner 传 counts (`group_list_type=1`)，调用原生 swiglu_group_quant 时该算子的 group_list_type=0 才表示相同 counts，枚举属于不同接口。

激活可返回 `(payload,scale)` 供 w2 使用，need_quant=False 则丢弃 scale。AllGatherActivationWrapper 只 gather 激活，不会自动 gather scale。

启用融合前比较 unfused 的 w13、激活后值、w2 和最终 combine；重点测试 limit 边缘值与空 expert。代价是更窄的语义支持范围和量化舍入变化；回退到明确的 GMM→激活→量化路径重新构造 runner。来源没有本次真机性能结果。

## 下层接口参考

- [SGL SiTU 与 MXFP8 融合接口](../../apis/sgl_kernel_npu/sgl_situ_mxfp8_quant.md)
- [SGL 分组 SwiGLU 量化接口](../../apis/sgl_kernel_npu/sgl_swiglu_group_quant.md)
- [SGL SwiGLU-OAI 量化接口](../../apis/sgl_kernel_npu/sgl_swiglu_oai_quant.md)
