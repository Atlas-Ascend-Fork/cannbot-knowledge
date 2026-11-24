---
type: Optimization
title: 量化尾 cast 链节食：3 级 cast 折叠为 fp32→half(CAST_ODD)→int8 并删除可证死钳位
description: 把量化尾 3 级 cast 链折叠为 fp32→half(CAST_ODD)→int8，并删除可证死的 Mins(127)/Maxs(-128) 钳位。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/quant-tail-cast-chain-diet.md
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
      "NO_SAT 为默认实现（零新编译面）；SAT 变体的编译 probe 在 build.py 之外不可复现（直接 make 对字节一致的 NO_SAT 源也报 harness 级错误），如需 SAT 必须经 scratch round 的 build 通路验证",
      "指令削减按家族 v-insn 分数折算设备时延（本例 vf_2 占整 repeat 流 9%~15%，随 dtype/对齐家族变化）；vec 占比低的 case 收益低于噪声",
      "对抗 probe 须包含域外超大值网格的 old/new 对照：head 侧预存在分歧（新旧相同）需排除出 golden 判定"
    ],
    "excluded_conditions": [
      "要求输出与原链逐字节一致的场景（机制上允许 ±1 翻转；零翻转是 CAST_ODD 的结构性结果，不能假设普遍成立）",
      "scale 派生/输出路径被同时触碰：scale rtol 数值面必须与本机制隔离，数值面只允许落在 y 尾",
      "round-to-nearest 的低精度中继 hop（会真实翻转半整数 tie）",
      "per-row 标量侧 s/rcp 节食（每行 1 条而非每 repeat 1 条，收益近零且触碰 scale 数值路径）"
    ],
    "required_conditions": [
      "目标 cast 链每一跳在工具链 cast trait 表中存在表项：立项前先读表（本例 arch35 tensor_api cast 子表无 int16→int8 表项，直接排除 int16 保留形式）",
      "2 级形式优先取同仓已通过官方精度的 sibling 算子的 trait 常量（零新编译面）",
      "钳位删除必须有元素级可证的不变式（|q| 界由 scale 派生闭环：amax 融合到精确存储值 + 正确舍入 Div/Mul）+ 设备对抗数值 probe 机检（半整数邻近、amax 比率极值、clamp 分支、全零/巨值）",
      "新 Cast 对的编译可行性先经正式 build 通路 probe（standalone make 不复现 build.py 的 opc 预处理环境，不能作编译判据）",
      "量化尾循环跨 route 无条件共享：correctness 范围必须全量 all_cases；整数 checker 语义确认（diff==threshold 内判过，threshold>=1）使 ±1 双舍入翻转可吸收"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-01",
  "evidence": [
    {
      "comparison_sha256": "69bae7628a720087c6133d781f9187d190a12123ba98917fb1dd95fbdab07b30",
      "decision_sha256": "f0deef01dc2439059b27a494c973dcfaa9025709fc057b0e0d436fe38142af4e",
      "operator_class": "fused-composite",
      "performance_sha256": "793ba135742fdd8eca4b61f0af494985d3e13658b072a6ad3635dad371b32de8",
      "round": 6,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "afb7adb4313e6128aab6715f2a8ee591923cd82778e0d9581d39f1204d892220",
      "verify_sha256": "8a3cfde127a893d95d06e7df8f2d64800a6f72046468ab5db3b922a58885b3ff"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "cast-chain-length",
      "serial-dependency-chain"
    ],
    "dtypes": [
      "fp32",
      "fp16",
      "int8"
    ],
    "pattern": "quant-tail-cast-chain-diet",
    "structure": [
      "quantize-tail",
      "cast-trait-map",
      "dead-clamp-elision",
      "round-to-odd-double-rounding"
    ]
  },
  "generality": "op_class",
  "id": "DSQ-R6-QUANT-TAIL-CAST-DIET",
  "implementation_steps": [
    "读工具链 cast trait 表确定可行链形（read-only 证伪不可编译的备选，记录表项证据）",
    "从已验证 sibling 复制 trait 常量；在量化尾删除可证死钳位并折叠 Cast 链，删除失效的中间 dtype RegTensor",
    "设备 probe：编译（经正式 build 通路）+ 对抗数值（old vs new vs fp64 golden，断言 max|Δy|<=1 且 scale bit-identical）",
    "全量 all_cases verify + 增量 compare；用 aiv_vec_time 下降且 scalar/mte2 ~持平的结构签名归因（区别于 scalar 膨胀类与 tiling 改动类机制）"
  ],
  "intent": "缩短量化尾每 repeat 的向量指令数与串行依赖链（q→clamp→clamp→cast→cast→cast 变为 q→cast→cast），在 vec-paced case 上转化为 wall 下降。",
  "mechanism": "kernel 单文件单函数（CustomRegImpl）：trait 常量块删除 castTraitF32ToI16/castTraitI16ToF16，新增 castTraitF32ToF16 = {RegLayout::ZERO, SatMode::NO_SAT, MaskMergeMode::ZEROING, RoundMode::CAST_ODD}（自 sibling dynamic_quant 的已验证常量逐字段复制），保留既有 castTraitF16ToI8；repeat 循环删除 Mins(127)/Maxs(-128) 钳位，3 条 Cast 折叠为 Cast<half,float,castTraitF32ToF16> + Cast<int8_t,half,castTraitF16ToI8>，删除 i16Reg RegTensor 声明；s 计算、rcp、scale store、PACK4 store、vf_0 头部、host tiling、workspace、队列、blockDim 全部不动。可选加固：末跳 Cast 用 SatMode::SAT（sat(RINT(x)) ≡ RINT(clamp(x)) 于 [-128,127]，对全部 x 与 golden 钳位语义恒等），仅当 probe 经正式 build 通路编译验证后采用，否则默认 NO_SAT。",
  "name": "量化尾 cast 链节食：3 级 cast 折叠为 fp32→half(CAST_ODD)→int8 并删除可证死钳位",
  "op": "dequant_swiglu_quant",
  "operator_class": "fused-composite",
  "operator_scope": "fp32 中间值量化到 int8 的每 repeat 尾部循环（per-row/per-tensor scale 量化），scale 派生与 scale 输出路径独立于该循环；量化尾被全部 route 无条件执行",
  "principle": "两个正交事实支撑正确性：(1) 钳位可证死——scale 派生（Div(maxVal,127) 及其 clamp 分支）给出 |q| <= 127*(1+~5*2^-24) < 127.5，RINT 后仍在 [-127,127]，int8 转换不越界；(2) CAST_ODD（round-to-odd）fp16 中继使 RINT(CAST_ODD(q)) ≡ RINT(q) 对 |q|<128 结构性成立——每个 int8 tie 点 k+0.5 都可被 fp16 精确表示且 mantissa 为偶数，双舍入不翻转（round-to-nearest 的 fp16 中继则会真实翻转半整数 tie，不可用）。官方整数 checker 按 diff>threshold 判失败且 int8 threshold=1.0，即使发生 ±1 翻转也可吸收；实测零翻转，强于界。链形可行性由 cast trait 表的表项存在性决定，须先读表证伪不可编译的备选。",
  "related_anti_patterns": [],
  "risks": [
    "NO_SAT 下若 |q| 界被破坏会 int8 回绕（灾难性而非边缘失败）：不变式必须闭环且对抗机检",
    "双舍入分析边界敏感：必须设备对抗网格机检，不能只靠纸面证明",
    "est-score 模型对 C<H 放大区 case 低估、对未测量 case 有盲区：官方分以 final eval 为准"
  ],
  "slug": "quant-tail-cast-chain-diet",
  "summary": "把量化尾每 repeat 的 8 条 v-insn 减到 5 条：删除 fp32 域 Mins(127)/Maxs(-128) 钳位（由 scale 派生不变式可证死），并把 Cast 链 fp32→int16→half→int8 折叠为 fp32→half→int8；链形状由工具链 cast trait 表决定（arch35 tensor_api cast 子表无 int16→int8 表项、float→half 与 half→int8 存在），2 级形式的 trait 常量取自同仓已通过官方精度的 sibling 算子。",
  "verification": {
    "correctness": [
      "rounds/006 verify 20/20 通过（all_cases，kernel 042ca0986203aa8a）",
      "P2 数值 probe：9 个对抗网格 / 6,029,376 元素 max|y_new − y_old| = 0（零翻转）、scale bit-identical——强于可证 <=1 界；域外网格的 head 侧旧有分歧（old/new 相同）被排除出 golden 判定"
    ],
    "performance": [
      "incremental total_speedup 1.0714x（target 集 1.0818x，control 集 1.0304x，10 improved / 0 regressed）；cumulative vs baseline 2.5636x",
      "预注册证伪信号全过：case 3 削减 +3.21us >= +1.0 且 case 4 +2.97us >= +1.2（primary），case 12 +3.91us >= +1.0（secondary）",
      "结构签名：aiv_vec_time 下降 11.5%~13.2%（case 3/12/19）且 aiv_scalar/mte2 ~持平；边界：control case 9 0.9688x 为 sub-10us n=1 噪声（绝对 +0.237us/inv 在该 case 自身同态 scatter 内，0.95 硬门通过）"
    ],
    "rollback_signals": [
      "probe 编译失败或对抗网格 max|Δy|>1：不得上轮次（回退到只删钳位的弱变体）",
      "最纯 vec-paced case 削减不足预注册阈值（V 引擎非指令数 paced，假设证伪）",
      "任一 validation case <0.97x（5 指令流不可能 plausible 变慢；大幅下降指示编译伪影/寄存器溢出）或任一 correctness/device error"
    ]
  }
}
-->

# 性能优化策略：量化尾 cast 链节食：3 级 cast 折叠为 fp32→half(CAST_ODD)→int8 并删除可证死钳位

单一优化点：把量化尾每 repeat 的 8 条 v-insn 减到 5 条：删除 fp32 域 Mins(127)/Maxs(-128) 钳位（由 scale 派生不变式可证死），并把 Cast 链 fp32→int16→half→int8 折叠为 fp32→half→int8；链形状由工具链 cast trait 表决定（arch35 tensor_api cast 子表无 int16→int8 表项、float→half 与 half→int8 存在），2 级形式的 trait 常量取自同仓已通过官方精度的 sibling 算子。

## 1. 原理

两个正交事实支撑正确性：(1) 钳位可证死——scale 派生（Div(maxVal,127) 及其 clamp 分支）给出 |q| <= 127*(1+~5*2^-24) < 127.5，RINT 后仍在 [-127,127]，int8 转换不越界；(2) CAST_ODD（round-to-odd）fp16 中继使 RINT(CAST_ODD(q)) ≡ RINT(q) 对 |q|<128 结构性成立——每个 int8 tie 点 k+0.5 都可被 fp16 精确表示且 mantissa 为偶数，双舍入不翻转（round-to-nearest 的 fp16 中继则会真实翻转半整数 tie，不可用）。官方整数 checker 按 diff>threshold 判失败且 int8 threshold=1.0，即使发生 ±1 翻转也可吸收；实测零翻转，强于界。链形可行性由 cast trait 表的表项存在性决定，须先读表证伪不可编译的备选。

实现机制：kernel 单文件单函数（CustomRegImpl）：trait 常量块删除 castTraitF32ToI16/castTraitI16ToF16，新增 castTraitF32ToF16 = {RegLayout::ZERO, SatMode::NO_SAT, MaskMergeMode::ZEROING, RoundMode::CAST_ODD}（自 sibling dynamic_quant 的已验证常量逐字段复制），保留既有 castTraitF16ToI8；repeat 循环删除 Mins(127)/Maxs(-128) 钳位，3 条 Cast 折叠为 Cast<half,float,castTraitF32ToF16> + Cast<int8_t,half,castTraitF16ToI8>，删除 i16Reg RegTensor 声明；s 计算、rcp、scale store、PACK4 store、vf_0 头部、host tiling、workspace、队列、blockDim 全部不动。可选加固：末跳 Cast 用 SatMode::SAT（sat(RINT(x)) ≡ RINT(clamp(x)) 于 [-128,127]，对全部 x 与 golden 钳位语义恒等），仅当 probe 经正式 build 通路编译验证后采用，否则默认 NO_SAT。

## 2. 性能问题模式

- 优化目标：缩短量化尾每 repeat 的向量指令数与串行依赖链（q→clamp→clamp→cast→cast→cast 变为 q→cast→cast），在 vec-paced case 上转化为 wall 下降。
- 适用数据流：fp32 中间值量化到 int8 的每 repeat 尾部循环（per-row/per-tensor scale 量化），scale 派生与 scale 输出路径独立于该循环；量化尾被全部 route 无条件执行
- Feature signature：`{"bottleneck": ["vec-bound", "cast-chain-length", "serial-dependency-chain"], "dtypes": ["fp32", "fp16", "int8"], "pattern": "quant-tail-cast-chain-diet", "structure": ["quantize-tail", "cast-trait-map", "dead-clamp-elision", "round-to-odd-double-rounding"]}`

## 3. 正确性红线

- NO_SAT 下若 |q| 界被破坏会 int8 回绕（灾难性而非边缘失败）：不变式必须闭环且对抗机检
- 双舍入分析边界敏感：必须设备对抗网格机检，不能只靠纸面证明
- est-score 模型对 C<H 放大区 case 低估、对未测量 case 有盲区：官方分以 final eval 为准

资源与硬件约束：

- NO_SAT 为默认实现（零新编译面）；SAT 变体的编译 probe 在 build.py 之外不可复现（直接 make 对字节一致的 NO_SAT 源也报 harness 级错误），如需 SAT 必须经 scratch round 的 build 通路验证
- 指令削减按家族 v-insn 分数折算设备时延（本例 vf_2 占整 repeat 流 9%~15%，随 dtype/对齐家族变化）；vec 占比低的 case 收益低于噪声
- 对抗 probe 须包含域外超大值网格的 old/new 对照：head 侧预存在分歧（新旧相同）需排除出 golden 判定

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 目标 cast 链每一跳在工具链 cast trait 表中存在表项：立项前先读表（本例 arch35 tensor_api cast 子表无 int16→int8 表项，直接排除 int16 保留形式）
- 2 级形式优先取同仓已通过官方精度的 sibling 算子的 trait 常量（零新编译面）
- 钳位删除必须有元素级可证的不变式（|q| 界由 scale 派生闭环：amax 融合到精确存储值 + 正确舍入 Div/Mul）+ 设备对抗数值 probe 机检（半整数邻近、amax 比率极值、clamp 分支、全零/巨值）
- 新 Cast 对的编译可行性先经正式 build 通路 probe（standalone make 不复现 build.py 的 opc 预处理环境，不能作编译判据）
- 量化尾循环跨 route 无条件共享：correctness 范围必须全量 all_cases；整数 checker 语义确认（diff==threshold 内判过，threshold>=1）使 ±1 双舍入翻转可吸收

不适用：

- 要求输出与原链逐字节一致的场景（机制上允许 ±1 翻转；零翻转是 CAST_ODD 的结构性结果，不能假设普遍成立）
- scale 派生/输出路径被同时触碰：scale rtol 数值面必须与本机制隔离，数值面只允许落在 y 尾
- round-to-nearest 的低精度中继 hop（会真实翻转半整数 tie）
- per-row 标量侧 s/rcp 节食（每行 1 条而非每 repeat 1 条，收益近零且触碰 scale 数值路径）

## 5. 实施步骤

1. 读工具链 cast trait 表确定可行链形（read-only 证伪不可编译的备选，记录表项证据）
2. 从已验证 sibling 复制 trait 常量；在量化尾删除可证死钳位并折叠 Cast 链，删除失效的中间 dtype RegTensor
3. 设备 probe：编译（经正式 build 通路）+ 对抗数值（old vs new vs fp64 golden，断言 max|Δy|<=1 且 scale bit-identical）
4. 全量 all_cases verify + 增量 compare；用 aiv_vec_time 下降且 scalar/mte2 ~持平的结构签名归因（区别于 scalar 膨胀类与 tiling 改动类机制）

## 6. LLM 前置问题

- 目标实现是否满足：目标 cast 链每一跳在工具链 cast trait 表中存在表项：立项前先读表（本例 arch35 tensor_api cast 子表无 int16→int8 表项，直接排除 int16 保留形式）？
- 目标实现是否满足：2 级形式优先取同仓已通过官方精度的 sibling 算子的 trait 常量（零新编译面）？
- 目标实现是否满足：钳位删除必须有元素级可证的不变式（|q| 界由 scale 派生闭环：amax 融合到精确存储值 + 正确舍入 Div/Mul）+ 设备对抗数值 probe 机检（半整数邻近、amax 比率极值、clamp 分支、全零/巨值）？
- 是否命中排除条件：要求输出与原链逐字节一致的场景（机制上允许 ±1 翻转；零翻转是 CAST_ODD 的结构性结果，不能假设普遍成立）？

## 7. 验收标准

正确性：

- rounds/006 verify 20/20 通过（all_cases，kernel 042ca0986203aa8a）
- P2 数值 probe：9 个对抗网格 / 6,029,376 元素 max|y_new − y_old| = 0（零翻转）、scale bit-identical——强于可证 <=1 界；域外网格的 head 侧旧有分歧（old/new 相同）被排除出 golden 判定

性能：

- incremental total_speedup 1.0714x（target 集 1.0818x，control 集 1.0304x，10 improved / 0 regressed）；cumulative vs baseline 2.5636x
- 预注册证伪信号全过：case 3 削减 +3.21us >= +1.0 且 case 4 +2.97us >= +1.2（primary），case 12 +3.91us >= +1.0（secondary）
- 结构签名：aiv_vec_time 下降 11.5%~13.2%（case 3/12/19）且 aiv_scalar/mte2 ~持平；边界：control case 9 0.9688x 为 sub-10us n=1 噪声（绝对 +0.237us/inv 在该 case 自身同态 scatter 内，0.95 硬门通过）

回滚信号：

- probe 编译失败或对抗网格 max|Δy|>1：不得上轮次（回退到只删钳位的弱变体）
- 最纯 vec-paced case 削减不足预注册阈值（V 引擎非指令数 paced，假设证伪）
- 任一 validation case <0.97x（5 指令流不可能 plausible 变慢；大幅下降指示编译伪影/寄存器溢出）或任一 correctness/device error

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- dequant_swiglu_quant-20260831_113139-0cf99e（round=6, status=accepted）

## 检索卡（短卡）

动作：把量化尾 3 级 cast 链折叠为 fp32→half(CAST_ODD)→int8，并删除可证死的 Mins(127)/Maxs(-128) 钳位。
适用：cast 链每一跳在工具链 cast trait 表中存在表项、2 级形式可取同仓已验证 sibling 的 trait 常量。
限制：NO_SAT 下 |q| 界破坏会 int8 回绕，不变式须闭环并机检；round-to-nearest 中继会翻转半整数 tie。
范围：fp32 量化到 int8 的每 repeat 尾部循环。
检索词：castTraitF32ToF16、CAST_ODD、NO_SAT、ZEROING、Mins/Maxs、PACK4
机会：量化尾每 repeat 8 条 v-insn 中 q→clamp→clamp→cast→cast→cast 串行链占用发射槽。
代价：机制允许 ±1 双舍入翻转；vec 占比低时收益低于噪声。
