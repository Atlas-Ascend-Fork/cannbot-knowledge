---
type: Runbook
title: 集合通信参与方逐 rank 对齐：按本地状态决定「是否进入集合通信」导致发散型挂死/超时
description: 集合通信参与方逐 rank 对齐：按本地状态决定「是否进入集合通信」导致发散型挂死/超时。分布式推理（TP × DP × EP / 序列并行）正常跑一段后无进展地卡住，最终以某个集合通信算子超时暴露：HCCL all-reduce / all-gather 挂起、Ulysses attention 的 ALLTOALL 超时、或 NCCL/HCCL watchdog timeout。多数情况无必然报错、就是不动了；HCCL 侧还可能表现为 AIV all-reduce 计数发散后 deadlock。当挂点落在集合通信算子上、且硬件/网络自检（TLS、链路）都正常时，优先怀疑本签名。
tags:
- task.debugging
- topic.kv_cache
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/315
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/325
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:32:48Z'
platforms:
- agnostic
---

# 集合通信参与方逐 rank 对齐：按本地状态决定「是否进入集合通信」导致发散型挂死/超时

## 适用场景 / 信号

分布式推理（[TP](../../concepts/parallelism/tensor_parallel.md) × [DP](../../concepts/parallelism/data_parallel.md) × EP / [序列并行](../../concepts/parallelism/ulysses.md)）正常跑一段后**无进展地卡住**，最终以某个集合通信算子超时暴露：HCCL all-reduce / all-gather 挂起、Ulysses attention 的 `ALLTOALL` 超时、或 NCCL/HCCL watchdog timeout。多数情况**无必然报错**、就是不动了；HCCL 侧还可能表现为 AIV all-reduce 计数发散后 deadlock。当挂点落在集合通信算子上、且硬件/网络自检（TLS、链路）都正常时，优先怀疑本签名。

## 根因（统一签名）

同一进程组里做**同一次**集合通信的各 rank，参与方必须**逐 rank 完全一致**——每个 rank 在每个集合通信点的到达次数与时机都要对齐。一旦「某 rank 是否进入某次集合通信」取决于**该 rank 的本地状态**（本地有没有工作、本地 `seq_len`、按本地量键控的缓存是否命中），不同 rank 就会在同一集合通信点上一部分进入、一部分跳过（或多进入一次），参与方发散 → 集合通信永远凑不齐 → 进程组挂起 → 超时。这是分布式集合通信的固有正确性约束（参与方必须一致），与具体框架无关。

## 迁移准则

在任何分布式路径上，「一个 rank 是否发起 / 进入某次集合通信」**绝不能取决于可能因 rank 而异的本地量**。两条落地方式：

- **无条件对齐**：本地没有真实工作也要跑一个**占位前向**保持集合通信节奏，让缺席方不缺席；
- **判定建立在全组一致的量上**：先用一次全组一致的集合通信 / 共识把「要不要通信、通信多长」同步开，再各自执行；并且**绝不缓存 / 条件化**那些「本地可不同」的集合通信结果——键控缓存会让命中态随 rank 发散，正是最隐蔽的一类发散源。

## 参考实现一：online 连续批调度——无工作 rank 陪跑 dummy + `has_work()` 排除 CPU-only 队列

[online PD 分离](../../concepts/frameworks/online_pd_inference.md)连续批调度里，`run_step` 按显式 `phase`（prefill/decode）推进；某 rank 本步没有本地可跑请求时若直接不进 `forward_batch`，同 DP 组其它 TP rank 会在集合通信处等它。处置：

- **无工作 rank 合成 dummy batch 陪跑**：构造 1-token 假请求（`request_id=-1` 永不与真实态碰撞、未知 id 解析为空 block 列表用 null block 补齐、`is_dummy=True`），照常跑一次 `forward_batch` 保持集合通信对齐，前向后跳过状态更新与输出：
  ```python
  output = engine.forward_batch(batch)   # dummy 也要跑，保持集合通信对齐
  if batch.is_dummy:
      return None                        # 假请求无真实态，跳过状态更新/输出
  ```
- **`has_work()` 只计需 NPU 的队列**：decode 的 `has_work()` **不得**把 CPU-only 的 prealloc / transfer（RDMA 等待）队列计入，只计 `waiting_queue` / `running_requests`。否则会产生紧循环的空 `forward_batch` 调用，**触发 HCCL AIV all-reduce 计数发散、在昇腾上 deadlock**：
  ```python
  def has_work(self) -> bool:
      # prealloc/transfer 是 CPU-only RDMA 等待，计入会造成紧循环 dummy forward
      # → HCCL AIV all-reduce 计数发散 → Ascend deadlock
      return bool(self.waiting_queue or self.running_requests)
  ```
- **队列推进走全组共识**：搬请求的 `pop_preallocated / pop_transferred` 用 `poll_and_all_reduce`（Gloo MIN）over `tp_cpu_group`，在 phase 协商**之前**、在**所有 rank** 上调用，使各 TP rank 锁步搬同一批请求——**不能 gate 在 is_dp_leader 上**（all-reduce 需全组参与）。

约束：这套落点在 cann-recipes-infer executor 的 base `Scheduler` 与 `DecodeDisaggScheduler`，且依赖 online 的 Gloo CPU 通信域（其启动前置见 [online-gloo-cpu-comm-domain-env-bringup](../../optimizations/rules/online_gloo_cpu_comm_domain_env_bringup.md)）。单 rank 时 `tp_cpu_group=None`、all-reduce 退化 no-op，dummy 机制仍安全。

## 参考实现二：动态-shape 序列并行——收集各 rank 长度的 all_gather 绝不按本地 size 缓存

各 rank 本地 `seq_len` 合法可不等的动态-shape [Ulysses](../../concepts/parallelism/ulysses.md)（UAA）里，`all_to_all_single` 前要先用一次 `all_gather` 收集各 rank 实际长度。这个 `all_gather` **不得按「本地 size」缓存**：本地 size 在不同 rank 上不同 → 各 rank 的缓存命中 / 未命中态随时间发散 → 命中的 rank 跳过 `all_gather`、未命中的进入 → 参与方不匹配 → 进程组挂死（常在稍后以 Ulysses 的 `ALLTOALL` 超时暴露）。因此该收集函数**每步实时调用、刻意不缓存**：

```python
def _gather_size_by_comm(size, group):
    # 动态-shape 下 size 各 rank 合法可不同；按本地 size 缓存会让命中态跨 rank 发散
    # → 部分 rank skip all_gather、部分 enter → 参与方不匹配 → 挂死（后续常以 ALLTOALL 超时暴露）
    ...
    dist.all_gather(gathered_sizes, torch.tensor([size], device="npu", dtype=torch.int64), group=group)
    return [s[0].item() for s in gathered_sizes]
```

约束：落点在 `module/unified_sp`（UAA / Ulysses-Anything）。**标准（等分）Ulysses 各 rank size 恒等、不触发**此风险；只有各 rank 本地形状合法可不等的动态-shape 序列并行才需要这条纪律。UAA 的 head/序列整除与 pad 机制另见 [ulysses-head-seq-divisibility-uaa](ulysses_head_seq_divisibility_uaa.md)。

## 相关经验

- 多机 / 多进程 DP+EP MoE 的另一套集合通信一致性落法（全局 phase 协调 + dummy 参与 + 变长换定长）：[multimachine-dp-ep-moe-collective-alignment](../../optimizations/rules/multimachine_dp_ep_moe_collective_alignment.md)。
- HCCL AIV 算子展开与 prefill micro-batch 双流的互斥（同涉 AIV all-reduce）：[hccl-aiv-expansion-vs-prefill-micro-batch](../../optimizations/rules/hccl_aiv_expansion_vs_prefill_micro_batch.md)。
- 集合通信 timeout 若是**某 rank 崩了**（而非设计上跳过）导致的缺席，诊断入口见 [hccl-timeout-secondary-to-rank-failure-oom](hccl_timeout_secondary_to_rank_failure_oom.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/315)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/325)（evidence）
