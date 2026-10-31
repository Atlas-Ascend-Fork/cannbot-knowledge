---
type: Optimization
title: MTP 与分片 Prefill 的缓存和请求边界
description: 更新为统一 Executor 的实际预测层缓存声明、packed 请求边界与 CP 元数据，不保留私有 cycle runner 接口。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:41:22Z'
platforms:
- agnostic
---

# MTP 与分片 Prefill 的缓存和请求边界

## 当前约束

预测层数、草稿步数、Prefill 调度批次是三个不同维度。当前 Executor 已替换模型私有 `model_infer.py`；按 cycle_idx 延后补跑 draft 的旧 GLM 流程不再是公共接口。

- 模型按实际预测层声明缓存；R1 的 `get_cache_info` 遍历 MTP 层容器。`next_n` 控制每轮提案数和主模型验证桶宽度，不决定缓存层数。
- `MTPWorker.inference` 在 Prefill 仅跑一次，在 Decode 跑 `next_n` 次。Prefill 后首提案会填充至固定宽度，后续 Decode 再顺序提案；不能把每个 Prefill 小批次当作已完成整个请求，提前跑完整 Decode 草稿链。
- Packed Prefill 使用每请求 seq_lens 和累计边界构造左移输入，各请求尾部替换为对应 next token；`request_offset` 保持调度批次定位。不要按统一 input_max_len 重新 pad+cumsum 覆盖真实长度。
- CP Prefill 通过 cp_metadata 恢复全局有效 token、选择本 rank 输出请求，隐状态长度按 local_token_num 检查；不能套用单 batch per die 的下标公式。

## 接入检查

同时覆盖不等长请求、多个 Prefill 小批次、next_n>1 和请求所有者映射，核对 block table、slot mapping、Q/KV 累计长度与位置是否描述同一批 token。R1 当前 MTP forward 默认执行首预测层；容器声明多层并不证明各层均被调用。

[缓存状态规则](mtp_draft_cache_state_correctness.md)负责状态推进；[MTP 接入](../../guides/integration/mtp_speculative_decode_model_onboarding.md)负责注册与模型接口。来源未给隔离该记账改动的性能或显存对照，不宣称定量收益。

## Evidence

- [mtp_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py)（primary）
- [base_speculative_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（implementation）
- [scheduler.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py)（implementation）
