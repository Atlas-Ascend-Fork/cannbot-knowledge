---
type: Optimization
title: "X88: 删 gemm_v0 入口 MTE2→MTE1 全量栅栏（让搬运与计算真正逐拍重叠）"
description: "模板 gemm_v0 每次调用开头都插了一条 MTE2→MTE1 的 Set/Wait 全量栅栏，把 MTE1 队列压到整条 MTE2 队列排空之后。删除这对栅栏后，L1 读侧保护由调用方已有的 MTE2→M 事件经 M 管道间接提供，搬运与计算可逐拍重叠，GEMM_STAGES 的深度才真正生效。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X88: 删 gemm_v0 入口 MTE2→MTE1 全量栅栏（让搬运与计算真正逐拍重叠）

## 核心思路

模板 `gemm_v0` 每次调用开头都插了一条
`SetFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT); WaitFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT);`。
L1 的真实消费者是 **MTE1**（L1→L0A/L0B），而调用方给的 slot 就绪事件却是 `MTE2_M`；为了补这个
「消费者类型不匹配」的缺口，这条栅栏把 MTE1 队列压到**整条 MTE2 队列排空之后**——于是每个 K 拍都是
「搬完才算、算完才搬」，GEMM_STAGES 再深也无效。

**删掉这两行**即可恢复逐拍重叠：L1 读侧保护由调用方已有的
`WaitFlag<MTE2_M>(EV_READY + slot)` 经 **M 管道间接**提供（M 队列每轮先过这条 wait，才在 gemm_v0 里
`SetFlag<M_MTE1>` 释放 L0，MTE1 才去读 L1）；写侧与块边界由无条件执行的 `Set/Wait<M_MTE2>(2)` 保护。

## 适用场景

- 用 `tl_templates/ascend/common.h::gemm_v0`（或同源 catlass 模板）做 Cube GEMM 的 AscendC 算子；
- profiling 显示 **aic 三条 pipe 占比之和 ≈ 1.0**，这是「逐拍零重叠」的指纹；正常重叠时应显著大于 1；
- 典型受害形态：投影/长 K 循环 GEMM（K=d_model 几百到几千，K 拍数越多损失越大）。

## 实现要点

1. 只删 `gemm_v0` 入口那一对 `MTE2_MTE1` 的 Set/Wait，**其他事件一律不动**（尤其 `M_MTE1`）。
2. 删后自检：跑一次 aic-metrics，看 `aic_mte2_ratio` 是否显著上升，且三 pipe 占比之和是否明显大于 1；
   同时用同形状的 kernel 时间做 A/B。
3. **不要**顺手把 slot 事件从 `MTE2_M` 改成 `MTE2_MTE1`。该「教科书式统一事件类型」写法在部分
   CANN/arch 版本上行为不符预期，全线变慢；收益全部来自「删栅栏」，与事件类型无关。
4. 若 L1 仍是单槽，本卡需与 X73/多槽 ring 叠加才有深流水；本卡负责「能重叠」，多槽负责「重叠多深」。

## 与相邻策略的边界

- 与 P1 双缓冲是**互补而非替代**：P1 解决「几条槽」，X88 解决「槽之间能不能同时干活」。
- 与 P5（细粒度同步）不冲突：本卡是**减**同步而非换同步粒度。
- 前置过滤（Preconditions）无法识别本卡（它判的是缺同步，本卡治的是多同步），按发现的 X 系列直接采纳。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 同步类改动额外用 profiling 的三条 AIC pipe 占比之和交叉验证重叠是否真的发生。
