---
type: "Runbook"
title: "DataCopyPad 尾块改逐行一维搬入"
description: "2D DataCopyPad 的多块参数未把短块落到 256B UB 行首，会让 LoadAlign 读错行；逐行 blockCount=1 可消除歧义。"
tags: ["task.debugging", "topic.precision", "topic.data_movement.data_copy"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopyPad 尾块改逐行一维搬入

## 现象

在 `operators/cummin/cummin.asc` 的 `(M,R,N)` 前缀扫描中，首行输入能正确搬入，但只要当前内层块小于一个 256B UB 行，后续扫描行的值和索引就大量错位。远端 Ascend950 探针显示：满 256B 块全部正确；不足 256B 的块即使满足 32B 对齐仍失败；一个满块后接很短尾块时，只有尾块失败。

逐行打印时，`r=0` 完整正确，而后续行会出现本应属于其他行/其他 lane 的值。代码当时用一次 2D `DataCopyPad` 搬入 `rTile` 个 block，并把 `srcStride`、`dstStride` 当成 block 之后的 byte gap，令 `dstStride = 256 - blockLen`。

## 适用场景

- 工程形态：Ascend C Kernel 使用 UB 固定 256B 行承载每个扫描位置，MTE2 一次搬多个逻辑行。
- API 路径：`DataCopyPad(LocalTensor, GlobalTensor, DataCopyExtParams, DataCopyPadExtParams)`。
- 已验证环境：Ascend950PR_957c / `dav-3510`，CANN 9.0.1，注册平台 `950`。
- 适用粒度：`same_operator`，也可迁移到相同“GM 行片段 → 固定宽 UB 行”的搬入模式。
- 路线优先级：`safety_fallback`。这是 fallback，性能不是最优，追求性能请用另一路线（见 ## 相关）。逐行 DMA 优先保证地址正确，未在本轨迹中证明性能最优。

## 根因

错误只随 `blockLen < 256B` 出现，而与 32B 对齐无关。把部分掩码替换为全掩码后，错误数量和“满块正确、尾块失败”的边界基本不变，排除了 Reg mask 是首要根因。 决定性差异落在 2D `DataCopyPad` 的多块参数化：原实现假定 `srcStride`/`dstStride` 可以按 block 末尾后的 byte gap 填写，并用 `dstStride = 256-blockLen` 表示 UB 行距；实卡结果证明该参数组合没有把后续短 block 实体化到 `r*256B` 的 UB 行首。`LoadAlign(inBuf + r*VL_T)` 仍按固定 256B 行寻址，因而从第二行开始读取错行，错误再被前缀状态传播。 轨迹中的修复注释把这一现象解释为 start-to-start byte stride，但查询到的卡片和头文件没有给出足以跨版本推广的明确契约。故本卡只采纳工具闭环能证明的机制——“该 2D 参数组合造成 UB 行落点与 `LoadAlign` 行距不一致”——不把 start-to-start 解释写成通用 API 结论。 改成每个 `r` 单独一次 `blockCount=1` 的一维搬入后，不再使用 stride 字段；GM 和 UB 起点都由显式索引给出，消除了语义歧义。

## 解决配方

以下是修复动作前后完整的 `ProcessTile`，逐字来自轨迹中的完整初始写入与成功 Edit 回放。

### before

```cpp
    __aicore__ inline void ProcessTile(int64_t rowBase, int64_t nStart,
                                       uint32_t nLanes, uint32_t rTile,
                                       int32_t rBase, uint32_t isFirstTile)
    {
        constexpr uint32_t VL_T = AscendC::VECTOR_REG_WIDTH / sizeof(DT);
        constexpr uint32_t VL_I = AscendC::VECTOR_REG_WIDTH / sizeof(int32_t);

        // ---- CopyIn (MTE2): one 2D strided DataCopyPad of rTile blocks
        // (nLanes each) from GM[m, rBase..rBase+rTile-1, nStart] -> UB rows
        // (contiguous, each row VECTOR_REG_WIDTH = 256 B). Stride fields are
        // byte GAPS: GM rows N apart -> srcGap = (N-nLanes)*sizeof; UB rows
        // 256 B apart but each block is only nLanes*sizeof bytes -> dstGap pads
        // the remainder so the next block lands at the next 256 B row
        // (dstGap = VECTOR_REG_WIDTH - nLanes*sizeof; 0 for float/int32 where
        // the block fills the whole row, 128 for half/bfloat16).
        // EnQue signals MTE2 completion; DeQue (V) waits.
        AscendC::DataCopyPadExtParams<DT> inPad{false, 0, 0, 0};
        int64_t inGmOff = rowBase + static_cast<int64_t>(rBase) * N_ + nStart;
        uint32_t inBlockBytes = static_cast<uint32_t>(nLanes * sizeof(DT));
        uint32_t gmGap = static_cast<uint32_t>((N_ - static_cast<int64_t>(nLanes)) * sizeof(DT));
        uint32_t ubRowGap = AscendC::VECTOR_REG_WIDTH - inBlockBytes;
        AscendC::DataCopyExtParams inParams{static_cast<uint16_t>(rTile), inBlockBytes, gmGap, ubRowGap, 0};
        auto inLocal = inBufQ_.AllocTensor<DT>();
        AscendC::DataCopyPad(inLocal, xGm_[inGmOff], inParams, inPad);
        inBufQ_.EnQue(inLocal);

        // Fill idxSrc (V pipe, TBuf): broadcast rBase+r across all VL_I int32
        // lanes per row. Classic LocalTensor Duplicate is a data-fill (not a
        // compute op) and replaces the unreliable RegBase Duplicate<int32_t>
        // (see cummin_scan_vf header comment). V-only, no cross-pipe sync.
        auto idxSrcLocal = idxSrcT_.Get<int32_t>();
        for (uint32_t r = 0; r < rTile; ++r) {
            AscendC::Duplicate(idxSrcLocal[r * VL_I],
                               static_cast<int32_t>(rBase + r),
                               static_cast<int32_t>(VL_I));
        }

        // ---- Compute (V): DeQue waits for the MTE2 CopyIn DMA to complete
        // before the vf LoadAlign reads inBuf. Running (min, idx) in registers;
        // carry in UB. outVal/idxI32 written by StoreAlign (V).
        auto inDeq = inBufQ_.DeQue<DT>();
        auto carryVal = carryValT_.Get<DT>();
        auto carryIdx = carryIdxT_.Get<int32_t>();
        auto outVal = outValQ_.AllocTensor<DT>();
        auto idxI32 = idxI32T_.Get<int32_t>();
        auto idxSrc = idxSrcT_.Get<int32_t>();
        ComputeCumminScan<DT>(carryVal, carryIdx, inDeq, outVal, idxI32, idxSrc,
                              nLanes, rTile, isFirstTile);
        outValQ_.EnQue(outVal);          // signal V->MTE3 for outVal
        inBufQ_.FreeTensor(inDeq);

        // ---- Cast argmin int32 -> int64 at the store boundary (documented
        // exception; separate idxI64 buffer -> zero address overlap). idxI32
        // written by the vf and read here are both V pipe (ordered). Cast
        // writes idxI64 (V); EnQue signals V->MTE3 for the CopyOut consumer.
        auto idxI32Cast = idxI32T_.Get<int32_t>();
        auto idxI64 = idxI64Q_.AllocTensor<int64_t>();
        AscendC::Cast(idxI64, idxI32Cast, AscendC::RoundMode::CAST_NONE,
                      rTile * VL_I);
        idxI64Q_.EnQue(idxI64);

        // ---- CopyOut (MTE3): DeQue waits for V completion. Per-r 1D
        // DataCopyPad (blockCount=1) for values (DT) and indices (int64).
        auto outValOut = outValQ_.DeQue<DT>();
        auto idxI64Out = idxI64Q_.DeQue<int64_t>();
        int64_t outGmOff = rowBase + static_cast<int64_t>(rBase) * N_ + nStart;
        uint32_t valBlockBytes = static_cast<uint32_t>(nLanes * sizeof(DT));
        uint32_t idxBlockBytes = static_cast<uint32_t>(nLanes * sizeof(int64_t));
        AscendC::DataCopyExtParams valOutParams{1, valBlockBytes, 0, 0, 0};
        AscendC::DataCopyExtParams idxOutParams{1, idxBlockBytes, 0, 0, 0};
        for (uint32_t r = 0; r < rTile; ++r) {
            AscendC::DataCopyPad(vGm_[outGmOff + static_cast<int64_t>(r) * N_],
                                 outValOut[r * VL_T], valOutParams);
            AscendC::DataCopyPad(iGm_[outGmOff + static_cast<int64_t>(r) * N_],
                                 idxI64Out[r * VL_I], idxOutParams);
        }
        outValQ_.FreeTensor(outValOut);
        idxI64Q_.FreeTensor(idxI64Out);
    }
```

### after

```cpp
    __aicore__ inline void ProcessTile(int64_t rowBase, int64_t nStart,
                                       uint32_t nLanes, uint32_t rTile,
                                       int32_t rBase, uint32_t isFirstTile)
    {
        constexpr uint32_t VL_T = AscendC::VECTOR_REG_WIDTH / sizeof(DT);
        constexpr uint32_t VL_I = AscendC::VECTOR_REG_WIDTH / sizeof(int32_t);

        // ---- CopyIn (MTE2): per-r 1D DataCopyPad (blockCount=1, no stride
        // fields) from GM[m, rBase+r, nStart] -> UB row r. Each row is exactly
        // one blockLen=nLanes*sizeof(DT) DMA; the rest of the 256 B UB row is
        // left stale but is never output (StoreAlign/CopyOut use the same
        // nLanes). This mirrors the verified operators/mul pattern ({1, len,
        // 0,0,0}) and avoids the 2D-strided stride-semantics ambiguity that
        // corrupted partial (nLanes<64) cases: when blockLen<256 B the
        // src/dst stride fields are *start-to-start byte strides* (NOT byte
        // gaps), so a dstGap of VECTOR_REG_WIDTH-blockLen landed blocks at
        // r*blockLen-row spacing instead of r*256 B rows, and LoadAlign then
        // read shifted/wrong-row data. Per-r 1D places each row explicitly.
        // EnQue signals MTE2 completion; DeQue (V) waits.
        AscendC::DataCopyPadExtParams<DT> inPad{false, 0, 0, 0};
        int64_t inGmOff = rowBase + static_cast<int64_t>(rBase) * N_ + nStart;
        uint32_t inBlockBytes = static_cast<uint32_t>(nLanes * sizeof(DT));
        AscendC::DataCopyExtParams inParams{1, inBlockBytes, 0, 0, 0};
        auto inLocal = inBufQ_.AllocTensor<DT>();
        for (uint32_t r = 0; r < rTile; ++r) {
            AscendC::DataCopyPad(inLocal[r * VL_T],
                                 xGm_[inGmOff + static_cast<int64_t>(r) * N_],
                                 inParams, inPad);
        }
        inBufQ_.EnQue(inLocal);

        // Fill idxSrc (V pipe, TBuf): broadcast rBase+r across all VL_I int32
        // lanes per row. Classic LocalTensor Duplicate is a data-fill (not a
        // compute op) and replaces the unreliable RegBase Duplicate<int32_t>
        // (see cummin_scan_vf header comment). V-only, no cross-pipe sync.
        auto idxSrcLocal = idxSrcT_.Get<int32_t>();
        for (uint32_t r = 0; r < rTile; ++r) {
            AscendC::Duplicate(idxSrcLocal[r * VL_I],
                               static_cast<int32_t>(rBase + r),
                               static_cast<int32_t>(VL_I));
        }

        // ---- Compute (V): DeQue waits for the MTE2 CopyIn DMA to complete
        // before the vf LoadAlign reads inBuf. Running (min, idx) in registers;
        // carry in UB. outVal/idxI32 written by StoreAlign (V).
        auto inDeq = inBufQ_.DeQue<DT>();
        auto carryVal = carryValT_.Get<DT>();
        auto carryIdx = carryIdxT_.Get<int32_t>();
        auto outVal = outValQ_.AllocTensor<DT>();
        auto idxI32 = idxI32T_.Get<int32_t>();
        auto idxSrc = idxSrcT_.Get<int32_t>();
        ComputeCumminScan<DT>(carryVal, carryIdx, inDeq, outVal, idxI32, idxSrc,
                              nLanes, rTile, isFirstTile);
        outValQ_.EnQue(outVal);          // signal V->MTE3 for outVal
        inBufQ_.FreeTensor(inDeq);

        // ---- Cast argmin int32 -> int64 at the store boundary (documented
        // exception; separate idxI64 buffer -> zero address overlap). idxI32
        // written by the vf and read here are both V pipe (ordered). Cast
        // writes idxI64 (V); EnQue signals V->MTE3 for the CopyOut consumer.
        auto idxI32Cast = idxI32T_.Get<int32_t>();
        auto idxI64 = idxI64Q_.AllocTensor<int64_t>();
        AscendC::Cast(idxI64, idxI32Cast, AscendC::RoundMode::CAST_NONE,
                      rTile * VL_I);
        idxI64Q_.EnQue(idxI64);

        // ---- CopyOut (MTE3): DeQue waits for V completion. Per-r 1D
        // DataCopyPad (blockCount=1) for values (DT) and indices (int64).
        auto outValOut = outValQ_.DeQue<DT>();
        auto idxI64Out = idxI64Q_.DeQue<int64_t>();
        int64_t outGmOff = rowBase + static_cast<int64_t>(rBase) * N_ + nStart;
        uint32_t valBlockBytes = static_cast<uint32_t>(nLanes * sizeof(DT));
        uint32_t idxBlockBytes = static_cast<uint32_t>(nLanes * sizeof(int64_t));
        AscendC::DataCopyExtParams valOutParams{1, valBlockBytes, 0, 0, 0};
        AscendC::DataCopyExtParams idxOutParams{1, idxBlockBytes, 0, 0, 0};
        for (uint32_t r = 0; r < rTile; ++r) {
            AscendC::DataCopyPad(vGm_[outGmOff + static_cast<int64_t>(r) * N_],
                                 outValOut[r * VL_T], valOutParams);
            AscendC::DataCopyPad(iGm_[outGmOff + static_cast<int64_t>(r) * N_],
                                 idxI64Out[r * VL_I], idxOutParams);
        }
        outValQ_.FreeTensor(outValOut);
        idxI64Q_.FreeTensor(idxI64Out);
    }
```

## 设计决策

选择逐行 `blockCount=1`，因为它把每个 GM 行起点和 UB 行起点显式化，可以用一次改动隔离 stride 语义。放弃继续调整 mask，因为全掩码探针已证明错误边界不随 mask 改变；放弃继续猜测 `srcStride/dstStride` 的 gap 数值，因为当前轨迹没有一个经过上板确认的 2D 参数组合。

当前方案是 `safety_fallback`：DMA 调用次数增加，但建立了可验证的正确基线。若要恢复批量 2D 搬入，应先用独立搬运探针确认两个 stride 字段的单位和 start-to-start 规则，再与逐行结果逐 byte 比对。

## 预防

- 对 2D 搬运同时覆盖“block 恰好填满 UB 行”和“block 明显短于 UB 行”的测试；只测满块会掩盖 stride 误解。
- 在计算前直接 dump UB 的前两行，先确认搬运布局，再排查 Compare/Select。
- 不把 32B 对齐通过当作 stride 正确的证明；对齐只约束块长，不证明下一块起点。
- 保留逐行一维版本作为 correctness oracle，再优化为 2D DMA。

## 验证信号

验证来自本次 cummin 开发中的远端 Ascend950 NPU 探针与完整 pytest，证据等级均为 `tool_observed`。

- 修复前的尺寸扫描显示：满 256B block 零错误，多个不足 256B 的 block 均大量错误；满块后附加尾块时，错误只落在尾块（950，tool_observed）。
- 强制 `CreateMask<ALL>` 后，同一不足 256B 的用例仍失败，证明 mask 修改没有闭环（950，tool_observed）。
- 将 CopyIn 改为逐行 `blockCount=1` 后，完整 pytest 从 14 个通过推进到 94 个通过；剩余 14 个失败只集中于两种 16 位 dtype，随后由独立的 lane-lock 修复处理（950，tool_observed）。
- 所有独立根因修复完成后，完整 pytest 为 109 passed、20 skipped，最终评测 20/20 正确（950，tool_observed）。

## 失效边界

- 本卡没有证明所有 CANN 版本、所有 `DataCopyPad` 重载都采用同一 stride 契约；迁移前必须以目标版本 API 或独立探针复核。
- 如果 UB 目标本来就是紧密排列而非固定 256B 行，逐行起点公式需要相应调整。
- 逐行 DMA 的性能没有与合法的 2D 参数化版本对比，不应宣称为快路径。

## 坏实践

- 只用满寄存器块验证 2D stride。
- 部分块失败时反复修改 mask，却不先检查 CopyIn 后的逐行 UB 布局。
- 把字段名中的 stride 自动理解为 gap，或反过来，未用目标版本实测确认。

## 误诊

曾把部分块故障归因于 `UpdateMask`。改用全寄存器 mask 后错误保持，且坏数据表现为跨行错位，因此该假设被否定。