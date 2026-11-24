---
type: Optimization
title: 小输出平坦 zone 坐标 hoist / 像素拥有 plane-group-split 负边界（load-latency-bound 证据）
description: 负向边界：把坐标一次计算/plane 循环移植进小输出平坦 zone 前，先用实测周期随访存步距扩张判别是否 load-latency 受限。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/flat-zone-coordinate-hoist-load-latency-bound.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "指令数模型预测必须在立项前用实测 cyc/el 与访存步距的相关性校验",
      "plane 分组填充线程不能改变每线程的访存跨度（否则延迟进一步恶化）"
    ],
    "excluded_conditions": [
      "load-latency 受限 zone（周期随采样步距扩张）不得立项坐标 hoist / 指令削减类机制：无收益且目标回归",
      "不得把发射受限 zone 的指令数收益模型外推到访存形态不同的 zone"
    ],
    "required_conditions": [
      "本卡为负边界：考虑把坐标一次计算/plane 循环结构移植进小输出或访存稀疏 zone 时适用",
      "判据：逐元素实测周期（aiv_total_cycles/blocks/每块元素数）随访存步距扩张 ⇒ load-latency 受限"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "comparison_sha256": "2cde3fa52503f9169d2c7d0e7f0ab96a171a0eeceaa5b1cb0cd48921702ae512",
      "decision_sha256": "48f8f36082f6bb658d4c27a14627f06f3e38fadf2cc8c5ebd14a6a9bf00f2ff7",
      "operator_class": "fused-composite",
      "performance_sha256": "ce108a38e91601b21276c36b142a01748a4e4f4249f2ad4be6414f324df650a1",
      "round": 6,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "d875030095bd0ca42740582a53d19c1089a0263482fdaed5f4186c879b3713fb",
      "verify_sha256": "afacdd4a5f0b6d896ff65e2aa0db07851b3a926888f53bbded817f90b62f5996"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "load-latency-bound-not-issue-bound",
      "issue-model-extrapolation-falsified"
    ],
    "dtypes": [
      "fp32",
      "fp16",
      "bf16"
    ],
    "pattern": "coordinate-hoist-into-flat-zone",
    "structure": [
      "pixel-owning-plane-group-split",
      "per-pixel-once-coordinates"
    ]
  },
  "generality": "op_class",
  "id": "NEG-RB-FLAT-ZONE-COORD-HOIST",
  "implementation_steps": [
    "（反例路径，勿复制）以像素为拥有单位加核内 plane 分组移植坐标一次计算结构",
    "对照：正确判别流程是先测逐元素周期与访存步距的相关性，确认发射受限后再谈指令削减"
  ],
  "intent": "消除平坦 zone 每元素重复的坐标分解/计算与寻址指令（假设该 zone 与大输出 zone 同为发射受限）",
  "mechanism": "像素拥有的 plane-group-split direct-GM VF：以像素为拥有单位、核内 plane 分组数 G=min(planeNum, ceil(线程数/每核像素数)) 填满 VF 线程，每像素坐标一次计算后组内 plane 循环复用；kernel 侧门控于平坦 zone 且 planeNum>=2，既有路径字节一致。",
  "name": "小输出平坦 zone 坐标 hoist / 像素拥有 plane-group-split 负边界（load-latency-bound 证据）",
  "operator_class": "fused-composite",
  "operator_scope": "坐标驱动重采样的小输出平坦 direct-GM zone（考虑把大输出 zone 已验证的坐标一次计算 + plane 循环结构移植进来的场合）",
  "principle": "同一指令流在不同访存形态下可以是发射受限或访存延迟受限；坐标 hoist 的收益前提是发射/ALU 受限。立项前必须用『逐元素周期 vs 采样步距/访存跨度』的实测相关性判别 zone 归属，不能把一个 zone 验证的机制外推到访存形态不同的另一个 zone。",
  "related_anti_patterns": [],
  "risks": [
    "指令数模型预测的收益完全落空（本轮预测 1.25-2.15x，实测全目标回归）",
    "plane 分组可能加大访存跨度使延迟进一步恶化"
  ],
  "slug": "flat-zone-coordinate-hoist-load-latency-bound",
  "summary": "把大输出 zone 已验证的『每像素坐标一次 + 线程内 plane 循环』结构移植到小输出平坦 zone（像素拥有 + 核内 plane 分组填充线程），实测无收益且全部目标回归：平坦 zone 逐元素实测周期随 W 向采样步距扩张（相同指令流下周期数成倍扩张），证明该 zone 是访存延迟受限而非发射/ALU 受限——基于指令数模型的收益预测被证伪。坐标 hoist 只在发射受限 zone 兑现。",
  "verification": {
    "correctness": [
      "verify 全 case 通过（本轮 20/20）；既有路径字节一致，control 增量 ~1.0x 且 0 回归"
    ],
    "performance": [
      "incremental total_speedup 0.9874，全部 3 个门控目标回归（低于 max_case_regression=0.95 阈值档），策略自设硬门（目标热形状 >=1.4x）实测 0.897x（稳定，非噪声）；aiv_vec_time 均上升",
      "逐元素周期实测：平坦 zone 相同指令流下周期随 W-tap 步距 1.12→2.19→2.44 cyc/el 扩张，而大输出 zone cache-friendly 地板 0.41-0.45 cyc/el——zone 受限类型不同的直接证据"
    ],
    "rollback_signals": [
      "门控目标增量 <1.0（cv 低即稳定非噪声）即回退；实测 cyc/el 随步距扩张即判 load-latency 受限、放弃指令类候选"
    ]
  }
}
-->

# 性能优化策略：小输出平坦 zone 坐标 hoist / 像素拥有 plane-group-split 负边界（load-latency-bound 证据）

单一优化点：把大输出 zone 已验证的『每像素坐标一次 + 线程内 plane 循环』结构移植到小输出平坦 zone（像素拥有 + 核内 plane 分组填充线程），实测无收益且全部目标回归：平坦 zone 逐元素实测周期随 W 向采样步距扩张（相同指令流下周期数成倍扩张），证明该 zone 是访存延迟受限而非发射/ALU 受限——基于指令数模型的收益预测被证伪。坐标 hoist 只在发射受限 zone 兑现。

## 1. 原理

同一指令流在不同访存形态下可以是发射受限或访存延迟受限；坐标 hoist 的收益前提是发射/ALU 受限。立项前必须用『逐元素周期 vs 采样步距/访存跨度』的实测相关性判别 zone 归属，不能把一个 zone 验证的机制外推到访存形态不同的另一个 zone。

实现机制：像素拥有的 plane-group-split direct-GM VF：以像素为拥有单位、核内 plane 分组数 G=min(planeNum, ceil(线程数/每核像素数)) 填满 VF 线程，每像素坐标一次计算后组内 plane 循环复用；kernel 侧门控于平坦 zone 且 planeNum>=2，既有路径字节一致。

## 2. 性能问题模式

- 优化目标：消除平坦 zone 每元素重复的坐标分解/计算与寻址指令（假设该 zone 与大输出 zone 同为发射受限）
- 适用数据流：坐标驱动重采样的小输出平坦 direct-GM zone（考虑把大输出 zone 已验证的坐标一次计算 + plane 循环结构移植进来的场合）
- Feature signature：`{"bottleneck": ["load-latency-bound-not-issue-bound", "issue-model-extrapolation-falsified"], "dtypes": ["fp32", "fp16", "bf16"], "pattern": "coordinate-hoist-into-flat-zone", "structure": ["pixel-owning-plane-group-split", "per-pixel-once-coordinates"]}`

## 3. 正确性红线

- 指令数模型预测的收益完全落空（本轮预测 1.25-2.15x，实测全目标回归）
- plane 分组可能加大访存跨度使延迟进一步恶化

资源与硬件约束：

- 指令数模型预测必须在立项前用实测 cyc/el 与访存步距的相关性校验
- plane 分组填充线程不能改变每线程的访存跨度（否则延迟进一步恶化）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 本卡为负边界：考虑把坐标一次计算/plane 循环结构移植进小输出或访存稀疏 zone 时适用
- 判据：逐元素实测周期（aiv_total_cycles/blocks/每块元素数）随访存步距扩张 ⇒ load-latency 受限

不适用：

- load-latency 受限 zone（周期随采样步距扩张）不得立项坐标 hoist / 指令削减类机制：无收益且目标回归
- 不得把发射受限 zone 的指令数收益模型外推到访存形态不同的 zone

## 5. 实施步骤

1. （反例路径，勿复制）以像素为拥有单位加核内 plane 分组移植坐标一次计算结构
2. 对照：正确判别流程是先测逐元素周期与访存步距的相关性，确认发射受限后再谈指令削减

## 6. LLM 前置问题

- 目标实现是否满足：本卡为负边界：考虑把坐标一次计算/plane 循环结构移植进小输出或访存稀疏 zone 时适用？
- 目标实现是否满足：判据：逐元素实测周期（aiv_total_cycles/blocks/每块元素数）随访存步距扩张 ⇒ load-latency 受限？
- 是否命中排除条件：load-latency 受限 zone（周期随采样步距扩张）不得立项坐标 hoist / 指令削减类机制：无收益且目标回归？

## 7. 验收标准

正确性：

- verify 全 case 通过（本轮 20/20）；既有路径字节一致，control 增量 ~1.0x 且 0 回归

性能：

- incremental total_speedup 0.9874，全部 3 个门控目标回归（低于 max_case_regression=0.95 阈值档），策略自设硬门（目标热形状 >=1.4x）实测 0.897x（稳定，非噪声）；aiv_vec_time 均上升
- 逐元素周期实测：平坦 zone 相同指令流下周期随 W-tap 步距 1.12→2.19→2.44 cyc/el 扩张，而大输出 zone cache-friendly 地板 0.41-0.45 cyc/el——zone 受限类型不同的直接证据

回滚信号：

- 门控目标增量 <1.0（cv 低即稳定非噪声）即回退；实测 cyc/el 随步距扩张即判 load-latency 受限、放弃指令类候选

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- resize_bilinear-20260902_032419-3fd855（round=6, status=rejected）

## 检索卡（短卡）

动作：负向边界：把坐标一次计算/plane 循环移植进小输出平坦 zone 前，先用实测周期随访存步距扩张判别是否 load-latency 受限
适用：考虑把坐标一次计算/plane 循环结构移植进小输出或访存稀疏 zone 时适用
限制：load-latency 受限 zone 不得立项坐标 hoist/指令削减类机制；不得外推发射受限 zone 的模型
范围：fused-composite 的坐标驱动重采样 direct-GM zone
检索词：cyc/el、W-tap 步距、load-latency-bound、plane-group-split、direct-GM VF
机会：平坦 zone 同指令流下周期随 W-tap 步距 1.12→2.19→2.44 cyc/el 扩张
代价：指令数模型的收益预测完全落空，全部门控目标回归
