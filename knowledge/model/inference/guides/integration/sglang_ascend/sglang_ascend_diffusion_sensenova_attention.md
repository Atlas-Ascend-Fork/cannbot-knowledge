---
type: Guide
title: SGLang Diffusion SenseNova：FIA长度、BNSD与MLP融合
description: 说明可调用FIA的必要条件、变量前缀fallback和无梯度BF16 SwiGLU融合的缓存约束。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/sensenova_u1/neo_unify/modeling_qwen3.py
  role: primary
created_at: '2026-11-08T12:27:29Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
---

# SGLang Diffusion SenseNova：FIA长度、BNSD与MLP融合

## Attention路线

SenseNova Qwen attention仅在NPU、非causal、dropout=0、已知actual KV长度且FIA op可用时使用npu_fused_infer_attention_score。输入可为BSND/BNSD，实际转BNSD，actual Q长度按batch列出query_len，KV长度由Host提供，并传padding。没有这些条件进入fallback；fallback不接受任意BNSD输入，调用侧必须正确转布局。

变量prefix的通用BSND路线按请求循环，不能把不同有效长度一律替成cache最大容量。cache预分配与实际可见长度是独立参数，掩码和长度必须一致。

## MLP与精度

fused MLP要求NPU、eval/no_grad、BF16且权重dtype一致、silu及npu_swiglu存在；打包gate/up权重后linear→swiglu→down。首次 torch.cat 产生临时 packed 分配，随后通过 set_ 把 gate/up 权重重绑定到 packed 两个切片，三者共享存储。缓存复用检查 device、dtype 和 gate 权重的 storage 指针，不检查权重版本；共享存储中的原地权重更新会直接反映到 packed。重新绑定权重存储或迁移设备/dtype 时应核对复用条件，不能概括为所有权重更新都会留下旧副本。

先对比FIA与fallback的变长prefix、padding、无前缀和多batch，再验融合开关数值与缓存重建。融合减少调用；首次打包临时分配、存活共享权重与分配器 reserved 应分别测量，不能推定持续额外 packed 副本，读取Host长度亦可能同步；本次未执行模型或kernel测试，平台未知。
