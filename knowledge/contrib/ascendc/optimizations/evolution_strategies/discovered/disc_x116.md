---
type: Optimization
title: "X116: 向量阶段的通道级 DMA 批处理（issue-many / wait-once）"
description: "向量阶段的逐通道「下发 DMA → 等一次同步」成本由 DMA 往返次数与固定延迟支配，不是带宽；把同相位通道搬运算子合并为 issue-many / wait-once 批处理即可摊薄。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/transfer_larger_data_blocks.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x116.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X116）。
>
> 原始元数据：
>
> ```yaml
> id: X116
> origin: discovered
> confidence: cross_op_verified
> op_families: [convolution, cv-mix, reduction, elementwise]
> bottlenecks: [mte2_stall, undersize_transfer, no_overlap, scalar_compute]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x116.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x116.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X116: 向量阶段的通道级 DMA 批处理（issue-many / wait-once）

## 核心思路
小 shape 的向量阶段（crop/stats/smean/out/prep）常被写成「逐通道：下发 1-5 个 DMA → 立刻
SetFlag/WaitFlag 等它 → 下一通道」。这类阶段**不是带宽受限**：实测 crop 搬 1.0MB 花 86us
**DMA 往返次数 × 固定延迟(~0.3us)**，再乘以 #channels/#cores。

改法：一个「通道块」（nCh 条通道，由 UB 预算定，通常 32-64）的所有 DMA 先背靠背下达到
互不相交的 UB 切片，最后**只等一个 flag**（同核内 MTE2/MTE3 保序，一个 flag 足够）。
每核往返次数从 #channels 降到 #blocks。

配套：把中间张量的槽位 pitch 从 `align64(HW)+8` 收到 `align8(HW)`，读者改用
`DataCopyPadExtParams{isPad=true, rightPadding=8-hw%8, paddingValue=0}` **自带零填充**，
从而删掉「零 slack DMA + 逐通道 7 次标量 GM SetValue 补尾」。

## 适用场景
- 任意「按通道/行独立处理、每次处理量很小」的向量阶段（cv 融合算子的后处理、norm、pooling）；
- 判据：某阶段「字节数/耗时」比 HBM 低一个数量级，且 kernel 内出现 `for c: DataCopy; SetFlag; WaitFlag`；

## 实现要点
- 尾块补零必须整段写零，只写 `[align8(hw), hwP)` 会让 `[hw, align8(hw))` 未定义（症状：随机 case 失败）；
- 某些 level-0 二元指令用 `repeatTimes=nc` + count/bitmap mask 时只有 repeat 0 正确，
 退回 rep=1 + 显式行偏移更稳；stride 单位是 32B(=8 floats)，别按元素算。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 复用来源 2：MLA preprocess 的 vec1 / vec2 段（本例算子，）

两段都是「逐行 / 逐 head：下发 1 条小 DMA → 立刻 SetFlag/WaitFlag → 下一行」，与本策略的
反模式完全同构，改造后分别从 369us→~120us（vec1）与 953us→570us（vec2）@T=8192：

- **vec2（对 out_q 每 head 末 64 通道就地 RoPE）**：同一行内相邻 head 的 rope 段在 GM 上是严格等距栅格
 （`blockLen = rope*esize = 128B`，`srcStride = (hd-rope)*esize = 256B` 为常数），于是**整行 128 个 head
 用一条 `DataCopyPad(blockCount=rows, blockLen=128B, srcStride=...*(c2-rope))` 搬完**；
 一批 DMA 全量下发后只 SetFlag/WaitFlag 一次；MTE3 回写延迟一个 buffer 才等；配 P1 双缓冲后
 每核同步往返 2730 → 513。另配 X112 的 `src1RepStride=0` 广播 MAC，把 `[rope]` 的 cos/sin
 用一条 level-0 `Mul` 广播到全部 head（取代 128 次小 Mul）。
- **vec1（q_c / kv_c 行 RMSNorm + k_pe RoPE）**：一次 2D `DataCopyPad` 搬 nr 行 × 整行段
 （`blockCount=nr, blockLen=行段长, srcStride=(c1-段长)*esize`），块内 `ReduceSum` 背靠背下发、
 每行结果独占 32B slice，**全块只做 1 次 V→S / S→V**（原为每行各一次）；cos/sin 用 `[rows,rope]`
 一次算完、整块只留 1 次 `PipeBarrier<PIPE_ALL>`。跨流水同步 14 次/行 → 1.14 次/行。

**新增注意（来自本算子）**：`--cce-auto-sync` 不覆盖「标量读 UB（S 流水）→ 下一条 DMA 覆写同一 buffer
（MTE2）」这条**反向**依赖，跨 chunk 复用位置缓冲时必须显式补 `PipeBarrier<PIPE_ALL>()`（见 F22）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x116.json`；引用时请结合上文适用条件与失效边界判断适用范围。

