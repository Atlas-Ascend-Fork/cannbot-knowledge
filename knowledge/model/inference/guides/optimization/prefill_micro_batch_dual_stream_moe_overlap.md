---
type: Guide
title: Prefill 用 micro-batch 双流把 MoE dispatch/combine 通信藏进计算
description: Prefill 用 micro-batch 双流把 MoE dispatch/combine 通信藏进计算。大 EP MoE 模型 prefill：整体是计算
  bound，但 MoE 的 dispatch/combine 两段 AllToAll 通信仍占一定比例（本仓一手优化文档称 prefill 通信耗时占比可达约
  30%）。计算与通信由不同硬件单元完成、可并行——把它们错开就能用计算掩盖通信、把 prefill 推向纯计算 bound。 拓扑：MLA 走 DP 切分、MoE
  走 EP 切分（DP+EP），或更一般的「EP + 可切 micro-batch」场景。 目标：用一路的计算穿插另一 micro-batch 的通信，隐藏 MoE
  EP 的通信空洞。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/72
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/17
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/351
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek_r1/models/modeling_deepseek.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/utils/stream_utils.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:38:03Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - throughput
---
# Prefill 用 micro-batch 双流把 MoE dispatch/combine 通信藏进计算

## 适用场景

大 [EP](../../concepts/parallelism/expert_parallel.md) MoE 模型 prefill：整体是计算 bound，但 MoE 的 dispatch/combine 两段 AllToAll 通信仍占一定比例（本仓一手优化文档称 prefill 通信耗时占比可达约 30%）。计算与通信由不同硬件单元完成、可并行——把它们错开就能用计算掩盖通信、把 prefill 推向纯计算 bound。

- 拓扑：MLA 走 [DP](../../concepts/parallelism/data_parallel.md) 切分、MoE 走 EP 切分（DP+EP），或更一般的「EP + 可切 micro-batch」场景。
- 目标：用一路的计算穿插另一 micro-batch 的通信，隐藏 MoE EP 的通信空洞。

## 问题信号

prefill 时芯片在等 MoE 跨卡 dispatch/combine 通信、或等计算，交替出现空洞；profiler 上 AllToAll 段与计算段串行、互不重叠。

## 何时不适用 / 前置条件（先确认，否则劣化）

1. **计算/通信线性度要好**：切分前的计算（或通信）性能 ≈ 切分后两份之和。否则单次 shape 变小导致算子性能劣化，收益被吃掉。
2. **不能已是 host bound**：模型本就 host bound 时，双流反而加剧 host 压力（eager 模式下 task 下发数翻倍），整体更慢。
3. **通信后端要退回 SDMA**：micro-batch 双流开启时不要设 `HCCL_OP_EXPANSION_MODE=AIV`——AIV 借 Vector Core 加速通信会与并行计算抢硬件资源、时延反增，须用默认 SDMA。详见 [hccl-aiv-expansion-vs-prefill-micro-batch](../../optimizations/rules/hccl_aiv_expansion_vs_prefill_micro_batch.md)。

## 做什么（手段）

把每层 prefill 计算划成 6 段：`atten`（MLA + o_proj）、`init_routing`、`dispatch`（token 分发 AllToAll）、`mlp`（路由专家 + 共享专家）、`combine`（token 回收 AllToAll）、`finalize_routing`。核心是让一路的计算与另一 micro-batch 的 dispatch/combine 通信重叠。

- **拆分**：每卡输入拆成 2 个 micro-batch（如每卡 2 个 4K 请求 → 每 micro-batch 处理 1 个 4K），两个 micro-batch 都算完即完成本层。
- **建流**：计算放默认（主）流、通信放新建副流；两个 micro-batch 的输入准备和计算均在主流，副流提交 dispatch/combine 通信。

```python
curr_stream = torch.npu.current_stream()
self.stream1 = torch.npu.Stream()          # MicroBatchMode != DISABLE 时建
with torch.npu.stream(curr_stream):
    atten()          # 一个 micro-batch 的计算走主流
with torch.npu.stream(self.stream1):
    dispatch()       # 另一 micro-batch 的 AllToAll 走副流
```

- **事件流水**：用 `record_event`/`wait_event` 把 dispatch/expert/combine 阶段跨流编排，让上一轮 combine/finalize 与下一轮 atten 交错掩盖。

```python
event_routing_dispatch_mb0 = curr_stream.record_event()
with torch.npu.stream(self.stream1):
    self.stream1.wait_event(event_routing_dispatch_mb0)
    ... = forward_dispatch_double_routing(...)        # 副流做 mb0 的 dispatch
    event_dispatch_expert_mb0 = self.stream1.record_event()
curr_stream.wait_event(event_dispatch_expert_mb0)
new_x_mb0 = forward_expert(...)                       # 主流做 mb0 的 expert
```

重点是多阶段事件的排列顺序，而非「简单开两条流」。dispatch 走的跨卡分发即 [double-routing](../../concepts/techniques/double_routing.md) AllToAll（prefill EP 分发骨架见 [moe-ep-double-routing-skeleton](../../optimizations/rules/moe_ep_double_routing_skeleton.md)）。图模式下的跨流同步 API 与 eager 不同、不可混写（ge_graph 控制边 vs aclgraph tagged-event），见 [graph-mode-multi-stream-cross-stream-sync-api](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)。

## 使能开关（参考实现）

固定 `2c45117` 里 Prefill 微批分支由 `micro_batch_mode`（≠0）选择，独立于 `enable_multi_streams`；参考落点 `prefill_r1_rank_32_32dp_32ep_a8w8.yaml` 内 `micro_batch_mode: 1`、`enable_multi_streams: True`。

## correctness 验证

event 顺序稍错就会死等 / 早读 / 精度异常——先验证功能与精度（与单流逐 token 对齐），再看 overlap 收益。参考落地报告 128 token 输出与基线逐字一致（仓自报）。

## benchmark（参考配置下的仓自报，无独立复测）

该组A3数据与物理卡/并行单位集中到[R1 Prefill 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)；来源自报不能证明其他负载均有净收益，通信是否真正被掩盖需读取实际timeline。

## 风险 / rollback

- shape 切半后若算子性能显著劣化，双流收益变差甚至负收益。
- host bound 模型上双流加剧劣化；event 顺序错会死等 / 精度异常。
- rollback：将 `micro_batch_mode` 设为 0 才退出该 Prefill 微批双流分支；`enable_multi_streams: False` 不能替代它，该开关控制其他独立多流路径。

## 参考实现及其约束

参考 cann-recipes-infer 的 [DeepSeek-R1](../../concepts/models/deepseek_r1.md)（[Kimi-K2-Thinking](../../concepts/models/kimi_k2_thinking.md) 为同架构思路的独立副本，需按自己的入口核对）prefill 与 `model-infer-multi-stream` skill。6 段划分、DP+EP 的「计算全放主流 / 通信放副流」排布是该实现落点；SP-TP-EP 与 DP-EP 可能采用不同流水版本。micro-batch 与 MTP 投机解码共存时的记账另有坑，见 [mtp-cache-and-microbatch-prefill-bookkeeping](../../optimizations/rules/mtp_cache_and_microbatch_prefill_bookkeeping.md)。技术思想（用计算掩盖 EP 通信）可迁移到其它 EP + micro-batch 结构，具体流事件编排随模型算子链而定。

## 相关经验

- 另见 [Prefill MLA 并行选型：大请求量走纯 DP、少 / 长请求走 SP-TP-SP（RS+AG 保持层间序列切分）](../../optimizations/rules/prefill_mla_dp_vs_sp_tp_sp_parallel.md)。


## Evidence

- `diff 事实`（@f5bf59cf）：`modeling_deepseek.py` 的 `MicroBatchMode`、`self.stream1 = torch.npu.Stream()`、`record_event`/`wait_event` 双流流水；config `micro_batch_mode: 1` + `enable_multi_streams: True`。溯源下探 [cann-recipes-infer-pr-72-feat-add-deepseek-r1-kimi-k2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/72)。
- `diff 事实`（@2c45117）+ `doc 披露`：micro_batch 双流分支与 `deepseek_r1_prefill_optimization.md` 的 6 段划分、前后性能对照表、30% 通信占比、「micro-batch 时禁 AIV」。溯源下探 [cann-recipes-infer-issue-17-rfc-deepseek-r1-kimi-k2-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/17)。
- `diff 事实`（@d739fecb4232）：`model-infer-multi-stream` skill 的 `prefill-microbatch-dual-stream` 示例（`torch.npu.Stream`/`record_event`/`wait_event`/`forward_dispatch_double_routing`）。溯源下探 [cann-recipes-infer-pr-351-feat-update-agent-skills-with-full-optimization-pipeline-and-role-based](https://gitcode.com/cann/cann-recipes-infer/merge_requests/351)。
- benchmark 与前置条件为仓自报、无独立复测；双流 + 2 micro-batch + event 同步机制为读到的 diff 事实。

## 验收与停止条件

保存未切分 Prefill 的精度、吞吐和峰值内存；启用对应 micro-batch 模式后检查请求切分、六阶段事件顺序与通信后端。覆盖不足两个请求和正常切分分支；输出不对齐、切分后算子效率下降或吞吐无净收益时关闭该模式。


## 固定 R1 的逐事件实现补充

以下节选固定提交 `2c45117` 的 R1 实现，说明该模型的事件顺序；迁移到其他模型时需重新检查流水依赖。

Prefill micro-batch 入口在 `forward`（`models/deepseek_r1/models/modeling_deepseek.py:1632-1641`）按 `micro_batch_mode` 选分支；构造函数在 `:1597-1598` 创建副流：

```python
# modeling_deepseek.py:1597-1598
self.micro_batch_mode = MicroBatchMode(...)   # :1596
if self.micro_batch_mode != MicroBatchMode.DISABLE:
    self.stream1 = torch.npu.Stream()
```

流水主体用 **显式 Stream + 逐事件 record/wait**（`forward_microbatch_v1` `:2018-2195`，下为 `:2127-2161` 节选）：

```python
cur_stream = torch.npu.current_stream()                 # :2026
...
event_routing_dispatch_mb0 = cur_stream.record_event()  # :2127
...
with torch.npu.stream(self.stream1):                    # :2151
    self.stream1.wait_event(event_routing_dispatch_mb0)
    ... = decode_layer.forward_dispatch_double_routing(...)  # mb0 dispatch
    event_dispatch_expert_mb0 = self.stream1.record_event()  # :2156
cur_stream.wait_event(event_dispatch_expert_mb0)        # :2158
new_x_mb0 = decode_layer.forward_expert(...)            # mb0 expert :2159
event_expert_combine_mb0 = cur_stream.record_event()    # :2161
```

收尾用 `cur_stream.wait_stream(self.stream1)` + `self.stream1.wait_stream(cur_stream)` 双向对齐两条流（`:2194-2195`）。

### 与 Decode 事件辅助函数的区别

同一固定版本另有 `record_event(enable_npugraphex_and_multistream, self.npu_events, idx)` 辅助函数，定义见 `executor/utils/stream_utils.py:46-60`。它封装普通 `torch.npu.Event` 的 `events[idx].record()` / `.wait()`，在 R1 中受 `and not is_prefill` 门控，服务于 Decode shared-expert overlap。该路径不等于本节的 Prefill 显式双流，也不能据此把 tagged-event API 用法套入 Prefill。

### 模式与流水入口

`forward` 显式映射 `PREFILL_MICRO_BATCH_DP_EP`（1）到 `forward_microbatch_v1`、`PREFILL_MICRO_BATCH_SP_TP_EP`（2）到 `forward_microbatch_v2`。固定 `2f82d10` 与 `2c45117` 的映射相同。`prefill_r1_rank_32_32dp_32ep_a8w8.yaml` 配置 `micro_batch_mode: 1`、`attn_tp_size: 1` 和 `moe_tp_size: 1`，使用 v1；应按枚举和调用分支判断，不能按函数在文件中的排列顺序判断。
