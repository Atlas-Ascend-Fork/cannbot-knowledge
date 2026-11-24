---
type: Optimization
title: FA-950 模板族能力清单（K-Search no_op 排查表）
description: 在 FA-A5 模板族（MHA/GQA 同源三段中转 ring 流水）算子上跑 flash_attention_strategies catalog 前，先对照本表剔除「模板已实现」的策略，避免 no_op 轮次浪费。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/05-template-capability-checklist.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 适用性卡：FA-950 模板族能力清单（K-Search no_op 排查表）

> **用途：在 FA-A5 模板族（MHA/GQA 同源三段中转 ring 流水）算子上跑
> flash_attention_strategies catalog 前，先对照本表剔除"模板已实现"的策略。**
> 实证：MHA 第一轮（2026-08-24/25）中下列策略全部 `no_op`（no_edit_scope），
> 每条浪费一轮的 select+codegen 时间（约 5-15 分钟），四条合计烧掉 ~1 小时预算。

---

## 1. 模板已有能力 → 对应 catalog 策略对照表

| 模板既有实现（代码位置） | catalog 策略 id | no_op 实证 | 说明 |
|---|---|---|---|
| PRELAUNCH=2 / RING_SLOTS=3 环形 + TQue 双缓冲（mha_common.h） | fa_multibuffer_soft_pipeline | ✅ R1（裸结构） | 多缓冲软流水已是骨架本身 |
| maxCache/sumCache/expCache 片上三态缓存（mha_vec.h InitBuffers，RING_SLOTS×2KB） | fa_onchip_state_cache | ✅ R2 | per-row softmax 状态全片上 |
| Process() 连续任务派发环（mha_kernel.h，无短流水启停） | fa_continuous_task_ring_pipeline | ✅ R5 | 全核连续任务环已实现 |
| Mmad `cmatrixInitVal=isFirstK`（mha_cube.h MM1/MM2） | fa_first_accumulate_barrier_elision | ✅ R6 | 首累加前 barrier 已省 |
| vec1 state 直写目标槽（SoftmaxFlashV2 输出直连 cacheUb_） | fa_state_direct_cache_write | 半：裸结构可改；**叠加在 01 上为负收益**（1.048x<1.133x，见 04 号卡） | 场景依赖 |
| s2 分块 + 跨块 online-softmax 归并（0821 归档起 tiling 封顶 2048） | （fa_qkv_two_level_l1_reuse 的子集能力） | 结构已存在 | 勿重复实现 s2 多块 |

## 2. 判定方法论（可复用到其它模板）

K-Search 对"已实现"策略的 no_op 判定是可靠的（code-reader 阶段比对代码与策略
描述）；人工预筛更快——拿 catalog 的"单一优化点"一句话与模板代码 grep 对照：

```bash
# 示例：多缓冲 → 查 PRELAUNCH/RING_SLOTS；状态缓存 → 查 Cache Buf；
# 任务环 → 查 Process 主循环；首累加 barrier → 查 cmatrixInitVal/isFirstK
grep -n "PRELAUNCH\|RING_SLOTS" op_kernel/*_common.h
grep -n "CacheBuf_\|cacheUb_" op_kernel/*_vec.h
grep -n "isFirstK\|cmatrixInitVal" op_kernel/*_cube.h
```

## 3. 本模板族的已知缺口（值得排队的方向）

| 缺口 | 对应方向 | 状态 |
|---|---|---|
| causal 块/微块级裁剪 | 本包 01（已验证）/ 02（未测） | 01 已采纳 |
| decode/MTP 长轴不进任务轴（S_kv 单任务串行） | GQA 包 01 号思路移植（G=1 特化：任务数=B×N×s2OuterBlocks） | 未试，**下一轮最高 ROI** |
| vec 消费者输入队列深度 2（MTE2 与 VEC 交替空转） | 本包 03（未测） | 待 profiling 佐证 |
| vec1 P-ready 信号在 Cast+MTE3 写回前释放 | fa_vec1_early_p_release | 未测（前置 s4/s5 在本模板不成立，直接可试） |
| L1→L0 微块级装载裁剪 | 本包 02（未测） | 待测 |

## 4. 使用建议

- 注入 FA-A5 模板族算子时，catalog 建议剔除上表第 1 节 ✅ 的四条 + s1（04 号卡证伪），
  保留 02/03 号（本包 catalog.json 即此口径）。
- 模板迭代后（如 GQA 包策略被合入 MHA）需重跑本表对照——能力清单是**快照**，
  不是永久判定。
