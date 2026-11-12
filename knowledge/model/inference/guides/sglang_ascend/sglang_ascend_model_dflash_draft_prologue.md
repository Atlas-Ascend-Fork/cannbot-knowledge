---
type: Guide
title: SGLang 昇腾 DFlash draft 的 Norm、RoPE 与 sink 边界
description: 说明 draft 训练 rotary width、Gemma Norm 回退、普通 QK 融合、FP32 sink 与当前重复投影位置。
tags:
- task.implementation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/dflash.py
  role: primary
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 DFlash draft 的 Norm、RoPE 与 sink 边界

## draft 的位置与 Norm

DFlash 可从显式 rope_dim 取训练时旋转宽度，覆盖 target 拷贝来的 partial/M-RoPE 字段；draft 只看一维 positions。NPU 排除 table_qk_norm_rope 的 GPU 快路径。Gemma Norm 分支显式 apply_qk_norm(allow_inplace=False) 再 RoPE，保留 `1+w` 语义；普通 RMSNorm 才走 NPU split+QK norm+RoPE，layer0 先刷新位置表，并传可选 bias。

NPU 的一般 attention_sink_bias 为 FP32；Nemotron3.5 DSpark sinks 另要求 trtllm_mha draft backend，此限制不能因 NPU 有普通 sink 参数就忽略。v_scale 在 attention 前作用于 V，再应用模型输出处理。

## 定位与验证

当前 forward 在调用 NPU prepare 前已计算一次 qkv，而 NPU helper 自己再次 qkv_proj；因此 profiling 发现两次投影时，应先核对此固定版本调用链。这里记录源码现象，没有修改上游或声称移除一次投影已经验证正确/提速。

验证 target/draft 不同 rotary_dim、Gemma/普通 norm、sink/无 sink、TP head 整除和长 positions，比较 draft hidden 与验收概率。回退到匹配的 native 公式仍要保留 trained rope_dim 与 sink 条件；不得为凑融合删除语义。本次未执行 DFlash 模型或 speculative 性能测试。
