---
type: Optimization
title: 形状门控 direct-GM SIMT 坐标一次计算数据流（大输出平面 zone）
description: 把逐行块 UB-staged 重采样迭代改为 kernel 侧按 DesHW 门控的持久 direct-GM SIMT 流，坐标每像素一次并跨 plane 复用。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/shape-gated-direct-gm-simt-coordinate-once.md
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
      "uint32 平坦寻址域必须覆盖 N*C*H*W 上限，超限形状回退原路径",
      "门控算术必须对全部形状的路由表做仿真核对，未命中路径与基线字节一致"
    ],
    "excluded_conditions": [
      "DesHW < 阈值（线程欠填充）：不得用本 per-plane 结构，需平面平坦变体（见 plane-flat-direct-gm-simt-small-output-zone 卡）",
      "host tiling 库在部署环境为陈旧 vendor 版本时，host 侧路由编辑运行时 inert：门控必须放 kernel 侧（本轮实测边界）"
    ],
    "required_conditions": [
      "输出平面 DesHW >= coreNum*每核 VF 线程数（满线程填充），且 src/des 平面尺寸相异（存在重采样计算）",
      "SIMT VF 标量链正确性已独立验证，lerp 结合序与原实现逐位一致",
      "kernel 侧能读取形状参数做门控（host tiling 不可依赖）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "7f2fc633fb1211e68a810d77436924ced700935c1ed9363626e1d0c4027c22c1",
      "decision_sha256": "fe9766581914a8af453a5d1d6bd4b07f563b68406ef6d89308fb05b4d15452f8",
      "operator_class": "fused-composite",
      "performance_sha256": "3271a9aebcc8229798cf542bd37303a261959523fb28d83bfeeb2db920c60b54",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ae4eb834188628d64c27c1c84a188d62ac1eb7d09be48554edba9f64c34efe16",
      "verify_sha256": "2bddd45acb4a6dceeae8dad87eef1de0104e156945c7111a44d7c21cfbbe474a"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-row-block-launch-sync-floor",
      "ub-staging-roundtrip",
      "aiv-scalar-bound"
    ],
    "dtypes": [
      "fp32",
      "fp16",
      "bf16"
    ],
    "pattern": "shape-gated-direct-gm-simt-coordinate-once",
    "structure": [
      "per-plane-grid-stride",
      "inner-plane-loop-coordinate-reuse",
      "kernel-side-shape-gate",
      "magic-div-2-per-pixel"
    ]
  },
  "generality": "op_class",
  "id": "VAL-RB-SHAPE-GATED-DIRECTGM",
  "implementation_steps": [
    "从参考/主线实现定位 SIMT_HW 数据流结构与 host tiling 的路由条件（阈值=coreNum*线程数）",
    "把门控移植到 kernel 侧（形状参数直接判定），非命中 zone 保持原路径字节一致",
    "实现每像素 2 次 magic UintDiv 分解 + 坐标一次计算 + 线程内 plane 循环复用（uint32 寻址）",
    "用 op_summary 的 aiv_mte2/aiv_mte3 塌缩签名验证机制 engage，用 control case 字节一致验证无外溢"
  ],
  "intent": "消除逐 (plane,row,ow-block) 迭代的 launch/sync 固定成本、UB 往返搬运与逐元素重复坐标/地址计算",
  "mechanism": "移植参考实现的 SIMT_HW 数据流：门控条件在 kernel 侧按 DesHW 阈值与 src/des HW 是否相异判定；命中后单次 asc_vf_call，1024 持久线程列驻 grid-stride 遍历一个平面的 DesHW 空间，2 次 magic UintDiv 分解 (H,W)，fp32 坐标每像素一次，线程内 N*C plane 循环复用坐标做 4 次标量 GM load + 相同结合序 lerp + 1 次 GM store；非命中 zone 走原 UB-staged 路径保持字节一致。",
  "name": "形状门控 direct-GM SIMT 坐标一次计算数据流（大输出平面 zone）",
  "operator_class": "fused-composite",
  "operator_scope": "坐标驱动重采样/gather 类算子（双线性 resize 等）：逐行块 UB-staged 管线的每迭代 launch/sync + staging 成本主导、且输出平面足够大的形状 zone",
  "principle": "标量受限的 UB-staged 重采样 kernel 里，真正的瓶颈是逐元素坐标+地址标量流与每行块同步；把坐标计算降为每像素一次并跨 plane 复用（时间换结构），同时去掉 UB staging（消除每迭代同步与搬运），两者叠加才产生量级收益。只做其一（朴素 flat 重写，见 naive-flat-direct-gm-simt-per-element-decompose-no-gain 卡）无收益。",
  "related_anti_patterns": [
    "per-row-pipebarrier-sync",
    "per-element-mte-descriptor-spray"
  ],
  "risks": [
    "小输出形状线程欠填充导致该 zone 回归（必须门控排除）",
    "host 侧 tiling 编辑在陈旧 vendor tiling 库环境运行时 inert，路由意图不生效",
    "坐标/结合序偏离原实现会破坏逐位精确（mare 必须==0 的 dtype 直接失败）"
  ],
  "slug": "shape-gated-direct-gm-simt-coordinate-once",
  "summary": "当输出平面元素数 DesHW=hOut*wOut >= coreNum*每核线程数（64 核 × 1024）时，kernel 侧门控路由到持久 direct-GM SIMT 数据流：每核一次 asc_vf_call，线程 grid-stride 遍历单个输出平面的 DesHW 空间，每像素仅 2 次 magic-number UintDiv 分解 (oh,ow)，H/W 采样坐标每像素计算一次，随后线程内循环全部 N*C 平面复用同一坐标（uint32 寻址）；小输出 zone 保留原 UB-staged 路径不动。消除逐行块 launch/sync 地板与 UB 往返后，标量管道从逐元素地址计算降为每像素一次，收益才兑现。",
  "verification": {
    "correctness": [
      "verify 全 case 通过（本轮 20/20，mare==0 dtype 逐位精确）",
      "非命中 zone 与基线 control case 字节一致（增量比 ~1.0x 且 pipeline 签名不变）"
    ],
    "performance": [
      "incremental total_speedup 2.3267（验证集 6/8 case 提升 1.55-5.82x，0 回归）；命中 case aiv_mte2 从 28-105us 塌缩至 ~0.5-1.0us、mte3 ~0，UB-zone control 保留 staging 签名（机制 engage 直接证据）",
      "参考锚点：多数命中 case 官方路径耗时不高于主线参考实现"
    ],
    "rollback_signals": [
      "任一门控 case 增量 <1.0 或 control 回归超 max_case_regression；aiv_mte2 未塌缩说明未 engage"
    ]
  }
}
-->

# 性能优化策略：形状门控 direct-GM SIMT 坐标一次计算数据流（大输出平面 zone）

单一优化点：当输出平面元素数 DesHW=hOut*wOut >= coreNum*每核线程数（64 核 × 1024）时，kernel 侧门控路由到持久 direct-GM SIMT 数据流：每核一次 asc_vf_call，线程 grid-stride 遍历单个输出平面的 DesHW 空间，每像素仅 2 次 magic-number UintDiv 分解 (oh,ow)，H/W 采样坐标每像素计算一次，随后线程内循环全部 N*C 平面复用同一坐标（uint32 寻址）；小输出 zone 保留原 UB-staged 路径不动。消除逐行块 launch/sync 地板与 UB 往返后，标量管道从逐元素地址计算降为每像素一次，收益才兑现。

## 1. 原理

标量受限的 UB-staged 重采样 kernel 里，真正的瓶颈是逐元素坐标+地址标量流与每行块同步；把坐标计算降为每像素一次并跨 plane 复用（时间换结构），同时去掉 UB staging（消除每迭代同步与搬运），两者叠加才产生量级收益。只做其一（朴素 flat 重写，见 naive-flat-direct-gm-simt-per-element-decompose-no-gain 卡）无收益。

实现机制：移植参考实现的 SIMT_HW 数据流：门控条件在 kernel 侧按 DesHW 阈值与 src/des HW 是否相异判定；命中后单次 asc_vf_call，1024 持久线程列驻 grid-stride 遍历一个平面的 DesHW 空间，2 次 magic UintDiv 分解 (H,W)，fp32 坐标每像素一次，线程内 N*C plane 循环复用坐标做 4 次标量 GM load + 相同结合序 lerp + 1 次 GM store；非命中 zone 走原 UB-staged 路径保持字节一致。

## 2. 性能问题模式

- 优化目标：消除逐 (plane,row,ow-block) 迭代的 launch/sync 固定成本、UB 往返搬运与逐元素重复坐标/地址计算
- 适用数据流：坐标驱动重采样/gather 类算子（双线性 resize 等）：逐行块 UB-staged 管线的每迭代 launch/sync + staging 成本主导、且输出平面足够大的形状 zone
- Feature signature：`{"bottleneck": ["per-row-block-launch-sync-floor", "ub-staging-roundtrip", "aiv-scalar-bound"], "dtypes": ["fp32", "fp16", "bf16"], "pattern": "shape-gated-direct-gm-simt-coordinate-once", "structure": ["per-plane-grid-stride", "inner-plane-loop-coordinate-reuse", "kernel-side-shape-gate", "magic-div-2-per-pixel"]}`

## 3. 正确性红线

- 小输出形状线程欠填充导致该 zone 回归（必须门控排除）
- host 侧 tiling 编辑在陈旧 vendor tiling 库环境运行时 inert，路由意图不生效
- 坐标/结合序偏离原实现会破坏逐位精确（mare 必须==0 的 dtype 直接失败）

资源与硬件约束：

- uint32 平坦寻址域必须覆盖 N*C*H*W 上限，超限形状回退原路径
- 门控算术必须对全部形状的路由表做仿真核对，未命中路径与基线字节一致

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 输出平面 DesHW >= coreNum*每核 VF 线程数（满线程填充），且 src/des 平面尺寸相异（存在重采样计算）
- SIMT VF 标量链正确性已独立验证，lerp 结合序与原实现逐位一致
- kernel 侧能读取形状参数做门控（host tiling 不可依赖）

不适用：

- DesHW < 阈值（线程欠填充）：不得用本 per-plane 结构，需平面平坦变体（见 plane-flat-direct-gm-simt-small-output-zone 卡）
- host tiling 库在部署环境为陈旧 vendor 版本时，host 侧路由编辑运行时 inert：门控必须放 kernel 侧（本轮实测边界）

## 5. 实施步骤

1. 从参考/主线实现定位 SIMT_HW 数据流结构与 host tiling 的路由条件（阈值=coreNum*线程数）
2. 把门控移植到 kernel 侧（形状参数直接判定），非命中 zone 保持原路径字节一致
3. 实现每像素 2 次 magic UintDiv 分解 + 坐标一次计算 + 线程内 plane 循环复用（uint32 寻址）
4. 用 op_summary 的 aiv_mte2/aiv_mte3 塌缩签名验证机制 engage，用 control case 字节一致验证无外溢

## 6. LLM 前置问题

- 目标实现是否满足：输出平面 DesHW >= coreNum*每核 VF 线程数（满线程填充），且 src/des 平面尺寸相异（存在重采样计算）？
- 目标实现是否满足：SIMT VF 标量链正确性已独立验证，lerp 结合序与原实现逐位一致？
- 目标实现是否满足：kernel 侧能读取形状参数做门控（host tiling 不可依赖）？
- 是否命中排除条件：DesHW < 阈值（线程欠填充）：不得用本 per-plane 结构，需平面平坦变体（见 plane-flat-direct-gm-simt-small-output-zone 卡）？

## 7. 验收标准

正确性：

- verify 全 case 通过（本轮 20/20，mare==0 dtype 逐位精确）
- 非命中 zone 与基线 control case 字节一致（增量比 ~1.0x 且 pipeline 签名不变）

性能：

- incremental total_speedup 2.3267（验证集 6/8 case 提升 1.55-5.82x，0 回归）；命中 case aiv_mte2 从 28-105us 塌缩至 ~0.5-1.0us、mte3 ~0，UB-zone control 保留 staging 签名（机制 engage 直接证据）
- 参考锚点：多数命中 case 官方路径耗时不高于主线参考实现

回滚信号：

- 任一门控 case 增量 <1.0 或 control 回归超 max_case_regression；aiv_mte2 未塌缩说明未 engage

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-pipebarrier-sync, per-element-mte-descriptor-spray

- resize_bilinear-20260902_032419-3fd855（round=3, status=accepted）

## 检索卡（短卡）

动作：把逐行块 UB-staged 重采样迭代改为 kernel 侧按 DesHW 门控的持久 direct-GM SIMT 流，坐标每像素一次并跨 plane 复用。
适用：DesHW>=coreNum*每核 VF 线程数，且 src/des 平面尺寸相异。
限制：DesHW<阈值不得用 per-plane 结构；host tiling 在陈旧 vendor 库下 inert；坐标偏离破坏逐位精确。
范围：坐标驱动重采样/gather 类算子的行块 UB-staged 管线
检索词：asc_vf_call、grid-stride、magic UintDiv、kernel 侧门控、uint32 寻址、plane 复用
机会：逐行块 launch/sync 地板与 UB 往返主导，标量管道逐元素算坐标
代价：小输出形状线程欠填充会回归该 zone，必须门控排除
