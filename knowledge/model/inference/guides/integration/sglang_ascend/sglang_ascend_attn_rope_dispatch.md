---
type: Guide
title: SGLang Ascend RoPE分派：可选融合kernel与原生回退
description: 说明fused_rope_qk_mqa缺失时的模型导入保护、token与dtype守卫、npu_mrope形状适配和rotary_mul边界。
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/base.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/utils.py
  role: implementation
created_at: '2026-11-08T12:07:59Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- fused_rope_qk_mqa
- RotaryEmbedding.forward_npu
---

# SGLang Ascend RoPE分派：可选融合kernel与原生回退

## 可选依赖与导入边界

NPU的fused_rope_qk_mqa是可选kernel。ImportError被转换为None并记录warning，避免因依赖缺失使ModelRegistry跳过依赖RoPE的模型；调用点仍必须检查None并回退，不能只捕获导入错误后继续无条件调用。

## 实际分派

forward_npu拒绝fused_set_kv_buffer_arg。若Q为BF16且cos/sin为FP32，或K为3维，优先使用预gather表（已有sin_cos_cache或按positions index_select）；只有kernel可用且token数<65535才融合，否则forward_native。其他分支选half（NeoX）或interleave模式，将Q/K展平到2维调用npu_mrope再恢复原shape。

融合 kernel 与 npu_mrope 两条快路均按原始 positions 取表/计算，不应用 offsets；forward_native 仅在没有预选 sin_cos_cache 时以 positions+offsets 取表。调用方应预先合并有效位置，或为支持预选表的分支准备对应位置的表；需要通过 offsets 参数计算位置时须选择 native 路径并确认未被预选表覆盖。否则 token 阈值或 kernel 可见性变化可能改变实际旋转位置。

cache通常按模型dtype保存，只有FP32开关/特定平台规则保留FP32；强制native时torch.compile对NPU关闭。不能把CUDA的BF16 RoPE+KV store能力标记套到NPU，相关能力guard只给CUDA。

辅助apply_rotary_pos_emb_npu只在cos为2维、Q为3维、head数<1000且head维<896时使用npu_rotary_mul；不符合时回退native。这个guard是调用尺寸限制，不构成产品支持矩阵。

## 接入与验证

检查可选kernel可见性、cache dtype、Q/K rank、token阈值、NeoX/interleave和positions/offset。测试缺依赖可导入、阈值两侧、partial rotary和维度恢复，比较融合与native输出。回退增加分步计算但保留可加载性；本次未运行数值测试，也不声称融合完全数值等价。
