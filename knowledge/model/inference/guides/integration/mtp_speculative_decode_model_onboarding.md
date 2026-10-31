---
type: Guide
title: MTP 接入：共享权重、隐状态与惰性注册
description: 新模型接入 MTP 推测解码：draft 构造、主草稿权重共享、prev_hidden_states、惰性注册、packed 输入与贪心 verify；旧三元组注册应迁移到当前模型对。
tags:
- task.debugging
- topic.speculative_decoding
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- agnostic
aliases:
- MTP 接入指南：权重共享、隐状态接口、注册与贪心校验
---

# MTP 接入：共享权重、隐状态与惰性注册

## 当前接入步骤

1. 为模型实现 native MTP 类。`forward` 接受 `input_ids`、`position_ids`、`forward_metadata` 和主模型的 `prev_hidden_states`，返回 `(logits, prev_hidden_states)`。R1 示例通过 `enorm/hnorm → concat → eh_proj` 融合 embedding 与上一隐状态，再进入预测层和共享输出头。
2. 在 `executor/core/support_models.py::_specs` 登记三个 `(module, attr)` 对：主模型、MTP 模型、配置类。`load_model_classes` 惰性解析；`load_speculative_model_classes(name, "mtp")` 要求恰好三项。直接写类对象的 `model_dict` 已不适用。
3. 设置如下配置；关闭时将宽度设为 0。旧 `model_config.next_n` 仍有兼容转换，新旧宽度冲突会拒绝。

```yaml
speculative_config:
  method: mtp
  num_speculative_tokens: 1
```

4. 让 draft 的 `lm_head`、`model.embed_tokens` 为 `None`，由 `BaseSpeculativeWorker.share_weights_from_main_model` 复用主模型层；其他 MTP 专有权重仍需正确加载。R1 映射包括 `shared_head.norm → shared_head_norm`、`enorm`、`hnorm`、`eh_proj`。可选 `draft_model_path` 只改变权重目录，不替代注册及接口约定。
5. 实现并检查模型的缓存声明。`get_cache_info` 按实际 MTP 层及其 CacheEntry 声明缓存，由统一管理器绑定。不要按 draft 调用次数重复分配模型层。

## Worker 的实际行为

`ExecutionEngine.draft_worker` 通过统一基类管理生命周期、共享权重和验证；MTPWorker 负责顺序提案。Prefill 只调用一次 draft：packed token 向左移一位，各请求尾部填主模型 next token；CP 分支还按有效索引恢复全局 token、检查本地隐状态长度。Decode 调用 `next_n` 次，形成固定 `next_n+1` 验证桶。

每轮主模型验证最长匹配前缀；MTP draft 用 argmax 生成候选，target token 则经过当前 Sampler。TP 时引擎广播 token、接受数及 logprobs，随后各 rank 使用相同结果推进 draft。确定性贪心输出应与关闭投机逐 token 对齐；这一验收不能代替任意随机采样分布的正确性证明。DSpark 有独立验证策略，不照搬 native MTP 的前缀比较。

`_pad_seq_len_to_size` 已在基类按 `shape[1]` 填充/截断，旧轴判断缺陷已修复。R1 的 MTP 容器可容纳多预测层，但实际 `forward` 调用容器未传 `mtp_layer_idx`，默认执行首层；文档遍历各层的伪代码不能证明所有层已参与。

## 验收与回退

先关闭投机保存确定性基线，再覆盖零/部分/全部接受、EOS、最大输出截断、多请求、变长 Prefill 和 CP。检查最终消费的 block table、slot mapping、位置与隐状态；缓存和递归状态约束见[缓存规则](../../optimizations/rules/mtp_draft_cache_state_correctness.md)。任何输出差异先排查状态推进，再讨论性能。

按[计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)分别比较每轮成本与每 token 成本；宽度设 0 回退。模型注册支持、图模式、PD、量化组合仍需按具体模型验收。

## Evidence

- [mtp_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py)（primary）
- [base_speculative_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（implementation）
- [support_models.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（implementation）
