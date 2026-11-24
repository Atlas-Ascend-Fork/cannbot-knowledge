---
type: Optimization
title: 按更新轴长度混合分派独占归约与原子更新
description: 短更新轴采用切片独占，长更新轴采用并行原子更新，以成本交叉决定分派。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.atomic
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/short-axis-owner-long-axis-atomic.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "excluded_conditions": [
      "物理地址别名破坏独占性",
      "要求固定顺序但原子路径不能满足"
    ],
    "required_conditions": [
      "不同owner的输出切片物理互斥",
      "归约语义允许原子路径的更新顺序"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "short-axis-atomic-contention",
      "long-axis-owner-serialization"
    ],
    "pattern": "short-axis-owner-long-axis-atomic",
    "structure": [
      "slice-ownership",
      "atomic-update",
      "cost-crossover-dispatch"
    ]
  },
  "generality": "pattern",
  "id": "SHORT-AXIS-OWNER-LONG-AXIS-ATOMIC",
  "implementation_steps": [
    "明确输出物理所有权及初始值复制关系，计算独立切片数和每切片更新量。",
    "实现短轴 owner 路径，缩小坐标解码与更新循环范围。",
    "实现长轴原子路径，核对累加类型、CAS 读写及最终转换。",
    "扫描成本交叉区域并设置元数据分派；融合时单独核算重复扫描和私有状态开销。"
  ],
  "intent": "统一使用原子时，少量目标被重复更新导致争用；统一使用 owner 时，长轴更新集中为少数线程的串行循环。",
  "mechanism": "短更新轴由单一owner独占目标切片，长更新轴摊开独立更新并以原子合并，按成本交叉选择。",
  "name": "按更新轴长度混合分派独占归约与原子更新",
  "operator_scope": "可由合法元数据识别短轴和长轴，owner 切片物理互斥，且存在满足语义的原子或 CAS 合并。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "短更新轴上，单线程遍历某一切片的全部更新，可用普通读改写消除原子竞争；当独立切片足够多时仍能保持并行。更新轴变长后，同一 owner 的串行链会拉长，改为将更新项分给多个线程并用原子合并，可提高可用并行度。两者优势由轴长、切片数、冲突分布和原子类型共同决定。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "owner 必须独占物理目标切片，不能只证明逻辑坐标不同",
    "每个有效更新必须贡献一次，初始输出、累加类型、整数溢出及特殊值规则须保留",
    "原子路径的重排必须符合精度和确定性要求；以 CAS 实现组合更新时，初值读取与重试循环必须保证一致性",
    "低精度累加后转换不得擅自改为低精度逐次写回"
  ],
  "schema_version": 2,
  "slug": "short-axis-owner-long-axis-atomic",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "短更新轴采用切片独占，长更新轴采用并行原子更新，以成本交叉决定分派。",
  "verification": {
    "correctness": [
      "覆盖分派两侧、重复索引、独立步长与尾部，确认每项贡献完整且精度符合要求",
      "完整调用分别验证短轴争用和长轴串行链得到改善"
    ],
    "performance": [
      "阈值邻域退化、物理别名、精度差异或私有资源超限时，调整分派或回退原路径"
    ],
    "rollback_signals": [
      "输出别名破坏所有权，或严格固定顺序使原子路径不合法",
      "分派阈值须按轴长、切片数、类型和设备重新确定，不能把固定轴长或线程数当作普遍常量",
      "双路径增加维护成本，窗口重复扫描和私有槽位可能抵消融合收益"
    ]
  }
}
-->

# 性能优化策略：按更新轴长度混合分派独占归约与原子更新

单一优化点：短更新轴采用切片独占，长更新轴采用并行原子更新，以成本交叉决定分派。

## 1. 原理

短更新轴上，单线程遍历某一切片的全部更新，可用普通读改写消除原子竞争；当独立切片足够多时仍能保持并行。更新轴变长后，同一 owner 的串行链会拉长，改为将更新项分给多个线程并用原子合并，可提高可用并行度。两者优势由轴长、切片数、冲突分布和原子类型共同决定。

## 2. 性能问题模式

统一使用原子时，少量目标被重复更新导致争用；统一使用 owner 时，长轴更新集中为少数线程的串行循环。按输出窗口分配 owner 又可能让每个窗口重复扫描所有更新。将整轴状态放入线程私有槽位，还会增加寄存器、栈与初始化成本。

## 3. 正确性红线

owner 必须独占物理目标切片，不能只证明逻辑坐标不同。每个有效更新必须贡献一次，初始输出、累加类型、整数溢出及特殊值规则须保留。原子路径的重排必须符合精度和确定性要求；以 CAS 实现组合更新时，初值读取与重试循环必须保证一致性。低精度累加后转换不得擅自改为低精度逐次写回。

## 4. 泛化条件

适用：可由合法元数据识别短轴和长轴，owner 切片物理互斥，且存在满足语义的原子或 CAS 合并。

不适用：输出别名破坏所有权，或严格固定顺序使原子路径不合法。分派阈值须按轴长、切片数、类型和设备重新确定，不能把固定轴长或线程数当作普遍常量。双路径增加维护成本，窗口重复扫描和私有槽位可能抵消融合收益。

## 5. 实施步骤

1. 明确输出物理所有权及初始值复制关系，计算独立切片数和每切片更新量。
2. 实现短轴 owner 路径，缩小坐标解码与更新循环范围。
3. 实现长轴原子路径，核对累加类型、CAS 读写及最终转换。
4. 扫描成本交叉区域并设置元数据分派；融合时单独核算重复扫描和私有状态开销。

## 6. LLM 前置问题

- 切片是否物理互斥，独立切片是否足够填满设备？
- 串行链长度与原子争用各由什么决定？
- 融合省掉的启动和复制，是否小于新增扫描、栈或寄存器成本？

## 7. 验收标准

覆盖分派两侧、重复索引、独立步长与尾部，确认每项贡献完整且精度符合要求。完整调用分别验证短轴争用和长轴串行链得到改善。阈值邻域退化、物理别名、精度差异或私有资源超限时，调整分派或回退原路径。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：短更新轴采用切片独占归约，长轴采用并行原子更新，以成本交叉决定分派。
适用：owner目标切片物理互斥，合法元数据可分派，且存在符合语义的原子或CAS合并。
限制：每项贡献一次并保留初值及累加类型；原子重排须合约允许；阈值按轴长、切片数、类型和设备确定。
范围：索引归约的独占切片与原子更新选择。
检索词：owner、切片独占、原子更新、CAS、成本交叉、分派阈值
机会：短轴原子竞争高，长轴单owner串行链长，统一路径难兼顾并行与冲突成本。
代价：双路径维护、窗口重复扫描及线程私有槽位可能抵消融合收益。
