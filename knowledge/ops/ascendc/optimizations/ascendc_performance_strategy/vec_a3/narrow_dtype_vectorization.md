---
type: Optimization
title: 窄 dtype 向量化（int64 索引/数据先 Cast 到 int32，用 128-lane 向量链）
description: 将可无损窄化的int64热点先Cast为int32，再用int32向量链处理
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-narrow-dtype-vectorization.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：窄 dtype 向量化（int64 索引/数据先 Cast 到 int32，用 128-lane 向量链）

> 单一优化点：当热点数据是 int64（如 64 位索引、int64 中间量）时，把能窄化的部分先 `Cast` 到 int32，再用 128-lane 的 int32 向量链处理（过滤/比较/算地址），避免 64 位向量宽度减半或无向量指令可用（A2 的 Compare/GatherMask 等仅支持 int32/16）。窄化只降宽度、不降精度语义（范围确认后），向量化收益 ~2-128×。

本策略适用于任何"int64 出现在向量可处理的位置、但被当标量/窄向量处理"的 kernel（64 位索引的 scatter/gather、int64 中间累加、embedding 索引等），与具体算子无关。

---

## 1. 原理

A2 等芯片上，向量指令的 lane 宽度与 dtype 相关：int32 向量 128 lanes/cycle，int64 向量要么宽度减半、要么该 op 根本不支持（如 `Compare`/`GatherMask` 常见只支持 int32/16）。若热点是 int64 索引的"判命中/算地址/压缩"链，保持 64 位会让向量化不可用或减半。

`Cast(indexInt, indexRaw, CAST_NONE)` 把 int64 索引安全窄化到 int32（数据范围内无损），之后整条向量链（负索引修正、`rel==clamp` 范围比较、GatherMask 压缩、`Muls/Add` 算偏移）都跑 128-lane int32——lane 数翻倍、且解锁 Compare/GatherMask 等原本对 int64 不可用的向量原语。

**前提**：窄化前确认 int64 值在 int32 范围内（`|idx| ≤ 2^31`），且**最终的目标/值仍按 int64 计算**（窄化只用于判命中/算地址的中间链；地址乘 `inner` 若溢出 int32 则用 int32 中间 + int64 最终，或分步）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 热点是 int64 索引的逐元素判命中/算地址循环，且 `GetValue` 返回 int64（标量处理）。
2. 想向量化（Compare/GatherMask/算术）但 int64 无对应向量 op，或向量宽度减半。
3. profiling：SCALAR pipe 高、向量管空闲，且数据里 int64 是主 dtype。
4. 索引取值范围远小于 int64 表示范围（`0..axisSize-1` 或 `-axisSize..axisSize-1`），窄化无损。

不适用：int64 值域超 int32 且无法分步窄化（如数据本身是 int64 且需 64 位精确算术）；无向量化需求的小循环；窄化反而引入额外 Cast/同步开销的场景（先确认向量链收益 > Cast 成本）。

## 3. 正确性红线

- **窄化无损**：Cast 前确认值在 int32 范围内（索引 `∈ [-axisSize, axisSize)` 通常满足）；数据窄化（如 int64 值）只用于判命中/比较，**最终写回/累加仍用原 int64 值**。
- **乘 inner 溢出**：`rel × inner` 或 `target = idx×inner + i` 若超 int32，用 int32 中间 + int64 最终，或 `Muls` 只在 `inner` 较小处用、最终偏移转 int64——禁止溢出截断。
- **Cast 后的同步**：`Cast`（V 管）产出被标量/后续向量读前须同步（V→S / V→V）；int64→int32 Cast 是逐元素，padding lane 也要毒化/窄化一致。
- **与 direct 指针/压缩配合**：窄化后的 int32 命中地址用于 direct 指针解引用时，`rel × localStride + col` 的中间溢出同样按 int32/int64 分步。
- **host 分派变体的值域证明**：单字 int32 路径须 `|x| < 2^31` 可证（INT32_MIN 溢出由用例规避）；UB 预算 scratch+队列 ≤ 标称 UB 的 95%（贴满会分配失败产生不确定行为）。

## 4. 泛化条件

适用（任一）：
- int64 索引/中间量占据热点，向量原语（Compare/GatherMask）对 int64 不可用或减半；
- 值域确认可无损窄化到 int32；
- 已有向量链（过滤/压缩/算偏移）可整体跑 int32；
- 混合位宽输入的逐元素整型算子：实现把全部 dtype 统一 widen 到 64 位（双字谓词链）浪费小位宽值域——host 按 dtype 分派 kernel 路径，值域可证 `|x| < 2^31` 的 dtype（int8/uint8/int32）走单字 int32 路径，仅 int64 走双字路径；单字路径红利：非负域内算术右移=逻辑右移（免进位修正）、有符号 Min/Max 可用、条件选择用 `Sel(m,a,b)=b+m*(a-b)`；迭代/循环上界按 dtype 位宽收紧（`bitlen(u)+bitlen(v)` 的函数，非全局常数）。

不适用（任一）：
- int64 值域超 int32 且无法分步；
- 无向量化需求的少量标量访问；
- 窄化 Cast 的同步/拷贝开销大于向量化收益（小循环）。

## 5. 实施步骤

1. 确认热点是 int64 且值域可无损窄化（`0..axisSize` 或 `±axisSize`）。
2. 把 int64 索引/中间量 `Cast` 到 int32 buffer（`Cast(dst32, src64, CAST_NONE)`）。
3. 判命中/算地址/压缩链全部改跑 int32 向量（配合 33 的过滤 + GatherMask）。
4. 最终目标/写回仍用 int64（窄化只用于中间链）；溢出风险点分步。
5. host 按 dtype 分派变体：tiling 加 mode/maxIter 字段；int8/uint8 用一次 host `cast to(int32)`（kernel 内 widen 的 interleave 难题使其不可行），abs 移入 kernel；仅 int64 走双字路径。
6. 全量编译、精度全过（含边界值、负索引、padding）、多次取样性能。

## 6. LLM 前置问题

- int64 值域是否保证在 int32 内？窄化只用于中间链、写回仍 int64 吗？
- `idx×inner + i` 的中间偏移会否在 int32 溢出？溢出点是否分步？
- Cast 产出与后续读之间是否补了 V→S/V→V 同步？

## 7. 验收标准

- 精度：全量用例通过（含 int64 边界值、负索引、溢出分步路径）。
- 性能：int64 热点改 int32 向量后 lane 数翻倍 + 解锁 Compare/GatherMask（scatter 案例 int64 索引 case3/5/18 均受益，配合 32/33 达 150~1000×）；host 按 dtype 分派变体：int8/uint8/int32 case 30-80×（轮内 geo 0.027→0.580）。
- 结构：int64 向量链只用于判命中/算地址，最终写回保持 64 位。

## 检索卡（短卡）

动作：将可无损窄化的int64热点先Cast为int32，再用int32向量链处理
适用：可无损窄化到int32；或int64索引/中间量为热点且向量原语不可用/减半；仍须满足窄化红线。
限制：Cast前必须确认所有值均在int32范围内
范围：int64索引、地址计算及可窄化中间量热点
检索词：int64、int32、Cast、128 lanes、Compare、GatherMask、索引buffer
机会：int64索引以GetValue标量执行逐元素命中判断或地址计算，阻碍Compare/GatherMask向量化
代价：int64路径可能向量宽度减半或缺少对应原语
