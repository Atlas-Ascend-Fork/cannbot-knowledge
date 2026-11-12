---
type: Guide
title: SGLang Ascend DSpark链采样：候选stride与接受概率
description: 说明NPU chain sampler的uniform矩阵宽度、target概率准备、cutoff接受截断及bonus索引，区分Torch调度与外部kernel调用。
tags:
- task.implementation
- topic.speculative_decoding
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dspark_accept.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/dspark/dispatch.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/verify_sampling.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/speculative_hook.py
  role: implementation
created_at: '2026-11-08T12:08:05Z'
updated_at: '2026-11-08T12:08:05Z'
platforms: []
aliases:
- AcceptSampling
- chain_speculative_sampling_triton NPU
---

# SGLang Ascend DSpark链采样：候选stride与接受概率

## 分派与概率

AcceptSampling.execute按第一个tensor的is_cuda选择融合或Torch reference；NPU tensor通常走Torch外壳，但accept_sampling的共享core仍调用NPU外部chain sampler。不能只凭方法名torch断定在CPU计算，也不能把所有triton分支都当实际可达。

无top-k/top-p过滤时先按请求温度softmax并reshape为[bs,verify_width,vocab]；否则由共享target概率构造器完成过滤与归一化。draft_probs必须对应实际提案分布；把greedy one-hot与采样proposal混用会改变接受规则。

## NPU stride与输出

NPU chain kernel以candidate完整宽度为uniform_samples行stride，因此uniform矩阵为[bs,candidates.shape[1]]，而其他实现可用gamma；最后一项刻意不消费，因为slot0是root。另生成[bs] final采样uniform。threshold_single/acc均1，deterministic=True是该调用参数，不能据此声称请求确定性模式在所有设备上都支持。

采样结果写predicts、accept_index、accept_token_num。若budget裁短验证，按cutoff_verify_lens进一步cap correct_len并返回cap_trim_lens；bonus从accept_index[row,correct_len]对应predicts取出，不能固定取最后一个draft。block_verification会传额外模式，但启动guard拒绝NPU，不得绕过guard。

## 验证与成本

核对bs、gamma与verify_width=gamma+1、target/draft概率dtype及词表、uniform stride、cutoff和bonus索引。用固定随机输入比较reference与kernel，并以分布统计验收非greedy语义；本次均未执行。全词表概率与scratch可能占较多显存，不能只按draft token数量估算峰值。平台范围仍待明确支持证据。
