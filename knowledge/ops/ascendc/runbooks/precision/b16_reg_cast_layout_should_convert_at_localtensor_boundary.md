---
type: "Runbook"
title: "特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换"
description: "dav-3510/CANN 9.0.1 的已测 DIST_UNPACK_B16→Reg::Cast→UB 中间组合产生系统性偏差；classic AscendC::Cast 边界转换建立了正确性基线，不代表所有 Reg Cast 组合失效。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["bfloat16_t"]
---

# 特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换

## 现象

在 dav-3510 Reg 直调归约 kernel 中，fp32 路径与参考实现一致（`maxdiff` 在 `1e-8` 量级），但 fp16/bf16 通过 `Reg::DataCopy<..., DIST_UNPACK_B16>` + `Reg::Cast<float,T>` 转为 fp32 中间 UB 后，fp16 出现 `1e-2~2e-1` 的系统性偏差。偏差会随归约长度增大而下降，说明不是 softmax 公式错误，而是 b16 转换/布局路径污染了一部分 lane。

## 适用场景

- 工程形态：Ascend950 `asc_vf_call` Reg 直调 kernel；
- API 路径：b16 `Reg::Cast` 与 UB 中间缓冲，后续 fp32 Reg Reduce/Exp/Div；
- 验证过的平台与版本：950 / CANN 9.0.1；
- 适用粒度：`operator_family`（b16→fp32 计算链）；
- 结论边界：只覆盖当前 SDK 和已测 `DIST_UNPACK_B16 → Reg::Cast → UB` 组合；classic 边界 Cast 是该组合的正确性 oracle；
- 明确不适用：已经用独立 probe 证明 Reg Cast dtype/layout 组合正确的 SDK 版本。

## 根因

本轨迹中这条 b16 load/cast/store 组合没有形成与 fp32 中间 UB 一致的 1:1 元素布局；将转换后的 RegTensor 写回 UB 再加载，导致部分 lane 值错误。因为 fp32 路径完全正确，且更换 `LoadAlign`/`DataCopy` 仍保持相同 b16 偏差，故障被收敛到该具体组合，而不是归约公式；这不否定具有显式正确 trait 且经独立 probe 验证的其他 Reg Cast 组合。

## 解决配方

把 b16↔fp32 转换移到 `LocalTensor` 边界，用 classic `AscendC::Cast`；所有核心计算仍在 fp32 Reg VF 中执行。

### before

```cpp
template <typename T>
__simd_vf__ inline void ar_cast_in_vf(__ubuf__ float *dst, __ubuf__ T *src,
                                      uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<T> srcReg;
    AscendC::Reg::RegTensor<float> dstReg;
    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(rem);
        AscendC::Reg::DataCopy<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, src + off);
        AscendC::Reg::Cast<float, T, kCastB16ToFp32>(dstReg, srcReg, mask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            dst + off, dstReg, mask);
    }
}
```

### after

```cpp
__aicore__ inline void Compute(int64_t row)
{
    (void)row;
    auto xLocal = inQueue_.DeQue<T>();
    __ubuf__ float *workPtr;
    if constexpr (std::is_same<T, float>::value) {
        workPtr = (__ubuf__ float *)xLocal.GetPhyAddr();
    } else {
        auto workFp32 = workFp32Buf_.Get<float>();
        AscendC::Cast<float, T>(
            workFp32, xLocal, AscendC::RoundMode::CAST_NONE, castCount_);
        workPtr = (__ubuf__ float *)workFp32.GetPhyAddr();
    }
    AscendC::PipeBarrier<PIPE_V>();

    auto slotLocal = slotBuf_.Get<float>();
    __ubuf__ float *maxSlot = (__ubuf__ float *)slotLocal.GetPhyAddr();
    __ubuf__ float *sumSlot = maxSlot + SLOT_ELEMS;
    auto workOutLocal = workOutBuf_.Get<float>();
    __ubuf__ float *workOutPtr = (__ubuf__ float *)workOutLocal.GetPhyAddr();

    constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t cc = (r_ + VL - 1) / VL;
    asc_vf_call<ar_reduce_max_vf>(workPtr, maxSlot, r_, cc);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<ar_sub_exp_vf>(workPtr, maxSlot, r_, cc);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<ar_reduce_sum_vf>(workPtr, sumSlot, r_, cc);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<ar_div_vf>(workOutPtr, workPtr, sumSlot, r_, cc);
    AscendC::PipeBarrier<PIPE_V>();

    auto yLocal = outQueue_.AllocTensor<T>();
    if constexpr (std::is_same<T, float>::value) {
        AscendC::DataCopy(yLocal, workOutLocal, r_);
    } else {
        AscendC::Cast<T, float>(
            yLocal, workOutLocal, AscendC::RoundMode::CAST_ROUND, castCount_);
    }
    outQueue_.EnQue(yLocal);
    inQueue_.FreeTensor(xLocal);
}
```

## 设计决策

- 采用边界 Cast：先建立正确性基线，计算主体仍保留 Reg 路线；
- 放弃 `LoadAlign` 与 `DataCopy<UNPACK_B16>` 互换：两者实测偏差相同，没有触及根因；
- classic 边界 Cast 建立了该问题的正确性 oracle；是否存在正确且更快的融合 Reg Cast 路线必须在相同 SDK 上单独验证。

## 性能影响

未获得“边界 Cast vs 已证明正确的纯 Reg Cast”的成对性能数据；本卡只声明该具体组合的正确性 oracle，不声明性能收益。

## 预防

- b16 错、fp32 对时先做最小 cast round-trip probe，不要先改归约公式；
- 同时观察短向量与长向量，若误差随长度稀释，优先检查 lane/布局；
- 转换结果写 UB 再读时，明确验证 store/load dist 的配对关系。

## 验证信号

来源为一次 Ascend950 归约 kernel 的 b16 精度联调：

- 错误 Reg Cast 路径下 fp16 `maxdiff` 为 `2.075e-01`、`1.248e-01`、`9.972e-03`，而 fp32 为 `1.118e-08`（来源平台: 950；证据等级: tool_observed）；
- 改为 LocalTensor 边界 Cast 后，对齐长度的 fp16 `maxdiff=3.815e-06`，bf16 `maxdiff=3.052e-05`（来源平台: 950；证据等级: tool_observed）；
- 后续完整 pytest 58/58 通过，含 fp16/bf16 与 NaN/Inf（来源平台: 950；证据等级: tool_observed）。

## 失效边界

短于最小搬运粒度的 b16 行还需要独立的对齐/最小 Cast count 修复；非 VL fp32 UB 局部复制也不由本卡解决。A2/A3 未验证（未验证，推断可迁移）。

## 坏实践

只把 `LoadAlign` 换成 `DataCopy<UNPACK_B16>`，但保持相同 Reg Cast→UB 中间布局；实测没有改善。

## 误诊

把偏差解释成 `exp` 或规约累加精度，会导致反复修改正确的 fp32 计算链。

<!-- cannbot:related:start -->
## 相关

- [AscStore](../../apis/simd_api/c_api/reg/reg_store/asc_store.md)（`exemplifies`）：AscStore 与《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》的实质衔接是：AscStore 的 C++ 对应入口共享 GM 写回语义；B16 load-cast-store 与 RoPE store-mask 故障直接约束存储分布和有效 lane。
- [Cast](../../apis/simd_api/basic_api/memory_vector_compute/type_conversion/cast.md)（`exemplifies`）：该故障卡的可执行修复正是把转换移到 LocalTensor 边界并调用 Memory《Cast》，以此建立 B16↔FP32 正确性基线。
- [Cast](../../apis/simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`exemplifies`）：该故障卡锁定的失真组合直接包含 Reg《Cast》：DIST_UNPACK_B16 后转换并写回 UB 时部分 lane 布局不再 1:1。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_continuous.md)（`exemplifies`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《LoadAlign》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [LocalTensor简介](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor_intro.md)（`exemplifies`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《LocalTensor简介》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [RegLayout](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/reg_layout.md)（`exemplifies`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《RegLayout》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [StoreAlignContinuous](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md)（`exemplifies`）：失真组合的写回端直接调用 Reg《StoreAlignContinuous》语义的 StoreAlign，把 Cast 后寄存器按指定 StoreDist 写入 FP32 UB 中间缓冲。
- [bfloat16类型](../../apis/simt_api/math_functions/bfloat16_type/bfloat16_type.md)（`exemplifies`）：《bfloat16类型》说明bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。；《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》说明dav-3510/CANN 9.0.1 的已测 DIST_UNPACK_B16→Reg::Cast→UB 中间组合产生系统性偏差；classic AscendC::Cast 边界转换建立了正确性基线，不代表所有 Reg Cast 组合失效。。二者在bfloat16类型入口的实际使用受全局类型命名、B16边界转换和提升后lane宽度约束，而非由平台或版本过滤上存在可执行的直接衔接。
- [数据排布转换](../../apis/simd_api/basic_api/memory_vector_compute/data_layout_conversion/data_layout_conversion.md)（`exemplifies`）：数据排布转换 与《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [FP16 算子 Cast 提升-计算-回退链设计](fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [RoPE DIST_INTLV_B16 store mask 致零值](rope_dist_intlv_b16_store_mask.md)（`related`）：该卡在另一条 B16 load-cast-store 组合上也用 LocalTensor 边界 Cast 建立正确性基线，支持 focal 将转换移出有问题的寄存器布局链，而不修改正确的 fp32 算术。
- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](b16_interleave_compute_should_promote_to_b32_layout.md)（`same_topic`）：两卡描述同一 b16 Reg 布局失真故障：B16 交错 Load/Cast/Store 会成对归零，验证过的修复是在 LocalTensor 边界先升为 B32，再以 B32 Reg 布局计算和重排。
- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`same_topic`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [Reg API int8 DIST_PACK_B32 交错零](reg_api_int8_dist_pack_b32.md)（`same_topic`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》说明dav-3510/CANN 9.0.1 的已测 DIST_UNPACK_B16→Reg::Cast→UB 中间组合产生系统性偏差；classic AscendC::Cast 边界转换建立了正确性基线，不代表所有 Reg Cast 组合失效。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
<!-- cannbot:related:end -->
