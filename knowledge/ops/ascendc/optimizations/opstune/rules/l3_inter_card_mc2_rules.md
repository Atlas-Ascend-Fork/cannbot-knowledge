---
type: Optimization
title: "L3 卡间层 MC² 通算比判定规则语义（R 值五档 + MTE2 污染路由 + rank 不均衡）"
description: MC² 通算融合的卡间判定：隔离测试产出 T_comm/T_compute 后按 R=T_compute/T_comm 分五档（R≈1 平衡 / 1.1<R≤2 计算 bound / R>2 强计算 / 0.5≤R<0.9 通信 bound / R<0.5 强通信）；L3_MTE2_POLLUTED 判定 MTE2 指标被通信等待污染（ratio_full−ratio_pure>0.1 或 pure/full<0.8）并禁用单核访存规则改道通信掩盖；L3_RANK_IMBALANCE 判跨 rank 木桶。仅 950 实测标定。
tags: [task.optimization, task.debugging, topic.performance.analysis, topic.data_movement.communication.collective_communication]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune/ops-verdict/rules/L3-inter-card.yaml
    role: primary
created_at: "2026-11-05T03:20:00Z"
updated_at: "2026-11-05T03:20:00Z"
platforms: ["950"]
---

# L3 卡间层 MC² 通算比判定规则语义

MC²（通算融合）算子的卡间层判定七条规则。**前置要求**：T_comm（tileCnt=1 注释计算 process，多 rank 并行采集，取各 rank 稳态均值最大值）与 T_compute（tileCnt=1 注释通信 process，同口径）须由隔离测试产出；缺失时本规则包整体降级为 UNRESOLVED + 补采指令，不猜测。

## R 值五档判定

R = T_compute / T_comm（跨 rank max 稳态均值口径）：

| 规则 | R 区间 | 结论与首选机制 | speedup 预期 |
| --- | --- | --- | --- |
| L3_MC2_BALANCED | 0.9 ~ 1.1 | 通算完美平衡：等分切分即最优 | 1.0~1.1x |
| L3_MC2_COMPUTE_BOUND | 1.1 < R ≤ 2 | 计算 bound：用通信掩盖计算，增大 tileCnt | 1.1~1.8x 🟡 |
| L3_MC2_STRONG_COMPUTE | R > 2 | 强计算 bound：增大 tileCnt 收益极小，倾向少切分；须搜索确认 | 1.0~1.2x |
| L3_MC2_COMM_BOUND | 0.5 ≤ R < 0.9 | 通信 bound：用计算掩盖通信，增大 tileCnt | 1.1~1.8x 🟡 |
| L3_MC2_STRONG_COMM | R < 0.5 | 强通信 bound：从短块出发搜索，最大化 tileCnt | 1.2~2.0x |

阈值来源全部为 `[mc2-practice]`（MC² 通算融合一线多卡实测；R 值五档标定于真机 R 从 0.3 到 9.8 的实测分布）。**R 不是常数**——随 shape/量化/rank 数剧烈变化，每 case 必须实测，禁止沿用上一次的 R。

## 路由副作用规则（关键）

**L3_MTE2_POLLUTED（MTE2 指标被通信等待污染）**：完整算子的 mte2_ratio（含通信等待）与隔离测试纯计算路径的 mte2_ratio 差距 >10 个百分点，或纯/完整比 <80% 时命中。**on_hit 副作用：禁用 L1_MTE2_BOUND 单核规则**——MTE2 含通信等待空转，单核访存优化无效，改道通信掩盖策略（mc2 机制卡）。这是「先判污染再做单核访存优化」纪律的机器化执行：污染场景下做单核访存优化的案例多为负优化。

## L3_RANK_IMBALANCE

跨 rank 稳态均值 max/mean > 1.1 判跨 rank 木桶不均衡（初值为工程经验占位，M1 实测标定 🟡）。处置：跨 rank 长尾排查（rank 间数据量/进度错配）。

## 失效边界

- 本包所有规则的实测标定仅覆盖 950（MC²/SHMEM 路径）；a2/a3 未验证，不入 platforms；
- 隔离测试数据（T_comm/T_compute）缺失时整体 UNRESOLVED，不做无据判定；
- 掩盖率 = (融合前耗时−融合后耗时)/min(T_comm,T_compute)；跨 rank 一律取 max 口径——用平均口径报告会系统性高估收益；
- 阈值变更只改规则 YAML + evals 回归，本卡随后同步。
