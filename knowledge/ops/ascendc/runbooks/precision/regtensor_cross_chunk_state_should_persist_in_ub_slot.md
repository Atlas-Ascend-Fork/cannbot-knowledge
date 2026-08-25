---
type: "Runbook"
title: "RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽"
description: "同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。"
tags: ["task.debugging", "topic.compute.reduction", "topic.compute.normalization", "topic.programming_model.execution_unit.vector", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["same_dtype_scalar"]
---

# RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽

## 现象

在 Ascend950 RegBase Softmax 的 last-axis 路径中，整行已正确搬入 UB，单个 vector-length（VL）内的 `max → exp/sum → div` 也正确；但把多个 VL 放进同一个 `__simd_vf__` 的 `for` 循环后，精度测试出现清晰边界：`K<=VL` 通过，`K=VL+1` 即失败，完整测试为 `13 failed, 36 passed`。

定向上板 probe 进一步排除了 DMA 与 Cast：

- 单 VL 的全零与递增输入均 `sum=1`；
- `K=VL+1` 的全零输入出现错误分母，递增输入归一化比例错误；
- 更长输入的结果和也偏离 1；
- non-last-axis 的逐元素 UB buffer 路径大部分通过，故故障集中在 last-axis 的 `Reduce + RegTensor acc` 多迭代累加。

## 适用场景

- 工程形态：Ascend950 kernel 直调；
- API 路径：`__simd_vf__` 内循环调用 `Reg::Reduce`，用一个 `RegTensor acc` 跨循环迭代维护 running max/sum，再在循环末 `StoreAlign`；
- 验证过的平台与 CANN 版本：950 / CANN 9.0.1；
- 适用粒度：`same_operator`，已在 last-axis Softmax 的 max/sum 两个规约阶段验证；迁移到其他规约前须重新上板；
- 路线优先级：`safety_fallback`；**这是 fallback，性能不是最优，追求性能请用另一路线（见 ## 相关）。** 当前卡没有可链接的已验证 fast path；
- 不适用：单 VL 输入没有触发该故障；逐元素路径不需要跨迭代标量累加。

## 根因

失败实现把跨 VL 的持久状态放在 VF 循环内的 `RegTensor acc`，只在循环开始从 UB 槽加载、循环结束再写回。目标编译/执行形态没有保持预期的跨迭代 running max/sum：单迭代正确，多迭代立即出现“max 停在首段、sum 重复/错误累加”的可观测结果。将每次 VF 限制为一个 VL，并在每次调用前从 UB 槽加载 running state、合并本 VL 的 Reduce 结果、立即写回，才得到稳定闭环。 这里不把现象泛化成所有 `RegTensor` 都不能跨循环存活；结论只覆盖这条已实测的 `Reduce + acc + 多 VL VF 循环` 代码形态。

## 解决配方

核心变换：

1. `__simd_vf__` 从“内部循环多个 VL”改成“只处理一个 VL”；
2. running max/sum 每个 VL 都 `LoadAlign(slot) → Reduce → Max/Add → StoreAlign(slot)`；
3. VL 循环移到 `__aicore__` wrapper，每次通过 `asc_vf_call` 处理一个 VL；
4. `ProcessRow` 对 max/sum 各调用一次 wrapper，wrapper 自己遍历整行。

以下 before/after 均来自该次真实写入/编辑。after 的 `ProcessRow` 是由同一函数的 Read 上下文与 Edit 新正文确定性重建，未改写语义。

### before

```cpp
template <typename T>
__simd_vf__ inline void reduce_max_accum_vf(__ubuf__ float *slot, __ubuf__ T *src,
                                           uint32_t count, uint32_t chunkCount)
{
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    SOFTMAX_FENCE_LOAD();
    AscendC::Reg::RegTensor<float> acc, s, tmp;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::UpdateMask<float>(VL);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(acc, slot);
    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(rem);
        SOFTMAX_LOAD_F32(s, src, off, mask);
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(tmp, s, mask);
        AscendC::Reg::Max(acc, acc, tmp, fullMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(slot, acc, fullMask);
}

template <typename T>
__simd_vf__ inline void exp_sum_accum_vf(__ubuf__ float *sumSlot, __ubuf__ T *src,
                                         __ubuf__ float *maxSlot,
                                         uint32_t count, uint32_t chunkCount)
{
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    SOFTMAX_FENCE_LOAD();
    AscendC::Reg::RegTensor<float> acc, s, tmp, mx, bmx, e;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::UpdateMask<float>(VL);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(acc, sumSlot);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(mx, maxSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::HighLowPart::LOWEST,
                            AscendC::Reg::MaskMergeMode::ZEROING>(bmx, mx, fullMask);
    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(rem);
        SOFTMAX_LOAD_F32(s, src, off, mask);
        AscendC::Reg::Sub(e, s, bmx, mask);
        AscendC::Reg::Exp(e, e, mask);
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(tmp, e, mask);
        AscendC::Reg::Add(acc, acc, tmp, fullMask);
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(sumSlot, acc, fullMask);
}
```

```cpp
template <typename T>
__aicore__ inline void ReduceMaxAccum(const AscendC::LocalTensor<float> &slot,
                                      const AscendC::LocalTensor<T> &src, int64_t srcOff,
                                      int64_t count)
{
    __ubuf__ float *slotAddr = (__ubuf__ float *)slot.GetPhyAddr();
    __ubuf__ T *srcAddr = (__ubuf__ T *)src.GetPhyAddr() + srcOff;
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t n = static_cast<uint32_t>(count);
    uint32_t cc = (n + VL - 1) / VL;
    asc_vf_call<reduce_max_accum_vf<T>>(slotAddr, srcAddr, n, cc);
}

template <typename T>
__aicore__ inline void ExpSumAccum(const AscendC::LocalTensor<float> &sumSlot,
                                   const AscendC::LocalTensor<T> &src, int64_t srcOff,
                                   const AscendC::LocalTensor<float> &maxSlot, int64_t count)
{
    __ubuf__ float *sumAddr = (__ubuf__ float *)sumSlot.GetPhyAddr();
    __ubuf__ T *srcAddr = (__ubuf__ T *)src.GetPhyAddr() + srcOff;
    __ubuf__ float *maxAddr = (__ubuf__ float *)maxSlot.GetPhyAddr();
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t n = static_cast<uint32_t>(count);
    uint32_t cc = (n + VL - 1) / VL;
    asc_vf_call<exp_sum_accum_vf<T>>(sumAddr, srcAddr, maxAddr, n, cc);
}
```

```cpp
__aicore__ inline void ProcessRow(int64_t row)
{
    int64_t base = row * rowLength_;
    auto maxSlot = maxSlot_.Get<float>();
    auto sumSlot = sumSlot_.Get<float>();

    auto xLocal = CopyIn(base, rowLength_);
    auto yLocal = outQueueY_.AllocTensor<T>();

    FillScalar(maxSlot, neg_inf_f(), SLOT_FLOATS);
    for (int64_t off = 0; off < rowLength_; off += chunkSize_) {
        int64_t cnt = min_i64(chunkSize_, rowLength_ - off);
        ReduceMaxAccum<T>(maxSlot, xLocal, off, cnt);
    }
    FillScalar(sumSlot, 0.0f, SLOT_FLOATS);
    for (int64_t off = 0; off < rowLength_; off += chunkSize_) {
        int64_t cnt = min_i64(chunkSize_, rowLength_ - off);
        ExpSumAccum<T>(sumSlot, xLocal, off, maxSlot, cnt);
    }
    for (int64_t off = 0; off < rowLength_; off += chunkSize_) {
        int64_t cnt = min_i64(chunkSize_, rowLength_ - off);
        SoftmaxDiv<T>(yLocal, off, xLocal, off, maxSlot, sumSlot, cnt);
    }

    outQueueY_.EnQue(yLocal);
    inQueueX_.FreeTensor(xLocal);
    CopyOut(base, rowLength_);
}
```

### after

```cpp
template <typename T>
__simd_vf__ inline void reduce_max_one_vf(__ubuf__ float *slot, __ubuf__ T *src,
                                          uint32_t count)
{
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    SOFTMAX_FENCE_LOAD();
    AscendC::Reg::RegTensor<float> acc, s, tmp;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::UpdateMask<float>(VL);
    AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(count);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(acc, slot);
    SOFTMAX_LOAD_F32(s, src, 0, mask);
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(tmp, s, mask);
    AscendC::Reg::Max(acc, acc, tmp, fullMask);
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(slot, acc, fullMask);
}

template <typename T>
__simd_vf__ inline void exp_sum_one_vf(__ubuf__ float *sumSlot, __ubuf__ T *src,
                                       __ubuf__ float *maxSlot, uint32_t count)
{
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    SOFTMAX_FENCE_LOAD();
    AscendC::Reg::RegTensor<float> acc, s, tmp, mx, bmx, e;
    AscendC::Reg::MaskReg fullMask = AscendC::Reg::UpdateMask<float>(VL);
    AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(count);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(acc, sumSlot);
    AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(mx, maxSlot);
    AscendC::Reg::Duplicate<float, AscendC::Reg::HighLowPart::LOWEST,
                            AscendC::Reg::MaskMergeMode::ZEROING>(bmx, mx, fullMask);
    SOFTMAX_LOAD_F32(s, src, 0, mask);
    AscendC::Reg::Sub(e, s, bmx, mask);
    AscendC::Reg::Exp(e, e, mask);
    AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(tmp, e, mask);
    AscendC::Reg::Add(acc, acc, tmp, fullMask);
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(sumSlot, acc, fullMask);
}
```

```cpp
template <typename T>
__aicore__ inline void ReduceMaxAccum(const AscendC::LocalTensor<float> &slot,
                                      const AscendC::LocalTensor<T> &src, int64_t srcOff,
                                      int64_t count)
{
    __ubuf__ float *slotAddr = (__ubuf__ float *)slot.GetPhyAddr();
    __ubuf__ T *srcAddr = (__ubuf__ T *)src.GetPhyAddr() + srcOff;
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t n = static_cast<uint32_t>(count);
    for (uint32_t off = 0; off < n; off += VL) {
        uint32_t cnt = (n - off < VL) ? (n - off) : VL;
        asc_vf_call<reduce_max_one_vf<T>>(slotAddr, srcAddr + off, cnt);
    }
}

template <typename T>
__aicore__ inline void ExpSumAccum(const AscendC::LocalTensor<float> &sumSlot,
                                   const AscendC::LocalTensor<T> &src, int64_t srcOff,
                                   const AscendC::LocalTensor<float> &maxSlot, int64_t count)
{
    __ubuf__ float *sumAddr = (__ubuf__ float *)sumSlot.GetPhyAddr();
    __ubuf__ T *srcAddr = (__ubuf__ T *)src.GetPhyAddr() + srcOff;
    __ubuf__ float *maxAddr = (__ubuf__ float *)maxSlot.GetPhyAddr();
    uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    uint32_t n = static_cast<uint32_t>(count);
    for (uint32_t off = 0; off < n; off += VL) {
        uint32_t cnt = (n - off < VL) ? (n - off) : VL;
        asc_vf_call<exp_sum_one_vf<T>>(sumAddr, srcAddr + off, maxAddr, cnt);
    }
}
```

```cpp
__aicore__ inline void ProcessRow(int64_t row)
{
    int64_t base = row * rowLength_;
    auto maxSlot = maxSlot_.Get<float>();
    auto sumSlot = sumSlot_.Get<float>();

    auto xLocal = CopyIn(base, rowLength_);
    auto yLocal = outQueueY_.AllocTensor<T>();

    FillScalar(maxSlot, neg_inf_f(), SLOT_FLOATS);
    ReduceMaxAccum<T>(maxSlot, xLocal, 0, rowLength_);
    FillScalar(sumSlot, 0.0f, SLOT_FLOATS);
    ExpSumAccum<T>(sumSlot, xLocal, 0, maxSlot, rowLength_);
    SoftmaxDiv<T>(yLocal, 0, xLocal, 0, maxSlot, sumSlot, rowLength_);

    outQueueY_.EnQue(yLocal);
    inQueueX_.FreeTensor(xLocal);
    CopyOut(base, rowLength_);
}
```

## 设计决策

- 选择 UB 槽作为跨 VL 的持久状态：每次 VF 的输入/输出都可观察，避免依赖本次已失败的跨循环寄存器状态。
- 放弃单次 VF 内多 VL 累加：它更少 `asc_vf_call`，但实测越过一个 VL 即错误。
- 当前方案是 `safety_fallback`：优先恢复正确性；每 VL 一次 `asc_vf_call` 带来明显调用开销，不能标为性能 fast path。
- 未采用“放宽容差”：失败包含归一化和数量级错误，不是浮点微小漂移。

## 系统信息

- toolchain：CANN 9.0.1 Ascend C/BiSheng；
- 目标：Ascend950PR_957c / `dav-3510`；
- 工程：Flash kernel 直调，`softmax.asc`；
- 相关 API：`Reg::Reduce<MAX/SUM>`、`Reg::Max/Add`、`LoadAlign/StoreAlign`、`asc_vf_call`；
- dtype 覆盖：fp16、fp32、bf16。

## 性能影响

## 预防

- 规约状态跨多个 VL 时，先做 `K=VL` 与 `K=VL+1` 的边界 probe；
- 同时检查输出和、max diff 与最后一个 VL 的贡献，避免只测单向量；
- 把跨调用状态放入明确的 UB/GM artifact，再用 barrier/fence 保证写后读；
- 正确性稳定后再融合多个 VL，任何融合优化都必须重跑边界 probe 与全量精度。

## 验证信号

来源是一次 Ascend950 Softmax last-axis 规约修复及连续上板验证：

- `K=VL+1`、多 VL 与尾块 probe 的输出和均恢复为 `1.000000`，递增输入 max diff 为 `3.725e-09` 到 `5.960e-08`（来源平台: 950；证据等级: tool_observed）；
- 完整 pytest `49/49 PASSED`（来源平台: 950；证据等级: tool_observed）；
- 干净重建后再次 `49/49 PASSED`（来源平台: 950；证据等级: tool_observed）；
- cann-bench 全部 20 个 case 精度通过、通过率 100%（来源平台: 950；证据等级: tool_observed）。

## 失效边界

- 该方案只验证了 Softmax last-axis 的 fp16/fp32/bf16 规约；其他规约算子需重新验证 Reduce 结果布局和同步；
- 单 VL 输入不需要 UB-backed 跨段累加，但保留该路径仍可正确运行；
- 性能目标严格时必须寻找已验证的融合 VF fast path；不能直接采用本 fallback；
- A2/A3 未验证，不能推断 RegBase 代码可直接迁移。

## 坏实践

- 只测 `K<=VL` 就认为规约循环正确；这条轨迹中单 VL 完全通过，却掩盖了跨迭代状态错误。
- 通过放宽 `rtol/atol` 掩盖归一化和数量级错误；该错误不是正常舍入。
- 把每 VL 一次 VF 的正确性方案宣传成性能最优路线；实测相对内置基线代价很大。

## 误诊

- 初看可怀疑 tail mask 或 DMA/Cast；但 `K=VL` 正确、`K=VL+1` 立刻失败，且逐元素 general path 大部分通过，更强地指向跨 VL 规约状态。
- 一次 bf16 non-last-axis 用例出现阈值边缘失败，未做针对性代码修改后在后续全量测试通过；该信号不纳入本卡根因。

<!-- cannbot:related:start -->
## 相关

- [RegTensor](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/reg_tensor.md)（`exemplifies`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《RegTensor》说明RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：RegTensor 跨 VF 内循环状态不能仅保留在寄存器对象中，案例将状态改存 UB 槽以跨 asc_vf_call 持久化。
- [Ascend950 Reg 扫描按 256B 锁定 lane](dav3510_vector_register_width_is_256_bytes.md)（`related`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《Ascend950 Reg 扫描按 256B 锁定 lane》说明dav-3510 上把向量寄存器误按 512B 计算会让高半 lane 重放低半数据，值与索引必须按共同的 64 lane 分块。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [Reg 尾块 masked Add 清零跨块累加器](reg_tail_mask_zeroing_clears_cross_chunk_accumulator.md)（`related`）：Reg 尾块 masked Add 清零跨块累加器 与《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》的实质衔接是：尾块 Mul 用 tail mask 把无效临时 lane 置零，但跨块 Add 必须用 full mask；MaskMergeMode 定义 ZEROING/MERGING，Add/Mul 是实际指令，UpdateMask、Reduce 与跨块状态卡验证该修复不会清空历史 accumulator。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](vector_scalar_ub_handoff_requires_explicit_completion.md)（`related`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《VF 归约落 UB 后 GetValue 读取陈旧标量》说明Vector 归约结果经 StoreAlign 落 UB 后立即由标量侧 GetValue 读取会出现竞态；保持归约和广播在同一 VF 内可消除错误。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`related`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《分块 wrapper 与 VF callee 不可重复叠加 offset》说明asc_vf_call 已传入按 chunk 前移的 UB 指针时，VF callee 再加同一 offset 会从第二块开始按双倍偏移读错数据。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`same_topic`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《AR 跨块循环放在 __simd_vf__ 只执行首块》说明Ascend950 Reg kernel 把 AR 跨向量块状态机留在单次 __simd_vf__ 中时只完成首块；将循环上移至 __aicore__ wrapper，并在同址读改写调用之间加入 Vector barrier。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [Reg 同 wrapper 回读 UB 引发尺寸相关漂移](split_multi_pass_vf_at_ub_producer_consumer_boundaries.md)（`same_topic`）：跨 chunk 状态不能依赖 RegTensor 跨 VF 调用存活，必须落到 UB slot；该卡给出状态持久化机制。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](fixed_address_vf_accumulator_needs_per_call_barrier.md)（`same_topic`）：两卡都定位多 VL 归约的跨 chunk 状态丢失，并把状态放在固定 UB 槽、每 VL 单独 asc_vf_call；focal 进一步证明 B16 场景调用间还需 PipeBarrier 才闭环。
- [Reg::Reduce 跨 chunk 覆写导致规约失真](reg_reduce_per_chunk_result_must_accumulate_explicitly.md)（`same_topic`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《Reg::Reduce 跨 chunk 覆写导致规约失真》说明dav-3510 Reg::Reduce 每次只产当前 chunk 的标量结果；循环复用 dstReg 会丢失前序 chunk，须显式折叠 lane 0。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
<!-- cannbot:related:end -->
