---
type: Runbook
title: 多流注意力主流张量被通信流消费致 NPU 内存不释放：跨流消费前 clone 副本解耦生命周期
description: 昇腾多流注意力后端里，主计算流创建的张量被直接拉进独立通信流（torch_npu.npu.stream）context 内消费后，该张量的 NPU 内存不释放——显存只增不减、结果正常无报错，典型出现在 context-parallel（CP）+ chunked prefill 的 gather-global 分支（vllm-ascend / qwen CP chunk 场景）。根因：跨流消费使主流那块内存与消费流生命周期隐式耦合，产出流无法回收。修法：进入通信流消费前先在消费流 context 内 .clone() 一份副本（tmp_local_context_output = local_context_output.clone()），通信流只消费副本、原张量内存即可正常释放；属对因下药解耦跨流生命周期，非绕过机制的 workaround，代价是一次拷贝开销。可迁移判断：多流下凡「主流张量被拉进另一条流的 torch_npu.npu.stream() context 消费」都要警惕内存不释放，标准解法是消费流 clone 副本；适用于用独立通信流做 all-gather / 通信重叠的注意力 / CP 路径。参考实现 vllm-ascend attention_cp.py forward_impl chunked-prefill 分支，merge sha e3725695169f，CI passed、观测确认内存正确释放。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/6479
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多流注意力主流张量被通信流消费致 NPU 内存不释放：跨流消费前 clone 副本解耦生命周期

## 信号（现象）

在昇腾多流（[multi-stream](../../concepts/techniques/multi_stream.md)）注意力后端里，主计算流创建的张量被直接拉进一条独立的通信流 context 内消费后，该张量的 **NPU 内存不释放**——显存持续占用、随迭代累积成内存压力，表现为纯内存问题（显存只增不减），区别于同名变量并发导致的多流卡死。典型出现在 [context-parallel](../../concepts/parallelism/context_parallel.md)（CP）+ chunked prefill 的 gather-global 分支，那里主流产出注意力的局部输出、再切到独立通信流做 all-gather 类通信。

适用范围核对（满足以下全部才落在本页）：

- 用了 **多条 NPU stream**：一条主计算流 + 至少一条独立的通信/搬运流，通信流通过 `wait_stream(torch.npu.current_stream())` 与主流同步后在 `with torch_npu.npu.stream(...)` context 内执行。
- 在通信流的 context 内**直接消费主流刚产出的张量**（把它喂给通信/搬运类算子，本参考实现中为 all-gather 型 `_gather_global_context_output`），没有先在消费流里做一份本地副本。
- 症状是**内存只增不减**，不是数值错、不是 hang（同名变量并发冲突导致的多流卡死是另一签名，见 [multistream-branch-variable-name-collision-hang](../runtime/multistream_branch_variable_name_collision_hang.md)；跨流同步 API 选型是 [graph-mode-multi-stream-cross-stream-sync-api](../../guides/experience/interventions/graph_mode_multi_stream_cross_stream_sync_api.md)）。

## 触发条件

- 注意力后端使用多流编排：主计算流产出张量（此参考实现中为 CP 局部注意力输出 `local_context_output`），一条独立通信流负责 gather。
- 通信流在 `with torch_npu.npu.stream(<comm_stream>):` 的 context 内**直接引用主流那个张量**，作为通信算子（此处 `_gather_global_context_output`）的输入。
- 场景：context parallel + chunked prefill 的全局 gather 分支（qwen CP chunk 场景）。但触发条件本身可迁移到任何「主流张量被拉进另一条流的 `torch_npu.npu.stream()` context 消费」的多流路径，不限于该分支。

## 根因

主流中创建的张量被**跨流**直接在通信流里消费。这种跨流使用使得该张量在原流上的 NPU 内存无法被正常释放——两条流对同一块内存形成生命周期上的隐式耦合，消费流仍在引用/依赖它时，分配它的那条流无法回收这块内存。

因果层级止于「跨流消费 → 原张量内存不释放」；更深的 NPU allocator per-stream 生命周期内部机制不在此展开。可迁移的判断是：**昇腾多流下，一块内存若被产出它的流之外的流引用着，产出流对它的释放就可能被卡住。**

## 修法

进入通信流消费前，先把主流张量 `.clone()` 一份到临时变量，**通信流只消费这个副本**。clone 出的副本归属消费流的生命周期，与原张量解耦；原张量在主流上不再被外部流引用，其 NPU 内存即可正常释放。

```python
with torch_npu.npu.stream(cp_chunkedprefill_comm_stream()):
    # If only local_context_output is used, the NPU memory cannot be released.
    # This problem can be avoided by using clone
    tmp_local_context_output = local_context_output.clone()
    global_context_output = self._gather_global_context_output(
        tmp_local_context_output)
```

要点：

- clone **必须发生在消费流的 context 内**（消费流持有副本），且喂给通信算子的是副本 `tmp_local_context_output`，不是原张量。
- 这是**针对根因的修复**（解耦跨流生命周期），不是关掉/绕过某个正常机制的 workaround——多流与通信照常保留，只是不再让通信流直接持有主流内存。
- 代价：多一次 clone 的拷贝开销，换回原张量内存可被及时释放；在内存受限（[multi-stream](../../concepts/techniques/multi_stream.md) 叠 CP 长序列）场景下这笔交换通常划算。

## 可迁移边界

- **技术层面（可迁移）**：凡「主流产出的张量被拉进另一条流的 `torch_npu.npu.stream()` context 内消费」，都要警惕该张量内存不释放；标准解法是在消费流内 clone 副本、让消费流只持有副本。这条「症状（内存不释放）→ 根因（跨流消费耦合生命周期）→ 修法（消费流 clone）」可迁移到其它用独立通信流做 all-gather / all-to-all / 通信重叠的注意力 / CP 路径。
- **参考实现专属（不是技术本身的限制）**：具体张量名 `local_context_output`、通信流 `cp_chunkedprefill_comm_stream()`、gather 函数 `_gather_global_context_output`、以及「qwen chunked-prefill 分支」这些都是该参考实现的细节，不构成技术边界。

## 参考实现及其约束

- 后端：`vllm-project/vllm-ascend`（vLLM 的昇腾 NPU 后端）context-parallel 注意力后端。
- 文件：`vllm_ascend/attention/context_parallel/attention_cp.py`，`forward_impl` 内 chunked-prefill 的 gather-global 分支。
- 该后端的多流机制前提：主计算流 + 独立通信流 `cp_chunkedprefill_comm_stream()`，通信流以 `wait_stream(torch.npu.current_stream())` 与主流同步后在其 `torch_npu.npu.stream(...)` context 内执行 all-gather 类通信。
- 约束：修法只在该 gather-global 分支落地（单文件 4 增 1 删）；副本引入一次拷贝开销。此为该参考实现的落点范围，不代表技术只适用于此。

## Outcome

- 参考实现自报：CI passed；观测确认该场景下 NPU 内存现在能正确释放。无独立复测的定量 before→after 数字。
- 改动规模：单文件 4 增 1 删。

## Evidence

- claim：[npu-多流注意力中主流创建的张量在通信流内被消费导致其-npu-内存不释放-消费前-clone-进通信流即可解](https://github.com/vllm-project/vllm-ascend/pull/6479)
- 事件源：[vllm-ascend-pr-6479-0-13-0-bugfix-fix-npu-memory-is-not-released-in-cp](https://github.com/vllm-project/vllm-ascend/pull/6479)
- 一手：合并态 diff（merge commit `e3725695169f9a6a43e19b2edd1b5ed970c698b2`，state MERGED）中 `attention_cp.py` 的 clone 修法，事件页 Changes 记为 `attention_cp.py` 4 增 1 删。
- 因果层级：跨流消费导致内存不释放，源自事件源的 PR 描述与 review comment；更深的 NPU allocator per-stream 生命周期内部机制不在证据范围内。
