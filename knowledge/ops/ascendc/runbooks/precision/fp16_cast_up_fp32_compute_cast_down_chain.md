---
type: "Runbook"
title: "FP16 算子 Cast 提升-计算-回退链设计"
description: "FP16 输入算子用 Cast(FP16→FP32, CAST_NONE) 提升到 FP32 做 VF 计算、Cast(FP32→FP16, CAST_RINT) 回退输出；AscendC::Cast 在 CANN 9.0.0/Ascend950 须带 RoundMode:: 前缀。ApplyAdamV2 穿刺与 ST 全量验证。"
tags: ["task.implementation", "topic.precision", "topic.compute.elementwise.type_conversion", "topic.implementation.api_layer.basic_api"]
status: stable
sources: []
created_at: "2026-08-17T02:27:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# FP16 算子 Cast 提升-计算-回退链设计

## 现象

在 Ascend950 上为 ApplyAdamV2 实现 FP16 dtype 支持。FP16 直接做 VF（向量函数）计算会因动态范围小、累加溢出而失精度；需要把 FP16 输入提升到 FP32 计算、输出再回退 FP16。该模式在穿刺 `probe_adam_fp16` / `probe_mbart_adam_fp16`（NPU Kernel 直调）全通过，ST NPU 2895/2895（含 FP16 全量用例）通过。期间发现 `AscendC::Cast` 在 CANN 9.0.0/Ascend950 上要求 `AscendC::RoundMode::` 前缀枚举值（`CAST_NONE` / `CAST_RINT`），裸用 `AscendC::CAST_NONE` 会编译失败（vendor 缓存陈旧版本时触发）。

## 适用场景

- 工程形态：AscendC 算子 FP16 dtype 实现（kernel 直调与图模式）。
- API 路径：`AscendC::Cast`、`AscendC::Reg::*`（Muls/Add/Sub）、`asc_vf_call`、`AscendC::GetVecLen`。
- 验证平台与版本：Ascend950PR（arch35/DAV_3510），CANN 9.0.0。
- 适用粒度：`operator_family`（适用于所有 FP16 输入、内部用 VF 做浮点运算的算子）。
- 路线优先级：`recommended_fastpath`（FP16 提升到 FP32 计算再回退，是该类算子精度与动态范围的标准做法）。
- 不适用或未验证场景：FP16 直接用 FP16 VF 指令（若硬件有原生 FP16 高精度指令且动态范围足够）不适用；a2/a3 平台未验证 RoundMode:: 前缀要求。

## 完整实现

FP16 路径以 `CopyIn(FP16) → Cast(FP16→FP32, CAST_NONE) → VF(FP32) → Cast(FP32→FP16, CAST_RINT) → CopyOut(FP16)` 为完整计算单元。Cast 提升用 `CAST_NONE`（无损、直接位扩展），Cast 回退用 `CAST_RINT`（就近舍入，避免截断引入偏置）。VF 函数模板用 `ComputeT = std::conditional<IS_FP16, float, T>` 在 FP16 路径下实例化为 float，复用同一份 FP32 VF 实现。同步事件 `MTE2_V`（CopyIn→VF）与 `MTE3_MTE2`（上一轮 CopyOut→本轮 CopyIn）保证 buffer 依赖。该实现经穿刺 + ST NPU 全量验证通过。

## 完整代码

`op_kernel/arch35/apply_adam_v2_kernel.h` 主循环 FP16 路径（verbatim，含 Cast 提升、VF 链、Cast 回退）：

```cpp
        // FP16 path: use FP32 VL for VF function calls (after Cast to FP32)
        constexpr uint32_t VL_FP32 = AscendC::GetVecLen() / sizeof(float);
        constexpr bool IS_FP16 = (sizeof(T) == 2);

        int64_t coord[8] = {};
        for (int64_t flat = start; flat < end; flat++) {
            int64_t a_i_seg = GetUBSplitRange(flat % td_->split.a_o, td_->split.a_o,
                                              td_->split.a_i, td_->split.a_i_tail);
            int64_t count = a_i_seg * inner_count;
            FlatToEffectiveCoord(flat, td_->max_bro_shape, RANK,
                                 td_->split.axis, td_->split.a_i, td_->split.a_o, coord);

            // === Sync: MTE3_MTE2 (non-first iteration) ===
            if (flat != start) AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(evMTE3toMTE2);

            // === CopyIn: 4 element tensors → UB (MTE2) ===
            CopyInBrc(coord, IN_GRAD, B0, a_i_seg);
            CopyInBrc(coord, IN_M, B1, a_i_seg);
            CopyInBrc(coord, IN_V, B2, a_i_seg);
            CopyInBrc(coord, IN_VAR, B3, a_i_seg);

            // === Sync: MTE2_V (RAW) ===
            AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(evMTE2toV);
            AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(evMTE2toV);

            // === FP16 path: Cast FP16→FP32 (in-place, 4 buffers) ===
            if constexpr (IS_FP16) {
                AscendC::Cast(buf_[B0].Get<float>(), buf_[B0].Get<T>(),
                              AscendC::RoundMode::CAST_NONE, count);
                AscendC::Cast(buf_[B1].Get<float>(), buf_[B1].Get<T>(),
                              AscendC::RoundMode::CAST_NONE, count);
                AscendC::Cast(buf_[B2].Get<float>(), buf_[B2].Get<T>(),
                              AscendC::RoundMode::CAST_NONE, count);
                AscendC::Cast(buf_[B3].Get<float>(), buf_[B3].Get<T>(),
                              AscendC::RoundMode::CAST_NONE, count);
            }

            // === VF chain: Moments → Div → Update ===
            // Use FP32 type for VF calls in FP16 path (after Cast)
            using ComputeT = typename std::conditional<IS_FP16, float, T>::type;
            uint16_t repCount = AscendC::CeilDivision(count, VL_FP32);

            // Moments VF: adam or mbart_adam
            if (td_->adam_mode_flag == 0) {
                // adam mode: AdamMomentsVF (with gradient clipping)
                asc_vf_call<AdamMomentsVF<ComputeT>>(
                    (__ubuf__ ComputeT*)buf_[B0].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B1].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B2].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B3].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B4].Get<ComputeT>().GetPhyAddr(),
                    count, VL_FP32, repCount,
                    clipCoeff, beta1, beta2);
            } else {
                // mbart_adam mode: MbartMomentsVF (no gradient clipping)
                asc_vf_call<MbartMomentsVF<ComputeT>>(
                    (__ubuf__ ComputeT*)buf_[B0].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B1].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B2].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B3].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B4].Get<ComputeT>().GetPhyAddr(),
                    count, VL_FP32, repCount,
                    beta1, beta2);
            }

            // Div VF: shared between both modes
            asc_vf_call<AdamDivVF<ComputeT>>(
                (__ubuf__ ComputeT*)buf_[B0].Get<ComputeT>().GetPhyAddr(),
                (__ubuf__ ComputeT*)buf_[B2].Get<ComputeT>().GetPhyAddr(),
                (__ubuf__ ComputeT*)buf_[B4].Get<ComputeT>().GetPhyAddr(),
                count, VL_FP32, repCount,
                epsilon);

            // Update VF: adam or mbart_adam
            if (td_->adam_mode_flag == 0) {
                // adam mode: AdamUpdateVF (weight_decay * var, lr * u_final)
                asc_vf_call<AdamUpdateVF<ComputeT>>(
                    (__ubuf__ ComputeT*)buf_[B0].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B2].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B3].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B4].Get<ComputeT>().GetPhyAddr(),
                    count, VL_FP32, repCount,
                    weightDecay, lr);
            } else {
                // mbart_adam mode: MbartUpdateVF (step_size * u, weight_decay * lr * var)
                asc_vf_call<MbartUpdateVF<ComputeT>>(
                    (__ubuf__ ComputeT*)buf_[B0].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B2].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B3].Get<ComputeT>().GetPhyAddr(),
                    (__ubuf__ ComputeT*)buf_[B4].Get<ComputeT>().GetPhyAddr(),
                    count, VL_FP32, repCount,
                    weightDecay, stepSize, lr);
            }

            // === FP16 path: Cast FP32→FP16 (output buffers only: B0, B4, B2) ===
            if constexpr (IS_FP16) {
                AscendC::Cast(buf_[B0].Get<T>(), buf_[B0].Get<float>(),
                              AscendC::RoundMode::CAST_RINT, count);
                AscendC::Cast(buf_[B4].Get<T>(), buf_[B4].Get<float>(),
                              AscendC::RoundMode::CAST_RINT, count);
                AscendC::Cast(buf_[B2].Get<T>(), buf_[B2].Get<float>(),
                              AscendC::RoundMode::CAST_RINT, count);
            }
```

## 系统信息

- 工具链：CANN 9.0.0，bisheng clang 15.0.5，`asc_op_compile_base` 编译器。
- 目标平台：Ascend950PR（arch35 / DAV_3510）。
- 目录布局：`op_kernel/arch35/apply_adam_v2_kernel.h`（kernel 主体）、`apply_adam_v2_tiling_struct.h`、`apply_adam_v2_struct.h`、`kernel_operator.h`。
- 相关文件清单（与事件流读写一一对应）：`op_kernel/arch35/apply_adam_v2_kernel.h`、`op_host/arch35/apply_adam_v2_tiling_arch35.cpp`、`op_api/aclnn_apply_adam_v2.cpp`、`probe/probe_adam_fp16/op_kernel/apply_adam_v2_kernel.asc`、`probe/probe_mbart_adam_fp16/op_kernel/apply_adam_v2_kernel.asc`。
- RoundMode 枚举定义位置：`/usr/local/Ascend/cann-9.0.0/x86_64-linux/asc/impl/basic_api/utils/kernel_utils_mode.h`（`enum class RoundMode : uint8_t`）。

## 设计决策

- 为何选"提升到 FP32 计算-回退 FP16"而非"全程 FP16 VF"：Adam 优化器有 `m_t = β1·m + (1-β1)·g`、`v_t = β2·v + (1-β2)·g²` 等累加与平方运算，FP16 动态范围小、累加易溢出且精度损失大；FP32 中间计算保证精度，仅输入/输出边界做 FP16 转换，是该类优化器算子的标准做法。
- 为何 Cast 提升用 `CAST_NONE`、回退用 `CAST_RINT`：`CAST_NONE` 在 FP16→FP32 是无损位扩展（不引入误差）；`CAST_RINT` 在 FP32→FP16 做就近舍入（round to nearest even），比截断 `CAST_TRUNC` 引入更小偏置。若回退用截断，大数会被系统性偏小。
- 为何 VF 函数用 `ComputeT = std::conditional<IS_FP16, float, T>` 模板：FP32 与 FP16 路径复用同一份 VF 实现，仅在 buffer 类型与是否 Cast 上分叉，避免维护两份算法代码导致公式不一致。
- 被放弃的设计：曾考虑 FP16 直接用 FP16 VF 指令并做 Kahan 补偿；因复杂度高、动态范围仍不足、收益不明确而放弃。
- 当前方案属哪档路线：`recommended_fastpath`（FP32 中间计算 + 边界 Cast）。

## 验证信号

穿刺 `probe_adam_fp16` / `probe_mbart_adam_fp16`（NPU Kernel 直调，`<<<>>>` 语法）全通过；ST NPU 含 FP16 全量用例 2895/2895 通过（双千双万 rtol=1e-3, atol=1e-4）。（来源平台：950；证据等级: tool_observed）

`AscendC::Cast` 在 CANN 9.0.0/Ascend950 要求 `AscendC::RoundMode::` 前缀；vendor 缓存陈旧版本（裸 `AscendC::CAST_NONE`）触发编译错误，源仓正确版本带前缀，重新编译部署后通过。（来源平台：950；证据等级: tool_observed）

## 失效边界

- 该 Cast 链模式适用于"FP16 输入、内部浮点运算、FP16 输出"的算子；若算子本身只需整数/位运算（无浮点动态范围问题），不需要提升。
- `RoundMode::` 前缀要求基于 CANN 9.0.0/Ascend950；推断可迁移到 a2/a3（API 命名空间一致），但未验证，推断可迁移。
- `CAST_RINT` 回退在某些需要确定性截断的场景（如量化感知训练对齐）不适用，需按目标精度策略改 `CAST_TRUNC` 或 `CAST_ROUND`。

## 预防

- 写 `AscendC::Cast` 调用时，RoundMode 参数一律写 `AscendC::RoundMode::CAST_*` 全限定形式，不依赖 `using` 把 `RoundMode` 引入当前作用域，避免跨 CANN 版本命名空间变化导致编译失败。
- 部署后若 TTK 报 Cast 相关编译错误，第一查项是 vendor 缓存 (`opp/vendors/<op>_custom/...`) 的 kernel.h 是否陈旧，而非源仓。

## 误诊

vendor 缓存陈旧导致 Cast 编译错误时，曾怀疑源仓 kernel.h 有误；实际源仓已正确带 `RoundMode::` 前缀，错误只在 vendor 部署的旧拷贝。重新编译安装 `cann-ops-nn-custom_linux-x86_64.run` 后修复。
