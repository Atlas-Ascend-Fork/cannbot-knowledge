---
type: Optimization
title: 单趟融合统计链与逐行 64-lane 折叠
description: 把多趟逐元素/归约 VF 融合成单趟统计 VF；逐行用 64-lane fold 累加，AR-reduce 成对折叠树一次归约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/single-pass-fused-statistics-chain.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F1",
  "slug": "single-pass-fused-statistics-chain",
  "name": "单趟融合统计链与逐行 64-lane 折叠",
  "summary": "把多趟逐元素/归约 VF 融合成单趟统计 VF；逐行用 64-lane fold 累加，AR-reduce 成对折叠树一次归约。",
  "intent": "消除中间量多次落 UB、重复 membar 与逐行 Reduce 串行化",
  "mechanism": "一个统计 VF 内完成两输入相加、cast 输出、乘系数、平方累加、绝对值最大；每行维护一个 64-lane fold 向量，逐 chunk 用全 lane mask 累加，每 tile 用 adv_api AR-reduce 成对折叠树对 [rows,64] 归约；量化段复用驻留中间量。不要用逐行 Reg::Reduce（vcadd/vcmax）在行循环里归约，它会把 V 流水串行化。",
  "principle": "多趟 VF 链的时间不只来自算术，还来自每趟 load/store 与 membar；单趟融合让中间量留在寄存器，UB 只承担首尾。",
  "operator_scope": "逐元素 + 行归约 + 量化的单遍流式复合算子",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "输入只读一遍、输出只写一遍",
      "行内统计可在寄存器折叠累加",
      "量化中间量可驻留"
    ],
    "excluded_conditions": [
      "多趟间存在必须落 UB 的跨 tile 依赖",
      "寄存器压力导致 spill",
      "只做融合、不配输入多槽（大 case 会回退）"
    ],
    "constraints": [
      "折叠累加必须全 lane mask（ZEROING 会清掉前序 chunk 的 lane）",
      "优先 AR-reduce 成对折叠树；逐行 Reduce 只作对照",
      "MulDstAdd 语义先穿刺（实测等价 dst*src0+src1）；紧凑回写用 StoreUnAlign(postUpdateStride=1)",
      "fold 链可用 2/4 路累加器，最后合并"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "ub-roundtrip",
      "membar",
      "vec-serial"
    ],
    "pattern": "fused-statistics",
    "reduce_mode": "row-stat",
    "structure": [
      "single-pass",
      "64-lane-fold",
      "ar-reduce",
      "full-mask"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "画出每 tile 的数据依赖，找出可融合的逐元素与归约",
    "把中间量放寄存器/UB 驻留，去掉中间落盘",
    "每行建 64-lane fold 向量，全 lane mask 累加平方/绝对值",
    "每 tile 用 AR-reduce 成对折叠树归约 [rows,64]",
    "量化段复用驻留中间量；与多趟链逐 case A/B"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "int8 位级/±1 门通过",
      "覆盖窄列、odd-N、NaN/Inf"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "寄存器压力/精度失败/大 case 回归时回退多趟链"
    ]
  },
  "risks": [
    "寄存器压力",
    "归约顺序变化影响精度",
    "单做融合会让大 case 回退"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "elementwise-reduction",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "multi-slot-input-prefetch-with-shape-routing",
    "cast-chain-fusion-int8-tolerance"
  ],
  "related_seed_ids": [],
  "instance_ids": [],
  "source": "benchmark-extraction",
  "status": "validated",
  "provenance": {
    "skill": "validated-optimization-extraction-20261111"
  }
}
-->

# 性能优化策略：单趟融合统计链与逐行 64-lane 折叠

单一优化点：把多趟逐元素/归约 VF 融合成单趟统计 VF；逐行用 64-lane fold 累加，AR-reduce 成对折叠树一次归约。

## 1. 原理

多趟 VF 链的时间不只来自算术，还来自每趟 load/store 与 membar；单趟融合让中间量留在寄存器，UB 只承担首尾。

实现机制：一个统计 VF 内完成两输入相加、cast 输出、乘系数、平方累加、绝对值最大；每行维护一个 64-lane fold 向量，逐 chunk 用全 lane mask 累加，每 tile 用 adv_api AR-reduce 成对折叠树对 [rows,64] 归约；量化段复用驻留中间量。不要用逐行 Reg::Reduce（vcadd/vcmax）在行循环里归约，它会把 V 流水串行化。

## 2. 性能问题模式

- 优化目标：消除中间量多次落 UB、重复 membar 与逐行 Reduce 串行化
- 适用数据流：逐元素 + 行归约 + 量化的单遍流式复合算子
- Feature signature：`{"bottleneck": ["ub-roundtrip", "membar", "vec-serial"], "pattern": "fused-statistics", "reduce_mode": "row-stat", "structure": ["single-pass", "64-lane-fold", "ar-reduce", "full-mask"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- int8 位级/±1 门通过
- 覆盖窄列、odd-N、NaN/Inf

资源与硬件约束：

- 折叠累加必须全 lane mask（ZEROING 会清掉前序 chunk 的 lane）
- 优先 AR-reduce 成对折叠树；逐行 Reduce 只作对照
- MulDstAdd 语义先穿刺（实测等价 dst*src0+src1）；紧凑回写用 StoreUnAlign(postUpdateStride=1)
- fold 链可用 2/4 路累加器，最后合并

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 输入只读一遍、输出只写一遍
- 行内统计可在寄存器折叠累加
- 量化中间量可驻留

不适用：

- 多趟间存在必须落 UB 的跨 tile 依赖
- 寄存器压力导致 spill
- 只做融合、不配输入多槽（大 case 会回退）

## 5. 实施步骤

1. 画出每 tile 的数据依赖，找出可融合的逐元素与归约
2. 把中间量放寄存器/UB 驻留，去掉中间落盘
3. 每行建 64-lane fold 向量，全 lane mask 累加平方/绝对值
4. 每 tile 用 AR-reduce 成对折叠树归约 [rows,64]
5. 量化段复用驻留中间量；与多趟链逐 case A/B

## 6. LLM 前置问题

- 目标实现是否满足：输入只读一遍、输出只写一遍？
- 目标实现是否满足：行内统计可在寄存器折叠累加？
- 目标实现是否满足：量化中间量可驻留？
- 是否命中排除条件：多趟间存在必须落 UB 的跨 tile 依赖？
- 是否命中排除条件：寄存器压力导致 spill？
- 是否命中排除条件：只做融合、不配输入多槽（大 case 会回退）？

## 7. 验收标准

正确性：

- 全量 20/20
- int8 位级/±1 门通过
- 覆盖窄列、odd-N、NaN/Inf

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 寄存器压力/精度失败/大 case 回归时回退多趟链

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：multi-slot-input-prefetch-with-shape-routing、cast-chain-fusion-int8-tolerance

- v3-cardonly-fused-20261111-01（status=accepted, operator_class=elementwise-reduction, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：把每tile多趟逐元素/归约VF融合成单趟统计VF；逐行用64-lane fold累加平方/绝对值，全lane mask，行末AR-reduce成对折叠树一次归约。
适用：逐元素+行归约+量化的单遍流式kernel；输入读一遍、三输出写一遍。
限制：逐行Reg::Reduce会串行化V流水，明显更慢；fold不能用chunk mask；单做融合不做输入流水会让大case回退。
范围：流式复合算子的计算链与逐行归约组织。
检索词：单趟融合、64-lane fold、全lane mask、AR-reduce、成对折叠、MulDstAdd、StoreUnAlign、多累加器。
机会：多趟VF链合并为1个统计VF；机制在目标算子族上有效。
代价：寄存器/UB预算；归约顺序变化需精度门；必须与输入多槽配套。
