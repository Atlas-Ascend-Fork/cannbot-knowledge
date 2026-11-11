---
type: Optimization
title: "X175: 把 kv_end 相同的连续 q-block 合进一个 ring（n2_mg 合并）"
description: "当任务映射使同一 KV head 的连续 q-block 共享相同 kv_end 时，可把多个 q-block 合成一个 ring group，用一次 ring 填/排空覆盖多个 block，摊薄 PRELAUNCH/FIX/心跳与 task 边界成本。只对连续子块 kv_end 全等成立；flag id 与 ws_o slab 数随 group 大小变化，必须 host/kernel 同步修改。"
tags:
  - task.optimization
  - topic.attention
  - topic.parallelism
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p160_n2_mg_merge
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p160_n2_mg_merge.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P160.yaml
    role: constraint
created_at: "2026-11-02T16:31:31Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X175: 把 kv_end 相同的连续 q-block 合进一个 ring

> 已晋升为 [P160](../cards/p160_n2_mg_merge.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
CV 环 attention 的 ring 每个合并 group 有 `PRELAUNCH` 次只做 C1、`PRELAUNCH` 次只做 C2 的填/排空；当每个 q-block 的平均迭代数较少时，边界气泡占比可观。若任务映射使同一 KV head 的连续 q-block 共享相同的 `kv_end`，可以把多个 q-block 合成一个 ring group：

- 一个连续 ring 覆盖多个 q-block；
- ring 填/排空（PRELAUNCH/FIX/心跳）与 task 边界成本被多个 block 分摊；
- 每个子块保留独立的 softmax 状态；
- 每个非末子块在 ring 中段 FIX 到自己的 ws_o slab，用 flag + 顺序 FIX_M 信用保证结果正确。

## 适用场景
- **连续子块的 `kv_end` 必须全等**。若不等，ring 的迭代边界无法共用，合并不成立。
- 任务序应让连续 task 对应同一 KV head 的 q-block（例如 s_blk 最快、g 次之），才能保证"连续 N 个 task 的 kv_end 全等"。
- flag id 预算与 ws_o slab 数随 group 大小变化；host 与 kernel 必须同步修改，不能只改一侧常量。

## 实现要点
1. host 侧增加 `MGROUP_MAX_HOST`，并在 ChooseMGroup 时校验 N 个子块的 `kv_end` 全等；不满足时退回 MGROUP=2/1。
2. kernel 侧 `MGROUP_MAX` 与 `tot_end = Σ sb_kvend[k]` 同步；每个子块独立 softmax 状态（UB 额外占用按 group 线性增长）。
3. 每个非末子块在 ring 中段 FIX 到自己的 ws_o slab；flag 与 FIX_M 信用按子块顺序配平。
4. 收益很小时，在共享/噪声较大的主机上很难单次判定；必须用同场交替 A/B、正反序至少两轮。
5. 若 MGROUP 增大后 UB 或 ws_o 超预算，先减少 group 大小，不要压缩每个子块的 softmax 状态。

## 边界与失效条件
- 只对连续子块 kv_end 全等成立；动态 shape 下要在运行期校验，不能只看 host 静态信息。
- flag id 与 ws_o slab 数随 MGROUP 变化；host/kernel 不同步会导致静默错值或死锁。
- 收益通常小于几个百分点，必须用配对 A/B 排除噪声。

## 验证方法
- 逐 bit 输出对比 + 全量精度。
- 同设备 A/B（至少 2 轮，正反序）；报告噪声带。
- 覆盖 kv_end 全等/不等、group 边界、尾块非整除。

## 关联
- 与 [X140](disc_x140.md)（M 方向合批）和 [X157](disc_x157.md)（0x2 信用批量化）同属"减少 task/ring 边界固定成本"的路线。
- 与 [X127](disc_x127.md)（RING/PRELAUNCH）共享 ring 深度与填/排空分析。
