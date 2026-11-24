---
type: Optimization
title: 连续行逐行搬运改批量 DataCopyPad
description: 将连续行的逐行DataCopyPad改为一次调用，以blockCount=行数批量搬完整段。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/batch-contiguous-rows-datadcopypad.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：连续行逐行搬运改批量 DataCopyPad

> 单一优化点：当一个 kernel 的片外↔片上搬运以"逐行一次 DataCopyPad（blockCount=1）"方式发出，而这些行在全局内存里本就是连续排布时，把整 tile 的若干行合并成**一次** DataCopyPad（blockCount=行数）。每次 DMA 发射都有固定开销（队列分配/入队/出队/释放 + DMA setup），行数多时这部分累加成主导；批量后 DMA 调用数从 O(行数) 降到 O(tile 数)。

本策略适用于任何"对全局内存中连续排布的多行做片外↔片上搬运、且当前是逐行发出"的 kernel，与具体算子无关。

---

## 1. 原理

AscendC 的 `DataCopyPad`（带 `DataCopyParams`）支持 `blockCount` 参数一次搬多个块。当源（全局内存）的多行连续、每行 blockLen 字节，一次 `blockCount=行数` 的调用即可搬完整段；片上目的端每行自动 pad 到 32B，行步长 = ceil(blockLen/32)·32 字节 = 该 dtype 的自然 32B 对齐元素数。

逐行搬（blockCount=1 循环行数次）与批量搬（blockCount=行数 一次）搬的字节量相同，但**DMA 发射次数**差行数倍。每次 DMA 发射伴随队列 Alloc/EnQue/DeQue/Free 与一次 DMA setup 的固定开销；当每行有效数据很小（小 D）而行数巨大（大 N）时，单行搬的字节极少、固定开销占比极高，端到端时间被"行数 × 每次发射开销"主导，远超带宽时间。

批量搬把发射次数压到 tile 数（通常每核个两位数），让端到端时间回到带宽限制附近。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. `CopyIn`/`CopyOut` 用 `for (行) DataCopyPad(..., blockCount=1, ...)` 形态，或等价的逐行搬。
2. 这些行在全局内存里连续（行 r 起始于 r·D 元素），无跨步/索引打散。
3. 实测/profiling 显示：小 D 大 N 的 case，DMA 描述符数量 ≈ 行数；端到端时间 ≈ 带宽时间 + 一截与"行数 × 每次发射开销"成正比。
4. 片上对该 tile 后续做整 tile 批量向量计算（即搬入后不再逐行处理），逐行搬与批量算的粒度不匹配，搬入成为残余瓶颈。

不适用：行在全局内存非连续（带 stride/索引 gather），或每行数据本就很大（一行接近一次 DMA 的经济粒度），或行数本就很少。

## 3. 正确性红线

- **行步长一致**：批量搬的片上目的行步长 = ceil(D·sizeof(elem)/32)·32 字节 = dtype 自然 32B 对齐元素数（半精度 align(D,16)、fp32 align(D,8)）。后续向量算若按 `tensor[r·行步长]` 寻址，行步长必须与此一致——这是最易错点；若 kernel 内部用了更大的统一行步长，需确保两者相同或改回逐行搬。
- **源连续**：全局内存源必须是 `行数·D` 个元素连续（行 r 在 r·D），否则批量搬会读到错误数据。
- **尾部 tile**：总行数非整除时，尾部 tile 的 blockCount 取余数；批量搬同样支持任意 blockCount。
- **pad 行为**：`DataCopyPad` 默认把每行 pad 到 32B（padding 区内容不保证，通常为旧值/未定义）；若后续 reduce 按 mask 只读前 D 个元素，padding 无害；若后续按整行步长读全行，需确保 padding 不参与有效运算。
- **方向**：片外→片上（GM→UB）用带 `DataCopyPadParams` 的重载；片上→片外（UB→GM）的 `DataCopyPad` 目的端在全局内存，无需 pad 参数，按真实 D·行数 截断写回。
- **对齐**：源/目的起始地址须 32B 对齐（GlobalTensor/LocalTensor 基址天然满足）；blockLen 可非 32B 对齐（pad 补齐）。

## 4. 泛化条件

适用（任一）：
- 拷贝/归一化/elementwise 等 kernel，逐行搬连续行且后续整 tile 批量计算。
- 小 D 大 N 的 case 实测耗时 ≈ 带宽 + 与行数成正比的发射开销。

不适用（任一）：
- 行非连续（gather/strided），需逐行或带 stride 的搬。
- 行数据本已大、行数少，发射开销非瓶颈。
- kernel 后续是逐行处理，批量搬入不会带来粒度匹配收益（但仍正确，收益小）。

## 5. 实施步骤

1. 定位逐行 `DataCopyPad` 循环，确认源在全局内存连续、片上按 32B 对齐行步长落点。
2. 核验 kernel 内部使用的行步长 == `ceil(D·sizeof(elem)/32)·32/sizeof(elem)`（批量搬的落点）。若不一致，先统一行步长再批量。
3. 片外→片上：改为单次 `DataCopyPad(localTile, gmSrc[tileFirst·D], {blockLen=D·sizeof, blockCount=rows}, padParams)`。
4. 片上→片外：改为单次 `DataCopyPad(gmDst[tileFirst·D], localTile, {blockLen=D·sizeof, blockCount=rows})`。
5. 全量编译，精度全过（与改前逐比特一致，因仅改搬运粒度），多次取样性能。
6. 重点看小 D 大 N case 的"行数 × 发射开销"那截是否消失；若改善超噪声且精度过则采纳，否则回退。

## 6. LLM 前置问题

- `CopyIn`/`CopyOut` 是否逐行发出 DataCopyPad？这些行在全局内存是否连续？
- 片上 tile 的行步长是否等于 dtype 自然 32B 对齐元素数（与 DataCopyPad 每行 pad 落点一致）？这是批量搬正确性的关键。
- 小 D 大 N case 的端到端时间里，"行数 × 每次 DMA 发射开销"能否解释超带宽的那截？
- 尾部 tile（行数非整除）与片上→片外方向（无 pad 参数）是否处理正确？

## 7. 验收标准

- 编译通过。
- 精度：全部用例与改前逐比特一致（仅改搬运粒度，不改计算）。
- 性能：小 D 大 N case 墙钟多次取样稳定改善、超噪声；改善量近似等于"行数 × 每次发射开销"的消除量；其它 case 不退化。
- 若任一不满足则回退。

## 检索卡（短卡）

动作：将连续行的逐行DataCopyPad改为一次调用，以blockCount=行数批量搬完整段。
适用：拷贝、归一化或elementwise内核逐行搬运连续行，随后按整tile批量计算。
限制：源行须在全局内存连续，片上落点采用32B对齐行步长，且内部行步长必须一致。
范围：拷贝、归一化及elementwise内核的片外与片上搬运。
检索词：DataCopyPad、DataCopyParams、blockCount、连续行、32B对齐行步长
机会：全局内存中的连续行仍以blockCount=1逐行发出DataCopyPad。
