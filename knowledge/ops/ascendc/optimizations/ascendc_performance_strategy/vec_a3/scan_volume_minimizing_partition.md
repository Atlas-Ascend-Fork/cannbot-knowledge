---
type: Optimization
title: 扫描体积最小化切分（条带切分，按 (outer×inner) 切分减少每核扫描量）
description: 将输出扁平字节分片且各子块重扫全输入，改为按 outer×inner 条带切分。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-scan-volume-minimizing-partition.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：扫描体积最小化切分（条带切分，按 (outer×inner) 切分减少每核扫描量）

> 单一优化点：把"按输出扁平字节区间切分 + 子块重扫全部输入"改为"按 **(outer × inner) 条带切分**"，使每个 task 只拥有输出的一列 inner 切片、只扫描自己切片的输入，把总扫描量从 `numSubBlocks × 全量输入` 降到 `numSegments × 切片输入`。这是"扫描全部输入找命中"型算子的**结构性**加速，远超任何常数级微优化。

本策略适用于任何"扫描全部/大部分输入、按索引匹配后才做写入"的 kernel（scatter / gather / embedding / index_select / segment_sum / unique 等），与具体算子无关。

---

## 1. 原理

**问题形态**：按输出 y 的扁平字节区间切核 + 子块（`SUB_TILE_BYTES`，如 128KB）时，输出被切成很多子块；每个子块要扫描**全部**输入来找"target 落在本子块"的条目（因为扁平子块横跨所有 inner 列，任何一列都可能命中）。总扫描量 = `numSubBlocks × 全量输入`。

对 1G 元素、region/子块 ≈ 44 的 shape：44 子块 × 24 核 × 33M 输入 ≈ **350 亿次 lane 扫描**，即使每 lane 只有几个 cycle 也到秒级。

**条带切分**：task 空间取 `outerSize × innerTiles`，每个 task 拥有 `x[outer][axis全部][innerStart:innerStart+innerTile]` 这条竖直带（各 task 写区互斥，单写者不破坏）。扫描输入时，每个 task 只读 `updates[outer][updateAxis全部][自己的 inner 切片]` = `1/innerTiles` 的输入；axis 方向按段装入 UB（`axisSegmentRows × innerTile` 塞进 UB 预算）。总扫描量 = `numSegments × 全量输入 / innerTiles × innerTiles`（跨 task）= `numSegments × 全量输入`，其中 `numSegments = ceil(dataAxis / segRows)`，而扁平方案 `numSubBlocks = ceil(outputBytes / (coreNum × subBlockBytes))`——对 inner 大的 shape，`numSegments ≪ numSubBlocks`（scatter 案例 case10：6129× 差距；case6：1906×）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 主循环"按输出字节区间分核 + 子块"，子块内**重扫全部输入**找命中；`总扫描 = numSubBlocks × 全量输入`。
2. 大 shape 的 `outputBytes ≫ UB`，子块数 `numSubBlocks` 大（数十~上千），每子块重复扫输入 → profiling 呈现纯 SCALAR/MTE 双高、加速比随 shape 变大急剧恶化（`speedup` 随输入规模近线性塌陷）。
3. 输入含"索引/命中"语义（`out[idx[i]]`、`y.scatter`、`x[idx[i],:]`），扫描量与"实际命中数"严重不成比例（扫描 33M、命中 1.4M）。
4. 用 `scan_volume_model.py` 算出扁平切分扫描乘子 >10×（且远高于条带切分）。

不适用：输出本身能整个装进 UB（无子块乘子）的小 shape；无索引匹配、纯连续搬运算子。

## 3. 正确性红线

- **单写者必须保持**：切分必须让每个 task 的输出写区互斥（`outer × innerTile` 条带天然互斥），否则多核写竞争丢写。写一致性通过 **UB 中转（MTE3 写回）** 保证——换切分不改写回方式，不要因"换切分会写竞争"而放弃重切分。
- **reduce 语义不破坏**：同一 target 的多次更新若跨 task 会破坏累加/后写覆盖。条带切分保证同一 (outer, inner) 列的所有 axis 更新都在同一 task 内按序处理；跨 axis 段的重复扫描须保证"后写/累加顺序"与该段只处理落入本段范围的 target 一致（段内以 `target ∈ [segmentStart, segmentStart+segmentRows)` 为最终裁决）。
- **innerTile 与 UB 预算**：`innerTile` 取 `ceil(inner / ceil(core/outer))`，并确保 `axisSegmentRows × innerTile × elemBytes ≤ 0.7 × UB`；溢出则减小 `axisSegmentRows`（多段）或 `innerTile`（多 task），二者按"估算同步次数"联合搜索（参考 07）。
- **inner==1 退化**：inner 很小时条带退化为按 outer 切分，收益仅剩向量化/常数优化，不要指望扫描乘子收益（scatter 案例 inner==1 case 仅 ~5×，inner>1 case 100~6000×）。

## 4. 泛化条件

适用（任一）：
- 输出 `outputBytes ≫ UB`，当前扁平切分产生大量子块、每子块重扫全部输入；
- 输入含索引/命中语义，且扫描量与命中量严重不成比例；
- `scan_volume_model.py` 扁平乘子 >10×。

不适用（任一）：
- 输出整体可装 UB（无子块乘子）；
- 无索引匹配的连续/规则搬运或纯 elementwise；
- inner==1 且 outer 小的退化场景（收益有限）。

## 5. 实施步骤

1. 用 `scan_volume_model.py` 对每个 shape 算扁平 vs 条带扫描乘子，确认 >10× 的 shape 集。
2. 把 task 空间从"输出扁平字节区间"改为 `outerSize × innerTiles`（每 task = (outer, innerTile 组)），保证写区互斥。
3. 每个 task 内按 `axisSegmentRows` 分 axis 段，段装入 UB（`innerTile` 与 `axisSegmentRows` 按 UB 预算 + 同步次数联合搜索）。
4. 每段内批量搬入自己 inner 切片的索引/输入（DataCopyPad 批拷），向量化过滤出命中（配合 33），标量只处理命中。
5. 处理 inner==1 退化路径（保留原向量化/常数优化）。
6. 全量编译、精度全过、多次取样性能，超噪声且精度过则采纳。

## 6. LLM 前置问题

- 当前切分轴是什么？每核/每子块扫描的输入量是"全量"还是"切片"？用 `scan_volume_model.py` 量化过吗？
- 输出能否按 (outer×inner) 切成互斥条带？换切分后写一致性是否仍由 UB 中转保证？
- `innerTile` 与 `axisSegmentRows` 是否按 UB 预算 + 同步次数联合搜索过？

## 7. 验收标准

- 精度：全量用例通过（与改前一致口径）。
- 性能：`scan_volume_model.py` 乘子 >10× 的 shape 提速显著（scatter 案例 inner>1 case 实测 100~6000×），全量不退化。
- 结构：主循环不再"子块 × 全量扫描"，改为"task 条带 × 切片扫描 + 段内批处理"。

## 检索卡（短卡）

动作：将输出扁平字节分片且各子块重扫全输入，改为按 outer×inner 条带切分。
适用：输出远大于 UB、扁平切分产生大量重扫子块，或索引命中量远小于扫描量。
限制：每个 task 的输出写区必须互斥，保持单写者。
范围：按输出 y 分核并扫描输入找命中的路径。
检索词：扫描体积、outer×inner 条带、扁平字节区间、子块重扫、单写者
机会：子块各自重扫全部输入，总扫描量等于子块数乘全量输入。
