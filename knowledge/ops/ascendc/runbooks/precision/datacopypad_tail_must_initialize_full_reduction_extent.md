---
type: "Runbook"
title: "DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部"
description: "行缓冲强制扩到固定向量长度、rightPadding 却只覆盖较短 DMA 边界时，小归一化维会把未初始化 UB 尾部纳入规约；用 32/sizeof(T) 统一分配与补零粒度。"
tags: ["task.debugging", "topic.precision", "topic.data_movement.data_copy", "topic.compute.reduction"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["sub-VL"]
---

# DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部

## 现象

在 Ascend950 的 kernel 直调工程中实现沿末维规约的 RMSNorm 时，`rms_norm.asc` 已能编译并运行，但 NPU 参数化测试只通过 20/29。失败集中在小于一个 fp32 向量长度的归一化维：部分输出的 `max_rel` 接近 1，BF16 路径还出现 NaN；较大的归一化维均通过。

当时代码把每行 UB 缓冲至少扩到 `FP32_VL_ELEMS`，同时只用固定的 `FP32_BLOCK_ELEMS` 计算 `DataCopyPadExtParams<T>::rightPadding`。因此，分配长度、DMA 补零长度和后续 `ReduceSum(..., Dalign_)` 的读取长度不是同一个边界。

## 适用场景

- 工程形态：Ascend C kernel 直调，按行搬入 UB 后沿末维做规约；
- API 路径：`DataCopyPad` → `Cast/Mul` → `ReduceSum`，计算长度使用对齐后的 `Dalign_`；
- 验证过的平台与版本：Ascend950PR_957b / dav-3510，CANN 9.0.1；与 frontmatter `platforms: [950]` 一致；
- 适用粒度：`operator_family`，适用于所有“DMA 尾部补零后又按对齐长度参与规约”的归一化或规约算子；
- 路线优先级：`recommended_fastpath`；这是本轨迹唯一通过全部 NPU pytest 的正确对齐方式，但没有做独立性能优越性比较；
- 明确不适用：计算只读取原始有效元素数、不会消费填充区的 kernel；非 `DataCopyPad` 搬入路径也需按其自身 padding 契约重新核对。

## 根因

UB 行缓冲被强制扩到固定 64 元素，而 `DataCopyPad` 的 `rightPadding` 仅补到固定 8 元素边界，导致 `ReduceSum(..., Dalign_)` 把未初始化尾部一并规约。 机制链如下：设原始末维为 `D`，旧实现令 `Dalign=max(ceil(D/8)×8,64)`，但 `padRight=ceil(D/8)×8-D`，因此实际初始化长度只有 `D+padRight=ceil(D/8)×8`；当 `Dalign` 更大时，区间 `[D+padRight,Dalign)` 未写入，后续按 `Dalign` 做 `Mul` 和 `ReduceSum`，脏值进入平方和，最终把 `rstd=1/sqrt(sum/D+epsilon)` 放大为大误差或 NaN。

## 解决配方

让 UB 分配长度与 `DataCopyPad` 的补零长度共享同一个 dtype 感知的 32B 数据块粒度：

`blockElems = 32 / sizeof(T)`，`Dalign = ceil(D/blockElems) × blockElems`，`padRight = Dalign - D`。

以下代码由轨迹中的 `Write`/`Edit` 事件逐字重建。证据位置：工作树 path `operators/rms_norm/rms_norm.asc`，symbol `KernelRmsNorm<T>::Init`；固定 40 位 revision 与 blob URL 未出现在 trace 中，因此本卡只能作为 DRAFT，落库前须由 curator 补齐或明确按轨迹证据例外处理。

### before

```cpp
__aicore__ inline void Init(GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
                                int64_t numRow, int64_t numCol, int64_t blockRowLength,
                                float epsilon)
    {
        int64_t coreOffset = blockRowLength * AscendC::GetBlockIdx();
        xGm_.SetGlobalBuffer((__gm__ T *)x + coreOffset * numCol);
        yGm_.SetGlobalBuffer((__gm__ T *)y + coreOffset * numCol);
        gammaGm_.SetGlobalBuffer((__gm__ T *)gamma);

        numCol_ = numCol;
        myRows_ = numRow - coreOffset;
        if (myRows_ > blockRowLength) myRows_ = blockRowLength;
        if (myRows_ < 0) myRows_ = 0;
        eps_ = epsilon;
        invD_ = (numCol == 0) ? 0.0f : (1.0f / static_cast<float>(numCol));

        uint32_t D = static_cast<uint32_t>(numCol);
        uint32_t a = (D + FP32_BLOCK_ELEMS - 1) / FP32_BLOCK_ELEMS * FP32_BLOCK_ELEMS;
        Dalign_ = (a < FP32_VL_ELEMS) ? FP32_VL_ELEMS : a;
        padRight_ = (D % FP32_BLOCK_ELEMS == 0) ? 0 : (FP32_BLOCK_ELEMS - D % FP32_BLOCK_ELEMS);

        uint32_t rowBytes = Dalign_ * sizeof(T);
        uint32_t fp32Bytes = Dalign_ * sizeof(float);
        pipe_.InitBuffer(xQueue_, PIPELINE_DEPTH, rowBytes);
        pipe_.InitBuffer(yQueue_, PIPELINE_DEPTH, rowBytes);
        pipe_.InitBuffer(gammaTBuf_, rowBytes);
        pipe_.InitBuffer(sumBuf_, 64);
        pipe_.InitBuffer(tmpBuf_, fp32Bytes);
        pipe_.InitBuffer(rstdBuf_, fp32Bytes);
        if constexpr (!AscendC::IsSameType<T, float>::value) {
            pipe_.InitBuffer(xfBuf_, fp32Bytes);
            pipe_.InitBuffer(gammaFpBuf_, fp32Bytes);
        }

        // Load gamma once (T) and upcast once (b16). TBuf MTE2->V sync via event flag.
        auto gammaLocal = gammaTBuf_.Get<T>();
        AscendC::DataCopyExtParams cp{1, static_cast<uint32_t>(numCol * static_cast<int64_t>(sizeof(T))), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> pp{false, 0, 0, 0};
        AscendC::DataCopyPad(gammaLocal, gammaGm_[0], cp, pp);
        AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(0);
        if constexpr (!AscendC::IsSameType<T, float>::value) {
            AscendC::Cast(gammaFpBuf_.Get<float>(), gammaLocal, AscendC::RoundMode::CAST_NONE, Dalign_);
        }
    }
```

### after

```cpp
__aicore__ inline void Init(GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
                                int64_t numRow, int64_t numCol, int64_t blockRowLength,
                                float epsilon)
    {
        int64_t coreOffset = blockRowLength * AscendC::GetBlockIdx();
        xGm_.SetGlobalBuffer((__gm__ T *)x + coreOffset * numCol);
        yGm_.SetGlobalBuffer((__gm__ T *)y + coreOffset * numCol);
        gammaGm_.SetGlobalBuffer((__gm__ T *)gamma);

        numCol_ = numCol;
        myRows_ = numRow - coreOffset;
        if (myRows_ > blockRowLength) myRows_ = blockRowLength;
        if (myRows_ < 0) myRows_ = 0;
        eps_ = epsilon;
        invD_ = (numCol == 0) ? 0.0f : (1.0f / static_cast<float>(numCol));

        uint32_t D = static_cast<uint32_t>(numCol);
        // Align the per-row T-buffer to a 32B DMA block (sizeof(T)-dependent) so DataCopyPad's
        // right-padding zeroes the WHOLE buffer (no uninit tail that the fp32 compute would read).
        uint32_t blockElems = 32U / static_cast<uint32_t>(sizeof(T));   // bf16/fp16=16, fp32=8
        Dalign_ = (D + blockElems - 1) / blockElems * blockElems;
        if (Dalign_ == 0) Dalign_ = blockElems;
        padRight_ = Dalign_ - D;                                        // T-elements to zero-pad

        uint32_t rowBytes = Dalign_ * sizeof(T);
        uint32_t fp32Bytes = Dalign_ * sizeof(float);
        pipe_.InitBuffer(xQueue_, PIPELINE_DEPTH, rowBytes);
        pipe_.InitBuffer(yQueue_, PIPELINE_DEPTH, rowBytes);
        pipe_.InitBuffer(gammaTBuf_, rowBytes);
        pipe_.InitBuffer(sumBuf_, 64);
        pipe_.InitBuffer(tmpBuf_, fp32Bytes);
        pipe_.InitBuffer(rstdBuf_, fp32Bytes);
        if constexpr (!AscendC::IsSameType<T, float>::value) {
            pipe_.InitBuffer(xfBuf_, fp32Bytes);
            pipe_.InitBuffer(gammaFpBuf_, fp32Bytes);
        }

        // Load gamma once (T) and upcast once (b16). TBuf MTE2->V sync via event flag.
        auto gammaLocal = gammaTBuf_.Get<T>();
        AscendC::DataCopyExtParams cp{1, static_cast<uint32_t>(numCol * static_cast<int64_t>(sizeof(T))), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> pp{false, 0, 0, 0};
        AscendC::DataCopyPad(gammaLocal, gammaGm_[0], cp, pp);
        AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(0);
        if constexpr (!AscendC::IsSameType<T, float>::value) {
            AscendC::Cast(gammaFpBuf_.Get<float>(), gammaLocal, AscendC::RoundMode::CAST_NONE, Dalign_);
        }
    }
```

`CopyIn` 的消费侧保持如下，`padRight_` 必须恰好覆盖 `Dalign_ - D`：

```cpp
__aicore__ inline void CopyIn(int64_t r)
    {
        AscendC::DataCopyExtParams cp{1, static_cast<uint32_t>(numCol_ * static_cast<int64_t>(sizeof(T))), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> pp{padRight_ > 0, 0, static_cast<uint8_t>(padRight_), 0};
        auto xLocal = xQueue_.template AllocTensor<T>();
        AscendC::DataCopyPad(xLocal, xGm_[r * numCol_], cp, pp);
        xQueue_.EnQue(xLocal);
    }
```

## 设计决策

1. 选择 `32/sizeof(T)`，因为 `DataCopyPad` 的搬运边界是 32B，而 `rightPadding` 用元素数表达；同一公式同时决定缓冲长度和补零长度，消除两个独立对齐口径。
2. 放弃“统一按 fp32 的 8 元素粒度”和“无条件至少分配 64 元素”：前者对 fp16/BF16 不是完整 32B 数据块，后者会制造 DMA 不会自动写满的额外 UB 尾区。
3. 当前方案标为 `recommended_fastpath`：它没有额外清零 kernel，只利用 `DataCopyPad` 完成必要的 32B 尾部补零；但本 trace 没有独立 profiling，不能宣称通用性能收益。

## 系统信息

- 工具链：CANN 9.0.1，bisheng，`--npu-arch=dav-3510`；
- 验证设备：Ascend950PR_957b，物理卡 5；
- 工程：Flash/direct-launch 单文件 `.asc`，PyTorch `TORCH_LIBRARY` 注册；
- 相关文件：`operators/rms_norm/rms_norm.asc`、`operators/rms_norm/test_rms_norm.py`；
- 代码证据固定 revision：trace 未提供 40 位哈希，只有后续提交的短哈希，故仍是 curator blocker。

## 预防

- 任何 `DataCopyPad` 路径都同时核对三件事：UB 分配元素数、`rightPadding` 元素数、后续计算/规约元素数；三者必须覆盖同一范围。
- 对模板 dtype 使用 `blockElems = 32 / sizeof(T)`，不要把 fp32 的 8 元素数据块直接复用于 fp16/BF16。
- 小于一个向量长度的末维必须单独进 NPU 用例矩阵；“大维全部通过、小维出现 NaN/近 1 误差”优先检查未初始化 padding，而不是先放宽精度阈值。
- 修复后既跑小维定向测试，也跑包含非对齐和大维的全量回归，防止把尾块修复变成 UB 超额或大维退化。

## 验证信号

来源说明：这条知识来自 Ascend950 上一次 RMSNorm kernel 开发，先在真实 NPU 参数化测试中观察到小维集中失败，再修改 `KernelRmsNorm<T>::Init` 的对齐与补零公式，并用同一远端 helper 重新构建和测试。

- 修复前 NPU pytest 为 20/29 通过，失败只集中于小归一化维，部分 `max_rel` 接近 1 且 BF16 出现 NaN（来源平台: 950；证据等级: tool_observed）。
- 改为 dtype 感知 32B 对齐后，远端构建输出 `[100%] Built target op_rms_norm`，NPU pytest 为 29/29 通过（来源平台: 950；证据等级: tool_observed）。
- 包含该修复的终版实现通过 cann-bench 20/20 case 精度评测，并在清理远端 build 目录后再次完成干净构建与 29/29 NPU pytest（来源平台: 950；证据等级: tool_observed）。

## 失效边界

- `rightPadding` 字段是 `uint8_t`；若单次尾部补齐元素数可能超过其表达范围，须改分块策略，不能直接照抄。
- 本结论验证于连续末维、单行一次 `DataCopyPad` 的直调实现；多维 stride、分段 DMA 或多模板路由需分别核对每段的实际消费范围。
- A2/A3 未验证；其 DMA 对齐契约若相同，机制上可能迁移，但必须标为“未验证，推断可迁移”，不得直接并入 `platforms`。

## 坏实践

- 为了方便向量计算而把所有小维无条件扩到 64 元素，却仍只补到更短的 DMA 边界；这会把“多分配的安全余量”变成可被计算读取的脏数据。
- 看到小维误差后修改 pytest 容差或跳过用例；本轨迹的 NaN 与近 1 误差来自未初始化 UB，不是低精度舍入。

## 误诊

轨迹中曾把小维失败怀疑为 `ReduceSum` 小计数限制或 V→S 同步竞争；这些只是 `agent_reported` 假设。真正可验证的区分信号是：仅调整分配/补零覆盖范围、不改规约公式和同步后，全部 NPU pytest 立即通过。

<!-- cannbot:related:start -->
## 相关

- [归约计算](../../apis/simd_api/basic_api/reg_vector_compute/reduction_compute/reduction_compute.md)（`exemplifies`）：《归约计算》处理“Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。”。《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》提供“行缓冲强制扩到固定向量长度、rightPadding 却只覆盖较短 DMA 边界时，小归一化维会把未初始化 UB 尾部纳入规约；用 32/sizeof(T) 统一分配与补零粒度。”，其具体合同或探针直接接入规约 count、尾部填充、并行切核和 UB 容量的直接正确性约束。
- [归约计算概述](../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/introduction.md)（`exemplifies`）：归约计算概述 与《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [DataCopyPad rightPad 字段为 uint8_t](../compilation/datacopypad_rightpad_uint8_t.md)（`related`）：目标卡展示 rightPadding 数值不足会留下 UB 脏尾部；本卡确保表达该数值时使用正确的 uint8_t 字段类型，连接编译契约与规约正确性验证。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](../compilation/datacopypad_gm_to_ub_requires_pad_params.md)（`related`）：GM→UB DataCopyPad 的 pad 参数决定尾部写入值；缺失时无法依赖搬运自动初始化 reduction tail。
- [DataCopyPad多行stride单位误用导致非对齐行输出NaN](datacopypad_stride_fields_use_32_byte_block_units.md)（`related`）：初始化 reduction extent 前必须按 32B block 理解搬入跨度，否则 tail 范围和物理行布局都会算错。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`related`）：归约后不仅 tail 要干净，lane0 标量还需广播到有效向量范围，二者共同保证后续归一化输入完整。
- [窄尾 tile 行距错位：补齐 UB gap](datacopypad_narrow_tile_needs_explicit_ub_row_gap.md)（`related`）：窄 tile 的 UB 行 gap 会留下未写区域；若参与归约必须显式初始化完整 extent。
- [AR 输出张量未初始化导致 Softmax 部分用例错](softmax_ar_output_buffer_must_be_initialized_from_input.md)（`same_topic`）：两卡都处理归约读取了未初始化 UB：一张针对 DataCopyPad tail，一张针对 AR 输出 buffer 的初值。
- [DataCopyPad stride 表示 block 间隙](datacopypad_stride_is_inter_block_gap.md)（`same_topic`）：DataCopyPad stride 表示 block 间隙 与《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》的实质衔接是：这些卡都直接解释 DataCopyPad 的 stride 是有效 block 后的 gap，并覆盖32B单位、窄尾padding、逐行复制、非连续子块、NDDMA stride及官方GM→L1参数契约。
- [Reduce count 必须排除 DMA 对齐填充元素](reduction_count_excludes_dma_padding.md)（`same_topic`）：Reduce count 必须排除 DMA 对齐填充元素 与《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》的实质衔接是：DMA 对齐容量不是 Reduce 的数学 count；DataCopyPad/padding 故障、Softmax 与 ReduceMax/Sum 各层入口共同验证填充零经 Exp 后会污染分母。
<!-- cannbot:related:end -->
