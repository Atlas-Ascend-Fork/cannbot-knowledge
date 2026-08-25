---
type: "Runbook"
title: "B16 结果大幅偏差 — UNPACK 后补 Reg Cast"
description: "Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# B16 结果大幅偏差 — UNPACK 后补 Reg Cast

## 现象

在单文件 Flash 工程中实现基于 `AscendC::Reg` 的归一化 kernel 时，远端构建已经成功，fp32 输入的直接真机检查也接近参考结果；但把同一计算路径换成 fp16 或 bf16 后，输出与参考值出现数量级明显更大的偏差。出错代码在 `operators/rms_norm/rms_norm.asc` 中直接用 `LoadAlign<float, DIST_UNPACK_B16>` 把 B16 数据装入 `RegTensor<float>`，计算后又直接用 `StoreAlign<float, DIST_PACK_B32>` 写回 B16 内存，没有显式数值格式转换。

## 适用场景

- 工程形态：Ascend950 Flash/kernel 直调，单个 `.asc` 中使用 `__simd_vf__` 与 `AscendC::Reg`；
- API 路径：`LoadAlign<T, DIST_UNPACK_B16>` → `Reg::Cast<float, T, CastParam::mulAddDstTrait>` → fp32 Reg 计算 → `Reg::Cast<T, float, CastParam::float2halfCastTrait>` → `StoreAlign<T, DIST_PACK_B32>`；
- 验证过的平台与版本：950（Ascend950PR_957b / dav-3510）+ CANN 9.0.1；与 frontmatter `platforms` 一致；
- 适用粒度：`operator_family`，适用于需要把 fp16/bf16 载入 fp32 Reg 计算、再写回 B16 的向量 kernel；
- 路线优先级：`safety_fallback`。这是 fallback，性能不是最优，追求性能请用另一路线（见 ## 相关）。本 trace 验证了正确性，没有完成与其他正确 B16 转换路径的性能对比；
- 明确不适用/未验证：纯 fp32 路径不需要这组 Cast；其他 CANN 版本的预定义 trait 名称与支持矩阵未验证。

## 根因

`DIST_UNPACK_B16`/`DIST_PACK_B32` 只控制 B16 数据在寄存器搬运时的展开/打包布局，并不等价于 fp16/bf16 与 fp32 的数值格式转换；把展开后的 B16 位模式直接当作 `RegTensor<float>` 参与运算，会让参与平方、规约和缩放的数值语义错误。 机制链为：B16 内存位模式 → `UNPACK_B16` 布局展开 → **仍缺 B16→fp32 数值 Cast** → fp32 算术解释错误；正确链路必须是 B16 内存位模式 → `UNPACK_B16` → `Cast<float, T>` → fp32 算术 → `Cast<T, float>` → `PACK_B32`。

## 解决配方

代码证据来自同一开发轨迹中的完整函数写入。固定 40 位 revision、稳定行号与 blob URL 未在 trace 中恢复，因此该候选必须由 curator 继续做 active 证据门禁；已恢复的 path 为 `operators/rms_norm/rms_norm.asc`，symbols 为 `rmsnorm_reduce_rstd_vf` 与 `rmsnorm_compute_y_vf`，以下均为函数级 verbatim 快照。

### before

`revision`: trace 修复前写入态（完整 commit 未恢复）；`path`: `operators/rms_norm/rms_norm.asc`；`symbol`: `rmsnorm_reduce_rstd_vf`；`line range`: 完整 symbol；`blob`: 未在 trace 中提供。

```cpp
template <typename T>
__simd_vf__ inline void rmsnorm_reduce_rstd_vf(
    __ubuf__ T *xAddr, __ubuf__ float *rstdAddr,
    uint32_t M, uint32_t D, float avgFactor, float eps)
{
    const uint32_t fullChunks = D / VF_VL;
    const uint32_t tail = D % VF_VL;

    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();
    uint32_t one = 1;
    AscendC::Reg::MaskReg scalarMask = AscendC::Reg::UpdateMask<float>(one);

    for (uint32_t r = 0; r < M; ++r) {
        AscendC::Reg::RegTensor<float> accReg;
        AscendC::Reg::Duplicate<float>(accReg, 0.0f, fullMask);

        const uint32_t rowOff = r * D;
        for (uint32_t c = 0; c < fullChunks; ++c) {
            AscendC::Reg::RegTensor<float> xReg;
            const uint32_t off = rowOff + c * VF_VL;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
            } else {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xReg, (__ubuf__ float *)(xAddr + off));
            }
            AscendC::Reg::Mul(xReg, xReg, xReg, fullMask);                       // x^2
            AscendC::Reg::RegTensor<float> dstReg;
            AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(dstReg, xReg, fullMask);
            AscendC::Reg::Add(accReg, accReg, dstReg, fullMask);                 // accumulate (lane0)
        }
        if (tail > 0) {
            uint32_t t = tail;
            AscendC::Reg::MaskReg tailMask = AscendC::Reg::UpdateMask<float>(t);
            AscendC::Reg::RegTensor<float> xReg;
            const uint32_t off = rowOff + fullChunks * VF_VL;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
            } else {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xReg, (__ubuf__ float *)(xAddr + off));
            }
            AscendC::Reg::Mul(xReg, xReg, xReg, tailMask);
            AscendC::Reg::RegTensor<float> dstReg;
            AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(dstReg, xReg, tailMask);
            AscendC::Reg::Add(accReg, accReg, dstReg, fullMask);
        }

        // rstd = 1 / sqrt(acc * avgFactor + eps)  (kept in Reg, lane0)
        AscendC::Reg::Muls(accReg, accReg, avgFactor, scalarMask);
        AscendC::Reg::Adds(accReg, accReg, eps, scalarMask);
        AscendC::Reg::RegTensor<float> sqrtReg;
        AscendC::Reg::Sqrt(sqrtReg, accReg, scalarMask);
        AscendC::Reg::RegTensor<float> oneReg;
        AscendC::Reg::Duplicate<float>(oneReg, 1.0f, scalarMask);
        AscendC::Reg::Div(accReg, oneReg, sqrtReg, scalarMask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            rstdAddr + r * RSTD_SLOT_FLOATS, accReg, scalarMask);
    }
}
```

`revision`: trace 修复前写入态（完整 commit 未恢复）；`path`: `operators/rms_norm/rms_norm.asc`；`symbol`: `rmsnorm_compute_y_vf`；`line range`: 完整 symbol；`blob`: 未在 trace 中提供。

```cpp
template <typename T>
__simd_vf__ inline void rmsnorm_compute_y_vf(
    __ubuf__ T *xAddr, __ubuf__ T *gammaAddr,
    __ubuf__ float *rstdAddr, __ubuf__ T *yAddr,
    uint32_t M, uint32_t D)
{
    const uint32_t fullChunks = D / VF_VL;
    const uint32_t tail = D % VF_VL;

    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();

    for (uint32_t r = 0; r < M; ++r) {
        AscendC::Reg::RegTensor<float> rstdBroad;
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_BRC_B32>(
            rstdBroad, rstdAddr + r * RSTD_SLOT_FLOATS);   // broadcast scalar to all lanes

        const uint32_t rowOff = r * D;
        for (uint32_t c = 0; c < fullChunks; ++c) {
            const uint32_t off = rowOff + c * VF_VL;
            const uint32_t gOff = c * VF_VL;
            AscendC::Reg::RegTensor<float> xReg, gReg;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(gReg, (__ubuf__ float *)gammaAddr + gOff);
            } else {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xReg, (__ubuf__ float *)(xAddr + off));
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(gReg, (__ubuf__ float *)(gammaAddr + gOff));
            }
            AscendC::Reg::Mul(xReg, xReg, rstdBroad, fullMask);            // x * rstd
            AscendC::Reg::Mul(xReg, xReg, gReg, fullMask);                  // x*rstd*gamma
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, fullMask);
            } else {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_PACK_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, fullMask);
            }
        }
        if (tail > 0) {
            uint32_t t = tail;
            AscendC::Reg::MaskReg tailMask = AscendC::Reg::UpdateMask<float>(t);
            const uint32_t off = rowOff + fullChunks * VF_VL;
            const uint32_t gOff = fullChunks * VF_VL;
            AscendC::Reg::RegTensor<float> xReg, gReg;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(gReg, (__ubuf__ float *)gammaAddr + gOff);
            } else {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xReg, (__ubuf__ float *)(xAddr + off));
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(gReg, (__ubuf__ float *)(gammaAddr + gOff));
            }
            AscendC::Reg::Mul(xReg, xReg, rstdBroad, tailMask);
            AscendC::Reg::Mul(xReg, xReg, gReg, tailMask);
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, tailMask);
            } else {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_PACK_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, tailMask);
            }
        }
    }
}
```

### after

`revision`: trace 修复后写入态（完整 commit 未恢复）；`path`: `operators/rms_norm/rms_norm.asc`；`symbol`: `rmsnorm_reduce_rstd_vf`；`line range`: 完整 symbol；`blob`: 未在 trace 中提供。

```cpp
template <typename T>
__simd_vf__ inline void rmsnorm_reduce_rstd_vf(
    __ubuf__ T *xAddr, __ubuf__ float *rstdAddr,
    uint32_t M, uint32_t D, float avgFactor, float eps)
{
    const uint32_t fullChunks = D / VF_VL;
    const uint32_t tail = D % VF_VL;

    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();
    uint32_t one = 1;
    AscendC::Reg::MaskReg scalarMask = AscendC::Reg::UpdateMask<float>(one);

    for (uint32_t r = 0; r < M; ++r) {
        AscendC::Reg::RegTensor<float> accReg;
        AscendC::Reg::Duplicate<float>(accReg, 0.0f, fullMask);

        const uint32_t rowOff = r * D;
        for (uint32_t c = 0; c < fullChunks; ++c) {
            AscendC::Reg::RegTensor<float> xReg;
            const uint32_t off = rowOff + c * VF_VL;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
            } else {
                AscendC::Reg::RegTensor<T> srcReg;
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + off);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(xReg, srcReg, fullMask);
            }
            AscendC::Reg::Mul(xReg, xReg, xReg, fullMask);                       // x^2
            AscendC::Reg::RegTensor<float> dstReg;
            AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(dstReg, xReg, fullMask);
            AscendC::Reg::Add(accReg, accReg, dstReg, fullMask);                 // accumulate (lane0)
        }
        if (tail > 0) {
            uint32_t t = tail;
            AscendC::Reg::MaskReg tailMask = AscendC::Reg::UpdateMask<float>(t);
            AscendC::Reg::RegTensor<float> xReg;
            const uint32_t off = rowOff + fullChunks * VF_VL;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
            } else {
                AscendC::Reg::RegTensor<T> srcReg;
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + off);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(xReg, srcReg, tailMask);
            }
            AscendC::Reg::Mul(xReg, xReg, xReg, tailMask);
            AscendC::Reg::RegTensor<float> dstReg;
            AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(dstReg, xReg, tailMask);
            AscendC::Reg::Add(accReg, accReg, dstReg, fullMask);
        }

        // rstd = 1 / sqrt(acc * avgFactor + eps)  (kept in Reg, lane0)
        AscendC::Reg::Muls(accReg, accReg, avgFactor, scalarMask);
        AscendC::Reg::Adds(accReg, accReg, eps, scalarMask);
        AscendC::Reg::RegTensor<float> sqrtReg;
        AscendC::Reg::Sqrt(sqrtReg, accReg, scalarMask);
        AscendC::Reg::RegTensor<float> oneReg;
        AscendC::Reg::Duplicate<float>(oneReg, 1.0f, scalarMask);
        AscendC::Reg::Div(accReg, oneReg, sqrtReg, scalarMask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            rstdAddr + r * RSTD_SLOT_FLOATS, accReg, scalarMask);
    }
}
```

`revision`: trace 修复后写入态（完整 commit 未恢复）；`path`: `operators/rms_norm/rms_norm.asc`；`symbol`: `rmsnorm_compute_y_vf`；`line range`: 完整 symbol；`blob`: 未在 trace 中提供。

```cpp
template <typename T>
__simd_vf__ inline void rmsnorm_compute_y_vf(
    __ubuf__ T *xAddr, __ubuf__ T *gammaAddr,
    __ubuf__ float *rstdAddr, __ubuf__ T *yAddr,
    uint32_t M, uint32_t D)
{
    const uint32_t fullChunks = D / VF_VL;
    const uint32_t tail = D % VF_VL;

    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();

    for (uint32_t r = 0; r < M; ++r) {
        AscendC::Reg::RegTensor<float> rstdBroad;
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_BRC_B32>(
            rstdBroad, rstdAddr + r * RSTD_SLOT_FLOATS);   // broadcast scalar to all lanes

        const uint32_t rowOff = r * D;
        for (uint32_t c = 0; c < fullChunks; ++c) {
            const uint32_t off = rowOff + c * VF_VL;
            const uint32_t gOff = c * VF_VL;
            AscendC::Reg::RegTensor<float> xReg, gReg;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(gReg, (__ubuf__ float *)gammaAddr + gOff);
            } else {
                AscendC::Reg::RegTensor<T> xs, gs;
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xs, xAddr + off);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(xReg, xs, fullMask);
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(gs, gammaAddr + gOff);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(gReg, gs, fullMask);
            }
            AscendC::Reg::Mul(xReg, xReg, rstdBroad, fullMask);            // x * rstd
            AscendC::Reg::Mul(xReg, xReg, gReg, fullMask);                  // x*rstd*gamma
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, fullMask);
            } else {
                AscendC::Reg::RegTensor<T> ys;
                AscendC::Reg::Cast<T, float, AscendC::CastParam::float2halfCastTrait>(ys, xReg, fullMask);
                AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(yAddr + off, ys, fullMask);
            }
        }
        if (tail > 0) {
            uint32_t t = tail;
            AscendC::Reg::MaskReg tailMask = AscendC::Reg::UpdateMask<float>(t);
            const uint32_t off = rowOff + fullChunks * VF_VL;
            const uint32_t gOff = fullChunks * VF_VL;
            AscendC::Reg::RegTensor<float> xReg, gReg;
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, (__ubuf__ float *)xAddr + off);
                AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(gReg, (__ubuf__ float *)gammaAddr + gOff);
            } else {
                AscendC::Reg::RegTensor<T> xs, gs;
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xs, xAddr + off);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(xReg, xs, tailMask);
                AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(gs, gammaAddr + gOff);
                AscendC::Reg::Cast<float, T, AscendC::CastParam::mulAddDstTrait>(gReg, gs, tailMask);
            }
            AscendC::Reg::Mul(xReg, xReg, rstdBroad, tailMask);
            AscendC::Reg::Mul(xReg, xReg, gReg, tailMask);
            if constexpr (std::is_same_v<T, float>) {
                AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                    (__ubuf__ float *)(yAddr + off), xReg, tailMask);
            } else {
                AscendC::Reg::RegTensor<T> ys;
                AscendC::Reg::Cast<T, float, AscendC::CastParam::float2halfCastTrait>(ys, xReg, tailMask);
                AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(yAddr + off, ys, tailMask);
            }
        }
    }
}
```

## 设计决策

1. 选择 CANN 9.0.1 已提供的 `AscendC::CastParam::mulAddDstTrait` 和 `float2halfCastTrait`，因为该版本没有向用户暴露可直接构造的 `AscendC::Reg::CastTrait`；
2. 放弃“仅靠 `UNPACK_B16`/`PACK_B32` 完成数值转换”的路线，因为真机已证明它只在 fp32 路径正确；
3. 轨迹曾考虑把 B16 先在 UB 中用 classic Cast 转为 fp32，再做 Reg 计算，但会增加中间 UB 缓冲，未采用；
4. 当前方案按 `safety_fallback` 管理：它是本 trace 中正确的 native Reg 转换方案，但没有完成与其他正确方案的性能最优性验证。

## 预防

- 看到 `DIST_UNPACK_B16` 或 `DIST_PACK_B32` 时，把它们当作搬运布局参数，不要当作 dtype Cast；
- B16→fp32 的 Load 后检查是否存在显式 `Reg::Cast<float, T, ...>`；fp32→B16 的 Store 前检查是否存在显式 `Reg::Cast<T, float, ...>`；
- full chunk 与 tail chunk 必须都执行同样的 Cast 链，并分别使用 full mask 与 tail mask；
- 在宣称修复前，至少分别运行 fp32、fp16、bf16 的直接真机对比；只验证 fp32 无法覆盖该根因。

## 验证信号

来源说明：在 Ascend950PR_957b 上对同一个 Reg kernel 先后运行修复前后的三 dtype 直接对比；修复只在 B16 Load/Store 路径补显式 Cast。

- 修复前 fp32 `max_diff=4.76837158203125e-07`，而 fp16 `max_diff=6.1953125`、bf16 `max_diff=6.3125`（950，证据等级: tool_observed）；
- 加入 `mulAddDstTrait` 与 `float2halfCastTrait` 后远端构建输出 `[100%] Built target op_rms_norm`（950，证据等级: tool_observed）；
- 修复后直接检查为 fp32 `max_diff=4.76837158203125e-07`、fp16 `max_diff=0.0`、bf16 `max_diff=0.0`（950，证据等级: tool_observed）。

## 失效边界

- 结论只在 Ascend950PR_957b、dav-3510、CANN 9.0.1 的 Reg API 上实测；A2/A3 与其他 CANN 版本未验证，不能直接写入 `platforms`；
- trait 名称是版本相关 API，升级 CANN 后应以固定版本声明或头文件实现重新核对；
- 本卡只解决 B16 数值格式转换，不覆盖 UB 行基址对齐、尾块越界或多行搬运问题。

## 坏实践

- 把 `DIST_UNPACK_B16` 直接装入 `RegTensor<float>` 后参与 fp32 算术；
- 把 fp32 `RegTensor` 直接用 `DIST_PACK_B32` 写入 B16 地址；
- 只跑 fp32 case 就断言混合 dtype kernel 已正确；
- 用放宽误差阈值掩盖 B16 结果偏差。

## 误诊

- “UNPACK 这个名字表示自动转换为 fp32”是错误假设；真机对比证明还需要显式 Cast；
- 用户自定义 `CastTrait` 的编译失败不表示 Reg Cast 不可用；该 CANN 版本应使用 `AscendC::CastParam` 的预定义 trait。

<!-- cannbot:related:start -->
## 相关

- [AscUnpack](../../apis/simd_api/c_api/reg/data_compress/asc_unpack.md)（`exemplifies`）：该卡证明 UnPack 只处理布局/位宽，随后仍需 Cast 才得到 fp32 数值。
- [Cast](../../apis/simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Cast》说明在RegTensor间执行数值类型转换，并通过CastTrait配置舍入、饱和和mask行为。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Pack](../../apis/simd_api/basic_api/reg_vector_compute/data_compression/pack.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Pack》说明将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [UnPack](../../apis/simd_api/basic_api/reg_vector_compute/data_compression/un_pack.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《UnPack》说明将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](b16_interleave_compute_should_promote_to_b32_layout.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《B16 交错 DINTLV 成对归零 — 转 fp32 后重排》说明B16 直接解交错经 Cast 后 lane 对不齐；先转连续 fp32 UB 再走 DINTLV_B32。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [B16 比较先升到 B32 锁定索引 lane](b16_value_and_b32_index_masks_need_common_b32_compute.md)（`related`）：统一到 B32 计算时，UNPACK 只改变布局，仍需显式数值 Cast 才能得到正确 float 值。
- [CastTrait 按值 NTTP 在 C++17 编译失败](../compilation/casttrait_nttp_uses_reference_in_cxx17.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《CastTrait 按值 NTTP 在 C++17 编译失败》说明AscendC Reg CastTrait 作为按值非类型模板参数需要 C++20；C++17 direct-launch 工程改用静态 constexpr 对象的 const 引用 NTTP。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [FP16 算子 Cast 提升-计算-回退链设计](fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《FP16 算子 Cast 提升-计算-回退链设计》说明FP16 输入算子用 Cast(FP16→FP32, CAST_NONE) 提升到 FP32 做 VF 计算、Cast(FP32→FP16, CAST_RINT) 回退输出；AscendC::Cast 在 CANN 9.0.0/Ascend950 须带 RoundMode:: 前缀。ApplyAdamV2 穿刺与 ST 全量验证。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../compilation/reg_load_and_store_use_distinct_dist_enums.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《LoadDist 错用 DIST_NORM_B32 导致编译失败》说明Reg LoadAlign 误用 StoreDist 风格枚举 DIST_NORM_B32 时编译失败；fp32 常规加载应使用 LoadDist::DIST_NORM。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](../compilation/reg_cast_requires_explicit_zeroing_trait.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING》说明dav-3510 Reg::Cast 的默认 CastTrait 使用 MaskMergeMode::UNKNOWN，设备实现静态断言只接受 ZEROING 或 MERGING，需传显式 trait。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Reg CastTrait RoundMode 命名空间编译失败](../compilation/casttrait_roundmode_is_in_ascendc.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Reg::Cast 的 trait 需要静态存储期](../compilation/reg_casttrait_requires_static_storage.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Reg::Cast 的 trait 需要静态存储期》说明Reg SIMD 的 CastTrait 作为引用型非类型模板实参时，函数内普通 constexpr 会导致 Cast 模板匹配失败；改为 static constexpr 后可编译。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane](compute_lane_count_must_follow_promoted_fp32_width.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》说明2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](bf16_cast_cast_rint.md)（`related`）：UNPACK 卡证明布局展开不能替代 B16→FP32 数值 Cast；本卡进一步约束该显式数值 Cast 在扩精度方向必须使用 CAST_NONE。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`same_topic`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
<!-- cannbot:related:end -->
