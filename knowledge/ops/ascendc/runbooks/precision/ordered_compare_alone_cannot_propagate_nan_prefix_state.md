---
type: "Runbook"
title: "累计极值 NaN 语义须用 self-NE 合成选择掩码"
description: "累计极值 Vector scan 在有限值全部正确、全 NaN 输入却同时出现 NaN 位置和索引失配时，用显式 is-current-NaN、is-running-NaN 与有限 LE 合成选择掩码。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.comparison_logic", "topic.compute.reduction", "topic.implementation.masking"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 累计极值 NaN 语义须用 self-NE 合成选择掩码

## 现象

一个 Ascend C 累积极小值 kernel 在 Ascend 950 上完成构建和大多数精度检查后，全量评测只剩全 NaN 输入失败：values 报 NaN 位置不匹配，indices 则有大量元素不一致。有限值、全零、Inf、非对齐和多个 dtype 的其它检查都已通过，因此继续调整 tiling、搬运或一般有限值比较方向不能解释这个单一失败面。

失败时 `op_kernel/<op>_kernel.cpp` 沿扫描轴只生成一份 `running < current` 掩码：bit 为 1 时保留 running 和旧索引，否则取 current 和当前索引。这在有限数平局时能实现最后出现语义，却把 NaN 传播和 NaN 索引语义隐含地交给了裸有序比较结果。

目标语义必须区分三种状态：current 是 NaN 时总取 current；running 已是 NaN 而 current 有限时保留 running；两者有限时在 `current <= running` 时取 current。全 NaN 前缀还要求每个位置更新为当前 NaN，使索引保持最后出现位置。

## 适用场景

- 工程形态：Ascend C kernel 直调中的逐 lane 累积极值 Vector scan。
- API 路径：`Compare(..., NE)` 自反比较检测 NaN，`Compare(..., LE)` 处理有限值，`Not` / `And` / `Or` 合成 bit-mask，再由 `Select` 同步更新 value 与 index。
- 验证过的平台与 CANN 版本：Ascend 950，CANN 9.0.1；实测修复路径为 half/float。
- 适用粒度：`operator_family`，适用于需要显式 NaN 传播且平局取最后出现位置的累计极小/累计极大或相似 scan；极大值需相应替换有限值比较方向。
- 路线优先级：`recommended_fastpath`。它是本 trace 中唯一通过全 NaN、混合 NaN、有限平局及全量精度评测的显式谓词路线；没有与其它正确 NaN 实现做性能排序，不外推通用性能收益。
- 不适用 / 未验证：NaN 策略不同、平局取首次出现、dtype 不支持相同 Compare/bit-mask API、或只需要 unordered 比较标志的场景不能直接套用；BF16 NaN、A2、A3 未验证。

## 根因

有限值选择可由一个有序比较表达，但 NaN 传播是额外的状态机语义。裸 `running < current` 不能同时编码： 1. current 为 NaN 时，无条件更新 value 和 index； 2. running 为 NaN、current 有限时，保持已传播的 NaN 与最近 NaN 索引； 3. 两者有限时，`current <= running` 才更新，以保留平局的最后出现位置。 修复把选择条件显式写成： `take_current = isCurNan OR ((NOT isRunNan) AND (current LE running))` 其中 `isCurNan` 和 `isRunNan` 都由 `Compare(t, t, NE)` 生成。虽然 `LE` 仍对整块执行，但 running 为 NaN 的位置会被 `NOT isRunNan` 屏蔽，current 为 NaN 的位置则由 `isCurNan` 强制取 current，因此最终 `Select` 不依赖 NaN 有序比较位。

## 解决配方

以下 before 是失败版本的完整 `ScanChunk`，after 是修复写入中的完整 `ScanChunk` 和新 `UpdateRunning`；均由 trace 的文件事件原样恢复。

### before

代码证据：revision = 修复前最近一次完整文件读取快照（无 Git commit，固定事件锚点仅存 manifest）；path = `example/csrc/ops/<op>/op_kernel/<op>_kernel.cpp`；symbol = `KernelCummin<X>::ScanChunk`；line_range = 函数完整体。

```cpp
    __aicore__ inline void ScanChunk(int64_t m, int64_t n0, int64_t chunkLen)
    {
        // row k 的 GM offset (chunkLen 个连续元素): m*R*N + k*N + n0
        int64_t rowBase = m * R_ * N_ + n0;
        int64_t rowStride = N_;  // 行间步长

        // 加载 row 0 → init running
        CopyInRow(rowBase, chunkLen);
        auto y0 = yQue_.template DeQue<X>();
        AscendC::DataCopy(tmpX_, y0, alignedCount_);
        AscendC::Duplicate(tmpArg_, static_cast<int32_t>(0),
                           static_cast<int32_t>(alignedCount_));
        yQue_.FreeTensor(y0);

        // 写 row 0 输出
        CopyOutRow(m, n0, 0, chunkLen);

        // 顺序 scan row 1..R-1
        for (int64_t k = 1; k < R_; ++k) {
            int64_t offset = rowBase + k * rowStride;
            CopyInRow(offset, chunkLen);
            auto yRow = yQue_.template DeQue<X>();

            // bit=1 当 running < current
            AscendC::Compare(mask_, tmpX_, yRow, AscendC::CMPMODE::LT,
                             static_cast<uint32_t>(alignedCount_));
            // bit=1 保留 running, bit=0 取 current (后出现语义)
            AscendC::Select(minDst_, mask_, tmpX_, yRow,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpX_, minDst_, alignedCount_);

            AscendC::Duplicate(kRow_, static_cast<int32_t>(k),
                               static_cast<int32_t>(alignedCount_));
            AscendC::Select(argDst_, mask_, tmpArg_, kRow_,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpArg_, argDst_, alignedCount_);

            yQue_.FreeTensor(yRow);

            CopyOutRow(m, n0, k, chunkLen);
        }
    }
```

### after

代码证据：revision = NaN 修复的终版文件写入快照（无 Git commit，固定事件锚点仅存 manifest）；path = `example/csrc/ops/<op>/op_kernel/<op>_kernel.cpp`；symbols = `KernelCummin<X>::ScanChunk`, `KernelCummin<X>::UpdateRunning`；line_range = 两个函数完整体。

```cpp
    __aicore__ inline void ScanChunk(int64_t m, int64_t n0, int64_t chunkLen)
    {
        // row k 的 GM offset (chunkLen 个连续元素): m*R*N + k*N + n0
        int64_t rowBase = m * R_ * N_ + n0;
        int64_t rowStride = N_;  // 行间步长

        // 加载 row 0 → init running
        CopyInRow(rowBase, chunkLen);
        auto y0 = yQue_.template DeQue<X>();
        AscendC::DataCopy(tmpX_, y0, alignedCount_);
        AscendC::Duplicate(tmpArg_, static_cast<int32_t>(0),
                           static_cast<int32_t>(alignedCount_));
        yQue_.FreeTensor(y0);

        // 写 row 0 输出
        CopyOutRow(m, n0, 0, chunkLen);

        // 顺序 scan row 1..R-1
        for (int64_t k = 1; k < R_; ++k) {
            int64_t offset = rowBase + k * rowStride;
            CopyInRow(offset, chunkLen);
            auto yRow = yQue_.template DeQue<X>();

            UpdateRunning(yRow, k);

            yQue_.FreeTensor(yRow);
            CopyOutRow(m, n0, k, chunkLen);
        }
    }

    // NaN-safe 谓词 (half/float) vs 原 LT 谓词 (bf16/int32)
    __aicore__ inline void UpdateRunning(
        const AscendC::LocalTensor<X>& yRow, int64_t k)
    {
        if constexpr (kNanAwareV<X>) {
            // mask2 = isCurNan = self-NE(current)
            AscendC::Compare(mask2_, yRow, yRow, AscendC::CMPMODE::NE,
                            static_cast<uint32_t>(alignedCount_));
            // mask3 = isRunNan = self-NE(running)
            AscendC::Compare(mask3_, tmpX_, tmpX_, AscendC::CMPMODE::NE,
                            static_cast<uint32_t>(alignedCount_));
            // mask4 = LE(current, running)  (NaN 位垃圾, 下面被 AND 屏蔽)
            AscendC::Compare(mask4_, yRow, tmpX_, AscendC::CMPMODE::LE,
                            static_cast<uint32_t>(alignedCount_));
            // mask_ = NOT isRunNan
            AscendC::Not(mask_, mask3_, static_cast<int32_t>(maskBytes_));
            // mask3 = (NOT isRunNan) AND LE   (复用 mask3 作 dst)
            AscendC::And(mask3_, mask_, mask4_, static_cast<int32_t>(maskBytes_));
            // mask_ = take_current = isCurNan OR ((NOT isRunNan) AND LE)
            AscendC::Or(mask_, mask3_, mask2_, static_cast<int32_t>(maskBytes_));

            // bit=1 → 取 current; src0=yRow(current), src1=tmpX_(running)
            AscendC::Select(minDst_, mask_, yRow, tmpX_,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpX_, minDst_, alignedCount_);

            AscendC::Duplicate(kRow_, static_cast<int32_t>(k),
                               static_cast<int32_t>(alignedCount_));
            // bit=1 → 取 k; src0=kRow, src1=tmpArg_
            AscendC::Select(argDst_, mask_, kRow_, tmpArg_,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpArg_, argDst_, alignedCount_);
        } else {
            // 原 LT 谓词: bit=1 当 running<current → 保留 running (后出现语义)
            AscendC::Compare(mask_, tmpX_, yRow, AscendC::CMPMODE::LT,
                             static_cast<uint32_t>(alignedCount_));
            // bit=1 保留 running, bit=0 取 current
            AscendC::Select(minDst_, mask_, tmpX_, yRow,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpX_, minDst_, alignedCount_);

            AscendC::Duplicate(kRow_, static_cast<int32_t>(k),
                               static_cast<int32_t>(alignedCount_));
            AscendC::Select(argDst_, mask_, tmpArg_, kRow_,
                            AscendC::SELMODE::VSEL_TENSOR_TENSOR_MODE,
                            static_cast<uint32_t>(alignedCount_));
            AscendC::DataCopy(tmpArg_, argDst_, alignedCount_);
        }
    }
```

after 还依赖以下同一终版写入中的类型门禁和 mask 初始化片段。

代码证据：revision = 同一终版文件写入快照；path = `example/csrc/ops/<op>/op_kernel/<op>_kernel.cpp`；symbol = `kNanAwareV`；line_range = namespace 内类型门禁定义。

```cpp
// half/float 走 NaN-safe 谓词; bf16/int32 走原 LT 谓词.
template <typename X>
constexpr bool kNanAwareV = std::is_same_v<X, half> || std::is_same_v<X, float>;
```

代码证据：revision = 同一终版文件写入快照；path = `example/csrc/ops/<op>/op_kernel/<op>_kernel.cpp`；symbol = `KernelCummin<X>::Init`；line_range = bit-mask 字节数、四个 mask queue 和 tensor 分配段。

```cpp
        // bit-mask 字节数 (256B 对齐); Or/And/Not 以此为 count.
        maskBytes_ = ALIGN_UP_BYTES((alignedCount_ + 7) / 8, ALIGN_BYTES);

        // UB buffer 规划 (DESIGN §1.5): 单缓冲. 全部用 TQue<VECCALC,1> +
        // 一次性 AllocTensor 持久复用 (TQue LocalTensor 可 cast 到 __ubuf__).
        pipe_.InitBuffer(yQue_,     1, alignedCount_ * sizeof(X));
        pipe_.InitBuffer(tmpXQue_,      1, alignedCount_ * sizeof(X));
        pipe_.InitBuffer(tmpArgQue_,    1, alignedCount_ * sizeof(int32_t));
        pipe_.InitBuffer(minDstQue_,    1, alignedCount_ * sizeof(X));
        pipe_.InitBuffer(argDstQue_,    1, alignedCount_ * sizeof(int32_t));
        pipe_.InitBuffer(kRowQue_,      1, alignedCount_ * sizeof(int32_t));
        // mask 缓冲: mask_(主/LT 或合成最终 take_current) + mask2/3/4 (NaN 合成中间)
        pipe_.InitBuffer(maskQue_,  1, maskBytes_);
        pipe_.InitBuffer(mask2Que_, 1, maskBytes_);
        pipe_.InitBuffer(mask3Que_, 1, maskBytes_);
        pipe_.InitBuffer(mask4Que_, 1, maskBytes_);
        // VECOUT 输出队列 (经 EnQue/DeQue 提供 V→MTE3 同步)
        pipe_.InitBuffer(valuesOutQue_,  1, alignedCount_ * sizeof(X));
        pipe_.InitBuffer(indicesOutQue_, 1, alignedCount_ * sizeof(int64_t));

        // 一次性分配持久 LocalTensor (compute-only scratch, 跨行复用, 不 FreeTensor)
        tmpX_    = tmpXQue_.template AllocTensor<X>();
        tmpArg_  = tmpArgQue_.template AllocTensor<int32_t>();
        minDst_  = minDstQue_.template AllocTensor<X>();
        argDst_  = argDstQue_.template AllocTensor<int32_t>();
        kRow_    = kRowQue_.template AllocTensor<int32_t>();
        mask_    = maskQue_.template AllocTensor<uint8_t>();
        mask2_   = mask2Que_.template AllocTensor<uint8_t>();
        mask3_   = mask3Que_.template AllocTensor<uint8_t>();
        mask4_   = mask4Que_.template AllocTensor<uint8_t>();
    }
```

## 设计决策

1. 选择 self-NE 加位掩码合成，因为它把 NaN 状态机直接编码进 `Select` 谓词，value 与 index 共用同一 take-current 位，避免两个输出分叉。
2. 放弃裸 `running < current`：它只足以表达有限值和后出现平局，已经在全 NaN 输入上被设备评测拒绝。轨迹没有验证额外 scalar `has_nan` 状态或更高阶 IsNaN API 的完整替代实现，因此不把它们列为并行正路线。
3. 当前路线为 `recommended_fastpath`：这是本 trace 唯一通过目标 NaN 语义和全量精度评测的 kernel 路线；未进行正确方案之间的性能排名。

## 系统信息

- 目标：Ascend 950（设备名探测为 Ascend950PR_957c）。
- 工具链：CANN 9.0.1。
- 工程：kernel 直调；修改文件角色为 `example/csrc/ops/<op>/op_kernel/<op>_kernel.cpp`。
- 实测修复分支：half/float；BF16 和 int32 保留原有限值 LT 分支。

## 预防

- 写累计极值前先把 NaN 传播与平局索引规则展开为显式真值表，不要从一个有限值比较式外推。
- value 与 index 必须使用同一个最终选择掩码，否则值正确时索引仍可能漂移。
- 用全 NaN、NaN 后有限值、有限值后 NaN、重复 NaN和有限平局分别验证状态转移。
- bit-mask 逻辑 API 的 count 单位要按接口契约计算，并把额外 mask buffer 纳入 UB 预算。

## 验证信号

来源是一次 Ascend C 累积极小值 kernel 的全量精度验收和随后设备端 NaN 语义探针；失败输出、函数改写和复评结果均来自工具事件。

- 修复前全量评测为 19/20，唯一失败是全 NaN 输入的 values NaN 位置不匹配与 indices 大量不匹配（Ascend 950，证据等级: tool_observed）。
- 谓词修复后远程构建成功，目标全 NaN 用例通过，有限 half 与 BF16 Inf 代表用例无回归（Ascend 950，证据等级: tool_observed）。
- 设备探针逐项显示自定义输出与 golden 在混合 NaN、前导 NaN、重复 NaN、全 NaN和有限平局上的 values/indices 一致（Ascend 950，证据等级: tool_observed）。
- 最终全量精度复评为 20/20（Ascend 950，证据等级: tool_observed）。

- 独立复现 R1：NaN 谓词修复后远程构建成功，目标全 NaN 用例通过，有限值与 Inf 代表用例无回归。（950，tool_observed）。
- 独立复现 R2：strict-LT 分支被替换为 GE 普通选择加 current-is-NaN 覆盖；目标重新构建成功，原测试不退化。（950，tool_observed）。
- 独立复现 R3：以 curr_nan OR (runMin_finite AND curr<=runMin) 构造共享的 values/indices 更新 mask 后，mixed-NaN 探针通过，完整评测由 19/20 提升为 20/20，后续 pytest 81/81 通过。（950，tool_observed）。

## 失效边界

- 本谓词绑定“NaN 传播 + NaN/有限平局都取最后出现位置”的语义；首次出现或忽略 NaN 的算子必须重写真值表。
- 终版只让 half/float 进入 NaN-aware 分支。BF16 NaN 语义未验证，不能从本卡推断正确。
- `Not` / `And` / `Or` 的 count 在该实现中使用对齐后的 mask 字节数；不同 API 版本若 count 单位不同，必须按目标 CANN 文档调整。
- A2、A3 未验证，推断可迁移，但不得写入 `platforms`。

## 坏实践

把 `Compare(running, current, LT)` 当成完整累计极值状态机是被设备结果否定的路线。它没有显式区分 current NaN、running NaN 与两者有限三种状态，即使有限值和平局用例全部通过，也不能据此宣称 NaN 语义正确。

## 误诊

- “只有一个极端输入失败，所以是评测器容差或随机误差”不成立：失败同时包含 NaN 位置与整数索引的大量不匹配，是离散语义错误。
- 普通相等比较会让两个同位 NaN 被判不等；诊断脚本可能显示聚合布尔失败，但这不能覆盖设备输出逐项显示相同的事实，也不能作为放宽评测的理由。

<!-- cannbot:related:start -->
## 相关

- [IsNan](../../apis/simd_api/adv_api/math_compute/is_nan_interface/is_nan.md)（`exemplifies`）：累计极值扫描需要显式识别 current/running NaN 后再合成 Select 掩码；IsNan 提供的逐元素布尔结果正是该诊断与修复链的必要信号。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《累计极值 NaN 语义须用 self-NE 合成选择掩码》具体提供“累计极值 Vector scan 在有限值全部正确、全 NaN 输入却同时出现 NaN 位置和索引失配时，用显式 is-current-NaN、is-running-NaN 与有限 LE 合成选择掩码。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播](rmsnorm_nan_propagation_not_positive_guard.md)（`related`）：两卡利用同一 IEEE ordered-compare 边界：NaN 与有限值比较为 false；RMSNorm 的 `denom>0` 因此把 NaN 错送入零分支，累计极值则需显式 self-NE 识别 NaN。
- [B16 比较先升到 B32 锁定索引 lane](b16_value_and_b32_index_masks_need_common_b32_compute.md)（`related`）：cummin/argmin 同时更新值与索引时还需统一 B32 lane 宽度，否则即使 NaN mask 逻辑正确也会驱动错索引半区。
- [BF16 标量 cast 后端失败—改用位序键](../compilation/bf16_scalar_compare_by_raw_bits.md)（`related`）：BF16 标量 cast 后端失败—改用位序键 与《累计极值 NaN 语义须用 self-NE 合成选择掩码》的实质衔接是：位序键是 BF16 标量 cast 失败的直接替代；所选卡补充同一后端限制、B16→B32 比较宽度及 NaN 显式选择。
- [b16 running 经 fp32 回转会改写 NaN payload](bit_exact_b16_nan_payload_needs_original_dtype_running_value.md)（`related`）：该卡构造 NaN-safe take_current mask，focal 要求用同一 mask 同步更新原 dtype value carry 和 fp32 compare carry；两者组成累计极值的谓词与位保持状态链。
- [跨批首行漏比较—续批从 row 0 扫描](prefix_scan_continuation_batch_must_compare_first_row.md)（`related`）：跨批前缀扫描还必须让续批 row0 参与比较；该状态边界与 NaN 传播规则共同决定 running extremum。
<!-- cannbot:related:end -->
