---
type: "Runbook"
title: "Reg Compare 的 CMPMODE 命名空间导致编译失败"
description: "Reg::Compare 属于 Reg API，但其比较模式枚举仍位于 AscendC 命名空间，写成 Reg::CMPMODE 会编译失败。"
tags: ["task.debugging", "topic.compute.elementwise.comparison_logic"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Reg Compare 的 CMPMODE 命名空间导致编译失败

## 现象

在 `__simd_vf__` 中调用 `AscendC::Reg::Compare` 实现寄存器逐元素比较时，把模板参数写成 `AscendC::Reg::CMPMODE::LT`。远端 bisheng 编译器直接报告：

```text
error: no member named 'CMPMODE' in namespace 'AscendC::Reg';
did you mean 'AscendC::CMPMODE'?
```

函数名位于 `AscendC::Reg` 并不意味着它依赖的所有枚举也位于同一层命名空间。

## 适用场景

- 工程形态：Ascend C kernel 直调构建；
- API 路径：`__simd_vf__` → `AscendC::Reg::Compare<T, mode>`；
- 验证过的平台与 CANN 版本：Ascend950PR_957c / dav-3510，CANN 9.0.1；
- 适用粒度：`platform_wide`，适用于该 SDK 的 RegBase Compare 模板实例化；
- 路线优先级：`recommended_fastpath`，使用 SDK 实际声明的枚举命名空间是已验证可编译形态，不据此宣称性能最优；
- 明确不适用/未验证场景：C API、经典 LocalTensor Compare 与其他 CANN 版本未验证。

## 根因

`Compare` 模板函数声明在 `AscendC::Reg`，但 `CMPMODE` 枚举声明在外层 `AscendC`；按函数命名空间推导枚举命名空间导致查找失败。

## 解决配方

只修正模板枚举的限定名：调用仍是 `AscendC::Reg::Compare`，模式改为 `AscendC::CMPMODE::LT`。下面保留轨迹写入的完整函数 before/after。

### before

代码证据：revision=轨迹修复前快照（源轨迹未绑定 Git revision）；path=`operators/cummin/cummin.asc`；symbol=`cummin_vf`；line=120-171。

```cpp
template <typename ComputeT, typename LoadT>
__simd_vf__ inline void cummin_vf(
    __ubuf__ LoadT *yAddr,         // cur input row r (LoadT)
    __ubuf__ ComputeT *tmpValAddr, // running value (ComputeT, in/out)
    __ubuf__ int32_t *tmpIdxAddr,  // running idx (int32, in/out)
    __ubuf__ LoadT *outValAddr,    // output values row r (LoadT)
    uint32_t count, uint32_t chunkCount, int32_t r)
{
    constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(ComputeT);
    constexpr bool kNeedsCast = !std::is_same<ComputeT, LoadT>::value;
    AscendC::Reg::RegTensor<ComputeT> curReg, runReg;
    AscendC::Reg::RegTensor<int32_t> idxReg, dupReg;
    AscendC::Reg::RegTensor<LoadT> curLoadReg, outLoadReg;

    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg maskT = AscendC::Reg::UpdateMask<ComputeT>(rem);

        // load cur (LoadT) and widen to ComputeT register
        AscendC::Reg::LoadAlign<LoadT, AscendC::Reg::LoadDist::DIST_NORM>(curLoadReg, yAddr + off);
        if constexpr (kNeedsCast) {
            AscendC::Reg::MaskReg castInMask = AscendC::Reg::UpdateMask<ComputeT>(rem);
            AscendC::Reg::Cast<ComputeT, LoadT, kCastToFp32>(curReg, curLoadReg, castInMask);
        } else {
            curReg = curLoadReg;
        }

        AscendC::Reg::LoadAlign<ComputeT, AscendC::Reg::LoadDist::DIST_NORM>(runReg, tmpValAddr + off);
        AscendC::Reg::LoadAlign<int32_t, AscendC::Reg::LoadDist::DIST_NORM>(idxReg, tmpIdxAddr + off);
        AscendC::Reg::Duplicate<int32_t>(dupReg, r);

        AscendC::Reg::MaskReg cmpMask;
        AscendC::Reg::Compare<ComputeT, AscendC::Reg::CMPMODE::LT>(cmpMask, runReg, curReg, maskT);
        AscendC::Reg::Select<ComputeT>(runReg, runReg, curReg, cmpMask);          // run<cur ? run : cur
        AscendC::Reg::Select<int32_t>(idxReg, idxReg, dupReg, cmpMask);            // run<cur ? idx : r

        // output values (LoadT): narrow ComputeT->LoadT register-side
        if constexpr (kNeedsCast) {
            AscendC::Reg::MaskReg castOutMask = AscendC::Reg::UpdateMask<ComputeT>(rem);
            AscendC::Reg::Cast<LoadT, ComputeT, kCastFromFp32>(outLoadReg, runReg, castOutMask);
            AscendC::Reg::MaskReg storeMask = AscendC::Reg::UpdateMask<LoadT>(rem);
            AscendC::Reg::StoreAlign<LoadT, AscendC::Reg::StoreDist::DIST_NORM_B32>(outValAddr + off, outLoadReg, storeMask);
        } else {
            AscendC::Reg::StoreAlign<ComputeT, AscendC::Reg::StoreDist::DIST_NORM_B32>(outValAddr + off, runReg, maskT);
        }

        // writeback running carry (full-register, chunk==VL → no overlap, no corruption)
        AscendC::Reg::StoreAlign<ComputeT, AscendC::Reg::StoreDist::DIST_NORM_B32>(tmpValAddr + off, runReg, maskT);
        AscendC::Reg::StoreAlign<int32_t, AscendC::Reg::StoreDist::DIST_NORM_B32>(tmpIdxAddr + off, idxReg, maskT);
    }
}
```

### after

代码证据：revision=CMPMODE 限定名修复后快照（源轨迹未绑定 Git revision）；path=`operators/cummin/cummin.asc`；symbol=`cummin_vf`；line=120-171。

```cpp
template <typename ComputeT, typename LoadT>
__simd_vf__ inline void cummin_vf(
    __ubuf__ LoadT *yAddr,         // cur input row r (LoadT)
    __ubuf__ ComputeT *tmpValAddr, // running value (ComputeT, in/out)
    __ubuf__ int32_t *tmpIdxAddr,  // running idx (int32, in/out)
    __ubuf__ LoadT *outValAddr,    // output values row r (LoadT)
    uint32_t count, uint32_t chunkCount, int32_t r)
{
    constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(ComputeT);
    constexpr bool kNeedsCast = !std::is_same<ComputeT, LoadT>::value;
    AscendC::Reg::RegTensor<ComputeT> curReg, runReg;
    AscendC::Reg::RegTensor<int32_t> idxReg, dupReg;
    AscendC::Reg::RegTensor<LoadT> curLoadReg, outLoadReg;

    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg maskT = AscendC::Reg::UpdateMask<ComputeT>(rem);

        // load cur (LoadT) and widen to ComputeT register
        AscendC::Reg::LoadAlign<LoadT, AscendC::Reg::LoadDist::DIST_NORM>(curLoadReg, yAddr + off);
        if constexpr (kNeedsCast) {
            AscendC::Reg::MaskReg castInMask = AscendC::Reg::UpdateMask<ComputeT>(rem);
            AscendC::Reg::Cast<ComputeT, LoadT, kCastToFp32>(curReg, curLoadReg, castInMask);
        } else {
            curReg = curLoadReg;
        }

        AscendC::Reg::LoadAlign<ComputeT, AscendC::Reg::LoadDist::DIST_NORM>(runReg, tmpValAddr + off);
        AscendC::Reg::LoadAlign<int32_t, AscendC::Reg::LoadDist::DIST_NORM>(idxReg, tmpIdxAddr + off);
        AscendC::Reg::Duplicate<int32_t>(dupReg, r);

        AscendC::Reg::MaskReg cmpMask;
        AscendC::Reg::Compare<ComputeT, AscendC::CMPMODE::LT>(cmpMask, runReg, curReg, maskT);
        AscendC::Reg::Select<ComputeT>(runReg, runReg, curReg, cmpMask);          // run<cur ? run : cur
        AscendC::Reg::Select<int32_t>(idxReg, idxReg, dupReg, cmpMask);            // run<cur ? idx : r

        // output values (LoadT): narrow ComputeT->LoadT register-side
        if constexpr (kNeedsCast) {
            AscendC::Reg::MaskReg castOutMask = AscendC::Reg::UpdateMask<ComputeT>(rem);
            AscendC::Reg::Cast<LoadT, ComputeT, kCastFromFp32>(outLoadReg, runReg, castOutMask);
            AscendC::Reg::MaskReg storeMask = AscendC::Reg::UpdateMask<LoadT>(rem);
            AscendC::Reg::StoreAlign<LoadT, AscendC::Reg::StoreDist::DIST_NORM_B32>(outValAddr + off, outLoadReg, storeMask);
        } else {
            AscendC::Reg::StoreAlign<ComputeT, AscendC::Reg::StoreDist::DIST_NORM_B32>(outValAddr + off, runReg, maskT);
        }

        // writeback running carry (full-register, chunk==VL → no overlap, no corruption)
        AscendC::Reg::StoreAlign<ComputeT, AscendC::Reg::StoreDist::DIST_NORM_B32>(tmpValAddr + off, runReg, maskT);
        AscendC::Reg::StoreAlign<int32_t, AscendC::Reg::StoreDist::DIST_NORM_B32>(tmpIdxAddr + off, idxReg, maskT);
    }
}
```

## 设计决策

- 仅修正 `CMPMODE` 的限定名，保留 `Reg::Compare` 调用与比较谓词不变；
- 放弃“相关类型都应在 `Reg` 下”的命名空间推断，改以 SDK 声明和编译器候选为准；
- 当前方案按 `recommended_fastpath` 记录，证据只覆盖 API 合规与编译通过。

## 系统信息

- toolchain：CANN 9.0.1，bisheng / ASC CMake；
- 目标：Ascend950PR_957c，`NpuArch=dav-3510`；
- 相关文件：算子 `.asc` 中的 RegBase `__simd_vf__` 比较函数。

## 预防

- 从头文件原型复制 `Reg::Compare` 的模板参数类型，不按函数命名空间猜枚举位置；
- 遇到 `did you mean` 时先核对声明，再做最小限定名修复；
- 编译修复后仍需用边界值与 NaN/相等值验证比较谓词语义，不能把“能编译”当“语义正确”。

## 验证信号

来源是一次 Ascend950 Flash kernel 的远端编译。错误限定名出现两次同型实例化错误；改单行后，下一次编译越过该位置，后续完整 ASC 目标构建成功。

- 修复前构建输出 `no member named 'CMPMODE' in namespace 'AscendC::Reg'` 和编译器候选 `AscendC::CMPMODE`（Ascend950 / CANN 9.0.1，证据等级: tool_observed）；
- 修复后的后续构建输出 `[100%] Linking ASC shared library` 与 `[100%] Built target`（Ascend950 / CANN 9.0.1，证据等级: tool_observed）。

## 失效边界

本卡只解决 C++ 名称查找，不判断该比较模式是否符合算子相等值、NaN 或 Inf 语义。A2/A3 与其他 CANN 版本未验证，推断可迁移时须重新核对头文件。

## 坏实践

- 根据 `Reg::Compare` 的函数名机械写成 `Reg::CMPMODE`；
- 为消除错误改掉比较谓词本身，例如把 `LT` 换成另一个可编译模式，从而掩盖语义变化。
