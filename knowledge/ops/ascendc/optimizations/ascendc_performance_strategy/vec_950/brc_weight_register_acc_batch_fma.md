---
type: Optimization
title: 标量管减压：广播权重进寄存器 + 列累加器跨行驻留的批式乘累加
description: 把逐行 VF 调用的 mask 重建与累加器 UB 往返改为按批单次 VF，权重广播进寄存器、列累加器跨 R 行驻留。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/brc-weight-register-acc-batch-fma.md
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
      "数值运算顺序与数值须不变（vaxpy-vmadd 同融合 MAC 指令族、同累加次序、权重闭式与递推同值），否则精度风险不可控",
      "广播加载依赖 DIST_BRC_B32 的 4B 对齐地址序列，权重表须按该对齐契约排布",
      "段 mask 与 accVec 的装载/写回按段外提后，段边界语义须与逐行版本一致"
    ],
    "excluded_conditions": [
      "MulDstAdd 语义不可按直觉使用：本 run r1 误用 dst+=s0*s1 语义（实为 dst*s0+s1）导致精度失败，r2 改 Mul+Add 两指令后退回三指令形态——使用前须在产线内核核实语义",
      "行数 R 很小（逐行固定开销摊薄不掉）或列宽 W 很小时，批式重构的收益不足以覆盖 mask/accVec 外提成本",
      "若权重不满足闭式（不能以 a=i+p 代入向量化生成），广播寄存器驻留方案不成立"
    ],
    "required_conditions": [
      "profiling 显示 aiv_scalar 为剩余主瓶颈且接近 pacing 满忙（本 run aiv_scalar 37.90us > aiv_vec 22.85us > aiv_mte2 14.80us > aiv_mte3 1.41us；重 case scalar/aiv 比值 0.92-0.996）",
      "热循环存在逐行 VF 调用：每行的 mask 重建 + 累加器 UB-寄存器往返 + __aicore__ 包装 + 标量递推均为 scalar 管指令",
      "CANN 版本提供 DIST_BRC_B32 广播加载（vlds BRC）与融合乘加指令（本 run CANN 9.2.0 dav_m510 Reg API，layer_norm_v3 产线内核同型用法）",
      "权重可闭式向量化生成：covH(i) 与 covW(j) 为同一闭式 GenCovWChunkImpl，以 a=i+p、上限 hOut 代入即可生成批内 R 行权重，纯 V 流水无 PIPE_S 参与"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 14.6394,
      "before_us": 23.738,
      "operator": "unfold_mean",
      "operator_class": "reduction",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": ["ses_f79f53612ffehxuExMiOpc9d0U", "ses_f7986b1eeffeifCofIAtjV5cyM"],
      "speedup": 1.6215,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipe-pacing",
      "per-row-vf-call-overhead",
      "ub-register-roundtrip"
    ],
    "pattern": "broadcast-weight-register-resident-accumulator",
    "structure": [
      "batch-single-vf-call",
      "dist-brc-b32-broadcast-weight",
      "cross-row-register-accumulator",
      "variant-mask-and-accumulator-hoist"
    ]
  },
  "generality": "op_class",
  "id": "UM-BRC-WEIGHT-REGISTER-ACC-BATCH-FMA",
  "implementation_steps": [
    "op_kernel: 新增 AccumRowCovHBatchImpl/VF——段(i) 外层每段每批一次 UpdateMask + accReg LoadAlign，段尾一次 StoreAlign",
    "行(r) 内层：POST_MODE_UPDATE 行距指针加载 x 段 + DIST_BRC_B32 广播 covH[r] + 乘累加，accReg 跨 R 行寄存器驻留（每行每段矢量指令 5→4 条）",
    "op_kernel: 新增 covHArr_ TBuf(256B)，每批 GenCovWChunkVF 闭式生成 covH 权重（a=i0+r+p、上限 hOut，纯 V 流水）",
    "op_kernel: 删除 AccumRowCovHImpl/VF、CovHNext 标量双指针递推与 lhHi_/lhLo_ 状态",
    "ComputeMainRow/ComputeSplitPartial 两个调用点替换为新的批式 VF"
  ],
  "intent": "把 (m,wc) 块内逐行 VF 调用的固定开销（mask 重建、累加器 UB-寄存器往返、__aicore__ 包装、标量递推）摊薄为每批一次，把每行每段矢量指令从 5 条降到 3-4 条，直接压缩 scalar 管的发射压力。",
  "mechanism": "将 (m,wc) 块内逐行 vf_1 累加（每行一次 VF 调用：LoadAcc+Axpy+StoreAcc+UpdateMask+CovHNext 标量递推）重构为按批单次 VF 调用：covH 权重闭式向量化生成到 UB，经 DIST_BRC_B32 广播加载进寄存器，列累加器跨 R 行驻留寄存器，逐行仅 Load-x + 广播-w + 乘累加三条矢量指令；段 mask 与 accVec 装载/写回按段外提（每批一次而非每行一次）。",
  "name": "标量管减压：广播权重进寄存器 + 列累加器跨行驻留的批式乘累加",
  "operator_class": "reduction",
  "operator_scope": "aiv_scalar pacing 的逐行累加循环类算子：每行一次 VF 调用含 mask 重建与累加器 UB 往返、权重可由闭式向量化生成、硬件提供广播加载与融合乘加指令",
  "principle": "scalar 管接近 pacing 满忙时，瓶颈不在矢量计算量而在逐行 VF 调用的固定开销（mask 重建、accVec 的 UB-寄存器往返、__aicore__ 包装、指针递推）。把「按行调用」改成「按批调用」，把这些固定项从 per-row 提到 per-batch，同时用广播加载让权重直接进寄存器、列累加器跨行驻留，逐行只剩三条矢量指令。数值不变的前提是新旧指令属同一融合 MAC 族且累加次序一致。",
  "related_anti_patterns": [],
  "risks": [
    "MulDstAdd 语义陷阱：本 run r1 按 dst+=s0*s1 理解（实为 dst*s0+s1，经 group_norm_grad 产线核实）导致精度失败，r2 改 Mul+Add 两指令；精度修复预算消耗 2/3",
    "covHArr_ TBuf（256B）新增 UB 足迹，需对账预算",
    "广播权重方案假设权重在批内可闭式生成；若某算子权重需递推维护，须另找寄存器驻留路径"
  ],
  "slug": "brc-weight-register-acc-batch-fma",
  "summary": "把 (m,wc) 块内逐行 vf_1 累加（每行一次 VF 调用：LoadAcc+Axpy+StoreAcc+UpdateMask+CovHNext 标量递推）重构为按批单次 VF 调用：covH 权重闭式向量化生成到 UB，经 DIST_BRC_B32 广播加载进寄存器，列累加器跨 R 行驻留寄存器，逐行仅 Load-x + 广播-w + 乘累加三条矢量指令；段 mask 与 accVec 装载/写回按段外提。kernel geomean 23.738→14.6394us（x1.6215），aiv_scalar 37.88→15.39us（-59%）。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（evidence_run/rounds/round_01/accuracy）",
      "数值不变论证：vaxpy-vmadd 同融合 MAC 指令族、同累加次序、covH 闭式与递推同值",
      "修复史：r1 MulDstAdd 语义错误致精度失败；r2 改 Mul+Add 两指令；r3 最终形态（精度修复预算用 2/3、编译修复 0/3）"
    ],
    "performance": [
      "形式化性能 10 对平衡交替（同 shape、溯源干净）：逐对比值 1.6114-1.6273 全部 >1",
      "kernel_geomean_us 23.738→14.6394（x1.6215）",
      "aiv_scalar 37.88→15.39us（-59%）；重 case 最高 x2.70（case5 172.6→63.9us）"
    ],
    "rollback_signals": [
      "精度失败（融合 MAC 指令语义误用或累加次序改变）",
      "aiv_scalar 未下降或 aiv_vec 因额外 load 饱和",
      "未达到配对对比值全部 >1 的门槛"
    ]
  }
}
-->

# 性能优化策略：标量管减压：广播权重进寄存器 + 列累加器跨行驻留的批式乘累加

把 (m,wc) 块内逐行 vf_1 累加（每行一次 VF 调用：LoadAcc+Axpy+StoreAcc+UpdateMask+CovHNext 标量递推）重构为按批单次 VF 调用：covH 权重闭式向量化生成到 UB，经 DIST_BRC_B32 广播加载进寄存器，列累加器跨 R 行驻留寄存器，逐行仅 Load-x + 广播-w + 乘累加三条矢量指令；段 mask 与 accVec 装载/写回按段外提。kernel geomean 23.738→14.6394us（x1.6215），aiv_scalar 37.88→15.39us（-59%）。

## 1. 原理

scalar 管接近 pacing 满忙时，瓶颈不在矢量计算量而在逐行 VF 调用的固定开销（mask 重建、accVec 的 UB-寄存器往返、__aicore__ 包装、指针递推）。把「按行调用」改成「按批调用」，把这些固定项从 per-row 提到 per-batch，同时用广播加载让权重直接进寄存器、列累加器跨行驻留，逐行只剩三条矢量指令。数值不变的前提是新旧指令属同一融合 MAC 族且累加次序一致。

实现机制：将 (m,wc) 块内逐行 vf_1 累加（每行一次 VF 调用：LoadAcc+Axpy+StoreAcc+UpdateMask+CovHNext 标量递推）重构为按批单次 VF 调用：covH 权重闭式向量化生成到 UB，经 DIST_BRC_B32 广播加载进寄存器，列累加器跨 R 行驻留寄存器，逐行仅 Load-x + 广播-w + 乘累加三条矢量指令；段 mask 与 accVec 装载/写回按段外提（每批一次而非每行一次）。

## 2. 性能问题模式

- 优化目标：把 (m,wc) 块内逐行 VF 调用的固定开销（mask 重建、累加器 UB-寄存器往返、__aicore__ 包装、标量递推）摊薄为每批一次，把每行每段矢量指令从 5 条降到 3-4 条，直接压缩 scalar 管的发射压力
- 适用数据流：aiv_scalar pacing 的逐行累加循环类算子：每行一次 VF 调用含 mask 重建与累加器 UB 往返、权重可由闭式向量化生成、硬件提供广播加载与融合乘加指令
- Feature signature：`{"bottleneck": ["scalar-pipe-pacing", "per-row-vf-call-overhead", "ub-register-roundtrip"], "pattern": "broadcast-weight-register-resident-accumulator", "structure": ["batch-single-vf-call", "dist-brc-b32-broadcast-weight", "cross-row-register-accumulator", "variant-mask-and-accumulator-hoist"]}`

## 3. 正确性红线

- MulDstAdd 语义陷阱：本 run r1 按 dst+=s0*s1 理解（实为 dst*s0+s1，经 group_norm_grad 产线核实）导致精度失败，r2 改 Mul+Add 两指令；精度修复预算消耗 2/3
- covHArr_ TBuf（256B）新增 UB 足迹，需对账预算
- 广播权重方案假设权重在批内可闭式生成；若某算子权重需递推维护，须另找寄存器驻留路径

资源与硬件约束：

- 数值运算顺序与数值须不变（vaxpy-vmadd 同融合 MAC 指令族、同累加次序、权重闭式与递推同值），否则精度风险不可控
- 广播加载依赖 DIST_BRC_B32 的 4B 对齐地址序列，权重表须按该对齐契约排布
- 段 mask 与 accVec 的装载/写回按段外提后，段边界语义须与逐行版本一致

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- profiling 显示 aiv_scalar 为剩余主瓶颈且接近 pacing 满忙（本 run aiv_scalar 37.90us > aiv_vec 22.85us > aiv_mte2 14.80us > aiv_mte3 1.41us；重 case scalar/aiv 比值 0.92-0.996）
- 热循环存在逐行 VF 调用：每行的 mask 重建 + 累加器 UB-寄存器往返 + __aicore__ 包装 + 标量递推均为 scalar 管指令
- CANN 版本提供 DIST_BRC_B32 广播加载（vlds BRC）与融合乘加指令（本 run CANN 9.2.0 dav_m510 Reg API，layer_norm_v3 产线内核同型用法）
- 权重可闭式向量化生成：covH(i) 与 covW(j) 为同一闭式 GenCovWChunkImpl，以 a=i+p、上限 hOut 代入即可生成批内 R 行权重，纯 V 流水无 PIPE_S 参与

不适用：

- MulDstAdd 语义不可按直觉使用：本 run r1 误用 dst+=s0*s1 语义（实为 dst*s0+s1）导致精度失败，r2 改 Mul+Add 两指令后退回三指令形态——使用前须在产线内核核实语义
- 行数 R 很小（逐行固定开销摊薄不掉）或列宽 W 很小时，批式重构的收益不足以覆盖 mask/accVec 外提成本
- 若权重不满足闭式（不能以 a=i+p 代入向量化生成），广播寄存器驻留方案不成立

## 5. 实施步骤

1. op_kernel: 新增 AccumRowCovHBatchImpl/VF——段(i) 外层每段每批一次 UpdateMask + accReg LoadAlign，段尾一次 StoreAlign
2. 行(r) 内层：POST_MODE_UPDATE 行距指针加载 x 段 + DIST_BRC_B32 广播 covH[r] + 乘累加，accReg 跨 R 行寄存器驻留（每行每段矢量指令 5→4 条）
3. op_kernel: 新增 covHArr_ TBuf(256B)，每批 GenCovWChunkVF 闭式生成 covH 权重（a=i0+r+p、上限 hOut，纯 V 流水）
4. op_kernel: 删除 AccumRowCovHImpl/VF、CovHNext 标量双指针递推与 lhHi_/lhLo_ 状态
5. ComputeMainRow/ComputeSplitPartial 两个调用点替换为新的批式 VF

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示 aiv_scalar 为剩余主瓶颈且接近 pacing 满忙（本 run aiv_scalar 37.90us > aiv_vec 22.85us > aiv_mte2 14.80us > aiv_mte3 1.41us；重 case scalar/aiv 比值 0.92-0.996）？
- 目标实现是否满足：热循环存在逐行 VF 调用：每行的 mask 重建 + 累加器 UB-寄存器往返 + __aicore__ 包装 + 标量递推均为 scalar 管指令？
- 目标实现是否满足：CANN 版本提供 DIST_BRC_B32 广播加载（vlds BRC）与融合乘加指令（本 run CANN 9.2.0 dav_m510 Reg API，layer_norm_v3 产线内核同型用法）？
- 目标实现是否满足：权重可闭式向量化生成：covH(i) 与 covW(j) 为同一闭式 GenCovWChunkImpl，以 a=i+p、上限 hOut 代入即可生成批内 R 行权重，纯 V 流水无 PIPE_S 参与？
- 是否命中排除条件：MulDstAdd 语义不可按直觉使用：本 run r1 误用 dst+=s0*s1 语义（实为 dst*s0+s1）导致精度失败，r2 改 Mul+Add 两指令后退回三指令形态——使用前须在产线内核核实语义？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（evidence_run/rounds/round_01/accuracy）
- 数值不变论证：vaxpy-vmadd 同融合 MAC 指令族、同累加次序、covH 闭式与递推同值
- 修复史：r1 MulDstAdd 语义错误致精度失败；r2 改 Mul+Add 两指令；r3 最终形态（精度修复预算用 2/3、编译修复 0/3）

性能：

- 形式化性能 10 对平衡交替（同 shape、溯源干净）：逐对比值 1.6114-1.6273 全部 >1
- kernel_geomean_us 23.738→14.6394（x1.6215）
- aiv_scalar 37.88→15.39us（-59%）；重 case 最高 x2.70（case5 172.6→63.9us）

回滚信号：

- 精度失败（融合 MAC 指令语义误用或累加次序改变）
- aiv_scalar 未下降或 aiv_vec 因额外 load 饱和
- 未达到配对对比值全部 >1 的门槛

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-001（operator=unfold_mean, status=accepted, speedup=1.6215, 23.738→14.6394us, 10 对配对）

## 检索卡（短卡）

动作：把逐行 VF 调用的 mask 重建与累加器 UB 往返改为按批单次 VF，权重广播进寄存器、列累加器跨 R 行驻留
适用：aiv_scalar 为剩余主瓶颈且接近 pacing 满忙；热循环每行一次 VF 调用；权重可闭式向量化生成
限制：数值顺序须不变；MulDstAdd 语义须在产线内核核实；广播加载依赖 DIST_BRC_B32 的 4B 对齐地址序列
范围：reduction 的 aiv_scalar pacing 逐行累加循环
检索词：DIST_BRC_B32、vlds BRC、covHArr_、UpdateMask、LoadAlign
机会：逐行 VF 调用固定开销（mask 重建、累加器 UB-寄存器往返、标量递推）全压在 scalar 管
代价：新增 covHArr_ TBuf（256B）UB 足迹，须对账预算
