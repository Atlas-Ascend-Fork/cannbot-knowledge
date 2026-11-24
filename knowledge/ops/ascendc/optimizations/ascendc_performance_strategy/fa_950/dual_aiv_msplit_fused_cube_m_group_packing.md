---
type: Optimization
title: dual-AIV 子核行分担与 Cube M 轴 group 满载的自包含融合落地（无前置结构依赖版）
description: 由单AIV工作改为dual-AIV子核分担；按B·N_kv组织任务，将G打包到Cube M轴并按BLOCK_M切块
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/01-dual-aiv-msplit-fused-cube-m-group-packing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：dual-AIV 子核行分担与 Cube M 轴 group 满载的自包含融合落地（无前置结构依赖版）

单一优化点（针对「MIX_AIC_1_2 下单 AIV 干活 + decode M=1 pad 到 C0 的 Cube 浪费」双瓶颈）：在**未做过 GQA
group-packing 重构的旧结构 baseline** 上，一次改动同时完成 (a) decode/MTP 路径的 task 重组织——把共享同一
KV 的 G 个 query head 的行折叠进 Cube M 轴（M=G 满载，替代每 head 一 tile、M=min(BLOCK_M,S) 被 pad 的旧路径），
和 (b) `SetMSplitInfo` 行维拆分让每个 AI Core 的两个 AIV sub-core 各担一半行块（lane 与下游消费 lattice 对齐）。
产出非空可编译 diff 的门槛低于完整 group-packing 重构（S1），但实测同时拿到两者的收益。

与存量策略的关系：`mla_strategries/08-dual-aiv-subcore-msplit-by-lattice.md`（S8）假设 M 已被 group-packing
撑大（"requires s1 softly"）；`mla_strategries/01-gqa-group-dim-packing-into-cube-m-axis.md`（S1）是纯 Cube
侧重构。本策略是两者在"裸 baseline"上的**自包含融合落地配方**：不要求先应用 S1，直接从旧结构一次写出。

## 1. 原理

两个耦合浪费同时消除：

- **Cube M 轴浪费**：decode（S=1）时旧结构每 (batch, kv-head, query-head) 一个 task，M=1 却要占 C0=16 的
  Cube 分形，MAC 利用率 1/16；且 KV（K/V 各 S_kv×D）每个 task 各搬一遍，G=128 个 head 重复搬 128 次。
  把同一 KV 组的 G 个 head 折叠进 M 轴（M=G=BLOCK_M）后：一次 Q@K^T / P@V 同时算 G 个 head，KV 只搬一次
  被 G 行复用，task 数从 (B·N_kv)·G 降到 (B·N_kv)·sQ。
- **AIV 单核干活**：MIX_AIC_1_2（1 AIC : 2 AIV sub-core）调度下，默认 Vector 代码只让 sub-core0 处理全部行，
  sub-core1 vecDealM=0 空转陪跑（仅为保持跨核 SetFlag 对称）。M 撑大后按 lattice 对齐边界拆行：
  sub-core0 处理 [0, dealM0)、sub-core1 处理 [dealM0, totalM)，Vector 阶段（softmax/rescale/写回）近似减半。

融合的乘法效应：单独 S8 在 M=1 的旧行结构上无行可拆（totalM < 2*align 自动退化，收益≈0）；单独 S1 只解决
Cube 侧。先在 task 重组织中把行数做大、再在同一个 diff 里落 SetMSplitInfo 拆分，两收益相乘。

## 2. 性能问题模式

- decode/MTP case 耗时比对标实现（如 FusedInferAttentionScore）慢 1~2 个数量级（实测本例 decode 大 batch
  慢 ~96x、MTP 慢 ~54x）；
- profiling 指纹：Cube aic_mac 利用率极低（M=1 pad 到 C0）、Vector 阶段单个 AIV sub-core 占用 ~50% 而另一个
  ~0%、GM→L1 的 KV 搬运流量 ≈ G 倍理论值；
- 结构特征：GQA/MQA（N_q/N_kv = G 个 query head 共享一组 KV），任意"一组输出行共享同一右操作数"的批 GEMM
  同样适用。

## 3. 正确性红线

**M 轴折叠（源自 S1 的硬约束）**
- causal 掩码阈值在 group-pack 后对同一 tile 内所有 M 行一致（同一 seqPos），不可再按序列行 +rowIdx 逐行算；
- layout 感知：BNSD 的 head-stride = S·d，超过 Nd2Nz srcDValue 上限（65535）时必须回退 seq-pack 旧路径，
  否则逐 head strided gather 整体劣化（实测 ~2.9x）；
- N_kv>1 时 qHeadBase = kvHead·G；G > BLOCK_M 须拆 M tile；
- 输出写回按 head 维寻址：BSND head 连续可批量写，BNSD 逐 head 写。

**双 AIV 行分担（源自 S8 的 AP-001..005）**
- 拆分边界必须是下游消费粒度（Vec2/mChunk、写回 tile）的整数倍：packed 行 16 整除用 lane=16，否则 lane=8；
  边界落在 chunk 中间会致写回/maxCache 行基错位；
- 同步对称不可破坏：任何路径两个 sub-core 的 SetFlag 数量必须相等（否则 CrossCore wait 悬挂）；仅退化兜底
  分支允许 idle；
- softmax maxCache/sumCache、rescale 累加等**行级状态 UB 基址须按行段起点 vecMStart 换算**（漏算 chunkRow
  是最常见潜伏 bug）；
- 退化路径逐位等价：totalM < 2*lane 时完整退回"AIV0 全行 / AIV1 idle"，dealM0=0 不得让 AIV1 走非空分支；
- 每 sub-core 行处理上限 BLOCK_M/subBlockNum（128/2=64），UB 容量按此估算。
- 全 mask 行（is_causal 且整行 -inf）softmax 须输出 0 而非 NaN。

## 4. 泛化条件

- **适用**：MIX_AIC_1_2（或任意 subBlockNum>1）调度 + GQA/MQA 注意力 decode/MTP（FlashAttention/MLA/变体），
  尤其 baseline 还是"每 query head 一个 task"旧结构的——本策略一步到位；任意"一组输出行共享同一右操作数、
  且 Vector 阶段有独立行维工作"的批 GEMM。
- **不适用**：非 GQA（G=1，M 折叠无来源）；纯 Cube 无 Vector 行阶段（双 AIV 无活可分）；BNSD head-stride 超
  上限且不实现 seq-pack 回退的场景。
- **与 S1/S8 叠加关系**：已应用 S1 的代码上，本策略退化为 S8 的检查清单（只落拆分）；裸 baseline 上本策略
  替代"S1 然后 S8"两步。

## 5. 实施步骤

1. tiling 层：decode（sQ==1）与 MTP（sQ≤2）路径按 (B·N_kv) 组织 task，M 维 = G（拆 BLOCK_M tile），
   causal 阈值改 per-task 常量；保留 prefill 旧路径不动（本例 prefill 由 tile 放大类策略另行处理）。
2. Cube 侧：Q 按 group 连续行装载（BSND 直接连续拷；BNSD 判 head-stride 上限走回退），K/V 每 task 搬一次。
3. Vector 侧：`SetMSplitInfo` 按 lane=16/8 求 dealM0；两 sub-core 行段 [0,dealM0)/[dealM0,totalM)，状态
   buffer 基址带 vecMStart 偏移。
4. 对照 S8 红线逐条自查（尤其 SetFlag 对称、退化分支）。
5. 精度 gate（全 case）→ 性能 bench（重点 decode/MTP case）。

## 6. LLM 前置问题

- 当前 task 粒度是什么？每 task 的 M 是多少？GQA 的 G 装进 M 了吗？
- 调度是 MIX_AIC_1_2 吗？Vector 阶段两个 sub-core 的 vecDealM 各是多少（看空转的那个）？
- BNSD head-stride（S·d）会不会超 65535？回退路径存在吗？
- 行级状态 buffer（max/sum/rescale）的基址是怎么按 sub-core 行段换算的？

## 7. 验收标准与实测

**实测锚点（Ascend950PR / 950DT，MLA fp16/bf16，cann-bench test11 基线，2026-08-20）**：
- 本策略单独落地（无 S5/S6）：5-case mean 8496 → 794.9μs（10.7x）；
  decode_bf16_b32 11569→119.9μs（**96x**）、mtp_bf16_b16 5786→108.1μs（**54x**）、
  decode_fp16_b60 21607→~331μs（~65x）；prefill 类持平（预期内，非本策略目标）；
- 精度：86/86（basic 20 + general 66）全过；
- 与后续 tile 放大（S5）、空闲核拆分（S6）叠加后 cann-bench 20 case 平均加速比 **1.35x**
  （对标 FusedInferAttentionScore，综合得分 65.57→78.84）。
- 验收：build 过 + 精度全过 + decode/MTP case 数量级下降 + prefill/BNSD case 不劣化（硬指标）。

## 检索卡（短卡）

动作：由单AIV工作改为dual-AIV子核分担；按B·N_kv组织任务，将G打包到Cube M轴并按BLOCK_M切块
适用：采用MIX_AIC_1_2或subBlockNum>1调度的GQA/MQA decode/MTP
限制：group-pack后，同一tile内所有M行的causal掩码阈值必须一致
范围：GQA/MQA注意力的decode/MTP路径
检索词：dual-AIV、MIX_AIC_1_2、group-pack、Cube M、BLOCK_M
机会：query-head任务过小，Cube M利用不足，单AIV工作且存在stage等待
