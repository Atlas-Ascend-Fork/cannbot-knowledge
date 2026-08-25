---
type: "Runbook"
title: "dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数"
description: "RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。"
tags: ["task.optimization", "topic.compute.normalization", "topic.compute.elementwise.math_function", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
aliases: ["KernelRmsNorm::Compute"]
---

# dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数

## 现象

RmsNorm 的 fp32 用例出现约 `1e-2` 最大输出差，而 fp16/bf16 因容差较宽可能通过。确定性 `x=1, gamma=1, eps=1e-6` 探针跨多个短、长归约长度都给出 `rstd=0.998046875`，期望约 `0.9999995`；随机输入也出现 `1.03515625` 对 `1.03701699` 的稳定偏差。整齐的二进制量化值是快速倒数精度不足的判别信号。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的定向精度调试。
- API 路径：`AscendC::Rsqrt`、`AscendC::Sqrt`、`dav-2201`、`rstd` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`operator_family`，只迁移卡内同一机制，不外推到未验证 dtype、layout 或执行路径。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

本轨迹中不带 config 的 `Rsqrt<float>` 在 dav-2201 上产生约 9-bit 量级的快速倒数结果。规约、均值和加 epsilon 链条随 D 正常变化，且固定 ones 输入对所有 D 得到相同低精度 rstd，排除了行索引、ReduceSum 除数和随机噪声。单指令近似精度不足是唯一根因。

## 解决配方

### before

```cpp
    __aicore__ inline void Compute(int64_t r)
    {
        (void)r;
        auto scalar = scalarBuf_.Get<float>();
        auto sq = sqBuf_.Get<float>();
        auto dummy = dummyBuf_.Get<float>();

        if constexpr (std::is_same<T, float>::value) {
            auto xFp32 = inQueueX_.DeQue<float>();
            AscendC::Mul(sq, xFp32, xFp32, numCol_);                              // x^2
            AscendC::ReduceSum<float>(scalar, sq, dummy, numCol_);               // sum(x^2)
            AscendC::PipeBarrier<PIPE_V>();
            AscendC::Muls(scalar, scalar, 1.0f / static_cast<float>(numCol_), 1); // mean
            AscendC::Adds(scalar, scalar, epsilon_, 1);                         // mean + eps
            AscendC::Rsqrt<float>(scalar, scalar, 1);                           // rstd = 1/sqrt(mean+eps)
            AscendC::PipeBarrier<PIPE_V>();
            float rstd = scalar.GetValue(0);

            auto yOut = outQueueY_.AllocTensor<float>();
            AscendC::Muls(yOut, xFp32, rstd, numCol_);                          // x * rstd
            AscendC::Mul(yOut, yOut, gammaFp32Local_, numCol_);                 // * gamma
            outQueueY_.EnQue(yOut);
            inQueueX_.FreeTensor(xFp32);
        } else {
            auto xT = inQueueX_.DeQue<T>();
            auto xFp32 = xFp32Buf_.Get<float>();
            AscendC::Cast(xFp32, xT, AscendC::RoundMode::CAST_NONE, numCol_);  // x -> fp32
            inQueueX_.FreeTensor(xT);
            AscendC::Mul(sq, xFp32, xFp32, numCol_);                            // x^2
            AscendC::ReduceSum<float>(scalar, sq, dummy, numCol_);              // sum(x^2)
            AscendC::PipeBarrier<PIPE_V>();
            AscendC::Muls(scalar, scalar, 1.0f / static_cast<float>(numCol_), 1); // mean
            AscendC::Adds(scalar, scalar, epsilon_, 1);                        // mean + eps
            AscendC::Rsqrt<float>(scalar, scalar, 1);                          // rstd = 1/sqrt(mean+eps)
            AscendC::PipeBarrier<PIPE_V>();
            float rstd = scalar.GetValue(0);

            AscendC::Muls(sq, xFp32, rstd, numCol_);                           // y = x * rstd (reuse sqBuf)
            AscendC::Mul(sq, sq, gammaFp32Buf_.Get<float>(), numCol_);         // * gamma
            auto yOutT = outQueueY_.AllocTensor<T>();
            constexpr auto roundMode = std::is_same<T, bfloat16_t>::value
                ? AscendC::RoundMode::CAST_RINT : AscendC::RoundMode::CAST_NONE;
            AscendC::Cast(yOutT, sq, roundMode, numCol_);                      // y -> T
            outQueueY_.EnQue(yOutT);
        }
    }
```

### after

```cpp
    __aicore__ inline void Compute(int64_t r)
    {
        (void)r;
        auto scalar = scalarBuf_.Get<float>();
        auto sq = sqBuf_.Get<float>();
        auto dummy = dummyBuf_.Get<float>();

        if constexpr (std::is_same<T, float>::value) {
            auto xFp32 = inQueueX_.DeQue<float>();
            AscendC::Mul(sq, xFp32, xFp32, numCol_);                              // x^2
            AscendC::ReduceSum<float>(scalar, sq, dummy, numCol_);               // sum(x^2)
            AscendC::PipeBarrier<PIPE_V>();
            AscendC::Muls(scalar, scalar, 1.0f / static_cast<float>(numCol_), 1); // mean
            AscendC::Adds(scalar, scalar, epsilon_, 1);                         // mean + eps
            AscendC::Sqrt(scalar, scalar, 1);                                  // sqrt(mean+eps)
            AscendC::PipeBarrier<PIPE_V>();
            float s = scalar.GetValue(0);
            float rstd = 1.0f / s;  // rstd = 1/sqrt(mean+eps); NaN/inf propagate (mean+eps >= eps > 0 for finite)

            auto yOut = outQueueY_.AllocTensor<float>();
            AscendC::Muls(yOut, xFp32, rstd, numCol_);                          // x * rstd
            AscendC::Mul(yOut, yOut, gammaFp32Local_, numCol_);                 // * gamma
            outQueueY_.EnQue(yOut);
            inQueueX_.FreeTensor(xFp32);
        } else {
            auto xT = inQueueX_.DeQue<T>();
            auto xFp32 = xFp32Buf_.Get<float>();
            AscendC::Cast(xFp32, xT, AscendC::RoundMode::CAST_NONE, numCol_);  // x -> fp32
            inQueueX_.FreeTensor(xT);
            AscendC::Mul(sq, xFp32, xFp32, numCol_);                            // x^2
            AscendC::ReduceSum<float>(scalar, sq, dummy, numCol_);              // sum(x^2)
            AscendC::PipeBarrier<PIPE_V>();
            AscendC::Muls(scalar, scalar, 1.0f / static_cast<float>(numCol_), 1); // mean
            AscendC::Adds(scalar, scalar, epsilon_, 1);                        // mean + eps
            AscendC::Sqrt(scalar, scalar, 1);                                 // sqrt(mean+eps)
            AscendC::PipeBarrier<PIPE_V>();
            float s = scalar.GetValue(0);
            float rstd = 1.0f / s;  // rstd = 1/sqrt(mean+eps); NaN/inf propagate (mean+eps >= eps > 0 for finite)

            AscendC::Muls(sq, xFp32, rstd, numCol_);                           // y = x * rstd (reuse sqBuf)
            AscendC::Mul(sq, sq, gammaFp32Buf_.Get<float>(), numCol_);         // * gamma
            auto yOutT = outQueueY_.AllocTensor<T>();
            constexpr auto roundMode = std::is_same<T, bfloat16_t>::value
                ? AscendC::RoundMode::CAST_RINT : AscendC::RoundMode::CAST_NONE;
            AscendC::Cast(yOutT, sq, roundMode, numCol_);                      // y -> T
            outQueueY_.EnQue(yOutT);
        }
    }
```

## 设计决策

保留 fp32 规约与既有缓冲，只替换 rstd 的最后一步，避免把精度问题误治为 tiling 或 Cast 问题。有限输入下 `mean+eps > 0`，无需 `s>0` 保护；该保护会在 `s=NaN` 时错误选择 0，破坏整行 NaN 传播。

## 性能影响

新路线增加一次标量读回和标量除法，轨迹未提供配对性能数据；本卡只主张精度恢复，不主张性能收益。

## 预防

- 对快速倒数/倒数平方根 API 用 `x=1` 和非整平方输入做目标平台精度探针；
- 分 dtype 检查，避免低精度宽容差掩盖 fp32 的系统偏差；
- 不把其他平台或带 config 形态的精度承诺迁移到当前调用形态。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：default-eps fp32 有限值最大差 1.315689e-02，边界子集汇总 5 failed、5 passed。（来源平台：a3；证据等级: tool_observed）。
- 修复后：Sqrt+标量倒数实现及 NaN 传播修正后完整 NPU 测试 167 passed。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

该结论只在 a3 路径验证，不覆盖 a2、950、带精度 config 的 API 或其他 CANN 版本；扩展平台前须按目标设备精确判型并复测。

## 坏实践

- 看到 `Rsqrt<float>` 就假设结果具有完整 fp32 精度；
- 只跑 fp16/bf16 用例，用宽容差宣布数值路径正确；
- 用 `s>0 ? 1/s : 0` 保护有限域，却忽略 NaN 比较恒为 false 会破坏传播。

## 误诊

若 rstd 误差随 D、行号或输入地址随机变化，先查规约、同步和索引；本问题的特征是同一数学输入得到稳定、整齐的低精度量化值。

<!-- cannbot:related:start -->
## 相关

- [AscRsqrt](../../apis/simd_api/c_api/vector_compute/asc_rsqrt.md)（`exemplifies`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数正文界定“RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [AscSqrt](../../apis/simd_api/c_api/reg/arithmetic_compute/asc_sqrt.md)（`exemplifies`）：AscSqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
- [H2Rsqrt](../../apis/simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2rsqrt.md)（`exemplifies`）：H2Rsqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：H2Rsqrt 与 sqrt/rcp、half/float Rsqrt 及精度替代卡共同界定倒数平方根实现。
- [Hrsqrt](../../apis/simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`exemplifies`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》说明RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Hrsqrt](../../apis/simt_api/math_functions/half_type/half_math_functions/hrsqrt.md)（`exemplifies`）：Hrsqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：Hrsqrt 可由 Hsqrt 与 Hrcp 分解；精度故障卡给出该替换在实测误差超限时的可执行验证。
- [Reciprocal](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/reciprocal.md)（`exemplifies`）：Reciprocal 提供同类倒数接口对照；本卡最终选标量 1.0f/s，避免再次引入快速近似。
- [RmsNorm](../../apis/simd_api/adv_api/normalization/rms_norm.md)（`exemplifies`）：本卡只替换 RmsNorm rstd 末端，规约、均值、epsilon 链不变。
- [RmsNorm Tiling](../../apis/simd_api/adv_api/normalization/rms_norm_tiling.md)（`exemplifies`）：RmsNorm Tiling 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：RmsNorm host tiling 直接生成 RmsNorm kernel 参数；同名结构体冲突、NaN/Rsqrt 与 UB 预算卡都作用于这套 tiling/kernel 契约。
- [Rsqrt](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/rsqrt.md)（`exemplifies`）：低精度信号来自不带 config 的 AscendC::Rsqrt<float>；接口用于核对实际重载和精度配置。
- [Rsqrtf](../../apis/simt_api/math_functions/float_math_functions/rsqrtf.md)（`exemplifies`）：该 runbook 以实测约 2^-9 误差说明快速 Rsqrt 的精度边界，并验证 Sqrt 后标量倒数可恢复 fp32 精度。
- [Sqrt](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/sqrt.md)（`exemplifies`）：推荐链先用 AscendC::Sqrt，再读取标量做 1.0f/s。
- [Sqrt](../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/sqrt.md)（`exemplifies`）：Rsqrt 快速近似精度不足时以 Sqrt 后取倒数替代，说明 Sqrt 精度模式在验证链中的作用。
- [A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播](rmsnorm_nan_propagation_not_positive_guard.md)（`related`）：候选指出 s>0 保护会在 NaN 时选择 0；本卡改 Sqrt+1/s 时也明确禁止该保护。
- [Reciprocal 低精度致 sigmoid 比对失败](reciprocal_sigmoid.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》说明RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../compilation/device_sqrt_uses_vector_api.md)（`related`）：“bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt”定义：device kernel 中直接调用 sqrtf 导致 bisheng 编译失败；改为 32B 对齐的向量 Sqrt 链并显式同步。；“dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数”定义：RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。。实质衔接：device sqrtf 编译失败时改用对齐 LocalTensor 的 Vector Sqrt；数值 runbook给出该替换在 Rsqrt 精度修复中的实例，PipeBarrier闭合向量结果消费。
- [golden BF16 rstd 归约误取 post-BF16 量化值](golden_bf16_rstd_post_bf16.md)（`related`）：候选区分 golden rstd 的量化阶段，本卡用 fp32 固定输入确认设备 Rsqrt 的量化误差。
- [基础API迁移指导](../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`related`）：基础API迁移指导 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
<!-- cannbot:related:end -->
