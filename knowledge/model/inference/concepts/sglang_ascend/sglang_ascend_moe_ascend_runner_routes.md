---
type: Concept
title: SGLang Ascend runner 的多通信模式与全容量汇合
description: 连接 Standard、AllToAllV、AllGather、MC2 与 DeepEP hooks，说明全局 expert 范围和 FP32
  汇合边界。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/ascend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/fused_moe_triton/layer.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/runner.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/unquant.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/ep_moe/layer.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/token_dispatcher/base.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/token_dispatcher/__init__.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/__init__.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/token_dispatcher/ascend_ops.py
  role: implementation
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:30:20Z'
platforms: []
---

# SGLang Ascend runner 的多通信模式与全容量汇合

## 计算流程与布局边界

AscendRunnerCore 将各 dispatcher 的 permute/unpermute hook 与 w13→activation→w2 计算连接。Standard 路径要求 StandardTopK，拒绝 pre_quant_input，由 hook 做 NPU routing 和 weighted finalize。`--moe-a2a-backend none` 要求每 rank 持有完整 expert 范围；普通 EP>1 的 rank-local expert 不能套 global expert 索引，构造时失败，DWDP 全权重视图例外。

AllToAllV 收到数据后按本地 expert 再路由，并复用收到的 scale；只有一个本地 expert 时可跳过这次重排。反向先恢复接收顺序，再 inverse AllToAllV。DeepEP normal 把 CPU counts 转 INT64，LL 使用 masked counts；MC2 输入已按 expert 分组且必须带对应 forward state。

## AllGather 的数值与容量

AllGather 仅在 prefill 被选择，要求 TP=EP、`num_local_experts×EP=num_experts`、连续 expert 布局且无 fused shared experts；decode 转入 low-latency MC2。以下本地 ID 转换与 FP32 汇合仅适用于满足这些条件的 AllGather 路径。

AllGather 本地 expert IDs 由全局范围转换，非本地路由使用 sentinel=num_local_experts 并把权重置零，不能替换为 -1。汇合按 `[global_tokens*topk,H]` 全容量保存 FP32 贡献，未用行清零，跨 ReduceScatter 保持 FP32 后再转输入 dtype，避免中间 BF16 舍入或未初始化 NaN 污染。

验证每种通信模式的路由总数、逆映射、空 expert、padding 与输出 dtype，分别比较 TP=1、EP 与不均衡 token 分布。原始 x 为 FP16 时按 FP16，否则通常 BF16。公共 MoE LoRA hooks 也接入启用 LoRA 的 MarlinLoraRunnerCore；AscendRunnerCore 尚未消费这些 expert LoRA hooks，通用类型带 LoRA 字段不能证明 Ascend 已支持。本卡没有 Device 或性能实测结论。
