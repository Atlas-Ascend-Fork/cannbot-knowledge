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

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad 后未先同步 Cast 导致低精度 NaN](../precision/mte2_barrier_must_precede_vector_cast.md)（`related`）：MTE2→Vector 方向需在读取前建立完成性，与 Vector→MTE3 共同组成双向流水依赖。
- [FP16 算子 Cast 提升-计算-回退链设计](../precision/fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：双缓冲模板展示 EnQue/DeQue/FreeTensor 的标准生产消费次序，可用于核对 fence 放置。
- [L2 读写端口独立并行 HBM 总线串行共享](../performance/l2_hbm.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位》明确提供“rms_norm_rope_k_store_kv_cache Phase2 回读用 TQue<VECIN> 走 MTE2→MTE3 跨迭代复用同一 UB，下一轮 MTE2 覆盖 UB 时上一轮 MTE3 未读完形成 WAR，大数据(max_seq_len=65536) kv_a_out 前段错位、后段正确；判别靠 debug_full.py 逐 batch front/back match + 单核(blockDim=1)排除多核；根因为 TQue event 在该跨迭代路径不可靠且跨 Phase GM 可见性需 Host 同步。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [RoPE DIST_INTLV_B16 store mask 致零值](../precision/rope_dist_intlv_b16_store_mask.md)（`related`）：focal 已用 barrier 探针排除普通流水时序；该卡给出真正的跨迭代 MTE2/MTE3 WAR 分形和双向 fence 验证，可据错误是周期性 lane 零还是前段回读错位区分布局与同步根因。
- [TBuf 跨 MTE2 与 Vector 须队列交接](../precision/tbuf_mte2_to_vector_requires_queue_handoff.md)（`related`）：若用 TBuf 而非 TQue，MTE2→Vector 没有自动队列依赖；该卡给出需要改队列或显式 barrier 的边界。
- [MTE2跨流水未建依赖导致UB读到上次调用残值](../precision/direct_mte_slot_reuse_needs_bidirectional_hard_events.md)（`same_topic`）：直接复用 MTE slot 时必须用双向 hard event 保护读写，等价落实本卡强调的 MTE2/MTE3 双向 fence。
- [Vector 结果搬出前须经 VECOUT 队列](../precision/vector_results_need_vecout_queue_before_mte3.md)（`same_topic`）：该卡给出 Vector→MTE3 必须经 VecOut 队列的所有权与同步，正是本 fence 的一半。
- [arch35 小 per-channel 输出读旧值判别与规避](arch35_per_channel.md)（`same_topic`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位》提供“rms_norm_rope_k_store_kv_cache Phase2 回读用 TQue<VECIN> 走 MTE2→MTE3 跨迭代复用同一 UB，下一轮 MTE2 覆盖 UB 时上一轮 MTE3 未读完形成 WAR，大数据(max_seq_len=65536) kv_a_out 前段错位、后段正确；判别靠 debug_full.py 逐 batch front/back match + 单核(blockDim=1)排除多核；根因为 TQue event 在该跨迭代路径不可靠且跨 Phase GM 可见性需 Host 同步。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
<!-- cannbot:related:end -->
