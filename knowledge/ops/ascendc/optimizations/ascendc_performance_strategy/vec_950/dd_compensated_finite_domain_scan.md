---
type: Optimization
title: 数值域降维：有限值域 fp32 双重补偿快链 + 特殊值整线精确回退
description: 把有限值主路径从 int64 超级累加器位操作链改为 Priest dd (hi,lo) 对累加，非有限值整线回退重扫。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/dd-compensated-finite-domain-scan.md
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
      "整线回退必须从线首重扫，回退路径（原 int64 慢链）须逐字保留且位级等价于 champion",
      "非有限检测分支须在快链每步之前，单分支 (x-x)!=0 形式，不可引入 per-element 多分支",
      "输出 (T)(hi+lo) 双舍入需与 golden 同构；精度护栏为相对误差阈值（MERE/MARE）而非 bit-exact 时才允许浮点对替换整数位精确链"
    ],
    "excluded_conditions": [
      "精度护栏要求 bit-exact 输出时：dd 快链为相对误差 ~2^-47，不满足逐位一致",
      "特殊值线占比高的数据分布（本 run case 12 全特殊值零收益；case 13 162877/162877 线全走回退，稳定 -2.2% 双扫描开销）：回退线要付两遍扫描成本，占比高则净负",
      "非 int64 超级累加器结构（若热链本就没有整数位操作链，无 3.5-4x 指令削减空间）"
    ],
    "required_conditions": [
      "profiling 显示 aiv_vec_ratio ≈ 1.0（VF 前端发射吞吐为唯一瓶颈），热链为逐元素串行依赖链",
      "慢链每元素 ~65 条 VF 指令且几乎全为整数位操作（位解析+对齐+msb 二分+变量移位 RNE）",
      "存在可从线首确定性重扫的回退语义（扫描类天然满足：只要能从线首重放即可 bit-exact）",
      "宿上位级仿真可先验验证：快链与 golden、回退触发集与实际数据分布三方对账"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 470.6,
      "before_us": 1040.5,
      "operator": "cumsum_minimum",
      "operator_class": "reduction",
      "pairs": 200,
      "pairs_per_case": 10,
      "precision": "20/20 PASS (host_sim_dd.py: 948 sampled lines bit-identical to torch golden)",
      "run_id": "<run-id>",
      "session_ids": ["ses_f79879d0affe0kvHcpTTKBIRm5"],
      "speedup": 2.211,
      "status": "accepted",
      "worst_case_ratio": 0.978
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-instruction-issue-bound",
      "int64-bit-manipulation-chain",
      "serial-dependency-chain"
    ],
    "pattern": "dd-compensated-finite-domain-fastloop",
    "structure": [
      "t1-gm-direct-vf",
      "priest-double-double-pair",
      "whole-line-exact-fallback",
      "threshold-guardrail-aware-domain-downgrade"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-DD-COMPENSATED-FINITE-DOMAIN",
  "implementation_steps": [
    "在热循环（本 run 为 cumsum_minimum_t1.h ScanLinesGmVF）线循环头部新增 Priest dd 快链：以 (x-x)!=0 单分支检测非有限值，命中即 break 整线回退",
    "快链以 2 次 Knuth 2Sum + 舍入误差回收的 (hi,lo) 对累加替代原 int64 超级累加器位操作链（~65 指令/元素 → ~16-18 指令/元素）",
    "输出按 (T)(hi+lo) 双舍入写出，保证与 golden 同构",
    "原 int64 循环体逐字保留置于 fast-continue 之后作为回退路径（从线首重扫，保证 bit-exact）",
    "不改 host/tiling/split/T2 与任何其它管线"
  ],
  "intent": "把有限值主路径从 int64 超级累加器位解析（~65 条 VF 整数位操作/元素）切换到 fp32 双重补偿浮点直线码（~16-18 条/元素），直接削减 aiv_vec 饱和瓶颈下的每元素指令数 3.5-4x，同时以整线回退保证特殊值语义位级不变。",
  "mechanism": "有限值域 fp32 双重补偿快链 + 特殊值整线回退：热循环主路径用 Priest dd (hi,lo) 对累加替代 int64 位精确累加；任何一步 hi+w 非有限（溢出/±inf/NaN，由单分支 (x-x)!=0 检测）立即中断并整线回退到逐字保留的 champion int64 慢链从线首重扫，从而在放宽到相对误差护栏的前提下获得 3.5-4x 的每元素指令削减，且特殊值语义保持位级不变。",
  "name": "数值域降维：有限值域 fp32 双重补偿快链 + 特殊值整线精确回退",
  "operator_class": "reduction",
  "operator_scope": "GM 直访 VF 热循环的扫描/前缀累加类算子（T1 模式），热链为逐元素串行 int64 超级累加器位操作链、VF 前端发射吞吐为唯一瓶颈、精度护栏为相对误差阈值而非 bit-exact",
  "principle": "当 aiv_vec_ratio≈1.0 时 wall 正比于 VF 每元素发射数。int64 位精确累加的代价是位解析+对齐+msb 二分+变量移位 RNE 的整数位操作链；若精度护栏允许相对误差（本 run MERE/MARE 允许 ~2^-23），可用 fp32 双重补偿（2Sum + 误差回收）把每元素指令数降到 1/4，代价是失去位精确性。恢复位精确性的唯一途径是「检测到超出有限域就从线首重扫」——扫描的确定性使整线重放天然 bit-exact，因此回退成本被限制在特殊值线的两遍扫描上，可用特殊值线占比预估净收益。",
  "related_anti_patterns": [
    "normalized-fixedpoint-superacc-constant-shift-rounding（同算子 d001：源码级指令削减在 bisheng VF 目标上编译为更大更慢代码，全零 case 2.39x 回退，登记为 negative_boundary）"
  ],
  "risks": [
    "回退线双扫描开销：case 13（162877/162877 线走回退）稳定 -2.2%，特殊值线占比更高的数据分布可能净负",
    "快链代码体积增量虽小（更简单直线码 + 1 分支，慢链作冷路径保留），但仍会改变 kernel 二进制体积，需在实测中确认不引发副作用",
    "dd 累加相对误差 ~2^-47 累积，长扫描链下需确认仍在护栏内（本 run 经 host_sim_dd.py 948 采样线验证）"
  ],
  "slug": "dd-compensated-finite-domain-scan",
  "summary": "把 GM 直访 VF 热循环（ScanLinesGmVF）的有限值主路径从「int64 超级累加器位解析+对齐+msb 二分+变量移位 RNE（~65 VF 指令/元素整数位操作）」整体切换为「Priest 双重补偿 fp32 (hi,lo) 对累加（2 次 Knuth 2Sum + 舍入误差回收，纯 add/sub 浮点直线码，~16-18 指令/元素）」，输出 (T)(hi+lo) 双舍入与 golden 同构；任何一步 hi+w 非有限（溢出/±inf/NaN，单分支 (x-x)!=0 检测）立即中断并整线回退到逐字保留的 champion int64 慢链从线首重扫（bit-exact 语义保障）。20 case 几何平均加速 2.211x（1040.5→470.6us）。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS；宿上位级仿真 host_sim_dd.py：20/20 case PASS，948 条采样线 vs torch golden 位级一致（MERE=MARE=0）",
      "特殊值回退集精确匹配：case 11 273/273 线、case 12 1/1、case 13 162877/162877 —— 回退触发集与实际数据分布完全对账"
    ],
    "performance": [
      "形式化 ABAB 平衡交替配对（A1 B1 A2 B2，每 block 新鲜构建，5 runs/case/block）：200 对，geomean 1040.5→470.6us（2.211x）",
      "18/20 case 10/10 全胜；case 12 零差异（6/10 at 1.000）；case 13 0/10 at 0.978（预测内的回退线双扫描开销，-2.2%）",
      "best_case_ratio 4.419 / worst_case_ratio 0.978；15/17 有限值 case 提速 52%-77%"
    ],
    "rollback_signals": [
      "特殊值线占比高于预测导致 geomean 回退",
      "宿上位级仿真出现快链/回退集与实际分布不对账",
      "worst_case_ratio 跌破 max_case_regression 阈值",
      "回退路径与 champion 语义不再位级一致"
    ]
  }
}
-->

# 性能优化策略：数值域降维：有限值域 fp32 双重补偿快链 + 特殊值整线精确回退

把 GM 直访 VF 热循环（ScanLinesGmVF）的有限值主路径从「int64 超级累加器位解析+对齐+msb 二分+变量移位 RNE（~65 VF 指令/元素整数位操作）」整体切换为「Priest 双重补偿 fp32 (hi,lo) 对累加（2 次 Knuth 2Sum + 舍入误差回收，纯 add/sub 浮点直线码，~16-18 指令/元素）」，输出 (T)(hi+lo) 双舍入与 golden 同构；任何一步 hi+w 非有限（溢出/±inf/NaN，单分支 (x-x)!=0 检测）立即中断并整线回退到逐字保留的 champion int64 慢链从线首重扫（bit-exact 语义保障）。20 case 几何平均加速 2.211x（1040.5→470.6us）。

## 1. 原理

当 aiv_vec_ratio≈1.0 时 wall 正比于 VF 每元素发射数。int64 位精确累加的代价是位解析+对齐+msb 二分+变量移位 RNE 的整数位操作链；若精度护栏允许相对误差（本 run MERE/MARE 允许 ~2^-23），可用 fp32 双重补偿（2Sum + 误差回收）把每元素指令数降到 1/4，代价是失去位精确性。恢复位精确性的唯一途径是「检测到超出有限域就从线首重扫」——扫描的确定性使整线重放天然 bit-exact，因此回退成本被限制在特殊值线的两遍扫描上，可用特殊值线占比预估净收益。

实现机制：有限值域 fp32 双重补偿快链 + 特殊值整线回退：热循环主路径用 Priest dd (hi,lo) 对累加替代 int64 位精确累加；任何一步 hi+w 非有限（溢出/±inf/NaN，由单分支 (x-x)!=0 检测）立即中断并整线回退到逐字保留的 champion int64 慢链从线首重扫，从而在放宽到相对误差护栏的前提下获得 3.5-4x 的每元素指令削减，且特殊值语义保持位级不变。

## 2. 性能问题模式

- 优化目标：把有限值主路径从 int64 超级累加器位解析（~65 条 VF 整数位操作/元素）切换到 fp32 双重补偿浮点直线码（~16-18 条/元素），直接削减 aiv_vec 饱和瓶颈下的每元素指令数 3.5-4x，同时以整线回退保证特殊值语义位级不变
- 适用数据流：GM 直访 VF 热循环的扫描/前缀累加类算子（T1 模式），热链为逐元素串行 int64 超级累加器位操作链、VF 前端发射吞吐为唯一瓶颈、精度护栏为相对误差阈值而非 bit-exact
- Feature signature：`{"bottleneck": ["vec-instruction-issue-bound", "int64-bit-manipulation-chain", "serial-dependency-chain"], "pattern": "dd-compensated-finite-domain-fastloop", "structure": ["t1-gm-direct-vf", "priest-double-double-pair", "whole-line-exact-fallback", "threshold-guardrail-aware-domain-downgrade"]}`

## 3. 正确性红线

- 回退线双扫描开销：case 13（162877/162877 线走回退）稳定 -2.2%，特殊值线占比更高的数据分布可能净负
- 快链代码体积增量虽小（更简单直线码 + 1 分支，慢链作冷路径保留），但仍会改变 kernel 二进制体积，需在实测中确认不引发副作用
- dd 累加相对误差 ~2^-47 累积，长扫描链下需确认仍在护栏内（本 run 经 host_sim_dd.py 948 采样线验证）

资源与硬件约束：

- 整线回退必须从线首重扫，回退路径（原 int64 慢链）须逐字保留且位级等价于 champion
- 非有限检测分支须在快链每步之前，单分支 (x-x)!=0 形式，不可引入 per-element 多分支
- 输出 (T)(hi+lo) 双舍入需与 golden 同构；精度护栏为相对误差阈值（MERE/MARE）而非 bit-exact 时才允许浮点对替换整数位精确链

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- profiling 显示 aiv_vec_ratio ≈ 1.0（VF 前端发射吞吐为唯一瓶颈），热链为逐元素串行依赖链
- 慢链每元素 ~65 条 VF 指令且几乎全为整数位操作（位解析+对齐+msb 二分+变量移位 RNE）
- 存在可从线首确定性重扫的回退语义（扫描类天然满足：只要能从线首重放即可 bit-exact）
- 宿上位级仿真可先验验证：快链与 golden、回退触发集与实际数据分布三方对账

不适用：

- 精度护栏要求 bit-exact 输出时：dd 快链为相对误差 ~2^-47，不满足逐位一致
- 特殊值线占比高的数据分布（本 run case 12 全特殊值零收益；case 13 162877/162877 线全走回退，稳定 -2.2% 双扫描开销）：回退线要付两遍扫描成本，占比高则净负
- 非 int64 超级累加器结构（若热链本就没有整数位操作链，无 3.5-4x 指令削减空间）

## 5. 实施步骤

1. 在热循环（本 run 为 cumsum_minimum_t1.h ScanLinesGmVF）线循环头部新增 Priest dd 快链：以 (x-x)!=0 单分支检测非有限值，命中即 break 整线回退
2. 快链以 2 次 Knuth 2Sum + 舍入误差回收的 (hi,lo) 对累加替代原 int64 超级累加器位操作链（~65 指令/元素 → ~16-18 指令/元素）
3. 输出按 (T)(hi+lo) 双舍入写出，保证与 golden 同构
4. 原 int64 循环体逐字保留置于 fast-continue 之后作为回退路径（从线首重扫，保证 bit-exact）
5. 不改 host/tiling/split/T2 与任何其它管线

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示 aiv_vec_ratio ≈ 1.0（VF 前端发射吞吐为唯一瓶颈），热链为逐元素串行依赖链？
- 目标实现是否满足：慢链每元素 ~65 条 VF 指令且几乎全为整数位操作（位解析+对齐+msb 二分+变量移位 RNE）？
- 目标实现是否满足：存在可从线首确定性重扫的回退语义（扫描类天然满足：只要能从线首重放即可 bit-exact）？
- 目标实现是否满足：宿上位级仿真可先验验证：快链与 golden、回退触发集与实际数据分布三方对账？
- 是否命中排除条件：精度护栏要求 bit-exact 输出时：dd 快链为相对误差 ~2^-47，不满足逐位一致？

## 7. 验收标准

正确性：

- 精度 20/20 PASS；宿上位级仿真 host_sim_dd.py：20/20 case PASS，948 条采样线 vs torch golden 位级一致（MERE=MARE=0）
- 特殊值回退集精确匹配：case 11 273/273 线、case 12 1/1、case 13 162877/162877 —— 回退触发集与实际数据分布完全对账

性能：

- 形式化 ABAB 平衡交替配对（A1 B1 A2 B2，每 block 新鲜构建，5 runs/case/block）：200 对，geomean 1040.5→470.6us（2.211x）
- 18/20 case 10/10 全胜；case 12 零差异（6/10 at 1.000）；case 13 0/10 at 0.978（预测内的回退线双扫描开销，-2.2%）
- best_case_ratio 4.419 / worst_case_ratio 0.978；15/17 有限值 case 提速 52%-77%

回滚信号：

- 特殊值线占比高于预测导致 geomean 回退
- 宿上位级仿真出现快链/回退集与实际分布不对账
- worst_case_ratio 跌破 max_case_regression 阈值
- 回退路径与 champion 语义不再位级一致

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：`normalized-fixedpoint-superacc-constant-shift-rounding`（同算子 d001：源码级指令削减在 bisheng VF 目标上编译为更大更慢代码，全零 case 2.39x 回退，登记为 negative_boundary）

- loop_20260909_010738-free-002（operator=cumsum_minimum, status=accepted, speedup=2.211, 1040.5→470.6us, 200 对 ABAB）

## 检索卡（短卡）

动作：把有限值主路径从 int64 超级累加器位操作链改为 Priest dd (hi,lo) 对累加，非有限值整线回退重扫
适用：aiv_vec_ratio≈1.0、慢链每元素约 65 条 VF 整数位操作，护栏为相对误差阈值
限制：回退须从线首重扫且原 int64 慢链逐字保留；非有限检测须单分支 (x-x)!=0；输出 (T)(hi+lo) 双舍入须与 golden 同构
范围：reduction 的 GM 直访 VF 扫描/前缀累加类算子（T1 模式）
检索词：Priest dd、Knuth 2Sum、(hi,lo) 累加、int64 超级累加器、整线回退
机会：wall 正比于 VF 每元素发射数，整数位操作链占满发射槽
代价：特殊值线付两遍扫描成本（占比高则净负）；dd 相对误差 ~2^-47 长链累积
