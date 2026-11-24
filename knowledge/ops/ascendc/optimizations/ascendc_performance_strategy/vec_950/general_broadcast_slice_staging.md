---
type: Optimization
title: GENERAL 广播 x2 侧搬入边界物化（模式分发 V-A / V-B / period-tile，附 done-scratch 每-slice 复位）
description: 将 GENERAL 广播从每 slice 的 V 管索引链与 UB Gather 物化，改为 x2 侧搬入边界物化。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/general-broadcast-slice-staging.md
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
      "驻留窗口容量门（per-dtype RES_CAP）决定 V-B/period-tile 分支是否可达，不得超出驻留上限",
      "done-scratch 别名约束：wzero[0] 若同时作数据与 done/gate 槽，必须每-slice 复位，否则污染下一 slice 首元素",
      "本策略只迁移 x2 侧 staging 与 done 复位，编辑面应限定在共享 KernelGcd<T> 类模板内（本 run 仅 op_kernel/gcd.h），T3 等控制臂逐字保留"
    ],
    "excluded_conditions": [
      "短 runLen 低 k 的不规则广播（每-slice 含大量不同值）——legacy Gather 成本更低，应保留作同路由结构控制，不强行套用 V-A/V-B",
      "SIMT-VF per-tile 直读队列槽的访问形态（单次 asc_vf_call 解引用 UB 足迹 >8192B 触发设备 507035）——属于独立负向边界，不属本 staging 机制",
      "SAME/SAME 同 shape 路由的载体差距与退化值地板是独立机制，不承诺由本策略修复"
    ],
    "required_conditions": [
      "elementwise kernel 含 GENERAL（多轴广播）操作数，且其值在 V 管每-slice 物化（CoordDecompose 索引链 + UB Gather 或非驻留整量 re-staging），而非在 copy-in 侧组装",
      "profiling 显示广播驻留路由 VEC_BOUND 且 aiv_vec_bank_cflt 明显高于同 dtype 的 SAME/SAME 路由（>0.01 量级），或非驻留路由 MTE2 比例偏高（整量 re-staging 放大）",
      "广播内维 stride-0 且 runLen≥256（V-A），或 x2 为单周期内维向量 / 小驻留 tile 且容量门通过（V-B / period-tile），使存在低成本的 copy-in 流式或 Duplicate 组装",
      "host tiling 可在 kernel 运行前对广播模式分类并下发分发标记"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-27",
  "evidence": [
    {
      "comparison_sha256": "e2f2867395e87889e7e8627209e24e2673047f266710f0fc7e490068348d061d",
      "decision_sha256": "3d49321ec2b481956cd731766e0c7956419ccce1644eb2435c9fbf728333a222",
      "operator_class": "broadcast",
      "performance_sha256": "5fe1f66d6da902a2909bf47b88861051dd431dab9ffd2192781073b14282666e",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "30997a1da445d2515d95f77062fe0eb92a072cb89bc1cec41758c2530e81b2d3",
      "verify_sha256": "676f95ee6eeb400c35510a6e9469562d2a8fd6609d5bb80510bf77766192d684"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "ub-bank-conflict",
      "per-slice-broadcast-assembly",
      "nonresident-restaging-amplification"
    ],
    "dtypes": [
      "int16",
      "int32",
      "int64"
    ],
    "pattern": "general-broadcast-x2-vpipe-assembly",
    "structure": [
      "general-broadcast",
      "resident-window",
      "coord-decompose-index-chain",
      "ub-gather",
      "duplicate-assembly",
      "period-tile",
      "datacopypad-streaming"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-GENERAL-BROADCAST-SLICE-STAGING",
  "implementation_steps": [
    "用 full-metrics op_summary/msprof 确认广播路由 VEC_BOUND、aiv_vec_bank_cflt 明显高于同 dtype 的 SAME/SAME 路由，并识别非驻留路由的整量 per-slice re-staging（MTE2 放大）",
    "host tiling 增加广播模式分类：内维 stride-0 且 runLen≥256 → V-A；x2=单周期内维向量或小驻留 tile（容量门通过）→ V-B；其余短 runLen 低 k → legacy",
    "V-A 实现：以 ≤2 条基址对齐 Duplicate 组装替代每-slice 索引链 + Gather",
    "V-B 实现：按整 tile mod-L 连续段 1D DataCopyPad 流式搬入；驻留且容量门通过时 Init 一次性周期平铺 + per-slice 一条 +0 Add",
    "每-slice 复位 wzero[0] done/gate scratch，消除跨 slice 泄漏",
    "保留一个 legacy-Gather 同路由 case 作结构控制；全量 case 正确性 + 稳定性 + 逐 case 落带核验，确认控制路由不变"
  ],
  "intent": "消除广播驻留/非驻留路由相对同 shape 路由的 3–4 倍结构性差距：把每-slice 的 CoordDecompose 索引链 + 字节比例 UB Gather 的 V 管成本（VEC_BOUND + UB bank 冲突）与非驻留整量 re-staging 的 MTE2 放大移出 V 管，使广播组装退化为 copy-in 侧的流式搬入或 1–2 条 Duplicate/Add 指令。",
  "mechanism": "host tiling 在运行时把 x2 侧 GENERAL 广播分类为：(V-A) 内维 stride-0 且 runLen≥256 → 每 256-slice 至多 2 个不同标量，用 2 条基址对齐 Duplicate 组装替代索引链 + Gather；(V-B) x2 为单周期内维向量 → 按整 tile mod-L 连续段 1D DataCopyPad 流式搬入，若驻留且容量门通过则在 Init 一次性周期平铺、per-slice 仅一条 +0 Add；(legacy) 短 runLen 低 k 广播保留 legacy Gather 作同路由结构控制。正确性伴修改：wzero[0] done/gate scratch 每-slice 复位，消除 done-scratch 别名（wzeroBuf_[0] 既作数据又作 done 槽）把上一 slice 泄漏污染下一 slice 首元素。",
  "name": "GENERAL 广播 x2 侧搬入边界物化（模式分发 V-A / V-B / period-tile，附 done-scratch 每-slice 复位）",
  "op": "gcd",
  "operator_class": "broadcast",
  "operator_scope": "broadcast-elementwise integer math（AIV-only 向量核，SIMD RegBase 载体，per-dtype 模板路由）：x2 侧为 GENERAL（多轴广播）操作数、且该操作数在 V 管按 slice 逐块物化（CoordDecompose 索引链 + 字节比例 UB Gather / 非驻留整量 re-staging）的 elementwise kernel",
  "principle": "广播是数据搬运问题而非计算问题：GENERAL 操作数在每-slice 经 CoordDecompose 索引链（outDimNum 维 × 每条若干向量指令）+ 字节比例 UB Gather 物化，叠加在计算轮体之上，向 V 管收取固定的 per-slice 索引税；对极小驻留窗口（≤16KB/8KB）的 64-lane Gather 还会引发 UB bank 冲突（aiv_vec_bank_cflt 0.141–0.208 vs SAME/SAME ≤0.009）。当广播可归约为少数标量（内维 stride-0 且长 run）、单周期内维向量（整 tile 连续段）或小驻留周期平铺时，其 per-slice 物化可退化为 copy-in 侧 1D 流式搬入或 1–2 条 Duplicate/Add 组装，把索引/收集成本移出 V 管。非驻留整量 re-staging（每-slice 重搬整个广播输入、MTE2 放大）同样被周期平铺/流式路径消除。",
  "related_anti_patterns": [],
  "risks": [
    "envelope lane 行为回归：清除泄漏缺陷会同时清除父核由偶然符号抵消产生的『碰巧正确』值（本 run 1,329 个 lane 翻转）——必须预登记 envelope（x1/x2==dtype INT_MIN/INT_MAX）并单独核对非 envelope lane 逐位精确",
    "模式误分类：把短 runLen 不规则广播当 V-A/V-B 处理会重新引入 bank 冲突或退化——必须保留 legacy 控制并测量",
    "done-scratch 别名：wzero[0] 同时作数据与 done 槽，per-slice 不复位会把上一 slice 泄漏污染下一 slice 首元素（父核 23,406 处无辜 lane 污染的根因）",
    "本策略只迁移 x2 侧 staging；SAME/SAME 载体差距、退化值地板与 INT32_MIN 收敛缺陷是独立机制，不在本卡承诺范围"
  ],
  "slug": "general-broadcast-slice-staging",
  "summary": "把 GENERAL（多轴广播）操作数每-slice 的 V 管物化成本迁出 V 管：广播驻留路由的 CoordDecompose 索引链 + 字节比例 UB Gather（bank_cflt 0.141–0.208，相对同 dtype SAME/SAME 的 3–4 倍路由开销）与非驻留整量 re-staging（MTE2 放大）由 host tiling 按广播模式分发消除——V-A『内维 stride-0 且 runLen≥256』→ ≤2 条基址对齐 Duplicate 组装；V-B『x2=单周期内维向量』→ 整 tile mod-L 连续段 1D DataCopyPad 流式搬入，或驻留且容量门通过 → Init 一次周期平铺 per slice 一条 +0 Add；短 runLen 低 k 保留 legacy Gather 作同路由结构控制。20-case incremental 1.0868x、cumulative 1.0851x；目标广播路由 1.42–1.83x，控制组 0.979–1.004，period-tile case vec_time −42.7%/−48.9%、非驻留 mte2 0.200→0.024。",
  "verification": {
    "correctness": [
      "官方 pytest 20/20 通过（kernel_hash 与 build receipt 闭环）",
      "golden 数值探针 139,970,214 元素：非 envelope lane 失配 0（父核同口径 23,406 处污染被清除）；A/B 逐位差分 31,647 处 100% 落在预登记 wzero 泄漏格点内，格点外 bit_exact_diff=0"
    ],
    "performance": [
      "20-case incremental 1.0868x（预测带 [1.063,1.105] 内）、cumulative 1.0851x；目标广播路由 1.42–1.83x 逐 case 落带（c11 1.459、c13 1.570、c18 1.684、c19 1.424、c20 1.832）",
      "控制组 15 case 0.979–1.004（聚合 0.9845），legacy 结构控制 case 逐字不动",
      "管道归因：period-tile case vec_time −42.7%/−48.9%（Gather 消失）；非驻留 case mte2 0.200→0.024（92.5→6.6us）；全 case Block Num=64 无少核"
    ],
    "rollback_signals": [
      "控制路由漂移超出 [0.95,1.05] 带",
      "目标广播路由 bank_cflt 未下降或 vec_time 未按机制预测下降",
      "非 envelope lane 出现新增逐位差异"
    ]
  }
}
-->

# 性能优化策略：GENERAL 广播 x2 侧搬入边界物化（模式分发 V-A / V-B / period-tile，附 done-scratch 每-slice 复位）

单一优化点：把 GENERAL（多轴广播）操作数每-slice 的 V 管物化成本迁出 V 管：广播驻留路由的 CoordDecompose 索引链 + 字节比例 UB Gather（bank_cflt 0.141–0.208，相对同 dtype SAME/SAME 的 3–4 倍路由开销）与非驻留整量 re-staging（MTE2 放大）由 host tiling 按广播模式分发消除——V-A『内维 stride-0 且 runLen≥256』→ ≤2 条基址对齐 Duplicate 组装；V-B『x2=单周期内维向量』→ 整 tile mod-L 连续段 1D DataCopyPad 流式搬入，或驻留且容量门通过 → Init 一次周期平铺 per slice 一条 +0 Add；短 runLen 低 k 保留 legacy Gather 作同路由结构控制。20-case incremental 1.0868x、cumulative 1.0851x；目标广播路由 1.42–1.83x，控制组 0.979–1.004，period-tile case vec_time −42.7%/−48.9%、非驻留 mte2 0.200→0.024。

## 1. 原理

广播是数据搬运问题而非计算问题：GENERAL 操作数在每-slice 经 CoordDecompose 索引链（outDimNum 维 × 每条若干向量指令）+ 字节比例 UB Gather 物化，叠加在计算轮体之上，向 V 管收取固定的 per-slice 索引税；对极小驻留窗口（≤16KB/8KB）的 64-lane Gather 还会引发 UB bank 冲突（aiv_vec_bank_cflt 0.141–0.208 vs SAME/SAME ≤0.009）。当广播可归约为少数标量（内维 stride-0 且长 run）、单周期内维向量（整 tile 连续段）或小驻留周期平铺时，其 per-slice 物化可退化为 copy-in 侧 1D 流式搬入或 1–2 条 Duplicate/Add 组装，把索引/收集成本移出 V 管。非驻留整量 re-staging（每-slice 重搬整个广播输入、MTE2 放大）同样被周期平铺/流式路径消除。

实现机制：host tiling 在运行时把 x2 侧 GENERAL 广播分类为：(V-A) 内维 stride-0 且 runLen≥256 → 每 256-slice 至多 2 个不同标量，用 2 条基址对齐 Duplicate 组装替代索引链 + Gather；(V-B) x2 为单周期内维向量 → 按整 tile mod-L 连续段 1D DataCopyPad 流式搬入，若驻留且容量门通过则在 Init 一次性周期平铺、per-slice 仅一条 +0 Add；(legacy) 短 runLen 低 k 广播保留 legacy Gather 作同路由结构控制。正确性伴修改：wzero[0] done/gate scratch 每-slice 复位，消除 done-scratch 别名（wzeroBuf_[0] 既作数据又作 done 槽）把上一 slice 泄漏污染下一 slice 首元素。

## 2. 性能问题模式

- 优化目标：消除广播驻留/非驻留路由相对同 shape 路由的 3–4 倍结构性差距：把每-slice 的 CoordDecompose 索引链 + 字节比例 UB Gather 的 V 管成本（VEC_BOUND + UB bank 冲突）与非驻留整量 re-staging 的 MTE2 放大移出 V 管，使广播组装退化为 copy-in 侧的流式搬入或 1–2 条 Duplicate/Add 指令。
- 适用数据流：broadcast-elementwise integer math（AIV-only 向量核，SIMD RegBase 载体，per-dtype 模板路由）：x2 侧为 GENERAL（多轴广播）操作数、且该操作数在 V 管按 slice 逐块物化（CoordDecompose 索引链 + 字节比例 UB Gather / 非驻留整量 re-staging）的 elementwise kernel
- Feature signature：`{"bottleneck": ["vec-bound", "ub-bank-conflict", "per-slice-broadcast-assembly", "nonresident-restaging-amplification"], "dtypes": ["int16", "int32", "int64"], "pattern": "general-broadcast-x2-vpipe-assembly", "structure": ["general-broadcast", "resident-window", "coord-decompose-index-chain", "ub-gather", "duplicate-assembly", "period-tile", "datacopypad-streaming"]}`

## 3. 正确性红线

- envelope lane 行为回归：清除泄漏缺陷会同时清除父核由偶然符号抵消产生的『碰巧正确』值（本 run 1,329 个 lane 翻转）——必须预登记 envelope（x1/x2==dtype INT_MIN/INT_MAX）并单独核对非 envelope lane 逐位精确
- 模式误分类：把短 runLen 不规则广播当 V-A/V-B 处理会重新引入 bank 冲突或退化——必须保留 legacy 控制并测量
- done-scratch 别名：wzero[0] 同时作数据与 done 槽，per-slice 不复位会把上一 slice 泄漏污染下一 slice 首元素（父核 23,406 处无辜 lane 污染的根因）
- 本策略只迁移 x2 侧 staging；SAME/SAME 载体差距、退化值地板与 INT32_MIN 收敛缺陷是独立机制，不在本卡承诺范围

资源与硬件约束：

- 驻留窗口容量门（per-dtype RES_CAP）决定 V-B/period-tile 分支是否可达，不得超出驻留上限
- done-scratch 别名约束：wzero[0] 若同时作数据与 done/gate 槽，必须每-slice 复位，否则污染下一 slice 首元素
- 本策略只迁移 x2 侧 staging 与 done 复位，编辑面应限定在共享 KernelGcd<T> 类模板内（本 run 仅 op_kernel/gcd.h），T3 等控制臂逐字保留

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- elementwise kernel 含 GENERAL（多轴广播）操作数，且其值在 V 管每-slice 物化（CoordDecompose 索引链 + UB Gather 或非驻留整量 re-staging），而非在 copy-in 侧组装
- profiling 显示广播驻留路由 VEC_BOUND 且 aiv_vec_bank_cflt 明显高于同 dtype 的 SAME/SAME 路由（>0.01 量级），或非驻留路由 MTE2 比例偏高（整量 re-staging 放大）
- 广播内维 stride-0 且 runLen≥256（V-A），或 x2 为单周期内维向量 / 小驻留 tile 且容量门通过（V-B / period-tile），使存在低成本的 copy-in 流式或 Duplicate 组装
- host tiling 可在 kernel 运行前对广播模式分类并下发分发标记

不适用：

- 短 runLen 低 k 的不规则广播（每-slice 含大量不同值）——legacy Gather 成本更低，应保留作同路由结构控制，不强行套用 V-A/V-B
- SIMT-VF per-tile 直读队列槽的访问形态（单次 asc_vf_call 解引用 UB 足迹 >8192B 触发设备 507035）——属于独立负向边界，不属本 staging 机制
- SAME/SAME 同 shape 路由的载体差距与退化值地板是独立机制，不承诺由本策略修复

## 5. 实施步骤

1. 用 full-metrics op_summary/msprof 确认广播路由 VEC_BOUND、aiv_vec_bank_cflt 明显高于同 dtype 的 SAME/SAME 路由，并识别非驻留路由的整量 per-slice re-staging（MTE2 放大）
2. host tiling 增加广播模式分类：内维 stride-0 且 runLen≥256 → V-A；x2=单周期内维向量或小驻留 tile（容量门通过）→ V-B；其余短 runLen 低 k → legacy
3. V-A 实现：以 ≤2 条基址对齐 Duplicate 组装替代每-slice 索引链 + Gather
4. V-B 实现：按整 tile mod-L 连续段 1D DataCopyPad 流式搬入；驻留且容量门通过时 Init 一次性周期平铺 + per-slice 一条 +0 Add
5. 每-slice 复位 wzero[0] done/gate scratch，消除跨 slice 泄漏
6. 保留一个 legacy-Gather 同路由 case 作结构控制；全量 case 正确性 + 稳定性 + 逐 case 落带核验，确认控制路由不变

## 6. LLM 前置问题

- 目标实现是否满足：elementwise kernel 含 GENERAL（多轴广播）操作数，且其值在 V 管每-slice 物化（CoordDecompose 索引链 + UB Gather 或非驻留整量 re-staging），而非在 copy-in 侧组装？
- 目标实现是否满足：profiling 显示广播驻留路由 VEC_BOUND 且 aiv_vec_bank_cflt 明显高于同 dtype 的 SAME/SAME 路由（>0.01 量级），或非驻留路由 MTE2 比例偏高（整量 re-staging 放大）？
- 目标实现是否满足：广播内维 stride-0 且 runLen≥256（V-A），或 x2 为单周期内维向量 / 小驻留 tile 且容量门通过（V-B / period-tile），使存在低成本的 copy-in 流式或 Duplicate 组装？
- 是否命中排除条件：短 runLen 低 k 的不规则广播（每-slice 含大量不同值）——legacy Gather 成本更低，应保留作同路由结构控制，不强行套用 V-A/V-B？

## 7. 验收标准

正确性：

- 官方 pytest 20/20 通过（kernel_hash 与 build receipt 闭环）
- golden 数值探针 139,970,214 元素：非 envelope lane 失配 0（父核同口径 23,406 处污染被清除）；A/B 逐位差分 31,647 处 100% 落在预登记 wzero 泄漏格点内，格点外 bit_exact_diff=0

性能：

- 20-case incremental 1.0868x（预测带 [1.063,1.105] 内）、cumulative 1.0851x；目标广播路由 1.42–1.83x 逐 case 落带（c11 1.459、c13 1.570、c18 1.684、c19 1.424、c20 1.832）
- 控制组 15 case 0.979–1.004（聚合 0.9845），legacy 结构控制 case 逐字不动
- 管道归因：period-tile case vec_time −42.7%/−48.9%（Gather 消失）；非驻留 case mte2 0.200→0.024（92.5→6.6us）；全 case Block Num=64 无少核

回滚信号：

- 控制路由漂移超出 [0.95,1.05] 带
- 目标广播路由 bank_cflt 未下降或 vec_time 未按机制预测下降
- 非 envelope lane 出现新增逐位差异

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260827_005737-1516a0（round=1, status=accepted）

## 检索卡（短卡）

动作：将 GENERAL 广播从每 slice 的 V 管索引链与 UB Gather 物化，改为 x2 侧搬入边界物化。
适用：elementwise kernel 含 GENERAL 多轴广播操作数，且其值由 V 管逐 slice 物化。
限制：V-B/period-tile 分支受 per-dtype RES_CAP 限制；修正 envelope lane 范围后须重验输出。
范围：elementwise-arithmetic 的 GENERAL 广播操作数搬入。
检索词：GENERAL 多轴广播、CoordDecompose、UB Gather、V-B、period-tile、RES_CAP。
机会：每 slice 都执行 CoordDecompose 与 UB Gather，且 VEC bank 冲突高于 SAME 路由。
