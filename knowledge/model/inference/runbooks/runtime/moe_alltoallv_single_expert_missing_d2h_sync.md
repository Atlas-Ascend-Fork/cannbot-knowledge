---
type: Runbook
title: 单专家 alltoall-v 缺同步屏障：非阻塞 D2H 搬回的 split 尺寸未就绪即被异步集合通信消费
description: MoE Expert-Parallel 的 alltoall-v token 分发器（MoEAlltoAllvTokenDispatcher）在单专家配置（num_local_experts == 1）下出现收发分片尺寸错误、通信结果错乱或集合通信挂死，多专家配置正常。根因：input_splits/output_splits（每专家 token 数）用 .to(cpu, non_blocking=True).numpy() 非阻塞 D2H 从 NPU 搬回 host，随后被 host 侧消费的 async_all_to_all 读取，但两者之间无显式同步屏障；正确性原本依赖 num_local_experts > 1 分支里 torch.repeat_interleave 隐含 D2H 读带来的偶然隐式同步，单专家分支跳过 repeat_interleave 后该屏障消失，async_all_to_all 读到未就绪的 split host 数组。修法：在 _preprocess 的 else 分支补一次 torch.npu.synchronize() 全设备/全流同步，确保非阻塞 D2H 落地再进集合通信；代价是全同步 stall CPU、有性能开销（维护者留 TODO），更细粒度做法是把这几个 split 改成阻塞 D2H 或只等其 event。可迁移 hazard：用非阻塞 D2H 搬回控制面数据再喂 host 侧异步集合通信时，中间必须有保证同步的屏障，不能依赖某条 op 的隐式同步副作用（随分支存在与否而消失）。涉及昇腾 NPU stream 异步 D2H 拷贝语义、torch.npu.synchronize 流同步屏障、MoE alltoall-v dispatch/combine 的 host 侧 split 消费。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3005
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 单专家 alltoall-v 缺同步屏障：非阻塞 D2H 搬回的 split 尺寸未就绪即被异步集合通信消费

## 信号（现象）

MoE Expert-Parallel 的 alltoall-v token 分发/合并器（`MoEAlltoAllvTokenDispatcher` 类），**只在单专家配置下**（每 rank 本地专家数 `num_local_experts == 1`，例如 EP 切分后每卡只落一个 local expert）出现收发分片尺寸错误——`async_all_to_all` 按 `input_splits`/`output_splits` 决定各 rank 收发多少 token，读到的却是**未就绪/陈旧的 host 数组**。其后果是集合通信按未就绪/陈旧的 split 收发，收发分片尺寸与真实不符（原理上可能进而导致结果错乱或集合通信异常，具体运行时症状取决于负载）；同一份代码在多专家（`num_local_experts > 1`）下正常，切到单专家才暴露。若你观测到「只有单专家 EP 布局的 MoE alltoall-v 出错、多专家不出错」，本页命中；若是多专家路径出错，根因不在此。

## 触发条件

- 分发器把 alltoall-v 的 split 尺寸（每专家 token 数）用**非阻塞 D2H 拷贝**从 NPU 搬回 host：`x.to(torch.device("cpu"), non_blocking=True).numpy()`。该拷贝在 NPU stream 上入队，主机侧不等待完成即返回。
- 这些 host numpy 数组随后被 **host 侧消费的异步集合通信**读取（`async_all_to_all(hidden_states, input_splits, output_splits, ep_group)` 在 host 侧读 split 决定收发分片大小）。
- **两次读取之间没有任何显式同步屏障**，代码原本靠一个偶然命中的 op 副作用来隐式同步——而那个 op 只在某条分支存在。
- 单专家分支（`num_local_experts == 1`）恰好绕过了那个带隐式同步的 op，屏障随之消失。

split 尺寸这样算并异步搬回 host：

```python
self.input_splits = (num_local_tokens_per_expert.reshape(
    ep_size, self.num_local_experts).sum(axis=1).to(
    torch.device("cpu"), non_blocking=True).numpy())
...
self.output_splits = (self.num_global_tokens_per_local_expert.sum(
    axis=-1).to(torch.device("cpu"), non_blocking=True).numpy())
```

随后喂给集合通信：

```python
_, permutated_local_input_tokens, handle = async_all_to_all(
    hidden_states, self.input_splits, self.output_splits, self.ep_group)
```

## 根因

`input_splits`/`output_splits` 是 `non_blocking=True` 异步搬回 host 的——`async_all_to_all` 在 host 侧读它们时，这些 D2H 拷贝**不保证已完成**。原代码从未显式为它们插同步屏障，正确性依赖一次**偶然的隐式同步**：

- `num_local_experts > 1` 分支里调用 `torch.repeat_interleave(expert_ids_per_ep_rank, num_global_tokens_per_local_expert.ravel())`——`repeat_interleave` 需在 host 侧知道 `ravel()` 出来的重复次数，隐含一次 D2H 读，从而**顺带把前面所有非阻塞 D2H 拷贝也强制同步完成**。这是「意外正确」：屏障不是有意加的，是这条 op 的副作用。
- `num_local_experts == 1` 时不需要构造 `global_input_tokens_local_experts_indices`，代码**跳过整个 `repeat_interleave`**、落到原本为空的 else 路径——那个偶然的隐式同步随之消失。此时非阻塞 D2H 的 split 可能尚未完成，`async_all_to_all` 就读到未就绪 host 内存，收发分片尺寸错误，且仅在单专家配置暴露。

一句话根因：**丢失了原本靠 `repeat_interleave` 副作用得到的同步屏障**，不是 `async_all_to_all` 或非阻塞拷贝本身有错。

> 可迁移的 hazard（拿掉仓/PR 仍成立）：用非阻塞 D2H 把**控制面数据**（如 split 尺寸）搬回 host、再喂给 host 侧消费的异步集合通信时，若中间没有强制同步的 op、而某分支只是碰巧命中了带隐式同步的 op，则**不命中隐式同步的那条分支会静默读到未就绪 host 数据**。这是 NPU 异步拷贝 + host 消费型集合通信的固有 hazard，凡写 NPU MoE/EP 分发器都可能撞上。审查点：任何 `.to(cpu, non_blocking=True)` 出来的值，在被 host 侧读之前，链路上必须有一个**保证同步**的屏障，而不能依赖某条 op 的隐式同步副作用（因为它随分支存在与否而消失）。

## 修法

在 `_preprocess` 的 else（`num_local_experts == 1`）分支补一次显式全流同步（改动仅 4 行）：

```python
        if self.num_local_experts > 1:
            ...
            self.global_input_tokens_local_experts_indices = torch.repeat_interleave(
                self.expert_ids_per_ep_rank,
                self.num_global_tokens_per_local_expert.ravel())
+        else:
+            # TODO: This full synchronization can be a performance bottleneck.
+            # A more granular sync (e.g., blocking D2H copies) should be investigated.
+            torch.npu.synchronize()

        return num_tokens_per_local_expert
```

`torch.npu.synchronize()` 是**全设备/全流**同步：阻塞主机线程直到 NPU 上所有已入队 kernel 完成，从而保证 `input_splits`/`output_splits` 的非阻塞 D2H 已落地再进 `async_all_to_all`。

**代价与更细粒度做法**：`torch.npu.synchronize()` 是**重量级全同步**，会 stall CPU 到全部 kernel 完成——它正确修复了竞态但引入性能开销，故随修法留下 TODO。更细粒度、性能更好的做法是**只等这几个 split 拷贝**：把它们的 D2H 改成**阻塞拷贝**（`non_blocking=False`），或只等这几个拷贝的 event，而非全流同步——作为后续优化留在 TODO，未在本修法落地。若要 backport 或复用此修法，优先考虑这种局部同步以免在热路径引入全流 stall。

## Evidence

- diff 事实（merge commit `05a700d3`，改动仅 4 行）：① `input_splits`/`output_splits` 以 `.to(cpu, non_blocking=True).numpy()` 异步搬回 host；② `repeat_interleave` 仅在 `num_local_experts > 1` 分支；③ 新增 else 分支即 `torch.npu.synchronize()`；④ `async_all_to_all(hidden_states, input_splits, output_splits, ep_group)` 在 host 侧消费这两个数组。
- 根因「丢失 `repeat_interleave` 的隐式同步」由 source 直接支撑（非本页推断）：单专家分支缺失 `repeat_interleave` 时原本靠其副作用得到的隐式同步屏障消失，`non_blocking=True` 拷贝可能在后续 `async_all_to_all` 使用前未完成。
- 无独立性能/精度数字（源未提供 before→after benchmark）；竞态在生产下的具体运行时症状串源未给，未并入事实面。
- 溯源下探 [vllm-ascend-pr-3005-bugfix-fix-async-copy-bug-under-single-expert-scenario](https://github.com/vllm-project/vllm-ascend/pull/3005)

## 关联

- 场景概念：[expert-parallel](../../concepts/parallelism/expert_parallel.md) · [moe-dispatch-combine-v2](../../concepts/techniques/moe_dispatch_combine_v2.md)

<!-- cannbot:related:start -->
## 相关

- [MoE 通信掩盖（Dispatch 调度 + AllToAll/AllGather Overlap + 前反向跨 MicroBatch 掩盖）](../../../training/concepts/techniques/moe_comm_overlap.md)（`related`）：`num_local_experts == 1` 时不需要构造 `global_input_tokens_local_experts_indices`，代码**跳过整个 `repeat_interleave`**；代价是要从 device 取回每专家 token 数（一次 device→host 同步）；前者说明单专家分支为何丢失 split 搬回的偶然屏障，后者说明 alltoall dispatcher 消费每专家 token 数时本来就跨越 device→host 控制面，二者共同定位 split 在集合通信前必须就绪。
<!-- cannbot:related:end -->
