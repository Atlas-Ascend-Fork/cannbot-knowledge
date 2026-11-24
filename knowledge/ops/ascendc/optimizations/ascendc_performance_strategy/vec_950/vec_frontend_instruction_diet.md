---
type: Optimization
title: 向量前端指令节食：对齐分派 B 半 load + SiLU 直接除 + 每行倒数 hoist + amax 融合进生产 pass
description: 在 VEC-paced 逐 repeat 链里删除四类语义形式指令：对齐分派 B 半 load、SiLU 直接除、每行倒数 hoist、amax 融合进产出 pass。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/vec-frontend-instruction-diet.md
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
      "修改仅限 kernel VF 体：mask/tail 处理、dtype 分派、tiling 路由、同步结构、缓冲尺寸不变",
      "每行谓词/倒数 hoist 会小幅增加 scalar（每行常数量级），须显著小于 vec 削减收益（本 run 实测 aiv_scalar +0.2~0.45us/inv，远小于 vec 削减）",
      "多分量共享同一 kernel 文件：需文档化 per-component 回滚边界（正交性）"
    ],
    "excluded_conditions": [
      "奇 H（H*sizeof(DX)%32!=0）：B 半保持 unaligned 路径，仅其余分量适用（收益打折）",
      "非 VEC-bound shape（launch/scalar/MTE 带宽主导）：指令节食不转化为时延收益，仅作 no-regression 守护",
      "要求逐位一致的输出：除法形式/倒数 hoist 有 ULP 级差（本 run 实测整数输出在官方阈值内全过）",
      "低精度 amax/计算路径（如 fp16）：scale rtol 量级禁止"
    ],
    "required_conditions": [
      "受益 case 实测 VEC 为主要流水（高 vec_ratio），且指令削减量大于其它流水（MTE2/MTE3/scalar）的未重叠部分",
      "每条被删指令都是语义形式变更（对齐谓词分派、除法形式、per-row 不变量 hoist、生产/消费 pass 融合），不是编译器可能已 CSE 的源码冗余——立项前先核实发射流中真实存在并检查 dominant 指令稀释",
      "对齐谓词为 shape 常量（host 已知 H 与 dtype，kernel 由模板推导）且每行只算一次；奇 H 行基保持 unaligned B 路径并仍受益于其余分量",
      "per-row 常量 hoist 不触碰 scale 输出路径（s 计算/scale store 逐字保留），数值差落在容差内（整数输出 threshold>=1 吸收边界翻转）",
      "被融合 pass 与生产 pass 值恒等（同一寄存器、相同指令形式累加），融合后寄存器生命周期仍可编排"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-01",
  "evidence": [
    {
      "comparison_sha256": "e1f4c1ddb98f3954055e5879c687b0ea4c8cd7328817002c74419029e854da09",
      "decision_sha256": "07eecbbf8bb2ff992e25e56d9c78c0887fea50b0d83884773f0cca762b7812a7",
      "operator_class": "fused-composite",
      "performance_sha256": "819d851f46b1696f1d9cb3ea9d773d32ccbc436df36ef2002866b2eb81d593f4",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "71c2bf7ef5b331304173c56e748070e7eedec4ad9e5491c8cbd242c6dfb4fc99",
      "verify_sha256": "ac164257efea7ead9c427e9917dd4d6ff1229d37d6fcc889fa2a3ef03e58541a"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "vec-instruction-count"
    ],
    "dtypes": [
      "int32",
      "fp16",
      "bf16"
    ],
    "pattern": "vec-frontend-instruction-diet",
    "structure": [
      "regtensor-vf-chain",
      "alignment-dispatch",
      "per-row-invariant-hoist",
      "producer-pass-fusion"
    ]
  },
  "generality": "op_class",
  "id": "DSQ-R3-VEC-FRONTEND-DIET",
  "implementation_steps": [
    "用 op_summary 确认受益 case 的 vec_ratio，并做源码级每 repeat v-insn 记账估算各分量削减比例",
    "对齐分派：加 B_ALIGNED 模板 bool（对称于既有 unaligned 模式），谓词在 Ptr 包装层每行计算一次",
    "除法形式：SiLU 直接 3 操作数 Div；quantize 每行 rcp=Div(one,s) + repeat 内 Mul",
    "pass 融合：把 amax 的 Abs+Max MERGING/Reduce/StoreFirst 移入生产 VF 尾部，删除 reload pass 与调用点，maxVal 指针穿参",
    "全量 correctness（RegImpl 跨 route 共享，范围 all_cases）+ 增量 compare；用 aiv_vec_time 下降且 aiv_scalar ~持平的管线签名归因，区分测量漂移"
  ],
  "intent": "削减 VEC 前端每 repeat 发射数与串行依赖链长度（load 路径、除法形式、不变量作用域、pass 结构四类语义形式），把 vec-paced case 的 wall 往下压，同时不引入 MTE/scalar 结构变化。",
  "mechanism": "(1) ComputeDequantSwiGLURegImpl 增加模板 bool B_ALIGNED（对称于既有 A_UNALIGNED 模式），谓词在 Ptr 包装层每行计算一次：bAligned = (h*sizeof(DX))%32==0（int32 H%8==0、16-bit H%16==0；HAS_WS 蕴含 DX==int32，同一谓词覆盖 fp32 ws 偏移 4H）；为真时 x B 半走 LoadXToFloatAligned、ws B 半用 LoadAlign<float> 替代 LoadUnAlignPre+LoadUnAlign 对；仅在对齐 row-base 分支派发，奇 H 与未对齐行基保持 unaligned 路径。(2) SiLUInPlace 以 3 操作数 Div(v,v,denom,mask) 结尾，删除 Duplicate(oneReg)+Div(sig)+Mul 链。(3) ComputeQuantizeRegImpl 在 s 计算（Div maxVal/127 + clamp）与 scale StoreFirst 均不动的前提下，每行一次 rcp=Div(one,s)，repeat 内 Div(q,src,s) 换 Mul(q,src,rcp)。(4) vf_0 尾部融合 amax：循环前 maxAccReg 初始化为 -FLT_MAX，每 repeat 在 pre-store 寄存器上 Abs(ZEROING)+Max(MERGING) 累加，函数末 Reduce<MAX>+StoreAlign DIST_FIRST_ELEMENT_B32；整段 reload pass（LoadAlign+Abs+Max per repeat）与其两个调用点删除，maxVal 以 __ubuf__ 指针穿参。拷贝描述符、队列、缓冲尺寸、blockDim、tiling、host 全部不动。",
  "name": "向量前端指令节食：对齐分派 B 半 load + SiLU 直接除 + 每行倒数 hoist + amax 融合进生产 pass",
  "op": "dequant_swiglu_quant",
  "operator_class": "fused-composite",
  "operator_scope": "行式 elementwise 融合的 RegTensor VF 计算链（逐 64-lane repeat 发射 v-insn），批/逐行两种 pipeline 路径共享同一 RegImpl；VEC 为测得的主要流水（高 vec_ratio），热链中存在可按语义形式（而非编译器可 CSE 的源码冗余）删除的指令",
  "principle": "VEC-paced 时 wall 近似正比于 v-insn 发射数，但前提是被删指令是语义形式变更——load 路径切换、除法形式改写、不变量作用域提升、生产/消费 pass 融合——编译器无法用 CSE 复原；这与删一条可能已被 CSE 的源码冗余的负向边界严格区分。数值分量（直接除 vs 乘倒数）只差 ULP 级、须落在精度容差内；pass 融合（amax）在 pre-store 寄存器上用相同指令形式累加，值恒等。转化须以增量 compare + 管线归因验收（aiv_vec_time 下降且 aiv_scalar 持平），不由基线相对值判定。",
  "related_anti_patterns": [],
  "risks": [
    "opcount→wall 转化是可证伪假设：预注册证伪信号（高 vec_ratio case 设备削减 <5% 即证伪）并按其裁决",
    "数值分量 ULP 差可能翻转整数舍入边界：必须全量 verify 且容差语义核对（diff==threshold 内判过）",
    "删除整段 VF pass（amax 融合）是最大 diff 块：寄存器生命周期/编译行为需 verify 兜底，分量可独立回滚",
    "sub-10us case 处于 n=1 微核噪声地板：control 按 same-state scatter 判定"
  ],
  "slug": "vec-frontend-instruction-diet",
  "summary": "在 VEC-paced 的逐 repeat 计算链里删除四类语义形式的指令：(1) B 半（x[H:2H] 与 ws B 半）load 按对齐谓词分派——(H*sizeof(DX))%32==0 时走 LoadAlign（16-bit 走 DIST_UNPACK_B16），跳过 LoadUnAlignPre+LoadUnAlign 对与 Interleave/Duplicate 解包链；(2) SiLU 用同一 3 操作数 Div 直接算 v/(1+exp(-v))，删 Duplicate(one)+倒数 Div+Mul；(3) per-row 常量 1/s 每行 hoist 一次 Div，repeat 内 Div 换 Mul；(4) amax（Abs+Max MERGING 累加 + Reduce + StoreFirst）融合进产出 pass 的 store 前寄存器上，删除整段 reload pass。四分量正交、可独立回滚。",
  "verification": {
    "correctness": [
      "rounds/003 verify 20/20 通过（all_cases，kernel ca8039dc891bbf5e）；数值分量 ULP 差被 int8 threshold 1.0 吸收，scale 输出路径未触碰（rtol 隔离）"
    ],
    "performance": [
      "incremental total_speedup 1.1333x（target 集 1.124x，control 集 1.1607x，regressed 0，14 case 改善）；case 4 1.297x、case 3 1.208x、case 12 1.160x、case 2 1.192x",
      "管线级归因：aiv_vec_time 下降 15.9%~26.0%（case 1/2/3/4/12）、10.5%~12.8%（case 18/19），aiv_scalar ~持平（个别 +0.2~0.45us/inv 来自每行谓词/倒数 hoist，策略预期内）",
      "cumulative vs baseline 2.3951x；边界：case 9 0.9741x 为 sub-10us n=1 target，处于同一二进制重测的自身 scatter（+0.258us/inv）与 ~0.5us/inv 抖动地板内"
    ],
    "rollback_signals": [
      "任一 correctness 失败（数值分量为嫌疑）；高 vec_ratio case 设备削减 <5%（opcount→wall 假设证伪）",
      "target 聚合增量 <1.03x；任一 control <0.95x；意外 device error（谓词或寄存器生命周期 bug，非机制边界）"
    ]
  }
}
-->

# 性能优化策略：向量前端指令节食：对齐分派 B 半 load + SiLU 直接除 + 每行倒数 hoist + amax 融合进生产 pass

单一优化点：在 VEC-paced 的逐 repeat 计算链里删除四类语义形式的指令：(1) B 半（x[H:2H] 与 ws B 半）load 按对齐谓词分派——(H*sizeof(DX))%32==0 时走 LoadAlign（16-bit 走 DIST_UNPACK_B16），跳过 LoadUnAlignPre+LoadUnAlign 对与 Interleave/Duplicate 解包链；(2) SiLU 用同一 3 操作数 Div 直接算 v/(1+exp(-v))，删 Duplicate(one)+倒数 Div+Mul；(3) per-row 常量 1/s 每行 hoist 一次 Div，repeat 内 Div 换 Mul；(4) amax（Abs+Max MERGING 累加 + Reduce + StoreFirst）融合进产出 pass 的 store 前寄存器上，删除整段 reload pass。四分量正交、可独立回滚。

## 1. 原理

VEC-paced 时 wall 近似正比于 v-insn 发射数，但前提是被删指令是语义形式变更——load 路径切换、除法形式改写、不变量作用域提升、生产/消费 pass 融合——编译器无法用 CSE 复原；这与删一条可能已被 CSE 的源码冗余的负向边界严格区分。数值分量（直接除 vs 乘倒数）只差 ULP 级、须落在精度容差内；pass 融合（amax）在 pre-store 寄存器上用相同指令形式累加，值恒等。转化须以增量 compare + 管线归因验收（aiv_vec_time 下降且 aiv_scalar 持平），不由基线相对值判定。

实现机制：(1) ComputeDequantSwiGLURegImpl 增加模板 bool B_ALIGNED（对称于既有 A_UNALIGNED 模式），谓词在 Ptr 包装层每行计算一次：bAligned = (h*sizeof(DX))%32==0（int32 H%8==0、16-bit H%16==0；HAS_WS 蕴含 DX==int32，同一谓词覆盖 fp32 ws 偏移 4H）；为真时 x B 半走 LoadXToFloatAligned、ws B 半用 LoadAlign<float> 替代 LoadUnAlignPre+LoadUnAlign 对；仅在对齐 row-base 分支派发，奇 H 与未对齐行基保持 unaligned 路径。(2) SiLUInPlace 以 3 操作数 Div(v,v,denom,mask) 结尾，删除 Duplicate(oneReg)+Div(sig)+Mul 链。(3) ComputeQuantizeRegImpl 在 s 计算（Div maxVal/127 + clamp）与 scale StoreFirst 均不动的前提下，每行一次 rcp=Div(one,s)，repeat 内 Div(q,src,s) 换 Mul(q,src,rcp)。(4) vf_0 尾部融合 amax：循环前 maxAccReg 初始化为 -FLT_MAX，每 repeat 在 pre-store 寄存器上 Abs(ZEROING)+Max(MERGING) 累加，函数末 Reduce<MAX>+StoreAlign DIST_FIRST_ELEMENT_B32；整段 reload pass（LoadAlign+Abs+Max per repeat）与其两个调用点删除，maxVal 以 __ubuf__ 指针穿参。拷贝描述符、队列、缓冲尺寸、blockDim、tiling、host 全部不动。

## 2. 性能问题模式

- 优化目标：削减 VEC 前端每 repeat 发射数与串行依赖链长度（load 路径、除法形式、不变量作用域、pass 结构四类语义形式），把 vec-paced case 的 wall 往下压，同时不引入 MTE/scalar 结构变化。
- 适用数据流：行式 elementwise 融合的 RegTensor VF 计算链（逐 64-lane repeat 发射 v-insn），批/逐行两种 pipeline 路径共享同一 RegImpl；VEC 为测得的主要流水（高 vec_ratio），热链中存在可按语义形式（而非编译器可 CSE 的源码冗余）删除的指令
- Feature signature：`{"bottleneck": ["vec-bound", "vec-instruction-count"], "dtypes": ["int32", "fp16", "bf16"], "pattern": "vec-frontend-instruction-diet", "structure": ["regtensor-vf-chain", "alignment-dispatch", "per-row-invariant-hoist", "producer-pass-fusion"]}`

## 3. 正确性红线

- opcount→wall 转化是可证伪假设：预注册证伪信号（高 vec_ratio case 设备削减 <5% 即证伪）并按其裁决
- 数值分量 ULP 差可能翻转整数舍入边界：必须全量 verify 且容差语义核对（diff==threshold 内判过）
- 删除整段 VF pass（amax 融合）是最大 diff 块：寄存器生命周期/编译行为需 verify 兜底，分量可独立回滚
- sub-10us case 处于 n=1 微核噪声地板：control 按 same-state scatter 判定

资源与硬件约束：

- 修改仅限 kernel VF 体：mask/tail 处理、dtype 分派、tiling 路由、同步结构、缓冲尺寸不变
- 每行谓词/倒数 hoist 会小幅增加 scalar（每行常数量级），须显著小于 vec 削减收益（本 run 实测 aiv_scalar +0.2~0.45us/inv，远小于 vec 削减）
- 多分量共享同一 kernel 文件：需文档化 per-component 回滚边界（正交性）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 受益 case 实测 VEC 为主要流水（高 vec_ratio），且指令削减量大于其它流水（MTE2/MTE3/scalar）的未重叠部分
- 每条被删指令都是语义形式变更（对齐谓词分派、除法形式、per-row 不变量 hoist、生产/消费 pass 融合），不是编译器可能已 CSE 的源码冗余——立项前先核实发射流中真实存在并检查 dominant 指令稀释
- 对齐谓词为 shape 常量（host 已知 H 与 dtype，kernel 由模板推导）且每行只算一次；奇 H 行基保持 unaligned B 路径并仍受益于其余分量
- per-row 常量 hoist 不触碰 scale 输出路径（s 计算/scale store 逐字保留），数值差落在容差内（整数输出 threshold>=1 吸收边界翻转）
- 被融合 pass 与生产 pass 值恒等（同一寄存器、相同指令形式累加），融合后寄存器生命周期仍可编排

不适用：

- 奇 H（H*sizeof(DX)%32!=0）：B 半保持 unaligned 路径，仅其余分量适用（收益打折）
- 非 VEC-bound shape（launch/scalar/MTE 带宽主导）：指令节食不转化为时延收益，仅作 no-regression 守护
- 要求逐位一致的输出：除法形式/倒数 hoist 有 ULP 级差（本 run 实测整数输出在官方阈值内全过）
- 低精度 amax/计算路径（如 fp16）：scale rtol 量级禁止

## 5. 实施步骤

1. 用 op_summary 确认受益 case 的 vec_ratio，并做源码级每 repeat v-insn 记账估算各分量削减比例
2. 对齐分派：加 B_ALIGNED 模板 bool（对称于既有 unaligned 模式），谓词在 Ptr 包装层每行计算一次
3. 除法形式：SiLU 直接 3 操作数 Div；quantize 每行 rcp=Div(one,s) + repeat 内 Mul
4. pass 融合：把 amax 的 Abs+Max MERGING/Reduce/StoreFirst 移入生产 VF 尾部，删除 reload pass 与调用点，maxVal 指针穿参
5. 全量 correctness（RegImpl 跨 route 共享，范围 all_cases）+ 增量 compare；用 aiv_vec_time 下降且 aiv_scalar ~持平的管线签名归因，区分测量漂移

## 6. LLM 前置问题

- 目标实现是否满足：受益 case 实测 VEC 为主要流水（高 vec_ratio），且指令削减量大于其它流水（MTE2/MTE3/scalar）的未重叠部分？
- 目标实现是否满足：每条被删指令都是语义形式变更（对齐谓词分派、除法形式、per-row 不变量 hoist、生产/消费 pass 融合），不是编译器可能已 CSE 的源码冗余——立项前先核实发射流中真实存在并检查 dominant 指令稀释？
- 目标实现是否满足：对齐谓词为 shape 常量（host 已知 H 与 dtype，kernel 由模板推导）且每行只算一次；奇 H 行基保持 unaligned B 路径并仍受益于其余分量？
- 是否命中排除条件：奇 H（H*sizeof(DX)%32!=0）：B 半保持 unaligned 路径，仅其余分量适用（收益打折）？

## 7. 验收标准

正确性：

- rounds/003 verify 20/20 通过（all_cases，kernel ca8039dc891bbf5e）；数值分量 ULP 差被 int8 threshold 1.0 吸收，scale 输出路径未触碰（rtol 隔离）

性能：

- incremental total_speedup 1.1333x（target 集 1.124x，control 集 1.1607x，regressed 0，14 case 改善）；case 4 1.297x、case 3 1.208x、case 12 1.160x、case 2 1.192x
- 管线级归因：aiv_vec_time 下降 15.9%~26.0%（case 1/2/3/4/12）、10.5%~12.8%（case 18/19），aiv_scalar ~持平（个别 +0.2~0.45us/inv 来自每行谓词/倒数 hoist，策略预期内）
- cumulative vs baseline 2.3951x；边界：case 9 0.9741x 为 sub-10us n=1 target，处于同一二进制重测的自身 scatter（+0.258us/inv）与 ~0.5us/inv 抖动地板内

回滚信号：

- 任一 correctness 失败（数值分量为嫌疑）；高 vec_ratio case 设备削减 <5%（opcount→wall 假设证伪）
- target 聚合增量 <1.03x；任一 control <0.95x；意外 device error（谓词或寄存器生命周期 bug，非机制边界）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- dequant_swiglu_quant-20260831_113139-0cf99e（round=3, status=accepted）

## 检索卡（短卡）

动作：在 VEC-paced 逐 repeat 链里删除四类语义形式指令：对齐分派 B 半 load、SiLU 直接除、每行倒数 hoist、amax 融合进产出 pass。
适用：受益 case 实测 VEC 为主要流水，且被删指令均为语义形式变更而非可被 CSE 的源码冗余。
限制：修改仅限 kernel VF 体，mask/tail、dtype 分派、tiling 路由、同步结构与缓冲尺寸不变。
范围：行式 elementwise 融合的 RegTensor VF 计算链
检索词：B_ALIGNED、LoadAlign、LoadUnAlignPre、DIST_UNPACK_B16、rcp hoist、reload pass
机会：VEC 前端每 repeat 发射数与串行依赖链长度主导 wall
代价：高 vec_ratio case 设备削减 <5% 即证伪假设；sub-10us 处于微核噪声地板
