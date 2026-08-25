---
type: "Runbook"
title: "TBuf 跨 MTE2 与 Vector 须队列交接"
description: "GM 数据写入裸 TBuf 后立刻由 V pipe 消费时，A3 与 Ascend950 的独立轨迹均出现数值错误、NaN 或非有限值位置不一致；改为 VECIN TQue 交接后定向及完整测试通过。"
tags: ["task.debugging", "topic.implementation.synchronization", "topic.implementation.pipeline", "topic.data_movement.data_copy", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3", "950"]
---

# TBuf 跨 MTE2 与 Vector 须队列交接

## 现象

多条 A3 与 Ascend950 轨迹都在“GM 经 MTE2 写入裸 TBuf，随后由 V pipe 立即消费”的路径上失败：cos/sin 隔离探针与参考不一致，gamma 路径的设备结果与 golden 非有限值位置不一致，950 Softmax 路径则出现 NaN、极值或不归一化输出。改为 VECIN TQue 的 EnQue/DeQue 交接后，各轨迹的定向或完整测试均闭合。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的定向精度调试。
- API 路径：`DataCopyPad`、`TBuf`、`TQue`、`MTE2` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：a3（CANN 版本未记录）与 950（CANN 9.0.1）。
- 适用粒度：`operator_family`，只迁移卡内同一机制，不外推到未验证 dtype、layout 或执行路径。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

`DataCopyPad(gammaRaw, gammaGm_)` 由 MTE2 异步写 UB，紧随其后的 `Cast(gammaFp32, gammaRaw)` 由 V pipe 读取。裸 TBuf 没有在这两个调用之间表达生产者到消费者的队列交接；本次会话中，改为 TQue 的 EnQue/DeQue 后原非有限值位置不一致消失。该单跑只支持这条数据路径的因果闭环，不外推为所有 TBuf 的版本规范。

## 解决配方

### before

```cpp
    __aicore__ inline void LoadGamma()
    {
        uint32_t bytesPerRow = static_cast<uint32_t>(numCol_ * sizeof(T));
        AscendC::DataCopyExtParams copyParams{1, bytesPerRow, 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> padParams{false, 0, 0, 0};
        auto gammaFp32 = gammaFp32Buf_.Get<float>();
        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopyPad(gammaFp32, gammaGm_, copyParams, padParams);
        } else {
            auto gammaRaw = gammaRawBuf_.Get<T>();
            AscendC::DataCopyPad(gammaRaw, gammaGm_, copyParams, padParams);
            AscendC::Cast(gammaFp32, gammaRaw, AscendC::RoundMode::CAST_NONE, numCol_);
            AscendC::PipeBarrier<PIPE_V>();
        }
    }
```

配套声明：before 的低精度分支在 `Init` 中 `InitBuffer(gammaRawBuf_, bytesPerRow)`，成员是 `TBuf<VECCALC> gammaRawBuf_`。

### after

```cpp
    __aicore__ inline void LoadGamma()
    {
        uint32_t bytesPerRow = static_cast<uint32_t>(numCol_ * sizeof(T));
        AscendC::DataCopyExtParams copyParams{1, bytesPerRow, 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> padParams{false, 0, 0, 0};
        auto gammaFp32 = gammaFp32Buf_.Get<float>();
        if constexpr (std::is_same<T, float>::value) {
            AscendC::DataCopyPad(gammaFp32, gammaGm_, copyParams, padParams);
        } else {
            // Load raw gamma through a TQue so EnQue/DeQue provides the
            // MTE2->V sync the Cast needs (a bare TBuf DataCopyPad here would
            // race the immediately-following vector Cast).
            auto gammaRaw = inQueueGamma_.AllocTensor<T>();
            AscendC::DataCopyPad(gammaRaw, gammaGm_, copyParams, padParams);
            inQueueGamma_.EnQue(gammaRaw);
            gammaRaw = inQueueGamma_.DeQue<T>();
            AscendC::Cast(gammaFp32, gammaRaw, AscendC::RoundMode::CAST_NONE, numCol_);
            AscendC::PipeBarrier<PIPE_V>();
            inQueueGamma_.FreeTensor(gammaRaw);
        }
    }
```

配套声明：after 在相同 `if constexpr` 中改为 `InitBuffer(inQueueGamma_, 1, bytesPerRow)`，成员改为 `TQue<VECIN, PIPELINE_DEPTH> inQueueGamma_`。

## 设计决策

常驻 gamma 最终仍保存在 fp32 TBuf，只把“原始低精度 gamma 的 DMA→Cast 交接”放进 VECIN TQue。这样既获得事件同步，也避免让常驻缓冲占用队列生命周期。

## 性能影响

初始化每核只执行一次，增加一次 EnQue/DeQue 与队列槽；轨迹没有配对性能数据，不主张性能收益。

## 预防

- 逐条列出 MTE2 写入后首个消费者属于哪条流水；
- GM→UB 后若紧跟 V 操作，优先采用匹配位置的 TQue 交接；
- dtype 分支分别测试，不能用 fp32 通过推断低精度初始化也安全。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 复现一修复前：补齐逻辑偏移后的 cos/sin 隔离探针中，参考值前半段与 NPU 输出不一致、后半段一致，`maxdiff=9.788...`（来源平台：a3；证据等级: tool_observed）。
- 复现一修复后：TQue EnQue/DeQue handoff 后定向探针与参考逐元素一致，`maxdiff=0`（来源平台：a3；证据等级: tool_observed）。
- 复现一修复后：clean build 后完整测试 `18 passed`（来源平台：a3；证据等级: tool_observed）。
- 复现二修复前：NaN 输入路径的设备结果与 golden 非有限值位置不一致（来源平台：a3；证据等级: tool_observed）。
- 复现二修复后：改用 TQue handoff 后完整测试列表全部 `PASSED`（来源平台：a3；证据等级: tool_observed）。
- 950 Softmax 路径改用 TQue 后，定向回归从 1/49 提升到 18/49；修复其余独立根因且保持队列交接不变后 49/49 通过（来源平台：950；证据等级: tool_observed）。
- 950 的另外两条独立轨迹在相同改法后分别 40/40 与 58/58 通过（来源平台：950；证据等级: tool_observed）。

## 失效边界

本卡只证明 A3 与 950 上已列出的初始化路径。不同 TPosition、显式 SetFlag/WaitFlag、其他架构或编译器的事件语义须独立验证。若 DMA 与首个 V 读之间已有可靠队列依赖，不能重复套用本修复。

## 坏实践

- 把 `PipeBarrier<PIPE_V>` 放在 Cast 之后，误以为它能补上 Cast 之前缺失的 MTE2→V 依赖；
- 用 fp32 分支正常作为裸 TBuf 初始化安全的证据；
- 只检查 Cast 支持矩阵，不检查生产者与消费者流水同步。

## 误诊

若修复后非有限值位置仍不一致，先把 gamma 搬运与规约标量路径分别做独立探针，不能继续把错误归到同一交接点。

<!-- cannbot:related:start -->
## 相关

- [DeQue](../../apis/simd_api/basic_api/resource_management/tscm/de_que.md)（`exemplifies`）：DeQue 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [asc_sync（同步）](../../apis/simd_api/c_api/sync/asc_sync.md)（`exemplifies`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《TBuf 跨 MTE2 与 Vector 须队列交接》明确提供“GM 数据写入裸 TBuf 后立刻由 V pipe 消费时，A3 与 Ascend950 的独立轨迹均出现数值错误、NaN 或非有限值位置不一致；改为 VECIN TQue 交接后定向及完整测试通过。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [FreeTensor早释使队列别名被下一轮DMA覆盖](reinterpret_tensor_alias_must_outlive_queue_release.md)（`related`）：别名所有权窗口和 MTE2 到 Vector 的队列交接共同保证消费者既读到已就绪数据，也不会读到复用后的数据。
- [InitOutput GM 专用，UB 清零用 Duplicate](../compilation/initoutput_gm_ub_duplicate.md)（`related`）：InitOutput GM 专用，UB 清零用 Duplicate 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [TBuf 不能直接传给 LocalTensor 形参](../compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`related`）：TBuf 直取 typed LocalTensor 可解决类型传递，但仍不建立 MTE2→Vector 依赖；两卡明确类型与同步是独立契约。
- [TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位](../compilation/tque_mte2_mte3_mte3_mte2_fence.md)（`related`）：若用 TBuf 而非 TQue，MTE2→Vector 没有自动队列依赖；该卡给出需要改队列或显式 barrier 的边界。
- [TQue tensor 所有权只能 DeQue 一次](../compilation/tque_tensor_ownership_single_dequeue.md)（`related`）：TQue tensor 所有权只能 DeQue 一次 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../compilation/tque_dequeue_must_end_with_freetensor.md)（`related`）：改用 TQue 交接后必须在消费结束 FreeTensor，否则正确同步会换成队列耗尽问题。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](vector_scalar_ub_handoff_requires_explicit_completion.md)（`related`）：若 TBuf 数据转由标量侧读取，还需显式完成 Vector/标量流水，而不仅是 MTE2→Vector。
- [Vector 结果搬出前须经 VECOUT 队列](vector_results_need_vecout_queue_before_mte3.md)（`related`）：反向 Vector→MTE3 需 VecOut 队列交接，和本卡组成 copy-in/compute/copy-out 两端的流水所有权。
- [arch35 小 per-channel 输出读旧值判别与规避](../compilation/arch35_per_channel.md)（`related`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《TBuf 跨 MTE2 与 Vector 须队列交接》提供“GM 数据写入裸 TBuf 后立刻由 V pipe 消费时，A3 与 Ascend950 的独立轨迹均出现数值错误、NaN 或非有限值位置不一致；改为 VECIN TQue 交接后定向及完整测试通过。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [按序列位缓存 cos/sin 并让 q/k 共享搬运](../performance/cache_position_coefficients_across_shared_inputs.md)（`related`）：The caching design loads cos/sin through an MTE2-to-Vector handoff before keeping them resident; this runbook verifies that a bare TBuf can race and that TQue EnQue/DeQue closes the dependency.
- [标量 S pipe 误用 TQue 导致输出全常数](scalar_s_pipe_requires_explicit_mte_dependencies.md)（`related`）：TBuf→Vector 卡证明裸 TBuf 不自动建立 MTE2→V 依赖；本卡把同一对象管理边界延伸到 MTE2→S 与 S→MTE3，并解释为何 V-only TQue 事件仍不足。
- [BF16 gamma Cast 分阶段编排导致随机 NaN](bf16_gamma_cast_must_share_ordered_compute_stage.md)（`same_topic`）：候选说明裸 TBuf 跨 MTE2 与 Vector 缺队列交接会读未就绪数据，本卡分阶段 gamma/x Cast 是同类边界。
- [DataCopyPad 后未先同步 Cast 导致低精度 NaN](mte2_barrier_must_precede_vector_cast.md)（`same_topic`）：两卡都要求 MTE2 写 UB 完成后才能由 Vector 读取；barrier 卡给出不用队列时的显式同步边界。
- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../compilation/vector_sub_ub_32b_340.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
<!-- cannbot:related:end -->
