---
type: Guide
title: 原子 GM 回写与事件边界契约（SetAtomicAdd/DisableDmaAtomic）
description: 多核向同一 GM 输出累加的回写契约：SetAtomicAdd<T> 是 UB/L0C→GM 通路的状态开关（影响后续所有搬出直至关闭），开启前按数据生产流水建立依赖（示例中为 V_MTE3 事件对，见骨架注释），累加段结束必须 DisableDmaAtomic 关闭（旧名 SetAtomicNone 已更名）；GM 不自动清零——从零求和时须在首个累加前完成清零，累加到已有结果时保留初值；原子解决写写冲突、事件/SyncAll 解决读写可见性，两类同步不可互替。
tags:
- task.implementation
- topic.implementation.synchronization
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/grid_sample/op_kernel/grid_sampler_2d.h
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicAdd.md
  role: supporting
created_at: '2026-10-12T10:30:11Z'
updated_at: '2026-10-12T10:30:11Z'
platforms:
- '950'
- a2
- a3
---

# 原子 GM 回写与事件边界契约（SetAtomicAdd/DisableDmaAtomic）

## 适用场景

多核/多阶段向同一 GM 输出区累加的场景：split-K 矩阵乘尾段聚合、GridSample 类越界采样聚合、flash-attention 的 LSE 累加、梯度 scatter。263 个固定提交源码文件使用 SetAtomicAdd，其中 203 个（77%）文件中同时出现事件/屏障 API（nn 93 / transformer 66 / math 26 / cv 18）——该比例只是共现统计，不作为契约证据；契约依据是原子搬出必须满足数据生产依赖本身（见约束 3）。

## 链路骨架

提炼自 grid_sampler_2d 的原子回写段：

```cpp
// ① 事件对保证数据生产流水完成后才进入搬出段（本例 GridSample：数据由 V 计算生成、MTE3 搬出，故用 V_MTE3；
//    若数据由 MTE2 搬入 UB，则用 MTE2_MTE3，见官方 SetAtomicAdd 示例）
event_t evVMte3 = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_MTE3));
SetFlag<HardEvent::V_MTE3>(evVMte3);
WaitFlag<HardEvent::V_MTE3>(evVMte3);

SetAtomicAdd<float>();                 // ② 开启原子累加（模板参数=数据类型）
DataCopy(gmOut[base], ubResult, len);  // ③ UB→GM 搬出变为原子累加（read-modify-write）
DisableDmaAtomic();                    // ④ 关闭（源码旧名 SetAtomicNone，已更名）

// 跨核读侧（如需）：SyncAll 或跨核事件，见 GetUserWorkspace 组合
```

## 成员职责

| 环节 | API |
|---|---|
| 事件边界 | [FetchEventID](../../apis/simd_api/basic_api/resource_management/t_pipe/fetch_event_id.md)、[AllocEventID](../../apis/simd_api/basic_api/resource_management/t_pipe/alloc_event_id.md)、[SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md) |
| 原子开关 | [SetAtomicAdd](../../apis/simd_api/basic_api/atomic_operations/set_atomic_add.md)、[DisableDmaAtomic](../../apis/simd_api/basic_api/atomic_operations/disable_dma_atomic.md)、[SetAtomicType](../../apis/simd_api/basic_api/atomic_operations/set_atomic_type.md) |
| 搬出 | [DataCopy UB→GM](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_ub_to_gm.md) |
| 跨核可见性 | [SyncAll](../../apis/simd_api/basic_api/sync_control/inter_core_sync/sync_all.md)、[GetUserWorkspace 组合](../matmul/tiling_shape_core_derivation_chain.md) 相关 |

## 跨 API 联动约束

1. **状态开关作用域**：[SetAtomicAdd](../../apis/simd_api/basic_api/atomic_operations/set_atomic_add.md) 官方语义为"对**后续**搬运到 GM 的数据开启原子累加"——它是通路状态而非单次操作参数；开启后所有 UB/L0C→GM 搬出都变为累加，**必须**在累加段结束后 [DisableDmaAtomic](../../apis/simd_api/basic_api/atomic_operations/disable_dma_atomic.md) 关闭，否则污染后续普通搬出（官方约束原文："以免影响后续相关指令功能"）。
2. **开启/关闭接口对的演进**：现用名为 `DisableDmaAtomic`（kernel_operator_set_atomic_intf.h 演进注释："SetAtomicNone has been updated, please use DisableDmaAtomic instead"）；固定提交源码中 203 个文件仍多用旧名 `SetAtomicNone()`——检索源码样例时按新旧两名对照。
3. **原子搬出前按数据生产流水建立依赖**：原子开关本身不提供流水依赖，需按数据的生产流水选择事件对——本例 GridSample 样例中数据由 V 计算生成后 MTE3 搬出，用 `V_MTE3`；官方 SetAtomicAdd 示例中数据由 MTE2 搬入 UB，用 `MTE2_MTE3`。骨架中的「先等生产完成 → 开原子 → 搬出 → 关闭」顺序是该样例的写法；通用要求是搬出指令执行前，其数据的生产依赖已满足，否则等待期间的乱序搬出会落入累加段。
4. **GM 不自动清零与初值语义**：官方约束明示执行前不清零 GM。目标语义是**从零求和**时，必须保证首个累加前输出区已完成清零（host 预清零或首个写入者清），否则累加进残留值；若算法语义是**累加到已有结果**（如梯度累加、跨阶段部分和），则应保留初值，不得清零——两种语义由算法决定，接口不替开发者判断。
5. **模板参数即数据类型**：`SetAtomicAdd<float>()` 的模板参数已集成 SetAtomicType 功能，无需额外调用 SetAtomicType；类型与实际搬运 dtype 不一致时累加语义错乱。
6. **写写冲突与读写可见性不可互替**：原子仅解决多核**同时写**同一 GM 地址的丢失更新；**写后读**的跨核可见性仍需 SyncAll 或跨核事件（参见已建 GetUserWorkspace→SyncAll 组合，PR #100 导航层）；漏 SyncAll 时原子写出完整但读核可能读到旧值。
7. **通路边界**：950 支持通路为 UB/L0C→GM；A2/A3 额外含 L1→GM（官方约束段按型号列出）——跨平台算子按目标通路核对。

## 失效边界

- 忘记 DisableDmaAtomic——后续普通 DataCopy 全部变累加，输出叠加污染（无报错，静默数据错误）；
- 从零求和语义下未预清零输出区——首块累加进残留值；反之，累加已有结果语义下误清零会抹掉初值（两类语义按算法选择）；
- 事件边界缺失（开原子后才等计算）——等待期间乱序进入的搬出落入累加段；
- 读写可见性误用原子替代——原子不保证读侧看到最新值，跨核读必须另行同步；
- nan/inf 输入的边界行为（饱和/非饱和模式）见 [原子操作边界值汇总](../../apis/appendix/atomic_operations_interface_boundary_value_summary.md)。

## 验证方式

- 双核同地址累加对拍：核 A 与核 B 各加不同值，结果为两值之和且无丢失；
- 开关配对检查：静态扫描每个 SetAtomicAdd 后、下一段普通 DataCopy 前存在 DisableDmaAtomic；
- **初值语义对拍（两组明确初值）**：GM 初值 0、核 A 加 2、核 B 加 3 → 预期 5（从零求和语义，须在首个累加前完成清零）；GM 初值 10、两核分别加 2 与 3 → 预期 15（累加到已有结果的语义，保留初值）；两组都不能用「清零与不清零结果一致」作判据——那会把正确的累加行为判为失败；
- 跨核读侧：累加完成 → SyncAll → 读核取值与最终和一致。
