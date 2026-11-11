---
type: Optimization
title: "X126: 有界分数下免 running-max，并让 PV 在 L0C 跨 chunk 累加"
description: "当 score 上界可静态证明时，用每个 slot 首 chunk 的行 max 作为固定偏移 m0，后续 chunk 不再做 alpha 重标定，PV 的 mmad 可在 L0C 中跨 chunk 纯累加，slot 末尾只 flush 一次；省掉 V2 阶段与 ws_o 的 GM 往返。要求 L0C 能同时容纳 acc_o 与 acc_s，O/combine 使用 fp32，P 的表示范围不足以承载无偏移值时必须回退。"
tags:
  - task.optimization
  - topic.attention
  - topic.kv_cache
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p148_fixed_offset_l0c_accumulation
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p148_fixed_offset_l0c_accumulation.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P148.yaml
    role: constraint
created_at: "2026-10-27T16:00:00Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X126: 有界分数下免 running-max，并让 PV 在 L0C 跨 chunk 累加

> 已晋升为 [P148](../cards/p148_fixed_offset_l0c_accumulation.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
decode / paged-decode attention（S_q 很小）的 C1→V1→C2→V2 环里，V2 的主要理由是 online softmax 的 running max 变化后，需要把已累积的 O 乘 `exp(m_old - m_new)` 重标定。若把 running max 换成一个**每个 slot 只算一次的固定偏移 m0**（例如取本 slot 首 chunk 的行 max），则
`P = exp(s - m0)`、`l = Σ exp(s - m0)`，m 恒定，**不需要任何重标定**。于是 C2 的 PV mmad 可以在 L0C 中跨 chunk 纯累加（`cmatrixInitVal` 仅首 chunk 为 true），slot 收尾时只 flush 一次。V2 阶段（读 ws_o、Cast/Broadcast/Mul/Add 与一对跨核 flag）与每 chunk 的 ws_o GM 往返整段消失。若 V2 还承担输出 dtype 转换、跨 KV split 合并等其它职责，则只删除重标定部分，不能整段删除。

## 适用场景
- decode / paged-decode attention，且 score 上界可以静态界定：`sm_scale * dqk` 的范围、输入分布、`logit_cap`、mask 规则都已知。
- **L0C 预算**：`acc_o + acc_s <= L0C 容量`。例如 `acc_o = hb * dc * 4`、`acc_s = hb * TOK * 4`；当 acc_o 单块就占满 L0C 时不可行。
- UB 预算：去掉 ws_o 环槽后通常更宽松；但 P 环槽仍需保留。
- 精度：固定偏移不等于全局 max，`P` 可能大于 1；O 与 combine 的输入必须用 fp32，除非能证明其量级不会溢出目标 dtype。

## 实现要点
1. **先证明表示范围，再删 max**：不要假设 q/k 服从标准正态。若输入分布使同一 slot 内 score 跨度很大，`l` 与 `|O|` 会达到 fp16 无法表示的量级。首版常见失败模式是 P/O 溢出为 Inf/NaN；此时应保留 running-max 或改用 fp32 累积。
2. **ws_p 的 dtype 由固定偏移的上界决定**：host 侧应给出静态上界（例如根据 dtype 的最大指数与 `exp` 的安全输入范围），门控不满足时回退带 max 路径。
3. **flush 一次写整块**：L0C 的 16×16 分形在内存中行交错；按 vid 分多次写同一块会覆盖前一次写入的行，表现为部分元素错误。应在 slot 收尾一次写完整块。
4. **保留必要的 WAR 节拍**：每 chunk 的一对 S_READY/O_READY 仍用于 ws_p 环槽的写后读保护（有意保留，不是遗漏）。
5. **尾块与特殊分支**：末 chunk 越界列在 exp 前压到 NEG_LARGE；`logit_cap > 0` 的 tanh 分支也要纳入上界判定，不要只对线性分支做静态分析。

## 验证方法
- 与保留 running-max 的参考实现做逐 case 数值对比，重点构造 score 量级跨度大的输入。
- 用静态断言/日志检查 L0C 占用与 `hb` 门控；对 hb 的每个分档分别验证。
- 压力测试：极值输入、全 mask 行、尾块非整除、`logit_cap` 开关。
- 若只能改一半（例如只去 max 但仍需 V2），收益会大幅缩水，需确认 V2 确实被整段删除。

## 关联
- 与 [X149](disc_x149.md)（block_m 取满 L0C）共享 L0C 预算约束。
- 与 [X174](disc_x174.md)（有界 logits 去 shift）同属"先证明上界再省向量操作"的路线，但作用点不同：本卡省的是跨 chunk 重标定与 GM 往返，X174 省的是每个 tile 的 shift 运算。
