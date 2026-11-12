---
type: Guide
title: SGLang 昇腾 DSV4 NextN 的多流残差与单层收尾
description: 说明 NextN HC 隐状态投影、DP token ID gather、逐 forward RoPE 以及必须完成的 deferred
  HC post。
tags:
- task.implementation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4_nextn.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 DSV4 NextN 的多流残差与单层收尾

## HC 输入与位置信息

DSV4 NextN 将 target spec hidden states view 成 `[tokens*hc_mult,H]`，hnorm+h_proj 后恢复多流，再与 enorm+e_proj 的 embedding 相加。空 token 则构造匹配的多流形状，不能沿用普通单流 NextN 的拼接规则。

attention DP>1 且无 A2A 时，input IDs 用 dp_gather_replicate 收集；attention-TP peers 的 IDs 已复制，不能用求和 gather 把 token ID 乘以 TP。调用前 clone，避免 MAX_LEN gather 对本地输入清零产生副作用。

## 单层 draft 的收尾

NPU 在 decoder 前 prime 当前 forward 的 RoPE cos/sin；prefill CP 启用时先准备 DSV4 CP metadata 和 local positions。非 CUDA decoder 返回 hidden、residual、post、comb；有 deferred residual 必须显式 hc_post，因为 NextN 只有一层，没有后继层消费此状态。

最终同时保留 pre_hc_head flattened state 和 hc_head+shared norm 的 hidden，供 logits 与后续 speculative 状态使用；wo_a 是否量化沿 target 相同守卫设置，但不等于复用 target 的所有执行布局。

验证 DP/TP token IDs、HC shape、空 batch、target/draft 共享 RoPE 时 positions 更新和残差只完成一次。关闭 speculative 或重建匹配的 NextN 状态可回退；本卡未执行多卡运行或加速测量。
