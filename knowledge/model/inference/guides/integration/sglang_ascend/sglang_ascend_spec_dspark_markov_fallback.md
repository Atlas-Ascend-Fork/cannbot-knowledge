---
type: Guide
title: SGLang Ascend DSpark草稿与预算：舍入一致的Markov回退
description: 说明Markov提案的dtype舍入、非CUDA参考分派、TP采样tie-break，以及NPU预算排序与KV投影融合限制。
tags:
- task.implementation
- topic.speculative_decoding
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dspark_draft_model.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/markov_sample.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dspark_schedule.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dispatch.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dspark_components/dspark_draft.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dspark_components/dspark_worker_v2.py
  role: implementation
created_at: '2026-11-08T12:08:06Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
aliases:
- MarkovGreedyStep
- MarkovSampleStep
- ScheduleVerifyLensTopk
---

# SGLang Ascend DSpark草稿与预算：舍入一致的Markov回退

## Markov提案与数值路线

MarkovGreedyStep计算base_logits+linear(prev_embeds,w2)后argmax。execute检查base_logits.is_cuda，非CUDA走Torch reference；其triton方法虽含NPU专用导入，标准NPU调用不能仅凭该分支存在就声称实际已融合。reference保留投影输出与加法的模型dtype舍入，CUDA融合FP32积累可能在近tie产生不同draft；target verify约束最终输出，但接受率可变化。

MarkovSampleStep同样由inputs_on_cuda决定。reference先将base+bias按step_dtype舍入，再在FP32进行温度与Philox噪声处理；greedy行不加采样噪声，padding词表mask为负无穷。未汇聚完整 logits 的 TP 路径只交换局部最大值与全局id，tie选择最小global id；NaN也遵循显式优先/最小id规则，不能依赖不稳定reduce顺序。若 gather_logits 与 logits_out 同时非空，先汇聚整个词表的舍入 logits，再执行 token 选择。DSpark 非 sharded_accept 调用传入此回调，而 sharded_accept 仅为 HIP 启用；因此 NPU 词表分片且保留 logits 时包含完整 logits 通信，不能只按候选交换估算。

## 预算回退

ScheduleVerifyLensTopk的NPU执行使用Torch排序reference，arch35显式回退，其他NPU也因is_cuda=False落到reference。其confidence转FP32累计乘积形成survival，再按概率降序、位置和请求id稳定排序分配额外budget，最终verify长度夹在min/max之间。不能用GPU O(n²) rank kernel替代：源码指出对应Triton-Ascend TTIR→Linalg模式无法合法化。

跨层stacked/fused commit-KV projection在NPU显式unsupported，回退逐linear投影；不能把GPU权重stack和量化dequant规则无条件迁入。

## 验证

检查实际分派、step_dtype、近tie、采样seed/offset、TP shard边界、budget0和survival阈值。建议对同批/单请求、greedy/采样混合、NaN/tie和稳定budget结果做对照，再评估reference额外操作成本。本次没有执行数值或性能测试，也未运行GPU融合kernel；不以外部原语存在证明其在本worker可达。
