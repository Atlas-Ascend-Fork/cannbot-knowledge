---
type: Optimization
title: 预扫相位消除：编译期 dtype 门控 + 单 dTile 融合 + 无标量循环的缩放决策
description: 按 dtype 编译期门控整段跳过非 fp32 的 prescan，单 dTile 时把预扫融合进主 Compute，标量缩放决策换 VF 直读与 2 的幂梯子。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/prescan-phase-elimination.md
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
      "dtype 门控必须由编译期 if constexpr 承载（非 fp32 跳过整段 prescan），并由数据流证明删除位级等价，不可用运行期分支替代",
      "缩放决策若用浮点除子替代位精确 2 的幂构造，须先确认该路径的 MERE/MARE 余量——本 run round_01 浮点除子因 case11 MARE 19.17 超阈被精度门拒绝，round_02 改位级精确 2 的幂梯子后才通过",
      "fp32 单 dTile 融合只能复用已 DeQue 的 y tile，不得为省一次拷贝改变 DeQue 时机或队列语义"
    ],
    "excluded_conditions": [
      "prescan 结果被非缩放用途消费时不适用：删除前提是 doScale 恒 false 或该结果仅用于缩放决策",
      "dTileNum > 1 的 fp32 路径不适用融合分量（第二次 GM->UB y 拷贝无法省），仅 dtype 门控与决策改造可用",
      "kernel-B 等未触碰域须在对照中保持 ±噪声带内，否则收益归因不成立"
    ],
    "required_conditions": [
      "存在可编译期判定的 dtype 分派，且非该 dtype 路径上 prescan 为可证死工作（本 run：ScaleYRowsA/doScale 为 fp32-only if constexpr，fp16 永不可能溢出 fp32 累加器，bf16 缩放已是 no-op）",
      "批量小（预扫相位固定开销占比高，本 run 单批 ~775ns~800ns 的 barrier+issue 开销），逐批重复付出",
      "存在 dTileNum==1 的单 tile 融合机会（预扫 max|y| 可直接从已 DeQue 的 y tile 算出，无需二次 GM->UB 拷贝）",
      "算子存在同 run 内的未触碰对照组（本 run kernel-B 13/20 case）用于收益归因"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 14.3608,
      "before_us": 19.394,
      "operator": "sigmoid_cosine_similarity",
      "operator_class": "fused-composite",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": ["ses_f7931da1bffe6K775UwNBH0k54"],
      "speedup": 1.3505,
      "status": "accepted",
      "worst_pair_ratio": 1.3432
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "prescan-phase-fixed-overhead",
      "redundant-gm-to-ub-recopys",
      "scalar-emission-loop",
      "mte2-scalar-coupled"
    ],
    "pattern": "prescan-phase-elimination",
    "structure": [
      "compile-time-dtype-gate",
      "single-dtile-fusion",
      "fixup-loop-free-scaling-decision",
      "per-dtype-dead-work-removal"
    ]
  },
  "generality": "op_class",
  "id": "SCS-PRESCAN-PHASE-ELIMINATION",
  "implementation_steps": [
    "用编译期 if constexpr 按 dtype 门控整段 prescan：非 fp32 跳过 CopyInY 循环 + MaxAbsRowsA + ReduceMaxScaleA + V_S/S_V barrier 对 + fixup 决策（由数据流证明对非 fp32 位级等价）",
    "fp32 单 dTile（dTileNum==1）时把预扫 max|y| 融合进主 Compute，直接从已 DeQue 的 y tile 计算，消除第二次 GM->UB y 拷贝；barrier 收敛为同一对 V_S/S_V",
    "删除所有路径上的标量 BuildPow2ScaleA <=256 次发射循环，缩放决策改为直读 VF 全局 max（maxSlot[0]，round-2 helper）",
    "用位级精确的 BuildPow2ScaleVF 2 的幂梯子（8 步 Compare/Select 二分）替代浮点除子构造缩放因子——浮点除子版本（round_01）因 MARE 超阈被精度门拒绝",
    "保留 +Inf 的全局 veto 语义（doScale=false 原生路径原样不动）"
  ],
  "intent": "消除 kernel-A 预扫相位在两类情形下的成本：对非 fp32 是可证死工作（整段删除），对 fp32 单 dTile 是重复拷贝（融合进主 Compute）；并把每批 ≤256 次标量发射的 fixup 决策循环改为 VF 直读，使大数量级/NaN 的 fp32 批次不再每 kernel 付出 ~160us 的标量循环。",
  "mechanism": "prescan-phase-elimination 三个正交分量：(a) 编译期 dtype 门控——非 fp32 整段跳过 prescan（CopyInY 循环 + MaxAbsRowsA + ReduceMaxScaleA + V_S/S_V barrier 对 + fixup 决策），因为 ScaleYRowsA/doScale 是 fp32-only（if constexpr），fp16 永不溢出 fp32 累加器、bf16 缩放本就是 no-op，故对所有非 fp32 输入位级等价；(b) fp32 单 dTile 融合——dTileNum==1 时预扫 max|y| 从已 DeQue 的 y tile 内计算，省去第二次 GM->UB y 拷贝，barrier 收敛为同一对 V_S/S_V；(c) 无 fixup 循环的缩放决策——所有路径上删除标量 BuildPow2ScaleA ≤256 次发射循环，改用位级精确的 BuildPow2ScaleVF 2 的幂梯子（8 步 Compare/Select 二分），+Inf 保留原全局 veto。",
  "name": "预扫相位消除：编译期 dtype 门控 + 单 dTile 融合 + 无标量循环的缩放决策",
  "operator_class": "fused-composite",
  "operator_scope": "带预扫（prescan）相位的融合类算子：预扫存在 compile-time 可判定的 dtype 死工作域、或单 tile 情形下可从主 Compute 已 DeQue 数据复用、且有每批重复的标量 fixup 发射循环",
  "principle": "预扫相位的成本是逐批固定开销（拷贝发射 + 归约 + barrier 对 + 决策），批量小时占优。削减有三条正交路径：按 dtype 在编译期删掉可证死工作的整段、把单 tile 情形的预扫融合进主 Compute 消除重复拷贝、把逐批标量发射循环换成 VF 直读。第一条要求编译期可分派 + 数据流可证死，第二条要求预扫输入已被主循环 DeQue，第三条要求缩放因子的位精确构造可由纯 VF 指令完成（浮点除子会破坏精度护栏）。",
  "related_anti_patterns": [],
  "risks": [
    "缩放因子构造方式直接决定精度门是否通过：浮点除子（round_01）case11 MARE 19.17 超阈失败，必须用位级精确 2 的幂梯子",
    "分量 (c) 改变缩放舍入语义（≤1e-7 相对）时，需确认 MERE 预算（本 run 0.02，5 个数量级余量）覆盖",
    "混合 NaN + 有限 >1e12 的 lane 会走缩放路径（NaN lane 仍为 NaN），与纯 NaN case（case13）语义等价但需在验收中显式确认"
  ],
  "slug": "prescan-phase-elimination",
  "summary": "消除 kernel-A 预扫相位：非 fp32 由编译期 if constexpr 整段跳过（在 fp32-only 缩放的约束下位级等价）、fp32 单 dTile 时把预扫 max|y| 融合进主 Compute 消除第二次 GM->UB 拷贝、并删除每批 ≤256 次标量 BuildPow2ScaleA 发射循环改用 VF 直读 + 位级精确 2 的幂梯子。kernel geomean 19.394→14.3608us（1.3505x），case11 11.24x / case13 8.61x / case14 2.12x / case19 1.31x / case9 1.32x / case20 1.17x，kernel-B 对照 13 case 全部在 ±1.1% 噪声带内。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（位级精确 2 的幂缩放，无舍入语义变化）",
      "round_01 浮点除子版本被精度门拒绝（case11 MARE 19.17 超阈），已归档；round_02 改位级精确梯子后通过",
      "缩放因子的 2 的幂构造逐位精确，+Inf 全局 veto 语义保留"
    ],
    "performance": [
      "10 对同 shape / provenance clean / 交替均衡 / 相关性明确的外层 msprof device Task Duration 配对校验全部通过",
      "geomean 19.394→14.3608us（speedup 1.3505，35.05%），最小对 1.3432",
      "kernel-B 对照组 13 case 全部在 ±1.1% 噪声带内（证伪收益外溢）"
    ],
    "rollback_signals": [
      "缩放路径 MARE/MERE 超阈（浮点构造的自然后果）",
      "dtype 门控删除在非 fp32 路径上不再位级等价",
      "kernel-B 或其它未触碰域出现超出噪声带的回退",
      "单 dTile 融合改变 DeQue 时机导致队列/精度异常"
    ]
  }
}
-->

# 性能优化策略：预扫相位消除：编译期 dtype 门控 + 单 dTile 融合 + 无标量循环的缩放决策

消除 kernel-A 预扫相位：非 fp32 由编译期 if constexpr 整段跳过（在 fp32-only 缩放的约束下位级等价）、fp32 单 dTile 时把预扫 max|y| 融合进主 Compute 消除第二次 GM->UB 拷贝、并删除每批 ≤256 次标量 BuildPow2ScaleA 发射循环改用 VF 直读 + 位级精确 2 的幂梯子。kernel geomean 19.394→14.3608us（1.3505x）。

## 1. 原理

预扫相位的成本是逐批固定开销（拷贝发射 + 归约 + barrier 对 + 决策），批量小时占优。削减有三条正交路径：按 dtype 在编译期删掉可证死工作的整段、把单 tile 情形的预扫融合进主 Compute 消除重复拷贝、把逐批标量发射循环换成 VF 直读。第一条要求编译期可分派 + 数据流可证死，第二条要求预扫输入已被主循环 DeQue，第三条要求缩放因子的位精确构造可由纯 VF 指令完成（浮点除子会破坏精度护栏）。

实现机制：prescan-phase-elimination 三个正交分量：(a) 编译期 dtype 门控——非 fp32 整段跳过 prescan（CopyInY 循环 + MaxAbsRowsA + ReduceMaxScaleA + V_S/S_V barrier 对 + fixup 决策），因为 ScaleYRowsA/doScale 是 fp32-only（if constexpr），fp16 永不溢出 fp32 累加器、bf16 缩放本就是 no-op，故对所有非 fp32 输入位级等价；(b) fp32 单 dTile 融合——dTileNum==1 时预扫 max|y| 从已 DeQue 的 y tile 内计算，省去第二次 GM->UB y 拷贝，barrier 收敛为同一对 V_S/S_V；(c) 无 fixup 循环的缩放决策——所有路径上删除标量 BuildPow2ScaleA ≤256 次发射循环，改用位级精确的 BuildPow2ScaleVF 2 的幂梯子（8 步 Compare/Select 二分），+Inf 保留原全局 veto。

## 2. 性能问题模式

- 优化目标：消除 kernel-A 预扫相位在两类情形下的成本：对非 fp32 是可证死工作（整段删除），对 fp32 单 dTile 是重复拷贝（融合进主 Compute）；并把每批 ≤256 次标量发射的 fixup 决策循环改为 VF 直读，使大数量级/NaN 的 fp32 批次不再每 kernel 付出 ~160us 的标量循环
- 适用数据流：带预扫（prescan）相位的融合类算子：预扫存在 compile-time 可判定的 dtype 死工作域、或单 tile 情形下可从主 Compute 已 DeQue 数据复用、且有每批重复的标量 fixup 发射循环
- Feature signature：`{"bottleneck": ["prescan-phase-fixed-overhead", "redundant-gm-to-ub-recopys", "scalar-emission-loop", "mte2-scalar-coupled"], "pattern": "prescan-phase-elimination", "structure": ["compile-time-dtype-gate", "single-dtile-fusion", "fixup-loop-free-scaling-decision", "per-dtype-dead-work-removal"]}`

## 3. 正确性红线

- 缩放因子构造方式直接决定精度门是否通过：浮点除子（round_01）case11 MARE 19.17 超阈失败，必须用位级精确 2 的幂梯子
- 分量 (c) 改变缩放舍入语义（≤1e-7 相对）时，需确认 MERE 预算（本 run 0.02，5 个数量级余量）覆盖
- 混合 NaN + 有限 >1e12 的 lane 会走缩放路径（NaN lane 仍为 NaN），与纯 NaN case（case13）语义等价但需在验收中显式确认

资源与硬件约束：

- dtype 门控必须由编译期 if constexpr 承载（非 fp32 跳过整段 prescan），并由数据流证明删除位级等价，不可用运行期分支替代
- 缩放决策若用浮点除子替代位精确 2 的幂构造，须先确认该路径的 MERE/MARE 余量——本 run round_01 浮点除子因 case11 MARE 19.17 超阈被精度门拒绝，round_02 改位级精确 2 的幂梯子后才通过
- fp32 单 dTile 融合只能复用已 DeQue 的 y tile，不得为省一次拷贝改变 DeQue 时机或队列语义

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 存在可编译期判定的 dtype 分派，且非该 dtype 路径上 prescan 为可证死工作（本 run：ScaleYRowsA/doScale 为 fp32-only if constexpr，fp16 永不可能溢出 fp32 累加器，bf16 缩放已是 no-op）
- 批量小（预扫相位固定开销占比高，本 run 单批 ~775ns~800ns 的 barrier+issue 开销），逐批重复付出
- 存在 dTileNum==1 的单 tile 融合机会（预扫 max|y| 可直接从已 DeQue 的 y tile 算出，无需二次 GM->UB 拷贝）
- 算子存在同 run 内的未触碰对照组（本 run kernel-B 13/20 case）用于收益归因

不适用：

- prescan 结果被非缩放用途消费时不适用：删除前提是 doScale 恒 false 或该结果仅用于缩放决策
- dTileNum > 1 的 fp32 路径不适用融合分量（第二次 GM->UB y 拷贝无法省），仅 dtype 门控与决策改造可用
- kernel-B 等未触碰域须在对照中保持 ±噪声带内，否则收益归因不成立

## 5. 实施步骤

1. 用编译期 if constexpr 按 dtype 门控整段 prescan：非 fp32 跳过 CopyInY 循环 + MaxAbsRowsA + ReduceMaxScaleA + V_S/S_V barrier 对 + fixup 决策（由数据流证明对非 fp32 位级等价）
2. fp32 单 dTile（dTileNum==1）时把预扫 max|y| 融合进主 Compute，直接从已 DeQue 的 y tile 计算，消除第二次 GM->UB y 拷贝；barrier 收敛为同一对 V_S/S_V
3. 删除所有路径上的标量 BuildPow2ScaleA <=256 次发射循环，缩放决策改为直读 VF 全局 max（maxSlot[0]，round-2 helper）
4. 用位级精确的 BuildPow2ScaleVF 2 的幂梯子（8 步 Compare/Select 二分）替代浮点除子构造缩放因子——浮点除子版本（round_01）因 MARE 超阈被精度门拒绝
5. 保留 +Inf 的全局 veto 语义（doScale=false 原生路径原样不动）

## 6. LLM 前置问题

- 目标实现是否满足：存在可编译期判定的 dtype 分派，且非该 dtype 路径上 prescan 为可证死工作（本 run：ScaleYRowsA/doScale 为 fp32-only if constexpr，fp16 永不可能溢出 fp32 累加器，bf16 缩放已是 no-op）？
- 目标实现是否满足：批量小（预扫相位固定开销占比高，本 run 单批 ~775ns~800ns 的 barrier+issue 开销），逐批重复付出？
- 目标实现是否满足：存在 dTileNum==1 的单 tile 融合机会（预扫 max|y| 可直接从已 DeQue 的 y tile 算出，无需二次 GM->UB 拷贝）？
- 目标实现是否满足：算子存在同 run 内的未触碰对照组（本 run kernel-B 13/20 case）用于收益归因？
- 是否命中排除条件：prescan 结果被非缩放用途消费时不适用：删除前提是 doScale 恒 false 或该结果仅用于缩放决策？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（位级精确 2 的幂缩放，无舍入语义变化）
- round_01 浮点除子版本被精度门拒绝（case11 MARE 19.17 超阈），已归档；round_02 改位级精确梯子后通过
- 缩放因子的 2 的幂构造逐位精确，+Inf 全局 veto 语义保留

性能：

- 10 对同 shape / provenance clean / 交替均衡 / 相关性明确的外层 msprof device Task Duration 配对校验全部通过
- geomean 19.394→14.3608us（speedup 1.3505，35.05%），最小对 1.3432
- kernel-B 对照组 13 case 全部在 ±1.1% 噪声带内（证伪收益外溢）

回滚信号：

- 缩放路径 MARE/MERE 超阈（浮点构造的自然后果）
- dtype 门控删除在非 fp32 路径上不再位级等价
- kernel-B 或其它未触碰域出现超出噪声带的回退
- 单 dTile 融合改变 DeQue 时机导致队列/精度异常

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-001（operator=sigmoid_cosine_similarity, status=accepted, speedup=1.3505, 19.394→14.3608us, 10 对配对）

## 检索卡（短卡）

动作：按 dtype 编译期门控整段跳过非 fp32 的 prescan，单 dTile 时把预扫融合进主 Compute，标量缩放决策换 VF 直读与 2 的幂梯子。
适用：有编译期可判定的 dtype 分派且非该 dtype 上 prescan 可证死工作、批量小（单批 ~775-800ns）。
限制：门控必须由 if constexpr 承载；缩放因子须位级精确 2 的幂梯子（浮点除子超阈被拒）；不得改 DeQue 时机。
范围：fused-composite 算子的预扫相位与缩放决策（kernel-A）。
检索词：if constexpr、MaxAbsRowsA、ReduceMaxScaleA、BuildPow2ScaleVF、DeQue、dTileNum
机会：预扫相位逐批重复付拷贝发射+归约+barrier 对+决策的固定开销。
代价：缩放决策改变舍入语义（≤1e-7 相对）须确认 MERE 预算覆盖。
