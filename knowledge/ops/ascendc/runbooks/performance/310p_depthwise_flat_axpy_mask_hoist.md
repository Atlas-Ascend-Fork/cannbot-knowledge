---
type: "Runbook"
title: "310P depthwise：flat Axpy + mask hoist"
description: "310P depthwise 的墙是每 tap 每行一次小向量调用；Level-2 Axpy 每次 75–90 scalar cycles。padded 窗口与 acc 同 stride → 单 tap 一次 flat Axpy（K·K·R→K·K），mask 每 task 一次，padded 输出消 flush；逐 tap 源起址实测非 32B 契约对齐。"
tags: [task.optimization, topic.performance.analysis, topic.programming_model.execution_unit.vector]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_vec_ternary_scalar_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/basic_api/kernel_operator_vec_binary_scalar_intf.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/general_description_and_constraints.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/adv_api/math_compute/Axpy_interface/Axpy.md
    role: constraint
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-11T09:46:56Z'
platforms: ["310p"]
---

# 310P depthwise：flat Axpy + mask hoist

## 现象

9 号 ConvDepthwise2d 的 V5 实现已经能跑、精度也过，但标准 `msprof quick` 的 kernel 级归因显示：`scalar_ratio = 0.82–0.87`（约 85% 的 aicore 时间花在 scalar pipe），`vec_ratio = 0.29–0.45`，`mte2_ratio = 0.17–0.27`；此外 `Ws%8≠0` 的 case 还有一个独立的 `flush` kernel，占设备时间 20–25%。

也就是说，瓶颈不是向量算力，也不是搬运，而是**每 tap 每行一次的小向量调用**。V5 每个 task 要发 `K·K·R` 次 `Axpy`（R 越大，调用数越线性增长），每次调用都带一套 scalar 的 mask 设置。

## 适用场景

- **工程形态**：AscendC kernel 直调；310P 上 depthwise conv、direct-conv、滑窗类“每个 tap 对每行发一次小向量加法”的 VEC 算子。
- **API 路径**：`Axpy`（Level-0 `Axpy<T,U,false>` 带 mask / Level-2 `Axpy(dst,src,scalar,count)`）、`SetMaskCount`/`SetVectorMask<COUNTER>`/`ResetMask`/`SetMaskNorm`、`Duplicate`、`DataCopy`/`Adds`。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0。
- **适用粒度**：`operator_family` —— depthwise/direct-conv 以及任何“每行一次 V 调用”的滑窗 VEC kernel。
- **路线优先级**：`recommended_fastpath`（310P 实测）—— padded 窗口 + flat Axpy + mask hoist；per-row Axpy 是已降级的慢路线。注意：逐 tap 源起址不是 32B 契约对齐的通用 fast path，见“解决配方”的 32B caveat。
- **明确不适用 / 未验证场景**：跨通道归约的普通卷积（应走 cube）；`S>1` 的相位分解（本卡只做分组窗，仍有 2× 宽度浪费）；其它代际未验证。

## 根因

310P 的 Level-2 `Axpy(dst, src, scalar, count)` 在 `impl/basic_api/dav_m200/kernel_operator_vec_ternary_scalar_impl.h:68-82` 里每次调用都展开为：

```cpp
// Axpy::Level 2
template <typename T, typename U>
__aicore__ inline void AxpyImpl(__ubuf__ T* dst, __ubuf__ U* src, const U& scalarValue, const int32_t& count)
{
    SetMaskCount();
    AscendCUtils::SetMask<U>(0, count);
    if constexpr (sizeof(T) > sizeof(U)) {
        AxpyIntrinsicsImpl(
            dst, src, scalarValue, 1,
            {DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REPEAT_STRIDE, DEFAULT_REPEAT_STRIDE / 2});
    } else {
        AxpyIntrinsicsImpl(
            dst, src, scalarValue, 1,
            {DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULT_REPEAT_STRIDE, DEFAULT_REPEAT_STRIDE});
    }
    ResetMask();
    SetMaskNorm();
}
```

即每次调用至少 4 条 scalar 指令（`SetMaskCount`、`SetMask<U>`、`ResetMask`、`SetMaskNorm`），其中 `SetMask<U>` 还会为动态 `count` 计算 `(1ULL << len) - 1`。按 2736–6000 调用/核反算，实测 **75–90 scalar cycles/调用**。V5 的 `K·K·R` 次小调用把 scalar pipe 打满，向量单元反而闲置。

## 解决配方

### 核心：padded 窗口与 acc 同 stride，单 tap 一次 flat Axpy

窗口行 = `P` 左 pad + `W` 数据 + 右 pad；行距

```
STRIDE = max(RuE(W + P, EA), RuE(P + Ws, EA))     # EA = 16 half / 8 float = 32B
```

acc 用同一 `STRIDE`，输出列 `c` 放在 acc 的 `P + c` 位置。对每个 tap `(i, j)`：

```
src   = GUARD + dst + i*STRIDE + (PADPOS - 2P) + j     # S=1
count = rowsHere * STRIDE
```

一次 `Axpy<TC,T,false>(acc_[accBase], win_[winBase+rowOff+j], tap, 0, 1, rep)` 覆盖整块行；调用数从 `K·K·R` 降到 `K·K`。

- **32B 对齐（重要 caveat）**：`acc_` 目的起址、窗口基址、`WINBLK`/`STRIDE` 按 32B 对齐；取 `PADPOS = P`，用 `GUARD` 相位补偿 `(GUARD+P)%EA==0`。但**逐 tap 源起址 `win_[winBase+rowOff+j]` 会随 j 平移**：fp32 下每加一个 tap 偏移就平移 4B，K≥2 时不可能所有 tap 同时 32B 对齐（3×3 通常只有一个 tap 落在边界）。`Axpy` 的接口契约要求 UB 操作数起始地址 32B 对齐（`general_description_and_constraints.md` 表 2），所以这条 flat fast path **不是契约保证的通用写法**：310P 上 50/50 + 5.4× 是实测结果，Debug 构建或其它 CANN 版本可能断言或行为未定义。契约洁净的替代：按 tap 建对齐窗口（每个 tap 一份、源起址对齐）后仍可 flat，或回退 per-row Axpy（慢路线）。新工程复用前先确认目标版本是否检查起址；否则按对齐契约重写后再测。
- **窗口外推**：窗口行尾外推读到的是下一行的左 pad（零），负偏移读到 GUARD（零）；两者预零且永不写入。
- **每 task 尾部零化窗口**：本 task 未装载的 top/bottom padding 行必须为 0，否则会读到上一 task 的残留（`S>1` 分组窗尤其致命；指纹 = `S>1` 且 `P>0` 的 case max_abs≈3，`P=0` 全对）。
- **mask hoist**：`SetMaskCount(); SetVectorMask<TC, MaskMode::COUNTER>(count);` 每 task 一次，内层用 `Axpy<T,U,false>(..., 0, 1, rep)`；tap 循环结束后 `ResetMask(); SetMaskNorm();`。**任何 Level-2 调用（`Duplicate`/`Cast`/`Adds`）都会复位 mask 模式**，所以 mask 段必须独立，不能和这些调用交错。

### After：V6 的 C/D 段

以下为 `DwConvFlatKernel::Process` 内的 C/D 段 scoped excerpt（含 task 尾部窗口零化；完整函数见开发会话的 V6 kernel 快照与窗口零化补丁）。

```cpp
            // bias 整块预填（V），taps 标量读在下方屏障后（V -> S）
            for (int64_t cl = 0; cl < cCnt; ++cl) {
                const int64_t c = cBase + cl;
                const int64_t hB = c % EA;
                const TC biasVal = static_cast<TC>(winB_[cl * 2 * EA].GetValue(static_cast<uint32_t>(hB)));
                AscendC::Duplicate(acc_[cl * R_ * STRIDE_], biasVal,
                                   static_cast<int32_t>(rowsHere * STRIDE_));
            }
            AscendC::PipeBarrier<PIPE_ALL>();  // V -> S（taps/bias GetValue）

            // ---- C：K*K 次 flat Axpy（计数模式 mask 每 task 只设一次）----
            const int64_t count = rowsHere * STRIDE_;
            AscendC::SetMaskCount();
            AscendC::SetVectorMask<TC, AscendC::MaskMode::COUNTER>(static_cast<int32_t>(count));
            const AscendC::UnaryRepeatParams rep{1, 1, 8, 8};
            for (int64_t cl = 0; cl < cCnt; ++cl) {
                const int64_t c = cBase + cl;
                const int64_t hW = c * KK_ - (c * KK_ / EA) * EA;
                TC taps[V6_MAX_TAPS];
                for (int64_t t = 0; t < KK_; ++t) {
                    if constexpr (QUANT_F16) {
                        taps[t] = static_cast<TC>(qhW_.GetValue(static_cast<uint32_t>(cl * WKA_ + hW + t)));
                    } else {
                        taps[t] = static_cast<TC>(winW_[cl * WKA_].GetValue(static_cast<uint32_t>(hW + t)));
                    }
                }
                const int64_t accBase = cl * R_ * STRIDE_;
                const int64_t winBase = cl * WINBLK_ + GUARD_ + PADPOS_ - 2 * P_;
                for (int64_t i = 0; i < K_; ++i) {
                    const int64_t rowOff = (S_ == 1) ? (i * STRIDE_) : (i * R_ * STRIDE_);
                    for (int64_t j = 0; j < K_; ++j) {
                        AscendC::Axpy<TC, T, false>(acc_[accBase], win_[winBase + rowOff + j],
                                                    taps[i * K_ + j], static_cast<uint64_t>(0),
                                                    static_cast<uint8_t>(1), rep);
                    }
                }
            }
            AscendC::ResetMask();
            AscendC::SetMaskNorm();

            // ---- D：整行块平铺写出（行距 = STRIDE，host 侧 view 取 [P, P+Ws)）----
            VToMte3Edge();
            for (int64_t cl = 0; cl < cCnt; ++cl) {
                const int64_t c = cBase + cl;
                const int64_t outRow = (n * C_ + c) * Ho_ + r0;
                AscendC::DataCopy(yGm_[outRow * STRIDE_], acc_[cl * R_ * STRIDE_],
                                  static_cast<int32_t>(rowsHere * STRIDE_));
            }
            Mte3ToVEdge();
            // 窗口零化复位：本 task 未装载的行（top/bottom padding 行）必须为 0，
            // 否则会读到上一个 task 的残留行（S>1 分组窗内尤其致命）。
            AscendC::Duplicate(win_[0], static_cast<T>(0),
                               static_cast<int32_t>(CB_ * WINBLK_));
            AscendC::PipeBarrier<PIPE_ALL>();  // win/winW/winB 复用（V/S -> MTE2）
```

### Before：V5 的 per-row Axpy

以下为 `DwConvKernel::Process` 的 `sameAligned` 分支 scoped excerpt（完整函数见开发会话的 V5 kernel 快照；此处截到 tap 循环体，省去外层收尾括号）。

```cpp
                if (sameAligned) {
                    AscendC::Duplicate(acc_[accBase], biasVal,
                                       static_cast<int32_t>(rowsHere * WSA_));
                    for (int64_t i = 0; i < K_; ++i) {
                        const bool spanInRange =
                            (r0 + i >= P_) && (r0 + rowsHere - 1 + i < P_ + H_);
                        if (spanInRange) {
                            // 中心 tap 全行融合（单发大调用，独立）
                            AscendC::Axpy(acc_[accBase], xcomp[(cl * ROWS_ + i) * WINLEN_],
                                          taps[i * K_ + P_],
                                          static_cast<int32_t>(rowsHere * WSA_));
                            // 边缘 tap：j 外层，r 内层（行间独立）
                            const int64_t src0 = (cl * ROWS_ + i) * WINLEN_;
                            for (int64_t j = 0; j < K_; ++j) {
                                if (j == P_) {
                                    continue;
                                }
                                const int64_t dJ = (j > P_) ? (j - P_) : 0;
                                const int64_t w0 = (j > P_) ? 0 : (P_ - j);
                                const int64_t w1 =
                                    (Ws_ < W_ + P_ - j) ? Ws_ : (W_ + P_ - j);
                                const int64_t g = w1 - w0;
                                if (g <= 0) {
                                    continue;
                                }
                                const TC tap = taps[i * K_ + j];
                                const int64_t srcJ = src0 + dJ;
                                for (int64_t r = 0; r < rowsHere; ++r) {
                                    AscendC::Axpy(acc_[accBase + r * WSA_ + w0],
                                                  xcomp[srcJ + r * WINLEN_], tap,
                                                  static_cast<int32_t>(g));
                                }
                            }
```

调用数 `K·K·R`；每次调用都带一套 Level-2 mask 设置，scalar pipe 被打满。

### 其它配套

- **padded 输出消 flush**：`y` 按 `STRIDE` 行距分配（`at::empty({N,C,Ho,STRIDE})`），kernel 每通道一次 flat store；host 返回 `y.narrow(3,P,Ws)` 视图。验证脚本先 `.contiguous()`，无影响。
- **`S>1` 分组窗**：垂直 tap `i` 的输入行 `(r0+r)*S+i` 在输出行序下不连续 → 每个 `i` 一组窗口行（窗口行号 `i*R+r`），K 组；flat 律用 `i*R*STRIDE`。`S=1` 用紧凑窗（`ROWS=R+K-1`，偏移 `i*STRIDE`）。
- **`W%EA≠0` 的 staging**：整带一次对齐 DMA（行距 `W`，band 行数 = `(R-1)S+K` 或 `ROWS`）→ 逐行 `Adds(win[m*STRIDE], stg[h0+(rowL-lo)*W], 0, W)` 进 padded 窗口；整带版约 75 次调用 vs 逐行版约 670 次。
- **tiling 目标反转**：flat 方案的调用数 ∝ `ceil(Ho/R)`（每 task 每通道 `K·K` 次，与 R 无关）⇒ **最大化 R**（约束 tasks≥16、UB 预算），CB 取满足并行度的最大带。V5 的“最小任务数”会把 R 压小。
- **数值**：fp32 lane 保持 `fp32→fp16(RNE)→fp32` 往返 + fp32 Axpy（eager = fp16 操作数 + fp32 累加）；`Axpy<float,half>` 半宽源实测慢 3–5%（省一次 cast、2B/元素读无收益），不要用。

## 设计决策

- **为什么用 flat 窗口而不是逐行**：Level-2 Axpy 的固定成本是 mask 设置，不是元素工作；把 `K·K·R` 次小调用合并成 `K·K` 次跨行调用，scalar 成本按 R 摊薄。
- **为什么 acc 与窗口同 stride**：这样单个 tap 的源/目的偏移是常量，一次 flat Axpy 可以跨行；如果 acc 用紧凑行距，每个 tap 都要按行重算偏移，又会退回逐行调用。
- **为什么 padded 输出**：`Wo%8≠0` 时原方案需要独立 flush kernel 压紧；把行距直接设成 STRIDE，host 用 view 取有效列，flush 整体消失（28 例受益）。
- **为什么 mask 段要独立**：`Duplicate`/`Cast`/`Adds` 等 Level-2 调用会复位 mask 模式；mask hoist 必须放在这些调用之后、tap 循环之前，循环内只调 `Axpy<T,U,false>`。
- **为什么不用 `Axpy<float,half>`**：半宽源省一次 cast，但混合类型 vaxpy 没有加速，实测慢 3–5%；保留 fp32 往返。
- **为什么仍保留非契约对齐的 flat Axpy**：310P 本轮的 50/50 与 5.4× 是实测收益，且目标版本未触发断言；但它依赖实现对未对齐起址的宽容，不是接口保证。若工程要求契约洁净（Debug 构建、跨 CANN 版本、形式化检查），应改用按 tap 对齐窗口或 per-row Axpy，并重新测性能。
- **当前方案路线档位**：`recommended_fastpath`。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调。
- 相关文件：`op_kernel/conv_depthwise2d_v5.cpp`（before）、`op_kernel/conv_depthwise2d_v6.cpp`（after）、`op_host/conv_depthwise2d.cpp`（tiling/padded 输出）。
- 实现证据：`asc-devkit/impl/basic_api/dav_m200/kernel_operator_vec_ternary_scalar_impl.h:42-82`（Level-0/Level-2 Axpy）；`include/basic_api/kernel_operator_vec_binary_scalar_intf.h`（`Adds` 族）。

## 完整代码

V6 的 C/D 段（含窗口零化）与 V5 的 `sameAligned` 分支已按代码语义内联，均为函数内 scoped excerpt（窗口零化注释在开发轨迹的两版编辑间有 reflow，代码语义一致；完整函数见开发会话的 V6 kernel 快照、窗口零化补丁与 V5 kernel 快照）。V6 的 A 段（`V6LoadAligned`/`V6LoadStaged`/`V6StageToWin`）是装载/staging 实现，完整文件在 `op_kernel/conv_depthwise2d_v6.cpp`；本卡聚焦 C/D 的调用税与 mask hoist，不重复展开装载函数。

## 性能影响

同一算子内部、同一轮测量内（310P，标准 `msprof quick` kernel 级 `Task_Duration`）：

- 单 task 的 Axpy 调用数：`K·K·R` → `K·K`（与 R 无关）。
- 主 kernel `scalar_ratio`：0.85 → 0.28–0.46；`Ws%8≠0` 的 28 例 flush kernel 整体消失。
- 全量 50 例 kernel 级 geomean 从 V5 到 V6 约 **5.4×**（同算子、同轮、标准 quick；参照路线=V5）。
- 精度 50/50 保持（V6 轮测试集；max_abs ≤ 1.9e-6）。
- 参照路线：V5（per-row Axpy + flush）；来源平台：310P。

## 验证信号

来源：9 号 ConvDepthwise2d V6 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`/`artifact_verified`）。Level-2 Axpy 的实现由 asc-devkit 固定提交 `a6a99bcf` 的 impl 源码独立核对。

- Level-2 `AxpyImpl` 每次调用展开 `SetMaskCount` + `SetMask<U>(0,count)` + `vaxpy` + `ResetMask` + `SetMaskNorm`；按 2736–6000 调用/核反算 75–90 scalar cycles/调用。（来源平台：310P；证据等级：tool_observed）
- V5 主 kernel `scalar_ratio 0.82–0.87`、`vec_ratio 0.29–0.45`；V6 `scalar_ratio 0.28–0.46`，flush kernel 消失。（来源平台：310P；证据等级：artifact_verified）
- 精度 50/50（V6 轮测试集）；全量 50 例 kernel 级 geomean 从 V5 到 V6 约 5.4×（同算子、同轮）。（来源平台：310P；证据等级：artifact_verified）

## 失效边界

- **`S>1` 的宽度浪费**：源算子契约是“先算 stride-1 全宽 Ws 再按 S 切片”，V6 的 `S>1` 分组窗仍有 2× 宽度浪费；相位分解（偶/奇列拆分）可砍一半，未做。
- **vec 占比仍 0.60–0.66**：RMW 3×4B/元素 ≈ 15–16 fp32 elem/cycle，已贴 vaxpy 吞吐；进一步收益要靠减少元素工作或换数据通路。
- **WINBLK 未 EA 对齐**：`P=1/2` 且 `CB≥2` 的 case max_abs≈3.3，`CB=1` 全对；必须保证 `WINBLK%EA==0`。
- **窗口残留**：`S>1` 且 `P>0` 的 case 若不在每 task 尾部零化窗口，会读到上一 task 的残留（max_abs≈3）。
- **`Axpy<float,half>`**：半宽源慢 3–5%，不要为了省 cast 换。
- **逐 tap 源起址非 32B 契约对齐**：`winBase+rowOff+j` 的 `+j` 在 fp32 下是 4B 粒度；310P 实测 50/50，但 `Axpy` 的 UB 起址要求是 32B。Debug 构建、换 CANN 版本、或换编译器前必须重验；需要契约保证时改对齐窗口/per-row。
- **跨代际**：只验证 310P；其它代际的 Level-2 调用成本/掩码语义不同（未验证，推断不可迁移）。

## 坏实践

- 用 per-row Axpy 写 direct-conv，然后调向量化/双缓冲；瓶颈是调用数，不是元素吞吐。
- 把 `SetMaskCount`/`SetVectorMask` 放在每行/每 tap 里；Level-2 调用的固定成本就是这么来的。
- 用紧凑 acc 行距 + padded 窗口；偏移不再是常量，flat Axpy 退化成逐行。
- 用 `Axpy<float,half>` 省 cast；混合类型 vaxpy 没有加速。
- 把 310P 上 flat Axpy 的 50/50 当成接口契约：`Axpy` 的 UB 起址要求 32B，逐 tap 的 `+j` 偏移不满足；换构建/版本前先重验。

## 误诊

- 第一轮把 V5 的慢归因为“向量算力不够”，想加核/换 tiling；profiler 的 `scalar_ratio 0.85` 和源码里的 per-row 循环才把方向纠正到“调用数”。
- 第二轮把 `Axpy<float,half>` 当成省 cast 的优化；实测慢 3–5%，因为混合类型 vaxpy 没有额外加速。
