---
type: "Runbook"
title: "RegTensor 累加须用 Add 而非 Adds"
description: "Reg Adds 的第三操作数是标量，归约结果寄存器参与累加时应改用寄存器对寄存器 Add。"
tags: ["task.debugging", "topic.implementation.api_layer.basic_api", "topic.compute.elementwise.arithmetic"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# RegTensor 累加须用 Add 而非 Adds

## 现象

在 CANN 9.0.1 的 flash 单文件 kernel 直调工程里，平方和归约把 `Reduce` 产生的 `RegTensor<float>` 累加进寄存器时写成 `AscendC::Reg::Adds(accReg, accReg, scalarReg, scalarMask)`。编译器进入 binary-scalar 实现后报：

```text
static assertion failed: current scalarValue data type is not supported on current device!
static assertion failed: scalarValue data type could be converted to RegTensor data type
error: no matching function for call to 'vadds'
```

## 适用场景

- 工程形态：Ascend C flash 单文件 kernel 直调构建；
- API 路径：`__simd_vf__` 中 `Reduce` 结果寄存器的跨 chunk 累加，涉及 `AscendC::Reg::Add` / `Adds`；
- 验证过的平台与版本：950（dav-3510）/ CANN 9.0.1，与 frontmatter `platforms` 一致；
- 适用粒度：`platform_wide`，适用于同 SDK 下任何把寄存器结果作为第三操作数的 Reg 二元运算；
- 路线优先级：`recommended_fastpath`，寄存器对寄存器累加直接调用 `Add`；
- 明确不适用或未验证：第三操作数本来就是 C++ 标量时仍应使用 `Adds`；A2、A3 和其他 CANN 版本未验证。

## 根因

`Adds` 是向量加标量接口，其第三个数据参数是 `scalarValue`。把 `RegTensor<float>` 传入后，模板会尝试把整个寄存器类型当成标量，随后触发 SupportType、可转换性和底层 `vadds` 重载检查。`Add` 的第三个数据参数才是寄存器引用，因此归约得到的单值寄存器即使只有 lane 0 有效，类型仍决定它必须走 `Add`。

## 解决配方

保留 scalar mask，把累加指令从 `Adds` 改成 `Add`。下面是失败和修复后完整函数；同轮的 mask 左值和 dtype 路线变化属于其他独立闭环，本卡只采用 `Adds` → `Add` 这一技术结论。

### before

代码证据：revision `49e5159e931ecc6a3c1dd38c365a6c6975f53861`（事件内完整源码的 Git blob id）；path `operators/rms_norm/rms_norm.asc`；symbol `reduce_sq_vf`；lines 55-91。该块支撑“RegTensor 被误传为 Adds 标量参数”的失败调用点；公开 blob URL 未包含在轨迹中，正式落库前需补导航。

```cpp
template <typename T>
__simd_vf__ inline void reduce_sq_vf(__ubuf__ float *sumSqAddr, __ubuf__ T *xAddr,
                                     uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    constexpr uint32_t reduceElems = 32 / sizeof(float);
    AscendC::Reg::MaskReg scalarMask = AscendC::Reg::UpdateMask<float>(1);

    AscendC::Reg::RegTensor<float> accReg;
    AscendC::Reg::Duplicate<float>(accReg, 0.0f, scalarMask);

    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = count - offset;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);

        AscendC::Reg::RegTensor<float> xFReg;
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xFReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> xReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(xReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP_B16>(xFReg, xReg, mask);
        }

        AscendC::Reg::RegTensor<float> sqReg;
        AscendC::Reg::Mul(sqReg, xFReg, xFReg, mask);            // x^2

        AscendC::Reg::RegTensor<float> scalarReg;
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM, float, float>(scalarReg, sqReg, mask);
        AscendC::Reg::Adds(accReg, accReg, scalarReg, scalarMask); // accumulate lane 0
    }

    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        sumSqAddr, accReg, scalarMask);
}
```

### after

代码证据：revision `2e622ced93d858e24f17ffb24436b335bc0b2640`（事件内完整源码的 Git blob id）；path `operators/rms_norm/rms_norm.asc`；symbol `reduce_sq_vf`；lines 43-71。该块支撑“寄存器结果通过 Add 累加”的修复；公开 blob URL 未包含在轨迹中，正式落库前需补导航。

```cpp
__simd_vf__ inline void reduce_sq_vf(__ubuf__ float *sumSqAddr, __ubuf__ float *xAddr,
                                     uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t scalarCount = 1;
    AscendC::Reg::MaskReg scalarMask = AscendC::Reg::UpdateMask<float>(scalarCount);

    AscendC::Reg::RegTensor<float> accReg;
    AscendC::Reg::Duplicate<float>(accReg, 0.0f);

    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = count - offset;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);

        AscendC::Reg::RegTensor<float> xReg;
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, xAddr + offset);

        AscendC::Reg::RegTensor<float> sqReg;
        AscendC::Reg::Mul(sqReg, xReg, xReg, mask);            // x^2

        AscendC::Reg::RegTensor<float> scalarReg;
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM, float, float>(scalarReg, sqReg, mask);
        AscendC::Reg::Add(accReg, accReg, scalarReg, scalarMask); // accumulate lane 0
    }

    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
        sumSqAddr, accReg, scalarMask);
}
```

## 设计决策

- 根据操作数类型选接口：第三操作数是寄存器时用 `Add`，是 C++ 标量时用 `Adds`；
- 不尝试从 `scalarReg` 回取 host/scalar 值，因为归约结果已在 Reg 数据通路内，改用 `Add` 避免额外数据移动；
- 当前方案是 `recommended_fastpath`，保持寄存器内累加路径。

## 预防

- 看到带 `s` 的 Reg 二元接口时先核对 scalar 形参，不要把“寄存器里只有一个有效 lane”误等同于 C++ 标量；
- 根据调用点第三操作数类型查 `kernel_reg_compute_vec_binary_intf.h` 和 `kernel_reg_compute_vec_binary_scalar_intf.h`；
- `SupportType<RegTensor,...>` 与 `vadds` 同时出现时，优先检查是否把寄存器误传给 scalarValue。

## 验证信号

本知识来自 Ascend 950 上一次 Reg 归约累加的编译联调，接口声明、错误链和修复后构建均由工具直接记录。

- SDK 头文件输出 `Add(... srcReg1, mask)` 与 `Adds(... scalarValue, mask)` 两组签名（950，证据等级: tool_observed）；
- 改为 `Add` 后下一次编译不再出现 `SupportType<RegTensor...>` 与 `no matching function for call to 'vadds'`，只剩独立的 Cast 错误（950，证据等级: tool_observed）；
- 最终构建输出 `[100%] Built target op_rms_norm`（950，证据等级: artifact_verified）。

## 失效边界

本卡只覆盖寄存器对寄存器的加法累加。若第三操作数来自函数参数或立即数且类型确为标量，`Adds` 仍是正确接口。其他 CANN 版本及 A2/A3 未验证。

## 坏实践

为了保留 `Adds` 而强转 `RegTensor` 会掩盖类型语义，且不能生成合法的 `vadds` 标量操作数；也不要因为归约只关心 lane 0 就把寄存器类型误判成标量类型。

## 误诊

静态断言中的“current device”容易让人误判为硬件不支持 float。实际不支持的是被错误推导为 `scalarValue` 的 `RegTensor` 类型，而不是 float 数据类型。