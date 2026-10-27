---
type: Optimization
title: 共享左矩阵的多右端合并（Multi-RHS Shared-Left Merge）
description: 多个线性求解共享同一左矩阵时，按列拼接右端做一次 [C,C]×[C,K+V] dot，FLOPs 不变而 dot 调用减半，规避 Ascend 上每个 dot 的固定搬运/同步开销。
tags: [task.optimization, topic.compute.composite, topic.implementation.memory_management]
status: draft
sources: []
created_at: '2026-10-23T00:00:00Z'
updated_at: '2026-10-23T00:00:00Z'
platforms: [a2]
---

# 共享左矩阵的多右端合并（Multi-RHS Shared-Left Merge）

## Summary

同一左矩阵乘多个右端时，按列拼接右端可合并为一次 `tl.dot`：
`M·[X|Y] = [M·X | M·Y]`。FLOPs 完全相同，但少一次 dot 的固定成本
（操作数 UB→L0、L0C→UB 回写、cube/vector 同步）——在 Ascend 上这部分
通常远大于矩阵本身的算力开销。

## Use When

- 多个求解/投影共享同一左矩阵，例如块内三角求解 `w = M·(βkq)`、`u = M·(βv)`，`M=(I+L)⁻¹`；
- `K+V` 是 2 的幂（Triton tile 维度要求；K=V=128 → 256 ✓）；不是 2 的幂时需 padding 或放弃合并；
- 单 dot 固定成本占主导（实测：独立 dot 0.09–0.35 µs、依赖链 ~1.45 µs）。

## Rewrite

```python
# 右端在 workspace 中连续排布：[C, K+V]，行 stride = K+V
rhs = tl.load(tl.make_block_ptr(base=wrhs + pid*C*(K+V), shape=(C, K+V),
                                strides=(K+V, 1), offsets=(0, 0),
                                block_shape=(C, K+V), order=(1, 0)))
res = tl.dot(rb, rhs)                 # [w | u]
tl.store(..., res)
# 消费者分别取前 K 列（w）与后 V 列（u），用 block_ptr 偏移即可
```

生产侧同样只需要两次列偏移 store：`gate` 把 `βkq` 写到 `[:, 0:K]`、`βv` 写到 `[:, K:K+V]`。

## Signals（探针）

- 求解段由 2 个 dot 组成却占显著时长（例：solve 3.07 ms，而 FLOPs 仅 ~1 GFLOP 级）；
- 消融：删除其中一个 dot 时长几乎线性下降 ⇒ 固定成本主导；
- 合并后逐位对拍应 `max|a−b| = 0`（每个输出元素仍是独立地对 C 求和）。

## Measured

`12_ChunkKdaFwd`（910B2C）：两次独立 `[C,C]×[C,K]` / `[C,C]×[C,V]` 的 solve kernel **3.07 ms**
→ 一次 `[C,C]×[C,K+V]` **0.78 ms**（终版 0.50 ms），整机 −1.86 ms；输出与拆分版逐位一致。

## Pitfalls

- 右端必须**物理连续**；分散在两个缓冲时合并前要先搬到一个缓冲（否则省下的 dot 成本被搬运吃掉）。
- `K+V` 非 2 的幂不能直接拼接；不要用 mask 伪造宽度（会引入额外向量开销）。
- 合并只改调用形态，不改数值；若两个右端需要不同的左矩阵（或不同精度模式），不适用。

## 相关

- [../../guides/constraints/kda_constraints.md](../../guides/constraints/kda_constraints.md)（L1.3）
- [../../guides/operator_playbooks/kda__chunk_kda_fwd.md](../../guides/operator_playbooks/kda__chunk_kda_fwd.md)
