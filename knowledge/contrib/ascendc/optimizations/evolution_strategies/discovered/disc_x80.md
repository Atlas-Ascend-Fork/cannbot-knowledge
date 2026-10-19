---
type: Optimization
title: "Chunked/SSM Cube 内核的『调用/指令条数』受限消除链（K 维融合 + 列组瓦片 + 行主序紧凑布局 + AIC gemm 合并）"
description: "MIX(Cube+Vector) 实现的 chunk-scan/SSM 类内核，块内 matmul 维度极小（如 [BT,BT]x[BT,16]）时，瓶颈既不是算力也不是带宽，而是**Cube 调用次数与向量指令/搬运条数**：单次 MatmulImpl IterateAll 有约 6us 库固定开销、每次 GM<->UB 搬运被拆成 BT 条 32B 微块（blockCount=BT, blockLen=1）；实测每次 Cube 调用摊销 ~2.2us 的 mte2+fixpipe 固定成本且与调用次数严格线性。四步链消除：(1) **K 维融合**——把 kNum 个 K 块拼成一个 [rows,K] tile，块内 matmul 由 [BT,BT]x[BT,16] 变成 [BT,BT]x[BT,K]，AIC 循环从 ch x kNum x 4 次 IterateAll 降到 ch x 4 次；(2) **列组瓦片**——向量粒度 [BT,16]\\(=1024 元素) 升到 [BT,W]（kwg=min(kNum, 4096/(BT*16)) 即 W=64/128，瓦片 <=4096 元素），逐元素算子与每次搬运变成 1 条大操作；(3) **紧凑布局改行主序 [NCH,BT,K]**——这是让列组搬运成为单条多块 DataCopyParams 的前提，pack/unpack 从「每 chunk kNum 次小搬运」降为「每张量 1 读 1 写」；(4) **AIC gemm 合并 4->2 + 屏障削减**——A 面板改 [nch,2BT,BT]（aq/ak 竖直相邻）使一次 M=2BT gemm 算 C1|C2，同一面板 isTransposeA 得 [aqT|akT] 再算 C3+C4；AIV 屏障改成「一次发齐 MTE2 -> 纯 V 段 -> 批量 MTE3」三段式，每组屏障 14~16 -> 3。ChunkKdaBwdIntra benchmark_evo：R2 4.53x -> R5 11.235x 相对基线（935.386 -> 83.2584us，全量 50 case，50/50 精度，vs PyTorch 9.61x -> 107.94x）。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X80: 调用/指令条数受限消除链（Cube chunk-scan 内核）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X80
> origin: discovered
> title: "Chunked/SSM Cube 内核的『调用/指令条数』受限消除链（K 维融合 + 列组瓦片 + 行主序紧凑布局 + AIC gemm 合并）"
> description: "MIX(Cube+Vector) 实现的 chunk-scan/SSM 类内核，块内 matmul 维度极小（如 [BT,BT]x[BT,16]）时，瓶颈既不是算力也不是带宽，而是**Cube 调用次数与向量指令/搬运条数**：单次 MatmulImpl IterateAll 有约 6us 库固定开销、每次 GM<->UB 搬运被拆成 BT 条 32B 微块（blockCount=BT, blockLen=1）；实测每次 Cube 调用摊销 ~2.2us 的 mte2+fixpipe 固定成本且与调用次数严格线性。四步链消除：(1) **K 维融合**——把 kNum 个 K 块拼成一个 [rows,K] tile，块内 matmul 由 [BT,BT]x[BT,16] 变成 [BT,BT]x[BT,K]，AIC 循环从 ch x kNum x 4 次 IterateAll 降到 ch x 4 次；(2) **列组瓦片**——向量粒度 [BT,16]\(=1024 元素) 升到 [BT,W]（kwg=min(kNum, 4096/(BT*16)) 即 W=64/128，瓦片 <=4096 元素），逐元素算子与每次搬运变成 1 条大操作；(3) **紧凑布局改行主序 [NCH,BT,K]**——这是让列组搬运成为单条多块 DataCopyParams 的前提，pack/unpack 从「每 chunk kNum 次小搬运」降为「每张量 1 读 1 写」；(4) **AIC gemm 合并 4->2 + 屏障削减**——A 面板改 [nch,2BT,BT]（aq/ak 竖直相邻）使一次 M=2BT gemm 算 C1|C2，同一面板 isTransposeA 得 [aqT|akT] 再算 C3+C4；AIV 屏障改成「一次发齐 MTE2 -> 纯 V 段 -> 批量 MTE3」三段式，每组屏障 14~16 -> 3。ChunkKdaBwdIntra benchmark_evo：R2 4.53x -> R5 11.235x 相对基线（935.386 -> 83.2584us，全量 50 case，50/50 精度，vs PyTorch 9.61x -> 107.94x）。"
> confidence: single_op
> status: active
> op_families: [ssm, linear_attention, chunk-scan, cv_fusion, matmul]
> bottlenecks: [scalar_compute, undersize_transfer, mte2_stall, tiling_imbalance]
> tags: [cube-mix, iterateall-fixed-overhead, k-dim-fusion, column-group-tile, row-major-compact-layout, aic-gemm-merge, barrier-reduction, chunk-scan, instruction-count-bound]
> strategy_ids: [X80, X79, P102, X27, P66]
> discovered_round: 5
> discovered_from: "ChunkKdaBwdIntra benchmark_evo round_3/parallel_0 (x0_k1_s1) -> round_4/parallel_2 (x0_x1_x1) -> round_5/parallel_0 (x5a)"
> base_speedup: "4.53x -> 11.235x 相对基线（935.386us -> 83.2584us，全量 50 case，50/50 精度；vs PyTorch 43.35x -> 107.94x）"
> ```

## 判定信号

`task_time.csv` / `op_summary` 出现下面任一组合，即可判为「调用/指令条数受限」而非算力/带宽受限：

- MIX 内核 `aic_mac` 极低（本例 0.019~0.037，**约 2%**），而 `aic_mte2 + aic_fixpipe >= duration`（串行）；
- AIV 侧 `aiv_scalar + aiv_mte2 + aiv_mte3` 超过 `aiv_time` 一半，**但该 case 的数据量按实测带宽算 < 1us**；
- 块内 matmul 维度极小（N 或 K <= 16~64），`MatmulImpl::IterateAll` 调用次数与 `ch x kNum x 4` 同量级。

判据的本质：**固定开销 x 调用次数** 主导，而不是「每个操作有多慢」。

## 核心思路（四步链，建议按此顺序）

### Step 1 — K 维融合（收益最大，约占总降幅 70%）
把 pack 产出的 kNum 个 K 块拼成一个 `[rows, K]` tile，让每个块内 matmul 由 `[BT,BT]x[BT,BK=16]`
变成 `[BT,BT]x[BT,K(64/128)]`。AIC 的 IterateAll 次数从 `ch x kNum x 4` 降到 `ch x 4`（/4~/8）。

> ★ **必须先对齐三处，否则静默算错**：host tiling 的 N=K、kernel 侧 `SetSingleShape(bt, K, bt)`、
> **以及 `SetOrgShape` / 单核 N（ldb）**。只改 host 的 `SetShape` 而不改 ldb 是本算子 R3 第一次失败的真因
> （当时 ldb 仍是 16）；而它的「hot 探针」用了 B 全 1 的退化输入，ldb 错了也看不出来 —— **探针必须是随机满值输入**。

### Step 2 — 列组瓦片 `[BT,W]`
向量粒度从 `[BT,16]`(=1024 元素) 升到 `[BT,W]`，`W` 取 `min(kNum, 4096/(BT*16))`（本例 W=64/128，瓦片 <=4096 元素）。
所有逐元素算子与每次搬运由此变成 1 条大操作。

### Step 3 — 紧凑布局改行主序 `[NCH,BT,K]`
原 `[NTK,BT,16]`（kb 主序）下，列组搬运无法表达为单条多块 `DataCopyParams`。
改成 `[NCH,BT,K]`（chunk 行主序）后，pack/unpack 从「每 chunk kNum 次小搬运」降为「每张量 1 读 1 写」，
列组搬运成为单条 `DataCopyParams`（`srcStride` 携带行 stride）。

### Step 4 — AIC gemm 合并 + 屏障削减
- A 面板改 `[nch, 2BT, BT]`（aq/ak 竖直相邻）=> 一次 `M=2BT` gemm 算 C1|C2；同一面板 `isTransposeA` 得 `[aqT|akT]`（K 维 2BT）再算 C3+C4。**4 gemm -> 2**，wsC 面板 4->3（-25%）、B 面板 MTE2 装载 4->2 次、workspace -25%。
- AIV 屏障改「**一次发齐 MTE2 -> 纯 V 段 -> 批量 MTE3**」三段式：同管道相邻操作无需屏障（V->V、异缓冲 MTE2->MTE2 都不需要），每组 `PipeBarrier<PIPE_ALL>` 由 14~16 降到 3。

## 量化结果（ChunkKdaBwdIntra，Ascend910B2C，全量 50 case）

| 阶段 | geomean asc | 相对基线 |
|---|---|---|
| R2（纯 Cube 初版，未融合） | 206.67 us | 4.53x |
| R3（Step 1 + 布局折叠） | 120.21 us | 7.781x |
| R4（Step 2 + Step 3） | 93.731 us | 9.9795x |
| R5（Step 4 + dbperm 折叠） | **83.2584 us** | **11.235x** |

Step 1 单独贡献约 70%（主核 2606->1355us）；Step 2+3 主核再 1.414x；Step 4 再 1.10x。

## 关键坑

1. **`SetOrgShape`/ldb 必须与 K 融合同步**（见 Step 1 的 ★）。退化输入探针会掩盖该错误。
2. **每次 Cube 调用的固定开销与调用次数严格线性**（实测 16 call/core -> mte2 16.1us；85 -> 81.5us）——
   所以「先放大单次调用规模（K 融合）」再做「替换实现方式」；**顺序反了收益就没了**：
   本例在未融合的结构上手写 Mmad（X27）能拿 1.101x，融合之后只剩 **1.012x**。
3. **手写 Mmad 在 910B2C/CANN8.5.1 上受 L0B 装载路径限制**：唯一正确路径是逐 `[bt,16]` 切片的
   `LoadData3DParamsV2`；n>16 的整条 L0B 装载三种写法全部失败（线性 `LoadData2D` ✗、单条 `LoadData3D(n=K)` ✗、
   MatmulImpl 同款 `LoadData3DParamsV2Pro + fMatrixCtrl` -> **507015 aicore exception**）。见 failure pattern `f23`。
4. **不要为了并行度抬 AIC 核数**：`min(24,nch) -> min(24,4*nch)` 在 nch∈[7,24] 的 case 上慢 **5.95%** ——
   MIX 核的 `SyncAll` 核数成本会吃掉 AIC 并行收益。见 failure pattern `f24`。
5. **拆行/拆 t-block 在掩码已折进操作数后没有收益**：Cube 结构下掩码已在 pack 阶段乘进 A，拆行不减任何 MAC，
   只把 IterateAll 次数翻倍（实测 ~2.2us/次的固定成本）=> 此时主核是「调用次数受限」而非并行度受限。

## 适用场景

- MIX（Cube+Vector）实现、任务粒度 = (chunk/batch, head) 且块内 matmul 维度 <=64 的 chunk-scan / SSM / 线性注意力族；
- 出现「Cube 很闲（aic_mac ~2%）但整核耗时高」或「AIV 指令条数远超数据量」的 profiling 特征；
- 与 X79 正交：X79 解决 host 侧布局 device task 数，X80 解决 kernel 内的调用/指令条数。

## 来源

ChunkKdaBwdIntra benchmark_evo（进化基线内核模式，5 轮）：
- round_2/parallel_1（x0_k1，P102 初版 Cube 化）：206.67us / 4.53x
- round_3/parallel_0（x0_k1_s1，Step 1 + 布局折叠 + `isTransposeA`）：120.21us / 7.781x
- round_4/parallel_2（x0_x1_x1，Step 2 + Step 3）：93.731us / 9.9795x
- round_5/parallel_0（x5a，Step 4 + dbperm 折叠进 unpack）：**83.2584us / 11.235x**，50/50 精度
