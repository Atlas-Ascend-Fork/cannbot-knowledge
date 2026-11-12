---
type: Guide
title: SGLang 昇腾模型变体的明确排除与证据强度
description: 区分ERNIE5.5 Flash的CUDA-only强制拒绝与Bailing MoE V3旧注释，按NPU gate生产及消费调用链判断证据。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/ernie55.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/bailing_moe_v3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/deepseek_v2_attention_mla_npu.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang 昇腾模型变体的明确排除与证据强度

## 强制拒绝的模型

ERNIE5.5 Flash 的 check_supported_deployment 在非 CUDA 时立即 ValueError，明确提示只支持 CUDA；注释指出 HIP/NPU prepare 直接调用 wq_b，跳过该变体需要的 gate split。不能因模型复用了 DeepSeek 公共类或存在 NPU imports 就将此架构列为可运行。

CUDA 分支另要求 attention-TP 整除多个 head/output-group/block 范围；这些检查不能作为 NPU 支持的补充条件，因为 NPU 在更早处已经被拒绝。可靠回退是选择有 NPU 适配的模型/变体或使用受支持设备，不能删除拒绝 guard 后声称完成迁移。

## 旧注释必须追踪实际消费者

Bailing MoE V3构造函数仍有gated_attn不支持NPU的旧注释，但forward已生成gate并作为inner_state尾参数传给forward_core。固定提交的forward_mla_core_npu明确接收可选gate，在attention/value投影后调用m._apply_gated，再o_proj；head_wise按local heads广播，element_wise逐元素相乘。

因此不能将该注释定性为当前缺失NPU gate消费，也不能仅凭可达路径认定所有型号/量化/图模式已通过。选择时核对准确architecture、gate粒度/shape与实际分派，覆盖gate有无、两种粒度、融合/非融合及整模型精度。ERNIE5.5的明确运行时拒绝仍单独成立，本次未实测这些模型。

## 相关机制

- [SGLang 昇腾模型支持矩阵的使用与新旧差异](../deployment/sglang_ascend/sglang_ascend_doc_model_support_evidence.md)
