---
type: Runbook
title: "P160 Playbook: 把 kv_end 相同的连续 q-block 合进一个 ring（n2_mg 合并） 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x175.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.parallelism
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x175.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p160_n2_mg_merge.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P160.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P160
---
# P160 Playbook: 把 kv_end 相同的连续 q-block 合进一个 ring（n2_mg 合并） 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x175.md](../../optimizations/evolution_strategies/discovered/disc_x175.md)。

## Step 1: 取证

```bash
grep -nE "MGROUP|kv_end|ring" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
CV 环 attention 的 ring 每个合并 group 有 `PRELAUNCH` 次只做 C1、`PRELAUNCH` 次只做 C2 的填/排空；当每个 q-block 的平均迭代数较少时，边界气泡占比可观。若任务映射使同一 KV head 的连续 q-block 共享相同的 `kv_end`，可以把多个 q-block 合成一个 ring group：

- 一个连续 ring 覆盖多个 q-block；
- ring 填/排空（PRELAUNCH/FIX/心跳）与 task 边界成本被多个 block 分摊；
- 每个子块保留独立的 softmax 状态；
- 每个非末子块在 ring 中段 FIX 到自己的 ws_o slab，用 flag + 顺序 FIX_M 信用保证结果正确。

## 适用场景
- **连续子块的 `kv_end` 必须全等**。若不等，ring 的迭代边界无法共用，合并不成立。
- 任务序应让连续 task 对应同一 KV head 的 q-block（例如 s_blk 最快、g 次之），才能保证"连续 N 个 task 的 kv_end 全等"。
- flag id 预算与 ws_o slab 数随 group 大小变化；host 与 kernel 必须同步修改，不能只改一侧常量。

## Step 2: 实施
1. host 侧增加 `MGROUP_MAX_HOST`，并在 ChooseMGroup 时校验 N 个子块的 `kv_end` 全等；不满足时退回 MGROUP=2/1。
2. kernel 侧 `MGROUP_MAX` 与 `tot_end = Σ sb_kvend[k]` 同步；每个子块独立 softmax 状态（UB 额外占用按 group 线性增长）。
3. 每个非末子块在 ring 中段 FIX 到自己的 ws_o slab；flag 与 FIX_M 信用按子块顺序配平。
4. 收益很小时，在共享/噪声较大的主机上很难单次判定；必须用同场交替 A/B、正反序至少两轮。
5. 若 MGROUP 增大后 UB 或 ws_o 超预算，先减少 group 大小，不要压缩每个子块的 softmax 状态。

## Step 4: 边界与回退
- 只对连续子块 kv_end 全等成立；动态 shape 下要在运行期校验，不能只看 host 静态信息。
- flag id 与 ws_o slab 数随 MGROUP 变化；host/kernel 不同步会导致静默错值或死锁。
- 收益通常小于几个百分点，必须用配对 A/B 排除噪声。

## Step 3: 验证
- 逐 bit 输出对比 + 全量精度。
- 同设备 A/B（至少 2 轮，正反序）；报告噪声带。
- 覆盖 kv_end 全等/不等、group 边界、尾块非整除。

## 关联
- 与 [X140](../../optimizations/evolution_strategies/discovered/disc_x140.md)（M 方向合批）和 [X157](../../optimizations/evolution_strategies/discovered/disc_x157.md)（0x2 信用批量化）同属"减少 task/ring 边界固定成本"的路线。
- 与 [X127](../../optimizations/evolution_strategies/discovered/disc_x127.md)（RING/PRELAUNCH）共享 ring 深度与填/排空分析。
