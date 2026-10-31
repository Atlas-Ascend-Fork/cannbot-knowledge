---
type: Runbook
title: 多卡 HcclAllGather / Get_Socket_Timeout 排查：核对全部 rank 的故障与通信状态
description: Get_Socket_Timeout / connect timeout 给出的三条「可能原因」（远端未发起 connect、算子启动过晚、链路断开）会把人引向网络排查——但 hccn_tool -i $devid -tls -g 本来源现场检查各卡 TLS / 网络为正常，不能据此判断其他故障现场也正常。
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
updated_at: '2026-10-29T15:29:20Z'
platforms:
- a3
---

# 多卡 HcclAllGather / Get_Socket_Timeout 排查：核对全部 rank 的故障与通信状态

## 信号

多卡 NPU 部署跑挂，rank0 的顶层栈只看到集合通信超时，形如：

```
RuntimeError: ... current working operator name is HcclAllGather.
Since the operator is called asynchronously, the stacktrace may be inaccurate. ...
Get_Socket_Timeout(EI0006): Getting socket times out. Reason:
  1. The remote does not initiate a connect request. some NPUs in the cluster are abnormal. ...
```

`Get_Socket_Timeout` / connect timeout 给出的三条「可能原因」（远端未发起 connect、算子启动过晚、链路断开）会把人引向**网络排查**——但 `hccn_tool -i $devid -tls -g` 本来源现场检查各卡 TLS / 网络为正常，不能据此判断其他故障现场也正常。

## 触发条件

多卡（含单卡双芯 → world_size 翻倍）分布式推理，挂点落在某个集合通信算子（`HcclAllGather` / all-reduce 等）。集合通信算子**异步下发**，报错栈本身就声明「stacktrace may be inaccurate」——rank0 看到的超时点可能不是真实故障点，须沿全部 rank 日志确认。

## 根因

本现场在其他 rank 找到了显存耗尽错误：某 rank 在到达集合通信前失败，可能使其他 rank 因参与方缺席而超时。这是[集合通信参与一致性](collective_participation_per_rank_consistency.md)的一种故障路径，不是超时根因的发生比例统计；若无对应硬错误，仍需排查通信、网络、算子启动和同步。现场错误如下：

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
4. 根因确认为显存不足后，走内存缓解手段——如单机 W8A8C8 下增大 `oproj_tp_size` / `dense_tp_size` 把重投影权重进一步分片，见 [local-tp-memory-heavy-projections](../../optimizations/rules/local_tp_memory_heavy_projections.md)。

## 参考实现 / 观测场景

观测于 [DeepSeek-V3.2-Exp](../../concepts/modules/dsa.md) [W8A8C8](../../concepts/quantization/w8a8c8.md)、单节点 8 卡 [Atlas A3](../../concepts/platforms/atlas_a3.md)（单卡双芯 → world_size=16）、`exe_mode: eager` 的 prefill（`cp_size: 16`）；挂点在 attention prefill 的 `indexer.prefill_decode_ascendc`（[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 内的 `all_gather_into_tensor`）与 [mla-prolog](../../concepts/kernels/mla_prolog.md) 的 `mlaprolog_prefill`（`all_gather_into_tensor(kv_all, ...)`）。这些是该现场的落点；「集合通信超时须回查全 rank 日志、警惕另一 rank 硬错误」的诊断纪律对任何多卡昇腾集合通信挂死通用。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/54)（evidence）
