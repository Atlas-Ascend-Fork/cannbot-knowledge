---
type: "Runbook"
title: "探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代"
description: "DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。"
tags: ["task.debugging", "topic.implementation.synchronization", "topic.implementation.pipeline"]
status: stable
sources: []
created_at: "2026-08-15T10:30:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代

## 适用场景

- 工程形态：Kernel 直调（ops-direct-invoke），Python/aclrt 调 `.so` kernel，用 NPU event 或 msprof/TTK CST_PERF 计时。
- API 路径：`PipeBarrier<PIPE_MTE2|PIPE_MTE3>`；`GetTPipePtr()->FetchEventID(HardEvent::MTE2_S|MTE3_S)`；`SetFlag`/`WaitFlag`；Host 侧 `aclrtSynchronizeStream`。
- 验证过的平台与 CANN 版本：Ascend950PR；CANN 9.1.0。
- 适用粒度：operator_family（所有 DMA 带宽探针 / 需精确计量 MTE2/MTE3 搬运完成时机的 kernel）。
- 路线优先级：recommended_fastpath（末尾保留 `PipeBarrier<PIPE_MTE*>` + `MTE2_S/MTE3_S` SetFlag/WaitFlag 作为正确性同步；不要为压开销去掉它）。
- 不适用或未验证场景：aclnn op_host 流程下 stream sync 的语义未在本卡验证；仅覆盖 Kernel 直调带 NPU event/引擎级计时的带宽探针。

## 判别方法

触发（tool_observed）：在 GM→UB 纯读带宽探针 kernel（`DataCopy` 循环 + 末尾同步）上，为压同步开销去掉末尾 `PipeBarrier<PIPE_MTE2>` + `MTE2_S` 的 `SetFlag`/`WaitFlag`，改由 Host 侧 `aclrtSynchronizeStream` 兜底，用 NPU event best-of-5 计时后，小数据量带宽相对偏高约 1%。

探针：对同一 kernel 做"保留 vs 去掉末尾 `MTE2_S` 同步"A/B（小数据量 112MB + 大数据量 1.75GB，best-of-5 NPU event），恢复同步后另用 best-of-50 NPU event 与 TTK `CST_PERF` 交叉校验计时口径。

原始观测（verbatim 同步块，保留态，取自 `test/read_only/probe_read.asc`）：

```
    PipeBarrier<PIPE_MTE2>();
    event_t eventId = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
    SetFlag<HardEvent::MTE2_S>(eventId);
    WaitFlag<HardEvent::MTE2_S>(eventId);
}
```

去掉态（verbatim，edit 的 OLD→NEW，删去末尾同步块只剩 `}`）：

OLD:
```
    }

    event_t eventId = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
    SetFlag<HardEvent::MTE2_S>(eventId);
    WaitFlag<HardEvent::MTE2_S>(eventId);
}
```

NEW:
```
    }
}
```

写侧对称同步（verbatim，取自 `test/write_only/probe_write.asc`）：

```
    PipeBarrier<PIPE_MTE3>();
    event_t eventId = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE3_S));
    SetFlag<HardEvent::MTE3_S>(eventId);
    WaitFlag<HardEvent::MTE3_S>(eventId);
}
```

观测：去掉同步后小数据量 best-of-5 NPU event 带宽相对约 +1.1%（参考路线：保留末尾 MTE2_S/MTE3_S 同步），大数据量基本不变；恢复同步后 best-of-50 NPU event 与 TTK `CST_PERF` 仅差约 0.7%。

判别与解释（interpretation，agent 根因分析，非 API 规范主张）：`aclrtSynchronizeStream` 等待 stream 上所有任务完成，但 kernel 内 MTE2/MTE3 管线的 `DataCopy` 是异步发出的——Scalar 发出 DataCopy 描述符后即可退出 kernel。末尾若无 `PipeBarrier<PIPE_MTE*>` + `MTE2_S/MTE3_S` 的 `SetFlag`/`WaitFlag`，Scalar 可能在 MTE 管线 `DataCopy` 还没搬完时退出 kernel，使 stream sync 返回时部分搬运未完成，小数据量下带宽测得值虚高（相对差异约 1%）。该机制解释属 agent 推断，未单独验证"搬运未完成"的确定性数据证据。结论：保留末尾 `PipeBarrier<PIPE_MTE*>` + `MTE2_S/MTE3_S` 同步，改用引擎级计时采集纯 MTE 时间以获得精确带宽。

## 验证信号

来源：本 trace 在 Ascend950PR（CANN 9.1.0）上对 `test/read_only/probe_read.asc` 做"保留 vs 去掉末尾 `MTE2_S` 同步"A/B，用 NPU event best-of-5 计时；恢复同步后用 best-of-50 NPU event 与 TTK `CST_PERF` 交叉校验。

- 去掉末尾 `MTE2_S` 同步后，小数据量(112MB) best-of-5 NPU event 带宽相对约 +1.1%（参考路线：保留末尾 MTE2_S/MTE3_S 同步）；大数据量(1.75GB) 基本不变。（来源平台：950；证据等级：tool_observed）
- 恢复同步后 best-of-50 NPU event 与 TTK `CST_PERF` 仅差约 0.7%（参考路线：保留末尾 MTE2_S/MTE3_S 同步）。（来源平台：950；证据等级：tool_observed）

## 失效边界

- Ascend950PR / CANN 9.1.0 实测；仅覆盖 Kernel 直调带 NPU event/引擎级计时的带宽探针。
- aclnn op_host 框架下 `aclrtSynchronizeStream` 的语义未验证，推断可迁移（保留末尾同步的推荐路线应跨流程有效，但未在 op_host 流程实测）。
- "去掉同步导致搬运未完成"目前仅有带宽相对差异的间接证据，缺确定性数据校验。

## 坏实践

- 为压同步开销直接删末尾 `MTE2_S`/`MTE3_S` 的 `SetFlag`/`WaitFlag`，靠 `aclrtSynchronizeStream` 兜底——会测到未完成搬运，带宽虚高。该路线标记为 `banned`。

<!-- cannbot:related:start -->
## 相关

- [AscSyncMte2](../../apis/simd_api/c_api/sync/asc_sync_mte2.md)（`exemplifies`）：Runbook 用带宽探针验证 kernel 末尾必须等待 MTE2/MTE3 工作完成，host stream sync 不能替代 kernel 内流水同步；它补充了接口的测量与退出边界。
- [AscSyncMte3](../../apis/simd_api/c_api/sync/asc_sync_mte3.md)（`exemplifies`）：AscSyncMte3 与《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》的实质衔接是：AscSyncMte3 与 MTE2/Vector/pipe/barrier 配套，保证 MTE3 写出在消费者读取前完成。
- [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`exemplifies`）：The API contract explains why a matched MTE2_S/MTE3_S SetFlag/WaitFlag pair waits for source-pipeline reads/writes before allowing the scalar-side exit path to continue.
- [asc_sync（同步）](../../apis/simd_api/c_api/sync/asc_sync.md)（`exemplifies`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》明确提供“DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [核内同步](../../apis/simd_api/basic_api/sync_control/intra_core_sync/intra_core_sync.md)（`exemplifies`）：核内同步 与《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [核内同步能力概述](../../apis/simd_api/c_api/sync/intra_core_sync_overview.md)（`exemplifies`）：该排障卡用 MTE2→Scalar→MTE3 数据链具体说明事件只覆盖硬件 pipe、Scalar 访问还需显式可见性处理，补足概述到诊断的桥梁。
- [L2 读写端口独立并行 HBM 总线串行共享](../performance/l2_hbm.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》明确提供“DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [逐 rank 通信路径的 MTE2 主导诊断](../performance/rank_flag_mte2.md)（`related`）：《逐 rank 通信路径的 MTE2 主导诊断》处理“ReduceScatter 远程读采用逐 rank DataCopy 与同步时，msprof 显示 aiv_mte2_time 主导 T_comm；三段注释法可排除 vec/reduce，但现有证据未单独验证 flag 是带宽缺口的唯一原因。”。《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》明确“DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。”，可直接用于核对ReduceScatter 逐 rank 搬运的 MTE2 计时、HBM 解释、同步必要性与成对 profile。
<!-- cannbot:related:end -->
