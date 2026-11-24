---
type: Optimization
title: dtype 限定的无除法二进制 GCD（Stein）轮体：在 TW=int32 计算域用尾零剥离 + min/|a-b| 收缩替换 Div/Mul，int64 保留父版欧几里得
description: 在 int32 计算域用无除法 Stein 轮体替换每轮 vdiv，改用廉价 ALU 序列。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/divfree-binary-roundbody-int32-scoped.md
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
      "共享模板（ComputeGcdChunkVF 等被全部 dtype 实例化）的改动会实例化到每个 BCT/dtype 组合，必须对每个 route 做 no-regression 验证",
      "host simdWorkB g 项与 kernel gBuf_ 注册必须同真同假（twin 对账），否则 UB 溢出（507015）",
      "条带阶梯宽度掩码不能 RegTensor 数组化（catalog NEG-4），需在块循环外 Duplicate 一次后按名传参",
      "int16 提升域真 abs 与 wrap-cast 缩窄出口必须与父版逐字一致以保位精确"
    ],
    "excluded_conditions": [
      "TW=int64/B64 原生域不适用——同一无除法轮体在 int64 域净回归（见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）；int64 域改用数据域窄化快路径（ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）",
      "非 VEC-bound（MTE2/launch/scalar bound）时不预期收益",
      "无编译期 dtype 分派能力（只能全共享轮体）时本机制退化为全局替换，须先确认所有 dtype 域都不回归"
    ],
    "required_conditions": [
      "完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%），MTE2/MTE3/scalar 在其下重叠",
      "热链为分块固定轮逐 lane 迭代（已有 chunk 早退/停止保护），轮体含单指令 dominant 向量整数除法（int32 域 vdiv）",
      "存在编译期 dtype 域分派点（if constexpr sizeof(TW)==4/8），能把替换限定到已验证实例、其余实例保持父版文本逐字不变",
      "替换域的收敛轮数上界（MAX_ROUNDS）可实测验证，替换不改变停止保护（B==0 吸收态）与位精确性"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "int32 domain T1/T2 9 case target + T3 6 case control",
      "operator_class": "broadcast",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "int32 2.7634x; T3 1.0004x; incremental total 1.1905x; cumulative 1.19x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "eb48e25edd09a86c96a4bae431af6da9d253a1e64ad431fa9edd31312e9a5ac4",
      "decision_sha256": "f41ab9a63be27f1a0d0ffd156652982bf342cb0622eb50ec60e81145613b9f9e",
      "operator_class": "broadcast",
      "performance_sha256": "099b625b7f213a7176380088a8fbd8ea6a11963f261c62f614552635d2ed8c35",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "bacae2c76b1fef60c9f00c32c9bea98ac7adfb144d0ce44ac5362e0d1bdc2fae",
      "verify_sha256": "7fbcc0360f5521af245485c081389b74a5efdb3aefd18dd1466b0f8514f9b662"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "fixed-round-loop",
      "div-dominant",
      "per-lane-convergence"
    ],
    "dtypes": [
      "int16",
      "int32"
    ],
    "pattern": "divfree-binary-roundbody-int32-scoped",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "dtype-scoped-dispatch",
      "ub-persistent-state"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED",
  "implementation_steps": [
    "用 msprof 确认 VEC 为唯一临界流水并定位固定轮迭代循环；用编译产物/逐指令 msprof 确认 int32 vdiv 为每轮 dominant 成本",
    "在共享轮体上实现无除法 Stein 轮体（strip-B 条带阶梯 + min/|a-b| 收缩）与 P=2^g 规范化/折回，保持分块早退与停止保护逐字不变",
    "用 if constexpr (sizeof(TW)==4) 把替换限定到 int32 实例；int64 实例逐功能恢复父版 Div 轮体、MAX_ROUNDS、gBuf_ 注册与 host g 项（DT_INT64 累加恰为 0）",
    "脚本化三方比对（parent / 轮 1 重建 / 工作区）证实 int32 臂文本 = 已验证构建、int64 臂 = parent 文本逐字",
    "对全 all_cases 跑 verify，对 validation_cases 跑 frozen-tool 性能采集，按 dtype 域拆分增量 compare 验收"
  ],
  "intent": "在 int32 计算域消除每轮 dominant 的向量整数除法 vdiv 成本（以更便宜的 ALU 序列替换），同时用编译期 dtype 分派隔离 int64 计算域，避免轮 1 全局替换暴露的 int64 回归。",
  "mechanism": "KernelGcd<T> 以 TW=(T==int16 ? int32 : T) 推导，分流用 if constexpr (sizeof(TW)==4)：int32 臂（T1 提升域 + T2 原生域）在 ComputeGcdAbsInit 调 GcdSteinNormalize（a==0 修正 -> 公共尾零剥离计 P=2^g -> 奇偶 swap）、ComputeGcdChunkVF 调 GcdSteinRounds（strip-B 条带阶梯 {16,8,4,2,1} + D=|A-B|/M=min(A,B)/B!=0 守卫 Select）、ComputeGcdFinalVF 以 Mul(A,A,P) 折回；int64 臂（T3）逐字调父版 GcdEuclidRounds/abs-init/final，MAX_ROUNDS 恢复 47/64/93，gBuf_ 仅 sizeof(TW)==4 注册，host simdWorkB 的 g 项对 DT_INT64 累加恰为 0（T3 ubFactor 回 parent 4352 clamp）。分块早退（EUCLID_CHUNK=8、TQueSync<PIPE_V,PIPE_S>+GetValue、not-done Reduce SUM、PipeBarrier<PIPE_V>）两臂共用逐字保留；条带阶梯掩码在块循环外 Duplicate 一次按名传参（不数组化，NEG-4）。",
  "name": "dtype 限定的无除法二进制 GCD（Stein）轮体：在 TW=int32 计算域用尾零剥离 + min/|a-b| 收缩替换 Div/Mul，int64 保留父版欧几里得",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为编译期固定 MAX_ROUNDS 的分块逐 lane 迭代循环（如截断欧几里得 GCD，已有 chunk 早退/停止保护），计算域为 TW=int32（原生 int32 或 int16 提升域，单指令 vdiv 主导每轮），且存在编译期 dtype 分派能力可把替换限定到已验证实例",
  "principle": "VEC-bound 且轮体含单指令 dominant 除法（int32 vdiv）时，用无除法轮体替换可按每轮把 dominant 除法成本替换为廉价 ALU 序列；Stein 轮数（≈bitlen）与 Euclid 轮数（≈商位数）在 int32 全值域相近，而 vdiv 是单指令，替换净收益为正。该收益依赖计算域：同一替换在 int64/B64 域（软件除法与软件移位单价相当）净回归（见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）。因此必须按 dtype 域限定编辑面，用 if constexpr 把替换限制在已验证的 TW=int32 实例，其余实例保持父版文本逐字不变，以消除共享模板改动的泄漏向量。",
  "related_anti_patterns": [],
  "risks": [
    "int64 臂文本与 parent 逐字不一致造成 scope 泄漏（轮 1 失败模式：int64 Stein +2048B g 项 + gBuf_ + MAX_ROUNDS 改动导致 T3 +20-22% cyc/el、0.817-0.833x）",
    "host g 项与 kernel gBuf_ 门控不同真同假导致 UB 溢出（507015）",
    "条带阶梯掩码数组化导致编译失败（NEG-4）",
    "Stein 轮数 ≈ bitlen 的剩余值域敏感：中/大值域每轮收益高，小值域接近地板哨兵时固定开销占比升高（scalar 5.6%->15.4%）"
  ],
  "slug": "divfree-binary-roundbody-int32-scoped",
  "summary": "把无除法二进制 GCD（Stein）轮体限定到 TW=int32 计算域（T1 int16 提升域 + T2 int32 原生域全部 BCT route）：GcdSteinStep 用条带阶梯剥尾零 + min/|a-b| 收缩替换 Div/Mul，GcdSteinNormalize 以 P=2^g 携带公共尾零并在 final 折回；TW=int64 实例逐功能恢复父版 Div 截断欧几里得体（MAX_ROUNDS 47/64/93、不注册 gBuf_、host g 项对 DT_INT64 恰为 0）。实测 int32 目标域 2.7634x 聚合、int64 控制域 1.0004x 聚合（cyc/el 与 parent 四位有效数字一致），增量 1.1905x，零回归。",
  "verification": {
    "correctness": [
      "round 2 verify ok=true，20/20（run.json.all_cases），kernel d15c0e64e3393be1 与 build/verify/已安装 kernel/worktree 复核指纹一致",
      "覆盖 gcd(0,0)、x2 标量 gcd(n,0)/gcd(0,n)（a==0 修正）、int32/int16 全值域（MAX_ROUNDS 64/47）、T3 大值域（恢复 93）与非对齐 case 6/7/14 的掩码纪律"
    ],
    "performance": [
      "int32 目标域（T1+T2，9 case）2.7634x 聚合（1.6116-2.9119x 每 case，含两个地板哨兵 case 7/14），aiv_total_cycles/element 坍缩（case 5 57.0->19.6、case 7 15.3->6.4）",
      "int64 控制域（T3，6 case）1.0004x 聚合，cyc/el 与 parent 四位有效数字一致（250.2/127.9/197.5/203.5/198.1/207.7），vec_ratio 0.993-0.996、mte2 <= 0.2% 不变",
      "增量 compare 1.1905x（预测 1.1902x），9 improved / 0 regressed / 6 unchanged；int32 数字复现轮 1 独立构建 0.215% 内",
      "值域梯子 3.73 -> 3.06（残差 bitlen 敏感已文档化）"
    ],
    "rollback_signals": [
      "任一 int64 控制 case 偏离 parent ±5%（scope 泄漏）",
      "int32 目标无方向性收益或任一 route 回归超 max_case_regression 0.95",
      "任一 verify 位精确失败"
    ]
  }
}
-->

# 性能优化策略：dtype 限定的无除法二进制 GCD（Stein）轮体：在 TW=int32 计算域用尾零剥离 + min/|a-b| 收缩替换 Div/Mul，int64 保留父版欧几里得

单一优化点：把无除法二进制 GCD（Stein）轮体限定到 TW=int32 计算域（T1 int16 提升域 + T2 int32 原生域全部 BCT route）：GcdSteinStep 用条带阶梯剥尾零 + min/|a-b| 收缩替换 Div/Mul，GcdSteinNormalize 以 P=2^g 携带公共尾零并在 final 折回；TW=int64 实例逐功能恢复父版 Div 截断欧几里得体（MAX_ROUNDS 47/64/93、不注册 gBuf_、host g 项对 DT_INT64 恰为 0）。实测 int32 目标域 2.7634x 聚合、int64 控制域 1.0004x 聚合（cyc/el 与 parent 四位有效数字一致），增量 1.1905x，零回归。

## 1. 原理

VEC-bound 且轮体含单指令 dominant 除法（int32 vdiv）时，用无除法轮体替换可按每轮把 dominant 除法成本替换为廉价 ALU 序列；Stein 轮数（≈bitlen）与 Euclid 轮数（≈商位数）在 int32 全值域相近，而 vdiv 是单指令，替换净收益为正。该收益依赖计算域：同一替换在 int64/B64 域（软件除法与软件移位单价相当）净回归（见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）。因此必须按 dtype 域限定编辑面，用 if constexpr 把替换限制在已验证的 TW=int32 实例，其余实例保持父版文本逐字不变，以消除共享模板改动的泄漏向量。

实现机制：KernelGcd<T> 以 TW=(T==int16 ? int32 : T) 推导，分流用 if constexpr (sizeof(TW)==4)：int32 臂（T1 提升域 + T2 原生域）在 ComputeGcdAbsInit 调 GcdSteinNormalize（a==0 修正 -> 公共尾零剥离计 P=2^g -> 奇偶 swap）、ComputeGcdChunkVF 调 GcdSteinRounds（strip-B 条带阶梯 {16,8,4,2,1} + D=|A-B|/M=min(A,B)/B!=0 守卫 Select）、ComputeGcdFinalVF 以 Mul(A,A,P) 折回；int64 臂（T3）逐字调父版 GcdEuclidRounds/abs-init/final，MAX_ROUNDS 恢复 47/64/93，gBuf_ 仅 sizeof(TW)==4 注册，host simdWorkB 的 g 项对 DT_INT64 累加恰为 0（T3 ubFactor 回 parent 4352 clamp）。分块早退（EUCLID_CHUNK=8、TQueSync<PIPE_V,PIPE_S>+GetValue、not-done Reduce SUM、PipeBarrier<PIPE_V>）两臂共用逐字保留；条带阶梯掩码在块循环外 Duplicate 一次按名传参（不数组化，NEG-4）。

## 2. 性能问题模式

- 优化目标：在 int32 计算域消除每轮 dominant 的向量整数除法 vdiv 成本（以更便宜的 ALU 序列替换），同时用编译期 dtype 分派隔离 int64 计算域，避免轮 1 全局替换暴露的 int64 回归。
- 适用数据流：VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为编译期固定 MAX_ROUNDS 的分块逐 lane 迭代循环（如截断欧几里得 GCD，已有 chunk 早退/停止保护），计算域为 TW=int32（原生 int32 或 int16 提升域，单指令 vdiv 主导每轮），且存在编译期 dtype 分派能力可把替换限定到已验证实例
- Feature signature：`{"bottleneck": ["vec-bound", "fixed-round-loop", "div-dominant", "per-lane-convergence"], "dtypes": ["int16", "int32"], "pattern": "divfree-binary-roundbody-int32-scoped", "structure": ["vec-iterative-loop", "streaming-elementwise", "dtype-scoped-dispatch", "ub-persistent-state"]}`

## 3. 正确性红线

- int64 臂文本与 parent 逐字不一致造成 scope 泄漏（轮 1 失败模式：int64 Stein +2048B g 项 + gBuf_ + MAX_ROUNDS 改动导致 T3 +20-22% cyc/el、0.817-0.833x）
- host g 项与 kernel gBuf_ 门控不同真同假导致 UB 溢出（507015）
- 条带阶梯掩码数组化导致编译失败（NEG-4）
- Stein 轮数 ≈ bitlen 的剩余值域敏感：中/大值域每轮收益高，小值域接近地板哨兵时固定开销占比升高（scalar 5.6%->15.4%）

资源与硬件约束：

- 共享模板（ComputeGcdChunkVF 等被全部 dtype 实例化）的改动会实例化到每个 BCT/dtype 组合，必须对每个 route 做 no-regression 验证
- host simdWorkB g 项与 kernel gBuf_ 注册必须同真同假（twin 对账），否则 UB 溢出（507015）
- 条带阶梯宽度掩码不能 RegTensor 数组化（catalog NEG-4），需在块循环外 Duplicate 一次后按名传参
- int16 提升域真 abs 与 wrap-cast 缩窄出口必须与父版逐字一致以保位精确

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%），MTE2/MTE3/scalar 在其下重叠
- 热链为分块固定轮逐 lane 迭代（已有 chunk 早退/停止保护），轮体含单指令 dominant 向量整数除法（int32 域 vdiv）
- 存在编译期 dtype 域分派点（if constexpr sizeof(TW)==4/8），能把替换限定到已验证实例、其余实例保持父版文本逐字不变
- 替换域的收敛轮数上界（MAX_ROUNDS）可实测验证，替换不改变停止保护（B==0 吸收态）与位精确性

不适用：

- TW=int64/B64 原生域不适用——同一无除法轮体在 int64 域净回归（见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）；int64 域改用数据域窄化快路径（ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）
- 非 VEC-bound（MTE2/launch/scalar bound）时不预期收益
- 无编译期 dtype 分派能力（只能全共享轮体）时本机制退化为全局替换，须先确认所有 dtype 域都不回归

## 5. 实施步骤

1. 用 msprof 确认 VEC 为唯一临界流水并定位固定轮迭代循环；用编译产物/逐指令 msprof 确认 int32 vdiv 为每轮 dominant 成本
2. 在共享轮体上实现无除法 Stein 轮体（strip-B 条带阶梯 + min/|a-b| 收缩）与 P=2^g 规范化/折回，保持分块早退与停止保护逐字不变
3. 用 if constexpr (sizeof(TW)==4) 把替换限定到 int32 实例；int64 实例逐功能恢复父版 Div 轮体、MAX_ROUNDS、gBuf_ 注册与 host g 项（DT_INT64 累加恰为 0）
4. 脚本化三方比对（parent / 轮 1 重建 / 工作区）证实 int32 臂文本 = 已验证构建、int64 臂 = parent 文本逐字
5. 对全 all_cases 跑 verify，对 validation_cases 跑 frozen-tool 性能采集，按 dtype 域拆分增量 compare 验收

## 6. LLM 前置问题

- 目标实现是否满足：完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%），MTE2/MTE3/scalar 在其下重叠？
- 目标实现是否满足：热链为分块固定轮逐 lane 迭代（已有 chunk 早退/停止保护），轮体含单指令 dominant 向量整数除法（int32 域 vdiv）？
- 目标实现是否满足：存在编译期 dtype 域分派点（if constexpr sizeof(TW)==4/8），能把替换限定到已验证实例、其余实例保持父版文本逐字不变？
- 是否命中排除条件：TW=int64/B64 原生域不适用——同一无除法轮体在 int64 域净回归（见 NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64）；int64 域改用数据域窄化快路径（ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）？

## 7. 验收标准

正确性：

- round 2 verify ok=true，20/20（run.json.all_cases），kernel d15c0e64e3393be1 与 build/verify/已安装 kernel/worktree 复核指纹一致
- 覆盖 gcd(0,0)、x2 标量 gcd(n,0)/gcd(0,n)（a==0 修正）、int32/int16 全值域（MAX_ROUNDS 64/47）、T3 大值域（恢复 93）与非对齐 case 6/7/14 的掩码纪律

性能：

- int32 目标域（T1+T2，9 case）2.7634x 聚合（1.6116-2.9119x 每 case，含两个地板哨兵 case 7/14），aiv_total_cycles/element 坍缩（case 5 57.0->19.6、case 7 15.3->6.4）
- int64 控制域（T3，6 case）1.0004x 聚合，cyc/el 与 parent 四位有效数字一致（250.2/127.9/197.5/203.5/198.1/207.7），vec_ratio 0.993-0.996、mte2 <= 0.2% 不变
- 增量 compare 1.1905x（预测 1.1902x），9 improved / 0 regressed / 6 unchanged；int32 数字复现轮 1 独立构建 0.215% 内
- 值域梯子 3.73 -> 3.06（残差 bitlen 敏感已文档化）

回滚信号：

- 任一 int64 控制 case 偏离 parent ±5%（scope 泄漏）
- int32 目标无方向性收益或任一 route 回归超 max_case_regression 0.95
- 任一 verify 位精确失败

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260826_015717-b0d16d（round=2, status=accepted, case=int32 domain T1/T2 9 case target + T3 6 case control, speedup=int32 2.7634x; T3 1.0004x; incremental total 1.1905x; cumulative 1.19x）
- gcd-20260826_015717-b0d16d（round=2, status=accepted）

## 检索卡（短卡）

动作：在 int32 计算域用无除法 Stein 轮体替换每轮 vdiv，改用廉价 ALU 序列。
适用：完整 msprof 显示 VEC 为唯一关键流水，aiv_vec_ratio约≥90%。
限制：int32 改动不得泄漏至 int64；共享模板新增状态或缓冲后须复核各 dtype 的 UB 预算。
范围：elementwise-arithmetic 的 int32 计算域。
检索词：int32 vdiv、Stein、Euclid、编译期 dtype 分派、UB预算
机会：固定轮迭代热链中，int32 vdiv 是每轮 dominant 指令。
代价：共享模板新增状态和缓冲会改变其他 dtype 的资源需求。
