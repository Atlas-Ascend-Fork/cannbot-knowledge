---
type: "Runbook"
title: "bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt"
description: "device kernel 中直接调用 sqrtf 导致 bisheng 编译失败；改为 32B 对齐的向量 Sqrt 链并显式同步。"
tags: ["task.debugging", "topic.compute.elementwise.math_function", "topic.implementation.api_layer.basic_api"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt

## 现象

在 kernel 直调工程中编译归约后开方的 device 代码时，`op_kernel/rms_norm_kernel.cpp` 在 `-xasc` 编译阶段失败。错误尾部指向 `/usr/include/math.h` 的宏展开与 `sqrtf`，并报告 `3 errors generated`，随后 `all_kernels_obj` 构建失败。当时代码在 `__aicore__` 函数内直接执行 `1.0f / sqrtf(sumSq / D + epsilon)`。

## 适用场景

- 工程形态：Ascend C kernel 直调工程，bisheng 编译 device 源文件。
- API 路径：归约结果经 `AscendC::Sqrt`、`PipeBarrier<PIPE_ALL>`、`LocalTensor::GetValue` 转成标量倒数。
- 验证平台与版本：Ascend 950，活动 CANN toolkit 路径为 9.0.1。
- 适用粒度：`operator_family`，适用于需要在 device kernel 中对归约标量做平方根/倒数的归一化与统计类算子。
- 路线优先级：`recommended_fastpath`；这是本轨迹中唯一完成编译与全量精度验证的实现形态，不代表其他平台上的全局最优实现。
- 不适用场景：Host 侧普通 C++ 可正常链接 libm 的代码；RegBase、SIMT 或其他平台工具链未验证。

## 根因

bisheng 的 device 编译环境不是普通 Host C++ 链接环境，`__aicore__` 内直接使用 libc/libm 的 `sqrtf` 会在头文件宏展开/设备符号解析阶段失败；应把 `mean+epsilon` 写入 LocalTensor，通过 Ascend C Vector API 完成开方。计算链必须明确为 `meanSq = sumSq × invD`、`stabilized = meanSq + epsilon`、`sqrt = Sqrt(stabilized)`、`rstd = 1 / sqrt`，其中 8 个 fp32 元素恰为 `8×4B=32B`，满足该实现使用的对齐粒度。

## 解决配方

### before

**失败状态**：revision=`before_fix_snapshot`；path=`example/csrc/ops/rms_norm/op_kernel/rms_norm_kernel.cpp`；symbol=`rms_norm_kernel<T>`；lines=30-152。

```cpp
template <typename T>
__global__ __aicore__ void rms_norm_kernel(
    GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
    int64_t A1, int64_t D, float epsilon, int64_t blockRows)
{
    int64_t rowBegin = AscendC::GetBlockIdx() * blockRows;
    int64_t rowEnd = rowBegin + blockRows;
    if (rowEnd > A1) rowEnd = A1;
    if (rowBegin >= rowEnd) return;

    // ---- Buffer 尺寸推导（32B 对齐）----
    const uint32_t sizeofT = static_cast<uint32_t>(sizeof(T));
    const uint32_t dAlignBytesT = (static_cast<uint32_t>(D) * sizeofT + 31u) & ~31u;
    const uint32_t dAlignBytesF32 = (static_cast<uint32_t>(D) * 4u + 31u) & ~31u;
    const uint32_t dAlignF32Elem = dAlignBytesF32 / 4u;
    // ReduceSum sharedTmpBuffer 最小尺寸（fp32）
    constexpr uint32_t perRepeat = 256u / 4u;   // 64
    constexpr uint32_t perBlock = 32u / 4u;     // 8
    uint32_t repeats = (dAlignF32Elem + perRepeat - 1u) / perRepeat;
    uint32_t tmpBufSize = ((repeats + perBlock - 1u) / perBlock) * perBlock * 4u;
    if (tmpBufSize < 4096u) tmpBufSize = 4096u;
    // sumBuf 保守取 256B（ReduceSum dst 对齐/中间结果覆盖），32B 对齐
    constexpr uint32_t sumBufSize = 256u;

    AscendC::TPipe pipe;
    AscendC::GlobalTensor<T> xGm, gammaGm, yGm;
    xGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(x));
    gammaGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(gamma));
    yGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(y));

    AscendC::TQue<AscendC::TPosition::VECIN, PIPELINE_DEPTH> inQueueX;
    AscendC::TQue<AscendC::TPosition::VECOUT, PIPELINE_DEPTH> outQueueY;
    AscendC::TBuf<AscendC::TPosition::VECCALC> gammaLoadBuf, gammaFp32Buf, xSqBuf, sumBuf, tmpBuf;
    AscendC::TBuf<AscendC::TPosition::VECCALC> xFp32Buf; // 仅 fp16/bf16 使用

    pipe.InitBuffer(inQueueX, PIPELINE_DEPTH, dAlignBytesT);
    pipe.InitBuffer(outQueueY, PIPELINE_DEPTH, dAlignBytesT);
    pipe.InitBuffer(gammaLoadBuf, dAlignBytesT);
    pipe.InitBuffer(gammaFp32Buf, dAlignBytesF32);
    pipe.InitBuffer(xSqBuf, dAlignBytesF32);
    pipe.InitBuffer(sumBuf, sumBufSize);
    pipe.InitBuffer(tmpBuf, tmpBufSize);
    if constexpr (!std::is_same<T, float>::value) {
        pipe.InitBuffer(xFp32Buf, dAlignBytesF32);
    }

    // ---- Init: gamma 一次性搬入 + Cast 到 fp32（跨行复用）----
    {
        AscendC::DataCopyExtParams gcp{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> gpp{false, 0, 0, 0};
        auto gammaLocal = gammaLoadBuf.Get<T>();
        AscendC::DataCopyPad(gammaLocal, gammaGm, gcp, gpp);
        AscendC::PipeBarrier<AscendC::PIPE_ALL>(); // MTE2 -> VEC 同步
        auto gammaFp32 = gammaFp32Buf.Get<float>();
        AscendC::Cast(gammaFp32, gammaLocal, AscendC::RoundMode::CAST_NONE, static_cast<int32_t>(D));
    }
    auto gammaFp32 = gammaFp32Buf.Get<float>();

    const AscendC::DataCopyExtParams inCopy{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
    const AscendC::DataCopyExtParams outCopy{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
    const AscendC::DataCopyPadExtParams<T> inPad{false, 0, 0, 0};

    // ---- 软件流水：预取首行 ----
    {
        int64_t off = rowBegin * D;
        auto xl = inQueueX.AllocTensor<T>();
        AscendC::DataCopyPad(xl, xGm[off], inCopy, inPad);
        inQueueX.EnQue(xl);
    }

    for (int64_t r = rowBegin; r < rowEnd; ++r) {
        // 预取下一行（与本行 compute 的 MTE2/Vector 行间重叠）
        if (r + 1 < rowEnd) {
            int64_t off = (r + 1) * D;
            auto xNext = inQueueX.AllocTensor<T>();
            AscendC::DataCopyPad(xNext, xGm[off], inCopy, inPad);
            inQueueX.EnQue(xNext);
        }

        auto xLocal = inQueueX.DeQue<T>();
        int64_t off = r * D;

        if constexpr (std::is_same<T, float>::value) {
            // fp32: xLocal 即 fp32 工作区；xSq 独立，保留原始 x
            auto xSq = xSqBuf.Get<float>();
            AscendC::Mul(xSq, xLocal, xLocal, static_cast<int32_t>(D));
            auto sumLocal = sumBuf.Get<float>();
            auto tmpLocal = tmpBuf.Get<float>();
            AscendC::ReduceSum(sumLocal, xSq, tmpLocal, static_cast<int32_t>(D));
            float sumSq = sumLocal.GetValue(0);
            float rstd = 1.0f / sqrtf(sumSq / static_cast<float>(D) + epsilon);
            AscendC::Muls(xLocal, xLocal, rstd, static_cast<int32_t>(D));
            AscendC::Mul(xLocal, xLocal, gammaFp32, static_cast<int32_t>(D));
            // VEC -> VECOUT 搬运（对齐 count），经 outQueueY 同步后 CopyOut
            auto yLocal = outQueueY.AllocTensor<T>();
            AscendC::DataCopy(yLocal, xLocal, static_cast<int32_t>(dAlignF32Elem));
            outQueueY.EnQue(yLocal);
            inQueueX.FreeTensor(xLocal);
            yLocal = outQueueY.DeQue<T>();
            AscendC::DataCopyPad(yGm[off], yLocal, outCopy);
            outQueueY.FreeTensor(yLocal);
        } else {
            auto xFp32 = xFp32Buf.Get<float>();
            AscendC::Cast(xFp32, xLocal, AscendC::RoundMode::CAST_NONE, static_cast<int32_t>(D));
            auto xSq = xSqBuf.Get<float>();
            AscendC::Mul(xSq, xFp32, xFp32, static_cast<int32_t>(D));
            auto sumLocal = sumBuf.Get<float>();
            auto tmpLocal = tmpBuf.Get<float>();
            AscendC::ReduceSum(sumLocal, xSq, tmpLocal, static_cast<int32_t>(D));
            float sumSq = sumLocal.GetValue(0);
            float rstd = 1.0f / sqrtf(sumSq / static_cast<float>(D) + epsilon);
            AscendC::Muls(xFp32, xFp32, rstd, static_cast<int32_t>(D));
            AscendC::Mul(xFp32, xFp32, gammaFp32, static_cast<int32_t>(D));
            auto yLocal = outQueueY.AllocTensor<T>();
            AscendC::Cast(yLocal, xFp32, AscendC::RoundMode::CAST_RINT, static_cast<int32_t>(D));
            outQueueY.EnQue(yLocal);
            inQueueX.FreeTensor(xLocal);
            yLocal = outQueueY.DeQue<T>();
            AscendC::DataCopyPad(yGm[off], yLocal, outCopy);
            outQueueY.FreeTensor(yLocal);
        }
    }
}
```

### after

**验证通过状态**：revision=`after_fix_validated_snapshot`；path=`example/csrc/ops/rms_norm/op_kernel/rms_norm_kernel.cpp`；symbol=`rms_norm_kernel<T>`；lines=29-170。

```cpp
template <typename T>
__global__ __aicore__ void rms_norm_kernel(
    GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
    int64_t A1, int64_t D, float epsilon, float invD, int64_t blockRows)
{
    int64_t rowBegin = AscendC::GetBlockIdx() * blockRows;
    int64_t rowEnd = rowBegin + blockRows;
    if (rowEnd > A1) rowEnd = A1;
    if (rowBegin >= rowEnd) return;

    // ---- Buffer 尺寸推导（32B 对齐）----
    const uint32_t sizeofT = static_cast<uint32_t>(sizeof(T));
    const uint32_t dAlignBytesT = (static_cast<uint32_t>(D) * sizeofT + 31u) & ~31u;
    const uint32_t dAlignBytesF32 = (static_cast<uint32_t>(D) * 4u + 31u) & ~31u;
    const uint32_t dAlignF32Elem = dAlignBytesF32 / 4u;
    // ReduceSum sharedTmpBuffer 最小尺寸（fp32）
    constexpr uint32_t perRepeat = 256u / 4u;   // 64
    constexpr uint32_t perBlock = 32u / 4u;     // 8
    uint32_t repeats = (dAlignF32Elem + perRepeat - 1u) / perRepeat;
    uint32_t tmpBufSize = ((repeats + perBlock - 1u) / perBlock) * perBlock * 4u;
    if (tmpBufSize < 4096u) tmpBufSize = 4096u;
    // sumBuf 保守取 256B（ReduceSum dst 对齐/中间结果覆盖），32B 对齐
    constexpr uint32_t sumBufSize = 256u;

    AscendC::TPipe pipe;
    AscendC::GlobalTensor<T> xGm, gammaGm, yGm;
    xGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(x));
    gammaGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(gamma));
    yGm.SetGlobalBuffer(reinterpret_cast<__gm__ T *>(y));

    AscendC::TQue<AscendC::TPosition::VECIN, PIPELINE_DEPTH> inQueueX;
    AscendC::TQue<AscendC::TPosition::VECOUT, PIPELINE_DEPTH> outQueueY;
    AscendC::TBuf<AscendC::TPosition::VECCALC> gammaLoadBuf, gammaFp32Buf, xSqBuf, sumBuf, tmpBuf, sqrtBuf;
    AscendC::TBuf<AscendC::TPosition::VECCALC> xFp32Buf; // 仅 fp16/bf16 使用

    pipe.InitBuffer(inQueueX, PIPELINE_DEPTH, dAlignBytesT);
    pipe.InitBuffer(outQueueY, PIPELINE_DEPTH, dAlignBytesT);
    pipe.InitBuffer(gammaLoadBuf, dAlignBytesT);
    pipe.InitBuffer(gammaFp32Buf, dAlignBytesF32);
    pipe.InitBuffer(xSqBuf, dAlignBytesF32);
    pipe.InitBuffer(sumBuf, sumBufSize);
    pipe.InitBuffer(tmpBuf, tmpBufSize);
    pipe.InitBuffer(sqrtBuf, 32u); // rstd 标量开方工作区（8 个 fp32，32B 对齐）
    if constexpr (!std::is_same<T, float>::value) {
        pipe.InitBuffer(xFp32Buf, dAlignBytesF32);
    }

    // ---- Init: gamma 一次性搬入 + (非 fp32)Cast 到 fp32（跨行复用）----
    {
        AscendC::DataCopyExtParams gcp{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
        auto gammaFp32 = gammaFp32Buf.Get<float>();
        if constexpr (std::is_same<T, float>::value) {
            // fp32: gamma 已是 float，直接搬入 gammaFp32Buf，无需 Cast（float->float Cast 非法）
            AscendC::DataCopyPadExtParams<float> gppF{false, 0, 0, 0};
            AscendC::DataCopyPad(gammaFp32, gammaGm, gcp, gppF);
            AscendC::PipeBarrier<PIPE_ALL>(); // MTE2 -> VEC 同步
        } else {
            AscendC::DataCopyPadExtParams<T> gpp{false, 0, 0, 0};
            auto gammaLocal = gammaLoadBuf.Get<T>();
            AscendC::DataCopyPad(gammaLocal, gammaGm, gcp, gpp);
            AscendC::PipeBarrier<PIPE_ALL>(); // MTE2 -> VEC 同步
            AscendC::Cast(gammaFp32, gammaLocal, AscendC::RoundMode::CAST_NONE, static_cast<int32_t>(D));
        }
    }
    auto gammaFp32 = gammaFp32Buf.Get<float>();

    const AscendC::DataCopyExtParams inCopy{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
    const AscendC::DataCopyExtParams outCopy{1, static_cast<uint32_t>(D) * sizeofT, 0, 0, 0};
    const AscendC::DataCopyPadExtParams<T> inPad{false, 0, 0, 0};

    // ---- 软件流水：预取首行 ----
    {
        int64_t off = rowBegin * D;
        auto xl = inQueueX.AllocTensor<T>();
        AscendC::DataCopyPad(xl, xGm[off], inCopy, inPad);
        inQueueX.EnQue(xl);
    }

    for (int64_t r = rowBegin; r < rowEnd; ++r) {
        // 预取下一行（与本行 compute 的 MTE2/Vector 行间重叠）
        if (r + 1 < rowEnd) {
            int64_t off = (r + 1) * D;
            auto xNext = inQueueX.AllocTensor<T>();
            AscendC::DataCopyPad(xNext, xGm[off], inCopy, inPad);
            inQueueX.EnQue(xNext);
        }

        auto xLocal = inQueueX.DeQue<T>();
        int64_t off = r * D;

        if constexpr (std::is_same<T, float>::value) {
            // fp32: xLocal 即 fp32 工作区；xSq 独立，保留原始 x
            auto xSq = xSqBuf.Get<float>();
            AscendC::Mul(xSq, xLocal, xLocal, static_cast<int32_t>(D));
            auto sumLocal = sumBuf.Get<float>();
            auto tmpLocal = tmpBuf.Get<float>();
            AscendC::ReduceSum(sumLocal, xSq, tmpLocal, static_cast<int32_t>(D));
            // rstd = 1/sqrt(meanSq+eps)：全程向量计算规避 libm sqrtf 不可用，
            // 并以 PipeBarrier 在 GetValue 前同步 VEC->标量（GetValue 不自动同步）。
            // sumLocal[0]=sumSq -> Muls(invD) -> Adds(eps) -> Sqrt -> 标量倒数 -> Muls 广播
            AscendC::Muls(sumLocal, sumLocal, invD, 8);
            AscendC::Adds(sumLocal, sumLocal, epsilon, 8);
            auto sqrtLocal = sqrtBuf.Get<float>();
            AscendC::Sqrt(sqrtLocal, sumLocal, 8);
            AscendC::PipeBarrier<PIPE_ALL>();
            float rstd = 1.0f / sqrtLocal.GetValue(0);
            AscendC::Muls(xLocal, xLocal, rstd, static_cast<int32_t>(D));
            AscendC::Mul(xLocal, xLocal, gammaFp32, static_cast<int32_t>(D));
            // VEC -> VECOUT 搬运（Adds+0 等价拷贝，避免 UB->UB DataCopy 对齐灰区）
            auto yLocal = outQueueY.AllocTensor<T>();
            AscendC::Adds(yLocal, xLocal, 0.0f, static_cast<int32_t>(dAlignF32Elem));
            outQueueY.EnQue(yLocal);
            inQueueX.FreeTensor(xLocal);
            yLocal = outQueueY.DeQue<T>();
            AscendC::DataCopyPad(yGm[off], yLocal, outCopy);
            outQueueY.FreeTensor(yLocal);
        } else {
            auto xFp32 = xFp32Buf.Get<float>();
            AscendC::Cast(xFp32, xLocal, AscendC::RoundMode::CAST_NONE, static_cast<int32_t>(D));
            auto xSq = xSqBuf.Get<float>();
            AscendC::Mul(xSq, xFp32, xFp32, static_cast<int32_t>(D));
            auto sumLocal = sumBuf.Get<float>();
            auto tmpLocal = tmpBuf.Get<float>();
            AscendC::ReduceSum(sumLocal, xSq, tmpLocal, static_cast<int32_t>(D));
            AscendC::Muls(sumLocal, sumLocal, invD, 8);
            AscendC::Adds(sumLocal, sumLocal, epsilon, 8);
            auto sqrtLocal = sqrtBuf.Get<float>();
            AscendC::Sqrt(sqrtLocal, sumLocal, 8);
            AscendC::PipeBarrier<PIPE_ALL>();
            float rstd = 1.0f / sqrtLocal.GetValue(0);
            AscendC::Muls(xFp32, xFp32, rstd, static_cast<int32_t>(D));
            AscendC::Mul(xFp32, xFp32, gammaFp32, static_cast<int32_t>(D));
            auto yLocal = outQueueY.AllocTensor<T>();
            AscendC::Cast(yLocal, xFp32, AscendC::RoundMode::CAST_RINT, static_cast<int32_t>(D));
            outQueueY.EnQue(yLocal);
            inQueueX.FreeTensor(xLocal);
            yLocal = outQueueY.DeQue<T>();
            AscendC::DataCopyPad(yGm[off], yLocal, outCopy);
            outQueueY.FreeTensor(yLocal);
        }
    }
}
```

## 设计决策

- 不在构建系统中尝试为 device kernel 强行补 Host libm 链接，而是改用目标平台支持的 `AscendC::Sqrt`。
- `invD` 由 Host 计算后传入，device 侧用 `Muls` 与 `Adds` 形成完整 Vector 链。
- `Sqrt` 后保留 `PipeBarrier<PIPE_ALL>` 再 `GetValue`；同一轨迹的删屏障对照实验出现大面积精度失败，说明不能用“同为 VEC 流水”推断标量读天然可见。
- 当前路线是已验证可用实现；没有证据支持把 `sqrtf` 失败归因为缺少普通链接参数。

## 性能影响

轨迹没有隔离测量“向量 Sqrt 替代 sqrtf”本身的性能成本，因此不宣称收益。后续批量标量同步实验未形成整体净收益，不能作为本卡的性能结论。

## 预防

- 在设计阶段把 device 数学函数逐个映射到 Ascend C API，不把 Host libc/libm 可用性外推到 `__aicore__`。
- 标量结果若来自 Vector 指令，先验证同步契约，再读取 `GetValue`。
- 对标量工作区按 API 粒度分配，当前验证形态为 32B 对齐。

## 验证信号

来源于一次 Ascend 950 直调归一化 kernel 的远程构建与上板评测；代码状态由轨迹中的完整写入与逐次编辑重建。

- 初始版本在 `sqrtf` 的 `math.h` 宏展开处报告 3 个编译错误，`all_kernels_obj` 失败（证据等级: tool_observed；来源平台: 950）。
- 改为向量计算链并完成同步/Host 参数配套后，远程 CMake 构建到 `_C` 目标成功（证据等级: tool_observed；来源平台: 950）。
- 最终实现通过完整 20/20 精度用例，覆盖 fp32、fp16 与 bfloat16（证据等级: tool_observed；来源平台: 950）。

- 独立复现 R1：工具报告 [100%] Built target _C。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R2：工具报告 [100%] Built target op_rms_norm。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。

## 失效边界

- 只验证 Ascend 950 与本次活动 CANN 9.0.1 工具链；A2/A3 是否具有相同 `sqrtf` 限制未验证，推断可迁移但不得直接视为已验证。
- `count=8` 是本实现对 32B fp32 工作区的代码形态，不应在其他 dtype/接口签名上机械照搬。
- 其他数学函数不能仅凭本卡推断同样不可用，需分别查 API/编译验证。

## 坏实践

- 在 `__aicore__` 里直接包含 `<cmath>` 并调用 `sqrtf`，然后把失败归咎于普通 Host 链接配置。
- 只把 `sqrtf` 换成 `AscendC::Sqrt`，却遗漏 LocalTensor 对齐、Vector→Scalar 同步和 Host 参数传递。

## 误诊

最初容易把报错理解成“缺少 `-lm`”；轨迹中的 device 编译上下文与后续 Ascend C API 修复表明，正确切入层是 kernel API 路径，不是通用链接参数。