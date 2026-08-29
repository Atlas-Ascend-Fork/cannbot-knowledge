---
type: "Runbook"
title: "bisheng 不支持 bf16 标量强转时用位布局精确提升到 fp32"
description: "dav-2201 的 bisheng 后端拒绝标量 bfloat16_t 到 float 强转；利用 bf16 与 fp32 共享符号位和指数布局，将原始 16 位左移后重解释为 float。"
tags: ["task.debugging", "topic.compute.elementwise.type_conversion", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
---

# bisheng 不支持 bf16 标量强转时用位布局精确提升到 fp32

## 现象

在 dav-2201 上构建包含多 dtype 模板的 Ascend C prefix-scan kernel 时，half、float 与 int32 分支可通过前端，但 bf16 实例中的 `float xf = (float)xn` 触发 bisheng 后端致命错误：`not support bf16 type cast`，clang 以 exit code 70 退出。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的编译、链接或运行工程。
- API 路径：`bfloat16_t`、`bf16`、`fp32` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`operator_family`，仅迁移到相同 BF16 位布局和设备侧标量提升路径。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

该后端不支持 UB bf16 标量经 C++ cast 直接生成 fp32。bf16 的 16 位编码正好是 fp32 的高 16 位，因此对原始位 `raw` 做 `fbits = uint32_t(raw) << 16`，再按 float 重解释即可保持符号位、指数和 7 位尾数，不引入算术舍入。

## 解决配方

### Before

```cpp
template <typename T>
__global__ __aicore__ __vector__ void cummin_kernel(GM_ADDR input, GM_ADDR values, GM_ADDR indices,
    int64_t totalLanes, int64_t R, int64_t inner, int64_t numBlocks,
    int64_t Tr, int64_t Tg, int32_t dtypeKind)
{
    using UT = typename std::conditional<std::is_same<T, half>::value || std::is_same<T, bfloat16_t>::value, uint16_t, T>::type;
    (void)dtypeKind;
    if (totalLanes <= 0 || R <= 0) return;

    int64_t bid = AscendC::GetBlockIdx();
    int64_t lpb = (totalLanes + numBlocks - 1) / numBlocks;
    int64_t lStart = bid * lpb;
    if (lStart >= totalLanes) return;
    int64_t lEnd = lStart + lpb;
    if (lEnd > totalLanes) lEnd = totalLanes;

    int64_t oStart = lStart / inner;
    int64_t jStart = lStart % inner;
    int64_t oEnd = (lEnd - 1) / inner;
    int64_t jEnd = (lEnd - 1) % inner + 1; // exclusive end for last outer block

    const uint32_t B = (uint32_t)sizeof(T);            // native element bytes
    const uint32_t B32 = sizeof(int32_t);              // 4
    const uint32_t B64 = sizeof(int64_t);              // 8
    // Max tile element count (full group): Tr * Tg. Tail groups are <= this.
    const uint32_t tileElemsMax = (uint32_t)(Tr * Tg);

    AscendC::TPipe pipe;
    AscendC::TBuf<AscendC::TPosition::VECIN>  inBuf;        // native, padded rows
    AscendC::TBuf<AscendC::TPosition::VECCALC> outValBuf;  // native, padded rows
    AscendC::TBuf<AscendC::TPosition::VECCALC> idx32Buf;   // int32, contiguous (for asc_int322int64)
    AscendC::TBuf<AscendC::TPosition::VECOUT> idx64Buf;    // int64, contiguous
    AscendC::TBuf<AscendC::TPosition::VECCALC> runFBuf, runVBuf, runIBuf;

    pipe.InitBuffer(inBuf, tileElemsMax * B);
    pipe.InitBuffer(outValBuf, tileElemsMax * B);
    pipe.InitBuffer(idx32Buf, tileElemsMax * B32);
    pipe.InitBuffer(idx64Buf, tileElemsMax * B64);
    pipe.InitBuffer(runFBuf, Tg * sizeof(float));
    pipe.InitBuffer(runVBuf, Tg * B);
    pipe.InitBuffer(runIBuf, Tg * B32);

    auto inLocal = inBuf.Get<T>();
    auto outValLocal = outValBuf.Get<T>();
    auto idx32Local = idx32Buf.Get<int32_t>();
    auto idx64Local = idx64Buf.Get<int64_t>();

    AscendC::GlobalTensor<T> inGm, valGm;
    AscendC::GlobalTensor<int64_t> idxGm;
    inGm.SetGlobalBuffer((__gm__ T *)input);
    valGm.SetGlobalBuffer((__gm__ T *)values);
    idxGm.SetGlobalBuffer((__gm__ int64_t *)indices);

    __ubuf__ T *inPtr = (__ubuf__ T *)inLocal.GetPhyAddr();
    __ubuf__ T *outValPtr = (__ubuf__ T *)outValLocal.GetPhyAddr();
    __ubuf__ int32_t *idx32Ptr = (__ubuf__ int32_t *)idx32Local.GetPhyAddr();
    __ubuf__ int64_t *idx64Ptr = (__ubuf__ int64_t *)idx64Local.GetPhyAddr();
    __ubuf__ float *runF = (__ubuf__ float *)runFBuf.Get<float>().GetPhyAddr();
    __ubuf__ T *runV = (__ubuf__ T *)runVBuf.Get<T>().GetPhyAddr();
    __ubuf__ int32_t *runI = (__ubuf__ int32_t *)runIBuf.Get<int32_t>().GetPhyAddr();

    const float posInf = __builtin_inff();

    // helper: round up bytes to 32
    auto roundUp32 = [](uint32_t b) -> uint32_t { return (b + 31u) & ~31u; };

    for (int64_t o = oStart; o <= oEnd; ++o) {
        int64_t jLo = (o == oStart) ? jStart : 0;
        int64_t jHi = (o == oEnd) ? jEnd : inner;
        int64_t base = o * (R * inner);

        for (int64_t g0 = jLo; g0 < jHi; g0 += Tg) {
            int64_t tg64 = jHi - g0;
            if (tg64 > Tg) tg64 = Tg;
            uint32_t tg = (uint32_t)tg64;
            uint32_t rowBytesT = tg * B;
            uint32_t padRowBytesT = roundUp32(rowBytesT);     // UB row stride for in/outVal (native)
            uint32_t padRowElemsT = padRowBytesT / B;          // index stride for in/outVal
            // init running for this j-group
            for (uint32_t k = 0; k < tg; ++k) {
                runF[k] = posInf;
                runI[k] = 0;
            }

            for (int64_t r0 = 0; r0 < R; r0 += Tr) {
                int64_t tr64 = R - r0;
                if (tr64 > Tr) tr64 = Tr;
                uint32_t tr = (uint32_t)tr64;
                uint32_t tileElem = tr * tg;
                int64_t srcOff = base + r0 * inner + g0;

                // ---- load inTile [tr][tg] (GM->UB), 2D strided padded ----
                AscendC::DataCopyExtParams inParams{
                    (uint16_t)tr, rowBytesT,
                    (uint32_t)((inner - tg64) * (int64_t)B),   // GM srcStride gap (bytes)
                    padRowBytesT - rowBytesT,                  // UB dstStride gap (pad)
                    0};
                AscendC::DataCopyPadExtParams<T> padParams{false, 0, 0, 0};
                AscendC::DataCopyPad(inLocal, inGm[srcOff], inParams, padParams);
                AscendC::PipeBarrier<PIPE_ALL>();

                // ---- scalar scan (compare in fp32 via scalar cast) ----
                for (uint32_t r = 0; r < tr; ++r) {
                    int64_t gi = r0 + (int64_t)r;
                    __ubuf__ T *inRow = inPtr + (uint64_t)r * padRowElemsT;
                    __ubuf__ T *outRow = outValPtr + (uint64_t)r * padRowElemsT;
                    __ubuf__ int32_t *idx32Row = idx32Ptr + (uint64_t)r * tg; // contiguous
                    for (uint32_t k = 0; k < tg; ++k) {
                        T xn = inRow[k];
                        float xf = (float)xn;          // scalar cast (test: works on 2201 for half/bf16/int32)
                        bool runNan = (runF[k] != runF[k]);
                        bool upd = (xf != xf) || (!runNan && xf <= runF[k]);
                        if (upd) {
                            runF[k] = xf;
                            runV[k] = xn;
                            runI[k] = (int32_t)gi;
                        }
                        outRow[k] = runV[k];
                        idx32Row[k] = runI[k];
                    }
                }

                AscendC::PipeBarrier<PIPE_V>(); // idx32 visible to asc_int322int64
                // ---- int32 -> int64 ----
                asc_int322int64(idx64Ptr, idx32Ptr, tileElem);
                AscendC::PipeBarrier<PIPE_ALL>(); // V -> MTE3

                // ---- store outVal (native, padded 2D) ----
                AscendC::DataCopyExtParams outValParams{
                    (uint16_t)tr, rowBytesT,
                    padRowBytesT - rowBytesT,                // UB srcStride gap
                    (uint32_t)((inner - tg64) * (int64_t)B), // GM dstStride gap
                    0};
                AscendC::DataCopyPad(valGm[srcOff], outValLocal, outValParams);

                // ---- store idx64 (contiguous UB -> 2D strided GM, int64) ----
                uint32_t rowBytes64 = tg * B64;
                AscendC::DataCopyExtParams outIdxParams{
                    (uint16_t)tr, rowBytes64,
                    0,                                       // UB contiguous (srcStride gap 0)
                    (uint32_t)((inner - tg64) * (int64_t)B64), // GM dstStride gap
                    0};
                AscendC::DataCopyPad(idxGm[srcOff], idx64Local, outIdxParams);

                AscendC::PipeBarrier<PIPE_ALL>(); // MTE3 -> V (free out buffers, WAR)
            }
        }
    }
}
```

### After

```cpp
template <typename T>
__global__ __aicore__ __vector__ void cummin_kernel(GM_ADDR input, GM_ADDR values, GM_ADDR indices,
    int64_t totalLanes, int64_t R, int64_t inner, int64_t numBlocks,
    int64_t Tr, int64_t Tg, int32_t dtypeKind)
{
    using UT = typename std::conditional<std::is_same<T, half>::value || std::is_same<T, bfloat16_t>::value, uint16_t, T>::type;
    (void)dtypeKind;
    if (totalLanes <= 0 || R <= 0) return;

    int64_t bid = AscendC::GetBlockIdx();
    int64_t lpb = (totalLanes + numBlocks - 1) / numBlocks;
    int64_t lStart = bid * lpb;
    if (lStart >= totalLanes) return;
    int64_t lEnd = lStart + lpb;
    if (lEnd > totalLanes) lEnd = totalLanes;

    int64_t oStart = lStart / inner;
    int64_t jStart = lStart % inner;
    int64_t oEnd = (lEnd - 1) / inner;
    int64_t jEnd = (lEnd - 1) % inner + 1; // exclusive end for last outer block

    const uint32_t B = (uint32_t)sizeof(T);            // native element bytes
    const uint32_t B32 = sizeof(int32_t);              // 4
    const uint32_t B64 = sizeof(int64_t);              // 8
    // Max tile element count (full group): Tr * Tg. Tail groups are <= this.
    const uint32_t tileElemsMax = (uint32_t)(Tr * Tg);

    AscendC::TPipe pipe;
    AscendC::TBuf<AscendC::TPosition::VECIN>  inBuf;        // native, padded rows
    AscendC::TBuf<AscendC::TPosition::VECCALC> outValBuf;  // native, padded rows
    AscendC::TBuf<AscendC::TPosition::VECCALC> idx32Buf;   // int32, contiguous (for asc_int322int64)
    AscendC::TBuf<AscendC::TPosition::VECOUT> idx64Buf;    // int64, contiguous
    AscendC::TBuf<AscendC::TPosition::VECCALC> runFBuf, runVBuf, runIBuf;

    pipe.InitBuffer(inBuf, tileElemsMax * B);
    pipe.InitBuffer(outValBuf, tileElemsMax * B);
    pipe.InitBuffer(idx32Buf, tileElemsMax * B32);
    pipe.InitBuffer(idx64Buf, tileElemsMax * B64);
    pipe.InitBuffer(runFBuf, Tg * sizeof(float));
    pipe.InitBuffer(runVBuf, Tg * B);
    pipe.InitBuffer(runIBuf, Tg * B32);

    auto inLocal = inBuf.Get<T>();
    auto outValLocal = outValBuf.Get<T>();
    auto idx32Local = idx32Buf.Get<int32_t>();
    auto idx64Local = idx64Buf.Get<int64_t>();

    AscendC::GlobalTensor<T> inGm, valGm;
    AscendC::GlobalTensor<int64_t> idxGm;
    inGm.SetGlobalBuffer((__gm__ T *)input);
    valGm.SetGlobalBuffer((__gm__ T *)values);
    idxGm.SetGlobalBuffer((__gm__ int64_t *)indices);

    __ubuf__ T *inPtr = (__ubuf__ T *)inLocal.GetPhyAddr();
    __ubuf__ T *outValPtr = (__ubuf__ T *)outValLocal.GetPhyAddr();
    __ubuf__ int32_t *idx32Ptr = (__ubuf__ int32_t *)idx32Local.GetPhyAddr();
    __ubuf__ int64_t *idx64Ptr = (__ubuf__ int64_t *)idx64Local.GetPhyAddr();
    __ubuf__ float *runF = (__ubuf__ float *)runFBuf.Get<float>().GetPhyAddr();
    __ubuf__ T *runV = (__ubuf__ T *)runVBuf.Get<T>().GetPhyAddr();
    __ubuf__ int32_t *runI = (__ubuf__ int32_t *)runIBuf.Get<int32_t>().GetPhyAddr();

    const float posInf = __builtin_inff();

    // helper: round up bytes to 32
    auto roundUp32 = [](uint32_t b) -> uint32_t { return (b + 31u) & ~31u; };

    for (int64_t o = oStart; o <= oEnd; ++o) {
        int64_t jLo = (o == oStart) ? jStart : 0;
        int64_t jHi = (o == oEnd) ? jEnd : inner;
        int64_t base = o * (R * inner);

        for (int64_t g0 = jLo; g0 < jHi; g0 += Tg) {
            int64_t tg64 = jHi - g0;
            if (tg64 > Tg) tg64 = Tg;
            uint32_t tg = (uint32_t)tg64;
            uint32_t rowBytesT = tg * B;
            uint32_t padRowBytesT = roundUp32(rowBytesT);     // UB row stride for in/outVal (native)
            uint32_t padRowElemsT = padRowBytesT / B;          // index stride for in/outVal
            // init running for this j-group
            for (uint32_t k = 0; k < tg; ++k) {
                runF[k] = posInf;
                runI[k] = 0;
            }

            for (int64_t r0 = 0; r0 < R; r0 += Tr) {
                int64_t tr64 = R - r0;
                if (tr64 > Tr) tr64 = Tr;
                uint32_t tr = (uint32_t)tr64;
                uint32_t tileElem = tr * tg;
                int64_t srcOff = base + r0 * inner + g0;

                // ---- load inTile [tr][tg] (GM->UB), 2D strided padded ----
                AscendC::DataCopyExtParams inParams{
                    (uint16_t)tr, rowBytesT,
                    (uint32_t)((inner - tg64) * (int64_t)B),   // GM srcStride gap (bytes)
                    padRowBytesT - rowBytesT,                  // UB dstStride gap (pad)
                    0};
                AscendC::DataCopyPadExtParams<T> padParams{false, 0, 0, 0};
                AscendC::DataCopyPad(inLocal, inGm[srcOff], inParams, padParams);
                AscendC::PipeBarrier<PIPE_ALL>();

                // ---- scalar scan (compare in fp32 via scalar cast) ----
                for (uint32_t r = 0; r < tr; ++r) {
                    int64_t gi = r0 + (int64_t)r;
                    __ubuf__ T *inRow = inPtr + (uint64_t)r * padRowElemsT;
                    __ubuf__ T *outRow = outValPtr + (uint64_t)r * padRowElemsT;
                    __ubuf__ int32_t *idx32Row = idx32Ptr + (uint64_t)r * tg; // contiguous
                    for (uint32_t k = 0; k < tg; ++k) {
                        T xn = inRow[k];
                        float xf;
                        if constexpr (std::is_same<T, bfloat16_t>::value) {
                            // bf16 -> fp32 is exact bit shift (shared sign/exp layout);
                            // bisheng backend does not support scalar (float)bf16.
                            uint16_t raw = ((__ubuf__ uint16_t *)inRow)[k];
                            uint32_t fbits = ((uint32_t)raw) << 16;
                            union { uint32_t u; float f; } cv; cv.u = fbits; xf = cv.f;
                        } else if constexpr (std::is_same<T, float>::value) {
                            xf = xn;
                        } else {
                            xf = (float)xn;   // half / int32
                        }
                        bool runNan = (runF[k] != runF[k]);
                        bool upd = (xf != xf) || (!runNan && xf <= runF[k]);
                        if (upd) {
                            runF[k] = xf;
                            runV[k] = xn;
                            runI[k] = (int32_t)gi;
                        }
                        outRow[k] = runV[k];
                        idx32Row[k] = runI[k];
                    }
                }

                AscendC::PipeBarrier<PIPE_V>(); // idx32 visible to asc_int322int64
                // ---- int32 -> int64 ----
                asc_int322int64(idx64Ptr, idx32Ptr, tileElem);
                AscendC::PipeBarrier<PIPE_ALL>(); // V -> MTE3

                // ---- store outVal (native, padded 2D) ----
                AscendC::DataCopyExtParams outValParams{
                    (uint16_t)tr, rowBytesT,
                    padRowBytesT - rowBytesT,                // UB srcStride gap
                    (uint32_t)((inner - tg64) * (int64_t)B), // GM dstStride gap
                    0};
                AscendC::DataCopyPad(valGm[srcOff], outValLocal, outValParams);

                // ---- store idx64 (contiguous UB -> 2D strided GM, int64) ----
                uint32_t rowBytes64 = tg * B64;
                AscendC::DataCopyExtParams outIdxParams{
                    (uint16_t)tr, rowBytes64,
                    0,                                       // UB contiguous (srcStride gap 0)
                    (uint32_t)((inner - tg64) * (int64_t)B64), // GM dstStride gap
                    0};
                AscendC::DataCopyPad(idxGm[srcOff], idx64Local, outIdxParams);

                AscendC::PipeBarrier<PIPE_ALL>(); // MTE3 -> V (free out buffers, WAR)
            }
        }
    }
}
```

## 系统信息

CANN 9.2.0 bisheng，目标 dav-2201；相关文件为 `operators/cummin/cummin.asc`。

## 设计决策

用 `if constexpr` 只隔离 bf16 实例：float 直接读取，half/int32 延续可编译的标量 cast。没有用测试侧降 dtype 或跳过 bf16。

## 性能影响

本轨迹未对这一局部修复做独立性能归因；它只声明解除构建或正确性阻塞。

## 预防

在目标 CANN/SoC 上为相关 API、dtype 或搬运形态保留最小编译与上板用例，不以静态推断替代。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：构建 exit=2，编译器明确报 not support bf16 type cast。（来源平台：a3；证据等级: tool_observed）。
- 修复后：构建 exit=0，libop_scatter.so 链接成功。（来源平台：a3；证据等级: tool_observed）。
- 修复后：NPU 测试 46 passed。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

- host 侧归约路线未作为 active 推荐；本卡只保留设备侧 BF16 位扩展到 FP32 的已验证机制。

该做法只适用于 bf16→fp32 的精确位扩展；大小端、不同浮点编码或反向转换不能照搬。950/a2 未验证，推断可迁移前需确认编译器和位布局。

## 坏实践

把 bf16 用例从测试集中删除或把输入先转成 half 会掩盖后端能力缺口，且改变算子 dtype 语义。

## 误诊

无。

<!-- cannbot:related:start -->
## 相关

- [BF16 标量 cast 后端失败—改用位序键](bf16_scalar_compare_by_raw_bits.md)（`related`）：比较卡定位到“dav-3510 的 bisheng aicore 后端不支持在该标量 kernel 路径中实例化 `bfloat16_t` 与 `float` 的双向 `static_cast`。”；转换卡给出“该后端不支持 UB bf16 标量经 C++ cast 直接生成 fp32。bf16 的 16 位编码正好是 fp32 的高 16 位，因此对原始位 `raw` 做 `fbits = uint32_t(raw) << 16`，再按 float 重解释即可保持符号位、指数和 7 位尾数，不引入算术舍入。”，共同提供绕开 BF16 标量 cast 限制的两种位级策略。
<!-- cannbot:related:end -->
