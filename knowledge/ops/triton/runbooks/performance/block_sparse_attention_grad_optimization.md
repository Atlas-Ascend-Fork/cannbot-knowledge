---
type: Runbook
title: BlockSparseAttentionGrad 算子优化
description: BlockSparseAttentionGrad 的 Triton-Ascend 优化：在 device 侧转置块掩码并构建 kv 主序选择表，避免 strided gather；dk/dv 使用连续写回与 0 轴归约，tile 按 UB 和 L0C 容量独立选取
tags: [task.optimization, topic.attention, topic.implementation.masking, topic.tiling, topic.memory, topic.precision]
status: draft
sources: []
created_at: '2026-10-27T00:00:00Z'
updated_at: '2026-10-28T00:00:00Z'
verified:
- by: process:opencode-deepseek-flash-tt36
  at: '2026-10-21T00:00:00Z'
platforms: [a2]
---

# BlockSparseAttentionGrad 算子优化

> 类别约束见 [attention_writing_classification.md](../../guides/constraints/attention_writing_classification.md)，
> 全局约束见 [global_constraints.md](../../guides/constraints/global_constraints.md)。

## 任务特征

- BNSD 布局、MHA、D=128，输入 dO、O 和 softmax 统计量，输出 dQ、dK、dV
- 块掩码为 uint8，形状是 [B,N,ceilQ,ceilKV]。实测 bx 为 16、32、48、64、128，by 为 16、32、64、80、128，两方向可以不同
- 评测共 17 case，覆盖 causal、滑窗、bigbird、随机和稠密掩码，包含非整除边界

## 优化 1：在 device 侧构建选择表

host 只做 shape、alloc 和 view。掩码转置与前缀计数都在 device 侧完成，不要物化 token 级稠密 mask 再传入。

类别约束默认使用无 dot 的建表 kernel。下面的 2D-dot 是 Ascend 910B3、triton_ascend 3.6.0 和 CANN 9.1.0 下的实测例外，仅对应本 17 case 的选择表，前缀矩阵边长 T 不超过 128，不作为类别通用替代规则。

```python
# ❌ host 侧物化 token 级稠密 mask
token_mask = block_mask.repeat_interleave(bx, 2).repeat_interleave(by, 3)

# 本卡受限场景：比较矩阵配合一次 cube matmul 计算前缀位置
U = (cc[:, None] < cc[None, :]).to(tl.float16)
pos = tl.dot(keep.to(tl.float16), U).to(tl.int32)
tl.store(sel_ptr + row * PAD + pos, col_ids, mask=keep)
```

对照使用相同输入并产生相同选择表：tl.cumsum 为 0.13ms，3D broadcast-sum 为 0.17ms，2D-dot 前缀为 0.095ms。终版建表 kernel 约 78µs，其中约 30µs 是小 dot 的 cube 固定时延。表规模或编译环境变化后需要重新比较，tl.atomic_add 建表在该后端直接报 aivec error，不使用。

掩码转置仍使用无 dot、无 atomic 的 kernel。device 侧建表、host 不物化稠密 mask、选择表与 kernel 粒度对齐等类别约束不变，program 粒度对齐掩码块粒度，不逐 token 发 program。

## 优化 2：kv 主序选择表避开 strided 列 gather

```python
# ❌ ub overflow 401KB，需要 3211264 bits，只有 1572864 bits
keep = tl.load(bmask_ptr + (bnidx * NQBLK + qts) * NKBLK + kb, mask=qts < NQB, other=0)
# 触发条件：gather 长度达到 128，或 gather 外面套了任意外层循环

# ✅ 先用 device 侧 kernel 转置掩码，之后只读连续行
v = tl.load(bmask_ptr + base + j[None, :] * NKBLK + i[:, None], mask=mk, other=0)
tl.store(bmt_ptr + pid * NKBLK * NQBLK + i[:, None] * NQBLK + j[None, :], v, mask=mk)
```

同样的紧致化流程，q 主序的连续 load 在 128 长度加 4 段循环下都能编过，只有 strided gather 爆 UB。转置是 uint8 小 tile 一次完成，实测结果与 mask.permute 逐位相等。

sel_k 的列是 q tile 粒度，转置掩码的列是掩码块粒度。bx 大于 BMK 时必须做映射，否则 dk/dv 全错：

```python
mqs = qts // (bx // BMK)
```

## 优化 3：连续写回并沿 0 轴归约

- dk/dv 写回走连续布局。实测连续写为 5.97ms，gather-store 为 107.6ms，atomic_add 为 156.2ms
- 归约沿 0 轴逐 lane 累加，快轴归约有 8~10 倍惩罚

## 优化 4：dk/dv 独立选择 tile

- BMK 必须整除 bx，从 64、48、32、16 中依次选择首个满足条件的值。实测 bx=48 时取 48，bx=128 时取 64；没有候选值时不套用本规则，需要重新做编译和正确性验证，不能直接使用 min(bx, 64)
- BT 取整除 by 的最大值，by 不超过 32 时取 by，否则依次试 32、48、16
- 同一套 BM=BN=64、BT=64 在 dq 能编过，在 dkdv 需要 224KB，直接越界
- L0C 住 cube 累加器，910B 为 128KB。两个 [128,128] fp32 累加器会触发 Cc overflow，dk/dv 双输出的 BT=128 不可用，需要降到 64 以下
- tl.dot 三参形态能把累加器放上 cube 复用，但双输出仍各占一个累加器，降 BT 才是生效的修复

## 精度要点

- q/k/v/dout 用原生 dtype 进 tl.dot，累加器用 fp32，不要把操作数升 fp32
- p 和 ds 是真 fp32 量，喂 dot 前做 hi+lo 二段拆分
- 边界列用 tl.where(valid, s, -3e38)，越界行地址先钳制再 mask

## 正确性验收

- 验证入口为 `.agents/skills/triton-op-verifier/scripts/verify.py --op_name BlockSparseAttentionGrad --verify_dir output/opt2_iter_2/verify`，运行环境为 Ascend 910B3、CANN 9.1.0、triton_ascend 3.6.0、torch 2.10.0+cpu、torch_npu 2.10.0.post7
- 本次 verify 使用 eco_open_source 判据，dQ、dK、dV 均要求 matched_ratio 不低于 0.99，并同时满足以下误差限制：

| dtype | atol 与 rtol | 逐元素误差上限 |
|---|---|---|
| fp16 | 2^-9，约 1.953e-3 | max(0.1, 32·ULP) |
| bf16 | 2^-6，约 1.562e-2 | max(1.0, 32·ULP) |

- 最终 `verify_result.json` 记录 17/17 通过。`cmp_case.py` 只用于 CANN 与 Triton 的核时对比，不做精度判定，正确性结论只来自上述 verify

## 调试方法

- aicore timeout 用消融定位，逐个禁用 kernel 跑问题 case，禁掉谁不 hang 谁就是元凶
- 输出 buffer 用 torch.empty 且没被 kernel 全覆盖写时，精度失败先查覆盖率再查数值
- tile 参数做成环境变量可调，扫描时触发 hang 的组合自动回退默认值

### 总结

1. 在 device 侧转置掩码并构建 kv 主序选择表，不用 strided gather
2. dk/dv 连续写回，归约沿 0 轴
3. dq 与 dk/dv 分别按 UB 和 L0C 容量选择 tile

## 实测观测

- **现象**：初版正确性通过，但性能远低于竞品
- **负载**：BNSD/MHA/D=128 块稀疏反向，17 case
- **解决层**：tiling + memory
- **严重度**：high
- **置信度**：multi_run
- **复现次数**：优化 10 轮，多轮复测
- **信号**：
  - 全 17 case 的 Triton 总核时从 5934.7ms 降到 21.67ms，提升 273.8 倍
  - 对竞品 geomean 0.9283，最低 0.6815，17/17 超过 0.6；4 个 case 反超，最高 3.41 倍
- **实测最优延迟**：全 17 case 总核时 21.67ms
- **证据**：910B3 实测，triton_ascend 3.6.0 + CANN 9.1.0；竞品为 ops-transformer 的 aclnnBlockSparseAttentionGrad，逐 case 独立进程加 profiler kernel_details 核时口径；官方 verify 17/17 通过
