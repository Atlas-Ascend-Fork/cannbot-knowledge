---
type: "Runbook"
title: "Reg CastTrait RoundMode 命名空间编译失败"
description: "dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。"
tags: ["task.debugging", "topic.compute.elementwise.type_conversion", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Reg CastTrait RoundMode 命名空间编译失败

## 现象

在 flash 单 TU 直调工程中编译一个 dav-3510 原生 Reg kernel。`softmax.asc` 的 `__simd_vf__` 函数把 fp16/bf16 上下转换所需的 `AscendC::Reg::CastTrait` 声明为函数内 `static constexpr`；当时 `RegLayout`、`SatMode`、`MaskMergeMode` 与 `RoundMode` 都被写在 `AscendC::Reg` 下。

远程 CANN 9.0.1 构建在 ASC object 阶段原样报错：

```text
softmax.asc:99:47: error: no member named 'RoundMode' in namespace 'AscendC::Reg'; did you mean 'AscendC::RoundMode'?
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::Reg::RoundMode::UNKNOWN};
                                              ^~~~~~~~~~~~~~~~~~~~~~~
                                              AscendC::RoundMode
/usr/local/Ascend/cann-9.0.1/x86_64-linux/tikcpp/tikcfw/impl/utils/kernel_utils_mode.h:103:12: note: 'AscendC::RoundMode' declared here
enum class RoundMode : uint8_t {
           ^
softmax.asc:102:47: error: no member named 'RoundMode' in namespace 'AscendC::Reg'; did you mean 'AscendC::RoundMode'?
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::Reg::RoundMode::CAST_RINT};
                                              ^~~~~~~~~~~~~~~~~~~~~~~
                                              AscendC::RoundMode
2 errors generated.
gmake[2]: *** [CMakeFiles/op_softmax.dir/softmax.asc.o] Error 1
```

这不是 Cast 模板参数顺序、尾块 mask 或计算逻辑错误；名字查找在编译期已经失败，kernel 尚未生成。

## 适用场景

- 工程形态：Ascend C flash 单 TU kernel 直调，`__simd_vf__` 内声明 Reg Cast trait；
- API 路径：`AscendC::Reg::CastTrait` 作为 `AscendC::Reg::Cast` 的 trait 参数，同时使用 `RegLayout`、`SatMode`、`MaskMergeMode` 和 `RoundMode`；
- 验证过的平台与版本：950（Ascend950PR_957b / dav-3510）+ CANN 9.0.1，与 frontmatter `platforms` 一致；
- 适用粒度：`operator_family`，适用于同一工具链上所有用 `Reg::CastTrait` 做 Reg dtype 转换的 kernel；
- 路线优先级：`recommended_fastpath`，只修正编译器已定位的枚举命名空间，不改变 cast 路径或计算序列；
- 明确不适用或未验证：其他 CANN 版本、其他 NPU 架构以及没有使用 `Reg::CastTrait` 的 kernel 未验证，必须以目标环境头文件声明为准。

## 根因

`CastTrait` 类型位于 `AscendC::Reg`，不表示它的全部字段枚举也嵌套在 `Reg`。在本次 CANN 9.0.1 头文件中，`RegLayout`、`SatMode` 和 `MaskMergeMode` 属于 `AscendC::Reg`，但 `RoundMode` 的声明位于外层 `AscendC`。因此编译器解析 `AscendC::Reg::RoundMode` 时在名字查找阶段失败；枚举值尚未参与模板实例化。

机制链为：

```text
CastTrait 属于 AscendC::Reg
  ≠ 每个字段枚举都属于 AscendC::Reg
  → RoundMode 实际声明为 AscendC::RoundMode
  → AscendC::Reg::RoundMode 名字查找失败
  → softmax.asc.o 不生成，gmake 终止
```

## 解决配方

只把两个 `RoundMode` 限定名从 `AscendC::Reg` 提升到 `AscendC`；其余 Reg 枚举、trait 的函数内 `static constexpr` 形态和三段计算逻辑全部保留。

### before

证据定位：revision `d554da5f1532471d098f3f7ab67ca884edfae273`；path `operators/softmax/softmax.asc`；symbol `softmax_row_vf<T>`；lines 79–180。可执行定位：

```bash
git show d554da5f1532471d098f3f7ab67ca884edfae273:operators/softmax/softmax.asc
```

该完整函数支撑“错误限定名位于真实 CastTrait 声明与三个 Cast 调用共同使用的代码路径中”这一结论：

```cpp
__simd_vf__ inline void softmax_row_vf(
    __ubuf__ T *yAddr, __ubuf__ T *xAddr, uint32_t dLen, uint32_t chunkCount)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> fReg;
    AscendC::Reg::RegTensor<float> maxReg;
    AscendC::Reg::RegTensor<float> maxRedReg;
    AscendC::Reg::RegTensor<float> maxBroadReg;
    AscendC::Reg::RegTensor<float> sumReg;
    AscendC::Reg::RegTensor<float> sumRedReg;
    AscendC::Reg::RegTensor<float> sumBroadReg;
    AscendC::Reg::RegTensor<float> chunkRedReg;
    AscendC::Reg::RegTensor<float> chunkBroadReg;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();

    // CastTrait (see file header): in-__simd_vf__ construction is the only place
    // the Reg enumerators are nameable. mrgMode=ZEROING is required by the device
    // static_assert on dav-3510/dav-c310.
    static constexpr AscendC::Reg::CastTrait CAST_UP = {
        AscendC::Reg::RegLayout::ZERO, AscendC::Reg::SatMode::UNKNOWN,
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::Reg::RoundMode::UNKNOWN};
    static constexpr AscendC::Reg::CastTrait CAST_DOWN = {
        AscendC::Reg::RegLayout::ZERO, AscendC::Reg::SatMode::NO_SAT,
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::Reg::RoundMode::CAST_RINT};

    AscendC::Reg::Duplicate(maxReg, SOFTMAX_NEG_INF, fullMask);
    AscendC::Reg::Duplicate(sumReg, 0.0f, fullMask);

    // Pass 1: row max. Per chunk: Reduce<MAX> over the mask-selected (active)
    // lanes only, then broadcast the chunk max and accumulate with a FULL-mask
    // Max. The full-mask Max with the broadcast chunk-max touches every lane
    // uniformly, so the accumulator is never corrupted and the true row max is
    // obtained (important for the large-value cases that would overflow exp).
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkRedReg, fReg, mask);
        AscendC::Reg::Duplicate(chunkBroadReg, chunkRedReg, fullMask);
        AscendC::Reg::Max(maxReg, maxReg, chunkBroadReg, fullMask);
    }
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(maxRedReg, maxReg, fullMask);
    AscendC::Reg::Duplicate(maxBroadReg, maxRedReg, fullMask);

    // Pass 2: (x - max), exp, accumulate sum (no tmp store). Sub/Exp run on the
    // partial tail mask with ZEROING (inactive fReg lanes -> 0); the Add then
    // uses the FULL mask, adding 0 to inactive accumulator lanes (no-op) and exp
    // to active lanes. Final Reduce<SUM> over the full register = the row sum.
    // Div has no (s>0)?1/s:0 guard: NaN sum propagates NaN, +inf sum -> 0
    // (field-note scalar-reciprocal-guard-hides-nan).
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Sub(fReg, fReg, maxBroadReg, mask);
        AscendC::Reg::Exp(fReg, fReg, mask);
        AscendC::Reg::Add(sumReg, sumReg, fReg, fullMask);
    }
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(sumRedReg, sumReg, fullMask);
    AscendC::Reg::Duplicate(sumBroadReg, sumRedReg, fullMask);

    // Pass 3: recompute exp(x - max), divide by sum, cast down, store y.
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Sub(fReg, fReg, maxBroadReg, mask);
        AscendC::Reg::Exp(fReg, fReg, mask);
        AscendC::Reg::Div(fReg, fReg, sumBroadReg, mask);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(yAddr + offset, fReg, mask);
        } else {
            AscendC::Reg::RegTensor<T> outReg;
            AscendC::Reg::Cast<T, float, CAST_DOWN>(outReg, fReg, mask);
            AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(yAddr + offset, outReg, mask);
        }
    }
}
```

### after

证据定位：revision `ca6b80c4ec1dff19fbb6ce9467373ec16314bd02`；path `operators/softmax/softmax.asc`；symbol `softmax_row_vf<T>`；lines 79–180。可执行定位：

```bash
git show ca6b80c4ec1dff19fbb6ce9467373ec16314bd02:operators/softmax/softmax.asc
```

该完整函数支撑“仅更换 RoundMode 限定名即可让同一 CastTrait 与三个 Cast 调用通过编译并运行”这一结论。它由完整写入版本加轨迹中的两个精确字符串替换确定性重建：

```cpp
__simd_vf__ inline void softmax_row_vf(
    __ubuf__ T *yAddr, __ubuf__ T *xAddr, uint32_t dLen, uint32_t chunkCount)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> fReg;
    AscendC::Reg::RegTensor<float> maxReg;
    AscendC::Reg::RegTensor<float> maxRedReg;
    AscendC::Reg::RegTensor<float> maxBroadReg;
    AscendC::Reg::RegTensor<float> sumReg;
    AscendC::Reg::RegTensor<float> sumRedReg;
    AscendC::Reg::RegTensor<float> sumBroadReg;
    AscendC::Reg::RegTensor<float> chunkRedReg;
    AscendC::Reg::RegTensor<float> chunkBroadReg;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::CreateMask<float>();

    // CastTrait (see file header): in-__simd_vf__ construction is the only place
    // the Reg enumerators are nameable. mrgMode=ZEROING is required by the device
    // static_assert on dav-3510/dav-c310.
    static constexpr AscendC::Reg::CastTrait CAST_UP = {
        AscendC::Reg::RegLayout::ZERO, AscendC::Reg::SatMode::UNKNOWN,
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::RoundMode::UNKNOWN};
    static constexpr AscendC::Reg::CastTrait CAST_DOWN = {
        AscendC::Reg::RegLayout::ZERO, AscendC::Reg::SatMode::NO_SAT,
        AscendC::Reg::MaskMergeMode::ZEROING, AscendC::RoundMode::CAST_RINT};

    AscendC::Reg::Duplicate(maxReg, SOFTMAX_NEG_INF, fullMask);
    AscendC::Reg::Duplicate(sumReg, 0.0f, fullMask);

    // Pass 1: row max. Per chunk: Reduce<MAX> over the mask-selected (active)
    // lanes only, then broadcast the chunk max and accumulate with a FULL-mask
    // Max. The full-mask Max with the broadcast chunk-max touches every lane
    // uniformly, so the accumulator is never corrupted and the true row max is
    // obtained (important for the large-value cases that would overflow exp).
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkRedReg, fReg, mask);
        AscendC::Reg::Duplicate(chunkBroadReg, chunkRedReg, fullMask);
        AscendC::Reg::Max(maxReg, maxReg, chunkBroadReg, fullMask);
    }
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(maxRedReg, maxReg, fullMask);
    AscendC::Reg::Duplicate(maxBroadReg, maxRedReg, fullMask);

    // Pass 2: (x - max), exp, accumulate sum (no tmp store). Sub/Exp run on the
    // partial tail mask with ZEROING (inactive fReg lanes -> 0); the Add then
    // uses the FULL mask, adding 0 to inactive accumulator lanes (no-op) and exp
    // to active lanes. Final Reduce<SUM> over the full register = the row sum.
    // Div has no (s>0)?1/s:0 guard: NaN sum propagates NaN, +inf sum -> 0
    // (field-note scalar-reciprocal-guard-hides-nan).
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Sub(fReg, fReg, maxBroadReg, mask);
        AscendC::Reg::Exp(fReg, fReg, mask);
        AscendC::Reg::Add(sumReg, sumReg, fReg, fullMask);
    }
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(sumRedReg, sumReg, fullMask);
    AscendC::Reg::Duplicate(sumBroadReg, sumRedReg, fullMask);

    // Pass 3: recompute exp(x - max), divide by sum, cast down, store y.
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = dLen - offset;
        uint32_t active = (remaining > vectorLength) ? vectorLength : remaining;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(active);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(fReg, xAddr + offset);
        } else {
            AscendC::Reg::RegTensor<T> srcReg;
            AscendC::Reg::LoadAlign<T, AscendC::Reg::LoadDist::DIST_UNPACK_B16>(srcReg, xAddr + offset);
            AscendC::Reg::Cast<float, T, CAST_UP>(fReg, srcReg, mask);
        }
        AscendC::Reg::Sub(fReg, fReg, maxBroadReg, mask);
        AscendC::Reg::Exp(fReg, fReg, mask);
        AscendC::Reg::Div(fReg, fReg, sumBroadReg, mask);
        if constexpr (std::is_same_v<T, float>) {
            AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(yAddr + offset, fReg, mask);
        } else {
            AscendC::Reg::RegTensor<T> outReg;
            AscendC::Reg::Cast<T, float, CAST_DOWN>(outReg, fReg, mask);
            AscendC::Reg::StoreAlign<T, AscendC::Reg::StoreDist::DIST_PACK_B32>(yAddr + offset, outReg, mask);
        }
    }
}
```

## 设计决策

- 选择只更换 `RoundMode` 的命名空间，因为编译器同时给出失败限定名、正确限定名和头文件声明位置；这是能解释两处报错的最小机制修复。
- 放弃“保留 `Reg::RoundMode`、只换枚举值”的候选，因为失败发生在 `RoundMode` 类型名字查找阶段，枚举值尚未被解析，换值不能解决根因。
- 未把整个 cast 路径改成 host staging，也未移动 function-local `CastTrait`：这会扩大修改面，而命名空间修复后原 Reg cast 路径已通过构建和上板验证。
- 当前方案属于 `recommended_fastpath`：保持原计算与 cast 结构，只有编译期限定名变化。

## 系统信息

- toolchain：CANN 9.0.1，Bisheng/ASC 编译链；
- 目标：Ascend950PR_957b，NpuArch=dav-3510，frontmatter 平台 `950`；
- 工程：flash 单 TU 直调，`softmax.asc` 同时承载 device kernel 与 host 注册；
- 相关文件：`operators/softmax/softmax.asc`；构建入口为 `operators/softmax/CMakeLists.txt`；验证入口为 `operators/softmax/test_softmax.py`；
- 固定源码状态：before `d554da5f1532471d098f3f7ab67ca884edfae273`，after `ca6b80c4ec1dff19fbb6ce9467373ec16314bd02`。

## 预防

- 不要因为 trait 类型位于 `AscendC::Reg`，就推断其全部字段枚举也位于 `Reg`；逐个核对目标 CANN 头文件的声明位置。
- 看到 `did you mean` 且同时给出声明文件/行号时，先按名字查找层修复，不要先改模板参数顺序或计算代码。
- 对 `CastTrait` 做版本适配时，至少检查 `RegLayout`、`SatMode`、`MaskMergeMode`、`RoundMode` 四个字段各自的真实命名空间。
- 修复后必须重新编译包含 fp16/bf16 Cast 实例化的目标，并在 NPU 上执行实际 cast 路径；仅有 fp32 路径通过不能证明 trait 正确。

## 验证信号

本知识来自一次 Ascend950 flash 直调算子开发：首次 CANN 9.0.1 构建在两个 CastTrait 字段处失败，按编译器声明位置修正限定名后完成重新构建、独立 cast probe、清理重建与最终验收。

- 两处 `AscendC::Reg::RoundMode` 均产生同一名字查找错误，编译器指向 `kernel_utils_mode.h` 中的 `AscendC::RoundMode` 声明（950 / CANN 9.0.1，证据等级: tool_observed）。
- 修复后 ASC object 编译完成并链接唯一目标共享库（950 / CANN 9.0.1，证据等级: artifact_verified）。
- 独立 NPU probe 的 fp16 cast 路径 `maxdiff=0.0`，bf16 cast 路径成功运行（950，证据等级: tool_observed）。
- 清理远程构建目录后重新构建，NPU pytest 的全部 71 项通过（950，证据等级: tool_observed）。
- 最终 cann-bench 精度验收全部 20 个 case 通过（950，证据等级: tool_observed）。

- 独立复现 R1：工具报告 [100%] Built target op_softmax。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R2：工具报告 [100%] Built target op_rms_norm。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R3：工具报告 [100%] Built target op_softmax。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。

## 失效边界

- 本卡只证明 CANN 9.0.1 / dav-3510 的名字空间契约；其他 CANN 版本和其他平台未验证，推断可迁移前必须先检查目标 `kernel_utils_mode.h`。
- 本卡不规定具体 `RoundMode` 枚举值应选 `UNKNOWN`、`CAST_RINT` 或其他模式；枚举值由 dtype 转换语义决定，本卡只处理枚举类型的限定名。
- 不使用 `AscendC::Reg::CastTrait` 的 classic AscendC、SIMT 或 host cast 路径不适用。

## 坏实践

- 把 `AscendC::Reg::CastTrait` 的所属命名空间机械传播给所有字段枚举；类型聚合位置与枚举声明位置不是同一契约。
- 在类型名字查找已经失败时反复更换枚举值、mask 或计算顺序；这些修改发生在错误阶段之后，无法让编译器找到 `RoundMode`。

## 误诊

- 把该错误当作 fp16/bf16 精度或 runtime 问题会走偏：构建尚未生成 ASC object，没有任何 kernel 运行结果可供精度归因。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../apis/simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [CastFloatToHalfInt32](../../apis/simd_api/basic_api/scalar_compute/cast_float_to_half_int32.md)（`exemplifies`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
- [MaskMergeMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/mask_merge_mode.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《MaskMergeMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [RoundMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/round_mode.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《RoundMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [SatMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/sat_mode.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《SatMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [AscendC 标量类型误加命名空间导致模板分发编译失败](device_half_bfloat16_types_are_global.md)（`related`）：Reg CastTrait RoundMode 命名空间编译失败 与《AscendC 标量类型误加命名空间导致模板分发编译失败》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](../precision/b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Reg CastTrait RoundMode 命名空间编译失败》说明dav-3510 Reg CastTrait 的 RoundMode 枚举不在 Reg 子命名空间；按编译器声明位置改用 AscendC::RoundMode 后恢复构建。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [CastTrait 文件域声明触发命名空间编译失败](reg_casttrait_define_inside_simd_vf.md)（`related`）：两卡都从 CastTrait“not in namespace”类错误出发，但该卡定位 RoundMode 实际位于 AscendC 外层，可与本卡的文件域/设备函数词法可见性诊断区分。
- [FP16 算子 Cast 提升-计算-回退链设计](../precision/fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《Reg CastTrait RoundMode 命名空间编译失败》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](../precision/bf16_cast_cast_rint.md)（`related`）：Reg CastTrait RoundMode 命名空间编译失败 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [CastTrait 按值 NTTP 在 C++17 编译失败](casttrait_nttp_uses_reference_in_cxx17.md)（`same_topic`）：Reg CastTrait RoundMode 命名空间编译失败 与《CastTrait 按值 NTTP 在 C++17 编译失败》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](reg_cast_requires_explicit_zeroing_trait.md)（`same_topic`）：Reg CastTrait RoundMode 命名空间编译失败 与《Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [Reg Compare 的 CMPMODE 命名空间导致编译失败](reg_compare_cmpmode_is_in_ascendc.md)（`same_topic`）：Compare 的 CMPMODE 与 Cast 的 RoundMode 都说明函数位于 AscendC::Reg 不代表枚举也在 Reg；枚举实际位于 AscendC。
- [Reg::Cast 的 trait 需要静态存储期](reg_casttrait_requires_static_storage.md)（`same_topic`）：Reg CastTrait RoundMode 命名空间编译失败 与《Reg::Cast 的 trait 需要静态存储期》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](reg_cast_f32_to_s64_uses_supported_rounding.md)（`same_topic`）：Reg CastTrait RoundMode 命名空间编译失败 与《f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
<!-- cannbot:related:end -->
