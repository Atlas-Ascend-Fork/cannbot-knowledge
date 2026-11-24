---
type: Optimization
title: 512-lane int64 SIMT 体的 per-element 偏移算术节食：magic-division（窄域 no-fixup）+ active-dim 列表 + 单活跃维直表达式 + SCALAR 预读
description: GcdSimtKernelInt64（LAUNCH_BOUND(512)）在 GENERAL-broadcast 每元素上付出一次运行时整除 + 一次取模（tGm 加载的运行时值）外加 8 槽守卫扫描。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-int64-offset-arithmetic-diet.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "薄收益机制（~1.03x 级）需与 max_rounds 预算权衡：优先在头部 headroom case 上使用",
      "header 增行数（本例 +152 行）会带来 c15 型 TU 漂移（-2.2%），属机制的常设成本，须记录不掩盖",
      "probe/measure 双通道的 canary（SAME 臂）方差在单-digit-us 级，读数按带内处理"
    ],
    "excluded_conditions": [
      "不得把同款 prologue 富集加到 1024-lane 臂（r3 证伪）",
      "divisor 域超出窄域 no-fixup 编码适用域时必须换带 fixup 形态或放弃（不得静默截断）",
      "编辑不得越出目标臂文件/函数（跨臂泄漏由 control 块检测）"
    ],
    "required_conditions": [
      "SIMT direct-GM 载体已 accepted 且其 GENERAL 偏移含运行时 div/mod + 固定槽宽守卫扫描",
      "目标臂 LAUNCH_BOUND 宽度的寄存器余量经 probe 验证可容纳 prologue 状态（512-lane 实证为正；1024-lane 实证为负）",
      "magic 常数在 host 侧经暴力对抗检查（覆盖角点/包络值）后才上设备",
      "每 route 有 gate 排除的 control case 监控 TU 漂移（[0.97,1.03] 带）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "facts": "r3 证伪补丁的 512-lane int64 半部逐字重提；probe go 干净；增量 1.0294x、零回归；官方最终 70.01 vs baseline 62.64",
      "operator_class": "broadcast",
      "round": 5,
      "run_id": "<run-id>",
      "status": "accepted"
    },
    {
      "comparison_sha256": "679805ca4adad07f4e90835650556f3c3e627ab570d30fb3dad111b4e8cbf57e",
      "decision_sha256": "6a869d77c1a7d227fd4841331487cdfb49ef3d04c05824846f1e5f7b8887c095",
      "operator_class": "broadcast",
      "performance_sha256": "7eb27775d13807f56dc72bedb6f208b888e24e48308b5b7c293f9fd7a029a1c9",
      "round": 5,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "592371799204908e8914d7a49a21aee73b058c72545fbb0c8ca2de8428748bfe",
      "verify_sha256": "16afe21756429ab480ff5b36255dce23941bb3e6e06be0d2db5c66c4876bf073"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "runtime-div-mod",
      "guard-scan",
      "per-element-offset-arithmetic"
    ],
    "dtypes": [
      "int64"
    ],
    "pattern": "simt-offset-arithmetic-diet-512lane",
    "structure": [
      "magic-division",
      "active-dim-list",
      "single-active-dim-direct",
      "scalar-pre-read",
      "launch-bound-512"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-SIMT-INT64-OFFSET-DIET",
  "implementation_steps": [
    "从上一轮保留 patch 中提取目标臂 hunk（若该机制曾在更宽 lane 臂被证伪）",
    "host 暴力对抗检查 magic-div 编码（角点 + 随机域）",
    "单文件最小编辑：magic helper + active-dim 列表 + 单活跃维直表达式 + SCALAR 预读，不动其他臂文本",
    "probe 验证目标为正且 canary 带内后再全量 measure，control 块裁决 TU 漂移"
  ],
  "intent": "消除 SIMT direct-GM 载体 int64 臂残余的 per-element 偏移算术税（运行时 div/mod + 守卫扫描），把 broadcast decompose 的每元素成本压到乘/移位级。",
  "mechanism": "op_kernel/gcd_simt.h 内：(1) SimtMagicDiv/SimtMagicMod helper（窄域 no-fixup 形态，pow2 经 mm bit31==0 自判别走 shift/mask）；(2) GcdSimtKernelInt64 prologue 每线程一次构建 active-dim 列表 act1/act2（broadcast 维剔除）；(3) 单活跃维走直表达式；(4) SCALAR 臂 x2 预读。编辑作用域仅 gcd_simt.h 单文件，T1/T2 体与父逐字节一致（机械验证）。补丁文本逐字取自 r3 保留 patch 的 int64 hunk。",
  "name": "512-lane int64 SIMT 体的 per-element 偏移算术节食：magic-division（窄域 no-fixup）+ active-dim 列表 + 单活跃维直表达式 + SCALAR 预读",
  "operator_class": "broadcast",
  "operator_scope": "整核 SIMT direct-GM 载体 int64/512-lane 臂的 GENERAL-broadcast per-element 偏移计算段：运行时整除/取模 + 8 槽守卫扫描 → 常数化除法 + 活跃维列表",
  "principle": "偏移 decompose 的除数在 kernel 生命周期内是常量（来自 tiling 表），运行时整除可用 Granlund-Montgomery magic 常数化为 mul/shift；broadcast 使多数维 stride=0（不活跃），把 8 槽全扫描换成每线程一次构建的 active-dim 列表；单活跃维可直表达式短路；SCALAR 臂的 x2 值每核只读一次。这些 prologue 状态在 512-lane 寄存器预算内为净收益——同一组合在 1024-lane 臂 spill 为净损失（见 simt-vf-prologue-enrichment-register-pressure），机制收益由 instantiation 宽度决定。",
  "related_anti_patterns": [],
  "risks": [
    "在更宽 lane 臂上复用同款 prologue 会寄存器 spill（见负向边界卡）",
    "magic 常数域外静默错值：必须 host 对抗检查前置",
    "TU 漂移累积：多个薄机制叠加时未编辑路径的 -2% 级漂移可能突破 0.95 硬线"
  ],
  "slug": "simt-int64-offset-arithmetic-diet",
  "summary": "GcdSimtKernelInt64（LAUNCH_BOUND(512)）在 GENERAL-broadcast 每元素上付出一次运行时整除 + 一次取模（tGm 加载的运行时值）外加 8 槽守卫扫描。把该路径节食为：namespace 级 SimtMagicDiv/SimtMagicMod（Granlund-Montgomery 窄域 no-fixup 编码，2 的幂用 shift/mask 自判别；host 暴力 127,674,604 对抗检查 0 失配）+ 每线程一次构建的 active-dim 列表 act1/act2 + 单活跃维直表达式 + SCALAR 操作数预读。accepted：增量 1.0294x（目标块 1.0441x：c13 1.0541x、c20 1.0379x，与 r3 隔离 A/B 复现差 <0.2%），8 个 per-route control 最差 c15 0.9775x 在带内，累计 1.8736x；官方最终累计 1.8991x、零回归、官方分 62.64→70.01。",
  "verification": {
    "correctness": [
      "verify 10/10（validation 集）golden 全过；指纹链一致（op_source 0ad1ebb744246466 / kernel 5ec20d61f846b849 / commit f4c0349，before 态正确链到 r2-accepted 父与 baseline）",
      "最终 final official_eval correctness 20/20"
    ],
    "performance": [
      "增量 1.0294x（目标块 1.0441x：c13 1.0541x、c20 1.0379x，复现 r3 隔离 A/B <0.2%）；8 control 最差 c15 0.9775x（0.95 硬线内、0.97 带边缘）",
      "累计 1.8736x（measure 口径）；官方最终累计 1.8991x、20/20 全改善、regressed_cases=0、官方分 62.64→70.01（+7.37）"
    ],
    "rollback_signals": [
      "control 块跌破 0.95 → TU 漂移超标，回退",
      "c13/c20 复现性破坏（与 r3 隔离 A/B 偏差 >2%）→ 环境异常，补采",
      "verify golden 失败 → 回退父核"
    ]
  }
}
-->

# 性能优化策略：512-lane int64 SIMT 体的 per-element 偏移算术节食：magic-division（窄域 no-fixup）+ active-dim 列表 + 单活跃维直表达式 + SCALAR 预读

单一优化点：GcdSimtKernelInt64（LAUNCH_BOUND(512)）在 GENERAL-broadcast 每元素上付出一次运行时整除 + 一次取模（tGm 加载的运行时值）外加 8 槽守卫扫描。把该路径节食为：namespace 级 SimtMagicDiv/SimtMagicMod（Granlund-Montgomery 窄域 no-fixup 编码，2 的幂用 shift/mask 自判别；host 暴力 127,674,604 对抗检查 0 失配）+ 每线程一次构建的 active-dim 列表 act1/act2 + 单活跃维直表达式 + SCALAR 操作数预读。accepted：增量 1.0294x（目标块 1.0441x：c13 1.0541x、c20 1.0379x，与 r3 隔离 A/B 复现差 <0.2%），8 个 per-route control 最差 c15 0.9775x 在带内，累计 1.8736x；官方最终累计 1.8991x、零回归、官方分 62.64→70.01。

## 1. 原理

偏移 decompose 的除数在 kernel 生命周期内是常量（来自 tiling 表），运行时整除可用 Granlund-Montgomery magic 常数化为 mul/shift；broadcast 使多数维 stride=0（不活跃），把 8 槽全扫描换成每线程一次构建的 active-dim 列表；单活跃维可直表达式短路；SCALAR 臂的 x2 值每核只读一次。这些 prologue 状态在 512-lane 寄存器预算内为净收益——同一组合在 1024-lane 臂 spill 为净损失（见 simt-vf-prologue-enrichment-register-pressure），机制收益由 instantiation 宽度决定。

实现机制：op_kernel/gcd_simt.h 内：(1) SimtMagicDiv/SimtMagicMod helper（窄域 no-fixup 形态，pow2 经 mm bit31==0 自判别走 shift/mask）；(2) GcdSimtKernelInt64 prologue 每线程一次构建 active-dim 列表 act1/act2（broadcast 维剔除）；(3) 单活跃维走直表达式；(4) SCALAR 臂 x2 预读。编辑作用域仅 gcd_simt.h 单文件，T1/T2 体与父逐字节一致（机械验证）。补丁文本逐字取自 r3 保留 patch 的 int64 hunk。

## 2. 性能问题模式

- 优化目标：消除 SIMT direct-GM 载体 int64 臂残余的 per-element 偏移算术税（运行时 div/mod + 守卫扫描），把 broadcast decompose 的每元素成本压到乘/移位级。
- 适用数据流：整核 SIMT direct-GM 载体 int64/512-lane 臂的 GENERAL-broadcast per-element 偏移计算段：运行时整除/取模 + 8 槽守卫扫描 → 常数化除法 + 活跃维列表
- Feature signature：`{"bottleneck": ["runtime-div-mod", "guard-scan", "per-element-offset-arithmetic"], "dtypes": ["int64"], "pattern": "simt-offset-arithmetic-diet-512lane", "structure": ["magic-division", "active-dim-list", "single-active-dim-direct", "scalar-pre-read", "launch-bound-512"]}`

## 3. 正确性红线

- 在更宽 lane 臂上复用同款 prologue 会寄存器 spill（见负向边界卡）
- magic 常数域外静默错值：必须 host 对抗检查前置
- TU 漂移累积：多个薄机制叠加时未编辑路径的 -2% 级漂移可能突破 0.95 硬线

资源与硬件约束：

- 薄收益机制（~1.03x 级）需与 max_rounds 预算权衡：优先在头部 headroom case 上使用
- header 增行数（本例 +152 行）会带来 c15 型 TU 漂移（-2.2%），属机制的常设成本，须记录不掩盖
- probe/measure 双通道的 canary（SAME 臂）方差在单-digit-us 级，读数按带内处理

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- SIMT direct-GM 载体已 accepted 且其 GENERAL 偏移含运行时 div/mod + 固定槽宽守卫扫描
- 目标臂 LAUNCH_BOUND 宽度的寄存器余量经 probe 验证可容纳 prologue 状态（512-lane 实证为正；1024-lane 实证为负）
- magic 常数在 host 侧经暴力对抗检查（覆盖角点/包络值）后才上设备
- 每 route 有 gate 排除的 control case 监控 TU 漂移（[0.97,1.03] 带）

不适用：

- 不得把同款 prologue 富集加到 1024-lane 臂（r3 证伪）
- divisor 域超出窄域 no-fixup 编码适用域时必须换带 fixup 形态或放弃（不得静默截断）
- 编辑不得越出目标臂文件/函数（跨臂泄漏由 control 块检测）

## 5. 实施步骤

1. 从上一轮保留 patch 中提取目标臂 hunk（若该机制曾在更宽 lane 臂被证伪）
2. host 暴力对抗检查 magic-div 编码（角点 + 随机域）
3. 单文件最小编辑：magic helper + active-dim 列表 + 单活跃维直表达式 + SCALAR 预读，不动其他臂文本
4. probe 验证目标为正且 canary 带内后再全量 measure，control 块裁决 TU 漂移

## 6. LLM 前置问题

- 目标实现是否满足：SIMT direct-GM 载体已 accepted 且其 GENERAL 偏移含运行时 div/mod + 固定槽宽守卫扫描？
- 目标实现是否满足：目标臂 LAUNCH_BOUND 宽度的寄存器余量经 probe 验证可容纳 prologue 状态（512-lane 实证为正；1024-lane 实证为负）？
- 目标实现是否满足：magic 常数在 host 侧经暴力对抗检查（覆盖角点/包络值）后才上设备？
- 是否命中排除条件：不得把同款 prologue 富集加到 1024-lane 臂（r3 证伪）？

## 7. 验收标准

正确性：

- verify 10/10（validation 集）golden 全过；指纹链一致（op_source 0ad1ebb744246466 / kernel 5ec20d61f846b849 / commit f4c0349，before 态正确链到 r2-accepted 父与 baseline）
- 最终 final official_eval correctness 20/20

性能：

- 增量 1.0294x（目标块 1.0441x：c13 1.0541x、c20 1.0379x，复现 r3 隔离 A/B <0.2%）；8 control 最差 c15 0.9775x（0.95 硬线内、0.97 带边缘）
- 累计 1.8736x（measure 口径）；官方最终累计 1.8991x、20/20 全改善、regressed_cases=0、官方分 62.64→70.01（+7.37）

回滚信号：

- control 块跌破 0.95 → TU 漂移超标，回退
- c13/c20 复现性破坏（与 r3 隔离 A/B 偏差 >2%）→ 环境异常，补采
- verify golden 失败 → 回退父核

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260902_124740-96739f（round=5, status=accepted）
- gcd-20260902_124740-96739f（round=5, status=accepted）

## 检索卡（短卡）

动作：把 int64 SIMT 体 per-element 的运行时 div/mod 与守卫扫描改为 magic 常数化除法加 active-dim 列表。
适用：载体 GENERAL 偏移含运行时 div/mod 与固定槽守卫扫描；512-lane 寄存器余量经 probe 验证。
限制：不得加到 1024-lane 臂（寄存器 spill）；magic 常数域外静默错值，须 host 对抗检查前置。
范围：SIMT direct-GM 载体 int64/512-lane 臂的偏移计算段
检索词：Granlund-Montgomery、SimtMagicDiv、active-dim 列表、stride-0 短路、SCALAR 预读
机会：每元素一次运行时整除加取模，外加 8 槽守卫全扫描
代价：薄收益（~1.03x 级），header 增行使未编辑路径 c15 型 TU 漂移 -2.2%
