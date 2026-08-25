---
type: "Runbook"
title: "Reg LoadAlign 不接受 const __ubuf__ 指针"
description: "CANN 9.0.1 RegBase 的两参数 LoadAlign/StoreAlign 要求非 const UB 指针；const 会让 VF 封装与 asc_vf_call 编译失败。"
tags: ["task.debugging", "topic.implementation.api_layer.simt_api", "topic.data_movement.memory_access"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Reg LoadAlign 不接受 const __ubuf__ 指针

## 现象

在 `operators/softmax/softmax.asc` 的 RegBase 三段 softmax 实现首次远端构建时，`softmax_max_vf<T>` 把输入声明为 `__ubuf__ const T *`，另外两个 VF 也把只读 UB 槽声明为 const。CANN 9.0.1 对两参数 `LoadAlign` 报：

```text
error: no matching function for call to 'LoadAlign'
candidate function template not viable: 2nd argument ('const __ubuf__ __bf16 *') would lose const qualifier
```

移除三个 VF 参数的 const 后，下一次构建仍在 `ComputeSoftmaxRow<T>` 的 `asc_vf_call` 包装边界报同类 const 转换错误；把 `xAddr` 同步改为非 const 后闭合了同一根因的全部调用链。

## 适用场景

- 工程形态：Ascend C RegBase kernel 直调；
- API 路径：`AscendC::Reg::LoadAlign` / `StoreAlign` 两参数重载、`__simd_vf__`、`asc_vf_call` 与 `LocalTensor::GetPhyAddr()`；
- 验证过的平台与 CANN 版本：950（Ascend950PR_957b / dav-3510）+ CANN 9.0.1；
- 适用粒度：`platform_wide`，适用于同工具链 Reg VF 的 UB 指针签名；
- 路线优先级：`recommended_fastpath`，表示唯一完成真实构建和上板验证的合法 ABI 写法；
- 明确不适用 / 未验证场景：三参数/五参数 LoadAlign 重载、其他 CANN 版本与 A2/A3 未验证。

## 根因

根因是该版本 RegBase 两参数 `LoadAlign` / `StoreAlign` 与 `asc_vf_call` 接口链要求 `__ubuf__ T *`，没有 const 兼容路径；任一 VF 形参或包装实参残留 `const __ubuf__ T *`，模板匹配都会因丢失 const 限定而失败。

## 解决配方

以下函数逐字恢复自轨迹实际写入（每个 `__simd_vf__` 与 `__aicore__` 函数前均有紧邻的 `template <typename T>`）。失败态与修复态均无固定 revision；路径为 `operators/softmax/softmax.asc`，symbols 为三个 VF 和 `ComputeSoftmaxRow<T>`，写入快照约 70–219 行。

### before

```cpp
template <typename T>
__simd_vf__ inline void softmax_max_vf(
    __ubuf__ float *work,         // out: fp32 row
    __ubuf__ const T *xIn,        // in: T row
    __ubuf__ float *maxSlot,      // out: one-VL (64 fp32) slot, [0]=row max
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);   // 64
    AscendC::Reg::RegTensor<float> xReg;
    AscendC::Reg::RegTensor<float> chunkMaxReg;
    AscendC::Reg::RegTensor<float> accMaxReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();
    AscendC::Reg::Duplicate<float>(accMaxReg, NEG_INF_F);   // init all lanes

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;                       // count >= off
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
                xReg, (__ubuf__ const float *)xIn + off);
        } else {
            AscendC::Reg::RegTensor<T> tReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(
                tReg, xIn + off);
            AscendC::Reg::Cast<float, T, softmaxCastTrait>(xReg, tReg, mask);
        }
        // fp32 row -> workBuf for pass2 re-read (UB, not GM).
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            work + off, xReg, mask);
        // reduce this chunk's max (reads the register xReg, not UB).
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkMaxReg, xReg, mask);
        // accumulate scalar at lane 0 across chunks (dst aliases src0; allowed
        // by the RegBase binary family, same idiom as Mul(xReg,xReg,yReg,mask)).
        AscendC::Reg::Max(accMaxReg, accMaxReg, chunkMaxReg, allMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        maxSlot, accMaxReg, allMask);   // [0]=row max
}

template <typename T>
__simd_vf__ inline void softmax_expsub_sum_vf(
    __ubuf__ float *work,             // in/out: fp32 row (in: x, out: exp)
    __ubuf__ const float *maxSlot,    // in: [0]=row max
    __ubuf__ float *sumSlot,          // out: [0]=row sum
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> xReg;
    AscendC::Reg::RegTensor<float> expReg;
    AscendC::Reg::RegTensor<float> maxSlotReg;
    AscendC::Reg::RegTensor<float> maxVecReg;
    AscendC::Reg::RegTensor<float> chunkSumReg;
    AscendC::Reg::RegTensor<float> accSumReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();
    AscendC::Reg::Duplicate<float>(accSumReg, 0.0f);

    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
        maxSlotReg, maxSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::MaskMergeMode::ZEROING,
        AscendC::Reg::BroadcastPos::LOWEST>(maxVecReg, maxSlotReg, allMask);

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
            xReg, work + off);                 // read fp32 x row (UB)
        AscendC::Reg::ExpSub<float, float,
            AscendC::Reg::RegLayout::ZERO,
            AscendC::Reg::MaskMergeMode::ZEROING>(expReg, xReg, maxVecReg, mask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            work + off, expReg, mask);         // overwrite work with exp
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(chunkSumReg, expReg, mask);
        AscendC::Reg::Add(accSumReg, accSumReg, chunkSumReg, allMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        sumSlot, accSumReg, allMask);   // [0]=row sum
}

template <typename T>
__simd_vf__ inline void softmax_div_cast_vf(
    __ubuf__ const float *work,       // in: exp row
    __ubuf__ const float *sumSlot,    // in: [0]=row sum
    __ubuf__ T *yOut,                 // out: T row
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> eReg;
    AscendC::Reg::RegTensor<float> outReg;
    AscendC::Reg::RegTensor<float> sumSlotReg;
    AscendC::Reg::RegTensor<float> sumVecReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();

    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
        sumSlotReg, sumSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::MaskMergeMode::ZEROING,
        AscendC::Reg::BroadcastPos::LOWEST>(sumVecReg, sumSlotReg, allMask);

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
            eReg, work + off);                 // read exp row (UB)
        AscendC::Reg::Div(outReg, eReg, sumVecReg, mask);   // exp/sum
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                (__ubuf__ float *)yOut + off, outReg, mask);
        } else {
            AscendC::Reg::RegTensor<T> tReg;
            AscendC::Reg::Cast<T, float, softmaxCastTrait>(tReg, outReg, mask);
            AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(
                yOut + off, tReg, mask);
        }
    }
}
```

```cpp
template <typename T>
__aicore__ inline void ComputeSoftmaxRow(
    const AscendC::LocalTensor<T> &xLocal, AscendC::LocalTensor<T> &yLocal,
    AscendC::LocalTensor<float> &workLocal, AscendC::LocalTensor<float> &maxLocal,
    AscendC::LocalTensor<float> &sumLocal, uint32_t count)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    __ubuf__ const T *xAddr = (__ubuf__ const T *)xLocal.GetPhyAddr();
    __ubuf__ T *yAddr = (__ubuf__ T *)yLocal.GetPhyAddr();
    __ubuf__ float *workAddr = (__ubuf__ float *)workLocal.GetPhyAddr();
    __ubuf__ float *maxAddr = (__ubuf__ float *)maxLocal.GetPhyAddr();
    __ubuf__ float *sumAddr = (__ubuf__ float *)sumLocal.GetPhyAddr();
    uint32_t chunkCount = (count + VL_F - 1) / VL_F;

    asc_vf_call<softmax_max_vf<T>>(workAddr, xAddr, maxAddr, count, chunkCount);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<softmax_expsub_sum_vf<T>>(workAddr, maxAddr, sumAddr, count, chunkCount);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<softmax_div_cast_vf<T>>(workAddr, sumAddr, yAddr, count, chunkCount);
}
```

### after

```cpp
template <typename T>
__simd_vf__ inline void softmax_max_vf(
    __ubuf__ float *work,         // out: fp32 row
    __ubuf__ T *xIn,              // in: T row (Reg API takes non-const __ubuf__*)
    __ubuf__ float *maxSlot,      // out: one-VL (64 fp32) slot, [0]=row max
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);   // 64
    AscendC::Reg::RegTensor<float> xReg;
    AscendC::Reg::RegTensor<float> chunkMaxReg;
    AscendC::Reg::RegTensor<float> accMaxReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();
    AscendC::Reg::Duplicate<float>(accMaxReg, NEG_INF_F);   // init all lanes

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;                       // count >= off
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
                xReg, xIn + off);
        } else {
            AscendC::Reg::RegTensor<T> tReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(
                tReg, xIn + off);
            AscendC::Reg::Cast<float, T, softmaxCastTrait>(xReg, tReg, mask);
        }
        // fp32 row -> workBuf for pass2 re-read (UB, not GM).
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            work + off, xReg, mask);
        // reduce this chunk's max (reads the register xReg, not UB).
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkMaxReg, xReg, mask);
        // accumulate scalar at lane 0 across chunks (dst aliases src0; allowed
        // by the RegBase binary family, same idiom as Mul(xReg,xReg,yReg,mask)).
        AscendC::Reg::Max(accMaxReg, accMaxReg, chunkMaxReg, allMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        maxSlot, accMaxReg, allMask);   // [0]=row max
}

template <typename T>
__simd_vf__ inline void softmax_expsub_sum_vf(
    __ubuf__ float *work,             // in/out: fp32 row (in: x, out: exp)
    __ubuf__ float *maxSlot,          // in: [0]=row max (Reg API: non-const)
    __ubuf__ float *sumSlot,          // out: [0]=row sum
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> xReg;
    AscendC::Reg::RegTensor<float> expReg;
    AscendC::Reg::RegTensor<float> maxSlotReg;
    AscendC::Reg::RegTensor<float> maxVecReg;
    AscendC::Reg::RegTensor<float> chunkSumReg;
    AscendC::Reg::RegTensor<float> accSumReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();
    AscendC::Reg::Duplicate<float>(accSumReg, 0.0f);

    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
        maxSlotReg, maxSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::MaskMergeMode::ZEROING,
        AscendC::Reg::BroadcastPos::LOWEST>(maxVecReg, maxSlotReg, allMask);

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
            xReg, work + off);                 // read fp32 x row (UB)
        AscendC::Reg::ExpSub<float, float,
            AscendC::Reg::RegLayout::ZERO,
            AscendC::Reg::MaskMergeMode::ZEROING>(expReg, xReg, maxVecReg, mask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            work + off, expReg, mask);         // overwrite work with exp
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(chunkSumReg, expReg, mask);
        AscendC::Reg::Add(accSumReg, accSumReg, chunkSumReg, allMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        sumSlot, accSumReg, allMask);   // [0]=row sum
}

template <typename T>
__simd_vf__ inline void softmax_div_cast_vf(
    __ubuf__ float *work,           // in: exp row (Reg API: non-const)
    __ubuf__ float *sumSlot,        // in: [0]=row sum (Reg API: non-const)
    __ubuf__ T *yOut,               // out: T row
    uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> eReg;
    AscendC::Reg::RegTensor<float> outReg;
    AscendC::Reg::RegTensor<float> sumSlotReg;
    AscendC::Reg::RegTensor<float> sumVecReg;
    AscendC::Reg::MaskReg allMask =
        AscendC::Reg::CreateMask<float, AscendC::Reg::MaskPattern::ALL>();

    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
        sumSlotReg, sumSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::MaskMergeMode::ZEROING,
        AscendC::Reg::BroadcastPos::LOWEST>(sumVecReg, sumSlotReg, allMask);

    for (uint32_t i = 0; i < chunkCount; ++i) {
        uint32_t off = i * VL_F;
        uint32_t remaining = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
            eReg, work + off);                 // read exp row (UB)
        AscendC::Reg::Div(outReg, eReg, sumVecReg, mask);   // exp/sum
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
                yOut + off, outReg, mask);
        } else {
            AscendC::Reg::RegTensor<T> tReg;
            AscendC::Reg::Cast<T, float, softmaxCastTrait>(tReg, outReg, mask);
            AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(
                yOut + off, tReg, mask);
        }
    }
}
```

```cpp
template <typename T>
__aicore__ inline void ComputeSoftmaxRow(
    const AscendC::LocalTensor<T> &xLocal, AscendC::LocalTensor<T> &yLocal,
    AscendC::LocalTensor<float> &workLocal, AscendC::LocalTensor<float> &maxLocal,
    AscendC::LocalTensor<float> &sumLocal, uint32_t count)
{
    constexpr uint32_t VL_F = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    __ubuf__ T *xAddr = (__ubuf__ T *)xLocal.GetPhyAddr();
    __ubuf__ T *yAddr = (__ubuf__ T *)yLocal.GetPhyAddr();
    __ubuf__ float *workAddr = (__ubuf__ float *)workLocal.GetPhyAddr();
    __ubuf__ float *maxAddr = (__ubuf__ float *)maxLocal.GetPhyAddr();
    __ubuf__ float *sumAddr = (__ubuf__ float *)sumLocal.GetPhyAddr();
    uint32_t chunkCount = (count + VL_F - 1) / VL_F;

    asc_vf_call<softmax_max_vf<T>>(workAddr, xAddr, maxAddr, count, chunkCount);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<softmax_expsub_sum_vf<T>>(workAddr, maxAddr, sumAddr, count, chunkCount);
    AscendC::PipeBarrier<PIPE_V>();
    asc_vf_call<softmax_div_cast_vf<T>>(workAddr, sumAddr, yAddr, count, chunkCount);
}
```

## 设计决策

- 选择当前方案：即便参数语义上只读，也服从该 Reg ABI 的非 const UB 指针签名；只读约束保留在实现纪律和注释里。
- 放弃的候选：对指针强制 `const_cast` 或切换其他 LoadAlign 重载；前者隐藏包装边界的不匹配，后者改变寻址语义。
- 当前路线：`recommended_fastpath`，是该平台已构建并上板验证的直接 Reg VF 路线。

## 系统信息

- toolchain：CANN 9.0.1，Bisheng/Clang 15.0.5；
- SoC：Ascend950PR_957b，NpuArch=dav-3510；
- 相关文件：`operators/softmax/softmax.asc`；
- 终版源码进入短提交 `9c1ca4e`，轨迹未提供 40 位 revision 或 blob URL。

## 预防

- 编写 `__simd_vf__` 前先核对目标 CANN 的真实声明，不把普通 C++ const-correctness 习惯强加给 `__ubuf__` ABI。
- 同时检查 VF 形参和 `asc_vf_call` 实参；只改 LoadAlign 调用点仍会在包装边界失败。
- 用 fp32、fp16、bf16 三种实例化触发所有 `if constexpr` 分支。

## 验证信号

来源是 softmax RegBase 三段 kernel 的真实构建循环；移除三个 VF 参数 const 后原始 LoadAlign 错误消失，包装边界继续明确报同一类型错误，补齐 `xAddr` 后最终合并修复完成构建与上板。

- 远端最终构建输出 `[100%] Built target op_softmax`（950，证据等级: tool_observed）。
- 终版 NPU pytest 输出 `98 passed, 6 skipped`（950，证据等级: tool_observed）。
- 隔离修补后的 cann-bench 新进程在 `npu:2` 完成 20/20（950，证据等级: tool_observed）。

- 独立复现 R1：工具报告 [100%] Built target op_apply_rotary_pos_emb。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R2：NPU/pytest 报告 59 passed。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R3：工具报告 [100%] Built target op_softmax。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。

## 失效边界

- 只验证 CANN 9.0.1 两参数 LoadAlign/StoreAlign 路径；带 stride/post-update 的其他重载需另查签名。
- 去掉 const 只解决编译 ABI，不声明 kernel 可以写入这些输入区域。
- 本修复与同轮其他编译修复合并后才获得最终成功构建，未做单变更隔离构建。

## 坏实践

- 依据“逻辑只读”给所有 `__ubuf__` 输入加 const，而不看 RegBase ABI。
- 只在 VF 调用点强制转换，保留 `asc_vf_call` 包装边界的 const 类型污染。

## 误诊

这不是 GM/UB 对齐、tail mask 或 Cast 精度问题；编译器在函数重载/包装参数匹配时已经失败。

<!-- cannbot:related:start -->
## 相关

- [AscLoadalign](../../apis/simd_api/c_api/reg/reg_load/asc_loadalign.md)（`exemplifies`）：该构建卡给出 LoadAlign 两参数 ABI 不接受 const __ubuf__ 指针的实测错误和完整调用链修复，是调用该接口时的直接编译诊断。
- [GetPhyAddr](../../apis/simd_api/basic_api/data_structures/local_tensor/get_phy_addr.md)（`exemplifies`）：《Reg LoadAlign 不接受 const __ubuf__ 指针》给出“CANN 9.0.1 RegBase 的两参数 LoadAlign/StoreAlign 要求非 const UB 指针；const 会让 VF 封装与 asc_vf_call 编译失败。”；该约束/探针可直接复现、解释或前置验证《GetPhyAddr》中的“返回LocalTensor的地址或指定偏移量后的地址。”。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_mask_reg.md)（`exemplifies`）：Runbook 实测两参数 Reg LoadAlign 不接受 const __ubuf__ 指针，并追到 asc_vf_call 包装边界；这是调用该搬入族时的直接编译诊断。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_noncontinuous.md)（`exemplifies`）：LoadAlign 与《Reg LoadAlign 不接受 const __ubuf__ 指针》的实质衔接是：非连续 LoadAlign 依赖 mask、地址推进、Store 交接和连续/非连续布局，相关卡片直接覆盖对齐、lane 和同步故障。
- [__isUbuf](../../apis/simt_api/address_space_predicate_functions/_is_ubuf.md)（`exemplifies`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《Reg LoadAlign 不接受 const __ubuf__ 指针》明确“CANN 9.0.1 RegBase 的两参数 LoadAlign/StoreAlign 要求非 const UB 指针；const 会让 VF 封装与 asc_vf_call 编译失败。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [GetPhyAddr const __gm__ 返回不可去 const](getphyaddr_const_gm_const.md)（`related`）：真正需要写指针的 Reg load 路径必须从可写 UB 来源取得，不能对 const GetPhyAddr 强转。
- [中级性能优化](../../guides/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《Reg LoadAlign 不接受 const __ubuf__ 指针》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [__ubuf__ 指针传普通形参导致编译失败](ubuf_pointer_preserves_address_space.md)（`same_topic`）：两卡都把 __ubuf__ 视为指针类型合同的一部分：helper 形参不能退化为普通 T*，而 Reg::LoadAlign 还要求可写的非 const __ubuf__ 指针；丢失任一限定都会导致重载匹配失败。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`same_topic`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Reg LoadAlign 不接受 const __ubuf__ 指针》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
<!-- cannbot:related:end -->
