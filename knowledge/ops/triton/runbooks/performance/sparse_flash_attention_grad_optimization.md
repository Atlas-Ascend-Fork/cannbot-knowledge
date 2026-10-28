---
type: Runbook
title: SparseFlashAttentionGrad 算子优化
description: SparseFlashAttentionGrad 的 Triton-Ascend 优化：先用微基准区分 gather 带宽与 dot 形状瓶颈，再用重数矩阵把梯度展开为大 GEMM；中间量按连续布局存放，tile 兼顾 L0C 容量与核间并行
tags: [task.optimization, topic.attention, topic.implementation.masking, topic.tiling, topic.memory, topic.precision]
status: draft
sources: []
created_at: '2026-10-27T00:00:00Z'
updated_at: '2026-10-28T00:00:00Z'
verified:
- by: process:opencode-deepseek-flash-tt36
  at: '2026-10-22T00:00:00Z'
platforms: [a2]
---

# SparseFlashAttentionGrad 算子优化

> 类别约束见 [attention_writing_classification.md](../../guides/constraints/attention_writing_classification.md)，
> 全局约束见 [global_constraints.md](../../guides/constraints/global_constraints.md)。

## 任务特征

- BSND 布局、MQA，N2=1、D=512，输入 dO、O 和 softmax 统计量，输出 dQ、dK、dV
- 每个 q token 带 K 个选中索引，K 从 1024 到 8192
- 评测共 18 case，K 分四档，S1 与 S2 可不等长，覆盖 fp16 与 bf16

## 优化 1：先用微基准定位瓶颈

旧架构按 N1 维铺小 dot，一度认定瓶颈是 gather 带宽。微基准直接证伪：

- 裸 gather 452~555 GB/s，纯连续读 1538 GB/s，而 prep kernel 有效带宽只有 46 GB/s
- 裸 matmul 128×128×64 达到 109 TFLOPS，而 N1=4 的 prep 只有 0.28 TFLOPS

瓶颈是小 N1 的 dot 形状喂不饱 cube，不是访存。先量出硬件能力和当前 kernel 吞吐的数量级差，再决定是否重写算法。

## 优化 2：dense-k 重构，梯度全部大 GEMM 化

选择结构和重数矩阵都在 device 侧构建，host 只做 shape、alloc 和 view。把每个 q token 组的选中集合在稠密 k 域展开，显式计算重数矩阵 cnt[bt, kk]：

- 同一个 kk 被多个 j 选中时，它的 s、p、dp、ds 完全相同，所以 Σ_{idx=kk} ds = cnt[kk] · ds_dense[kk]
- dq、dk、dv 全部变成 M、N、K 不小于 64 的大 GEMM。低密度的稠密化浪费最多 8 倍，被 GEMM 约 400 倍的效率差覆盖
- 中间量 R 按 [b][k-tile][m][j] 分块，qT/doT 按 [b][m/BKM][d][j] 分块，让 dk 的两个操作数都连续，dk 从 20~55ms 降到 2.5~6.5ms

program 粒度对齐 q token 组粒度，不要逐 token 发 program。

## 优化 3：连续写回并沿 0 轴归约

- dk/dv 写回走连续布局。实测连续写为 5.97ms，gather-store 为 107.6ms，atomic_add 为 156.2ms
- 归约沿 0 轴逐 lane 累加，快轴归约有 8~10 倍惩罚

## 优化 4：tile 兼顾 L0C 容量与并行度

- dk/dv 沿 D 每多切一刀就要把 R 和 qT 重读一遍。ND 取最小切分，使 fp32 累加 tile 不超 64KB，且 program 数不少于核数
- bk 在 MM 不超 128 时取 128。case11 实测 bk 从 64 升到 128、ND 从 8 降到 4，总时间从 8.64ms 降到 6.73ms
- 搬运型 kernel 的 program 数按两倍核数起步。同一 128MB copy kernel，20 个 program 实测 1.18 TB/s，40 个为 2.29 TB/s；cube 密集 kernel 没有这项收益

## 精度要点

- q/k/v/dout 用原生 dtype 进 tl.dot，累加器用 fp32，不要把操作数升 fp32
- cnt 用 uint8 会在 mode3 溢出，改用 int16
- 转置 kernel 的末块必须补 mask，避免越界
- qT 分块与 dk 的 BKM 必须对齐，强制 BKTQ 不超 BKM，且 BKM 整除 BKT
- offs_m 整除 N1 在 N1=32 会被后端错编译，该形状走展开布局

## 正确性验收

- 验证入口为 `.agents/skills/triton-op-verifier/scripts/verify.py --op_name SparseFlashAttentionGrad --verify_dir output/opt4_iter_1/verify`，运行环境为 Ascend 910B3、CANN 9.1.0、triton_ascend 3.6.0、torch 2.10.0+cpu、torch_npu 2.10.0.post7
- 本次 verify 使用 eco_open_source 判据，dQ、dK、dV 均要求 matched_ratio 不低于 0.99，并同时满足以下误差限制：

| dtype | atol 与 rtol | 逐元素误差上限 |
|---|---|---|
| fp16 | 2^-9，约 1.953e-3 | max(0.1, 32·ULP) |
| bf16 | 2^-6，约 1.562e-2 | max(1.0, 32·ULP) |

- 最终 `verify_result.json` 记录 18/18 通过。性能脚本只做核时对比；`cmp_opt/bench_case.py` 使用已验证实现的缓存 golden 和 eco_limits 做快速回归，不能替代从参考实现重新生成 golden 的完整 verify

## 调试方法

- aicore timeout 用消融定位，逐个禁用 kernel 跑问题 case，禁掉谁不 hang 谁就是元凶
- 输出 buffer 用 torch.empty 且没被 kernel 全覆盖写时，精度失败先查覆盖率再查数值
- tile 参数做成环境变量可调，扫描时触发 hang 的组合自动回退默认值

### 总结

1. 先用微基准区分访存瓶颈与算力瓶颈，本算子的瓶颈是 dot 形状
2. 用重数矩阵把稀疏梯度展开为大 GEMM，中间量按消费顺序连续存放
3. 写回连续化，归约沿 0 轴，tile 同时满足 L0C 容量与核间并行要求

## 实测观测

- **现象**：初版正确性通过，但性能远低于竞品
- **负载**：BSND/MQA/D=512 topK 索引反向，18 case
- **解决层**：tiling + memory + 算法重构
- **严重度**：high
- **置信度**：multi_run
- **复现次数**：优化 4 轮，多轮复测
- **信号**：
  - geomean 轨迹为 0.2432 → 0.3493 → 2.1549 → 2.5626 → 2.6177
  - 全 18 case 总核时从 6764.3ms 降到 199.5ms，提升 33.9 倍
  - 18/18 超过 0.6，最低 case11 为 0.7424，最高 case13 为 6.96 倍
- **实测最优延迟**：全 18 case 总核时 199.5ms
- **证据**：910B3 实测，triton_ascend 3.6.0 + CANN 9.1.0；竞品为 ops-transformer 的 npu_sparse_flash_attention_grad，逐 case 独立进程加 profiler kernel_details 核时口径；官方 verify 18/18 通过
