---
type: "Runbook"
title: "转置卷积等价标准卷积：零插值 32B 粒度免费"
description: "转置卷积 = 零插值上采样 + 翻转权重 + pad'=k-1-p 的标准卷积；310P 的 16 通道 block = 32B，列插零就是 block 间隔 1，xrepack 一套 DataCopy 即可表达，之后复用 conv2d 硬件 im2col。"
tags: [task.optimization, topic.performance.analysis, topic.compute.neighborhood.convolution]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/basic_api/kernel_struct_data_copy.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_mm_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/general_description_and_constraints.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Cast.md
    role: constraint
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-22T04:01:25Z'
platforms: ["310p"]
---

# 转置卷积等价标准卷积：零插值 32B 粒度免费

## 现象

ConvTranspose2d 的 v1 实现走“逐 tap GEMM + fused col2im”：每个 `(tap, oh)` 单元要发 10–20 次串行 V/MTE 调用。v2 换了一个完全不同的结构：先把转置卷积改写成**标准卷积**，再复用 conv2d 的硬件 im2col（其 stride/filter 边界见 [310P im2col 负结果卡](310p_im2col_stride_gt1_filter_gt1_silent_zero.md)），热路径从逐 tap 散射变成一次 im2col + 一条 GEMM 链。精度与逐例数据留在项目仓评测记录，本卡只保留可迁移的机制。

关键不是“重写了一个更快的 col2im”，而是**把问题变成了另一个已经解决的问题**。

## 适用场景

- **工程形态**：AscendC kernel 直调；310P 上的转置卷积/反卷积算子，尤其是希望复用 conv2d 硬件 im2col 的场景。
- **API 路径**：`DataCopy` + `DataCopyParams`（xrepack 的行/块写入）；`TransDataTo5HD`（16ch×pos → pos×16ch）；`LoadData3DParamsV2Pro` + `Mmad`（等价标准卷积的 im2col/GEMM）。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0。
- **等价性自查**：先按 `## 验证信号` 的“最小验证步骤”用框架 `ConvTranspose2d` 对拍等价变换，再对拍目标 kernel；不要只凭输出形状一致判断变换正确。
- **适用粒度**：`operator_family` —— 转置卷积/反卷积；也适用于任何“先零插值上采样再卷积”的等价变换。
- **路线优先级**：`recommended_fastpath`（310P 实测）—— 等价标准卷积 + 硬件 im2col；v1 的 tap-GEMM+col2im 是已降级的慢路线。xrepack 的非 8 对齐分支存在 Cast 起址对齐 caveat（见 §2）。
- **明确不适用 / 未验证场景**：本实现的 op 签名只有 `stride/padding`，**固定 `output_padding=0`、`dilation=1`、`groups=1`**（没有这些参数）；fast path 还要求 `p≤k-1`（`padH/padW>=0`）、`Wo≤128`、`kH/kW≤255`、`K≤65535` 且 L1 预算通过，否则走 `composeFallback`。大 K（s=2 时 K 维含 4× 零 tap）下 cube 空算占比过高时可能不划算；其它代际未验证。

## 根因/等价变换

转置卷积（stride=s、pad=p、kernel=kH×kW）可以写成三步：

```
xv[s·ih][s·iw] = x[ih][iw]，其余 0            # 零插值上采样
P = pad(xv, 每边 pad' = k-1-p)               # 逐边 pad'
out[oh][ow] = Σ_{kh,kw} P[oh+kh][ow+kw] · W'[kh][kw]
W'[kh][kw] = w[ci][co][kH-1-kh][kW-1-kw]     # 翻转权重（host CPU 侧，可缓存）
```

输出尺寸天然一致：`Hp - kH + 1 = Ho`；光栅宽 `Wp - (kW-1) = Wo`。等价后的卷积 **stride 恒为 1**，因此绕开 V2Pro/mode 3 在 `stride>1 + filter>1` 的负结果；V1 单块 mode 1 仍有成功证据，但本卡选择 stride=1 的等价变换是更稳的路线。

**零插值为什么免费**：310P 的硬件 im2col 读的是 NC1HWC0 布局（本文的 `NC1HWC0`、`[plane][pixel][16]` 与 `[N][ciG1][Hp][WpImg][16]` 均指同一布局的不同写法），一个位置 = 16 half = 32B = 一个 DataBlock。列插零就是“每写一个有效列，跳过 1 个 block”：

```
s==2: DataCopy(dst, src, DataCopyParams{W_i, 1, 0, 1})   // 每行一条，偶位置落地
s==1: DataCopy(dst, src, DataCopyParams{rows, W_i, 0, WpImg-W_i})
```

零行/零列/pad 全部由 NC1HWC0 的 **一次性 `at::zeros`** 提供，xrepack 只写有效位置、永不清零——不需要元素级 interleave / Gather / Broadcast 复制。

## 解决配方

### 1. host 侧：权重翻转 + pad' + 缓存

- `W'[kh][kw] = w[ci][co][kH-1-kh][kW-1-kw]` 在 host CPU 上重排，按权重 key 缓存（一次性）。
- `pad' = k-1-p`；host 侧的几何是 `Hp = (Hi-1)·s + 1 + 2(kH-1-p)`、`Wp = (Wi-1)·s + 1 + 2(kW-1-p)`、`WpImg = Ru8(Wo) + (kW-1)`（`Wo = (Wi-1)·s - 2p + kW`）。注意 `Hp/Wp` 是**输入侧 pad 后图像**尺寸，`WpImg` 是 NC1HWC0 的行宽；不要把 `Hp` 写成输出尺寸 `Ho`。
- NC1HWC0 用 **device `at::zeros`** 创建；不要用 CPU zeros + H2D（H2D copy 与裸 launch 的排序问题会让每 case 首调整行错）。

### 2. xrepack kernel：把 x 写成零插值/pad 后的 L1 镜像

`x fp32 [N][Ci][Hi][Wi] -> NC1HWC0 fp16 [N][ciG1][Hp][WpImg][16]`；每 task = `(n, ci1, 输入行块)`，每通道一条对齐窗口装载 + `Cast`，一次 `TransDataTo5HD<half>`（16ch×pos → pos×16ch），然后按行 store。

`pitch_` 是每通道在 UB 的行缓冲容量。本实现取 `pitch_ = Ru16(rowBlock_ * Wi_) + 32`（16 元素对齐 + 32 元素余量），不是 `Ru8(pos)`；`else` 分支的 `delta ≤ 7` 与 `cnt = Ru8(delta+pos)` 都落在该余量内，最后一个通道的写入不会越到下一段。复用时至少按 `Ru8(pos) + 8` 预留，不能只按 `Ru8(pos)`。

```cpp
    __aicore__ inline void Process()
    {
        const int64_t numCores = static_cast<int64_t>(GetBlockNum());
        const int64_t coreIdx = static_cast<int64_t>(GetBlockIdx());
        const int64_t totalTasks = N_ * ciG1_ * rowBlocks_;
        const int32_t evMte2V = static_cast<int32_t>(
            GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));
        const int32_t evVMte3 = static_cast<int32_t>(
            GetTPipePtr()->FetchEventID(HardEvent::V_MTE3));
        const int32_t evMte3Mte2 = static_cast<int32_t>(
            GetTPipePtr()->FetchEventID(HardEvent::MTE3_MTE2));

        LocalTensor<float> f32 = f32B_.Get<float>();
        LocalTensor<half> hi = hiB_.Get<half>();
        LocalTensor<half> out = outB_.Get<half>();

        for (int64_t task = coreIdx; task < totalTasks; task += numCores) {
            const int64_t blk = task % rowBlocks_;
            const int64_t t2 = task / rowBlocks_;
            const int64_t ci1 = t2 % ciG1_;
            const int64_t n = t2 / ciG1_;

            const int64_t h0 = blk * rowBlock_;
            int64_t rows = Hi_ - h0;
            if (rows > rowBlock_) { rows = rowBlock_; }
            if (rows <= 0) { continue; }
            int64_t cValid = Ci_ - ci1 * 16;
            if (cValid > 16) { cValid = 16; }
            if (cValid <= 0) { continue; }

            const int64_t pos = rows * Wi_;
            const int64_t pos16 = (pos + 15) / 16 * 16;

            // ---- load x rows (fp32) ----
            const bool fast = ((Hi_ * Wi_) % 8 == 0) && ((h0 * Wi_) % 8 == 0) &&
                              (pos % 8 == 0);
            if (fast) {
                const int64_t src0 =
                    ((static_cast<int64_t>(n) * Ci_ + ci1 * 16) * Hi_ + h0) * Wi_;
                DataCopy(f32, xGM_[src0],
                         DataCopyParams{static_cast<uint16_t>(cValid),
                                        static_cast<uint16_t>(pos / 8),
                                        static_cast<uint16_t>((Hi_ * Wi_ - pos) / 8),
                                        static_cast<uint16_t>((pitch_ - pos) / 8)});
            } else {
                for (int64_t c = 0; c < cValid; ++c) {
                    const int64_t ci = ci1 * 16 + c;
                    const int64_t srcStart =
                        ((static_cast<int64_t>(n) * Ci_ + ci) * Hi_ + h0) * Wi_;
                    const int64_t aligned = srcStart & ~static_cast<int64_t>(7);
                    const int64_t delta = srcStart - aligned;
                    const int64_t cnt = (delta + pos + 7) / 8 * 8;
                    DataCopy(f32[c * pitch_], xGM_[aligned],
                             DataCopyParams{1, static_cast<uint16_t>(cnt / 8), 0, 0});
                }
            }
            SetFlag<HardEvent::MTE2_V>(evMte2V);
            WaitFlag<HardEvent::MTE2_V>(evMte2V);

            // ---- cast to fp16 ----
            if (fast) {
                Cast(hi, f32, RoundMode::CAST_NONE,
                     static_cast<int32_t>(cValid * pitch_));
            } else {
                for (int64_t c = 0; c < cValid; ++c) {
                    const int64_t ci = ci1 * 16 + c;
                    const int64_t srcStart =
                        ((static_cast<int64_t>(n) * Ci_ + ci) * Hi_ + h0) * Wi_;
                    const int64_t delta = srcStart & static_cast<int64_t>(7);
                    Cast(hi[c * pitch_], f32[c * pitch_ + delta],
                         RoundMode::CAST_NONE, static_cast<int32_t>(pos));
                }
            }
            if (cValid < 16) {
                Duplicate(hi[cValid * pitch_], static_cast<half>(0.0f),
                          static_cast<int32_t>((16 - cValid) * pitch_));
            }
            PipeBarrier<PIPE_V>();

            // ---- 16ch x pos -> pos x 16ch ----
            {
                uint64_t srcList[16], dstList[16];
                const uint64_t hiPhy = hi[0].GetPhyAddr();
                const uint64_t outPhy = out[0].GetPhyAddr();
                for (int64_t c = 0; c < 16; ++c) {
                    srcList[c] = hiPhy + c * pitch_ * 2;
                    dstList[c] = outPhy + c * 16 * 2;
                }
                const int32_t reps = static_cast<int32_t>(pos16 / 16);
                if (reps == 1) {
                    TransDataTo5HDParams prm(false, false, 1, 0, 0);
                    TransDataTo5HD<half>(dstList, srcList, prm);
                } else {
                    TransDataTo5HDParams prm(false, false, reps, 16, 1);
                    TransDataTo5HD<half>(dstList, srcList, prm);
                }
            }
            SetFlag<HardEvent::V_MTE3>(evVMte3);
            WaitFlag<HardEvent::V_MTE3>(evVMte3);

            // ---- store to the padded/upsampled image ----
            const int64_t planeBase =
                (static_cast<int64_t>(n) * ciG1_ + ci1) * Hp_ * WpImg_;
            if (s_ == 1) {
                const int64_t dst0 =
                    (planeBase + (h0 + padH_) * WpImg_ + padW_) * 16;
                DataCopy(oGM_[dst0], out,
                         DataCopyParams{static_cast<uint16_t>(rows),
                                        static_cast<uint16_t>(Wi_), 0,
                                        static_cast<uint16_t>(WpImg_ - Wi_)});
            } else {
                for (int64_t r = 0; r < rows; ++r) {
                    const int64_t dst =
                        (planeBase + (s_ * (h0 + r) + padH_) * WpImg_ + padW_) * 16;
                    DataCopy(oGM_[dst], out[r * Wi_ * 16],
                             DataCopyParams{static_cast<uint16_t>(Wi_), 1, 0, 1});
                }
            }
            SetFlag<HardEvent::MTE3_MTE2>(evMte3Mte2);
            WaitFlag<HardEvent::MTE3_MTE2>(evMte3Mte2);
            PipeBarrier<PIPE_ALL>();
        }
        {
            TEventID idE = GetTPipePtr()->AllocEventID<HardEvent::MTE3_MTE2>();
            SetFlag<HardEvent::MTE3_MTE2>(idE);
            WaitFlag<HardEvent::MTE3_MTE2>(idE);
            GetTPipePtr()->ReleaseEventID<HardEvent::MTE3_MTE2>(idE);
        }
        PipeBarrier<PIPE_ALL>();
    }
```

**对齐 caveat（非契约 fast path）**：`fast` 分支的 `f32`/`hi` 起址按 32B 对齐；`else` 分支为处理非 8 对齐的输入，用 `aligned = srcStart & ~7` 装载，`delta = srcStart - aligned`（fp32 下 0–7 个元素 = 0–28B），再 `Cast(hi[c*pitch_], f32[c*pitch_+delta], ...)`——这个 **Cast 源起址不是 32B 对齐**。`Cast` 的 UB 操作数起始地址按通用约束要求 32B 对齐（`general_description_and_constraints.md` 表 2）；因此该 delta 分支是 310P 实测精度通过的宽容行为（逐例数据见项目仓），不是接口契约保证的通用 fast path，Debug 构建或其它版本可能断言/行为未定义。契约洁净的替代：① 不跳过 delta，而是 `Cast` 整个对齐窗口（源 `f32[c*pitch_]` 对齐），把 delta 吸收到 half 侧 channel-major 行缓冲的元素索引：目标 `hi[c*pitch_]` 需容纳 `delta+pos` 个元素（本实现 `pitch_` 的 +32 余量已覆盖；复用时至少 `Ru8(pos)+8`），下游从 `hi[c*pitch_ + delta]` 取数（`TransDataTo5HD` 的 `srcList[c]` 对应改为 `(c*pitch_+delta)*2` 字节）。注意 `delta` 是 fp32 元素偏移，**不能写成 `hi + delta*16`**；`delta*16` 只有在 TransDataTo5HD 之后、pixel-major 的 `out` 上（每像素 16 half = 32B）才成立。这条路径仍需单独核对 TransDataTo5HD 的起址约束。② 上层预对齐/预 pad 输入，使 delta=0；③ 非 8 对齐输入回退到逐元素/通用路径。本卡未对 ①/② 做实测；新工程复用应优先选 ②/③ 或先核对 ① 的起址约束，只有确认目标版本容忍未对齐起址时才直接照抄 delta 分支。

### 3. 等价标准卷积：复用 conv2d 硬件 im2col

NC1HWC0 已经是 `[plane][pixel][16]` 的 L1 镜像，等价卷积的 `stride=1`、`P=0`；gemm 每次装载一行带，`l1H=tileRows`、`l1W=Wp_`（不是整图 `Hp`）；之后就是 conv2d 的 im2col + 裸 Mmad + epilogue。以下为 `ConvT2dGemmKernel::Process` 的逐字片段（注意 gemm 侧用 `Wp_`，dilation 恒为 1——零插值已由 xrepack 完成，不再有 `D_` 变量）：

```cpp
                    SetFmatrix(static_cast<uint16_t>(tileRows),
                               static_cast<uint16_t>(Wp_), pad0,
                               FmatrixMode::FMATRIX_LEFT);
                    LoadData3DParamsV2Pro pa;
                    pa.enTranspose = false;
                    pa.enSmallK = false;
                    pa.filterSizeW = false;
                    pa.filterSizeH = false;
                    pa.fMatrixCtrl = false;
                    pa.channelSize = static_cast<uint16_t>(ciG1_ * 16);
                    pa.extConfig = (static_cast<uint64_t>(kc) << 32) |
                                   (static_cast<uint64_t>(M) << 16) |
                                   static_cast<uint64_t>(kl);
                    pa.filterConfig = (static_cast<uint64_t>(1) << 40) |
                                      (static_cast<uint64_t>(1) << 32) |
                                      (static_cast<uint64_t>(kH_) << 24) |
                                      (static_cast<uint64_t>(kW_) << 16) |
                                      0x0101ULL;
                    LoadData(a2, fmapV[0], pa);
```

## 设计决策

- **为什么不做 tap-GEMM + col2im**：v1 的每个 `(tap, oh)` 单元 10–20 次串行 V/MTE 调用，单元数随 `tap × oh` 增长；等价标准卷积把“散射”变成“预插值 + 规整卷积”，热路径变成一次 im2col + 一条 GEMM 链。
- **为什么零插值放在 32B block 粒度**：310P 的 im2col 位置天然是 16 half = 32B；列插零就是 block 步进 1，不需要元素级 interleave。若按元素插零，会引入 Gather/Broadcast 的额外 V 调用。
- **为什么权重翻转在 host**：翻转只改变权重布局，不改变数值；host CPU 侧一次性重排并缓存，避免每 call 的 kernel 内重排。
- **为什么 NC1HWC0 用 device `at::zeros`**：CPU zeros + H2D 版本在每 case 首调出现整行错（H2D 与裸 launch 的排序问题）；device `at::zeros` 走 torch lazy 队列，与 `EXEC_KERNEL_CMD` 有确定的顺序保证。代价是首轮多一个 `ZerosLike` kernel，测量时按 quick 口径说明处理。**但这只解决 H2D 排序，不解决 E18**。
- **为什么每个新配置要双跑**：裸 Mmad/im2col 在**每个新 `(M,n,k,tiling)` 配置的首发**可能产出错值（实测指纹：每 case 首调整行错、同配置第二次调用起逐位正确）；处置是该配置首次调用把整条流水线跑两遍、丢弃第一遍结果。`at::zeros`、prep H2D 同步、kernel 尾部 MTE3 守卫都不能替代这次双跑。
- **当前方案路线档位**：`recommended_fastpath`。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调。
- 相关文件：`op_kernel/conv_transpose2d_xrepack.cpp`（零插值/pad 预排）、`op_kernel/conv_transpose2d_gemm.cpp`（等价卷积 im2col + Mmad + epilogue）、`op_kernel/conv_transpose2d_flush.cpp`、`op_host/conv_transpose2d.cpp`（权重翻转/pad'/缓存）。
- 实现证据：`asc-devkit/include/basic_api/kernel_struct_data_copy.h:63`（`DataCopyParams`）、`impl/basic_api/dav_m200/kernel_operator_mm_impl.h:328-355`（V2Pro A1→L0A）、`include/basic_api/kernel_struct_mm.h:356`（`LoadData3DParamsV2Pro`）。

## 完整代码

xrepack 的 `Process` 已逐字内联；等价卷积的 `SetFmatrix`/`LoadData3DParamsV2Pro` causal unit 也已内联（`ConvT2dGemmKernel::Process` 逐字片段；gemm 侧用 `Wp_`、dilation 恒 1）。完整的 gemm kernel（K 分块、Mmad 链、L0C 常驻、TransDataTo5HD epilogue）复用 conv2d 的 v5/v6 配方，本卡不重复展开；两边的接口约定是：**NC1HWC0 的 `[plane][pixel][16]` 布局 + `stride=1` + `P=0`**。

## 性能影响

同一算子内部、同一轮测量内（310P，标准 `msprof quick` kernel 级 `Task_Duration`）：

- v1 的每 `(tap, oh)` 单元 10–20 次串行 V/MTE 调用是主因；v2 把这段调用税折成一次 im2col + 一条 GEMM 链。
- v2 的稳态每 case 只剩 2–3 个 kernel（xrepack / gemm / flush）；xrepack 的 fast path 把“每通道多次 Cast”降到每任务 16 次 Cast。
- 参照路线：v1（tap-GEMM + fused col2im）；来源平台：310P。具体分数、门槛与逐例统计留在项目仓评测记录，本卡不复制。

## 预防

- 转置卷积先做等价变换，再考虑 col2im 优化；不要在 tap-GEMM 结构里逐点优化。
- 零插值用 block 粒度表达（`dstStride=1`），不要元素级 interleave。
- 权重翻转/pad' 放 host 并缓存；缓存 key 含完整几何（s/p/k/H/W）。
- NC1HWC0 用 device `at::zeros`；不要用 CPU zeros+H2D 替换（首调排序问题）。
- 每个新 `(M,n,k,tiling)` 配置的首调必须双跑并丢弃第一遍（E18）；`at::zeros` 只解决 H2D 排序，不能消除 Mmad/im2col 的冷启动错值。
- 等价卷积的 `stride` 恒为 1；如果发现还在给 im2col 传 stride>1，说明等价变换没做对。

## 验证信号

来源：ConvTranspose2d v2 重写的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`/`artifact_verified`）。等价变换/零插值的实现由终版 xrepack kernel 逐字核对；API 由 asc-devkit 固定提交 `a6a99bcf` 的头文件/impl 核对。

- 等价变换后精度与参考对齐；逐例分数、门槛与统计留在项目仓评测记录，本卡只保留可迁移的机制与自查步骤。（来源平台：310P；证据等级：artifact_verified）
- v2 稳态每 case 2–3 个 kernel（xrepack/gemm/flush）；v1 每 `(tap, oh)` 10–20 次串行 V/MTE 调用（同算子内部、同轮）。（来源平台：310P；证据等级：artifact_verified）
- 零插值的 block 粒度表达：`s==2` 每行一条 `DataCopyParams{W_i, 1, 0, 1}`；`s==1` 整块一条 `DataCopyParams{rows, W_i, 0, WpImg-W_i}`；两者都在终版 xrepack 中逐字出现。（来源平台：310P；证据等级：tool_observed）

### 最小验证步骤（复现用）

以下为通用自查步骤（不是本轨迹的原始测量）；先单独验证等价变换，再验证 kernel，两步使用同一份权重与输入：

```python
import torch
import torch.nn.functional as F

def ref_ct(x, w, s, p):
    return F.conv_transpose2d(x, w, stride=s, padding=p)

def equiv_conv(x, w, s, p):
    n, ci, hi, wi = x.shape
    co, _, kh, kw = w.shape
    xv = torch.zeros(n, ci, (hi - 1) * s + 1, (wi - 1) * s + 1, dtype=x.dtype)
    xv[:, :, ::s, ::s] = x
    xv = F.pad(xv, (kw - 1 - p, kw - 1 - p, kh - 1 - p, kh - 1 - p))
    wf = w.permute(1, 0, 2, 3).flip(-1).flip(-2)
    return F.conv2d(xv, wf)
```

覆盖输入：`s∈{1,2}`；`kH≠kW`（如 3×5）；`p∈[0,k-1]` 且覆盖 `p>0`/`p=0`；`Ci∈{1,3,16,17,19}`（非 16 倍数与尾块）；`N≥2`；`Hi/Wi` 取 8 的倍数和非倍数（分别走 xrepack 的 `fast`/`else` 分支）；固定 `output_padding=0`、`dilation=1`、`groups=1`。

误差判据：先用 fp64 比 `ref_ct` 与 `equiv_conv`，差应远小于 fp16/bf16 的量级（CPU fp64 下通常是 1e-12 量级；本卡未单独测量该阈值）；若明显更大，先查零插值/pad/flip 顺序，而不是 kernel。再用同一输入比目标 kernel 与 `ref_ct`，按项目 `ops-precision-standard` 的混合容差（fp16 输入/输出记录 `max_abs` 与 `matched_ratio`，任一不达标记失败）；逐例分数留在项目仓，不写入本卡。

## 失效边界

- **op 参数边界**：本实现只接受 `stride∈{1,2}`、`padding>=0`，没有 `output_padding/dilation/groups` 参数；因此 `output_padding=0`、`dilation=1`、`groups=1` 是固定前提，不是可选项。
- **fast path gate**：`p>k-1`（`padH/padW<0`）、`Wo>128`、`kH/kW>255`、`K>65535` 或 L1 预算不足时，host 会走 `composeFallback`，不是等价卷积 kernel。
- **大 K / s=2 的空算**：s=2 时等价卷积的 K 维含 4× 零 tap（零插值带来的空乘），算例 MAC 较小时可忽略，大 K 时可能不划算。
- **E18 冷启动**：每个新 `(M,n,k,tiling)` 配置首调必须双跑；`at::zeros` 只解决 H2D 排序，不能消除 Mmad/im2col 冷启动错值。
- **NC1HWC0 的 device `at::zeros`**：不要换成 CPU zeros+H2D；首调整行错是排序问题，不是数值问题（与 E18 是两件事）。
- **缓存 key**：权重翻转/pad' 的缓存必须含完整几何（s/p/k/H/W）与 dtype；否则跨 case 污染。
- **跨代际**：只验证 310P；其它代际的 im2col/DataCopy 语义不同（未验证，推断不可迁移）。
- **未决项**：`s>2` 的零插值 block 间隔未验证；非零 `output_padding`/`dilation>1`/`groups>1` 不在本实现参数面内，未做探针。

## 坏实践

- 在 tap-GEMM + col2im 结构里逐点优化（v1 的路），而不是先做等价变换。
- 用元素级 interleave/Gather 做零插值；310P 的 32B block 粒度已经免费表达了列插零。
- 把 `Cast` 的源起址当成只要 GM→UB 对齐就安全；`else` 分支的 `f32[c*pitch_+delta]` 不满足 UB 32B 起址对齐，实测过门不等于契约保证。
- 把 `pad'` 算成 `p`，或忘记翻转权重；两者都会得到“尺寸对、值错”的结果。
- 用 CPU zeros + H2D 创建 NC1HWC0；首调整行错，后续命中缓存才正确。
- 只靠 `at::zeros` 就认为首调问题解决了；E18 的 Mmad/im2col 冷启动仍需同配置双跑。

## 误诊

- v1 的第一反应是“col2im 的散射太慢”，于是优化散射的向量化；真正的瓶颈是 `(tap, oh)` 单元数 × 每次 10–20 条串行调用，结构本身需要换。
- 等价变换后一度怀疑 `TransDataTo5HD` 的 `reps` 参数；实际 `reps=1` 与 `reps>1` 是两个合法形态，错的是 `pitch_` 的 32B 对齐。
- **xrepack `else` 分支的 Cast 源起址**：`f32[c*pitch_+delta]` 在 fp32 下是 4B 粒度；310P 实测精度通过（逐例数据见项目仓），但 `Cast` 的 UB 起址要求是 32B，换构建/版本前必须重验；契约洁净做法见 §2 caveat。
