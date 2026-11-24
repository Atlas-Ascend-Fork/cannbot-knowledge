---
type: Optimization
title: decode 分 KV 任务轴重组（S<=16 场景）
description: 将decode任务按KV块重组为B×N_kv×headBlocks×s2OuterBlocks，并在线性任务轴上均分到核
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/01-decode-splitkv-task-axis.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：decode 分 KV 任务轴重组（S<=16 场景）

> **单一优化点：** S<=16（decode/MTP）场景把任务轴从 `B×N_kv×G×⌈S/mBase⌉`
> （Q 行主序、单任务串行扫全 S_kv）改为 `(bNkv, gSq=hb*s2OuterBlocks+c)`——
> **S_kv 长轴按 s2Chunk 切块升入任务轴**（多核并行 + 确定序 online-softmax
> 归并），同 KV head 的 G 个 query head 折叠进单任务 M 维复用同一 K/V chunk。

> **已验证锚点：** GQA bench 子集 {1,3,8,11,12,14,15,16} 均值 0.5597→0.1878ms
> （3.0x）。decode 单 case：case12（bf16 B16 S1 Skv2048 Nq96 G12）577→55us
> （**10.5x**）、case14（fp16 B128 S1 Skv4096 Nq128 G16）1742→144us（**12.1x**）、
> case11 196→54us（3.6x）、case15 655→190us、case16 727→466us。20/20 allclose。

---

## 1. 优化原理

### 1.1 性能问题模式

S=1 decode 时原任务轴 mBase=128 行 M 维**有效行只有 1**：

- cube M 维空算：128 行槽装 1 个有效行，MM1 利用率 ~1/128；
- S_kv 长轴（2048/4096）在单任务内串行，其它 AIC 空闲；
- 大 batch 下任务粒度极不均衡（每任务 = 一个 q head 的全部 KV）。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 任务轴/分核 | `totalWork=B×N_kv×headBlocks×s2OuterBlocks`，`usedCoreNum=min(totalWork, aicNum=8)` 线性均分；decode 任务数轻松打满 8 AIC 且多波均衡 |
| G 头折叠 | 同 (b,kvHead) 的 G 个 q head 折叠进单任务 M 维（共享同一 K/V chunk，K/V 装载一次）：S==1 → rowPitch=1（GM 同一查询行内 G 头连续，稠密单次 Nd2Nz）；S∈[2,16] → rowPitch=16（每头一个 16 行对齐分形槽） |
| online softmax | 每 s2 块产出 partial (max,sum,O)，块序固定 owner 确定序归并，与 full softmax 分块等价 |
| 片上存储 | 折叠 Q [hc×dim] 常驻 qBufL1 半区；K/V chunk 按任务装载复用 |

### 1.3 核心改动点

- **host tiling**（`op_host/gqa_tiling.cpp`）：`isDecodeBranch=qSeqLen<=16`；
  `decodeRowPitch=S==1?1:16`；`headChunkFull=clamp(BLOCK_M/rowPitch,1,G)`；
  小 B 补核：`groups=B×N_kv×headBlocks < aicNum` 时减小 headChunk 换 headBlocks；
  `totalGSq=headBlocks×s2OuterBlocks`（decode 口径，与 prefill 的 `G×qOuterBlocks` 单点切换）。
- **kernel 任务反解码**（`op_kernel/gqa_kernel.h` CreateTask）：decode 分支
  `hb=curGSq/s2OuterBlocks, c=curGSq% s2OuterBlocks`；`qHeadBase=kvHead*G+hb*headChunk`；
  `hc=min(headChunk, G-hb*headChunk)`；物理折叠 M=`hc*rowPitch`（≤mBase=128 恒成立）。
- **Q 折叠装载**（gqa_cube.h LoadQChunkDecode）：rowPitch=1 → 稠密
  `LoadNdGmToNzL1(qL1, qGm, hc, dim, ld=dim, dstNzC0Stride=AlignUp(hc,16))`；
  rowPitch=16 → 逐头 `LoadNdGmToNzL1(qL1[j*16*dim], qGm+j*dim, S, dim, ld=N_q*dim, 16)`。
- **MM1**：Mm1FoldedBlockDecode（mRows=hc*rowPitch，A 装载列距 colC0Stride=pitch，
  Fixpipe 有效行 fixM=S*hc 不写垃圾行）。
- **Vec1 垃圾行整块跳过**：rowPitch=16 且 S<=8 时物理行块 [16k+8,16k+16) 整块
  continue（有效行 i<S≤8 恒落前半），不拷贝/不掩码/不 softmax/不写 P。
- **causal 掩码折叠行语义**：折叠行 p 的序列行号 `i=p mod rowPitch`（组内全部
  折叠头共享同一 i 序列），掩码档位与 prefill 分支同口径。

## 2. 正确性红线

- **确定序归并**：同组 s2 chunk 必须同核按 loop 连续出现（gSq 编码 c 最快变化），
  归并顺序确定，run-to-run bit 级可复现，禁 AtomicAdd。
- rowPitch=16 槽内 [S,16) 垃圾行不得污染 softmax state 或写回 y（§1.3 垃圾行跳过
  + y 写按 i<S 丢弃双重防护）。
- decode 下 `s2Cur` 恒 0 不进位（s2 已并入 gSq），AdvanceTaskCursor 分支勿混用
  两坐标系的任务数口径。

## 3. 泛化条件

- **适用**：S<=16 且 `B×N_kv×G×⌈Skv/s2Chunk⌉ ≥ aicNum×2`；MQA（N_kv=1、G 大）
  收益最大（折叠后 M 维有效行占比 1/128 → hc/128）。
- **不适用**：S>16 prefill（Q 行主序能填满 M 维）；任务数 < aicNum 且 headChunk
  已到 1（最坏逐头任务）仍打不满核。

## 4. 实施步骤

1. TilingData 末尾追加 `isDecodeBranch/headChunkSize/headBlocks` 三字段
   （host 声明序==赋值序==kernel 读取序；不动 TilingKey，运行时 if）。
2. CreateTask 双口径反解码 + AdvanceTaskCursor decode 分支。
3. LoadQChunkDecode 折叠装载 + Mm1FoldedBlockDecode。
4. Vec1/Vec2 state 行号按折叠物理行推导；Vec1 垃圾行整块跳过；y 写按 i<S。

## 5. LLM 前置问题

- S=1 时 M 维有效行占比？S_kv 是否单任务串行？任务数 vs aicNum？
- 折叠装载 dstNzC0Stride 与 L1 半区跨度是否满足 D=256 上界（hc*pitch*dim*2B ≤ 半区）？
- headChunk 补核边界：G=1（MHA）时 headBlocks=1，有无除零/死任务？

## 6. 风险与回退

- 编译失败多因 TilingData 字段序不一致（host/kernel 两份镜像）。
- 回退旋钮：`isDecodeBranch` 置 0 整支回原轴，与其它策略解耦。
- 与 02 号（网格重调）叠加时，headChunk/s2Chunk 的取值以 02 号网格结果为准
  （本策略默认值 128/1024 不是最优）。

## 7. 验收标准

- 精度：20 case allclose（含 MQA case18 / MHA case19 退化）+ sequential 场景。
- 性能：decode 类 case ≥3x（本锚点 10x+）；prefill case ±2% 噪声内不回退。
- 均衡性：profiler timeline 无单核长热点。

## 检索卡（短卡）

动作：将decode任务按KV块重组为B×N_kv×headBlocks×s2OuterBlocks，并在线性任务轴上均分到核
适用：S≤16，且任务量B×N_kv×G×Skv/s2Chunk不少于AIC核数的2倍
限制：同组s2 chunk须同核连续且确定序归并；追加字段须保持host声明序、赋值序与kernel读取序一致。
范围：S≤16的decode/MTP路径
检索词：decode、分KV任务轴、s2OuterBlocks、线性分核、确定序归并
机会：decode中M轴128行槽仅有1个有效行，且KV长轴工作可拆分
