---
type: Optimization
title: 寄存器驻留累加器归约（含逐块部分掩码修复）
description: 将maxVal/maxIdx全程驻留寄存器，以逐块向量比较RMW替代UB往返和逐块屏障，同步移至slice边界。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/register-resident-accumulator-arg-reduce.md
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
      "累加器寄存器驻留要求向量比较/选择原语可用，且每块 RMW 指令数小于被替代的 UB 往返指令数",
      "末块必须显式部分掩码（blockCount=min(innerChunk-off, BLK)），不得依赖 UpdateMask 计数器跨块递减"
    ],
    "excluded_conditions": [
      "inner 无法切块的 case（numInnerChunks==1 或 outer>=coreNumAiv 的已饱和路径）走 legacy outer-only，本机制不激活",
      "int64(b64) T2 任务空间路径源码级一致但套件无数值覆盖，int64 dim=0 上线前须补测"
    ],
    "required_conditions": [
      "T2 路径（dimIsLast=0、stridedMode=1）且 innerChunk 可为任意长度（含非 BLK 整数倍）",
      "任务块内归约相互独立，运行极值/索引可全程驻留寄存器（每块 RMW 更新）",
      "CopyInStrided/CopyOutStrided 已就绪，输出 flat 索引可精确计算"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "97cdacc8596893b5e63b04536ca2408bcdfc2b23c2af08ec9670176a1335590d",
      "decision_sha256": "bbd51aeb3b3650fa4f224abce56fbabc792ed25f8c47902cc908e4ba98c968f9",
      "operator_class": "sort-select",
      "performance_sha256": "8e0548c461f561edf1531e4440e78fd9e42b001c9168b4f94cdea33c7ae3f2ef",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "94a777734a005b1960b2b696c14f10675582f81bd6f10e74b226e24465e534fe",
      "verify_sha256": "91dcd45bb6806f3a077d399627238bfe79a1df8e717f46bd7ee980d23627a1bf"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-block-ub-roundtrip",
      "local-membar-chain",
      "vector-latency"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "register-resident-accumulator-arg-reduce",
    "reduce_mode": "argmax-argmin",
    "structure": [
      "strided-copy",
      "register-rmw-accumulator",
      "partial-mask"
    ]
  },
  "generality": "op_class",
  "id": "ARGRED-003",
  "implementation_steps": [
    "确认 T2 strided 路径任务分解与 CopyInStrided/CopyOutStrided 边界",
    "把运行 maxVal/maxIdx 累加器改为寄存器驻留，逐块向量比较 RMW 更新",
    "在块首显式计算逐块部分掩码（修复 UpdateMask 计数器作用域 bug），末块只更新有效 lane",
    "输出按 flat 索引经 CopyOutStrided 写回，核对 (outer, innerChunk) 任务覆盖互不重叠、无 dropped/doubled 切片",
    "精度验证含非对齐尾块 case（如 inner=1021/innerChunk=1016、innerChunk=368），并复核 pipeline 归因与 Block Num 扩张"
  ],
  "intent": "消除 strided arg-reduce 中每块把运行极值/索引经 UB 往返与 LocalMemBar 串行链同步的开销，让运行累加器全程驻留寄存器。",
  "mechanism": "ComputeArgMaxUpdateRegImpl 保持运行 maxVal/maxIdx 为寄存器累加器，逐块向量比较并 RMW 更新；块首显式计算 blockCount=min(innerChunk-off, BLK) 的部分掩码（修复 round 2 的 UpdateMask 计数器作用域 bug，见 NEG-UPDATEMASK-COUNTER-SCOPE），末块只更新有效 lane，避免越界写与尾 lane 垃圾；输出经 CopyOutStrided 按 flat 索引写回。pipeline 归因显示 aiv_vec_time 崩塌（case4 22317.6->2367.3us -89.4%）而 aiv_scalar_time 基本不变（-2.7%~+1.7%）、aiv_mte2_time 次要变动。",
  "name": "寄存器驻留累加器归约（含逐块部分掩码修复）",
  "operator_class": "sort-select",
  "operator_scope": "dimIsLast=0、stridedMode=1 的 strided argmax/argmin T2 路径（CopyInStrided + 寄存器驻留 RMW 累加器），innerChunk 可为任意长度（含非 BLK 整数倍）",
  "principle": "任务块内归约相互独立时，运行 maxVal/maxIdx 累加器可全程驻留向量寄存器，用逐块向量比较 RMW 更新替代每块 UB LoadAlign/StoreAlign + LocalMemBar 往返；同步成本从每块一次降到每个 slice 一次。收益来自向量域指令量减少，非数据搬运减少。",
  "related_anti_patterns": [],
  "risks": [
    "掩码簿记错误会静默产生输出首列/尾列垃圾（确定性 bug，重采不可修复，见 NEG-UPDATEMASK-COUNTER-SCOPE）",
    "int64(b64) 路径同缺陷修复仅源码论证，无数值覆盖，int64 dim=0 上线前须补测",
    "case10 aiv_mte2_time +27% 为次要引擎变动（循环交换固有特性），vec 崩塌绝对节省远超增量，不构成回归"
  ],
  "slug": "register-resident-accumulator-arg-reduce",
  "summary": "把 strided arg-reduce 每块的 UB 往返（2×LoadAlign+2×StoreAlign+1×LocalMemBar）替换为寄存器驻留 RMW 累加器，并在块首显式部分掩码修复非对齐尾块；实测 T2 8/8 case 精度通过、median 4.65x 加速、aiv_vec_time 崩塌 -77.7%~-89.4% 而 scalar/mte2 基本不变。",
  "verification": {
    "correctness": [
      "10/10 验证 case 精度通过，含 round 2 失败点 case8(innerChunk=1016)/case10(innerChunk=368)；输出 flat 索引与 golden 完全一致，无 dropped/doubled 列切片"
    ],
    "performance": [
      "T2 8/8 case median 4.65x（min 3.693x case13、max 7.7015x case4），aiv_vec_time 崩塌 -77.7%~-89.4% 而 aiv_scalar_time 基本不变（-2.7%~+1.7%）",
      "comparison total_speedup=5.4206>1.02、regressed_cases=0（9 improved + 1 unchanged）；控制 case 全在 0.95-1.05 带内（case2=0.989、case3=0.9997），无路由串扰"
    ],
    "rollback_signals": [
      "任一非对齐 case 输出与 golden 不一致（掩码回归）",
      "控制 case 超 0.95-1.05 波动带（路由串扰）或 regressed_cases>0",
      "case13 类 microkernel 量级 case 须按噪声地板门禁单独处理，禁止重采翻案"
    ]
  }
}
-->

# 性能优化策略：寄存器驻留累加器归约（含逐块部分掩码修复）

单一优化点：把 strided arg-reduce 每块的 UB 往返（2×LoadAlign+2×StoreAlign+1×LocalMemBar）替换为寄存器驻留 RMW 累加器，并在块首显式部分掩码修复非对齐尾块；实测 T2 8/8 case 精度通过、median 4.65x 加速、aiv_vec_time 崩塌 -77.7%~-89.4% 而 scalar/mte2 基本不变。

## 1. 原理

任务块内归约相互独立时，运行 maxVal/maxIdx 累加器可全程驻留向量寄存器，用逐块向量比较 RMW 更新替代每块 UB LoadAlign/StoreAlign + LocalMemBar 往返；同步成本从每块一次降到每个 slice 一次。收益来自向量域指令量减少，非数据搬运减少。

实现机制：ComputeArgMaxUpdateRegImpl 保持运行 maxVal/maxIdx 为寄存器累加器，逐块向量比较并 RMW 更新；块首显式计算 blockCount=min(innerChunk-off, BLK) 的部分掩码（修复 round 2 的 UpdateMask 计数器作用域 bug，见 NEG-UPDATEMASK-COUNTER-SCOPE），末块只更新有效 lane，避免越界写与尾 lane 垃圾；输出经 CopyOutStrided 按 flat 索引写回。pipeline 归因显示 aiv_vec_time 崩塌（case4 22317.6->2367.3us -89.4%）而 aiv_scalar_time 基本不变（-2.7%~+1.7%）、aiv_mte2_time 次要变动。

## 2. 性能问题模式

- 优化目标：消除 strided arg-reduce 中每块把运行极值/索引经 UB 往返与 LocalMemBar 串行链同步的开销，让运行累加器全程驻留寄存器。
- 适用数据流：dimIsLast=0、stridedMode=1 的 strided argmax/argmin T2 路径（CopyInStrided + 寄存器驻留 RMW 累加器），innerChunk 可为任意长度（含非 BLK 整数倍）
- Feature signature：`{"bottleneck": ["per-block-ub-roundtrip", "local-membar-chain", "vector-latency"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "register-resident-accumulator-arg-reduce", "reduce_mode": "argmax-argmin", "structure": ["strided-copy", "register-rmw-accumulator", "partial-mask"]}`

## 3. 正确性红线

- 掩码簿记错误会静默产生输出首列/尾列垃圾（确定性 bug，重采不可修复，见 NEG-UPDATEMASK-COUNTER-SCOPE）
- int64(b64) 路径同缺陷修复仅源码论证，无数值覆盖，int64 dim=0 上线前须补测
- case10 aiv_mte2_time +27% 为次要引擎变动（循环交换固有特性），vec 崩塌绝对节省远超增量，不构成回归

资源与硬件约束：

- 累加器寄存器驻留要求向量比较/选择原语可用，且每块 RMW 指令数小于被替代的 UB 往返指令数
- 末块必须显式部分掩码（blockCount=min(innerChunk-off, BLK)），不得依赖 UpdateMask 计数器跨块递减

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- T2 路径（dimIsLast=0、stridedMode=1）且 innerChunk 可为任意长度（含非 BLK 整数倍）
- 任务块内归约相互独立，运行极值/索引可全程驻留寄存器（每块 RMW 更新）
- CopyInStrided/CopyOutStrided 已就绪，输出 flat 索引可精确计算

不适用：

- inner 无法切块的 case（numInnerChunks==1 或 outer>=coreNumAiv 的已饱和路径）走 legacy outer-only，本机制不激活
- int64(b64) T2 任务空间路径源码级一致但套件无数值覆盖，int64 dim=0 上线前须补测

## 5. 实施步骤

1. 确认 T2 strided 路径任务分解与 CopyInStrided/CopyOutStrided 边界
2. 把运行 maxVal/maxIdx 累加器改为寄存器驻留，逐块向量比较 RMW 更新
3. 在块首显式计算逐块部分掩码（修复 UpdateMask 计数器作用域 bug），末块只更新有效 lane
4. 输出按 flat 索引经 CopyOutStrided 写回，核对 (outer, innerChunk) 任务覆盖互不重叠、无 dropped/doubled 切片
5. 精度验证含非对齐尾块 case（如 inner=1021/innerChunk=1016、innerChunk=368），并复核 pipeline 归因与 Block Num 扩张

## 6. LLM 前置问题

- 目标实现是否满足：T2 路径（dimIsLast=0、stridedMode=1）且 innerChunk 可为任意长度（含非 BLK 整数倍）？
- 目标实现是否满足：任务块内归约相互独立，运行极值/索引可全程驻留寄存器（每块 RMW 更新）？
- 目标实现是否满足：CopyInStrided/CopyOutStrided 已就绪，输出 flat 索引可精确计算？
- 是否命中排除条件：inner 无法切块的 case（numInnerChunks==1 或 outer>=coreNumAiv 的已饱和路径）走 legacy outer-only，本机制不激活？

## 7. 验收标准

正确性：

- 10/10 验证 case 精度通过，含 round 2 失败点 case8(innerChunk=1016)/case10(innerChunk=368)；输出 flat 索引与 golden 完全一致，无 dropped/doubled 列切片

性能：

- T2 8/8 case median 4.65x（min 3.693x case13、max 7.7015x case4），aiv_vec_time 崩塌 -77.7%~-89.4% 而 aiv_scalar_time 基本不变（-2.7%~+1.7%）
- comparison total_speedup=5.4206>1.02、regressed_cases=0（9 improved + 1 unchanged）；控制 case 全在 0.95-1.05 带内（case2=0.989、case3=0.9997），无路由串扰

回滚信号：

- 任一非对齐 case 输出与 golden 不一致（掩码回归）
- 控制 case 超 0.95-1.05 波动带（路由串扰）或 regressed_cases>0
- case13 类 microkernel 量级 case 须按噪声地板门禁单独处理，禁止重采翻案

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- arg_max-20260824_083424-ff0f95（round=3, status=accepted）

## 检索卡（短卡）

动作：将maxVal/maxIdx全程驻留寄存器，以逐块向量比较RMW替代UB往返和逐块屏障，同步移至slice边界。
适用：T2非末轴strided路径，块内归约独立，innerChunk可非BLK整倍。
限制：须有向量比较/选择原语，并正确维护逐块部分掩码。
范围：selection-reduce的T2 strided arg-reduce路径。
检索词：maxVal/maxIdx、向量比较RMW、LocalMemBar、部分掩码。
机会：每块运行极值和索引仍经UB往返并串行执行LocalMemBar。
