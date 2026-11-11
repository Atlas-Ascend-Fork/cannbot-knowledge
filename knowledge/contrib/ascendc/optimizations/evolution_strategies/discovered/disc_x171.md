---
type: Optimization
title: "X171: 跨 block 完成标志的两个静默陷阱：DataCopyPad 打包与首 launch 残留 UB"
description: "DataCopyPad 搬运 4B 元素块时，UB 侧会按 32B 对齐打包，轮询判等的偏移必须与打包后布局一致；否则会稳定撞满轮询上界但结果仍正确。另一个陷阱是首 launch 读到残留/未初始化 UB：同一输入连跑两次，第一次错、第二次对，应做 device 端逐段 PRINTF 定位脏块，而不是继续 Fill/PipeBarrier 扰动调度。"
tags:
  - task.debugging
  - topic.precision
  - topic.architecture
status: draft
sources: []
created_at: "2026-10-29T06:00:00Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X171: 跨 block 完成标志的两个静默陷阱

## 陷阱 1：DataCopyPad 的 4B 元素块会被按 32B 对齐打包
- **现象**：designated block 的轮询**每一次**都稳定撞满安全上界，但 kernel 退出后结果**完全正确**（数据其实早已就绪）。
- **误诊路径**：先怀疑"并发 case 串改标志"（per-forward 标志区 + epoch 后现象不变）、再怀疑"MTE3 写 GM 后另一 block 的 MTE2 读不可见"（加 dcci 后现象仍不变）——两者都不是主因。
- **真因**：`DataCopyPad(blockCount=gg*2, blockLen=4B, srcStride=28B, dstStride=1)` 在 UB 侧把每个 4B 块补齐到 32B，再叠加 `dstStride` 个 32B 间隔 → 第 i 个标志实际落在 `fpoll[i*64B]`，而判等读的是 `fpoll[i*32B]`。
- **修法**：把整组标志当作**连续 1D 缓冲**一次搬（`blockCount=1`，长度 = n*32B），打包与判等用同一套偏移。可见性要按访问方式区分：只有 Scalar 经核内 DCache 访问 GM 时才需要对应 `DataCacheCleanAndInvalid`；DMA 路径（MTE3 写 / MTE2/DataCopyPad 读）应使用完成与顺序同步（如 Set/Wait、SyncAll），刷新 DCache 不能替代 DMA 完成顺序。
- **判据**：若"单进程单流 + 单 case"也能稳定复现上界撞满，就不要先查并发/可见性，先查**读回布局**。

## 陷阱 2：首 launch 残留 UB 读的指纹是"同一输入第二次就对了"
- **现象**：全量 harness 下必现单元素污染（其余元素逐位一致、污染常在 flat index 0）；单独跑该例、或用随机数据跑多次却通过。
- **排查线索（非唯一根因）**：同一输入在同一上下文里**连跑两次** → 第一次错、第二次与 golden 逐位一致，提示首 launch 读到了未初始化/残留 UB；但工作区初始化时序等问题也可能呈现同样现象，需用下面的 PRINTF/对拍进一步定位，不能仅凭该现象定论。
- **无效修法**（都只扰动调度）：对目的缓冲 `Fill(0)` / `Fill(非零常量)` / `Fill + PipeBarrier<PIPE_V>`（子集能过、全量仍败）。
- **有效路径**：做 device 端 PRINTF/对拍（升宽 Cast、广播图、RA 归约、写回四处逐段），把"只在首 launch 为脏"的那块 UB 找出来并显式初始化。

## 适用场景
- 跨 block 完成标志、轮询同步、多 block 协作的 kernel。
- 需要"首 launch 与后续 launch 行为不同"的静默精度问题。

## 实现要点
1. 任何 `DataCopyPad` 的小元素块都要确认 UB 侧的打包布局；判等/索引使用打包后的偏移。
2. 跨 block 可见性按访问方式处理：只有 Scalar 经核内 DCache 访问 GM 时才需要对应的 `DataCacheCleanAndInvalid`；DMA 路径（MTE3 写 / MTE2/DataCopyPad 读）用完成与顺序同步（如 Set/Wait、SyncAll）。不能用刷新 DCache 掩盖布局错误。
3. 首 launch 残留问题优先用"连跑两次"实验分类，再做 PRINTF 定位；不要用 Fill/PipeBarrier 碰运气。
4. 修复后要同时验证单跑、连跑、全量 harness 三种口径。

## 验证方法
- 构造轮询上界日志，确认是否撞满；对比打包前后偏移。
- 同一输入连跑两次/多次，统计首次与后续的差异。
- 全量精度 + 重复 launch 稳定性。

## 关联
- 与 [X170](disc_x170.md)（host 读错地址）和 [X161](disc_x161.md)（跨 launch 竞态）共同覆盖"单次测试看不见的静默错误"。
