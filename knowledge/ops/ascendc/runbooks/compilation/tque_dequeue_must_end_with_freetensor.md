---
type: "Runbook"
title: "TQue 输入未释放导致循环 AllocTensor 卡死"
description: "循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。"
tags: ["task.debugging", "topic.implementation.pipeline"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# TQue 输入未释放导致循环 AllocTensor 卡死

## 现象

在 Ascend C 直调归约 kernel 的逐行路径中，代码为输入队列配置了有限 depth，并在每轮执行 `AllocTensor → DataCopyPad → EnQue → DeQue → Cast`。远程探针在较少循环时能返回正确结果；扩大循环次数后，命令在 180 秒内不再产生输出，最终只能停止。内核没有新的精度 mismatch，症状是执行无进展。

检查 `example/csrc/ops/softmax/op_kernel/softmax_kernel.cpp` 的 `ProcessARPerRow` 后发现，输出张量在写回后调用了 `outQueueY_.FreeTensor`，而输入张量从 `inQueueX_` 取出并完成 Cast 后从未调用 `inQueueX_.FreeTensor`。这使问题与计算公式、数值精度和远程 harness 区分开来。

## 适用场景

- 工程形态：Ascend C kernel 直调，循环体内使用 `TPipe/TQue` 搬入并消费输入 Tensor；
- API 路径：`TQue::AllocTensor`、`EnQue`、`DeQue`、`FreeTensor`；
- 验证过的平台与版本：950（Ascend 950PR）/ CANN 9.0.1，与 frontmatter `platforms` 一致；
- 适用粒度：`platform_wide`，约束来自 TQue buffer 生命周期，不依赖具体算子数学语义；
- 路线优先级：`recommended_fastpath`，及时归还已消费 Tensor 是循环流水的正确生命周期基线；
- 明确不适用：没有使用 TQue 的裸 LocalTensor/TBuf 路径，或 Tensor 仍被后续异步指令读取、尚未到安全释放点的代码；A2、A3 与其他 CANN 版本未验证。

## 根因

`DeQue` 只把已入队 Tensor 交给消费者，不等于把底层 buffer 归还给队列；循环在消费完成后遗漏 `FreeTensor`，有限 depth 的输入 buffer 被逐轮占用，后续 `AllocTensor` 无空闲 buffer 可分配而无进展。

机制链为：`AllocTensor` 占用空闲 buffer → `EnQue/DeQue` 完成生产者到消费者的所有权传递 → 消费者未 `FreeTensor` → 空闲 buffer 数每轮减一 → 空闲数归零 → 下一轮 `AllocTensor` 等待。因而“小循环正常、超过队列容量后稳定卡住”是这个根因的关键判别信号。

## 解决配方

在最后一次读取输入 LocalTensor 的指令已发出之后、进入下一轮 `AllocTensor` 之前，立即调用对应输入队列的 `FreeTensor`。不要把输出侧的 `FreeTensor` 当成输入侧也已释放；每个 `DeQue` 得到的 Tensor 都要沿所属队列闭合生命周期。

### before

代码证据：revision=`uncommitted trace snapshot before fix`；path=`example/csrc/ops/softmax/op_kernel/softmax_kernel.cpp`；symbol=`KernelSoftmax<T>::ProcessARPerRow`；line span=`285-353`。以下函数由完整 file-edit 事件逐字恢复。

```cpp
    __aicore__ inline void ProcessARPerRow(int64_t row)
    {
        int64_t rAlign = tiling_.rAlign;
        int64_t rLen = tiling_.rLength;
        auto padParams = AscendC::DataCopyPadExtParams<T>{true, 0,
            static_cast<uint8_t>(rAlign - rLen), 0};

        // 1. CopyIn: GM → UB (raw dtype)
        AscendC::DataCopyExtParams copyParams{1,
            static_cast<uint32_t>(rLen * sizeof(T)), 0, 0, 0};
        auto xRawLocal = inQueueX_.AllocTensor<T>();
        AscendC::DataCopyPad(xRawLocal, xGm_[row * rLen], copyParams, padParams);
        inQueueX_.EnQue(xRawLocal);
        xRawLocal = inQueueX_.DeQue<T>();

        // 2. Cast → fp32 (if needed)
        auto xFp32 = xFp32Buf_.Get<float>();
        auto zFp32 = zFp32Buf_.Get<float>();
        auto expFp32 = expFp32Buf_.Get<float>();
        auto tmpFloat = tmpBuf_.Get<float>();
        auto tmpUint8 = tmpBuf_.Get<uint8_t>();
        auto scalarLocal = scalarBuf_.Get<float>();

        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopy(xFp32, xRawLocal, rAlign);
        } else {
            AscendC::Cast(xFp32, xRawLocal, AscendC::RoundMode::CAST_NONE,
                          static_cast<int32_t>(rAlign));
        }

        // 3. ReduceMax → maxScalar
        AscendC::ReduceMax<float>(scalarLocal, xFp32, tmpFloat,
                                  static_cast<int32_t>(rLen), false);
        float maxVal = scalarLocal.GetValue(0);

        // 4. z = x - max
        AscendC::Adds<float>(zFp32, xFp32, -maxVal,
                             static_cast<int32_t>(rAlign));

        // 5. Exp (dst ≠ src)
        AscendC::Exp<float, 0, false>(expFp32, zFp32, tmpUint8,
                                       static_cast<uint32_t>(rAlign));

        // 6. ReduceSum → sumScalar
        AscendC::ReduceSum<float>(scalarLocal, expFp32, tmpFloat,
                                  static_cast<int32_t>(rLen));
        float sumVal = scalarLocal.GetValue(0);

        // 7. y = exp * (1/sum)  (in-place on expFp32)
        float invSum = 1.0f / sumVal;
        AscendC::Muls<float>(expFp32, expFp32, invSum,
                            static_cast<int32_t>(rAlign));

        // 8. Cast back to T (if needed) + 9. CopyOut
        auto yRawLocal = outQueueY_.AllocTensor<T>();
        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopy(yRawLocal, expFp32, rAlign);
        } else {
            constexpr auto roundMode = std::is_same<T, bfloat16_t>::value
                ? AscendC::RoundMode::CAST_RINT
                : AscendC::RoundMode::CAST_ROUND;
            AscendC::Cast(yRawLocal, expFp32, roundMode,
                          static_cast<int32_t>(rAlign));
        }
        outQueueY_.EnQue<T>(yRawLocal);
        yRawLocal = outQueueY_.DeQue<T>();
        AscendC::DataCopyPad(yGm_[row * rLen], yRawLocal, copyParams);
        outQueueY_.FreeTensor(yRawLocal);
    }
```

### after

代码证据：revision=`uncommitted final trace snapshot`；path=`example/csrc/ops/softmax/op_kernel/softmax_kernel.cpp`；symbol=`KernelSoftmax<T>::ProcessARPerRow`；line span=`285-354`。以下函数由后续 reviewer 的完整文件读取逐字恢复；唯一生命周期修复位于 Cast/DataCopy 之后。

```cpp
    __aicore__ inline void ProcessARPerRow(int64_t row)
    {
        int64_t rAlign = tiling_.rAlign;
        int64_t rLen = tiling_.rLength;
        auto padParams = AscendC::DataCopyPadExtParams<T>{true, 0,
            static_cast<uint8_t>(rAlign - rLen), 0};

        // 1. CopyIn: GM → UB (raw dtype)
        AscendC::DataCopyExtParams copyParams{1,
            static_cast<uint32_t>(rLen * sizeof(T)), 0, 0, 0};
        auto xRawLocal = inQueueX_.AllocTensor<T>();
        AscendC::DataCopyPad(xRawLocal, xGm_[row * rLen], copyParams, padParams);
        inQueueX_.EnQue(xRawLocal);
        xRawLocal = inQueueX_.DeQue<T>();

        // 2. Cast → fp32 (if needed)
        auto xFp32 = xFp32Buf_.Get<float>();
        auto zFp32 = zFp32Buf_.Get<float>();
        auto expFp32 = expFp32Buf_.Get<float>();
        auto tmpFloat = tmpBuf_.Get<float>();
        auto tmpUint8 = tmpBuf_.Get<uint8_t>();
        auto scalarLocal = scalarBuf_.Get<float>();

        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopy(xFp32, xRawLocal, rAlign);
        } else {
            AscendC::Cast(xFp32, xRawLocal, AscendC::RoundMode::CAST_NONE,
                          static_cast<int32_t>(rAlign));
        }
        inQueueX_.FreeTensor(xRawLocal);

        // 3. ReduceMax → maxScalar
        AscendC::ReduceMax<float>(scalarLocal, xFp32, tmpFloat,
                                  static_cast<int32_t>(rLen), false);
        float maxVal = scalarLocal.GetValue(0);

        // 4. z = x - max
        AscendC::Adds<float>(zFp32, xFp32, -maxVal,
                             static_cast<int32_t>(rAlign));

        // 5. Exp (dst ≠ src)
        AscendC::Exp<float, 0, false>(expFp32, zFp32, tmpUint8,
                                       static_cast<uint32_t>(rAlign));

        // 6. ReduceSum → sumScalar
        AscendC::ReduceSum<float>(scalarLocal, expFp32, tmpFloat,
                                  static_cast<int32_t>(rLen));
        float sumVal = scalarLocal.GetValue(0);

        // 7. y = exp * (1/sum)  (in-place on expFp32)
        float invSum = 1.0f / sumVal;
        AscendC::Muls<float>(expFp32, expFp32, invSum,
                            static_cast<int32_t>(rAlign));

        // 8. Cast back to T (if needed) + 9. CopyOut
        auto yRawLocal = outQueueY_.AllocTensor<T>();
        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopy(yRawLocal, expFp32, rAlign);
        } else {
            constexpr auto roundMode = std::is_same<T, bfloat16_t>::value
                ? AscendC::RoundMode::CAST_RINT
                : AscendC::RoundMode::CAST_ROUND;
            AscendC::Cast(yRawLocal, expFp32, roundMode,
                          static_cast<int32_t>(rAlign));
        }
        outQueueY_.EnQue<T>(yRawLocal);
        yRawLocal = outQueueY_.DeQue<T>();
        AscendC::DataCopyPad(yGm_[row * rLen], yRawLocal, copyParams);
        outQueueY_.FreeTensor(yRawLocal);
    }
```

## 设计决策

- 选择在 Cast/DataCopy 后立即释放输入 Tensor：该位置已完成对 `xRawLocal` 的最后一次读取，后续计算只依赖 `xFp32`，能够尽早归还 buffer，又不破坏数据依赖；
- 没有通过增大 TQue depth 掩盖问题：增大 depth 只会推迟耗尽，不能闭合消费者生命周期；
- 没有把跨行批量向量化当成本卡修复：批量路径改变了算法调度且与本根因并非一一对应，本卡只记录可由定向探针隔离的 `FreeTensor` 修复；
- 当前方案为 `recommended_fastpath`，属于正确性与资源生命周期基线。

## 系统信息

- toolchain：CANN 9.0.1，Ascend C 直调工程，kernel 由 bisheng `-xasc` 编译；
- 目标平台：Ascend 950PR，物理卡经容器映射为逻辑设备；
- 相关文件：`example/csrc/ops/softmax/op_kernel/softmax_kernel.cpp`；
- 相关函数：`KernelSoftmax<T>::InitAR` 配置输入 TQue，`KernelSoftmax<T>::ProcessARPerRow` 循环消费并释放 Tensor。

## 预防

- 对每个 `AllocTensor` 建立局部生命周期表：所属队列、`EnQue`、`DeQue`、最后读取点、`FreeTensor`；
- 审查循环 kernel 时逐队列核对 `DeQue` 与同队列 `FreeTensor`，不要只检查输出队列；
- “少量循环正确、循环次数增加后无进展”优先检查 queue depth 与 Tensor 归还，不先改计算公式；
- 修复后至少做一个超过队列 depth 的递增规模探针，确保不是只让最小 case 通过。

## 验证信号

本知识来自一次 Ascend 950PR 直调归约 kernel 的开发会话：先用定向上板探针复现循环规模增加后的无进展，再补齐输入队列 `FreeTensor`，最后执行同类探针与完整评测。

- 修复前，探针只输出较小规模 fp16/fp32 的 `pass=True`，进入更长循环后 180 秒内没有后续输出并被停止（950 / CANN 9.0.1，证据等级: tool_observed）；
- 修复后，同类探针对 fp16/fp32 的六组递增规模组合全部输出 `pass=True`，并返回 `ALL TESTS PASSED`（950 / CANN 9.0.1，证据等级: tool_observed）；
- 最终 cann-bench 重新编译并完成 20/20 精度用例，未再出现该挂起（950 / CANN 9.0.1，证据等级: tool_observed）。

## 失效边界

- `FreeTensor` 必须放在该 LocalTensor 的最后一次消费之后；如果后续异步操作仍读取它，提前释放会引入复用覆盖风险；
- 本卡只证明 TQue 生命周期缺口会造成循环无进展，不把同轮出现的所有设备错误或性能低下都归因于该缺口；
- A2、A3 与其他 CANN 版本未验证，推断可迁移但必须重新上板确认。

## 坏实践

- 只写 `AllocTensor/EnQue/DeQue`，认为 `DeQue` 会自动释放 buffer；`DeQue` 是消费侧取出，不是归还；
- 通过增大 queue depth 或减少循环次数绕过挂起；这只改变触发阈值，资源仍会耗尽；
- 看到 kernel 无进展就直接归因于标量同步慢；应先核对每个队列的 buffer 生命周期。

## 误诊

开发过程中曾把规模增大后的无进展主要归因于逐行 `GetValue` 同步开销，并先引入跨行批量路径。后续定向探针显示：超过少量循环后稳定无进展，代码审计又发现输入侧唯一缺少 `FreeTensor`；补齐后同类探针立即全部完成。因此“标量同步慢”不能替代本卡的生命周期根因。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](../../apis/simd_api/basic_api/resource_management/t_que/alloc_tensor.md)（`exemplifies`）：AllocTensor 消费队列空闲块，若前次 DeQue 未 Free 则后续分配无可用块；这是挂死的直接资源机制。
- [AllocTensor](../../apis/simd_api/basic_api/resource_management/t_que_bind/alloc_tensor.md)（`exemplifies`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《TQue 输入未释放导致循环 AllocTensor 卡死》提供“循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [DeQue](../../apis/simd_api/basic_api/resource_management/t_que_bind/de_que.md)（`exemplifies`）：Runbook 证明 DeQue 后漏 FreeTensor 会耗尽队列资源并导致后续执行卡死。
- [DeQue](../../apis/simd_api/basic_api/resource_management/tscm/de_que.md)（`exemplifies`）：DeQue 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [EnQue](../../apis/simd_api/basic_api/resource_management/t_que_bind/en_que.md)（`exemplifies`）：EnQue→DeQue 后还需 FreeTensor 归还 buffer；该卡证明遗漏释放会耗尽队列并阻塞后续 AllocTensor，闭合生产消费生命周期。
- [FreeTensor](../../apis/simd_api/basic_api/resource_management/t_que/free_tensor.md)（`exemplifies`）：《TQue 输入未释放导致循环 AllocTensor 卡死》给出“循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。”；该约束/探针可直接复现、解释或前置验证《FreeTensor》中的“释放Que中的指定Tensor，需与AllocTensor配对使用。”。
- [TSCM](../../apis/simd_api/basic_api/resource_management/tscm/tscm.md)（`exemplifies`）：TSCM 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [FreeTensor早释使队列别名被下一轮DMA覆盖](../precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`related`）：不能早释不等于不释放；该卡补充循环 DeQue 若缺少最终 FreeTensor 会耗尽队列并卡死。
- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方 负责“ascend910b 上 HardSwish 算子的可复用实现：2 个 TQue in-place、单 tile 快速路径、5 指令序列、remainder 均衡分块；15 测试点全部 Pass”；TQue 输入未释放导致循环 AllocTensor 卡死 负责“循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor”。
- [TBuf 跨 MTE2 与 Vector 须队列交接](../precision/tbuf_mte2_to_vector_requires_queue_handoff.md)（`related`）：改用 TQue 交接后必须在消费结束 FreeTensor，否则正确同步会换成队列耗尽问题。
- [TPipe和TQue编程范式](../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TQue 输入未释放导致循环 AllocTensor 卡死》说明循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [Vector 结果搬出前须经 VECOUT 队列](../precision/vector_results_need_vecout_queue_before_mte3.md)（`related`）：VecOut 队列消费完成后必须 FreeTensor，避免正确交接后队列耗尽。
- [运行验证时AllocTensor/FreeTensor失败](../../guides/programming_guide/appendix/faq/alloc_free_tensor_failure.md)（`related`）：FAQ 给出 Alloc/Free 失败与挂死的观测日志，可用于确认是否为 buffer 未归还而非计算耗时。
- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](tque_dequeue_requires_prior_enqueue_507035.md)（`same_topic`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [TQue tensor 所有权只能 DeQue 一次](tque_tensor_ownership_single_dequeue.md)（`same_topic`）：TQue tensor 所有权只能 DeQue 一次 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
<!-- cannbot:related:end -->
