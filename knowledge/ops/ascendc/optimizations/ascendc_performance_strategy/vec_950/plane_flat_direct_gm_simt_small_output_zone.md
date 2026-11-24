---
type: Optimization
title: 平面平坦 direct-GM SIMT 小输出 zone 门控臂
description: 对单平面欠填充的小输出 zone 用平面平坦 direct-GM SIMT：单次 asc_vf_call 交给持久线程，线程内 2 次 magic UintDiv 分解 (plane,row)。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/plane-flat-direct-gm-simt-small-output-zone.md
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
      "门控算术必须与既有臂互斥且覆盖全部形状的路由表（本轮仿真路由与实测一致）",
      "uint32 平坦寻址域覆盖校验"
    ],
    "excluded_conditions": [
      "DesHW >= 阈值的大输出形状走 per-plane 臂（本臂列驻分解多一次 plane magic-div，无收益）",
      "planeNum<2 的形状保留原路径（本轮未覆盖，未验证）"
    ],
    "required_conditions": [
      "planeNum>=2 且 DesHW < coreNum*每核 VF 线程数（单平面欠填充，需要跨平面填充线程）",
      "既有大输出 direct-GM 臂已验证（本卡是同族互补臂，不是替代）",
      "lerp 结合序与坐标 fp32 表达式与原实现一致"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "6fb5a3df41f47a0e3b0704694e7c8dd103efb71d4b426828dbb9698ba582c474",
      "decision_sha256": "580f20d1f2215c898ebe6aea67067e016f96b9513b5795c83affe20a03b92c2d",
      "operator_class": "fused-composite",
      "performance_sha256": "6bc0ba44f013c64f7d7901d48d0424394803ad3d2de1ce2a7fd66759b5cc41d5",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "1d93de8e73da58d6a6359597cd5d9fe18ae118f8a2b5e95a95bbbb21a1dfb554",
      "verify_sha256": "8e99e0bafe28077eb813178fffc194b278e501a5e7e079a66ac7cfd435e39c9d"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-row-block-launch-sync-floor",
      "small-output-underfill"
    ],
    "dtypes": [
      "fp32",
      "fp16",
      "bf16"
    ],
    "pattern": "plane-flat-direct-gm-simt",
    "structure": [
      "flat-2-magic-div-plane-row-decompose",
      "kernel-side-zone-gate-complement",
      "no-ub-staging"
    ]
  },
  "generality": "op_class",
  "id": "VAL-RB-PLANE-FLAT-DIRECTGM",
  "implementation_steps": [
    "确认小输出 zone 集合（DesHW<阈值 ∧ planeNum>=2）与逐行迭代地板的 profiling 证据（墙钟=最差核迭代数×每迭代成本）",
    "实现平坦索引 2-magic-div (plane,row) 分解 + 行内列推进的 direct-GM SIMT 变体",
    "kernel 侧门控，既有路径字节一致；路由表全形状仿真核对",
    "op_summary 验证 mte2/mte3 塌缩签名（与 UB-staging 签名区分），control case 验证无外溢"
  ],
  "intent": "消除小输出 zone 里最差核串行行迭代数 × 每迭代 launch/sync+staging 成本构成的墙钟地板",
  "mechanism": "kernel 侧新增 flat direct-GM SIMT path：平坦输出索引 → 2 次 magic UintDiv 分解 (plane,row)，行内列联推进，uint32 寻址，4 次标量 GM load + 原结合序 lerp + 1 次 GM store；门控 planeNum>=2 且 DesHW<coreNum*1024；三个既有路径（大输出 per-plane 臂、UB-staged 回退）编译保留且字节一致。",
  "name": "平面平坦 direct-GM SIMT 小输出 zone 门控臂",
  "operator_class": "fused-composite",
  "operator_scope": "坐标驱动重采样/gather 类算子：输出平面 DesHW < coreNum*每核线程数（单平面线程欠填充）且 planeNum>=2 的小输出形状 zone",
  "principle": "小输出 zone 的墙钟 ≈ 最差核串行行迭代数 × 每迭代固定成本；把逐行迭代合并为一次 VF 调用的平坦遍历即可移除该地板。与 per-plane 结构不同，这里以 (plane,row) 两次 magic-div 分解换取跨平面填充线程，避免单平面欠填充。",
  "related_anti_patterns": [
    "per-row-pipebarrier-sync"
  ],
  "risks": [
    "planeNum==1 或极端窄行形状未验证，不得默认受益",
    "平坦分解多出的 plane magic-div 在大输出形状上是纯开销（必须门控互斥）"
  ],
  "slug": "plane-flat-direct-gm-simt-small-output-zone",
  "summary": "对小输出 zone（单平面无法填满 VF 线程）用平面平坦索引变体消除同样的逐行 launch/sync 地板：单次 asc_vf_call 把整个输出的平坦索引空间交给持久线程，线程内 2 次 magic-number UintDiv 分解 (plane,row) 后行内列推进，fp32 坐标表达式与原实现一致，direct-GM 标量 load/lerp/store；kernel 侧门控于 planeNum>=2 且 DesHW<阈值，大输出 per-plane 臂与其他已接受路径保持字节一致。",
  "verification": {
    "correctness": [
      "verify 全 case 通过（本轮 20/20）",
      "既有三个路径字节一致，control case 增量 ~1.0x 无外溢"
    ],
    "performance": [
      "incremental total_speedup 1.3014（目标形状分别 6.93x / 4.65x / 1.83x，0 回归）；命中形状 aiv_mte2 从 ~60us 塌缩至 <1us、mte3 归零、scalar 时长塌缩（机制 engage 直接证据）",
      "官方路径抽查复测确认目标形状收益存在于官方评测路径（非 measure 伪影），且对主线参考锚点为净提升"
    ],
    "rollback_signals": [
      "任一门控 case 增量 <1.0；control 路径 pipeline 签名变化说明外溢"
    ]
  }
}
-->

# 性能优化策略：平面平坦 direct-GM SIMT 小输出 zone 门控臂

单一优化点：对小输出 zone（单平面无法填满 VF 线程）用平面平坦索引变体消除同样的逐行 launch/sync 地板：单次 asc_vf_call 把整个输出的平坦索引空间交给持久线程，线程内 2 次 magic-number UintDiv 分解 (plane,row) 后行内列推进，fp32 坐标表达式与原实现一致，direct-GM 标量 load/lerp/store；kernel 侧门控于 planeNum>=2 且 DesHW<阈值，大输出 per-plane 臂与其他已接受路径保持字节一致。

## 1. 原理

小输出 zone 的墙钟 ≈ 最差核串行行迭代数 × 每迭代固定成本；把逐行迭代合并为一次 VF 调用的平坦遍历即可移除该地板。与 per-plane 结构不同，这里以 (plane,row) 两次 magic-div 分解换取跨平面填充线程，避免单平面欠填充。

实现机制：kernel 侧新增 flat direct-GM SIMT path：平坦输出索引 → 2 次 magic UintDiv 分解 (plane,row)，行内列联推进，uint32 寻址，4 次标量 GM load + 原结合序 lerp + 1 次 GM store；门控 planeNum>=2 且 DesHW<coreNum*1024；三个既有路径（大输出 per-plane 臂、UB-staged 回退）编译保留且字节一致。

## 2. 性能问题模式

- 优化目标：消除小输出 zone 里最差核串行行迭代数 × 每迭代 launch/sync+staging 成本构成的墙钟地板
- 适用数据流：坐标驱动重采样/gather 类算子：输出平面 DesHW < coreNum*每核线程数（单平面线程欠填充）且 planeNum>=2 的小输出形状 zone
- Feature signature：`{"bottleneck": ["per-row-block-launch-sync-floor", "small-output-underfill"], "dtypes": ["fp32", "fp16", "bf16"], "pattern": "plane-flat-direct-gm-simt", "structure": ["flat-2-magic-div-plane-row-decompose", "kernel-side-zone-gate-complement", "no-ub-staging"]}`

## 3. 正确性红线

- planeNum==1 或极端窄行形状未验证，不得默认受益
- 平坦分解多出的 plane magic-div 在大输出形状上是纯开销（必须门控互斥）

资源与硬件约束：

- 门控算术必须与既有臂互斥且覆盖全部形状的路由表（本轮仿真路由与实测一致）
- uint32 平坦寻址域覆盖校验

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- planeNum>=2 且 DesHW < coreNum*每核 VF 线程数（单平面欠填充，需要跨平面填充线程）
- 既有大输出 direct-GM 臂已验证（本卡是同族互补臂，不是替代）
- lerp 结合序与坐标 fp32 表达式与原实现一致

不适用：

- DesHW >= 阈值的大输出形状走 per-plane 臂（本臂列驻分解多一次 plane magic-div，无收益）
- planeNum<2 的形状保留原路径（本轮未覆盖，未验证）

## 5. 实施步骤

1. 确认小输出 zone 集合（DesHW<阈值 ∧ planeNum>=2）与逐行迭代地板的 profiling 证据（墙钟=最差核迭代数×每迭代成本）
2. 实现平坦索引 2-magic-div (plane,row) 分解 + 行内列推进的 direct-GM SIMT 变体
3. kernel 侧门控，既有路径字节一致；路由表全形状仿真核对
4. op_summary 验证 mte2/mte3 塌缩签名（与 UB-staging 签名区分），control case 验证无外溢

## 6. LLM 前置问题

- 目标实现是否满足：planeNum>=2 且 DesHW < coreNum*每核 VF 线程数（单平面欠填充，需要跨平面填充线程）？
- 目标实现是否满足：既有大输出 direct-GM 臂已验证（本卡是同族互补臂，不是替代）？
- 目标实现是否满足：lerp 结合序与坐标 fp32 表达式与原实现一致？
- 是否命中排除条件：DesHW >= 阈值的大输出形状走 per-plane 臂（本臂列驻分解多一次 plane magic-div，无收益）？

## 7. 验收标准

正确性：

- verify 全 case 通过（本轮 20/20）
- 既有三个路径字节一致，control case 增量 ~1.0x 无外溢

性能：

- incremental total_speedup 1.3014（目标形状分别 6.93x / 4.65x / 1.83x，0 回归）；命中形状 aiv_mte2 从 ~60us 塌缩至 <1us、mte3 归零、scalar 时长塌缩（机制 engage 直接证据）
- 官方路径抽查复测确认目标形状收益存在于官方评测路径（非 measure 伪影），且对主线参考锚点为净提升

回滚信号：

- 任一门控 case 增量 <1.0；control 路径 pipeline 签名变化说明外溢

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-pipebarrier-sync

- resize_bilinear-20260902_032419-3fd855（round=4, status=accepted）

## 检索卡（短卡）

动作：对单平面欠填充的小输出 zone 用平面平坦 direct-GM SIMT：单次 asc_vf_call 交给持久线程，线程内 2 次 magic UintDiv 分解 (plane,row)。
适用：planeNum>=2 且 DesHW < coreNum*每核 VF 线程数、既有大输出 direct-GM 臂已验证。
限制：planeNum<2 或极端窄行未验证不得默认受益；多出的 plane magic-div 在大输出上是纯开销，门控须互斥。
范围：坐标驱动重采样/gather 类算子的小输出 zone 门控臂。
检索词：asc_vf_call、持久线程、magic UintDiv、grid-stride、uint32 寻址、direct-GM
机会：小输出 zone 墙钟 ≈ 最差核行迭代数 × 每迭代 launch/sync+staging 成本。
