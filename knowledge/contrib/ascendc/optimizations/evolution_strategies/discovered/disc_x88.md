---
type: Optimization
title: "X88: 删 gemm_v0 入口 MTE2→MTE1 全量栅栏（让搬运与计算真正逐拍重叠）"
description: "模板 gemm_v0 每次调用开头都插了一条SetFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT); WaitFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT);。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X88: 删 gemm_v0 入口 MTE2→MTE1 全量栅栏（让搬运与计算真正逐拍重叠）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X88
> origin: discovered
> discovered_round: 2
> discovered_from: round_2/parallel_2
> base_speedup: 0.522x
> ```

## 核心思路
模板 `gemm_v0` 每次调用开头都插了一条
`SetFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT); WaitFlag<HardEvent::MTE2_MTE1>(L0AB_EVENT);`。
L1 的真实消费者是 **MTE1**（L1→L0A/L0B），而调用方给的 slot 就绪事件却是 `MTE2_M`；为了补这个
"消费者类型不匹配"的缺口，这条栅栏把 MTE1 队列压到**整条 MTE2 队列排空之后**——于是每个 K 拍都是
「搬完才算、算完才搬」，GEMM_STAGES 再深也无效。

**删掉这两行**即可恢复逐拍重叠：L1 读侧保护由调用方已有的
`WaitFlag<MTE2_M>(EV_READY + slot)` 经 **M 管道间接**提供（M 队列每轮先过这条 wait，才在 gemm_v0 里
`SetFlag<M_MTE1>` 释放 L0，MTE1 才去读 L1）；写侧与块边界由无条件执行的 `Set/Wait<M_MTE2>(2)` 保护。

## 适用场景
- 用 `tl_templates/ascend/common.h::gemm_v0`（或同源 catlass 模板）做 Cube GEMM 的 AscendC 算子；
- profiling 显示 **aic 三条 pipe 占比之和 ≈ 1.0**（例如 MTE2 0.517 + MTE1 0.157 + MAC 0.310 = 0.984），
  这是"逐拍零重叠"的指纹；正常应显著 > 1（实测改造后 1.783）；
- 典型受害形态：投影/长 K 循环 GEMM（K=d_model 几百到几千，K 拍数越多损失越大）。

## 实现要点
1. 只删 `gemm_v0` 入口那一对 `MTE2_MTE1` 的 Set/Wait，**其他事件一律不动**（尤其 `M_MTE1`）。
2. 删后自检：跑一次 aic-metrics，看 `aic_mte2_ratio` 是否显著上升（本例 0.517 → 0.887），
   且三 pipe 占比之和是否 > 1.5；同时用同 case 的 kernel 时间做 A/B（本例 qkv_proj 16104 → 8676us，1.86x）。
3. **不要**顺手把 slot 事件从 `MTE2_M` 改成 `MTE2_MTE1`。实测该"教科书式统一事件类型"写法在
   CANN 8.5.1 / arch 2201 上行为不符预期，全线慢 1.45~1.59x（每拍 3.077us ≈ 3× 单拍 MTE2）。
   收益全部来自"删栅栏"，与事件类型无关。
4. 若 L1 仍是单槽，本卡需与 X73/多槽 ring 叠加才有深流水；本卡负责"能重叠"，多槽负责"重叠多深"。

## 与相邻策略的边界
- 与 P1 双缓冲是**互补而非替代**：P1 解决"几条槽"，X88 解决"槽之间能不能同时干活"。
- 与 P5（细粒度同步）不冲突：本卡是**减**同步而非换同步粒度。
- 前置过滤（Preconditions）无法识别本卡（它判的是缺同步，本卡治的是多同步），按发现的 X 系列直接采纳。

## 验证记录（本仓实测）
- 算子 `10_FlashAttention`（6 段式 FA：qkv_proj/qscale/score/softmax/pv/out_proj），910B2C。
- case33 [32,512,4096] fp16 H=32 M=16384：`fa_qkv_proj_fp16` 16104.1 → 8676us（**1.86x**），
  整算子 24703 → 17883us；同 case aic pipe 0.517/0.157/0.310（和 0.984）→ 0.887/…/…（和 1.783）。
- 全量评测（50 case，per-case + warmup=3）：同 run geomean 0.5222 → **0.6546**（父实现 → 本变体 1.2586x），
  47/47 交集 case 全部变快（min 1.068 / median 1.262 / max 1.542）；与父实现 5/5 case 输出逐位相同。

## 来源
自动发现于第 2 轮进化（round_2/parallel_2，open_exploration 节点 x0_x1 的续作），
算子 10_FlashAttention，score 0.522x → 0.655x（vs PyTorch）。
