---
type: "Runbook"
title: "TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位"
description: "rms_norm_rope_k_store_kv_cache Phase2 回读用 TQue<VECIN> 走 MTE2→MTE3 跨迭代复用同一 UB，下一轮 MTE2 覆盖 UB 时上一轮 MTE3 未读完形成 WAR，大数据(max_seq_len=65536) kv_a_out 前段错位、后段正确；判别靠 debug_full.py 逐 batch front/back match + 单核(blockDim=1)排除多核；根因为 TQue event 在该跨迭代路径不可靠且跨 Phase GM 可见性需 Host 同步。"
tags: ["task.debugging", "topic.implementation.pipeline", "topic.implementation.synchronization"]
status: stable
sources: []
created_at: "2026-08-18T07:57:42Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位

## 现象

在 `rms_norm_rope_k_store_kv_cache`（MLA Prefill 融合算子，dav-3510 / Ascend950PR V100 / CANN 9.1.0）RMSNorm/RoPE 修复后，小数据（`max_seq_len=1024`，bs=4）全部通过，但 UT 用 `max_seq_len=65536`（大数据）时 `kv_a_out` 前段（Phase 2 回读区段）不匹配、后段（Phase 1 新算）正确。`debug_full.py` 对每个 batch 输出 `front match=False, back match=True`。

## 适用场景

- 工程形态：kernel 直调（AscendC `TBuf` + 显式 `HardEvent` fence + Host 双 launch + `aclrtSynchronizeStream`）。
- API 路径：`TQue<VECIN>` / `TBuf<TPosition::VECCALC>` / `GetTPipePtr()->FetchEventID(HardEvent::MTE2_MTE3|MTE3_MTE2)` / `SetFlag`/`WaitFlag` / `DataCopyPad` / `aclrtSynchronizeStream`。
- 验证过的平台与 CANN 版本：Ascend950（dav-3510，Ascend950PR V100）/ CANN 9.1.0。
- 适用粒度：`operator_family`（所有"MTE2 读 GM → MTE3 写 GM"跨迭代复用同一 UB 的二阶段/回读算子）。
- 路线优先级：`recommended_fastpath`（跨流水线 WAR 必须显式 fence；跨 Phase GM 可见性必须 Host 同步）。
- 不适用或未验证场景：单 Phase 算子无回读；a2/a3 未验证，推断可迁移（`HardEvent`/`aclrtSynchronizeStream` 为跨架构通用机制）。

## 判别方法

触发（tool_observed）：大数据（`max_seq_len=65536`）UT 下 `kv_a_out` 前段（Phase 2 回读区段）不匹配、后段（Phase 1 新算）正确，`debug_full.py` 逐 batch 输出 `front match=False, back match=True`；小数据（`max_seq_len=1024`）全部通过。

探针：① 跑 `debug_full.py`，对每个 batch 分别报告 `front match` / `back match`，定位错位只在回读区段且只在大数据暴露；② 把 kernel launch 的 `blockDim` 收为 1（单核），重跑同一大数据 UT——前段仍 `match=False`，排除"多核竞争写同一 GM 地址"假说；③ 检查 `ProcessCache` 回读 buffer 是否用 `TQue<VECIN>` 依赖 `EnQue/DeQue` 自动同步、且回读与下一轮搬入复用同一 UB 区。

观测（tool_observed）：大数据下逐 batch `front match=False, back match=True`；单核 `blockDim=1` 仍复现前段错位（非多核问题）；问题只在数据量大、多轮 UB 复用时暴露，小数据不触发。

解释（interpretation，agent 根因分析，非 API 规范主张）：`ProcessCache` 用 `TQue<VECIN>` 做 cache 回读 buffer，`EnQue/DeQue` 的 event 管理在 MTE2→MTE3 跨迭代路径上不可靠——下一轮 MTE2 把新数据搬进同一 UB 区时，上一轮 MTE3（`DataCopyPad` 写 GM）可能还没读完该 UB 区，形成 WAR 竞争，导致回读区段错位；叠加跨 Phase GM 可见性问题（`Process` 写 paged cache、`ProcessCache` 读 paged cache，原在同 kernel 内靠 `pipe_->Reset()`+`SyncAll()` 切换，大数据时跨核 GM 写对读不可见）。修复方向（已验证 3/3 UT 通过）为改 `TBuf` + 显式 `HardEvent::MTE2_MTE3`（MTE2 搬完才让 MTE3 写）+ `HardEvent::MTE3_MTE2`（MTE3 读完 UB 才让下一轮 MTE2 覆盖）双向 fence 消除 WAR，并把 `Process`/`ProcessCache` 拆为两个独立 kernel entry、Host 两次 launch 之间 `aclrtSynchronizeStream` 确保跨 Phase GM 可见性。

## 验证信号

- 大数据(`max_seq_len=65536`) `kv_a_out` 前段(Phase2回读)`front match=False`、后段(Phase1新算)`back match=True`，小数据全部通过（来源平台:Ascend950；证据等级:tool_observed）
- 单核(`blockDim=1`)重跑同一大数据 UT 前段仍 `match=False`，排除多核竞争写同一 GM（来源平台:Ascend950；证据等级:tool_observed）
- 改 `TBuf` + `MTE2_MTE3`/`MTE3_MTE2` 双向 fence + 双 kernel launch + `aclrtSynchronizeStream` 后 3/3 UT 全部通过（来源平台:Ascend950；证据等级:tool_observed）

## 预防

- AscendC 跨迭代复用同一 UB 的 MTE2→MTE3 路径必须显式 `HardEvent::MTE2_MTE3` + `HardEvent::MTE3_MTE2` 双向 fence，不要依赖 `TQue` 的自动 event 管理（event ID 复用在大数据多轮场景不可靠）。
- 跨 Phase GM 读写（一个 Phase 写、另一个 Phase 读同一 GM）应拆为独立 kernel launch + Host `aclrtSynchronizeStream`，不要靠核内 `pipe_->Reset()` + `SyncAll()` 保证 GM 可见性。

## 失效边界

- 平台：实测仅 dav-3510（Ascend950）/ CANN 9.1.0。a2/a3 未验证，推断可迁移（`HardEvent`/`aclrtSynchronizeStream` 为跨架构通用机制）。
- 单 Phase 算子（无回读）不需要双 launch；UB 足够大、单次搬入不跨迭代复用时 WAR 不触发，`TQue` 可用。
- `aclrtSynchronizeStream` 相对单 kernel 的额外同步开销未在本 trace 做成对相对测量。

## 坏实践

- 用 `TQue` 自动同步替代跨流水线 WAR 的显式 fence（大数据暴露不可靠）。该路线标记为 `banned`。
- 在同 kernel 内靠 `pipe_->Reset()` + `SyncAll()` 保证跨 Phase GM 可见性（大数据不可见）。该路线标记为 `banned`。
