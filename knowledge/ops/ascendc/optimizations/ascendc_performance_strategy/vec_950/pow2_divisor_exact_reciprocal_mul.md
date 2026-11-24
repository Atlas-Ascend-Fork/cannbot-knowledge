---
type: Optimization
title: 2 的幂除数精确倒数乘法：以 Reg::Mul 替换分箱链的 0-ULP Div
description: 把热向量体的 0-ULP 精确除法改为乘 host 位运算门控下发的精确 2 的幂倒数，按编译期模板参量在乘法与除法间分派。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/pow2-divisor-exact-reciprocal-mul.md
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
      "host 门控必须是位运算判定精确 2 的幂并排除 0/次正规/inf/NaN（尾数位全 0、指数位非全 0/全 1）；只有 pow2 的倒数无舍入，才能把 rangeRecip=1.0f/rangeVal 当作精确值下发",
      "rangePow2(uint32)/rangeRecip(float) 作为 MaxHistcTiling 尾部追加字段，前段布局不变；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化",
      "分派必须是编译期（if constexpr 在 Mul 与 Div 之间选择），不得在向量循环体内引入运行时分支；ComputeBinsVF（非融合回退路径）与 final kernel 未改动",
      "模板实例倍增使 .so 达 10.81MB（FusedRowScanVF 模板实例 +0.26MB），必须确认 icache miss 稳态未恶化（实测 1.2-1.6%）"
    ],
    "excluded_conditions": [
      "除数不是 2 的幂时不适用：非 pow2 的 range 保持原 Div 路径作为回退门控（本 run 的回退路径无套件覆盖，如实记录）",
      "允许有界数值误差而非要求逐位一致时不适用——那是 relaxed-division-mode 的域：把 0-ULP 除法切成硬件快速模式、以精度契约换吞吐，与本机制方向相反",
      "热链上的 0-ULP 除法不是唯一/主导多槽指令时收益不可期：本机制的收益直接等于该指令在向量管上的占比",
      "对象不是浮点 0-ULP 向量除法时不适用：pow-pspecific-fast-reduce-paths 换的是幂模拟的 Ln/Exp 超越链，divfree-binary-roundbody-int32-scoped 换的是整数 vdiv 轮体，机制、对象与证明均不同"
    ],
    "required_conditions": [
      "热向量体里存在唯一的多槽精确算术指令且它是向量管主导：champion FusedRowScanVF 的 64 元素向量循环体（fp32 约 26 条向量指令）中唯一多槽精确算术指令是 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div（分箱链 tmp=(v-min)*bins/range），实测删除后 main kernel aiv_vec 55-57us -> 6.4us（-88%），其开销约占 champion 向量管 86%，远超探索时 k≈4-6 槽的保守估算",
      "除数是运行期标量、且测试/perf case 全部落在 2 的幂上：全部 20 个 case 的 histc attrs 均为 min=-1/max_val=1 -> rangeVal=2.0，bins=3，[1024,1024] dim=-1 -> fused=1，全部命中 Mul 路径",
      "存在编译期分派点，使向量循环体内无运行时分支：FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false），分派点在 FusedPhaseB 每行一次（按 main kernel 成员 rangePow2_ 判定），main kernel 的 rangePow2_/rangeRecip_ 从 tiling 初始化",
      "可保逐位一致（限于已测有限正常数域）：IEEE-754 下除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，分箱边界与 torch.histc 判箱逐位不变；NaN 输入在 Div 前已被 valid 掩码 Select 为 minR，不会进入除法。subnormal 边界需先确认 `Reg::Mul` 的 FTZ 语义；未确认前不得宣称全边界逐位一致"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "task_0314_max_histc",
      "operator_class": "scan",
      "precision": "20/20 PASS（hist_exact 全 True，分箱计数逐位一致）",
      "run_id": "<run-id>",
      "speedup": 1.7263,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "div-dominant",
      "high-precision-divide",
      "vec-instruction-issue-bound",
      "single-multislot-arith-per-rep"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "pow2-exact-reciprocal-mul",
    "reduce_mode": "fused-scan-bin-chain",
    "structure": [
      "host-bitwise-pow2-gate",
      "exact-reciprocal-shipped-in-tiling",
      "compile-time-template-dispatch",
      "runtime-original-div-fallback",
      "bitwise-identical-rounding"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-POW2-EXACT-RECIPROCAL-MUL",
  "implementation_steps": [
    "host 侧在 kernel/pybind11.cpp 加 rangeVal 位运算门控：尾数位全 0、指数位非全 0/全 1 判定为精确 2 的幂（排除 0/次正规/inf/NaN），命中时写 rangePow2=1 且 rangeRecip=1.0f/rangeVal（精确）",
    "在 MaxHistcTiling 尾部追加 rangePow2(uint32)/rangeRecip(float) 两字段，前段布局不变；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化",
    "在 kernel/maxhistc_kernel.h 给 FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false）与 recipR 寄存器，用 if constexpr 在 Reg::Mul(tmp,tmp,recipR) 与原 Reg::Div 之间分派",
    "把分派点上提到 FusedPhaseB：按 rangePow2_ 每行分派一次，保证向量循环体内没有运行时分支；非 pow2 保持原 Div 路径作回退",
    "以 20/20 精度门（hist_exact 全 True）与形式化 ABBA 配对验收，并复核 .so 体积增幅（+0.26MB）未使 icache miss 稳态恶化（1.2-1.6%）"
  ],
  "intent": "在精度契约不放松的前提下，去掉热向量体里 0-ULP 精确除法在 A5 向量管上的极长微码序列成本：当除数是运行期常量且被 host 静态判定为精确 2 的幂时，把向量循环体内的 Reg::Div 换成一次 Reg::Mul（乘精确倒数），非 pow2 保留原路径作回退。",
  "mechanism": "pow2-exact-reciprocal-mul：host 侧在 kernel/pybind11.cpp 用位运算门控 rangeVal（maxValF-minValF）是否为精确 2 的幂——尾数位全 0、且指数位非全 0/全 1（排除 0/次正规/inf/NaN）——命中时向 tiling 写 rangePow2=1 与精确倒数 rangeRecip=1.0f/rangeVal（pow2 的倒数无舍入），MaxHistcTiling 尾部追加 rangePow2(uint32)/rangeRecip(float) 两字段（前段布局不变）。kernel 侧 maxhistc_kernel.h 给 FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false）与 recipR 寄存器，用 if constexpr 在 Reg::Mul(tmp,tmp,recipR) 与原 Reg::Div 之间分派；分派点在 FusedPhaseB 每行一次（按 rangePow2_ 判定），向量循环体内没有运行时分支；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化。ComputeBinsVF（非融合回退路径）与 final kernel 未改动；一次应用、零修复轮。非 2 的幂 range 保持原 Div 路径作为回退门控。",
  "name": "2 的幂除数精确倒数乘法：以 Reg::Mul 替换分箱链的 0-ULP Div",
  "operator_class": "scan",
  "operator_scope": "热向量循环体内含浮点 0-ULP 精确除法、除数是运行期标量且可取到 2 的幂的算子；典型如直方图/分箱家族（本 run max_histc 的 FusedRowScanVF 分箱链 tmp=(v-min)*bins/range，bins=3、[1024,1024] dim=-1 fused=1，main+final 两个 kernel、三 dtype）",
  "principle": "向量管的近全部时间可以挂在一条多槽微码指令上，而这条指令的语义往往可以被等价的廉价指令替换。本 run 的 max_histc champion 在 FusedRowScanVF 的每 64 元素向量循环体（fp32 约 26 条向量指令）里，唯一的多槽精确算术指令就是分箱链 tmp=(v-min)*bins/range 中 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div，其余每个槽位都是单条 compare/select/add/mul/cast；实测把它删掉后 main kernel 的 aiv_vec 由 55-57us 降到 6.4us（-88%），即这条 0-ULP 除法约吃掉 champion 向量管的 86%，远超探索时 k≈4-6 槽的保守估算。既然除数是运行期标量而所有 case 的 rangeVal 恰好是 2.0，就可以利用 IEEE-754 的一条精确事实：在 IEEE-754 语义下（未启用 FTZ），对任意有限/无穷/NaN/±0 输入，除以 2^k 与乘以精确的 2^-k 是同一实数的单次正确舍入，二者逐位相同；上溢/下溢/次正规边界也只在 Mul 不 flush subnormal 时成立。本 run 的实测域是有限正常数，不能把该边界结论外推到 subnormal 输入/输出；`Reg::Mul` 受 `--cce-ftz` 控制（默认 true），若目标编译选项会 flush subnormal，则含 subnormal 的 case 必须回退 Div 路径。于是把『运行期精确除法』换成『运行期精确倒数 × 一次乘法』，除数是否 2 的幂由 host 用位运算静态判定并下发：这是与 relaxed-division-mode 方向相反的取舍——后者把 0-ULP 除法换成硬件快速模式、以精度契约换吞吐，本机制不放松任何精度契约，反而把结果锁到与精确除法逐位一致；也与 pow-pspecific-fast-reduce-paths（换的是幂模拟里的 Ln/Exp 超越链）和 divfree-binary-roundbody-*（换的是整数域 vdiv 轮体）对象不同、证明不同，本条的对象是浮点 0-ULP 向量除法，证明是 IEEE-754 单次正确舍入的位等价。",
  "related_anti_patterns": [
    "relaxed-division-mode",
    "pow-pspecific-fast-reduce-paths",
    "divfree-binary-roundbody-int32-scoped",
    "divfree-binary-roundbody-int64-falsified"
  ],
  "risks": [
    "位等价论证必须覆盖边界：除以 2^k 与乘以精确 2^-k 的逐位一致只在倒数无舍入时成立，故 host 门控必须排除 0/次正规/inf/NaN；若把次正规 rangeVal 误判为 pow2（指数位全 0 形态被放过），倒数不再精确且结果与精确除法逐位不同",
    "非 pow2 回退路径无套件覆盖：本 run 20 个 case 全部命中 Mul 路径，回退 Div 代码保持原样但未被任何 case 触达，属于如实记录的未验证面",
    "门控信息必须随 tiling 走而不是在 kernel 内重算：rangeVal 由 maxValF-minValF 得到（float 域），若把判定挪到 kernel 侧做浮点比较/对数运算，一是引入新的长微码序列，二是判定结果可能与 host 不一致",
    "icache/镜像代价：模板实例倍增使 .so 到 10.81MB，若某算子的热循环本身受取指带宽限制，收益会被膨胀的镜像吃掉；本 run icache_miss 稳态保持在 1.2-1.6% 未恶化",
    "收益归因必须落在 aiv_vec：若删掉 Div 后 aiv_vec 未下降，说明向量管时间不在那条微码序列上，本机制不成立（此时按 0 收益回滚）"
  ],
  "slug": "pow2-divisor-exact-reciprocal-mul",
  "summary": "max_histc champion 的 FusedRowScanVF 每 64 元素向量体里只有一条多槽精确算术指令——分箱链里 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div，而它几乎就是向量管的全部开销（删除后 main kernel aiv_vec 55-57us -> 6.4us，-88%）。全部 20 个 case 的 histc attrs 都是 min=-1/max_val=1 -> rangeVal=2.0，于是 host 用位运算判定 rangeVal 是否为精确 2 的幂（尾数位全 0、指数位非全 0/全 1，排除 0/次正规/inf/NaN）并下发精确倒数 rangeRecip=1/range；kernel 侧 FusedRowScanVF 增加模板参量 POW2_RECIP，pow2 路径用 Reg::Mul 替换 0-ULP Div，非 pow2 保留原 Div 作回退。IEEE-754 下除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，故在未启用 FTZ 且除数/倒数精确的语义下逐位一致（本 run 20/20 PASS、hist_exact 全 True，但输入/输出均在有限正常数域，未覆盖 subnormal 边界；`Reg::Mul` 在默认 `--cce-ftz=true` 下的 subnormal 行为未实测）。形式化 ABBA 3 对、72 项 case 级配对 geomean 13.885->8.0433us = 1.7263x；main kernel 三 dtype 71.115/69.771/71.31us -> 22.743/22.812/22.934us，final kernel +3.2~4.7%（~0.1us 布局效应）被完全覆盖。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS 一次通过，hist_exact 全 True（分箱计数逐位一致）",
      "逐位等价由 IEEE-754 论证支撑：除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，分箱边界与 torch.histc 判箱逐位不变；该结论目前只覆盖有限正常数域，subnormal 边界需补 `Reg::Mul` 的 FTZ 语义或硬件测试，未覆盖前不得宣称全边界逐位一致",
      "NaN 输入在 Div 前已被 valid 掩码 Select 为 minR，不进入除法；非 pow2 回退保留原 Div 代码（无套件覆盖，如实记录）",
      "改动一次应用、零修复轮（compile_result attempts=1、repair_rounds_used=0）"
    ],
    "performance": [
      "形式化 ABBA x3 blocks（A B B A / A B B A / A B B A = 6 base + 6 cand msprof runs，72 项 case 级配对测量，逐 run 波动 <0.2%），同 shape、provenance clean、平衡交替、相关性无歧义：geomean 13.885 -> 8.0433us = 1.7263x；baseline 侧与 BEST_MS 0.0138656 交叉一致（<0.15%）",
      "main kernel 三 dtype 的 per_case_ratio（候选/基线）0.3198/0.327/0.3216（bf16/fp16/fp32，即约 3.127/3.058/3.110x），71.115/69.771/71.31us -> 22.743/22.812/22.934us；final kernel 1.0399/1.0321/1.0469（+3.2~4.7%，约 0.1us 布局效应），被 main 侧收益完全覆盖",
      "候选 main kernel 流水：aiv_vec 6.4-6.5us（champion 55-57us，-88%），aiv_scalar 11.7-12.9us 升为新主导（54-57%），aiv_mte2 0.89us、aiv_mte3 1.69us，icache_miss_rate 0.012-0.016",
      "总 ratio_geomean 0.5793（= 1/1.7263；由 main 三 case 的 0.3198-0.327 与 final 三 case 的 1.0321-1.0469 共同构成）"
    ],
    "rollback_signals": [
      "任何 case 的分箱计数不再逐位一致（hist_exact 非全 True）",
      "host 门控把非 2 的幂（或 0/次正规/inf/NaN 边界）误判为 pow2，导致倒数有舍入",
      "Mul 的 FTZ 行为与 Div(PRECISION_0ULP_FTZ_FALSE) 不一致，subnormal 输入/输出被 flush 为 0",
      "在向量循环体内引入运行时分支而非编译期分派，或 .so/icache 膨胀吃掉收益",
      "收益不可归因：aiv_vec 未下降说明删掉的不是那条多槽微码序列，按 0 收益回滚"
    ]
  }
}
-->

# 性能优化策略：2 的幂除数精确倒数乘法：以 Reg::Mul 替换分箱链的 0-ULP Div

max_histc champion 的 FusedRowScanVF 每 64 元素向量体里只有一条多槽精确算术指令——分箱链里 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div，而它几乎就是向量管的全部开销（删除后 main kernel aiv_vec 55-57us -> 6.4us，-88%）。全部 20 个 case 的 histc attrs 都是 min=-1/max_val=1 -> rangeVal=2.0，于是 host 用位运算判定 rangeVal 是否为精确 2 的幂（尾数位全 0、指数位非全 0/全 1，排除 0/次正规/inf/NaN）并下发精确倒数 rangeRecip=1/range；kernel 侧 FusedRowScanVF 增加模板参量 POW2_RECIP，pow2 路径用 Reg::Mul 替换 0-ULP Div，非 pow2 保留原 Div 作回退。IEEE-754 下除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，故在未启用 FTZ 且除数/倒数精确的语义下逐位一致（本 run 20/20 PASS、hist_exact 全 True，但输入/输出均在有限正常数域，未覆盖 subnormal 边界；`Reg::Mul` 在默认 `--cce-ftz=true` 下的 subnormal 行为未实测）。形式化 ABBA 3 对、72 项 case 级配对 geomean 13.885->8.0433us = 1.7263x；main kernel 三 dtype 71.115/69.771/71.31us -> 22.743/22.812/22.934us，final kernel +3.2~4.7%（~0.1us 布局效应）被完全覆盖。

## 1. 原理

向量管的近全部时间可以挂在一条多槽微码指令上，而这条指令的语义往往可以被等价的廉价指令替换。本 run 的 max_histc champion 在 FusedRowScanVF 的每 64 元素向量循环体（fp32 约 26 条向量指令）里，唯一的多槽精确算术指令就是分箱链 tmp=(v-min)*bins/range 中 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div，其余每个槽位都是单条 compare/select/add/mul/cast；实测把它删掉后 main kernel 的 aiv_vec 由 55-57us 降到 6.4us（-88%），即这条 0-ULP 除法约吃掉 champion 向量管的 86%，远超探索时 k≈4-6 槽的保守估算。既然除数是运行期标量而所有 case 的 rangeVal 恰好是 2.0，就可以利用 IEEE-754 的一条精确事实：在 IEEE-754 语义下（未启用 FTZ），对任意有限/无穷/NaN/±0 输入，除以 2^k 与乘以精确的 2^-k 是同一实数的单次正确舍入，二者逐位相同；上溢/下溢/次正规边界也只在 Mul 不 flush subnormal 时成立。本 run 的实测域是有限正常数，不能把该边界结论外推到 subnormal 输入/输出；`Reg::Mul` 受 `--cce-ftz` 控制（默认 true），若目标编译选项会 flush subnormal，则含 subnormal 的 case 必须回退 Div 路径。于是把『运行期精确除法』换成『运行期精确倒数 × 一次乘法』，除数是否 2 的幂由 host 用位运算静态判定并下发：这是与 relaxed-division-mode 方向相反的取舍——后者把 0-ULP 除法换成硬件快速模式、以精度契约换吞吐，本机制不放松任何精度契约，反而把结果锁到与精确除法逐位一致；也与 pow-pspecific-fast-reduce-paths（换的是幂模拟里的 Ln/Exp 超越链）和 divfree-binary-roundbody-*（换的是整数域 vdiv 轮体）对象不同、证明不同，本条的对象是浮点 0-ULP 向量除法，证明是 IEEE-754 单次正确舍入的位等价。

实现机制：pow2-exact-reciprocal-mul：host 侧在 kernel/pybind11.cpp 用位运算门控 rangeVal（maxValF-minValF）是否为精确 2 的幂——尾数位全 0、且指数位非全 0/全 1（排除 0/次正规/inf/NaN）——命中时向 tiling 写 rangePow2=1 与精确倒数 rangeRecip=1.0f/rangeVal（pow2 的倒数无舍入），MaxHistcTiling 尾部追加 rangePow2(uint32)/rangeRecip(float) 两字段（前段布局不变）。kernel 侧 maxhistc_kernel.h 给 FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false）与 recipR 寄存器，用 if constexpr 在 Reg::Mul(tmp,tmp,recipR) 与原 Reg::Div 之间分派；分派点在 FusedPhaseB 每行一次（按 rangePow2_ 判定），向量循环体内没有运行时分支；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化。ComputeBinsVF（非融合回退路径）与 final kernel 未改动；一次应用、零修复轮。非 2 的幂 range 保持原 Div 路径作为回退门控。

## 2. 性能问题模式

- 优化目标：在精度契约不放松的前提下，去掉热向量体里 0-ULP 精确除法在 A5 向量管上的极长微码序列成本：当除数是运行期常量且被 host 静态判定为精确 2 的幂时，把向量循环体内的 Reg::Div 换成一次 Reg::Mul（乘精确倒数），非 pow2 保留原路径作回退。
- 适用数据流：热向量循环体内含浮点 0-ULP 精确除法、除数是运行期标量且可取到 2 的幂的算子；典型如直方图/分箱家族（本 run max_histc 的 FusedRowScanVF 分箱链 tmp=(v-min)*bins/range，bins=3、[1024,1024] dim=-1 fused=1，main+final 两个 kernel、三 dtype）
- Feature signature：`{"bottleneck": ["div-dominant", "high-precision-divide", "vec-instruction-issue-bound", "single-multislot-arith-per-rep"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "pow2-exact-reciprocal-mul", "reduce_mode": "fused-scan-bin-chain", "structure": ["host-bitwise-pow2-gate", "exact-reciprocal-shipped-in-tiling", "compile-time-template-dispatch", "runtime-original-div-fallback", "bitwise-identical-rounding"]}`

## 3. 正确性红线

- 位等价论证必须覆盖边界：除以 2^k 与乘以精确 2^-k 的逐位一致只在倒数无舍入且 Mul 不 flush subnormal 时成立，故 host 门控必须排除 0/次正规/inf/NaN；若把次正规 rangeVal 误判为 pow2（指数位全 0 形态被放过），倒数不再精确且结果与精确除法逐位不同。另须确认 `Reg::Mul` 在目标编译选项（默认 `--cce-ftz=true`）下的 subnormal 行为；不能保证保留 subnormal 时，含 subnormal 输入/输出的 case 必须回退 Div 路径。
- 非 pow2 回退路径无套件覆盖：本 run 20 个 case 全部命中 Mul 路径，回退 Div 代码保持原样但未被任何 case 触达，属于如实记录的未验证面
- 门控信息必须随 tiling 走而不是在 kernel 内重算：rangeVal 由 maxValF-minValF 得到（float 域），若把判定挪到 kernel 侧做浮点比较/对数运算，一是引入新的长微码序列，二是判定结果可能与 host 不一致
- icache/镜像代价：模板实例倍增使 .so 到 10.81MB，若某算子的热循环本身受取指带宽限制，收益会被膨胀的镜像吃掉；本 run icache_miss 稳态保持在 1.2-1.6% 未恶化
- 收益归因必须落在 aiv_vec：若删掉 Div 后 aiv_vec 未下降，说明向量管时间不在那条微码序列上，本机制不成立（此时按 0 收益回滚）

资源与硬件约束：

- host 门控必须是位运算判定精确 2 的幂并排除 0/次正规/inf/NaN（尾数位全 0、指数位非全 0/全 1）；只有 pow2 的倒数无舍入，才能把 rangeRecip=1.0f/rangeVal 当作精确值下发
- rangePow2(uint32)/rangeRecip(float) 作为 MaxHistcTiling 尾部追加字段，前段布局不变；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化
- 分派必须是编译期（if constexpr 在 Mul 与 Div 之间选择），不得在向量循环体内引入运行时分支；ComputeBinsVF（非融合回退路径）与 final kernel 未改动
- 模板实例倍增使 .so 达 10.81MB（FusedRowScanVF 模板实例 +0.26MB），必须确认 icache miss 稳态未恶化（实测 1.2-1.6%）

## 4. 泛化条件

- 策略作用域：op_class：scan

适用：

- 热向量体里存在唯一的多槽精确算术指令且它是向量管主导：champion FusedRowScanVF 的 64 元素向量循环体（fp32 约 26 条向量指令）中唯一多槽精确算术指令是 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div（分箱链 tmp=(v-min)*bins/range），实测删除后 main kernel aiv_vec 55-57us -> 6.4us（-88%），其开销约占 champion 向量管 86%，远超探索时 k≈4-6 槽的保守估算
- 除数是运行期标量、且测试/perf case 全部落在 2 的幂上：全部 20 个 case 的 histc attrs 均为 min=-1/max_val=1 -> rangeVal=2.0，bins=3，[1024,1024] dim=-1 -> fused=1，全部命中 Mul 路径
- 存在编译期分派点，使向量循环体内无运行时分支：FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false），分派点在 FusedPhaseB 每行一次（按 main kernel 成员 rangePow2_ 判定），main kernel 的 rangePow2_/rangeRecip_ 从 tiling 初始化
- 可保逐位一致（限于已测有限正常数域）：IEEE-754 下除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，分箱边界与 torch.histc 判箱逐位不变；NaN 输入在 Div 前已被 valid 掩码 Select 为 minR，不会进入除法。subnormal 边界需先确认 `Reg::Mul` 的 FTZ 语义；未确认前不得宣称全边界逐位一致

不适用：

- 除数不是 2 的幂时不适用：非 pow2 的 range 保持原 Div 路径作为回退门控（本 run 的回退路径无套件覆盖，如实记录）
- 允许有界数值误差而非要求逐位一致时不适用——那是 relaxed-division-mode 的域：把 0-ULP 除法切成硬件快速模式、以精度契约换吞吐，与本机制方向相反
- 热链上的 0-ULP 除法不是唯一/主导多槽指令时收益不可期：本机制的收益直接等于该指令在向量管上的占比
- 对象不是浮点 0-ULP 向量除法时不适用：pow-pspecific-fast-reduce-paths 换的是幂模拟的 Ln/Exp 超越链，divfree-binary-roundbody-int32-scoped 换的是整数 vdiv 轮体，机制、对象与证明均不同

## 5. 实施步骤

1. host 侧在 kernel/pybind11.cpp 加 rangeVal 位运算门控：尾数位全 0、指数位非全 0/全 1 判定为精确 2 的幂（排除 0/次正规/inf/NaN），命中时写 rangePow2=1 且 rangeRecip=1.0f/rangeVal（精确）
2. 在 MaxHistcTiling 尾部追加 rangePow2(uint32)/rangeRecip(float) 两字段，前段布局不变；main kernel 成员 rangePow2_/rangeRecip_ 从 tiling 初始化
3. 在 kernel/maxhistc_kernel.h 给 FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false）与 recipR 寄存器，用 if constexpr 在 Reg::Mul(tmp,tmp,recipR) 与原 Reg::Div 之间分派
4. 把分派点上提到 FusedPhaseB：按 rangePow2_ 每行分派一次，保证向量循环体内没有运行时分支；非 pow2 保持原 Div 路径作回退
5. 以 20/20 精度门（hist_exact 全 True）与形式化 ABBA 配对验收，并复核 .so 体积增幅（+0.26MB）未使 icache miss 稳态恶化（1.2-1.6%）

## 6. LLM 前置问题

- 目标实现是否满足：热向量体里存在唯一的多槽精确算术指令且它是向量管主导：champion FusedRowScanVF 的 64 元素向量循环体（fp32 约 26 条向量指令）中唯一多槽精确算术指令是 DivAlgo::PRECISION_0ULP_FTZ_FALSE 的 Reg::Div（分箱链 tmp=(v-min)*bins/range），实测删除后 main kernel aiv_vec 55-57us -> 6.4us（-88%），其开销约占 champion 向量管 86%，远超探索时 k≈4-6 槽的保守估算？
- 目标实现是否满足：除数是运行期标量、且测试/perf case 全部落在 2 的幂上：全部 20 个 case 的 histc attrs 均为 min=-1/max_val=1 -> rangeVal=2.0，bins=3，[1024,1024] dim=-1 -> fused=1，全部命中 Mul 路径？
- 目标实现是否满足：存在编译期分派点，使向量循环体内无运行时分支：FusedRowScanVF 增加模板参量 POW2_RECIP（默认 false），分派点在 FusedPhaseB 每行一次（按 main kernel 成员 rangePow2_ 判定），main kernel 的 rangePow2_/rangeRecip_ 从 tiling 初始化？
- 目标实现是否满足：可保逐位一致（限于已测有限正常数域）：IEEE-754 下除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，分箱边界与 torch.histc 判箱逐位不变；NaN 输入在 Div 前已被 valid 掩码 Select 为 minR，不会进入除法？若输入/输出可能落入 subnormal，`Reg::Mul` 在 `--cce-ftz=true` 下是否仍保留 subnormal，是否有硬件测试或编译选项依据？
- 是否命中排除条件：除数不是 2 的幂时不适用：非 pow2 的 range 保持原 Div 路径作为回退门控（本 run 的回退路径无套件覆盖，如实记录）？
- 是否命中排除条件：允许有界数值误差而非要求逐位一致时不适用——那是 relaxed-division-mode 的域：把 0-ULP 除法切成硬件快速模式、以精度契约换吞吐，与本机制方向相反？
- 是否命中排除条件：热链上的 0-ULP 除法不是唯一/主导多槽指令时收益不可期：本机制的收益直接等于该指令在向量管上的占比？
- 是否命中排除条件：对象不是浮点 0-ULP 向量除法时不适用：pow-pspecific-fast-reduce-paths 换的是幂模拟的 Ln/Exp 超越链，divfree-binary-roundbody-int32-scoped 换的是整数 vdiv 轮体，机制、对象与证明均不同？

## 7. 验收标准

正确性：

- 精度 20/20 PASS 一次通过，hist_exact 全 True（分箱计数逐位一致）
- 逐位等价由 IEEE-754 论证支撑：除以 2^k 与乘以精确 2^-k 是同一实数的单次正确舍入，分箱边界与 torch.histc 判箱逐位不变；该结论目前只覆盖有限正常数域，subnormal 边界需补 `Reg::Mul` 的 FTZ 语义或硬件测试，未覆盖前不得宣称全边界逐位一致
- NaN 输入在 Div 前已被 valid 掩码 Select 为 minR，不进入除法；非 pow2 回退保留原 Div 代码（无套件覆盖，如实记录）
- 改动一次应用、零修复轮（compile_result attempts=1、repair_rounds_used=0）

性能：

- 形式化 ABBA x3 blocks（A B B A / A B B A / A B B A = 6 base + 6 cand msprof runs，72 项 case 级配对测量，逐 run 波动 <0.2%），同 shape、provenance clean、平衡交替、相关性无歧义：geomean 13.885 -> 8.0433us = 1.7263x；baseline 侧与 BEST_MS 0.0138656 交叉一致（<0.15%）
- main kernel 三 dtype 的 per_case_ratio（候选/基线）0.3198/0.327/0.3216（bf16/fp16/fp32，即约 3.127/3.058/3.110x），71.115/69.771/71.31us -> 22.743/22.812/22.934us；final kernel 1.0399/1.0321/1.0469（+3.2~4.7%，约 0.1us 布局效应），被 main 侧收益完全覆盖
- 候选 main kernel 流水：aiv_vec 6.4-6.5us（champion 55-57us，-88%），aiv_scalar 11.7-12.9us 升为新主导（54-57%），aiv_mte2 0.89us、aiv_mte3 1.69us，icache_miss_rate 0.012-0.016
- 总 ratio_geomean 0.5793（= 1/1.7263；由 main 三 case 的 0.3198-0.327 与 final 三 case 的 1.0321-1.0469 共同构成）

回滚信号：

- 任何 case 的分箱计数不再逐位一致（hist_exact 非全 True）
- host 门控把非 2 的幂（或 0/次正规/inf/NaN 边界）误判为 pow2，导致倒数有舍入
- Mul 的 FTZ 行为与 Div(PRECISION_0ULP_FTZ_FALSE) 不一致，subnormal 输入/输出被 flush 为 0
- 在向量循环体内引入运行时分支而非编译期分派，或 .so/icache 膨胀吃掉收益
- 收益不可归因：aiv_vec 未下降说明删掉的不是那条多槽微码序列，按 0 收益回滚

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：relaxed-division-mode, pow-pspecific-fast-reduce-paths, divfree-binary-roundbody-int32-scoped, divfree-binary-roundbody-int64-falsified

- loop_20260915_101435（round=1, status=accepted, speedup=1.7263, precision=20/20 PASS（hist_exact 全 True，分箱计数逐位一致））

## 检索卡（短卡）

动作：把热向量体的 0-ULP 精确除法改为乘 host 位运算门控下发的精确 2 的幂倒数，按编译期模板参量在乘法与除法间分派
适用：热向量体唯一多槽精确算术指令即向量管主导（实测约占 86%）；除数为运行期标量且 case 全落 2 的幂
限制：host 门控须位运算判定且排除 0/次正规/inf/NaN；分派须编译期，循环体内无运行时分支；门控随 tiling 走不在 kernel 重算；Mul 的 FTZ 语义须确认，subnormal 未覆盖时回退 Div。
范围：扫描/直方图分箱类算子的热向量循环体
检索词：Reg::Div、Reg::Mul、POW2_RECIP、PRECISION_0ULP_FTZ_FALSE、if constexpr、aiv_vec
机会：热向量体约 86% 时间挂在唯一一条 0-ULP 精确除法的长微码序列上，其余槽位均为单条指令
代价：模板实例倍增使 .so 达 10.81MB，取指带宽受限时收益会被镜像膨胀吃回
