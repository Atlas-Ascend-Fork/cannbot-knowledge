---
type: Guide
title: SGLang 昇腾 DeepSeek 权重名称与量化分片加载
description: 说明 ModelSlim KV scale 名称、packed 权重映射、expert/fused shard 顺序和 MLA 权重连续布局。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_common/deepseek_weight_loader.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/linear.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾 DeepSeek 权重名称与量化分片加载

## 名称映射先于加载

DeepSeek loader 在 NPU ModelSlim 路径对 `.scale/.offset` 调用 maybe_remap_kv_scale_name，无法映射时跳过；不能任意删除后缀或直接按字符串替换成 weight_scale。stacked Dense 与 expert 映射中，NPU 把 `weight_packed` 规范化为 `weight`，但专家应先走 expert mapping，避免 gate_proj 被重复融合成错误 gate_gate_up 名称。

fused shared experts、NextN target/draft、PP stage 拥有的 embedding/head 有各自名称与跳过条件。当前模型没有对应 indexer module 时会跳过其 checkpoint 权重，不能把所有 skipped weight 都当丢权重，也不能忽略真正缺失的 scale。

## 布局与量化分片

MLA kv_b 权重拆成 w_kc 与 w_vc 后有不同 transpose/contiguous 顺序；NPU 额外把 w_vc contiguous，不能直接采用 GPU transpose view。NPU ReplicatedLinear.weight_loader 在 target 或 source 为 INT8 时强制二者 dtype 一致；多值 per-tensor scale 仅在源/目标形状不同、目标第一维为1，且 torch.allclose(loaded_weight, loaded_weight[0]) 成立时折为首项，否则报错。ColumnParallelLinear/RowParallelLinear 的 loader 没有这两项专属检查，不能概括为所有 Linear 的合同；新整数 W4A4 packing 还影响 merged output 的 TP offset/size。

适配新 checkpoint 时先核对 named_parameters 与映射后的名称，再验证 expert_id/shard_id、scale/offset 和 loaded shape。记录真正加载、按模型结构跳过与因名称不匹配遗漏三类信号，最后比较 Dense/MLA/expert 层输出与模型 logits。加载布局更改须从原 checkpoint 重载回退；本卡不扩展为所有 DeepSeek 变体的部署配方，也未执行上游模型测试。
