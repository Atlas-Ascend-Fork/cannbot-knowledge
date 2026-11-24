---
type: Optimization
title: 范围归约边界折返消除：删除数值上不可达的 ±π fold 对
description: cosreshape 的 cos 核心在 rint-magic + 3 项 Cody-Waite 范围归约之后仍然跑两组 ±π 边界折返（2×[Adds + CompareScalar + Select]，占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条）。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/range-reduction-boundary-fold-elimination.md
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
      "删除必须给出『残余上界 × 余项增长因子 × 对护栏余量』的解析论证（本 run <=~4e-3 漂移 -> 余项 1.39e-7 -> ~1.42e-7，因子 <=1.024，对 1e-5 余量 ~70 倍）",
      "范围归约与 Horner 链逐字不动，折返-free 的 r 直接喂 t=r*r；改动面只含折返对、tmpReg 张量与 COS_PI/COS_TWO_PI 常量",
      "inf/NaN 路径必须核对：本 run ±inf 仍在第一条 Axpy 处得到 inf-inf=NaN，NaN 传播不变",
      "护栏是容差型（fp32 atol/rtol=1e-5）而非 bit-exact；精度验收用与基线一致的报告（本 run 逐 case 指标一致、最差 case 10 fp16 [-65504,65504] atol_fail=0）",
      "改动应是单文件单处（kernel/cosreshape_kernel.h），不牵动 tiling/host 与其它 dtype 路径"
    ],
    "excluded_conditions": [
      "精度护栏要求逐位一致（bit-exact）时不适用：删除会改变超界输入的最终取值（哪怕只在 ~4e-3 的漂移域内），这类管线须保留折返",
      "前置范围归约不能提供残余上界时不适用：本机制的全部合法性来自『折返不可达』的解析论证，而不是『测试没触发』",
      "本机制不改变多项式链本身（级数截断 / 次数 / 共享硬件恒等式复用属于 transcendental-chain-algebraization 的域），也不做 load/cast 前端形式与除法形式改写（那是 vec-frontend-instruction-diet 的域，其自身排除条款已声明『要求逐位一致的输出』时不适用）",
      "折返以外的代码不得顺手改动：范围归约与 Horner 链必须逐字保留，否则收益归因与误差论证同时失效",
      "低精度路径的护栏与 fp32 不同（本 run fp16/bf16 松 100-1000 倍），fp32 的论证不可直接搬运，各 dtype 需分别给出"
    ],
    "required_conditions": [
      "VEC 管道承载任务时间的主体且核已饱和：本 run aiv_vec 19.30us（77.4%），aiv_scalar 3.61us（14.5%）、aiv_mte2 2.35us（9.4%）、aiv_mte3 1.60us（6.4%）；大 case vec_ratio 0.88-0.89；Block Num=32 on every launch、Aicore Count=32（核扩展零空间）",
      "被删代码是管道上的一块可观指令：折返对占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条（~23%）",
      "前置范围归约已把残余量约束住，使折返在数值上不可达：rint-magic + 3 项 Cody-Waite 后残余只在舍入漂移内超过 π，测试幅度下上界 ~6e-5（n<=163）到 ~4e-3（n~10426）",
      "误差预算可解析且余量可量化：级数余项 1.39e-7 -> 至多 ~1.42e-7（增长因子 <=1.024），对 fp32 atol/rtol=1e-5 余量 ~70 倍，fp16/bf16 护栏 1e-3/1e-2 更松 100-1000 倍",
      "特殊值路径不因此改变：±inf 仍在第一条 Axpy 处变 NaN（inf-inf），NaN 继续传播"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "cosreshape",
      "operator_class": "elementwise",
      "precision": "20/20 PASS（报告与基线一致；最差 case 10 fp16 [-65504,65504] atol_fail=0）",
      "run_id": "<run-id>",
      "speedup": 1.1555,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "vec-instruction-count",
      "numerically-unreachable-reduction-epilogue"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "range-reduction-boundary-fold-elimination",
    "reduce_mode": "",
    "structure": [
      "rint-magic-cody-waite-range-reduction",
      "boundary-fold-deletion",
      "analytic-error-budget-vs-guardrail",
      "dead-tensor-and-constant-removal",
      "horner-chain-verbatim"
    ]
  },
  "generality": "op_class",
  "id": "VEC-BOUNDARY-FOLD-ELIMINATION",
  "implementation_steps": [
    "先记账：数清每 repeat 的核心向量指令构成与各块占比（本 run fp32 repeat = rint magic 3 + Cody-Waite Axpy 3 + 边界折返 6 + t=r*r 1 + Horner Q7 17 ≈ 26），确认被删块是管道上可观的整数条指令",
    "给出解析误差预算：残余超界上界（~6e-5..~4e-3）、级数余项增长（1.39e-7 -> ~1.42e-7，因子 <=1.024）、与最紧护栏的倍数余量（fp32 1e-5 下 ~70 倍，fp16/bf16 护栏松 100-1000 倍）",
    "删除两组 ±π 折返对（原第 84-94 行）及随之死掉的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量；范围归约与 Horner 链逐字保留，折返-free 的 r 直接喂 t=r*r",
    "核对特殊值路径（±inf 在第一条 Axpy 处仍得 NaN、NaN 继续传播）与三个 dtype 的护栏余量",
    "以 20/20 精度门（报告与基线逐 case 指标一致）+ 形式化配对 ABBA 验收，并核对逐 dtype 改善一致（本 run bf16 -12.7%、fp16 -13.8%、fp32 -13.9%）"
  ],
  "intent": "删除 CosReshapeCosCore 里数值上不可达的两组 ±π 边界折返（2×[Adds+CompareScalar+Select]，占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条），只削减 VEC 发射数——该管承载 77.4% 的 Task Duration，且 32/32 个 AIV 核已全部饱和，核心向量指令数是唯一的一阶杠杆。",
  "mechanism": "reduction-boundary-fold-elimination：CosReshapeCosCore 的每 64-lane fp32 repeat 原本是 rint magic 3 + Cody-Waite Axpy 3 + 边界折返 6（2×[Adds+CompareScalar+Select]）+ t=r*r 1 + Horner Q7 17（Duplicate + 7×[Mul+Adds] + 末 Mul+Adds）≈ 26 条核心向量指令。修复删除了两组 ±π 折返对（原第 84-94 行）以及因此变成死代码的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量；范围归约（rint-magic 的 Muls+2×Adds、3 项 Cody-Waite Axpy）与 degree-7 Horner 链逐字未动，折返-free 的残余 r 直接喂给 t=r*r。删除的合法性来自误差预算：归约后残余超过 π 的量级由测试幅度上界给出——n<=163 时 ~6e-5、n~10426 时 ~4e-3；级数余项 |r|^18/18! 从 1.39e-7 抬到至多 ~1.42e-7（增长因子 <=1.024），对 fp32 atol/rtol=1e-5 余量约 70 倍，fp16/bf16 护栏（1e-3/1e-2）更松 100-1000 倍；±inf 仍在第一条 Axpy 处变 NaN（inf-inf）、NaN 继续传播，可观测行为不变。单文件单处改动（kernel/cosreshape_kernel.h），不牵动 tiling/host 与其它 dtype 路径。",
  "name": "范围归约边界折返消除：删除数值上不可达的 ±π fold 对",
  "operator_class": "elementwise",
  "operator_scope": "VEC 管道主导（本 run aiv_vec 19.30us = 77.4% Task Duration，大 case vec_ratio 0.88-0.89）、核已满（Block Num=32 on every launch、Aicore Count=32）、且工作内容含『范围归约 + 截断级数』两段式超越函数核心的逐元素算子；精度护栏是容差型而非 bit-exact。",
  "principle": "死代码不总在源码里，也可能在数值上——这是『容差型精度护栏』下的一类可删除对象。当护栏是容差（fp32 atol/rtol=1e-5、fp16 1e-3、bf16 1e-2）而不是逐位一致时，一条指令只要其输出对最终误差的贡献远小于护栏余量，它就是可删的，哪怕它在语义上仍然会被执行。本 run 的边界折返就是这种情形：前置的范围归约已经把残余量约束到 ±π 附近（只在舍入漂移内超界），而这个漂移对截断级数余项的影响只有 2.4%（1.39e-7 -> ~1.42e-7），对最紧护栏仍有 ~70 倍余量。判据是『可解析论证的误差上界 × 量化余量』，不是『看起来不会发生』；并且必须同时核对特殊值路径（inf/NaN）与 dtype 更紧的护栏——fp16/bf16 的护栏本 run 松 100-1000 倍，但论证仍需分别给出。机制的作用面严格限定在归约的 epilogue：多项式链本身、load/cast 前端形式与除法形式都不属于本机制。",
  "related_anti_patterns": [],
  "risks": [
    "误差论证依赖测试幅度上界：本 run 的 ~4e-3 残余超界与 ~1.42e-7 余项上界都来自 |x| 到 65504 的测试域；输入幅度更大时两者都要重算",
    "把『源码里看起来不会发生』当成论证：折返在语义上仍会被执行，删除的合法性只能来自解析误差上界与量化余量",
    "误删范围归约或 Horner 链的任一环会让误差论证与收益归因同时失效（改动面必须严格限定在折返对及其死常量）",
    "inf/NaN 行为若曾被折返掩盖，删除后可能改变可观测结果——本 run 核对为不变，换算子必须单独核对",
    "同一杠杆类里收益与削减比例不成比例：同族兄弟方向 vec-pipe::hw-intrinsic-idiom-substitution::cos-core（rint-magic→vtrc、Duplicate+Mul→Muls，-2 of 25 核心向量指令即 -8.0%）在形式化配对上只有 1.0290x——必须按配对测量而非按指令数预测"
  ],
  "slug": "range-reduction-boundary-fold-elimination",
  "summary": "cosreshape 的 cos 核心在 rint-magic + 3 项 Cody-Waite 范围归约之后仍然跑两组 ±π 边界折返（2×[Adds + CompareScalar + Select]，占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条）。这两组折返在数值上不可达：归约后的残余量只在舍入漂移范围内超过 π（|r| <= π + ~4e-3，|x| 到 65504 时），它把 degree-16 截断级数的余项从 1.39e-7 最多抬到 ~1.42e-7——仍比最紧的 fp32 atol/rtol=1e-5 低约 70 倍，inf/NaN 行为不变。删除两组折返对 + 已死的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量，范围归约与 Horner 链逐字保留：核心向量指令 ~26→~20（-23%），外层 msprof device Task Duration geomean 24.636→21.321us（1.1555x，-13.5%，5 对 balanced ABBA 的每一对每个 case 都更快），三个 dtype 一致（bf16 -12.7%、fp16 -13.8%、fp32 -13.9%），精度 20/20 且报告与基线一致（零修复轮次）。",
  "verification": {
    "correctness": [
      "20/20 PASS，零修复轮次；报告与基线一致（除时间戳），最差 case 10 fp16 [-65504,65504] atol_fail=0",
      "inf/NaN 行为不变：±inf 仍在第一条 Axpy 处 inf-inf=NaN，NaN 继续传播",
      "改动面严格限定：两组折返对（2×[Adds+CompareScalar+Select]，原第 84-94 行）+ 死掉的 tmpReg 张量 + COS_PI/COS_TWO_PI 常量；范围归约与 degree-7 Horner 链逐字未动"
    ],
    "performance": [
      "形式化配对 5 对 balanced ABBA（10 次测量，provenance-clean 双 .so，同一 20 个 cached shape）：候选在每一对的每个 case 上都更快；baseline 24.636us vs candidate 21.321us geomean = 1.1555x（-13.5%）",
      "逐 dtype 一致：bf16 20.683→18.050（-12.7%）、fp16 25.229→21.750（-13.8%）、fp32 28.656→24.688（-13.9%）",
      "screening 24.927→21.645us（-13.2%）；核心向量指令 ~26→~20 per 64-lane fp32 repeat（-23%）",
      "冻结基线 24.636us 与方向记录的 champion BEST_MS 24.633us 一致"
    ],
    "rollback_signals": [
      "任一精度 case 在删除后 FAIL 且无 >=5% 的补偿收益",
      "形式化配对 geomean 相对冻结 champion 回退",
      "超界漂移上界被推翻（输入幅度域扩大使残余可能显著超过 π）",
      "inf/NaN 可观测行为改变",
      "改动溢出到范围归约 / Horner 链，使误差论证不再适用"
    ]
  }
}
-->

# 性能优化策略：范围归约边界折返消除：删除数值上不可达的 ±π fold 对

cosreshape 的 cos 核心在 rint-magic + 3 项 Cody-Waite 范围归约之后仍然跑两组 ±π 边界折返（2×[Adds + CompareScalar + Select]，占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条）。这两组折返在数值上不可达：归约后的残余量只在舍入漂移范围内超过 π（|r| <= π + ~4e-3，|x| 到 65504 时），它把 degree-16 截断级数的余项从 1.39e-7 最多抬到 ~1.42e-7——仍比最紧的 fp32 atol/rtol=1e-5 低约 70 倍，inf/NaN 行为不变。删除两组折返对 + 已死的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量，范围归约与 Horner 链逐字保留：核心向量指令 ~26→~20（-23%），外层 msprof device Task Duration geomean 24.636→21.321us（1.1555x，-13.5%，5 对 balanced ABBA 的每一对每个 case 都更快），三个 dtype 一致（bf16 -12.7%、fp16 -13.8%、fp32 -13.9%），精度 20/20 且报告与基线一致（零修复轮次）。

## 1. 原理

死代码不总在源码里，也可能在数值上——这是『容差型精度护栏』下的一类可删除对象。当护栏是容差（fp32 atol/rtol=1e-5、fp16 1e-3、bf16 1e-2）而不是逐位一致时，一条指令只要其输出对最终误差的贡献远小于护栏余量，它就是可删的，哪怕它在语义上仍然会被执行。本 run 的边界折返就是这种情形：前置的范围归约已经把残余量约束到 ±π 附近（只在舍入漂移内超界），而这个漂移对截断级数余项的影响只有 2.4%（1.39e-7 -> ~1.42e-7），对最紧护栏仍有 ~70 倍余量。判据是『可解析论证的误差上界 × 量化余量』，不是『看起来不会发生』；并且必须同时核对特殊值路径（inf/NaN）与 dtype 更紧的护栏——fp16/bf16 的护栏本 run 松 100-1000 倍，但论证仍需分别给出。机制的作用面严格限定在归约的 epilogue：多项式链本身、load/cast 前端形式与除法形式都不属于本机制。

实现机制：reduction-boundary-fold-elimination：CosReshapeCosCore 的每 64-lane fp32 repeat 原本是 rint magic 3 + Cody-Waite Axpy 3 + 边界折返 6（2×[Adds+CompareScalar+Select]）+ t=r*r 1 + Horner Q7 17（Duplicate + 7×[Mul+Adds] + 末 Mul+Adds）≈ 26 条核心向量指令。修复删除了两组 ±π 折返对（原第 84-94 行）以及因此变成死代码的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量；范围归约（rint-magic 的 Muls+2×Adds、3 项 Cody-Waite Axpy）与 degree-7 Horner 链逐字未动，折返-free 的残余 r 直接喂给 t=r*r。删除的合法性来自误差预算：归约后残余超过 π 的量级由测试幅度上界给出——n<=163 时 ~6e-5、n~10426 时 ~4e-3；级数余项 |r|^18/18! 从 1.39e-7 抬到至多 ~1.42e-7（增长因子 <=1.024），对 fp32 atol/rtol=1e-5 余量约 70 倍，fp16/bf16 护栏（1e-3/1e-2）更松 100-1000 倍；±inf 仍在第一条 Axpy 处变 NaN（inf-inf）、NaN 继续传播，可观测行为不变。单文件单处改动（kernel/cosreshape_kernel.h），不牵动 tiling/host 与其它 dtype 路径。

## 2. 性能问题模式

- 优化目标：删除 CosReshapeCosCore 里数值上不可达的两组 ±π 边界折返（2×[Adds+CompareScalar+Select]，占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条），只削减 VEC 发射数——该管承载 77.4% 的 Task Duration，且 32/32 个 AIV 核已全部饱和，核心向量指令数是唯一的一阶杠杆。
- 适用数据流：VEC 管道主导（本 run aiv_vec 19.30us = 77.4% Task Duration，大 case vec_ratio 0.88-0.89）、核已满（Block Num=32 on every launch、Aicore Count=32）、且工作内容含『范围归约 + 截断级数』两段式超越函数核心的逐元素算子；精度护栏是容差型而非 bit-exact。
- Feature signature：`{"bottleneck": ["vec-bound", "vec-instruction-count", "numerically-unreachable-reduction-epilogue"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "range-reduction-boundary-fold-elimination", "reduce_mode": "", "structure": ["rint-magic-cody-waite-range-reduction", "boundary-fold-deletion", "analytic-error-budget-vs-guardrail", "dead-tensor-and-constant-removal", "horner-chain-verbatim"]}`

## 3. 正确性红线

- 误差论证依赖测试幅度上界：本 run 的 ~4e-3 残余超界与 ~1.42e-7 余项上界都来自 |x| 到 65504 的测试域；输入幅度更大时两者都要重算
- 把『源码里看起来不会发生』当成论证：折返在语义上仍会被执行，删除的合法性只能来自解析误差上界与量化余量
- 误删范围归约或 Horner 链的任一环会让误差论证与收益归因同时失效（改动面必须严格限定在折返对及其死常量）
- inf/NaN 行为若曾被折返掩盖，删除后可能改变可观测结果——本 run 核对为不变，换算子必须单独核对
- 同一杠杆类里收益与削减比例不成比例：同族兄弟方向 vec-pipe::hw-intrinsic-idiom-substitution::cos-core（rint-magic→vtrc、Duplicate+Mul→Muls，-2 of 25 核心向量指令即 -8.0%）在形式化配对上只有 1.0290x——必须按配对测量而非按指令数预测

资源与硬件约束：

- 删除必须给出『残余上界 × 余项增长因子 × 对护栏余量』的解析论证（本 run <=~4e-3 漂移 -> 余项 1.39e-7 -> ~1.42e-7，因子 <=1.024，对 1e-5 余量 ~70 倍）
- 范围归约与 Horner 链逐字不动，折返-free 的 r 直接喂 t=r*r；改动面只含折返对、tmpReg 张量与 COS_PI/COS_TWO_PI 常量
- inf/NaN 路径必须核对：本 run ±inf 仍在第一条 Axpy 处得到 inf-inf=NaN，NaN 传播不变
- 护栏是容差型（fp32 atol/rtol=1e-5）而非 bit-exact；精度验收用与基线一致的报告（本 run 逐 case 指标一致、最差 case 10 fp16 [-65504,65504] atol_fail=0）
- 改动应是单文件单处（kernel/cosreshape_kernel.h），不牵动 tiling/host 与其它 dtype 路径

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- VEC 管道承载任务时间的主体且核已饱和：本 run aiv_vec 19.30us（77.4%），aiv_scalar 3.61us（14.5%）、aiv_mte2 2.35us（9.4%）、aiv_mte3 1.60us（6.4%）；大 case vec_ratio 0.88-0.89；Block Num=32 on every launch、Aicore Count=32（核扩展零空间）
- 被删代码是管道上的一块可观指令：折返对占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条（~23%）
- 前置范围归约已把残余量约束住，使折返在数值上不可达：rint-magic + 3 项 Cody-Waite 后残余只在舍入漂移内超过 π，测试幅度下上界 ~6e-5（n<=163）到 ~4e-3（n~10426）
- 误差预算可解析且余量可量化：级数余项 1.39e-7 -> 至多 ~1.42e-7（增长因子 <=1.024），对 fp32 atol/rtol=1e-5 余量 ~70 倍，fp16/bf16 护栏 1e-3/1e-2 更松 100-1000 倍
- 特殊值路径不因此改变：±inf 仍在第一条 Axpy 处变 NaN（inf-inf），NaN 继续传播

不适用：

- 精度护栏要求逐位一致（bit-exact）时不适用：删除会改变超界输入的最终取值（哪怕只在 ~4e-3 的漂移域内），这类管线须保留折返
- 前置范围归约不能提供残余上界时不适用：本机制的全部合法性来自『折返不可达』的解析论证，而不是『测试没触发』
- 本机制不改变多项式链本身（级数截断 / 次数 / 共享硬件恒等式复用属于 transcendental-chain-algebraization 的域），也不做 load/cast 前端形式与除法形式改写（那是 vec-frontend-instruction-diet 的域，其自身排除条款已声明『要求逐位一致的输出』时不适用）
- 折返以外的代码不得顺手改动：范围归约与 Horner 链必须逐字保留，否则收益归因与误差论证同时失效
- 低精度路径的护栏与 fp32 不同（本 run fp16/bf16 松 100-1000 倍），fp32 的论证不可直接搬运，各 dtype 需分别给出

## 5. 实施步骤

1. 先记账：数清每 repeat 的核心向量指令构成与各块占比（本 run fp32 repeat = rint magic 3 + Cody-Waite Axpy 3 + 边界折返 6 + t=r*r 1 + Horner Q7 17 ≈ 26），确认被删块是管道上可观的整数条指令
2. 给出解析误差预算：残余超界上界（~6e-5..~4e-3）、级数余项增长（1.39e-7 -> ~1.42e-7，因子 <=1.024）、与最紧护栏的倍数余量（fp32 1e-5 下 ~70 倍，fp16/bf16 护栏松 100-1000 倍）
3. 删除两组 ±π 折返对（原第 84-94 行）及随之死掉的 tmpReg 张量与 COS_PI/COS_TWO_PI 常量；范围归约与 Horner 链逐字保留，折返-free 的 r 直接喂 t=r*r
4. 核对特殊值路径（±inf 在第一条 Axpy 处仍得 NaN、NaN 继续传播）与三个 dtype 的护栏余量
5. 以 20/20 精度门（报告与基线逐 case 指标一致）+ 形式化配对 ABBA 验收，并核对逐 dtype 改善一致（本 run bf16 -12.7%、fp16 -13.8%、fp32 -13.9%）

## 6. LLM 前置问题

- 目标实现是否满足：VEC 管道承载任务时间的主体且核已饱和：本 run aiv_vec 19.30us（77.4%），aiv_scalar 3.61us（14.5%）、aiv_mte2 2.35us（9.4%）、aiv_mte3 1.60us（6.4%）；大 case vec_ratio 0.88-0.89；Block Num=32 on every launch、Aicore Count=32（核扩展零空间）？
- 目标实现是否满足：被删代码是管道上的一块可观指令：折返对占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条（~23%）？
- 目标实现是否满足：前置范围归约已把残余量约束住，使折返在数值上不可达：rint-magic + 3 项 Cody-Waite 后残余只在舍入漂移内超过 π，测试幅度下上界 ~6e-5（n<=163）到 ~4e-3（n~10426）？
- 目标实现是否满足：误差预算可解析且余量可量化：级数余项 1.39e-7 -> 至多 ~1.42e-7（增长因子 <=1.024），对 fp32 atol/rtol=1e-5 余量 ~70 倍，fp16/bf16 护栏 1e-3/1e-2 更松 100-1000 倍？
- 目标实现是否满足：特殊值路径不因此改变：±inf 仍在第一条 Axpy 处变 NaN（inf-inf），NaN 继续传播？
- 是否命中排除条件：精度护栏要求逐位一致（bit-exact）时不适用：删除会改变超界输入的最终取值（哪怕只在 ~4e-3 的漂移域内），这类管线须保留折返？
- 是否命中排除条件：前置范围归约不能提供残余上界时不适用：本机制的全部合法性来自『折返不可达』的解析论证，而不是『测试没触发』？
- 是否命中排除条件：本机制不改变多项式链本身（级数截断 / 次数 / 共享硬件恒等式复用属于 transcendental-chain-algebraization 的域），也不做 load/cast 前端形式与除法形式改写（那是 vec-frontend-instruction-diet 的域，其自身排除条款已声明『要求逐位一致的输出』时不适用）？
- 是否命中排除条件：折返以外的代码不得顺手改动：范围归约与 Horner 链必须逐字保留，否则收益归因与误差论证同时失效？
- 是否命中排除条件：低精度路径的护栏与 fp32 不同（本 run fp16/bf16 松 100-1000 倍），fp32 的论证不可直接搬运，各 dtype 需分别给出？

## 7. 验收标准

正确性：

- 20/20 PASS，零修复轮次；报告与基线一致（除时间戳），最差 case 10 fp16 [-65504,65504] atol_fail=0
- inf/NaN 行为不变：±inf 仍在第一条 Axpy 处 inf-inf=NaN，NaN 继续传播
- 改动面严格限定：两组折返对（2×[Adds+CompareScalar+Select]，原第 84-94 行）+ 死掉的 tmpReg 张量 + COS_PI/COS_TWO_PI 常量；范围归约与 degree-7 Horner 链逐字未动

性能：

- 形式化配对 5 对 balanced ABBA（10 次测量，provenance-clean 双 .so，同一 20 个 cached shape）：候选在每一对的每个 case 上都更快；baseline 24.636us vs candidate 21.321us geomean = 1.1555x（-13.5%）
- 逐 dtype 一致：bf16 20.683→18.050（-12.7%）、fp16 25.229→21.750（-13.8%）、fp32 28.656→24.688（-13.9%）
- screening 24.927→21.645us（-13.2%）；核心向量指令 ~26→~20 per 64-lane fp32 repeat（-23%）
- 冻结基线 24.636us 与方向记录的 champion BEST_MS 24.633us 一致

回滚信号：

- 任一精度 case 在删除后 FAIL 且无 >=5% 的补偿收益
- 形式化配对 geomean 相对冻结 champion 回退
- 超界漂移上界被推翻（输入幅度域扩大使残余可能显著超过 π）
- inf/NaN 可观测行为改变
- 改动溢出到范围归约 / Horner 链，使误差论证不再适用

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260916_165309 status=accepted, speedup=1.1555, precision=20/20 PASS（报告与基线一致；最差 case 10 fp16 [-65504,65504] atol_fail=0））

## 检索卡（短卡）

动作：把范围归约后数值上不可达的 ±π 边界折返对删除，连同已死的 tmpReg 与 COS_PI/COS_TWO_PI 常量。
适用：VEC 主导且核已饱和、折返对占每 repeat 约 23% 指令、前置归约能给出残余上界、护栏为容差型。
限制：bit-exact 管线不适用；残余上界必须解析论证；范围归约与 Horner 链须逐字保留。
范围：两段式超越函数核心（范围归约 + 截断级数）的逐元素 epilogue。
检索词：Cody-Waite、rint-magic、CompareScalar、Select、Horner、COS_PI
机会：折返对占每 64-lane fp32 repeat 约 26 条核心向量指令中的 6 条，VEC 管承载 77.4%。
代价：删除只在容差护栏下成立，输入幅度域扩大会推翻残余漂移上界。
