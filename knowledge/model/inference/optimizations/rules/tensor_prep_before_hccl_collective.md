---
type: Optimization
title: 集合通信前的张量准备陷阱（行并行 bias 重复累加、zeros vs empty 覆写）
description: 集合通信前的张量准备陷阱（行并行 bias 重复累加、zeros vs empty 覆写）。HCCL 集合通信会累加（all_reduce）或整体覆写（all_gather_into_tensor / all_to_all_single）它的输出。所以集合通信前的张量准备必须考虑通信语义——否则要么静默数值错误、要么白白多一次 kernel。两条易错。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/195
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/168
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# 集合通信前的张量准备陷阱（行并行 bias 重复累加、zeros vs empty 覆写）

## 适用场景

HCCL 集合通信会**累加**（`all_reduce`）或**整体覆写**（`all_gather_into_tensor` / `all_to_all_single`）它的输出。所以集合通信前的张量准备必须考虑通信语义——否则要么静默数值错误、要么白白多一次 kernel。两条易错。

## 陷阱一：行并行 + all_reduce 的 bias 必须只在 rank 0 加载

**场景**：投影按行切到各卡（[RowParallelLinear](../../concepts/parallelism/tensor_parallel.md) 语义），各卡算部分和后用 `all_reduce` 跨卡求和汇总，且该投影带 bias（如专家/FFN 的 `down_proj`）。

**问题**：bias 是不随行切分的完整向量。若每张卡都在本地部分和上加完整 bias 再 `all_reduce`，bias 被求和 `tp_size` 次：结果 = 真实和 + `(tp_size-1)×bias`。**无报错、随卡数放大**，容易在 TP 扩卡时才暴露精度漂移。

**手段**：权重加载阶段对"行切且走 all_reduce"的 bias 做 rank-0-only 载入：

```python
if tp_rank == 0:
    param.data.copy_(loaded_bias)   # 只有 rank 0 载真实 bias
else:
    param.data.zero_()              # 其余 rank 清零
```

这样 `all_reduce` 汇总后 bias 恰好只计一次。**判据** = "该 bias 所在投影是否在 all_reduce 之前被完整叠加"。对照：列切权重（`ColumnParallel`，如合并的 `gate_up_proj`）各卡持各自列切片对应的 bias 片段、不经 all_reduce 求和，无此问题，按普通切片各自载入即可。

## 陷阱二：被集合通信整体覆写的输出缓冲用 empty_like，别用 zeros_like

**场景**：输出缓冲区分配后**立即被某个集合通信的完整输出整体写满**——如 lm_head 的 TP `all_gather_into_tensor`、SP prefill 的 `all_gather_into_tensor`、logits 的 `all_to_all_single`。

**规则**：集合通信写满整个缓冲，因此分配时 `zeros_like` 预清零那次 kernel 毫无意义（0 立即被通信结果覆盖）。改用 `empty_like`（不清零）省掉集合通信前每处一次的清零 kernel，语义不变。

**关键 anti-pattern**：仅当缓冲随后被**整体覆写**才安全。对**部分写入**的缓冲不可套用——例如 `scatter_` 只写选中位置、其余元素需保持 0，换成 `empty_like` 会读到未初始化残值。改前必须确认该缓冲会被后续操作 **100% 覆盖**，否则保留 `zeros_like`。（同一建模文件里 `group_limited_greedy` 分支就有 `empty_like` 后接 `scatter_` 的部分写入形态，只因该模型实际走 `noaux_tc` 分支、该路径是死代码才未触发错误——正说明部分写入是本手段禁区。）

## 参考实现

陷阱一：[GPT-OSS](../../concepts/models/gpt_oss.md) 128-专家 MoE 的 `down_proj`（`moe_tp_size>1` 时 `all_reduce`），`GptOssForCausalLM.load_weights` 的 rank-0-only bias 分支。规则不限 MoE，任何"行切 + all_reduce + 带 bias"的层同理。陷阱二：[DeepSeek-R1](../../concepts/models/deepseek_r1.md)（含 MTP 头，复用同一 SP prefill 路径）的 `DeepseekV3ForCausalLM.forward` / `DeepseekV3ModelMTP`。

## Evidence

- `diff 事实`（@f8e36fc3，陷阱一）：`load_weights` 里 `down_proj_bias` rank-0-载真值/其余清零、`GptOssExperts.forward` 的 `moe_tp_size>1 → all_reduce`。属正确性约束、非性能，源无 benchmark。溯源下探：[cann-recipes-infer-pr-195-feat-add-gpt-oss-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/195)
- `diff 事实`（@30d45bc4，陷阱二）：`forward` / `ModelMTP` 的 `zeros_like → empty_like` 均"紧跟一个整体覆写的 HCCL 集合通信"；`group_mask` 那处 `empty_like` 后接 `scatter_` 在 R1 未走的 `group_limited_greedy` 分支。溯源下探：[cann-recipes-infer-pr-168-feat-for-ds-r1-skip-tensor-creation-before-calling-hccl-enable-static-ke](https://gitcode.com/cann/cann-recipes-infer/merge_requests/168)
