---
type: Optimization
title: QKV 两级分块 L1 复用在 ring 流水模板上三连回退
description: 反模式：放大 mBase 做 Q 微块共享 K/V 两级 L1 复用，ring 流水模板三连回退 0.904/0.856/0.999x 证伪。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/04-antipattern-two-level-tiling.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 反模式卡：QKV 两级分块 L1 复用在 ring 流水模板上三连回退

> **结论：在 FA-A5 模板族（MHA/GQA 三段中转 ring 流水）上，`fa_qkv_two_level_l1_reuse`
> （mBase 放大 + Q 微块共享 K/V L1 复用）是负收益方向。** 三次独立 codegen 实测：
> 0.904x（-10.6%）→ 0.856x（-14.4%）→ 0.999x（持平，修复尝试），均被拒。
> （2026-08-24/25，MHA run1 round 5-7，GLM-5.3，20 case 求和口径。）

---

## 1. 该策略的设计前提（为何在别的模板上有效）

历史锚点（flash_attention_strategies/01）：shape `4,32,4,1024,1024,128,fp16` 上
1.49x。其前提是被优化基线是**单级调度**：`for qBlock: for kvBlock: load K/V`——
每个 Q 微块都重复全量搬 K/V，放大 mBase 让一个任务装多个 Q 微块、K/V L1 tile 被
多次复用，GM→L1 搬运次数按 Q 微块数下降。

## 2. 为什么在 FA-A5 模板上失效（实证机理）

本模板已有结构：task=(bNkv, gSq, s2Cur)，mBase=128=BLOCK_M（**单 Q 微块/任务**），
K/V 的 L1 复用已发生在任务内 nL1 循环（kpQueL1_ 3 槽）；Q 每任务 LoadQ 一次。
放大 mBase→512 后实测回退，机理：

1. **任务数 ÷4 → 并行度受损**：totalWork=B×N×⌈S/512⌉，中小 batch 直接打不满
   32 核（本模板 MHA_MAX_CORES=32，GQA 侧 aicNum=8 同理）。
2. **workspace 槽膨胀**：wsS/wsP 槽 = mBase×s2Base，×4 后 per-core workspace 膨胀，
   Fixpipe 写出距离变长、L2 局部性劣化。
3. **L1 压力**：qBufL1_=2×mBase×dimAlign×2B，mBase=512 且 D=128 时 256KB，逼近
   L1 512KB 的半区约束（D256 直接溢出风险）。
4. **ring 流水失衡**：三段流水的槽位时延随任务粒度增大而方差增大，prelaunch=2
   的掩盖能力下降。

第三次尝试（0.999x）说明"参数调对能回到持平"，但**始终未见正收益**——复用收益
（本模板本就存在）< 并行度+局部性损失。

## 3. 判定清单（遇到该策略/同类"放大任务粒度"提案时先过一遍）

- [ ] 当前模板 K/V 是否已 per-task 装载、任务内 nL1 循环复用？（是 → 本策略前提不成立）
- [ ] mBase 当前是否 == BLOCK_M（单微块/任务）？
- [ ] 放大后 totalWork 是否仍 ≥ 核数×2（保持两波以上均衡）？
- [ ] qBufL1/kpQueL1 的 L1 半区预算是否容纳（含 D256 上界）？
- [ ] wsS/wsP/wsO 槽膨胀后 per-core workspace 与 L2 局部性影响评估过？

任一不过 → 跳过该策略，省一轮（本模板每轮 codegen+eval 约 40-60 分钟）。

## 4. 同轮其它负/零结果速记

| 策略 | 结果 | 判定 |
|---|---|---|
| fa_qkv_two_level_l1_reuse（s1） | 0.904/0.856/0.999x | 本卡主对象，方向证伪 |
| fa_vec_row_chunk_coalescing（s5） | 0.985x | vec2 行块合并在 20 case 总量上无收益（decode 局部或有小赢但被噪声淹没） |
| fa_monotonic_mask_suffix_bulk_fill（s13） | 1.002x | 掩码构造微优化，持平（正但也近零；作为 eval 链路首通锚点有价值） |
| fa_state_direct_cache_write（s3 叠加在 01 上） | 1.048x（低于 01 的 1.133x） | 叠加负收益，方向关闭 |
| fa_multibuffer_soft_pipeline（s2 裸结构） | no_op | 模板已实现（见 05 号清单） |

## 5. 交叉引用

- 正向对照：GQA 包 01 号（decode 分 KV 任务轴）是**反向操作**——把长轴拆进任务轴
  增加并行度，与本卡"放大粒度"互为镜像；在 decode 场景 GQA 01 拿到 3~12x。
  粒度决策先看并行度再看复用。

## 检索卡（短卡）

动作：反模式：放大 mBase 做 Q 微块共享 K/V 两级 L1 复用，ring 流水模板三连回退 0.904/0.856/0.999x 证伪。
适用：模板 K/V 已 per-task 装载且任务内 nL1 复用、mBase==BLOCK_M 单微块/任务时前提不成立，直接跳过。
限制：放大后 totalWork 须≥核数×2；qBufL1/kpQueL1 须容 L1 半区预算（含 D256 上界）；wsS/wsP 膨胀局部性先评估。
范围：MHA/GQA 三段中转 ring 流水模板的调度粒度决策。
检索词：fa_qkv_two_level_l1_reuse、mBase、两级分块、L1 复用、totalWork、kpQueL1。
机会：看到每 Q 微块重复搬 K/V 想放大粒度省搬运；实际该模板复用已存在，损失在并行度与局部性。
代价：任务数÷4 打不满 32 核；workspace 槽膨胀写出变长；L1 逼近半区约束。
