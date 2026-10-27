---
type: Optimization
title: 守卫式零 Carry 快路径（Guarded Zero-Carry Fast Path）
description: 分块递推中当 chunk 间状态 carry 可被运行时上界证明可忽略时，把串行 scan 塌缩为逐块独立计算（o=Aqk@u），并用 Bmax/(1-gl_max) 守卫保证慢衰减输入自动回退精确实现。
tags: [task.optimization, topic.compute.composite, topic.parallelism, topic.precision]
status: draft
sources: []
created_at: '2026-10-23T00:00:00Z'
updated_at: '2026-10-23T00:00:00Z'
platforms: [a2]
---

# 守卫式零 Carry 快路径（Guarded Zero-Carry Fast Path）

## Summary

分块线性递推的块间状态扫描是 pure serial：`S' = gl⊙S + kgt@(u − w@S)`，输出
`o = qg@S + Aqk@(u − w@S)`。当进入每个 chunk 的状态 `S_c` 可忽略时，整段退化为
`v_new = u`、`o = Aqk@u`——**每 chunk 独立、完全并行**。本 pattern 用**运行时上界**
判断"何时可塌缩"，并保留精确 scan 作为回退，因此在目标分布上拿到并行收益、
在慢衰减输入上仍然正确。

## Use When

- 递推形如 `S_{c+1} = gl_c ⊙ S_c + B_c`，`gl_c = 2^{Σg/ln2}` 由门控给出；
- 目标输入分布下 gate 强衰减（`gl_max ≪ 1`），chunk 边界状态由**本块贡献**主导；
- scan kernel 是端到端大头且被证明是同步/搬运受限（simulator：cube `CUBE` 占比低、
  FLOWCTRL/MTE 占比高），继续压缩串行链无空间。

## Signals（探针）

1. **状态量级**：算 `B_c = kgt_c @ u_c`（与 `o` 共享 `u` 的额外 dot），取其最大绝对值 `Bmax`；
2. **衰减强度**：`gl_max = max(gl)`；
3. **上界**：由递推直接得 `|S_c| ≤ Bmax/(1−gl_max)`（几何级数；`gl_max<1`）；
4. **被丢项**：零 carry 时丢 `qg@S_c` 与 `Aqk@(w@S_c)`，量级 ∝ |S_c|。

实测（`12_ChunkKdaFwd`，910B2C）：`Bmax=2.05e-3`、`gl_max=1.48e-15` → 上界 2.05e-3；
40 个随机用例的快速路径输出与参考 `max_abs ≤ 5.4e-4`（官方容差 1.56e-2）。

## Rewrite

```python
# 快速路径 kernel（grid = nchunk，每 chunk 独立）
kgt = load(...); u = load(...); aqk = load(...)
b = tl.abs(tl.dot(kgt, u))                         # 守卫量（无 carry 状态贡献）
o = tl.dot(aqk, u)                                 # 零 carry 输出
store o
store 守卫量（见下）
```

**守卫量的低成本落盘**（关键工程点）：
- kernel 内 `tl.max(x, axis=…)` 在 2D dot 结果上会让 Triton-Ascend 编译器挂起（实测 >14 min）；
  全 2D 归约可编译但极慢（~6 µs/chunk）。
- 用**小轴求和**压缩：`tl.sum(tl.reshape(|B|, (K, V//4, 4)), axis=2)` → `[K,V/4]`，可编译且便宜；
  `Σ_4|B| ≥ max|B|`，是**保守 ≤4× 的上界**。
- host 侧一次归约 + 一次同步：`bmax, glmax = stack([wB.amax(), wgl.amax()]).tolist()`；
  `use_fast = bmax / max(1−glmax, 1e-30) < THRESH`（实测取 2e-2，等效真值阈值 5e-3）。

## Guard and fallback

- 启用条件：`use_fast and not has_init and not output_final_state`（有初始状态/要末状态时 carry 非零）。
- 否则运行**精确 scan**（始终保留同一份代码）。
- 快速路径 kernel 的 `o` 在回退时被丢弃（浪费 ~1 个 dot），可接受。

## Verification

- 目标用例：记录 `Bmax/gl_max/bound`，确认触发了快速路径；
- 多 case 精度：官方 verify 全过 + 与精确实现的逐位对拍（改搬运/拆分时 `max|a−b|=0`）；
- **回退路径**：构造慢衰减强输入（如 `g≈−5e-4`，`gl≈0.97`），确认守卫失败、精确 scan 运行，
  且与参考相对误差在 bf16 精度水平。

## Failure Modes / 边界

- **不要**用"经验阈值"替代 `Bmax/(1−gl_max)`：状态可能很大而 `gl` 很小（`S≈kgt@u` 与 gl 无关）。
- 输出量级远小于绝对容差时，快速路径是**绝对精度**近似（相对误差在小元素上可 O(1)）；
  报告/交付必须披露，并保留精确路径。
- 若后续要求 `output_final_state`，需在快速路径里补 `S_c` 的计算（当前直接回退）。

## 相关

- [../../guides/constraints/kda_constraints.md](../../guides/constraints/kda_constraints.md)
- [../../guides/operator_playbooks/kda__chunk_kda_fwd.md](../../guides/operator_playbooks/kda__chunk_kda_fwd.md)
- [../../runbooks/performance/chunk_kda_fwd_mfu.md](../../runbooks/performance/chunk_kda_fwd_mfu.md)
