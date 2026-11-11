---
type: Runbook
title: "P148 Playbook: 有界分数下免 running-max，并让 PV 在 L0C 跨 chunk 累加 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x126.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.kv_cache
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x126.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p148_fixed_offset_l0c_accumulation.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P148.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P148
---
# P148 Playbook: 有界分数下免 running-max，并让 PV 在 L0C 跨 chunk 累加 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x126.md](../../optimizations/evolution_strategies/discovered/disc_x126.md)。

## Step 1: 取证

```bash
grep -nE "softmax|Exp|kv|K|V" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
decode / paged-decode attention（S_q 很小）的 C1→V1→C2→V2 环里，V2 的主要理由是 online softmax 的 running max 变化后，需要把已累积的 O 乘 `exp(m_old - m_new)` 重标定。若把 running max 换成一个**每个 slot 只算一次的固定偏移 m0**（例如取本 slot 首 chunk 的行 max），则
`P = exp(s - m0)`、`l = Σ exp(s - m0)`，m 恒定，**不需要任何重标定**。于是 C2 的 PV mmad 可以在 L0C 中跨 chunk 纯累加（`cmatrixInitVal` 仅首 chunk 为 true），slot 收尾时只 flush 一次。V2 阶段（读 ws_o、Cast/Broadcast/Mul/Add 与一对跨核 flag）与每 chunk 的 ws_o GM 往返整段消失。若 V2 还承担输出 dtype 转换、跨 KV split 合并等其它职责，则只删除重标定部分，不能整段删除。

## 适用场景
- decode / paged-decode attention，且 score 上界可以静态界定：`sm_scale * dqk` 的范围、输入分布、`logit_cap`、mask 规则都已知。
- **L0C 预算**：`acc_o + acc_s <= L0C 容量`。例如 `acc_o = hb * dc * 4`、`acc_s = hb * TOK * 4`；当 acc_o 单块就占满 L0C 时不可行。
- UB 预算：去掉 ws_o 环槽后通常更宽松；但 P 环槽仍需保留。
- 精度：固定偏移不等于全局 max，`P` 可能大于 1；O 与 combine 的输入必须用 fp32，除非能证明其量级不会溢出目标 dtype。

## Step 2: 实施
1. **先证明表示范围，再删 max**：不要假设 q/k 服从标准正态。若输入分布使同一 slot 内 score 跨度很大，`l` 与 `|O|` 会达到 fp16 无法表示的量级。首版常见失败模式是 P/O 溢出为 Inf/NaN；此时应保留 running-max 或改用 fp32 累积。
2. **ws_p 的 dtype 由固定偏移的上界决定**：host 侧应给出静态上界（例如根据 dtype 的最大指数与 `exp` 的安全输入范围），门控不满足时回退带 max 路径。
3. **flush 一次写整块**：L0C 的 16×16 分形在内存中行交错；按 vid 分多次写同一块会覆盖前一次写入的行，表现为部分元素错误。应在 slot 收尾一次写完整块。
4. **保留必要的 WAR 节拍**：每 chunk 的一对 S_READY/O_READY 仍用于 ws_p 环槽的写后读保护（有意保留，不是遗漏）。
5. **尾块与特殊分支**：末 chunk 越界列在 exp 前压到 NEG_LARGE；`logit_cap > 0` 的 tanh 分支也要纳入上界判定，不要只对线性分支做静态分析。

## Step 3: 验证
- 与保留 running-max 的参考实现做逐 case 数值对比，重点构造 score 量级跨度大的输入。
- 用静态断言/日志检查 L0C 占用与 `hb` 门控；对 hb 的每个分档分别验证。
- 压力测试：极值输入、全 mask 行、尾块非整除、`logit_cap` 开关。
- 若只能改一半（例如只去 max 但仍需 V2），收益会大幅缩水，需确认 V2 确实被整段删除。

## 关联
- 与 [X149](../../optimizations/evolution_strategies/discovered/disc_x149.md)（block_m 取满 L0C）共享 L0C 预算约束。
- 与 [X174](../../optimizations/evolution_strategies/discovered/disc_x174.md)（有界 logits 去 shift）同属"先证明上界再省向量操作"的路线，但作用点不同：本卡省的是跨 chunk 重标定与 GM 往返，X174 省的是每个 tile 的 shift 运算。
