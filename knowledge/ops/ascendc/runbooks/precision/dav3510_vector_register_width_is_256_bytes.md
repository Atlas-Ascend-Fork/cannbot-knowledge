---
type: "Runbook"
title: "Ascend950 Reg 扫描按 256B 锁定 lane"
description: "dav-3510 上把向量寄存器误按 512B 计算会让高半 lane 重放低半数据，值与索引必须按共同的 64 lane 分块。"
tags: ["task.debugging", "topic.precision", "topic.programming_model.execution_unit.vector"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["RegTensor"]
---

# Ascend950 Reg 扫描按 256B 锁定 lane

## 现象

在 Ascend950 的 `operators/cummin/cummin.asc` 中实现 Reg SIMD 前缀扫描后，远端 CANN 9.0.1 构建成功，但完整 NPU pytest 只有 4 个用例通过、104 个失败。随后对首个扫描位置做逐 lane 比对：低 64 lane 与输入一致，高 64 lane 却从低半区重复取值；坏 lane 从 64 开始，呈稳定的半寄存器边界。

当时代码把 `VECTOR_REG_WIDTH` 当成 512B，令 `LANES=128`。`Process()` 又以这个常量推进 `nStart` 和 `nLanes`，因此每个内层块都按 128 个 int32 索引 lane 搬运和计算。

## 适用场景

- 工程形态：Ascend C 单文件自定义算子，`__aicore__` 外层循环调用 `asc_vf_call` 的 Reg SIMD 路径。
- API 路径：同一个向量函数同时维护值寄存器与 int32 索引寄存器，且二者共享逻辑 lane。
- 已验证环境：Ascend950PR_957c / `dav-3510`，CANN 9.0.1，注册平台 `950`。
- 适用粒度：`platform_wide`，但只覆盖 dav-3510 上 256B Reg 宽度与 int32 lane 约束。
- 路线优先级：`safety_fallback`。这是 fallback，性能不是最优，追求性能请用另一路线（见 ## 相关）。本轨迹只验证了正确性修复，没有恢复性能最优实现。

## 根因

工具链头文件与算子源码探针都显示 dav-3510 的 `VECTOR_REG_WIDTH` 是 256B，不是 512B。int32 寄存器实际只有 `256 / 4 = 64` 个 lane。代码却让 `LANES=128` 同时控制 GM/UB 偏移、每块长度和 int32 索引向量，导致逻辑上访问 128 lane，硬件实际只完成 64 lane；下一半数据因此从低半寄存器内容重放。 该问题不是 `LoadAlign` 默认 distribution 造成的：显式改为 `DIST_NORM` 后，同一高 64 lane 重放现象保持不变。决定性机制是硬编码寄存器宽度错误。 值与索引要在同一比较/选择链中 lane-lock。对 float32/int32，值和索引都恰为 64 lane；对 16 位值，值寄存器虽然可容纳更多元素，仍应以 int32 索引寄存器的 64 lane 作为共同活动上限。

## 解决配方

修复边界取 `Process()` 消费的编译期常量及完整函数。before/after 均由最初完整写入与后续成功 Edit 事件逐字回放得到。

### before

```cpp
// Lanes per inner chunk. Equals int32 VL (VECTOR_REG_WIDTH/4 = 128) and is <=
// the B16/B32 value VL, so value and idx registers stay lane-locked at 128.
constexpr static uint32_t LANES = 128;

    __aicore__ inline void Process()
    {
        for (int64_t m = mStart_; m < mEnd_; ++m) {
            int64_t rowBase = m * R_ * N_;   // GM offset (elements) to this m-row
            for (int64_t nStart = 0; nStart < N_; nStart += LANES) {
                int64_t remN = N_ - nStart;
                uint32_t nLanes = (LANES < remN) ? LANES : static_cast<uint32_t>(remN);
                uint32_t isFirstTile = 1;
                for (int64_t rBase = 0; rBase < R_; rBase += TILE_R) {
                    int64_t remR = R_ - rBase;
                    uint32_t rTile = (TILE_R < remR) ? TILE_R : static_cast<uint32_t>(remR);
                    ProcessTile<T>(rowBase, nStart, nLanes, rTile,
                                   static_cast<int32_t>(rBase), isFirstTile);
                    isFirstTile = 0;
                }
            }
        }
    }
```

### after

```cpp
// Lanes per inner chunk. On dav-3510 VECTOR_REG_WIDTH = 256 B (verified both
// via the toolkit headers -- atan2/v35 `constexpr VECTOR_REG_WIDTH = 256UL`,
// resize_nearest_neighbor comment "vl size: 256 / dtypeSize" -- and on-card
// probe: a hardcoded 128 produced deterministic high-64 corruption because
// VL_T(float)=64 but CopyIn/CopyOut assumed 128). So the int32 register holds
// VL_I = 256/4 = 64 elements. Value (T) and index (int32) must be lane-locked
// inside one __simd_vf__ call sharing one cmp mask, so the active lane count is
// the MIN VL across the two = VL_I = 64. For float/int32 this is a full
// register (VL_T = VL_I = 64); for half/bfloat16 VL_T = 128 > 64, so only the
// low 64 of the 128-lane value register are active (mask selects them; the
// high 64 are don't-care). The mask is lane-indexed (bit i = lane i), so a
// value-derived cmp mask correctly drives the 64-lane int32 Select.
// AscendC::VECTOR_REG_WIDTH is not visible at namespace scope, hence literal.
constexpr static uint32_t LANES = 64;

    __aicore__ inline void Process()
    {
        for (int64_t m = mStart_; m < mEnd_; ++m) {
            int64_t rowBase = m * R_ * N_;   // GM offset (elements) to this m-row
            for (int64_t nStart = 0; nStart < N_; nStart += LANES) {
                int64_t remN = N_ - nStart;
                uint32_t nLanes = (LANES < remN) ? LANES : static_cast<uint32_t>(remN);
                uint32_t isFirstTile = 1;
                for (int64_t rBase = 0; rBase < R_; rBase += TILE_R) {
                    int64_t remR = R_ - rBase;
                    uint32_t rTile = (TILE_R < remR) ? TILE_R : static_cast<uint32_t>(remR);
                    ProcessTile<T>(rowBase, nStart, nLanes, rTile,
                                   static_cast<int32_t>(rBase), isFirstTile);
                    isFirstTile = 0;
                }
            }
        }
    }
```

## 设计决策

选择 64 lane，是因为值与 int32 argmin 必须共享同一逻辑 lane，最窄参与类型决定共同活动 lane 数。放弃继续使用 128 lane，因为它已被首行高半重复的实测模式和工具链中的 256B 定义共同否定；放弃仅修改 `LoadAlign` distribution，因为该尝试没有改变错误。

当前方案属于 correctness-first 的 `safety_fallback`。如果后续设计面向 16 位值的双半寄存器高性能路径，必须拆成两个各自与 64-lane int32 索引锁定的子批，并重新上板验证。

## 预防

- 不从旧架构注释或经验硬编码 Reg 宽度；先在目标 CANN 头文件或同架构官方实现中确认 `VECTOR_REG_WIDTH`。
- 同一 Mask/Select 链含不同 dtype 时，以参与类型中的最小有效 lane 数规划循环步长。
- 首次上板先做 `r=0` 的逐 lane 恒等探针；它能把搬运/寄存器宽度问题从扫描递推逻辑中隔离出来。
- 为 lane 边界两侧增加回归检查，至少比较最后一个有效 lane 与下一个 lane。

## 验证信号

验证来自本次 cummin 开发中对远端 Ascend950 实卡的诊断命令和测试输出，证据等级均为 `tool_observed`。

- 修复前，首行首个坏 lane 为 64，高半区出现低半输入的重复值；按 128-lane 周期统计时，坏点集中在每块高半。
- CANN 9.0.1 目标环境的实现头显示 `vlSize = 256 / dtypeSize`，另一个 dav-3510 官方实现显式定义 `VECTOR_REG_WIDTH = 256UL`。
- 改成 64 lane 并重新构建后，同一 `r=0` 全 lane 探针报告 `bad=0`（950，tool_observed）。
- 该修复后的完整 pytest 仍有其他 dtype/尾块失败，因此这里只把首行 lane 错位结案；后续根因由其他卡分别处理。

## 失效边界

- 未验证 a2、a3 或其他 NPU 架构；不得把 64 直接写成跨平台常量。
- 若值与索引不共享比较掩码，或索引不在 Reg 中并行维护，本卡的“取最窄 dtype lane”约束未必适用。
- 16 位值想利用完整值寄存器时，必须提供独立的索引映射与两段验证，不能直接把活动 lane 放大到 128。

## 坏实践

- 看到 128-lane 现象就假定寄存器是 512B。
- 只检查 lane 0 或整张量最大误差，不检查寄存器半边界。
- 把显式 `DIST_NORM` 的无效尝试继续包装为根因修复。

## 误诊

曾把高半错位归因于 `LoadAlign` 默认 distribution，并将所有 load 显式改为 `DIST_NORM`；实卡输出逐值不变，故该假设被否定。

<!-- cannbot:related:start -->
## 相关

- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_continuous.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《LoadAlign》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_mask_reg.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《LoadAlign》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_noncontinuous.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《LoadAlign》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [MaskGenWithRegTensor](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《MaskGenWithRegTensor》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [RegTensor](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/reg_tensor.md)（`exemplifies`）：RegTensor 与《Ascend950 Reg 扫描按 256B 锁定 lane》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《VF调用》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [asc_vf_call](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《asc_vf_call》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [寄存器数据类型](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/register_data_types.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《寄存器数据类型》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [B16 比较先升到 B32 锁定索引 lane](b16_value_and_b32_index_masks_need_common_b32_compute.md)（`related`）：256B 寄存器决定 B16 为 128 lane、B32 为 64 lane，是该 mask 错配的硬件根因。
- [RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽](regtensor_cross_chunk_state_should_persist_in_ub_slot.md)（`related`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《Ascend950 Reg 扫描按 256B 锁定 lane》说明dav-3510 上把向量寄存器误按 512B 计算会让高半 lane 重放低半数据，值与索引必须按共同的 64 lane 分块。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [Reg int32→int64 Cast 源目 VL 错配留空索引](int32_to_int64_reg_cast_must_respect_destination_lane_width.md)（`same_topic`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《Reg int32→int64 Cast 源目 VL 错配留空索引》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [VECTOR_REG_WIDTH 只能在 Device 作用域求值](../compilation/vector_reg_width_only_in_device_context.md)（`same_topic`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《VECTOR_REG_WIDTH 只能在 Device 作用域求值》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane](compute_lane_count_must_follow_promoted_fp32_width.md)（`same_topic`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [半精度索引错位—拆分双 int32 掩码](b16_value_mask_must_split_for_two_int32_index_registers.md)（`same_topic`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《半精度索引错位—拆分双 int32 掩码》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
<!-- cannbot:related:end -->
