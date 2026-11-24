---
type: Optimization
title: p=1/p=2 专用廉价 reduce 路径替代 Ln/Exp 幂模拟
description: p=1时用绝对值与恒等收尾，p=2时用平方累加与sqrt收尾，替代Ln/Exp。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/pow-pspecific-fast-reduce-paths.md
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
      "POWMODE 模板维度三倍化 POS_P 的 VF 实例（编译时间/对象体积小幅增加；每次调用仅两次 float compare，非每元素开销）",
      "尾部 lane 中和必须保留：任何后续编辑删除 Select(..., zeroReg, ...) 会引入 vector-api-unaligned-overread 类标量污染",
      "修改必须保持 mask/tail 处理、dtype 分派、tiling 路由、同步结构与 workspace 布局不变"
    ],
    "excluded_conditions": [
      "p 不在 {1,2} 的有限 p（1.5/2.5/3/4/5/-1）——必须保留 Ln/Exp 通用路径",
      "PMODE_ZERO / PMODE_POS_INF / PMODE_NEG_INF——已有专用分支，不触碰",
      "fp32 4B/element p=1/p=2 场景已处于 ~78GB/s MTE2 带宽下限时，移除 Ln/Exp 不转化为 per-kernel 收益（实测 4 个 fp32 case 中性、无回归）"
    ],
    "required_conditions": [
      "pMode==PMODE_POS_P 且 p 精确等于 1.0f 或 2.0f（1.0f/2.0f 在 float 中精确可表示，== 比较安全；近邻值自动落入通用路径，永不错误只是不快）",
      "p=1 累加器 Σ|x| 与 p=2 累加器 Σx² 非负，finalize 直通/Sqrt 良定义（含全零输入 sqrt(0)=0）",
      "每个 fast path 在 full-width Add/ReduceSum 前用 Select 将 tail lane 中和为 0，保持与通用路径一致的尾处理",
      "VF 层存在 runtime pMode dispatch 或模板维度可插入编译期分派"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "2813334daebb34bb795d4201e127324e1669d610cd8c9cf3b293d5801ec77242",
      "decision_sha256": "57dd678abb10ea8874f2a58d73eb168de34bf603b0a2af63ee296b0517a567e9",
      "operator_class": "reduction",
      "performance_sha256": "38ac27b68590aa1fe7be48fbd09eebfc8f03003c7135e161d21876cd50540cae",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "055d75bb40d35fdcfbec57626151e8519cf1af1f694f0a5e8f8bffc344c2adf5",
      "verify_sha256": "a621a3f1c76e1f07608d9e27cc65eed3cfe66e80ea78560400cfd8d60cf375df"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "transcendental-emulation",
      "vec-instruction-count"
    ],
    "dtypes": [
      "fp16",
      "bf16"
    ],
    "guard": [
      "exact-float-p-in-1-2",
      "p-tail-neutralized-to-zero"
    ],
    "pattern": "pow-pspecific-fast-reduce",
    "structure": [
      "regbase-vf-reduce",
      "ln-exp-pow-emulation",
      "compile-time-powmode-dispatch"
    ]
  },
  "generality": "op_class",
  "id": "NORM-POW-PSPECIFIC-FAST-REDUCE",
  "implementation_steps": [
    "定义编译期 POWMODE 常量（POW_GENERIC/POW_P1/POW_P2）并作为 VF_0/VF_1/VF_2 模板的第三维",
    "POW_P1：VF_0 共享 Abs 后 Select 中和 tail lane 再 Add（无 Ln/Exp）；POW_P2：Mul-self 后 Select 中和 tail 再 Add",
    "finalize/merge-finalize：POW_P1 直通 acc；POW_P2 用 Sqrt(acc)；POW_GENERIC 保留 Ln->Muls(invP)->Exp",
    "在三个 __aicore__ wrapper 的 PMODE_POS_P 分支内按 p==1.0f/p==2.0f 分派，其他 pMode 分支不动",
    "保留通用路径逐字节不变，重新跑完整 correctness/精度门禁与 measure 验收"
  ],
  "intent": "消除 VEC 对每个元素重复执行的高延迟超越函数 Ln/Exp（reduce 与 finalize 各一次）在 fp16/bf16 p=1/p=2 工作负载上的主导开销",
  "mechanism": "在三个 __aicore__ wrapper（ComputeNormReducePartial / ComputeNormFinalize / ComputeNormMergeFinalize）对 (pMode==PMODE_POS_P && p==1.0f)/(p==2.0f) 提前分派到编译期 POWMODE 模板维度（POW_P1/POW_P2/POW_GENERIC），使 per-branch 指令 mix 在 codegen 时固定（无每元素 runtime predicate）。POW_P1 在 VF_0 共享 Abs 后 Select 中和 tail lane 再 Add；POW_P2 用 Mul-self + Select 中和 tail + Add；VF_1/VF_2 finalize 分别为直通与 Sqrt。POW_GENERIC（默认）保持 Ln->Muls(p)->Exp / Ln->Muls(invP)->Exp 逐字节不变。p 以 float 端到端透传（host attrs -> tiling->p -> p_），== 比较安全。",
  "name": "p=1/p=2 专用廉价 reduce 路径替代 Ln/Exp 幂模拟",
  "operator_class": "reduction",
  "operator_scope": "Lp 范数类归约算子（ForeachNorm / LpNorm / 逐张量范数）的 VF reduce/finalize/merge-finalize：对每个 PMODE_POS_P 元素执行 Ln->Muls(p)->Exp 幂模拟，且 p 以 float 端到端透传、1.0f/2.0f 精确可表示",
  "principle": "|x|^p 对精确可表示的 p=1/2 存在无超越函数的代数恒等（|x|^1=|x|、|x|^2=x*x，finalize 分别为恒等与 sqrt(acc)，且 acc=Σ|x|/Σx² 非负保证良定义）。对 p=1/p=2 在编译期 POWMODE 模板维度上绕过 Ln/Exp 可大幅降低每元素 VEC 指令数；收益是否落地取决于瓶颈归属——仅当 VEC 是临界流水时（fp16/bf16 2B/element 场景成立），fp32 4B/element 已处 MTE2 带宽下限时移除超越函数不转化为 per-kernel 收益。",
  "related_anti_patterns": [],
  "risks": [
    "float 相等分派依赖 p 端到端透传：若调用方算术构造 p（如 2.0*0.5 有舍入）会错过 fast path——安全（回落通用路径），只是不快",
    "移除 Ln/Exp 的收益依赖瓶颈归属：fp32/带宽 bound 场景指令削减不转化为时延收益（实测 4 个 fp32 case 中性、无回归），不可把该机制外推为所有 dtype 通用",
    "POWMODE 三实例化增大 kernel 对象体积；若 tail 中和被误删会破坏 full-width reduce 正确性"
  ],
  "slug": "pow-pspecific-fast-reduce-paths",
  "summary": "对 pMode==PMODE_POS_P 且 p 精确等于 1.0f/2.0f 的输入，在 VF reduce/finalize/merge-finalize 中用廉价代数路径替换 Ln/Exp 幂模拟：p=1 用 Abs+ReduceSum 且 finalize 直通（acc^(1/1)=acc），p=2 用 Mul-self+ReduceSum 且 finalize 用 Sqrt（acc^(1/2)=sqrt(acc)）；其他有限 p 与 ZERO/+-inf 分支保持原路径逐字节不变。实测 fp16/bf16 p=1/p=2 工作负载 7/11 目标 case 提升 1.48-1.76x，fp32 p=1/p=2 case 中性（已到 MTE2 带宽下限）。",
  "verification": {
    "correctness": [
      "rounds/001 verify ok=true，11/11 目标 case（1,2,3,4,9,10,11,14,15,16,18）全部通过；kernel_hash 1e427900d86ddb75 与 build.json kernel_after 一致",
      "fp16/fp32 relative_error ~2^-13、bf16 ~2^-10/2^-7 容差内；p=1/p=2 fast path 与 Ln/Exp 路径在 fp32 计算内的 ULP 差在精度门禁内"
    ],
    "performance": [
      "7/11 目标 case 实测 1.48-1.76x：case 3 891.696->507.774us（1.756x）、case 16 1.686x、case 10 1.629x、case 1 1.636x、case 4 1.496x、case 9 1.483x、case 14 1.486x，全部是 fp16/bf16 p=1/p=2",
      "selector 子集加权 total 1.4684x（4614.562->3142.675us），7 improved / 0 regressed，超过 minimum_total_speedup=1.02",
      "4 个 fp32 p=1/p=2 case（2/11/15/18）中性（1.0057-1.0163x）——已处 ~78GB/s MTE2 带宽下限，不回归"
    ],
    "rollback_signals": [
      "任一 case 正确性失败或漂移超门禁",
      "case 3（或 p=1/p=2 组整体）无 measurable per-kernel 改善——证伪 Ln/Exp-dominance 假设",
      "未触碰的 generic-p / ZERO / ±inf case 超出样本噪声回归",
      "tail-lane 中和或对齐处理回归并触发 vector-api-unaligned-overread 类错误"
    ]
  }
}
-->

# 性能优化策略：p=1/p=2 专用廉价 reduce 路径替代 Ln/Exp 幂模拟

单一优化点：对 pMode==PMODE_POS_P 且 p 精确等于 1.0f/2.0f 的输入，在 VF reduce/finalize/merge-finalize 中用廉价代数路径替换 Ln/Exp 幂模拟：p=1 用 Abs+ReduceSum 且 finalize 直通（acc^(1/1)=acc），p=2 用 Mul-self+ReduceSum 且 finalize 用 Sqrt（acc^(1/2)=sqrt(acc)）；其他有限 p 与 ZERO/+-inf 分支保持原路径逐字节不变。实测 fp16/bf16 p=1/p=2 工作负载 7/11 目标 case 提升 1.48-1.76x，fp32 p=1/p=2 case 中性（已到 MTE2 带宽下限）。

## 1. 原理

|x|^p 对精确可表示的 p=1/2 存在无超越函数的代数恒等（|x|^1=|x|、|x|^2=x*x，finalize 分别为恒等与 sqrt(acc)，且 acc=Σ|x|/Σx² 非负保证良定义）。对 p=1/p=2 在编译期 POWMODE 模板维度上绕过 Ln/Exp 可大幅降低每元素 VEC 指令数；收益是否落地取决于瓶颈归属——仅当 VEC 是临界流水时（fp16/bf16 2B/element 场景成立），fp32 4B/element 已处 MTE2 带宽下限时移除超越函数不转化为 per-kernel 收益。

实现机制：在三个 __aicore__ wrapper（ComputeNormReducePartial / ComputeNormFinalize / ComputeNormMergeFinalize）对 (pMode==PMODE_POS_P && p==1.0f)/(p==2.0f) 提前分派到编译期 POWMODE 模板维度（POW_P1/POW_P2/POW_GENERIC），使 per-branch 指令 mix 在 codegen 时固定（无每元素 runtime predicate）。POW_P1 在 VF_0 共享 Abs 后 Select 中和 tail lane 再 Add；POW_P2 用 Mul-self + Select 中和 tail + Add；VF_1/VF_2 finalize 分别为直通与 Sqrt。POW_GENERIC（默认）保持 Ln->Muls(p)->Exp / Ln->Muls(invP)->Exp 逐字节不变。p 以 float 端到端透传（host attrs -> tiling->p -> p_），== 比较安全。

## 2. 性能问题模式

- 优化目标：消除 VEC 对每个元素重复执行的高延迟超越函数 Ln/Exp（reduce 与 finalize 各一次）在 fp16/bf16 p=1/p=2 工作负载上的主导开销
- 适用数据流：Lp 范数类归约算子（ForeachNorm / LpNorm / 逐张量范数）的 VF reduce/finalize/merge-finalize：对每个 PMODE_POS_P 元素执行 Ln->Muls(p)->Exp 幂模拟，且 p 以 float 端到端透传、1.0f/2.0f 精确可表示
- Feature signature：`{"bottleneck": ["vec-bound", "transcendental-emulation", "vec-instruction-count"], "dtypes": ["fp16", "bf16"], "guard": ["exact-float-p-in-1-2", "p-tail-neutralized-to-zero"], "pattern": "pow-pspecific-fast-reduce", "structure": ["regbase-vf-reduce", "ln-exp-pow-emulation", "compile-time-powmode-dispatch"]}`

## 3. 正确性红线

- float 相等分派依赖 p 端到端透传：若调用方算术构造 p（如 2.0*0.5 有舍入）会错过 fast path——安全（回落通用路径），只是不快
- 移除 Ln/Exp 的收益依赖瓶颈归属：fp32/带宽 bound 场景指令削减不转化为时延收益（实测 4 个 fp32 case 中性、无回归），不可把该机制外推为所有 dtype 通用
- POWMODE 三实例化增大 kernel 对象体积；若 tail 中和被误删会破坏 full-width reduce 正确性

资源与硬件约束：

- POWMODE 模板维度三倍化 POS_P 的 VF 实例（编译时间/对象体积小幅增加；每次调用仅两次 float compare，非每元素开销）
- 尾部 lane 中和必须保留：任何后续编辑删除 Select(..., zeroReg, ...) 会引入 vector-api-unaligned-overread 类标量污染
- 修改必须保持 mask/tail 处理、dtype 分派、tiling 路由、同步结构与 workspace 布局不变

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- pMode==PMODE_POS_P 且 p 精确等于 1.0f 或 2.0f（1.0f/2.0f 在 float 中精确可表示，== 比较安全；近邻值自动落入通用路径，永不错误只是不快）
- p=1 累加器 Σ|x| 与 p=2 累加器 Σx² 非负，finalize 直通/Sqrt 良定义（含全零输入 sqrt(0)=0）
- 每个 fast path 在 full-width Add/ReduceSum 前用 Select 将 tail lane 中和为 0，保持与通用路径一致的尾处理
- VF 层存在 runtime pMode dispatch 或模板维度可插入编译期分派

不适用：

- p 不在 {1,2} 的有限 p（1.5/2.5/3/4/5/-1）——必须保留 Ln/Exp 通用路径
- PMODE_ZERO / PMODE_POS_INF / PMODE_NEG_INF——已有专用分支，不触碰
- fp32 4B/element p=1/p=2 场景已处于 ~78GB/s MTE2 带宽下限时，移除 Ln/Exp 不转化为 per-kernel 收益（实测 4 个 fp32 case 中性、无回归）

## 5. 实施步骤

1. 定义编译期 POWMODE 常量（POW_GENERIC/POW_P1/POW_P2）并作为 VF_0/VF_1/VF_2 模板的第三维
2. POW_P1：VF_0 共享 Abs 后 Select 中和 tail lane 再 Add（无 Ln/Exp）；POW_P2：Mul-self 后 Select 中和 tail 再 Add
3. finalize/merge-finalize：POW_P1 直通 acc；POW_P2 用 Sqrt(acc)；POW_GENERIC 保留 Ln->Muls(invP)->Exp
4. 在三个 __aicore__ wrapper 的 PMODE_POS_P 分支内按 p==1.0f/p==2.0f 分派，其他 pMode 分支不动
5. 保留通用路径逐字节不变，重新跑完整 correctness/精度门禁与 measure 验收

## 6. LLM 前置问题

- 目标实现是否满足：pMode==PMODE_POS_P 且 p 精确等于 1.0f 或 2.0f（1.0f/2.0f 在 float 中精确可表示，== 比较安全；近邻值自动落入通用路径，永不错误只是不快）？
- 目标实现是否满足：p=1 累加器 Σ|x| 与 p=2 累加器 Σx² 非负，finalize 直通/Sqrt 良定义（含全零输入 sqrt(0)=0）？
- 目标实现是否满足：每个 fast path 在 full-width Add/ReduceSum 前用 Select 将 tail lane 中和为 0，保持与通用路径一致的尾处理？
- 是否命中排除条件：p 不在 {1,2} 的有限 p（1.5/2.5/3/4/5/-1）——必须保留 Ln/Exp 通用路径？

## 7. 验收标准

正确性：

- rounds/001 verify ok=true，11/11 目标 case（1,2,3,4,9,10,11,14,15,16,18）全部通过；kernel_hash 1e427900d86ddb75 与 build.json kernel_after 一致
- fp16/fp32 relative_error ~2^-13、bf16 ~2^-10/2^-7 容差内；p=1/p=2 fast path 与 Ln/Exp 路径在 fp32 计算内的 ULP 差在精度门禁内

性能：

- 7/11 目标 case 实测 1.48-1.76x：case 3 891.696->507.774us（1.756x）、case 16 1.686x、case 10 1.629x、case 1 1.636x、case 4 1.496x、case 9 1.483x、case 14 1.486x，全部是 fp16/bf16 p=1/p=2
- selector 子集加权 total 1.4684x（4614.562->3142.675us），7 improved / 0 regressed，超过 minimum_total_speedup=1.02
- 4 个 fp32 p=1/p=2 case（2/11/15/18）中性（1.0057-1.0163x）——已处 ~78GB/s MTE2 带宽下限，不回归

回滚信号：

- 任一 case 正确性失败或漂移超门禁
- case 3（或 p=1/p=2 组整体）无 measurable per-kernel 改善——证伪 Ln/Exp-dominance 假设
- 未触碰的 generic-p / ZERO / ±inf case 超出样本噪声回归
- tail-lane 中和或对齐处理回归并触发 vector-api-unaligned-overread 类错误

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- foreach_norm-20260823_153850-f56b93（round=1, status=accepted）

## 检索卡（短卡）

动作：p=1时用绝对值与恒等收尾，p=2时用平方累加与sqrt收尾，替代Ln/Exp
适用：PMODE_POS_P下p精确等于1.0f或2.0f
限制：相等分派要求p端到端透传；算术构造产生舍入时仅错过快速路径
范围：normalization的fp16/bf16正p归约路径
检索词：POWMODE、POW_P1、POW_P2、Ln/Exp、sqrt、Lp范数
机会：reduce与finalize对每个元素重复执行Ln/Exp
