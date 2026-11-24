---
type: Optimization
title: 未跑通的高价值方向（冲 score 1.10 的剩余弹药）
description: 状态：世界模型已排队但因会话中断（LLM 代理故障/轮次耗尽）未落地评测的方向；每条附预期收益模型与实施要点，按性价比排序。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/09-pending-opportunities.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-23T02:18:48Z'
platforms:
- '950'
---

# 机会清单：未跑通的高价值方向（冲 score 1.10 的剩余弹药）

> 状态：世界模型已排队但因会话中断（LLM 代理故障/轮次耗尽）未落地评测的
> 方向。每条附预期收益模型与实施要点，按性价比排序。

---

## 09-1. p_direct_mm2：P 单程中转（消除 wsP 写读双程）

- **问题**：softmax 输出 P 目前走 `AIV UB → GM wsP → AIC L1` 双程（写+读各
  mBase×s2Base×2B），占子集总流量 ~15-20%。F1（全留片上）证伪于无片上通路，
  但 **GM 单程是可行的**：Vec1 落 P 与 MM2 取 P 之间只有 flag 时序依赖。
- **方案**：Vec1 的 P Cast 直接写入 MM2 的 KP L1 布局（NZ 形态），MM2 免去
  `LoadNdGmToNzL1(pL1, wsPGm_…)` 的 ND→NZ 转装——中转仍在 GM 但消除
  "ND 写 + ND 读 + NZ 转装"三步中的转装步，且 L1 命中率提升。
  进阶：P 落盘与 MM2 首 K 段装载重叠（flag 提前半段发）。
- **预期**：prefill 大 case 5-10%（case8 314 vs 基线 197us 的差距主力之一）。
- **红线**：P 的 NZ 布局装载（LoadNzL1ToNzL0A 的 colC0Stride 口径）已有先例
  （decode 折叠 Q）；注意 P 精度维持 2B（07 号已证单级安全）。

## 09-2. decode 尾部：KV L1 预取加深（case14 136 vs 100us）

- **问题**：case14（B128 S1 Skv4096）MM1 的 Nd2Nz KV 装载是瓶颈段——
  vQueL1/kpQueL1 depth=2，Skv 长轴装载与 Mmad 交替出现停顿。
- **方案**：L1 预取深度 2→3/4（512KB 预算内重排：qBufL1 192KB + vQueL1
  128KB + kpQueL1 192KB 满负荷，需压缩 qBufL1 半区或复用 KP 槽）；或 KV
  装载改 4 段游标轮转（mla 包 02 号同款思路：MTE2 预发 + 游标轮转 depth-2
  右操作数槽，可直接借鉴）。
- **预期**：case14 10-15%；case11（52.6 vs 42.6us）同向。
- **红线**：L1 满负荷布局（RK-B03）改动必须重算全 buffer 预算表；D=256 的
  qBufL1 半区跨度约束（hc*pitch*dim*2B）不可破。

## 09-3. per-shape tiling 表扩展（case1/3/11 小 shape 键位）

- **问题**：02 号网格主要重扫了 MTP/短序列键位；小 prefill（case1 14 vs
  12us、case3 30 vs 18us、case11 52.6 vs 42.6us）的键位表未单独扫透。
- **方案**：按 02 号框架补扫小 shape 键位：mBase 16/32 档 + ring 槽深 1 +
  headChunk 微调；case3（Nq128 G16）可试 headChunk=16 的 M 维打包（01 号
  折叠机制在 prefill 小 shape 的复用）。
- **预期**：三个 case 合计对子集均值贡献 5-8%。
- **红线**：见 02 号（顺序纪律：必须在一切机制策略之后）。

## 09-4. case15 D=256 decode 的 L1 双段装载优化

- **问题**：case15（B60 S1 Skv1024 D256）188 vs 193us 已略反超，但 D=256 时
  kpQueL1 K 段跨度 D×256B 限制段深，MM1 的 K 维分块多一倍循环。
- **方案**：D=256 键位把 K 段与 V 段交错装载（同 L1 槽分时复用），或 K 段
  半段预装。
- **预期**：case15 5-10%（对子集贡献 ~2%，优先级最低）。

---

## 冲 1.10 的组合建议

当前 0.1236ms（score 0.777），需再 -30% 到 ~0.087ms：
**09-1（-8%）+ 09-2（-6%）+ 09-3（-6%）** 合计约 -20% → score ~0.97；
剩余靠 09-2/3 二轮迭代补足。若 p_direct_mm2 落地顺利（-10%+），达标概率大。

## 会话运维教训（连续跑长会话前先修）

- LLM 代理长请求偶发不归（本批会话致死 2 次）：SDK 超时 3600s + stage 重试
  预算是兜底但太钝，建议 KSEARCH_LLM_TIMEOUT_SECONDS 降到 900 重试更敏捷。
- 共享机器 torch 会被并行任务升降级（ABI 断裂致全 case ImportError）：长会话
  前 `import cv_agent_a5` 冒烟 + 评测 child 首轮失败先查环境再判代码。
- 迭代轮 fork 点钉最优 solution（F3 教训），必要时人工同步最优快照到
  task-path 后重启会话。
