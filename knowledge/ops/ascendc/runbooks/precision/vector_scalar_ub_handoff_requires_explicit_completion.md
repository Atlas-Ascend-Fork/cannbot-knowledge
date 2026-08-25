---
type: "Runbook"
title: "VF 归约落 UB 后 GetValue 读取陈旧标量"
description: "Vector 归约结果经 StoreAlign 落 UB 后立即由标量侧 GetValue 读取会出现竞态；保持归约和广播在同一 VF 内可消除错误。"
tags: ["task.debugging", "topic.compute.reduction", "topic.implementation.synchronization", "topic.programming_model.execution_unit.vector", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# VF 归约落 UB 后 GetValue 读取陈旧标量

## 现象

在 Ascend 950 `dav-3510` 的 Kernel 直调工程中，为绕过一次 RegTensor 广播编译问题，把末轴归约拆成三个 VF：第一个 VF 将最大值写入 32B UB 槽，`__aicore__` 包装层执行 `PipeBarrier<PIPE_V>()` 后用 `LocalTensor::GetValue(0)` 读回标量，再把它作为下一 VF 的 scalarValue。

该版本可以干净构建，但上板执行完整 pytest 时只有 21 个用例通过、25 个失败。失败集中在采用这条末轴路径的多种 dtype；部分输出为正常概率，部分行却出现千级到万级异常值，记录到的最大绝对差超过 `1e6`。使用纯 per-lane VF 的非末轴路径仍能通过，说明问题落在“VF 归约结果→UB→标量读取→下一 VF”的跨执行域交接，而不是 softmax 公式或测试容差。

## 适用场景

- 工程形态：Ascend 950 Kernel 直调，`__simd_vf__` 与 `__aicore__` 包装层混合编排。
- API 路径：`AscendC::Reg::Reduce`/`StoreAlign` → `PipeBarrier<PIPE_V>` → `LocalTensor::GetValue` → 下一次 `asc_vf_call`。
- 验证过的平台与 CANN 版本：Ascend 950（`dav-3510`）+ CANN 9.0.1，与 frontmatter `platforms` 一致。
- 适用粒度：`operator_family`；适用于“向量归约产生 lane 0 标量，再广播回整向量”的 RegBase 算子族。
- 路线优先级：`recommended_fastpath`；保持归约结果、广播和消费都在同一个 VF/寄存器域内。
- 明确不适用：已经有文档化 V→Scalar 同步原语并在目标版本实测通过的路径；纯 Vector→Vector UB 依赖不等同于本卡的 Scalar `GetValue` 读取。

## 根因

`PipeBarrier<PIPE_V>` 只约束 Vector pipe 内部顺序，不能保证前一 VF 的 `StoreAlign` 已对 `__aicore__` 标量侧 `LocalTensor::GetValue` 可见，因而包装层可能读取陈旧 UB 标量并把错误的 max/sum 传播到整行输出。

## 解决配方

不要把 Reg 归约标量经 UB 交给 AICore 标量侧读取；让归约、lane 0 广播和后续向量计算留在同一 `__simd_vf__`，使用 RegTensor→RegTensor `Duplicate<T, HighLowPart::LOWEST, MaskMergeMode::ZEROING>` 广播最低 lane。

### before

revision: 精度失败前完整函数快照；path: `operators/softmax/softmax.asc`；symbol: `softmax_last_max_vf`；lines: 106-126。

```cpp
__simd_vf__ inline void softmax_last_max_vf(__ubuf__ float *slotAddr, __ubuf__ float *xAddr, uint32_t count)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> xReg, accMax, chunkMax;
    AscendC::Reg::MaskReg scalarMask;
    {
        uint32_t oneLen = 1;
        scalarMask = AscendC::Reg::UpdateMask<float>(oneLen);
    }
    AscendC::Reg::Duplicate<float>(accMax, -1.0e38f);  // max-neutral; see header note
    uint32_t chunkCount = (count + vectorLength - 1) / vectorLength;
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = count - offset;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, xAddr + offset);
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkMax, xReg, mask);
        AscendC::Reg::Max(accMax, accMax, chunkMax, scalarMask);  // lane0: max(accMax, chunkMax)
    }
    AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(slotAddr, accMax, scalarMask);
}
```

revision: 精度失败前完整函数快照；path: `operators/softmax/softmax.asc`；symbol: `KernelSoftmaxLast<T>::Compute`；lines: 312-353。

```cpp
__aicore__ inline void Compute(uint32_t off)
    {
        (void)off;
        auto xIn = inQueueX_.DeQue<T>();
        auto yOut = outQueueY_.AllocTensor<T>();
        auto maxSlot = maxSlotBuf_.Get<float>();
        auto sumSlot = sumSlotBuf_.Get<float>();
        __ubuf__ float *maxSlotAddr = (__ubuf__ float *)maxSlot.GetPhyAddr();
        __ubuf__ float *sumSlotAddr = (__ubuf__ float *)sumSlot.GetPhyAddr();

        if constexpr (std::is_same_v<T, float>) {
            __ubuf__ float *xAddr = (__ubuf__ float *)xIn.GetPhyAddr();
            __ubuf__ float *yAddr = (__ubuf__ float *)yOut.GetPhyAddr();
            SoftmaxLastMaxVF(maxSlotAddr, xAddr, r_);
            AscendC::PipeBarrier<PIPE_V>();
            float maxVal = maxSlot.GetValue(0);
            float negMax = -maxVal;
            SoftmaxLastSumVF(sumSlotAddr, xAddr, negMax, r_);
            AscendC::PipeBarrier<PIPE_V>();
            float sumVal = sumSlot.GetValue(0);
            float invSum = 1.0f / sumVal;
            SoftmaxLastNormVF(yAddr, xAddr, negMax, invSum, r_);
        } else {
            auto xFp32 = xFp32Buf_.Get<float>();
            __ubuf__ float *fp32Addr = (__ubuf__ float *)xFp32.GetPhyAddr();
            CastInVF<T>(fp32Addr, (__ubuf__ T *)xIn.GetPhyAddr(), r_);
            AscendC::PipeBarrier<PIPE_V>();
            SoftmaxLastMaxVF(maxSlotAddr, fp32Addr, r_);
            AscendC::PipeBarrier<PIPE_V>();
            float maxVal = maxSlot.GetValue(0);
            float negMax = -maxVal;
            SoftmaxLastSumVF(sumSlotAddr, fp32Addr, negMax, r_);
            AscendC::PipeBarrier<PIPE_V>();
            float sumVal = sumSlot.GetValue(0);
            float invSum = 1.0f / sumVal;
            SoftmaxLastNormVF(fp32Addr, fp32Addr, negMax, invSum, r_);
            AscendC::PipeBarrier<PIPE_V>();
            CastOutVF<T>((__ubuf__ T *)yOut.GetPhyAddr(), fp32Addr, r_);
        }
        outQueueY_.EnQue(yOut);
        inQueueX_.FreeTensor(xIn);
    }
```

### after

revision: 终版完整函数，由完整函数写入与后续精确 `-INFINITY` 编辑重建；path: `operators/softmax/softmax.asc`；symbol: `softmax_last_vf`；lines: 109-165。

```cpp
__simd_vf__ inline void softmax_last_vf(__ubuf__ float *yAddr, __ubuf__ float *xAddr, uint32_t count)
{
    constexpr uint32_t vectorLength = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> xReg, eReg, yReg, bcastMax, bcastSum;
    AscendC::Reg::RegTensor<float> accMax, accSum, chunkMax, newMax, diff, rescale, chunkSum;
    AscendC::Reg::MaskReg fullMask;
    {
        uint32_t fullLen = vectorLength;
        fullMask = AscendC::Reg::UpdateMask<float>(fullLen);
    }
    AscendC::Reg::MaskReg scalarMask;
    {
        uint32_t oneLen = 1;
        scalarMask = AscendC::Reg::UpdateMask<float>(oneLen);
    }

    // init: accMax = -inf (max-neutral; below all finite fp32 incl. extreme negatives, and
    // reproduces torch special-value behavior for +/-inf/NaN rows via natural IEEE arithmetic).
    AscendC::Reg::Duplicate<float>(accMax, -INFINITY);
    AscendC::Reg::Duplicate<float>(accSum, 0.0f);

    uint32_t chunkCount = (count + vectorLength - 1) / vectorLength;

    // pass 1: online max + sum. accMax/accSum are scalars in lane 0.
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = count - offset;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, xAddr + offset);
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::MAX>(chunkMax, xReg, mask);
        AscendC::Reg::Max(newMax, accMax, chunkMax, scalarMask);          // newMax[0] = max(accMax, chunkMax)
        AscendC::Reg::Sub(diff, accMax, newMax, scalarMask);             // oldMax - newMax (<=0)
        AscendC::Reg::Exp(rescale, diff, scalarMask);
        AscendC::Reg::Mul(accSum, accSum, rescale, scalarMask);          // rescale running sum
        AscendC::Reg::Duplicate<float, AscendC::Reg::HighLowPart::LOWEST,
                                 AscendC::Reg::MaskMergeMode::ZEROING>(bcastMax, newMax, fullMask);
        AscendC::Reg::Sub(xReg, xReg, bcastMax, mask);
        AscendC::Reg::Exp(eReg, xReg, mask);
        AscendC::Reg::Reduce<AscendC::Reg::ReduceType::SUM>(chunkSum, eReg, mask);
        AscendC::Reg::Add(accSum, accSum, chunkSum, scalarMask);
        AscendC::Reg::Max(accMax, newMax, newMax, scalarMask);           // accMax = newMax (copy)
    }

    // pass 2: y = exp(x - max) / sum. Recompute exp (x persists in UB).
    AscendC::Reg::Duplicate<float, AscendC::Reg::HighLowPart::LOWEST,
                             AscendC::Reg::MaskMergeMode::ZEROING>(bcastMax, accMax, fullMask);
    AscendC::Reg::Duplicate<float, AscendC::Reg::HighLowPart::LOWEST,
                             AscendC::Reg::MaskMergeMode::ZEROING>(bcastSum, accSum, fullMask);
    for (uint32_t chunk = 0; chunk < chunkCount; ++chunk) {
        uint32_t offset = chunk * vectorLength;
        uint32_t remaining = count - offset;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remaining);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(xReg, xAddr + offset);
        AscendC::Reg::Sub(xReg, xReg, bcastMax, mask);
        AscendC::Reg::Exp(eReg, xReg, mask);
        AscendC::Reg::Div(yReg, eReg, bcastSum, mask);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(yAddr + offset, yReg, mask);
    }
}
```

revision: 修复后完整函数快照；path: `operators/softmax/softmax.asc`；symbol: `KernelSoftmaxLast<T>::Compute`；lines: 294-311。

```cpp
__aicore__ inline void Compute(uint32_t off)
    {
        (void)off;
        auto xIn = inQueueX_.DeQue<T>();
        auto yOut = outQueueY_.AllocTensor<T>();
        if constexpr (std::is_same_v<T, float>) {
            SoftmaxLastVF((__ubuf__ float *)yOut.GetPhyAddr(), (__ubuf__ float *)xIn.GetPhyAddr(), r_);
        } else {
            auto xFp32 = xFp32Buf_.Get<float>();
            CastInVF<T>((__ubuf__ float *)xFp32.GetPhyAddr(), (__ubuf__ T *)xIn.GetPhyAddr(), r_);
            AscendC::PipeBarrier<PIPE_V>();
            SoftmaxLastVF((__ubuf__ float *)xFp32.GetPhyAddr(), (__ubuf__ float *)xFp32.GetPhyAddr(), r_);
            AscendC::PipeBarrier<PIPE_V>();
            CastOutVF<T>((__ubuf__ T *)yOut.GetPhyAddr(), (__ubuf__ float *)xFp32.GetPhyAddr(), r_);
        }
        outQueueY_.EnQue(yOut);
        inQueueX_.FreeTensor(xIn);
    }
```

## 设计决策

选择把 online max/sum、lane 0 广播和归一化保留在一个 VF 内，避免 V→UB→Scalar→V 的未定义交接。被放弃的三 VF 方案虽然能编译，且 `PipeBarrier<PIPE_V>` 看似合理，但上板出现大面积真实错误；增加更多同类 barrier 没有可用证据能建立 Scalar 可见性。当前方案为 `recommended_fastpath`，三 VF + `GetValue` 路线为 `banned`。

## 系统信息

- toolchain：CANN 9.0.1、毕昇编译器、pytest NPU 测试。
- SoC/NPU arch：Ascend 950、`dav-3510`。
- 相关文件：`operators/softmax/softmax.asc`、`operators/softmax/test_softmax.py`。
- 关键 API：`Reduce`、`StoreAlign`、`LocalTensor::GetValue`、`PipeBarrier<PIPE_V>`、RegTensor 广播 `Duplicate`。

## 预防

- Reg 归约标量若下一步仍是 Vector 计算，优先保留在 RegTensor 中并在同一 VF 广播。
- 不把 `PipeBarrier<PIPE_V>` 自动解释为 Vector 写 UB 对 Scalar `GetValue` 的可见性保证。
- 若只有某条“落 UB→GetValue”路线错误，而纯 VF 路线正常，先检查跨执行域同步，不要放宽精度容差。
- 测试需覆盖多个 dtype 和多行输入，陈旧标量竞态可能表现为部分行正确、部分行异常。

## 验证信号

来源于一次 Ascend 950 RegBase softmax Kernel 开发会话：三 VF + UB 标量槽方案先成功构建，随后真实 NPU pytest 暴露 25 个失败；替换为同一 VF 内的 RegTensor 广播后重新执行构建、完整 pytest 和标准评测。

- 三 VF + `StoreAlign`/`PipeBarrier<PIPE_V>`/`GetValue` 版本能够构建，但上板 pytest 为 25 failed、21 passed，并观测到最大绝对差超过 `1e6`（来源平台: 950；证据等级: tool_observed）。
- 错误集中在末轴路径，使用另一条纯 per-lane VF 路径的用例仍通过（来源平台: 950；证据等级: tool_observed）。
- 改为同一 VF 内 RegTensor 广播后成功链接，完整 pytest 46/46 通过，标准评测 20/20 正确性通过（来源平台: 950；证据等级: tool_observed）。

- 独立复现 R1：去除 vector 写后立即 Scalar GetValue 的跨管线读取后，四组定向 shape/dim 的 values_ok 与 indices_ok 均为 True（950，tool_observed）。
- 独立复现 R2：把跨 VF 的 UB槽→GetValue 标量交接改为同一 VF 内 RegTensor 广播后，修后 NPU pytest 46/46 通过（950，tool_observed）。
- 独立复现 R3：消除 Vector→UB→Scalar 的未完成交接后，cann-bench 最终汇总为 20/20 精度通过（950，tool_observed）。
- 独立复现 R4：把 upcast 后的 PIPE_V 改为 PIPE_ALL，并在 Scalar SetValue 后增加 PIPE_ALL 后，half ties/Inf/NaN、bf16 ties 与 fp32 ties 五组定向探针的 values/indices 均为 True（950，tool_observed）。

## 失效边界

- 结论针对 CANN 9.0.1、Ascend 950 `dav-3510` 上实测的 `StoreAlign`→`GetValue` 交接；其他版本未验证，推断可迁移但需独立 probe。
- 本卡不禁止一般 `GetValue`；只有当值由前一 VF/Vector pipe 刚写入且缺少明确 V→Scalar 同步契约时禁止采用。
- 同一 V pipe 内按程序顺序执行的 VF→VF 依赖不是本卡直接证明的范围。

## 坏实践

- 把 `PipeBarrier<PIPE_V>` 当成任意执行域之间的通用内存栅栏，然后立即在 AICore 标量侧 `GetValue`。
- 为让失败用例通过而放宽 rtol/atol，会掩盖千级异常输出，不能修复同步根因。

## 误诊

- 该现象不是普通浮点累积误差：错误量级超过概率范围，且同行中正常值和巨大异常值并存。
- 该现象也不是测试 harness 问题：替换 Kernel 内跨域交接后，同一测试和参考实现全部通过。

<!-- cannbot:related:start -->
## 相关

- [GetValue](../../apis/simd_api/basic_api/data_structures/local_tensor/get_value.md)（`exemplifies`）：该 Runbook 证明向量流水写 UB 后立即用 GetValue 做标量读取会读到未完成数据，并给出显式 completion 的正确交接顺序。
- [PipeBarrier](../../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《PipeBarrier》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《VF调用》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [asc_vf_call](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《asc_vf_call》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽](regtensor_cross_chunk_state_should_persist_in_ub_slot.md)（`related`）：《RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽》说明同 dtype 标量归约的 Reg Softmax 安全回退：每 VL 一次 VF、UB 槽持久化 max/sum；不适用于同时携带 B16 值与 B32 索引的 cummin/argmin 前缀扫描。；《VF 归约落 UB 后 GetValue 读取陈旧标量》说明Vector 归约结果经 StoreAlign 落 UB 后立即由标量侧 GetValue 读取会出现竞态；保持归约和广播在同一 VF 内可消除错误。。二者在跨VL Reduce必须由AICore wrapper逐次调用并把max/sum持久化到UB；跨chunk累加、同步、offset和RegTensor合同均直接参与修复验证上存在可执行的直接衔接。
- [Scalar读写数据](../../guides/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md)（`related`）：指南中的 Scalar↔UB 访问还需尊重异步 Vector 流水；该卡验证 StoreAlign 后立即 GetValue 会读陈旧标量，并给出完成边界。
- [TBuf 跨 MTE2 与 Vector 须队列交接](tbuf_mte2_to_vector_requires_queue_handoff.md)（`related`）：若 TBuf 数据转由标量侧读取，还需显式完成 Vector/标量流水，而不仅是 MTE2→Vector。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《AR 跨块循环放在 __simd_vf__ 只执行首块》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [GM SetValue 写回后 GetValue 读到旧值](gm_setvalue_getvalue_reads_stale_within_kernel.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《GM SetValue 写回后 GetValue 读到旧值》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [MTE2跨流水未建依赖导致UB读到上次调用残值](direct_mte_slot_reuse_needs_bidirectional_hard_events.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《MTE2跨流水未建依赖导致UB读到上次调用残值》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [Reg 同 wrapper 回读 UB 引发尺寸相关漂移](split_multi_pass_vf_at_ub_producer_consumer_boundaries.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《Reg 同 wrapper 回读 UB 引发尺寸相关漂移》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](fixed_address_vf_accumulator_needs_per_call_barrier.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《Reg 固定地址跨块累加需逐 VF PipeBarrier》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`same_topic`）：VF 归约卡在 Reduce 后把 lane0 落 UB 再从标量侧读取，正好命中另一卡的 VEC Store→Scalar GetValue 未完成竞态；把归约与广播留在同一 VF 可同时修复陈旧标量和未广播 lane。
- [arch35 GetValue/SetValue 标量bypass禁用](../compilation/arch35_getvalue_setvalue_bypass.md)（`same_topic`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《arch35 GetValue/SetValue 标量bypass禁用》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`same_topic`）：arch35 count Compare Select 异步VF 存读 RAW 与《VF 归约落 UB 后 GetValue 读取陈旧标量》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [arch35 小 per-channel 输出读旧值判别与规避](../compilation/arch35_per_channel.md)（`same_topic`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《VF 归约落 UB 后 GetValue 读取陈旧标量》提供“Vector 归约结果经 StoreAlign 落 UB 后立即由标量侧 GetValue 读取会出现竞态；保持归约和广播在同一 VF 内可消除错误。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
<!-- cannbot:related:end -->
