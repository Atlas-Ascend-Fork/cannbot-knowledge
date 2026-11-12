---
type: Runbook
title: 多卡 HcclAllGather / Get_Socket_Timeout 排查：核对全部 rank 的故障与通信状态
description: HCCL timeout 或卡住时，核对全部 rank 首错、OOM、未到达和残留进程占用；区分网络、同步与设备资源，并检查 Gloo 调试屏障边界。
tags:
- task.debugging
- topic.parallelism
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
- resource: https://docs.pytorch.org/docs/2.8/distributed.html#torch.distributed.monitored_barrier
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-11-10T01:48:58Z'
platforms:
- a3
aliases:
- HCCL timeout 与 rank 首错
- 其他 rank OOM 导致通信超时
- monitored_barrier
- 异步同步点与 rank 检查点
- 残留进程 HCCL
- HCCL 卡住
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
2. 网络自检（`hccn_tool ... -tls`）正常，只能支持本次自检范围；结合其他 rank 的 OOM 等首错判断超时是否次生。没有对应硬错误时仍保留网络、链路和通信配置假设，不能凭一次 TLS 检查排除网络。
3. 需要精确定位真实下发点时，用 `ASCEND_LAUNCH_BLOCKING=1` 强制集合通信同步下发（会拖慢性能，**定位后需取消**）。
4. 根因确认为显存不足后，走内存缓解手段——如单机 W8A8C8 下增大 `oproj_tp_size` / `dense_tp_size` 把重投影权重进一步分片，见 [local-tp-memory-heavy-projections](../../optimizations/rules/local_tp_memory_heavy_projections.md)。

## 同步检查点与 host 侧屏障

NPU 操作异步下发，forward 返回或在 synchronize 处报错，不等于错误由该行算子引入。先按 Prefill/Decode、层、模块逐步放少量 `torch.npu.synchronize()` 检查点，并比较所有 rank 的日志；同步会扰动时序，不能一次插满。

已有 rank 失败时直接加 dist.barrier 可能使其他 rank 继续等待。PyTorch 2.8 的 `torch.distributed.monitored_barrier` 提供 host 侧超时与未到达 rank 报告，但仅支持 GLOO 后端；需要匹配的 Gloo 调试组，不能在 HCCL 组上照搬调用，也不证明 NPU stream 上的任务已经全部完成。调试结束恢复正常同步路径，保留首错和参与顺序证据。

无明确报错时先对齐任务启动器、PID/rank 和 npu-smi 状态。部分 rank 进程缺失、HBM 不均要回查对应加载日志；进程存在但 CPU 低且 HBM 不变也可能在等 I/O 或同步，不能仅凭这一项认定死锁。旧材料的8进程、3GB HBM只是示例，不是所有拓扑的固定判据。

残留任务进程可能占用设备或通信资源，清理前先把 PID/进程所属任务与本次运行对应；不照搬按用户名批量 kill 的命令。重新启动后复查参与 rank 和通信顺序，不能把清理后能启动当成已定位全部根因。

## 参考实现 / 观测场景

观测于 [DeepSeek-V3.2-Exp](../../concepts/modules/dsa.md) [W8A8C8](../../concepts/quantization/w8a8c8.md)、单节点 8 卡 [Atlas A3](../../concepts/platforms/atlas_a3.md)（单卡双芯 → world_size=16）、`exe_mode: eager` 的 prefill（`cp_size: 16`）；挂点在 attention prefill 的 `indexer.prefill_decode_ascendc`（[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 内的 `all_gather_into_tensor`）与 [mla-prolog](../../concepts/kernels/mla_prolog.md) 的 `mlaprolog_prefill`（`all_gather_into_tensor(kv_all, ...)`）。这些是该现场的落点；「集合通信超时须回查全 rank 日志、警惕另一 rank 硬错误」的诊断纪律对任何多卡昇腾集合通信挂死通用。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/54)（evidence）

- [https://docs.pytorch.org/docs/2.8/distributed.html#torch.distributed.monitored_barrier](https://docs.pytorch.org/docs/2.8/distributed.html#torch.distributed.monitored_barrier)（supporting）

- [.agents/skills/model-infer-runtime-debug/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md)（supporting）
