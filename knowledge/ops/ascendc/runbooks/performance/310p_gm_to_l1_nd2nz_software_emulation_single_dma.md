---
type: "Runbook"
title: "310P GM→L1 Nd2Nz 软件模拟，改单条 DataCopy"
description: "310P 的 GM→L1 Nd2Nz 走 GM→UB 8KB→TransND2NZ→UB→L1 软件模拟，每 8KB 一轮流水同步；GM 已是 L1 镜像布局时改用 DataCopy(L1,GM) 单条 DMA，同轮单 case 快 1.8–3.5×。"
tags: [task.optimization, topic.performance.analysis, topic.data_movement.data_copy, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_data_copy_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_continuous.md
    role: constraint
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-09T00:00:00Z'
platforms: ["310p"]
---

# 310P GM→L1 Nd2Nz 软件模拟，改单条 DataCopy

## 现象

在把 7 号 conv2d 的 dense 路径改成硬件 im2col 后，主 kernel 的 msprof 归因出现一个反直觉的比例：`mte2_ratio` 约占 kernel 时间的三分之一，按搬运字节数折算的等效带宽很低，而同一台设备上 vendor Conv2D 搬同样数据量的时间明显更低。起初按“带宽受限”排查，试了双缓冲、加大单次搬运、减少调用次数，收益都很小；直到直接读 310P 的 DataCopy 实现，才看到 GM→L1 的 ND2NZ 并不是一条 DMA，而是软件模拟。

## 适用场景

- **工程形态**：AscendC kernel 直调（`__global__ __aicore__` + `EXEC_KERNEL_CMD`/raw launch），cube/GEMM 类 kernel 的 GM→L1 操作数装载。
- **API 路径**：`DataCopy(L1, GM, Nd2NzParams)`（ND2NZ）vs `DataCopy(L1, GM, DataCopyParams)`（continuous）；`Nd2NzParams`、`DataCopyParams`。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0（本卡实现证据取自 asc-devkit `a6a99bcf` 的 `impl/basic_api/dav_m200/kernel_operator_data_copy_impl.h`，实测取自 7 号 conv2d 战役）。
- **适用粒度**：`operator_family` —— 凡是 310P 上把 GM 操作数经 L1 喂 cube 的 kernel；不限于卷积。
- **路线优先级**：`recommended_fastpath` —— GM 已经是 L1 镜像布局（`[c1][pixel][16]` 或 `[coBlock][K][16]`）时，单条 `DataCopy` 是唯一正解；否则先做布局预排，再走单条 DMA。
- **明确不适用 / 未验证场景**：GM 布局不是 L1 镜像（任意 ND 行主序、非 16 对齐的通道块）时不能直接替换；其它代际的 Nd2Nz 实现不同（未验证，推断不可直接迁移）。

## 根因

310P 的 `DataCopyGM2L1ND2NZImplBase` 是**软件模拟**，不是 DMA 引擎：

1. 用 `AscendCUtils::GetTemporaryBufferAddr<T>(TMP_UB_OFFSET, 8 * 1024 / sizeof(T))` 取一块 8KB 的 UB 临时区；
2. `DataCopyGM2UBImpl` 把 GM 的 ND 行按 32B 对齐搬到 UB；
3. 在 V 管道上跑 `TransND2NZ` 做 ND→NZ 重排；
4. `DataCopyUB2L1Impl` 再把 NZ 结果搬进 L1；
5. 每个 ND 矩阵前后各有一对 `SetFlag/WaitFlag<HardEvent::MTE3_MTE2>`，即每 8KB 一轮全流水同步。

因此它的成本是“GM→UB + 向量重排 + UB→L1 + 同步”四段之和，而不是一条 `copy_gm_to_cbuf` 的时间。实测折算的等效带宽很低；同一批 case 里 vendor Conv2D 搬同样数据量的时间明显更低。

当 GM 布局**已经是 L1 镜像布局**时，ND2NZ 的重排是恒等变换，可以完全跳过：把 GM 当作 `DataCopyParams` 的连续块源，直接用 `DataCopy(L1, GM, DataCopyParams)` 发一条真 DMA。关键是 stride 的单位：`DataCopyParams.blockLen/srcStride/dstStride` 都是 **32B DataBlock**，不是元素。

## 解决配方

### Before：用 Nd2NzParams 装载

权重（GM 是 `[coBlock][K][16]`，本来就是 L0B 的 NZ 镜像）：

```cpp
            // ---- full-K B for this co tile: staged once per task ----
            LocalTensor<half> wb = qWB_.AllocTensor<half>();
            {
                Nd2NzParams bp;
                bp.ndNum = 1;
                bp.nValue = static_cast<uint16_t>(K_);
                bp.dValue = static_cast<uint16_t>(nTile);
                bp.srcNdMatrixStride = 0;
                bp.srcDValue = static_cast<uint16_t>(coGPad_);
                bp.dstNzC0Stride = static_cast<uint16_t>(K_);
                bp.dstNzNStride = 1;
                bp.dstNzMatrixStride = 0;
                DataCopy(wb, wGM_[static_cast<int64_t>(g) * K_ * coGPad_ + co0], bp);
            }
```

fmap（xNC1 已经是 `[c1][pixel][16]`，即 L1 镜像）：

```cpp
                LocalTensor<half> fmap = qFmap_.AllocTensor<half>();
                {
                    const int64_t planeElems = Hp_ * Wp_ * 16;
                    const int64_t xBase =
                        (static_cast<int64_t>(n) * G_ + g) * ciG1_ * planeElems +
                        static_cast<int64_t>(oh0) * Wp_ * 16;
                    if (planeElems <= V5_ND_STRIDE_MAX) {
                        Nd2NzParams fp;
                        fp.ndNum = static_cast<uint16_t>(ciG1_);
                        fp.nValue = static_cast<uint16_t>(tileRows * Wp_);
                        fp.dValue = 16;
                        fp.srcNdMatrixStride = static_cast<uint16_t>(planeElems);
                        fp.srcDValue = 16;
                        fp.dstNzC0Stride = static_cast<uint16_t>(tileRows * Wp_);
                        fp.dstNzNStride = 1;
                        fp.dstNzMatrixStride =
                            static_cast<uint16_t>(tileRows * Wp_ * 16);
                        DataCopy(fmap, xGM_[xBase], fp);
                    } else {
                        for (int64_t ci1 = 0; ci1 < ciG1_; ++ci1) {
                            Nd2NzParams fp;
                            fp.ndNum = 1;
                            fp.nValue = static_cast<uint16_t>(tileRows * Wp_);
                            fp.dValue = 16;
                            fp.srcNdMatrixStride = 0;
                            fp.srcDValue = 16;
                            fp.dstNzC0Stride = static_cast<uint16_t>(tileRows * Wp_);
                            fp.dstNzNStride = 1;
                            fp.dstNzMatrixStride = 0;
                            DataCopy(fmap[ci1 * tileRows * Wp_ * 16],
                                     xGM_[xBase + ci1 * planeElems], fp);
                        }
                    }
                }
```

### After：单条 DataCopy + L1 镜像布局

权重：一条连续 DMA，`blockLen=K`（32B 块），`srcStride=0`：

```cpp
            // ---- full-K B for this co tile: staged once per task ----
            // GM already holds the [c0block][K][16] NZ panel order -> one plain
            // DMA (Nd2Nz is a software emulation on 310P).
            LocalTensor<half> wb = qWB_.AllocTensor<half>();
            {
                DataCopy(wb,
                         wGM_[static_cast<int64_t>(g) * K_ * coGPad_ +
                              (co0 / 16) * K_ * 16],
                         DataCopyParams{static_cast<uint16_t>(nTile / 16),
                                        static_cast<uint16_t>(K_), 0, 0});
            }
```

fmap：按 plane 组一条 DMA，`blockLen=tileRows*Wp`（32B 块），`srcStride` 是两个 plane 之间的 gap（也是 32B 块）：

```cpp
                // ---- fmap tile: xNC1 rows [oh0, oh0+tileRows) -> L1 ----
                // xNC1 already is the L1 image layout ([plane][pixel][16]), so
                // one plain DMA per plane group (Nd2Nz is a software emulation
                // on 310P: GM->UB->TransND2NZ->L1 with full pipeline syncs).
                LocalTensor<half> fmap = qFmap_.AllocTensor<half>();
                {
                    const int64_t planeElems = Hp_ * Wp_ * 16;
                    const int64_t xBase =
                        (static_cast<int64_t>(n) * G_ + g) * ciG1_ * planeElems +
                        static_cast<int64_t>(oh0) * Wp_ * 16;
                    // xNC1 is already the L1 image layout: plain DMA per plane
                    // group (310P Nd2Nz is a GM->UB->TransND2NZ->L1 software
                    // emulation, ~8KB-chunked with pipeline syncs).
                    const int64_t planeBlocks = tileRows * Wp_;          // 32B units
                    const int64_t gapBlocks = (planeElems >> 4) - planeBlocks;
                    if (gapBlocks >= 0 && gapBlocks <= V5_ND_STRIDE_MAX &&
                        planeBlocks <= V5_ND_STRIDE_MAX) {
                        DataCopy(fmap, xGM_[xBase],
                                 DataCopyParams{
                                     static_cast<uint16_t>(ciG1_),
                                     static_cast<uint16_t>(planeBlocks),
                                     static_cast<uint16_t>(gapBlocks), 0});
                    } else {
                        for (int64_t ci1 = 0; ci1 < ciG1_; ++ci1) {
                            DataCopy(fmap[ci1 * tileRows * Wp_ * 16],
                                     xGM_[xBase + ci1 * planeElems],
                                     DataCopyParams{
                                         1, static_cast<uint16_t>(planeBlocks),
                                         0, 0});
                        }
                    }
                }
```

`gapBlocks` 必须按 **halves/32B 块**算：`planeElems` 是 half 元素数，一个 32B DataBlock = 16 个 half，所以 `planeElems >> 4` 才是块数。第一版写成 `(planeElems - tileRows * Wp_) / 16` 时，gap 少乘了 16，结果是整片 NaN——这是“单条 DMA”路线自己的单位陷阱，不是 Nd2Nz 的问题。

## 设计决策

- **为什么不用 `Nd2Nz` 的“多 burst”形态绕过**：m200 的 Nd2Nz 软件模拟每 8KB 一轮全流水同步，burst 数增加只会增加同步轮数；且它要求源行距 `srcDValue` 与目标 NZ 的语义同时成立，能表达的形状比 `DataCopyParams` 窄。
- **为什么先把 GM 预排成 L1 镜像**：把 ND→NZ 的重排从 kernel 热路径移到 host 侧一次性 prelayout（或前一个 prep kernel），热路径只剩一条连续/多 burst DMA；这是 7 号 conv2d 单 case 热路径去掉 Nd2Nz 软件模拟的关键一步。全量 geomean 的提升与三内核批量化/v6 同轮落地，不能单独归因给本卡。
- **为什么保留 per-ci1 回退分支**：`Nd2NzParams`/`DataCopyParams` 的块长字段是 `uint16_t`，单块上限 65535 个 32B 块；当 plane 的 `planeBlocks` 或 `gapBlocks` 超限时，必须退回逐 plane 单发，不能截断。
- **当前方案路线档位**：`recommended_fastpath`（GM 已是 L1 镜像时）；不是 `safety_fallback`，因为回退到 Nd2Nz 只会在热路径重新引入软件模拟。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调 + `EXEC_KERNEL_CMD` raw launch。
- 相关文件：`op_kernel/conv_standard2d_v5_gemm.cpp`（v6/v7 主线）；`op_kernel/conv_standard2d_v4_xrepack.cpp`（xNC1 预排）；`op_host/conv_standard2d_v4.cpp`（host 侧 prelayout 与缓存）。
- 实现证据：`asc-devkit/impl/basic_api/dav_m200/kernel_operator_data_copy_impl.h:61-75`——plain GM→A1/B1 的 `ASCENDC_REPORT_NOT_SUPPORT` 只在 `#if defined(__DAV_M200_VEC__)` 分支（AIV 编译）出现；`#else`（AIC）走 `copy_gm_to_cbuf`。`:192-260` 是 `DataCopyGM2L1ND2NZImplBase` 的 GM→UB→`TransND2NZ`→UB→L1 软件模拟（ND2NZ 形态）。不要把“AIV 分支的 NOT_SUPPORT”误读成“310P 上 plain GM→L1 一律不可用”。

## 完整代码

上面的 Before/After 两个 causal unit 即完整实现片段；`DataCopyGM2L1ND2NZImplBase` 的关键实现（asc-devkit `a6a99bcf`，逐字）：

```cpp
template <typename T>
__aicore__ inline void DataCopyGM2L1ND2NZImplBase(__cbuf__ T* dst, __gm__ T* src, Nd2NzParams& intriParams)
{
    uint16_t ndNum = intriParams.ndNum;
    uint16_t nValue = intriParams.nValue;
    uint16_t dValue = intriParams.dValue;
    uint16_t srcNdMatrixStride = intriParams.srcNdMatrixStride;
    uint16_t srcDValue = intriParams.srcDValue;
    uint16_t dstNzC0Stride = intriParams.dstNzC0Stride;
    uint16_t dstNzNStride = intriParams.dstNzNStride;
    uint16_t dstNzMatrixStride = intriParams.dstNzMatrixStride;

    uint16_t alignedDValueBlockNum = (dValue * sizeof(T) - 1) / 32 + 1;
    uint16_t alignedDValue = alignedDValueBlockNum * 32 / sizeof(T);

    event_t eventIdMTE3ToMTE2 = static_cast<event_t>(GetTPipePtr()->AllocEventID<HardEvent::MTE3_MTE2>());
    SetFlag<HardEvent::MTE3_MTE2>(eventIdMTE3ToMTE2);
    for (int i = 0; i < ndNum; ++i) {
        WaitFlag<HardEvent::MTE3_MTE2>(eventIdMTE3ToMTE2);
        __ubuf__ T* nd2nzTempBuf = AscendCUtils::GetTemporaryBufferAddr<T>(TMP_UB_OFFSET, 8 * 1024 / sizeof(T));
        if (((dValue * sizeof(T)) % 32 == 0) && ((srcDValue * sizeof(T)) % 32 == 0)) {
            DataCopyGM2UBImpl(
                nd2nzTempBuf, src + i * srcNdMatrixStride,
                {nValue, static_cast<uint16_t>(dValue * sizeof(T) / 32),
                 static_cast<uint16_t>((srcDValue - dValue) * sizeof(T) / 32), 0});
            event_t eventIdMTE2ToV = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));
            SetFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);
            WaitFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);
        } else {
            // copy and pad zero
            for (int j = 0; j < nValue; ++j) {
                DataCopyGM2UBImpl(
                    nd2nzTempBuf + j * alignedDValue, src + i * srcNdMatrixStride + j * srcDValue,
                    {1, static_cast<uint16_t>(alignedDValueBlockNum), 0, 0});
            }
            if (alignedDValue != dValue) {
                event_t eventIdMTE2ToV = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));
                SetFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);
                WaitFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);

                uint16_t downAlignedDValueBlockNum = dValue * sizeof(T) / 32;
                uint16_t downAlignedDValue = downAlignedDValueBlockNum * 32 / sizeof(T);
                uint64_t mask[2];
                mask[0] = ((1 << (alignedDValue - dValue)) - 1) << (dValue - downAlignedDValue);
                mask[1] = 0;
                DuplicateImpl(nd2nzTempBuf + downAlignedDValue, (T)0, mask, nValue, 1, alignedDValueBlockNum);
                PipeBarrier<PIPE_V>();
            } else {
                event_t eventIdMTE2ToV = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));
                SetFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);
                WaitFlag<HardEvent::MTE2_V>(eventIdMTE2ToV);
            }
        }

        __ubuf__ T* nzTempBuf = nd2nzTempBuf + (4 * 1024 / sizeof(T));
        TransND2NZ(nzTempBuf, nd2nzTempBuf, nValue, alignedDValue, (T)0);

        event_t eventIdVToMTE3 = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::V_MTE3));
        SetFlag<HardEvent::V_MTE3>(eventIdVToMTE3);
        WaitFlag<HardEvent::V_MTE3>(eventIdVToMTE3);

        uint16_t widthFractal = alignedDValue * sizeof(T) / 32;
        for (int j = 0; j < widthFractal; ++j) {
            DataCopyUB2L1Impl(
                dst + i * dstNzMatrixStride + j * 32 * dstNzC0Stride / sizeof(T),
                nzTempBuf + j * 32 * nValue / sizeof(T), {nValue, 1, 0, 0});
        }
        AscendCUtils::FreeTemporaryBuffer<T>(nd2nzTempBuf);
        SetFlag<HardEvent::MTE3_MTE2>(eventIdMTE3ToMTE2);
    }
    WaitFlag<HardEvent::MTE3_MTE2>(eventIdMTE3ToMTE2);
    GetTPipePtr()->ReleaseEventID<HardEvent::MTE3_MTE2>(eventIdMTE3ToMTE2);
}
```

## 性能影响

同一算子、同一轮测量内（310P，标准 `msprof quick` kernel 级 `Task_Duration`）：

- 单 case：单条 `DataCopy` 路线相对 v6a 的 `Nd2Nz` 路线快 **1.8–3.5×**（case1 约 2.3×、case13 约 3.5×、case22 约 1.8×、case28 约 2.1×；各 case 的绝对耗时随 shape 变化，不在此列出）。
- 全量：Nd2Nz 单条 DMA 与“三内核批量化 + v6 任意 Wo/grouped”是同一轮一起落地的，全量 geomean 的提升不能单独归因给本卡；本卡只主张**单 case 的同轮相对代价**。
- 参照路线：v6a（`Nd2NzParams` GM→L1）；来源平台：310P。

## 预防

- 在 310P 上看到 GM→L1 的 `mte2` 占比高、但折算等效带宽很低，先读 `kernel_operator_data_copy_impl.h` 确认是不是 Nd2Nz 软件模拟，不要先调双缓冲。
- 改用单条 `DataCopy` 前，先用打印/断点确认 GM 布局确实是 L1 镜像（`[c1][pixel][16]` 或 `[coBlock][K][16]`）；不是的话先做 prelayout。
- 所有 `DataCopyParams` 的 `blockLen/srcStride/dstStride` 按 32B DataBlock 计算；gap 用“元素数 >> 4”，不是“元素数 / 16 后再除别的”。
- 单块长度超过 65535 时走 per-plane/per-ci1 回退，不要截断。

## 验证信号

来源：7 号 conv2d v6→v7 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级均为 `tool_observed`/`artifact_verified`）。实现机制另由 asc-devkit 固定提交 `a6a99bcf` 的 impl 源码独立核对。

- 实现源码：`DataCopyGM2L1ND2NZImplBase` 逐字显示 GM→UB 8KB temp → `TransND2NZ` → UB→L1，且每个 ND 矩阵前后 `SetFlag/WaitFlag<HardEvent::MTE3_MTE2>`。（来源平台：310P；证据等级：tool_observed）
- 改用单条 `DataCopy` 后，同一轮 case 级相对 v6a 路线快 1.8–3.5×；精度 56/56 保持。（来源平台：310P；证据等级：artifact_verified）
- 首版 gap 用 `(planeElems - tileRows * Wp_) / 16` 时输出整片 NaN；改为 `(planeElems >> 4) - planeBlocks` 后恢复。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **GM 布局不是 L1 镜像**：单条 `DataCopy` 不能替代 Nd2Nz；必须先 prelayout（host 或 prep kernel），否则读到的就是错行/错块。
- **块长超限**：`DataCopyParams` 的块长字段是 `uint16_t`，单块上限 65535 个 32B 块；更大的 plane 必须回退到逐 plane 单发。
- **跨代际**：本卡只验证 310P/dav-m200；其它代际的 Nd2Nz 可能是硬件 DMA，不能直接照搬“软件模拟”结论（未验证，推断不可迁移）。
- **未决项**：`DataCopy(L1,GM)` 在多 plane、gap 很大时的最优 burst 组合未系统扫描；当前只验证了“单 plane 组一条 + 超限回退”的形态。

## 坏实践

- 把 `Nd2Nz` 当成 DMA 引擎，看到 `mte2` 高就去调双缓冲/加大单次搬运——软件模拟的瓶颈是 8KB 分块与全流水同步，不是带宽。
- 用 `Nd2NzParams` 装载已经是 L1 镜像的 GM 数据——重排是恒等变换，白付一遍 UB 往返和同步。
- 把 `DataCopyParams` 的 stride 当元素数——gap 少乘 16 会得到整片 NaN，且看起来像“数据坏了”而不是“地址算错了”。

## 误诊

- 另一条 conv3d 战役的 §25 记录的是反方向：ND2NZ 多 burst 明显快于 GM→UB。本卡的“Nd2Nz 软件模拟”内部仍然走 GM→UB 8KB 分段 + 同步，两者的通路上下文不同；不要把 §25 的结论反推成“本卡软件模拟也很快”，也不要把它读成“ND2NZ 比 GM→UB 慢”。
- 第一轮把 mte2 高三分之一读成“带宽受限”，试了双缓冲和更大 burst，收益 <5%；真正原因是 Nd2Nz 的软件模拟路径。
- 第一版单条 `DataCopy` 的 gap 用元素数计算，输出全 NaN；当时先怀疑 `xNC1` 的 pad 区污染，直到把 `planeElems` 按 32B 块重算才定位到单位错误。
