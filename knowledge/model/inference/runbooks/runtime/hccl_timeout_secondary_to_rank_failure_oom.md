---
type: Runbook
title: 多卡 HcclAllGather 超时 / Get_Socket_Timeout 常是次生症状：先查全部 rank 日志找真实故障（多为另一 rank OOM）
description: Get_Socket_Timeout / connect timeout 给出的三条「可能原因」（远端未发起 connect、算子启动过晚、链路断开）会把人引向网络排查——但 hccn_tool -i $devid -tls -g 检查各卡 TLS / 网络往往全部正常。
tags:
- task.debugging
- topic.parallelism
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a3
---

# 多卡 HcclAllGather 超时 / Get_Socket_Timeout 常是次生症状：先查全部 rank 日志找真实故障（多为另一 rank OOM）

## 信号

多卡 NPU 部署跑挂，rank0 的顶层栈只看到集合通信超时，形如：

```
RuntimeError: ... current working operator name is HcclAllGather.
Since the operator is called asynchronously, the stacktrace may be inaccurate. ...
Get_Socket_Timeout(EI0006): Getting socket times out. Reason:
  1. The remote does not initiate a connect request. some NPUs in the cluster are abnormal. ...
```

`Get_Socket_Timeout` / connect timeout 给出的三条「可能原因」（远端未发起 connect、算子启动过晚、链路断开）会把人引向**网络排查**——但 `hccn_tool -i $devid -tls -g` 检查各卡 TLS / 网络往往全部正常。

## 触发条件

多卡（含单卡双芯 → world_size 翻倍）分布式推理，挂点落在某个集合通信算子（`HcclAllGather` / all-reduce 等）。集合通信算子**异步下发**，报错栈本身就声明「stacktrace may be inaccurate」——rank0 看到的超时点不是真实故障点。

## 根因

真正的故障几乎总在**另一个 rank**：某 rank 因**显存耗尽**（或其它非通信类硬错误）在到达该集合通信点之前挂死 / 退出 → 集合通信在其余 rank 上永远凑不齐 → rank0 表现为 socket / connect 超时。这是[「集合通信缺席方 → 全组挂死」](../runtime/collective_participation_per_rank_consistency.md)的一个实例，区别在于缺席不是设计上跳过、而是那个 rank **崩了**。典型现场（其它 rank 日志里才有的真实错误）：

```
[rank15] Memory_Allocation_Failure(EL0004): Failed to allocate memory.
         Failed to allocate resource[DeviceMemory] with info [size:420478976]. Reason: Memory resources are exhausted.
[rank4]  RuntimeError: ... OPS function error: HcclAllGather, error code is 6
         Memory_Allocation_Failure(EL0004): ... malloc physical memory failed, runtime result = 207001
```

## 修法（诊断流程）

1. **不要停留在 rank0 的异步 timeout 栈**。遇到 `HcclAllGather` 超时 / `EI0006 Get_Socket_Timeout`，先 **grep 全部 rank 的日志**，找**最早的、非通信类**的真实错误（此处是 `EL0004 Memory_Allocation_Failure`）。
2. 网络自检（`hccn_tool ... -tls`）全正常反而是**「超时是次生、根因在别处」**的佐证，不是要继续查网络的信号。
3. 需要精确定位真实下发点时，用 `ASCEND_LAUNCH_BLOCKING=1` 强制集合通信同步下发（会拖慢性能，**定位后需取消**）。
4. 根因确认为显存不足后，走内存缓解手段——如单机 W8A8C8 下增大 `oproj_tp_size` / `dense_tp_size` 把重投影权重进一步分片，见 [local-tp-memory-heavy-projections](../../optimizations/experience/rules/local_tp_memory_heavy_projections.md)。

## 参考实现 / 观测场景

观测于 [DeepSeek-V3.2-Exp](../../concepts/modules/dsa.md) [W8A8C8](../../concepts/quantization/w8a8c8.md)、单节点 8 卡 [Atlas A3](../../concepts/platforms/atlas_a3.md)（单卡双芯 → world_size=16）、`exe_mode: eager` 的 prefill（`cp_size: 16`）；挂点在 attention prefill 的 `indexer.prefill_decode_ascendc`（[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 内的 `all_gather_into_tensor`）与 [mla-prolog](../../concepts/kernels/mla_prolog.md) 的 `mlaprolog_prefill`（`all_gather_into_tensor(kv_all, ...)`）。这些是该现场的落点；「集合通信超时须回查全 rank 日志、警惕另一 rank 硬错误」的诊断纪律对任何多卡昇腾集合通信挂死通用。

## Evidence

- `多 rank 日志 + 维护者确认`：事件页给出 rank0（`HcclAllGather` / `EI0006`）、rank4、rank15（均 `EL0004`）多 rank 日志并存、报告者自查各卡 TLS / 网络正常；维护者答复即要求「检查所有 rank 日志里是否有其他报错」。「异步栈不准」为 HCCL 报文本身声明。
- `diff 事实`（@2c45117）：`indexer.py:prefill_decode_ascendc`（含 `dist.all_gather_into_tensor`）与 `modeling_deepseek.py:mlaprolog_prefill` 的代码路径与栈一致。
- 溯源下探：[cann-recipes-infer-issue-54-bug-report-deepseek-v3-2-exp-w8a8c8-8p-16](https://gitcode.com/cann/cann-recipes-infer/issues/54)

<!-- cannbot:related:start -->
## 相关

- [Attention-DP + MoE-EP 部署：对访存 / 内存重的投影层（O_proj / LM_Head / Embedding / dense）单独局部 TP](../../optimizations/experience/rules/local_tp_memory_heavy_projections.md)（`related`）：“根因确认为显存不足后，走内存缓解手段”把 HCCL 次生超时收敛到 OOM 处置；“`oproj_tp_size` 与 `dense_tp_size` 增大”给出单节点 W8A8C8 场景下分片重投影和 dense 权重的具体调参。
- [集合通信参与方逐 rank 对齐：按本地状态决定「是否进入集合通信」导致发散型挂死/超时](collective_participation_per_rank_consistency.md)（`related`）：“集合通信在其余 rank 上永远凑不齐”描述 rank 崩溃造成的缺席，“集合通信参与方逐 rank 对齐”给出集合通信为何因此挂死的统一正确性约束。
<!-- cannbot:related:end -->
