---
type: Operator
title: Block Sparse Attention Grad：Arc35 官方语义与 CATLASS 优化实现
description: 区分 Arc35 官方 bool block mask/workspace 路径与 CATLASS R5 int32 索引表/kernel 内清零/FP32 workspace + post 路径，并记录固定源码、36 例正确性与性能证据。
tags:
- task.design
- task.optimization
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/README.md
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/block_sparse_attention_grad.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_host/arch35/block_sparse_attention_grad_tiling_arch35.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/block_sparse_attention_grad_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/addr_compute.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/cube_op_bsag_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/vec_op_bsag_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/3f54e4334060281fad7b4b682393d22830928a33/attention/block_sparse_attention/README.md
  role: supporting
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/README.md
  role: supporting
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/op_kernel/bsag_kernel.cpp
  role: implementation
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/op_host/bsag_e2e.cpp
  role: implementation
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/test/workload.jsonl
  role: evidence
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/benchmark_final.json
  role: evidence
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/validation_summary.json
  role: evidence
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/bsag_latest_aclnn_comparison.json
  role: evidence
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/docs/performance_report.md
  role: evidence
- resource: https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/docs/knowledge_hits.md
  role: evidence
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-11-02T00:00:00Z'
platforms:
- '950'
verified:
- by: bsag-catlass/e3c13c049616745a17d63ff1f5389ae33f449afa
  at: '2026-11-02T07:32:25Z'
---

# Block Sparse Attention Grad：Arc35 官方语义与 CATLASS 优化实现

本卡消费两份不同的固定材料：`ops-transformer@adc5fd3` 的 Arc35 官方实现，以及
`bsag-catlass@e3c13c0` 的 CATLASS R5 项目实现。后者是本卡的工程落地与证据来源，不作为
官方 Arc35 语义的独立证明。两者共享反向公式，但稀疏输入 ABI、D 的承载方式、workspace
布局和调度不同；**任何结论都必须先声明属于哪一份实现，不能跨实现拼接**。R3/R4 的 host
预清零、正式输出直出方案已废弃，R5 固定为 kernel 内清零 + FP32 workspace + post。
[^arc35-readme][^bsag-catlass-readme][^bsag-catlass-hits]

## 接口与概念

### 算子算法

两份实现使用相同的块稀疏注意力反向计算链：[^arc35-readme][^bsa-forward]

```text
D  = rowsum(dO * O)
S  = scale * (Q @ K^T)
P  = exp(S - LSE)
dP = dO @ V^T
dS = P * (dP - D)
dV = P^T @ dO
dQ = scale * (dS @ K)
dK = scale * (dS^T @ Q)
```

`D` 是逐 query 行的点积归约，不进入 MMAD；五次矩阵乘为 `S`、`dP`、`dV`、`dQ`、`dK`。
`dV` 不乘 softmax scale，`dQ/dK` 乘 scale。P/dS 在进入后三次 MMAD 前窄化到输入 dtype，
因此 oracle 必须允许该舍入边界。[^arc35-cube][^arc35-vector][^bsag-catlass-kernel]

### 两套稀疏输入 ABI

| 项目 | Arc35 官方实现 | `bsag-catlass` 优化实现 |
|---|---|---|
| 输入名 | `blockSparseMaskOptional`（kernel 参数 `blockSparseMask`） | `block_indices` |
| 表示 | 0/1 bool 块掩码 | int32 物理 KV block 索引表 |
| 逻辑 shape | `[B, Nq, QBlocks, KVBlocks]` | `[B, mask_heads, QBlocksMax, K_sel]`；3D 形式可省略 head 维。 |
| head 共享 | 由 `Nq` 维显式表达 | `mask_heads` 为 1 或 `Nq`；为 1 时全部 query head 共享。 |
| 负值 | 不适用 | `-1` 或越界值作为 padding 忽略。 |
| 重复项 | 不适用 | 同值重复只计算一次。 |
| 顺序 | 按 KV block 轴遍历 | 保留索引输入顺序，不排序。 |

官方 README 声明掩码轴序为 `[B, Nq, QBlocks, KVBlocks]`，但固定 kernel 的线性 offset 是
`kvBlock * QBlocks + qBlock`，按行主序等价于读取 `[B, Nq, KVBlocks, QBlocks]`。非对称 mask
会暴露该差异；在官方轴序未确认前，必须双向构造测试，全部为 1 或对称 mask 不能证明实现正确。
[^arc35-readme][^arc35-addr]

`bsag-catlass` 的索引表不能当作官方 bool mask 的直接替代。转换只能按行执行：对每个
`(b, head, q_block)`，按 KV block 递增顺序收集 bool mask 中非零的位置，得到该行的物理 block
索引表；不能把 bool 数值直接当索引使用。[^bsag-catlass-kernel]

### varlen 边界语义

| 项目 | Arc35 官方 / vendor 路径 | `bsag-catlass` 内部 ABI |
|---|---|---|
| 输入名 | `actual_seq_lengths` / `actual_seq_lengths_kv` | `cu_seqlens_q` / `cu_seqlens_k` |
| 长度 | `B` | `B + 1` |
| 起点 | 无前导 0 | 必须为 0 |
| 示例 | 两段 8191、4097：`[8191, 12288]` | `[0, 8191, 12288]` |

官方 kernel 把第 0 项直接作为第一段累计终点，后续项做差分；传入 `[0, ...]` 会把第一段解释成
长度 0，并使后续段整体错位。项目内部使用标准前缀边界，但调用 vendor 基线时必须去掉前导 0：
`cu_seqlens[1:]`，不能把 `cu_seqlens` 原样传给 `actual_seq_lengths`。[^arc35-pipeline]
[^bsag-catlass-host]

### 前向输入契约

`O` 与 `LSE` 必须来自同一次前向、同一 `scale`、同一选择表；`LSE` 为 FP32，`O` 为 FP16/BF16。
当前冻结 contract 不支持 causal、attention sink、滑窗、非零 token mask 或 deterministic 模式；
固定实现没有额外的 LSE NaN/Inf 前置过滤，有限性属于调用方输入约束。[^arc35-readme][^bsa-forward]

## 分核策略与基本块切分

### 官方 Arc35 路径

Arc35 host tiling 读取设备 AIC 核数 `GetCoreNumAic()`，直接写入 tiling 并调用
`SetBlockDim(cubeCoreNum)`；Arc35 固定源码中没有 22/26/28 核分支。不得把优化项目的核数策略
反推为官方行为。[^arc35-tiling]

官方路径的 `D` 由 `SendVecSftgFront`/`SoftmaxGradFront` 写入 `sftg_workspace`；`dQ/dK/dV`
也分别进入 FP32 workspace，最后由 `SendVecPost` 统一 scale/cast 回正式输出。这里确实存在
D、dQ、dK、dV 的 workspace，不应写成“D 内联、dQ 直出”。R5 虽然同样使用 dQ/dK/dV 的
FP32 workspace + post，但 D 在 UB 内联计算、清零位于主 kernel 开头，不能与官方的 D/sftg
workspace 和五 flag 流水混写。[^arc35-pipeline][^arc35-vector]

### CATLASS 优化路径

`bsag-catlass` 采用 per-head-owner：一个任务拥有一个 `(b, h, q_block)`，按 grid-stride 轮转。
固定 layout 下：

```text
qBlocks         = ceil(q_len / 128)
tasks_per_batch = q_heads * qBlocks
total_q_tasks   = batch * tasks_per_batch
task            = (b, h, q_block)
```

varlen 下按每个 batch 的 `ceil(q_len_b/128)` 展开任务；选择表行号仍按全局
`qBlocksMax = ceil(max_seqlen_q/128)` 计算。每个 task 只处理一个 q block，内部按过滤后的
索引表顺序遍历 KV block。[^bsag-catlass-kernel]

核数策略为本项目的固定实测选择：

```text
max_q <= 2048:  varlen ? 26 : 22
max_q >  2048:  28
blockDim       = max(1, min(coreLimit, task_count))
```

核数是 host 启动参数，不是 kernel 常量。该策略只在 `bsag-catlass` 的冻结 workload 上验证；
官方 Arc35 使用设备 AIC 核数。[^bsag-catlass-host]

### 固定块与索引处理

`q_block = kv_block = head_dim = 128`。选择表在 task 内构建紧凑缓存，上限 64 项；超出时回退
标量扫描。过滤规则是：忽略负值和越界索引、折叠重复值、保留首次出现顺序。该实现不会自动
排序，也不会把 bool mask 解释为索引表。[^bsag-catlass-kernel]

## 数据路径与存储层级

### 官方 Arc35 数据路径

```text
prologue : O/dO -> SoftmaxGradFront -> sftg_workspace(D)
           dq/dk/dv FP32 workspace -> 0
task     : QK、dP、P/dS、dV、dQ、dK 走 Cube/AIV 流水
post     : FP32 dq/dk/dv workspace -> scale/cast -> 正式输出
```

官方主 kernel 使用 5 个跨核 flag：`FLAG_C1_V1`、`FLAG_C2_V2`、`FLAG_V1_C3`、
`FLAG_V2_C45`、`FLAG_CUBE_POST`；D 准备完成后和 post 前各一次 `SyncAll`。这是官方结构，
不是优化项目的 22/26/28 核结构。[^arc35-pipeline]

### CATLASS 优化路径数据流

```text
host start : 分配 dqWs/dkWs/dvWs；启动 main，再在同一 stream 启动 post；不 memset
main start : AIV 清零 dqWs/dkWs/dvWs -> PipeBarrier<PIPE_ALL> -> SyncAll<false>
task start : Q/dO GM -> L1；LSE GM -> UB；O GM -> UB
             D[row] = dot(dO[row], O[row]) -> UB
KV loop    : K/V GM -> L1 -> L0A/L0B
             QK MMAD -> L0C -> UB(S)
             dO @ V^T MMAD -> L0C -> UB(dP)
             AIV: P = exp(scale*S - LSE), dS = P*(dP - D)
             P/dS -> L1，AIC 直接消费
             dV = P^T @ dO -> L0C -> FP32 atomic -> dvWs
             dQ += dS @ K -> L0C owner accumulator
             dK = dS^T @ Q -> L0C -> FP32 atomic -> dkWs
task end   : dQ L0C -> FP32 dqWs
post       : dqWs/dkWs/dvWs -> dQ/dK *= scale, dV *= 1.0 -> CAST_RINT -> dQ/dK/dV GM
```

R5 固定 `kUsePostKernel=true`：`BsagMainKernel` 的 AIV 在每次 launch 开头清零三段 FP32
workspace，随后 `SyncAll<false>()` 才进入 AIC/AIV 主流水；dQ 在 owner L0C 内跨 selected
block 累加后写 `dqWs`，dK/dV 以 FP32 atomic 写 `dkWs/dvWs`。`BsagPostKernel` 固定 56 个
AIV block，按 dQ、dK、dV 顺序执行 scale、`CAST_RINT` 和正式输出回写。host 只分配 workspace
并启动两个 kernel，不执行 `aclrtMemsetAsync`；D 仍在 UB 内联，不落 workspace。R3/R4 的直出
方案虽然更快，但依赖 host 预清零正式输出，ABI 责任错误，已回退，不能作为 R5 实现。
[^bsag-catlass-host][^bsag-catlass-kernel]

### Stage 划分与片上容量

优化路径的主要 Stage 为：

| Stage | owner | 输入 | 输出 | 边界 |
|---|---|---|---|---|
| S0 workspace 清零 | AIV | — | dqWs/dkWs/dvWs | `PipeBarrier<PIPE_ALL>` 后 `SyncAll<false>` |
| S1 QK | AIC | Q、K | FP32 S | S 经 L0C→UB 交给 AIV |
| S2 dP | AIC | dO、V | FP32 dP | 与 S1 同一 selected block |
| S3 P/dS | AIV | S、dP、LSE、D | 低精度 P、dS | 写 L1，不回读 GM |
| S4 梯度 MMAD | AIC | P、dS、Q、dO、K | dV/dQ/dK | dQ 留 owner L0C；dK/dV FP32 atomic 到 workspace |
| S5 dQ 回写 | AIC | owner L0C | dqWs | task 末一次完成 |
| S6 Post | AIV x 56 | FP32 dqWs/dkWs/dvWs | dQ/dK/dV GM | dQ/dK 乘 scale、dV 乘 1.0，统一 `CAST_RINT` |

按 `bsag_kernel.cpp` 的 `Layout` 常量重新计算，128 块、FP16/BF16 的片上预留为：

| 层级 | buffer | 大小 |
|---|---|---:|
| L1 | Q、dO | 各 32 KiB |
| L1 | K[2]、V[2] | 各 2 x 32 KiB |
| L1 | P^T[2]、dS[2] | 各 2 x 32 KiB |
| L0C | S、dP、dQ、dKV scratch | 各 64 KiB |
| UB | S[2]、dP[2] | 各 2 x 32 KiB |
| UB | P16[2]、dS16[2] | 各 2 x 16 KiB |
| UB | O16/dO16 staging + D/LSE 行与广播 + tail | 32 + 8.5 + 0.5 KiB |

总计 L1 320 KiB、L0C 256 KiB、UB 233 KiB（`kUbSize = 238592 B`）；K/V/P/dS 都是物理
ping-pong。O32/dO32 在 prologue 期间复用 P16/dS16 区域，不能把该复用再计入总量。该表只描述
`bsag-catlass`，不是官方 Arc35 的资源承诺。清零阶段的全零 tile 复用 UB 起始的 64 KiB
（S ping-pong 区），进入 task 流水后交回 S 使用，不增加静态预留。[^bsag-catlass-kernel]

## 流水排布、同步关系与数值精度

### 滞后一拍

优化路径采用 MM12/MM345 滞后一拍：

```text
MM12(current)  = { S(current), dP(current) }      -> UB
MM345(previous)= { dV, dQ, dK }                   -> L0C / FP32 workspace
```

第 `selected_count` 次是 flush 迭代：不产生新的 MM12，只排空上一轮的 MM345。dQ 在 task 内
跨 selected block 累加，task 末一次写入 `dqWs`；dK/dV 在每块完成后追加到对应 FP32
workspace。[^bsag-catlass-kernel]

### 同步

优化路径使用 `SYNC_MODE=4`，跨核基础 flag 为 `kFlagS`、`kFlagDp`、`kFlagDs`、`kFlagAck`、
`kFlagFree`、`kFlagStride`，分别保护 S、dP、P/dS、AIC 归还、slot free 和双 sub-core 偏移；
其余数据搬运由本地 `HardEvent` 配对。主 kernel 在 AIV 清零 workspace 后使用一次
`PipeBarrier<PIPE_ALL>()` + `SyncAll<false>()`，任务流水本身不依赖 host 预清零；Post 与 Main
在同一 stream 上顺序执行。[^bsag-catlass-kernel][^bsag-catlass-host]

### 数值边界

- Q/K/V/dO/O 为 FP16/BF16；QK、dP、dQ、dK、dV 的 MMAD 累加为 FP32。
- D 在 FP32 中计算；P 由 FP32 S、FP32 scale、FP32 LSE 重算；dS 在 FP32 中形成后窄化。
- 优化路径的 dK/dV 对 FP32 workspace 做 atomic add，跨 task 的累加非确定性会保留到 Post
  的 `CAST_RINT` 之前；dQ 由 owner 独占，不需要 atomic。
- dQ/dK 在 Post 出口乘 `scale`，dV 乘 1.0；三者都在 Post 统一 `CAST_RINT` 回写。
  [^arc35-readme][^bsag-catlass-kernel]

### 正确性与性能证据

以下数据来自固定提交 `e3c13c0`（R5）发布的 36 例冻结 workload，不是 Arc35 源码字面结论，
也不是本次独立复测；frontmatter 的 `verified` 事件记录该固定提交发布方的验证结果
（`bsag-catlass/e3c13c0...`），不代表本知识仓重跑。[^bsag-catlass-workload]
[^bsag-catlass-benchmark][^bsag-catlass-validation][^bsag-catlass-report]

**正确性**

| 指标 | 结果 |
|---|---|
| 用例 | 36/36 PASS |
| 输出 tensor | 108/108 `matched_ratio=1.0`，全部有限 |
| FP16 最大绝对误差 | 0.000488 |
| BF16 最大绝对误差 | 0.001953 |
| 容差 | FP16 atol/rtol=0.005/0.01，cap=0.1；BF16 atol/rtol=0.02/0.01，cap=1.0 |

**性能**：候选为 `BsagMainKernel + BsagPostKernel`，两段 device `Task Duration` 相加；
测量为 Ascend950PR、CANN 9.2.0-beta.2、`msprof op_summary`、warmup=1、repeat=20、逐例 p50。
host API 时间不计入。旧基线为
`torch_npu.npu_block_sparse_attention_backward` 的 Transpose + BlockSparseAttentionGrad
调用链；最新基线为 `ops-transformer@6c8c5f19` 的 aclnn 实现。旧基线与候选在 device 6
采集；最新 aclnn 在 device 7、候选在 device 6 采集，均为独占测量。

| 基线 | 达到 1.0x | 最小 | p50 | 几何平均 | 算术平均 |
|---|---:|---:|---:|---:|---:|
| 旧 `torch_npu` | 36/36 | 1.042x | 1.273x | 1.504x | 1.624x |
| 最新 aclnn | 14/36 | 0.834x | 0.987x | 1.004x | 1.012x |

最新 aclnn 未达 1.0x 的 22 例覆盖 8K/16K 的 fixed/tail/varlen 和 k8/k50；1K 的 12 例全部
达到 1.0x，8K varlen k50 的 2 例也通过。不能用旧基线 36/36 替代最新 aclnn 的 14/36。
逐例输入、耗时和结果见固定 workload 与报告。性能门禁为逐例
`vendor / candidate >= 1.0x`。R5 恢复 workspace + Post 后，大 shape 的 dQ/dK/dV 回写成本
高于 R3/R4 直出实验：8K fixed k50 由 R4 约 1900 us 增至 2093.1 us，8K TND k50 由约
2514.6 us 增至 2851.7 us。这是恢复 ABI 责任后的口径变化；R3/R4 的直出耗时不能作为最终性能。
[^bsag-catlass-benchmark][^bsag-catlass-aclnn]

## 用法

1. 先冻结实现层：选择官方 Arc35 bool mask，还是 `bsag-catlass` int32 索引表；两套 ABI 不能混用。
2. 官方路径冻结 `blockSparseMask` 的轴序、`actual_seq_lengths` 的无前导 0 规则，并采用
   `GetCoreNumAic()`、D/sftg workspace、dq/dk/dv FP32 workspace + post。
3. 项目路径冻结索引表 shape、`mask_heads`、`K_sel` 和 `[B+1]` 前缀边界；需要 bool mask 时先
   完成逐行“非零位置 -> 物理 block 索引”的转换。
4. 若调用 vendor 基线，使用 `cu_seqlens[1:]` 作为 `actual_seq_lengths`，不要传前导 0。
5. 采用 `bsag-catlass` 路径时，必须实现 R5 的“AIV 在主 kernel 内清零 dqWs/dkWs/dvWs +
   dQ 写 dqWs + dK/dV FP32 atomic + 独立 post scale/cast 回写”；host 不得承担 memset，
   也不要采用 R3/R4 host 预清零直出正式输出的方案。D 仍在 UB 内联。
6. 性能判断使用固定 workload 和固定基线；先报告正确性，再报告逐例性能，并分别列出旧基线与
   最新 aclnn 结果。

## 代码模式

以下伪代码只表达 `bsag-catlass` 最终测量路径：

```text
host:
    alloc(dqWs, dkWs, dvWs)
    launch main; launch post

main:
    AIV: zero(dqWs, dkWs, dvWs); PipeBarrier; SyncAll

    for task in grid_stride(total_q_tasks, block_num):
        (b, h, qb) = decode_task(task)
        selected = filter_negative_out_of_range_and_dedupe(block_indices, mask_row), keep order

        load Q, dO, LSE
        for row in q_rows:
            D[row] = dot(dO[row], O[row])

        dQ_acc = 0
        for idx in 0..selected_count:       # last idx is flush
            if idx < selected_count:
                kvb = selected[idx]
                S   = MMAD(Q, K[kvb]^T)     # FP32 L0C
                dP  = MMAD(dO, V[kvb]^T)    # FP32 L0C
                P   = exp(scale*S - LSE)
                dS  = P * (dP - D)
                dV  = MMAD(P^T, dO)         # FP32 L0C
                atomic_add_fp32(dvWs[kvb], dV)
                dK  = MMAD(dS^T, Q)         # FP32 L0C
                atomic_add_fp32(dkWs[kvb], dK)
                dQ_acc += MMAD(dS, K[kvb])  # owner L0C

        write_fp32(dqWs, dQ_acc)            # L0C -> workspace

post:
    dQ_out = cast_rint(scale * dqWs)
    dK_out = cast_rint(scale * dkWs)
    dV_out = cast_rint(1.0 * dvWs)
```

五次矩阵乘必须落到 CATLASS Cube MMAD 数据路径；workspace 清零、D、P/dS、atomic 和 Post
scale/cast 的 staging 由 Vector/MTE 承担。标量代码只处理索引、循环和尾块。
[^bsag-catlass-kernel]

## 约束

- 官方 Arc35 与 `bsag-catlass` 的输入 ABI、workspace、核数和同步结论不能混写；引用时写明实现与提交。
- Arc35 固定源码支持 BSND/BNSD/TND；`bsag-catlass` 的冻结路径只覆盖 BNSD/TND。[^arc35-entry]
- 输入为 FP16/BF16，`head_dim=128`，`block_shape=[128,128]`，`Nq % Nkv == 0`。
- 项目路径的实现接受 `mask_heads` 为 1 或 `Nq`，但项目 API 契约与 36 例冻结证据只覆盖
  `mask_heads=1`；索引表允许负 padding、重复和非升序，过滤后保留输入顺序。
- 项目路径的 `cu_seqlens_q/k` 为 `[B+1]`、非降、首项 0、末项等于 packed token 数；vendor 基线
  使用去掉首项的累计值。
- R5 的 dK/dV atomic 目标是 FP32 workspace，Post 之后才写正式输出；不设置 `deterministic`
  模式，低位非确定性不视为该路径错误。
- R5 必须由主 kernel 内 AIV 清零 workspace，并由独立 Post 完成 scale/cast；host memset 或
  R3/R4 直出正式输出都不属于 R5 实现。
- 性能数字只适用于 `bsag-catlass@e3c13c0` 的 36 例、Ascend950PR、CANN 9.2.0-beta.2 实测范围。

## 失败表现

- 把官方 bool mask 当作物理 block 索引：数字 0 在 bool mask 中表示“不选”，在索引表中表示“选第 0 块”。
- 沿用官方 `[B, Nq, QBlocks, KVBlocks]` 轴序读取固定 kernel：非对称 mask 会整块错位；全 1 或对称 mask 会掩盖。
- 给官方/vendor 传入带前导 0 的 `actual_seq_lengths`：第一段被解释为长度 0，后续每段整体错位。
- 每行索引表有负值或重复时结果异常：先检查过滤/折叠逻辑，不能直接按槽位计算。
- dK/dV 只有最后一个 KV block 的结果：缺少 FP32 atomic，或主 kernel 的 workspace 清零阶段没有执行。
- dQ 只保留最后一个 selected block：owner L0C 没有在 task 内累加，或首块没有正确初始化。
- dQ/dK 成比例偏大/偏小：scale 作用位置错；dV 不应乘 scale。
- 空选择结果非 0 或重复 launch 被上一轮污染：主 kernel 清零/`SyncAll` 缺失，或 Post 未按
  R5 读取清零后的 workspace。
- D 整行偏差：dO/O 行对齐或 LSE 行映射错；D 是逐行点积，不应引入 `dO@O^T` MMAD。
- varlen 第二个 batch 起错位：项目任务前缀应使用每 batch 的 local q block 数，索引表行号仍使用全局 `qBlocksMax`。
- 小 shape 或 k50 大 shape 性能不足：先核对核数、kernel 内清零、FP32 atomic、Post 和基线版本，
  再调整 TileShape。

## 验证方法

先用 CPU/FP32 oracle 按有效 sparse tile 计算 `D`、P、dS，再比较 `dQ/dK/dV`。真实链路测试必须
使用同一次前向产生的 O/LSE；只给合成 O/LSE 时验证的是给定输入的反向契约。[^arc35-readme]

正确性矩阵至少覆盖：

- 官方 bool mask：非对称轴序、全选、单块、空行、不同 `Nq/Nkv`，并验证 README 与 kernel 轴序是否有漂移。
- 项目索引表：负 padding、越界值、重复、非升序、空选择行、`mask_heads=1` 与 `mask_heads=Nq`。
- ABI 转换：官方 bool mask 逐行非零位置转项目索引表；调用 vendor 时再把索引表展开为同 shape
  的 bool mask；项目 `[B+1]` 边界转 vendor 无前导 0 累计值。
- dtype x layout：FP16/BF16 x BNSD/TND；覆盖 1K/8K/16K、尾块和 varlen 多 batch。
- 输出：padded row 不写；空选择行由 kernel 清零 + Post 保持 0；dK/dV 跨 task 的 FP32 atomic
  累加完整；同一进程重复 launch 不残留上一轮结果。

性能验收使用固定 36 例（24 定长，其中 12 fixed + 12 tail；另 12 varlen），同设备、同 shape、
同 dtype/layout、同稀疏模式，
取每例 p50，并以对应基线逐例判定 `vendor / candidate >= 1.0x`。候选耗时为
`BsagMainKernel + BsagPostKernel` 的 device `Task Duration` 之和，包含 kernel 内清零和 Post，
不含 host API 时间。旧 `torch_npu` 与最新 aclnn 必须分开报告，不能用一套基线的通过数替代
另一套。[^bsag-catlass-benchmark][^bsag-catlass-aclnn]

[^arc35-readme]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/README.md> Arc35 Block Sparse Attention Grad README：公式、bool block mask、dtype/layout 与 TND 输入说明。
[^arc35-entry]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/block_sparse_attention_grad.cpp> Arc35 kernel entry：模板分发与执行路径。
[^arc35-tiling]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_host/arch35/block_sparse_attention_grad_tiling_arch35.cpp> Arc35 host tiling：`GetCoreNumAic()`、`SetBlockDim()`、workspace 与输入检查。
[^arc35-pipeline]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/block_sparse_attention_grad_arch35.h> Arc35 AIC/AIV 流水：D/sftg、五个跨核 flag、两次 SyncAll 与 post。
[^arc35-addr]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/addr_compute.h> Arc35 稀疏任务生成：bool mask 读取与线性 offset。
[^arc35-cube]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/cube_op_bsag_arch35.h> Arc35 Cube：五次 MMAD 与 L1/L0 数据路径。
[^arc35-vector]: <https://gitcode.com/cann/ops-transformer/blob/adc5fd30003da4c73bc478cf42c6f031b491b973/attention/block_sparse_attention_grad/op_kernel/arc35/vec_op_bsag_arch35.h> Arc35 Vector：D/sftg、P/dS、workspace 清零与 scale/cast。
[^bsa-forward]: <https://gitcode.com/cann/ops-transformer/blob/3f54e4334060281fad7b4b682393d22830928a33/attention/block_sparse_attention/README.md> Block Sparse Attention 前向 README：O/LSE 定义与 gathered-KV 语义。
[^bsag-catlass-readme]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/README.md> CATLASS R5 项目总览、最终结果、复现入口与源码校验值。
[^bsag-catlass-kernel]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/op_kernel/bsag_kernel.cpp> CATLASS R5 kernel：索引过滤、D 内联、AIV workspace 清零、dQ 写 FP32 workspace、dK/dV FP32 atomic、流水与 `Layout` 常量。
[^bsag-catlass-host]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/op_host/bsag_e2e.cpp> CATLASS host：22/26/28 核、`kUsePostKernel=true`、56-block Post、host 不 memset 与 TND 边界构造。
[^bsag-catlass-workload]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/code/test/workload.jsonl> 36 例冻结 workload：shape、dtype、稀疏模式与容差。
[^bsag-catlass-benchmark]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/benchmark_final.json> R5 旧 `torch_npu` 基线逐例 p50 与 36/36 汇总。
[^bsag-catlass-validation]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/validation_summary.json> R5 36 例正确性、108 个输出与误差汇总。
[^bsag-catlass-aclnn]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/reports/bsag_latest_aclnn_comparison.json> 最新 aclnn 基线的逐例对比与 14/36 汇总。
[^bsag-catlass-report]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/docs/performance_report.md> R5 最终性能与 R0-R5 迭代报告：kernel 清零、FP32 workspace + Post 的验收口径。
[^bsag-catlass-hits]: <https://gitcode.com/jiay0u/bsag-catlass/blob/e3c13c049616745a17d63ff1f5389ae33f449afa/docs/knowledge_hits.md> CATLASS 项目的知识库命中记录：固定知识库版本、BSAG 卡读取与采用位置。
