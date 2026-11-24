---
type: Optimization
title: 跨步拷贝 DMA 超集/32B 窗口读 + UB 向量 Gather 压实
description: 把按固定步长逐元素从 GM 取数改为读覆盖目标元素的连续超集或每元素一个 32B 窗口，再在片上用向量 gather 压实。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/superset-window-read-vector-gather-compaction.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：跨步拷贝 DMA 超集/32B 窗口读 + UB 向量 Gather 压实

> 单一优化点：需要"按固定步长从一段连续数据里挑元素"的搬运（非连续元素选择），不要
> 逐元素读 GM（无论是逐元素 MTE2 小 block，还是 SIMT 线程逐 lane LDG），而是
> **用一条 2D MTE2 描述符读"覆盖目标元素的连续超集"（或每元素 1 个 32B 窗口），
> 再在 UB 内用 SIMD `Gather`（每 64/128 lane 一条指令）压成连续输出**。

---

## 1. 原理

**两类成本，必须分别消掉；只消一类通常没有收益（已用对照组验证）。**

| 成本 | 成因 | 消除手段 |
|---|---|---|
| 每元素一次 GM 读请求（含地址算式） | 逐元素 MTE2 `blockLen=db` 小 block；或 SIMT 每 lane LDG（受 LSU 发射率与 VEC 发射占用限制，有效带宽远低于 HBM） | **2D MTE2 描述符读超集/窗口**：`blockCount=rows, blockLen=((cols-1)P+1)·es, srcStride=rowStep-inSeg`；一条描述符吃多行 |
| 每元素一次压实指令 | 逐元素 UB 拷贝（无论标量还是 SIMT） | **SIMD `Gather` + `StoreAlign`**：每 256B slice（b16 128 lane / b32 64 lane）一条，索引向量构造一次、行循环内复用 |

**超集读**：目标集合 `S={base+i·P}`，读区间 `[base, base+(cols-1)·P]`。读放大严格 = `P`，
与元素大小无关；换来"每行一次块拷贝"。`P` 很大时改用 **32B 窗口读**（每元素 1 个 32B 扇区，
放大 `32/es`），再按 32 位字压实。

**选路判据**：
- `P·es ≤ 32`（且 `es∈{2,4,8}`）→ **超集读**；
- 否则若 `es∈{4,8}`、`(P·es)%32==0`、`(baseOff·es)%32 + es ≤ 32`、所有行距 `%32==0` → **32B 窗口读**；
- 否则回退逐元素。

**归因判据（本策略的关键）**：只把读换成 DMA 超集读、而压实仍在 UB 内逐元素拷，通常**没有收益甚至
更差**；只有"DMA 读 + SIMD 压实"同时上才有效。即瓶颈是**每元素指令**，不是"读的引擎"本身。
例外是大 `P` 的窗口读：它只降物理字节（每元素 128B 线 → 32B 扇区），此时即使压实仍逐元素也能获益，
收益应归因为"降物理读放大"而非"降指令数"。

瓶颈类型：mte2/element_issue（跨步内轴）/ vec_bound（压实阶段）。

## 2. 性能问题模式

- 实现形态 A：`DataCopyPad{blockCount=count, blockLen=sizeof(T), srcStride=(P-1)·es}`——每元素一个 block；
  或实现形态 B：`__simt_vf__` 里 `stage[f] = x[base + f·P]`，每 lane 一次 LDG + 一次 STS。
- profiling 症状：mte2 pipe 接近饱和但有效带宽远低于 HBM（形态 A）；或 VEC pipe 接近饱和、
  LSU 加载发射率封顶而 DRAM 远未吃满（形态 B）。
- 结构判据：**输出有用字节 ≪ 需要触碰的地址跨度**（末轴 stride>1），且 `P·es ≤ 32` 或 `P·es` 是 32 的倍数。
- 反例信号（不该做）：`P==1`（连续，直接用连续搬运）；`P·es` 既 >32 又非 32 的倍数（超集放大过大、窗口不对齐）。

## 3. 正确性红线

1. **元素偏移 vs 字节偏移**：`GlobalTensor<uint8_t>` 的下标是字节，DMA 基址若按元素算必须 `★ sizeof(T)`。
   踩坑表现：core0 全对、其余 core 全错（偏移被除以 `es`）。
2. **窗口读的 block 形态与超集读不同**：窗口读必须 `blockCount = rows·cols, blockLen = 32,
   srcStride = P·es - 32`（每元素一个 block），且基址要回退到窗口起点 `srcElem -= winOff/es`；
   沿用 `blockCount=rows, blockLen=cols·32` 会读到连续内存。
3. **UB 侧行距必须与 MTE 的 32B 推进一致**：`PaddingMode::Normal` 下 UB 块按 `ceil32(blockLen)` 推进。
   搬入用 `inPitch=ceil32(inSeg)` 落位，VF 必须用同一 `inPitch` 取行；写出用
   `srcStride=(outPitch-outSeg)/32`（UB 侧单位 32B），`dstStride = rowLen·es - outSeg`（GM 侧单位字节）。
   任一侧不一致 → 行内/行间错位（典型症状：只有首个 block 对）。
4. **行距在批内必须一致且已知**：只允许所有外层 stride > 0（负数退回逐元素）；逐行 base 用 odometer
   增量推进，热循环内不做除法。
5. **UB 预算**：`2·rows·(inPitch+outPitch) + 尾对齐余量` 必须装得下（双缓冲）；同时增行数可能触发
   反解列块（用列块变窄换行块高度，索引摊销才成立；`rows==1` 时索引构造可能占 VF 时间大头）。
6. **若压实用 SIMT**（对照组/降级路径），launch 必须声明 `dyn_ub_size` 覆盖 SIMT TPipe footprint，
   否则 UB 访问窗口塌缩 → 越界错误（本芯片报 errcode 341）；声明值需按平台能力核对。
7. **尾部/头部碎片行**：按核切分若以行对齐（推荐）则只剩最后一核有碎片；一维（`N/L==1`）时
   单行被多核切分，走"单行分段串行"tile，不能套用行批量。
8. **1D 超集不必强行上**：`rows==1` 且 `P·es≤32` 时逐元素路径已足够快，建议按 `rows>1` 门控。

## 4. 泛化条件

- **适用**：末轴（或可折叠的最内层 run）`P>1` 的 strided 拷贝/选择；`es ∈ {2,4,8}`；`P·es≤32` 或
  `P·es % 32==0`；行距在批内等差（mode U 天然成立；mode R 用 odometer 的最内层 digit run 拆批）。
- **不适用 / 收益低**：
  - `P·es>32` 且非 32 倍数（超集放大过大、窗口不对齐）→ 回退逐元素；
  - 外层 stride 含负值（需降序 gather 变体，本卡未覆盖）；
  - `rows==1` 的超集读（逐元素路径更优）；
  - 极小输出：新通路的固定开销（TPipe/事件/kernel 体积）不可忽略，需实测门控。
- **叠加项**：连续（`P==1`）形态另可用"按物理/有用字节定核数（较大 per-core 预算）"和
  "每核工作量只有几 KB 时不再强制拆双 chunk"两条降低固定开销。

## 5. 实施步骤

1. **host 侧判路与定量**（一次完成，写进 tiling）：
   - 算 `winOff=(baseOff·es)%32`，检查窗口对齐条件与所有行距 `%32==0`；
   - 选 `path=1`（超集）/`2`（窗口）/`0`（不动）；
   - 定核数：**按物理读字节** `phys = N·es·amp`（`amp=P` 或 `32/es`）与 per-core 字节预算换算；
     窗口路径再加"每核元素数上限"下限；clamp 到 AIV 数；
   - 反解列块/行块：`cols ≈ budget/(targetRows·(P+1)·es)`，`cols` 向下取 32 的倍数，
     `rows = budget/(cols·(P+1)·es)`；预算取可用 UB 的一半（双缓冲）；超了减 rows。
   - **行块（targetRows）必须分档**：加宽列块（减小行块）能进一步降索引构造与描述符数，但对
     `es` 较大、单行超集很宽的形态会因"行摊销消失 + 单块过大"而显著退化；需按 `es`/`L` 或
     "每行超集字节上限 + 最少行数"二维约束选取，不要用单一常数（1D/`rows==1` 时取 1）。
2. **kernel 侧切分**：优先**按整行切核**（`rowsPerCore=ceil(rows/numBlocks)`，`f0=bid·rowsPerCore·L`），
   消除每核头尾碎片；`N/L==1` 时退回 flat 切分。
3. **搬入**：`DataCopyPad{blockCount=rows, blockLen=inSeg, srcStride=rowStep·es-inSeg, dstStride=0}`，
   `PaddingMode::Normal`；窗口路径改 `{blockCount=rows·cols, blockLen=32, srcStride=P·es-32}`。
4. **压实**：`__simd_vf__` 内 `Arange+Muls(+Adds/Sub)` 构造索引一次，逐 256B slice 复用；
   b16 用 128 lane、b32/字级用 64 lane；`Gather` 后 `StoreAlign` 到 `outPitch` 行距。
   `es==8` 或窗口路径用 32 位字级变体（`elemWords = es/4`；窗口 `wordStride=32/es, baseWord=winOff/es`）。
5. **写出**：`DataCopyPad{blockCount=rows, blockLen=outSeg, srcStride=(outPitch-outSeg)/32,
   dstStride=rowLen·es-outSeg}`，目的基址 `(row·L+colOff)·es`。
6. **流水**：2 槽 ping-pong + 4 对事件（`MTE2_V`/`V_MTE2`/`V_MTE3`/`MTE3_V`），发射下一块后再 drain
   上一块；每个列块结束把两槽的 pending 事件全部 wait 掉，避免 set/wait 失配。
7. **收尾**：头/尾碎片行用单行串行 tile；`es` 只支持 2/4/8，其余回退。

## 6. LLM 前置问题

- 最内层的 `P`（元素步长）与 `es`：`P·es` 是否 ≤32，或是否 32 的倍数且 `winOff+es≤32`？
- 行距在批内是否等差（mode U？mode R 能否用最内层 digit run 拆批）？外层 stride 是否全为正？
- 是否已有逐元素循环（`blockLen=es` 的 block spray 或 SIMT 逐 lane LDG）？profile 里 mte2/VEC 谁打满？
- 目标输出规模/形状：`rows==1`？行数是否足够摊销索引构造（建议每 slice 构造覆盖 ≥4~8 行）？
- UB 预算是否容得下 `2·rows·(inPitch+outPitch)`？是否需要反解列块换行块？
- 若保留 SIMT 压实，launch 是否声明足够的 `dyn_ub_size`（否则 UB 访问越界）？
- 是否只支持 dtype 2/4/8 字节，其余是否有回退路径与精度回归？

## 检索卡（短卡）

动作：把按固定步长逐元素从 GM 取数改为读覆盖目标元素的连续超集或每元素一个 32B 窗口，再在片上用向量 gather 压实。
适用：内层步长大于 1 且步长乘元素宽不超过 32 或为 32 的整数倍，输出有用字节远小于需触碰的地址跨度。
限制：行基址须 32B 对齐；窗口读的块形态与超集读不同；片上行距须与搬运的 32B 推进一致；外层步长为负时退回。
范围：非连续元素选择的搬入环节（按固定步长跳选、列方向选择）。
检索词：超集读、32B 窗口、DataCopyPad、blockCount、srcStride、向量 gather、压实、读放大。
机会：逐元素小块搬运把有效带宽压到很低，且向量发射被每元素压实指令占满。
代价：读放大到步长倍，需额外片上压实与行距窗口对齐处理。
