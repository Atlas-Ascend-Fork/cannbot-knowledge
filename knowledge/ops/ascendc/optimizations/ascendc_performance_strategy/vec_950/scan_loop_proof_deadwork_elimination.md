---
type: Optimization
title: 扫描循环证死删除：不变量守卫段末外提 + 退化段恒等塌缩
description: 把逐块逐步重复的 NaN/Inf 守卫外提到段末消费点一次，并把退化段恒零的 carry 链整段删掉。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scan-loop-proof-deadwork-elimination.md
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
      "守卫外提的等价性必须建立在『前缀单调性 + 精度契约排除非有限元素』两条论证同时成立之上，二者缺一不可（本 run：hi 非有限对后续步保持非有限；tests/testcases.py 的 _finite_pairs / atol_rtol_pass 把 NaN/Inf 元素整体排除在比较之外）",
      "守卫必须只保留在被消费点一次（本 run FinalizeBlockCore 的 ZeroBadLo(loReg, hiReg, mask) 置于 out = hi + lo 之前），不得顺手改动 hi 通道；标量 carry 守卫（Compute / ComputeBlockOffset）原样不动",
      "退化段路线必须始终以 numSeg==1 为门：扫描第 1 步全量写 lo（active lane 写 two-sum 误差 e、masked lane 写 0）以取消 per-row loA 清零时，必须保留 N==1 的守卫",
      "两条路线都要求删除对象是死代码或精确恒等式：任何需要新数值语义或新『VF store 后标量读回』依赖的改动越界（本 run direction_001 的段内两级化即因工具链标量读限制失败）"
    ],
    "excluded_conditions": [
      "守卫结果不满足前缀单调性时不能外提（例如 hi 非有限后还能被后续步写回有限值，或 lo 的 NaN 可能先于 hi 非有限出现）",
      "精度契约把 NaN/Inf 纳入比较时不适用：此时输出必须按位等价，而不是『非有限 lane 的形态变化不可见』",
      "路径不存在恒零 carry 不变量时不适用：本 run 唯一的例外 c12（blockDim=1，走段路径）跨段 carry 是活路径，逐字未动",
      "把向量不变量构造外提（tap-loop-invariant-vector-hoisting 的外提对象）或用链上已有中间量替换整遍归约（max-identity-substitution，无单调性论证、无退化段门控）都不属于本机制：本机制的两个分量都必须先证明『该 region 不做有用工作』，然后才删除"
    ],
    "required_conditions": [
      "扫描是补偿（two-sum）Hillis-Steele，且防御指令逐块逐步重复：本 run 每块每步 ~22 条向量指令中 ZeroBadLo 占 ~7（1 Duplicate + 3 Compare + 2 Or + 1 Select），4096 元素段要跑 12 步 x 64 块 = 768 个块步，而只有每段最终被消费的 (hi,lo) 对需要守卫",
      "精度契约把非有限元素排除在比较之外（本 run tests/testcases.py 的 _finite_pairs / atol_rtol_pass），使 +Inf（hi + 清零的 lo）到 NaN（hi + NaN lo）一类差异在非有限 lane 上不可见",
      "存在可证的退化不变量：本 run numSeg==1 的行批路径里每行 carry 从 (0,0) 起步、以 (0,0) 调用 RunCarryAddFinalize、行末 two-sum 更新出的 carry 被直接丢弃——整条 carry 链是死代码（20 个 case 中 19 个走该路径）",
      "向量管是该算子的实测瓶颈：本 run cumulativetrapezoid__v2 的 aiv_vec_ratio 在全部 100 个匹配 launch 上 0.66-0.96；cumulativetrapezoid 的重 case c13 aiv_vec_ratio=0.946（aiv_vec 1518.6us / aiv_scalar 859.4us）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "cumulativetrapezoid__v2",
      "operator_class": "scan-reduce",
      "precision": "20/20 PASS（0 次修复）；5 对配对中全部 20 case 均改善、逐 case ratio 0.8695-0.9729，零回归",
      "run_id": "<run-id>",
      "speedup": 1.1187,
      "status": "accepted"
    },
    {
      "operator": "cumulativetrapezoid",
      "operator_class": "scan-reduce",
      "precision": "20/20 PASS 首次通过（0 次修复）；与冻结基线 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素为 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False）",
      "run_id": "<run-id>",
      "speedup": 1.0605,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "compensated-scan-vec-instruction-share",
      "per-step-invariant-guard-re-execution",
      "degenerate-segment-dead-carry-chain"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "scan-loop-proof-deadwork-elimination",
    "reduce_mode": "hillis-steele-prefix-scan",
    "structure": [
      "loop-invariant-guard-hoist",
      "prefix-monotonicity-argument",
      "degenerate-segment-identity-collapse",
      "dead-scalar-carrier-removal",
      "bitwise-identical-output"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-PROOF-DEADWORK-ELIMINATION",
  "implementation_steps": [
    "守卫外提（分量 a）：删除 ScanPairBlockCore 每步的 ZeroBadLo 调用与 CarryAddPairBlockCore 的每段守卫，改在 FinalizeBlockCore 里 out = hi + lo 之前插入一次 ZeroBadLo(loReg, hiReg, mask)；本 run 只改这一个 kernel 文件，标量 carry 守卫保持不变",
    "退化段（分量 b）：新增 ScanPairStep1BlockCore / ScanPairStep1PartialVF / ScanPairStep1FullVF——扫描第 1 步不读 lo 源、全量写 dst lo（active lane 写 two-sum 误差 e、masked lane 写 0，保留 ZeroBadLo），RunScan 对 step==1 专用分派",
    "新增 FinalizeNoCarryBlockCore / FinalizeNoCarryVF / RunFinalizeNoCarry（load hi、load lo、add、store）；numSeg==1 的 fp32/fp16 档删除 per-row carry 机件（GetValue×2 + 标量 two-sum + 非有限分支）与 loA 清零（保留 N==1 守卫）",
    "bf16 档在删除 carry 机件后，把 RunCarryAddFinalizeHi + outStg 中转替换为直接 Cast(outTile, hiResT[ubPad], CAST_RINT)",
    "段路径 Compute() 与 RunCarryAddFinalize / RunCarryAddFinalizeHi（跨段 carry 的活路径）逐字保留；以 bitcmp 双口径（IEEE 相等 + raw-bit）与 6 对平衡交替配对验收"
  ],
  "intent": "不减少扫描的算术强度，而是先证明扫描循环里某一段区域对最终被消费的值不做任何有用工作，再把它整段删掉：(a) 补偿扫描每步都为每个 64-lane 块跑一次 NaN/Inf 防御（ZeroBadLo，1 Duplicate + 3 Compare + 2 Or + 1 Select，占每块每步 ~22 条向量指令中的 ~7），但守卫只需对最终被消费的 (hi,lo) 对成立；(b) numSeg==1 的行批路径上每行的跨段 carry 链从 (0,0) 起步、行末被丢弃，整条链与环绕它的补偿 finalize、outStg 中转、loA 清零都是死代码。",
  "mechanism": "两条证死删除分量。(a) 守卫外提（cumulativetrapezoid__v2）：ZeroBadLo 原本在扫描每一 Hillis-Steele 步、每个 64-lane 块执行（~7/~22 条向量指令），4096 元素段要跑 12 步 x 64 块 = 768 个块步，而只有段末被 finalize 消费的 (hi,lo) 对需要守卫。外提的合法性来自前缀单调性：hi lane 一旦非有限，它在该 lane 的后续前缀里一直非有限；lo 只能经由一个其 hi 已在同一步非有限的 loSh lane 变成 NaN（add mask 同时覆盖两者），因此 NaN 的 lo 总与最终非有限的 hi 同时出现，段末一次守卫即可覆盖。改动为删除 ScanPairBlockCore 每步守卫与 CarryAddPairBlockCore 每段守卫，在 FinalizeBlockCore 的 out = hi + lo 之前插入一次 ZeroBadLo(loReg, hiReg, mask)。(b) 退化段死工作消除（cumulativetrapezoid）：numSeg==1 时每行 carry 从 (0,0) 起步、以 (0,0) 调用 RunCarryAddFinalize、行末 two-sum 更新出的 carry 被直接丢弃，整条 carry 链是死代码；carry==0 时补偿 finalize 的 two-sum 恒等于 0（s=hi+0 逐位等于 hi、e=0），且扫描每步存 hi 前已对该步 sReg 做过 ZeroBadLo（hi 非有限 ⇒ 同步 lo==0），故 out=hi+lo 与现 finalize 逐位一致。于是 fp32/fp16 档新增 FinalizeNoCarry（load hi、load lo、add、store，~4 向量操作/块 vs 补偿版 ~20 含 two-sum + ZeroBadLo），bf16 档的 RunCarryAddFinalizeHi(carry=0) 退化为 hi 的纯拷贝后 CAST_RINT，改为直接从 resHi CAST_RINT，连带删掉 outStg 中转；同时删除每行死的 segHi/segLo GetValue 读取（×2）与标量 two-sum carry 更新，并把扫描第 1 步改为全量写 lo（active lane 写 two-sum 误差 e、masked lane 写 0，保留 ZeroBadLo），从而取消每行的 loA 清零 pass（N==1 时保留守卫）。全部被删计算为死代码或精确恒等式，输出与 champion 数值恒等。",
  "name": "扫描循环证死删除：不变量守卫段末外提 + 退化段恒等塌缩",
  "operator_class": "scan-reduce",
  "operator_scope": "补偿（two-sum）Hillis-Steele 前缀扫描类算子，且精度契约把非有限元素排除在比较之外；本 run 覆盖两个算子：cumulativetrapezoid__v2（20 个 case，基线 geomean 101.076us，分量 a 守卫外提）与 cumulativetrapezoid（20 个 case 中 19 个走 numSeg==1 行批路径，基线 geomean 199.128us，分量 b 退化段死工作消除）",
  "principle": "扫描循环里的指令并不都值得优化，有些只是不需要执行。两个可证明的『不需要』：(a) 防御性守卫的作用域被高估了——ZeroBadLo 每步都跑，但它保护的是最终被消费的 (hi,lo) 对，而补偿扫描的前缀结构使守卫结果成为 loop-invariant：hi lane 一旦非有限就对该 lane 的剩余前缀一直非有限，且 NaN 的 lo 只能随 hi 同时非有限出现（add mask 覆盖两者），所以整段只需在 finalize 前清理一次；再叠加精度契约把 NaN/Inf 元素完全排除在比较之外，非有限 lane 上 +Inf 到 NaN 的形态变化对任何判据都不可见。(b) 退化路径的不变量被忽略了——numSeg==1 时跨段 carry 链从 (0,0) 起步又回到 (0,0)、行末丢弃，carry==0 使补偿 finalize 的 two-sum 恒等于 0，退化成一个恒等式 out = hi + lo，而 bf16 档更是退化成 hi 的纯拷贝后 CAST_RINT。两条论证都不改数值语义：一条用单调性把守卫搬出循环，一条用退化不变量把整段计算删掉。对照而言，tap-loop-invariant-vector-hoisting 外提的是向量不变量构造（不是语义守卫），max-identity-substitution 是用链上已有中间量替换整遍归约（既没有单调性论证，也没有退化段门控）。",
  "related_anti_patterns": [
    "tap-loop-invariant-vector-hoisting",
    "max-identity-substitution"
  ],
  "risks": [
    "守卫外提的正确性完全依赖『前缀单调性 + 精度契约排除非有限元素』两条论证：若测试契约改为把 NaN/Inf 纳入比较（或新增 finite-only 之外的判据），外提立即失效；本 run 的证据正是 tests/testcases.py 的 _finite_pairs / atol_rtol_pass 把 NaN/Inf 元素整体排除",
    "退化段删除的必要条件是 numSeg==1 这一不变量：本 run 20 个 case 中 19 个走行批路径、唯一例外 c12（blockDim=1 段路径）保持不变；一旦拓扑变化使某行走多段（carry 链不再是死的），删除动作就会静默改变结果",
    "外提后的守卫必须落在真正被消费的位置（本 run 是 FinalizeBlockCore 里 out = hi + lo 之前），且 CarryAddPairBlockCore 的段内守卫一并删除；漏留一处或位置错位都会让非有限 lane 以不同形式泄出",
    "『删除恒等式』路线的收益兑现依赖该 region 在向量管上确有份额：本 run 守卫占每块每步 ~22 条中的 ~7（预期扫描向量指令 -32%），实际 +11.87%；退化段路线预期 vec -9.6%（N=66 fp32 每行 ~364 向量操作中 finalize 2 块 x ~20 + loA 清零 3），实际 fp32 档 +10.6%、fp16 +7.5%、bf16 仅 +0.3%——bf16 档的 finalize-hi 本就只有 3 op/块，收益小于模型预测",
    "bitwise 对照必须双口径（IEEE 相等 + raw-bit）才读得对：本 run 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素是 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False）"
  ],
  "slug": "scan-loop-proof-deadwork-elimination",
  "summary": "对补偿 Hillis-Steele 扫描先证明某段区域不做有用工作、再整段删除，两个分量各自在算子上兑现：(a) 守卫外提——ZeroBadLo（~7/~22 条向量指令/块/步，4096 元素段要跑 768 个块步）依前缀单调性只需在段末 finalize 前执行一次，cumulativetrapezoid__v2 kernel geomean 101.076 -> 90.348us = 1.1187x（5 对 ABBA / 10 次测量，20 case 全改善、逐 case ratio 0.8695-0.9729，精度 20/20）。(b) 退化段死工作消除——numSeg==1 时 carry 链恒零，补偿 finalize 退化为 out = hi + lo、bf16 档直接从扫描 hi 缓冲 CAST_RINT 省掉 finalize pass 与 outStg 中转，并删掉每行死的 segHi/segLo 标量读取与 two-sum carry 更新、扫描第 1 步全量写 lo 取消每行 loA 清零；cumulativetrapezoid geomean 199.128 -> 187.7663us = 1.0605x（6 对，ratio 1.0599-1.0610，spread <0.11%；fp32 +10.6%、fp16 +7.5%、bf16 +0.3%），输出与冻结基线数值恒等（18/20 逐位一致）。",
  "verification": {
    "correctness": [
      "守卫外提：20/20 PASS（0 次修复），5 对配对中全部 20 case 均改善、逐 case ratio 0.8695-0.9729，零回归；标量 carry 守卫（Compute / ComputeBlockOffset）未改，且只改了 kernel/cumulativetrapezoid_kernel.h 一个文件",
      "退化段：20/20 PASS 首次通过（0 次修复）；与冻结基线 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素为 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False）",
      "退化段的两条代码事实：carry==0 时 two-sum 恒等于 0（s=hi+0 逐位等于 hi、e=0），且扫描每步存 hi 前已对该步 sReg 做过 ZeroBadLo（hi 非有限 ⇒ 同步 lo==0），故 out=hi+lo 与现 finalize 逐位一致；bf16 档 RunCarryAddFinalizeHi(carry=0) 退化为 hi 的纯拷贝后再 CAST_RINT，可改为直接从 resHi CAST",
      "段路径 Compute() 与 RunCarryAddFinalize / RunCarryAddFinalizeHi（c12 跨段 carry 的活路径）逐字未动"
    ],
    "performance": [
      "守卫外提：formal 5 对 ABBA / 10 次独立 msprof（顺序 B,A / A,B / B,A / A,B / B,A；base 独立构建 ext sha 507c58c374104500、cand 7fed8b22e0a26107），kernel geomean 101.076 -> 90.348us（speedup 1.1187，improvement 11.87%）；base 区间 [101.056,101.094]、cand 区间 [90.322,90.381] 完全不重叠，逐 case ratio 0.8695-0.9729",
      "退化段：formal 12 次 / 6 对（顺序 A,B,B,A,A,B,B,A,B,A,A,B；A=冻结基线独立构建 sha c2ce3e4a、B=候选 sha 459048fe），geomean 199.128 -> 187.7663us（speedup 1.0605，improvement 5.70%，逐对 ratio 1.0599-1.0610，spread <0.11%）",
      "退化段按 dtype 均值：bf16 281.6154 -> 280.6900us（+0.3%）、fp16 85.8168 -> 79.8598us（+7.5%）、fp32 326.7142 -> 295.3234us（+10.6%，c13 1606->1424us）",
      "退化段独立筛选口径复核：全量测试入口 geomean 197.7114 -> 186.2828（-5.78%），19 个 numSeg==1 case 全部下降（c13 -11.35%、c20 -7.66%、c5 -6.82%、c17 -7.89%），c12 -0.02% 持平"
    ],
    "rollback_signals": [
      "非有限 lane 的输出形态变化被精度判据看到（说明精度契约或前缀单调性论证不成立）",
      "任一 case 的逐位/逐值对照不再与冻结基线一致（退化段路线：±0 符号位以外的位差）",
      "numSeg 不再恒为 1 而行批路径仍走无 carry finalize（carry 链已变成活路径）",
      "删除后 vec 忙时不降或 duration 回退：说明被删的不是 pacing 工作，例如 bf16 档 finalize-hi 本就只有 3 op/块，收益接近于零"
    ]
  }
}
-->

# 性能优化策略：扫描循环证死删除：不变量守卫段末外提 + 退化段恒等塌缩

对补偿 Hillis-Steele 扫描先证明某段区域不做有用工作、再整段删除，两个分量各自在算子上兑现：(a) 守卫外提——ZeroBadLo（~7/~22 条向量指令/块/步，4096 元素段要跑 768 个块步）依前缀单调性只需在段末 finalize 前执行一次，cumulativetrapezoid__v2 kernel geomean 101.076 -> 90.348us = 1.1187x（5 对 ABBA / 10 次测量，20 case 全改善、逐 case ratio 0.8695-0.9729，精度 20/20）。(b) 退化段死工作消除——numSeg==1 时 carry 链恒零，补偿 finalize 退化为 out = hi + lo、bf16 档直接从扫描 hi 缓冲 CAST_RINT 省掉 finalize pass 与 outStg 中转，并删掉每行死的 segHi/segLo 标量读取与 two-sum carry 更新、扫描第 1 步全量写 lo 取消每行 loA 清零；cumulativetrapezoid geomean 199.128 -> 187.7663us = 1.0605x（6 对，ratio 1.0599-1.0610，spread <0.11%；fp32 +10.6%、fp16 +7.5%、bf16 +0.3%），输出与冻结基线数值恒等（18/20 逐位一致）。

## 1. 原理

扫描循环里的指令并不都值得优化，有些只是不需要执行。两个可证明的『不需要』：(a) 防御性守卫的作用域被高估了——ZeroBadLo 每步都跑，但它保护的是最终被消费的 (hi,lo) 对，而补偿扫描的前缀结构使守卫结果成为 loop-invariant：hi lane 一旦非有限就对该 lane 的剩余前缀一直非有限，且 NaN 的 lo 只能随 hi 同时非有限出现（add mask 覆盖两者），所以整段只需在 finalize 前清理一次；再叠加精度契约把 NaN/Inf 元素完全排除在比较之外，非有限 lane 上 +Inf 到 NaN 的形态变化对任何判据都不可见。(b) 退化路径的不变量被忽略了——numSeg==1 时跨段 carry 链从 (0,0) 起步又回到 (0,0)、行末丢弃，carry==0 使补偿 finalize 的 two-sum 恒等于 0，退化成一个恒等式 out = hi + lo，而 bf16 档更是退化成 hi 的纯拷贝后 CAST_RINT。两条论证都不改数值语义：一条用单调性把守卫搬出循环，一条用退化不变量把整段计算删掉。对照而言，tap-loop-invariant-vector-hoisting 外提的是向量不变量构造（不是语义守卫），max-identity-substitution 是用链上已有中间量替换整遍归约（既没有单调性论证，也没有退化段门控）。

实现机制：两条证死删除分量。(a) 守卫外提（cumulativetrapezoid__v2）：ZeroBadLo 原本在扫描每一 Hillis-Steele 步、每个 64-lane 块执行（~7/~22 条向量指令），4096 元素段要跑 12 步 x 64 块 = 768 个块步，而只有段末被 finalize 消费的 (hi,lo) 对需要守卫。外提的合法性来自前缀单调性：hi lane 一旦非有限，它在该 lane 的后续前缀里一直非有限；lo 只能经由一个其 hi 已在同一步非有限的 loSh lane 变成 NaN（add mask 同时覆盖两者），因此 NaN 的 lo 总与最终非有限的 hi 同时出现，段末一次守卫即可覆盖。改动为删除 ScanPairBlockCore 每步守卫与 CarryAddPairBlockCore 每段守卫，在 FinalizeBlockCore 的 out = hi + lo 之前插入一次 ZeroBadLo(loReg, hiReg, mask)。(b) 退化段死工作消除（cumulativetrapezoid）：numSeg==1 时每行 carry 从 (0,0) 起步、以 (0,0) 调用 RunCarryAddFinalize、行末 two-sum 更新出的 carry 被直接丢弃，整条 carry 链是死代码；carry==0 时补偿 finalize 的 two-sum 恒等于 0（s=hi+0 逐位等于 hi、e=0），且扫描每步存 hi 前已对该步 sReg 做过 ZeroBadLo（hi 非有限 ⇒ 同步 lo==0），故 out=hi+lo 与现 finalize 逐位一致。于是 fp32/fp16 档新增 FinalizeNoCarry（load hi、load lo、add、store，~4 向量操作/块 vs 补偿版 ~20 含 two-sum + ZeroBadLo），bf16 档的 RunCarryAddFinalizeHi(carry=0) 退化为 hi 的纯拷贝后 CAST_RINT，改为直接从 resHi CAST_RINT，连带删掉 outStg 中转；同时删除每行死的 segHi/segLo GetValue 读取（×2）与标量 two-sum carry 更新，并把扫描第 1 步改为全量写 lo（active lane 写 two-sum 误差 e、masked lane 写 0，保留 ZeroBadLo），从而取消每行的 loA 清零 pass（N==1 时保留守卫）。全部被删计算为死代码或精确恒等式，输出与 champion 数值恒等。

## 2. 性能问题模式

- 优化目标：不减少扫描的算术强度，而是先证明扫描循环里某一段区域对最终被消费的值不做任何有用工作，再把它整段删掉：(a) 补偿扫描每步都为每个 64-lane 块跑一次 NaN/Inf 防御（ZeroBadLo，1 Duplicate + 3 Compare + 2 Or + 1 Select，占每块每步 ~22 条向量指令中的 ~7），但守卫只需对最终被消费的 (hi,lo) 对成立；(b) numSeg==1 的行批路径上每行的跨段 carry 链从 (0,0) 起步、行末被丢弃，整条链与环绕它的补偿 finalize、outStg 中转、loA 清零都是死代码。
- 适用数据流：补偿（two-sum）Hillis-Steele 前缀扫描类算子，且精度契约把非有限元素排除在比较之外；本 run 覆盖两个算子：cumulativetrapezoid__v2（20 个 case，基线 geomean 101.076us，分量 a 守卫外提）与 cumulativetrapezoid（20 个 case 中 19 个走 numSeg==1 行批路径，基线 geomean 199.128us，分量 b 退化段死工作消除）
- Feature signature：`{"bottleneck": ["compensated-scan-vec-instruction-share", "per-step-invariant-guard-re-execution", "degenerate-segment-dead-carry-chain"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "scan-loop-proof-deadwork-elimination", "reduce_mode": "hillis-steele-prefix-scan", "structure": ["loop-invariant-guard-hoist", "prefix-monotonicity-argument", "degenerate-segment-identity-collapse", "dead-scalar-carrier-removal", "bitwise-identical-output"]}`

## 3. 正确性红线

- 守卫外提的正确性完全依赖『前缀单调性 + 精度契约排除非有限元素』两条论证：若测试契约改为把 NaN/Inf 纳入比较（或新增 finite-only 之外的判据），外提立即失效；本 run 的证据正是 tests/testcases.py 的 _finite_pairs / atol_rtol_pass 把 NaN/Inf 元素整体排除
- 退化段删除的必要条件是 numSeg==1 这一不变量：本 run 20 个 case 中 19 个走行批路径、唯一例外 c12（blockDim=1 段路径）保持不变；一旦拓扑变化使某行走多段（carry 链不再是死的），删除动作就会静默改变结果
- 外提后的守卫必须落在真正被消费的位置（本 run 是 FinalizeBlockCore 里 out = hi + lo 之前），且 CarryAddPairBlockCore 的段内守卫一并删除；漏留一处或位置错位都会让非有限 lane 以不同形式泄出
- 『删除恒等式』路线的收益兑现依赖该 region 在向量管上确有份额：本 run 守卫占每块每步 ~22 条中的 ~7（预期扫描向量指令 -32%），实际 +11.87%；退化段路线预期 vec -9.6%（N=66 fp32 每行 ~364 向量操作中 finalize 2 块 x ~20 + loA 清零 3），实际 fp32 档 +10.6%、fp16 +7.5%、bf16 仅 +0.3%——bf16 档的 finalize-hi 本就只有 3 op/块，收益小于模型预测
- bitwise 对照必须双口径（IEEE 相等 + raw-bit）才读得对：本 run 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素是 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False）

资源与硬件约束：

- 守卫外提的等价性必须建立在『前缀单调性 + 精度契约排除非有限元素』两条论证同时成立之上，二者缺一不可（本 run：hi 非有限对后续步保持非有限；tests/testcases.py 的 _finite_pairs / atol_rtol_pass 把 NaN/Inf 元素整体排除在比较之外）
- 守卫必须只保留在被消费点一次（本 run FinalizeBlockCore 的 ZeroBadLo(loReg, hiReg, mask) 置于 out = hi + lo 之前），不得顺手改动 hi 通道；标量 carry 守卫（Compute / ComputeBlockOffset）原样不动
- 退化段路线必须始终以 numSeg==1 为门：扫描第 1 步全量写 lo（active lane 写 two-sum 误差 e、masked lane 写 0）以取消 per-row loA 清零时，必须保留 N==1 的守卫
- 两条路线都要求删除对象是死代码或精确恒等式：任何需要新数值语义或新『VF store 后标量读回』依赖的改动越界（本 run direction_001 的段内两级化即因工具链标量读限制失败）

## 4. 泛化条件

- 策略作用域：op_class：scan-reduce

适用：

- 扫描是补偿（two-sum）Hillis-Steele，且防御指令逐块逐步重复：本 run 每块每步 ~22 条向量指令中 ZeroBadLo 占 ~7（1 Duplicate + 3 Compare + 2 Or + 1 Select），4096 元素段要跑 12 步 x 64 块 = 768 个块步，而只有每段最终被消费的 (hi,lo) 对需要守卫
- 精度契约把非有限元素排除在比较之外（本 run tests/testcases.py 的 _finite_pairs / atol_rtol_pass），使 +Inf（hi + 清零的 lo）到 NaN（hi + NaN lo）一类差异在非有限 lane 上不可见
- 存在可证的退化不变量：本 run numSeg==1 的行批路径里每行 carry 从 (0,0) 起步、以 (0,0) 调用 RunCarryAddFinalize、行末 two-sum 更新出的 carry 被直接丢弃——整条 carry 链是死代码（20 个 case 中 19 个走该路径）
- 向量管是该算子的实测瓶颈：本 run cumulativetrapezoid__v2 的 aiv_vec_ratio 在全部 100 个匹配 launch 上 0.66-0.96；cumulativetrapezoid 的重 case c13 aiv_vec_ratio=0.946（aiv_vec 1518.6us / aiv_scalar 859.4us）

不适用：

- 守卫结果不满足前缀单调性时不能外提（例如 hi 非有限后还能被后续步写回有限值，或 lo 的 NaN 可能先于 hi 非有限出现）
- 精度契约把 NaN/Inf 纳入比较时不适用：此时输出必须按位等价，而不是『非有限 lane 的形态变化不可见』
- 路径不存在恒零 carry 不变量时不适用：本 run 唯一的例外 c12（blockDim=1，走段路径）跨段 carry 是活路径，逐字未动
- 把向量不变量构造外提（tap-loop-invariant-vector-hoisting 的外提对象）或用链上已有中间量替换整遍归约（max-identity-substitution，无单调性论证、无退化段门控）都不属于本机制：本机制的两个分量都必须先证明『该 region 不做有用工作』，然后才删除

## 5. 实施步骤

1. 守卫外提（分量 a）：删除 ScanPairBlockCore 每步的 ZeroBadLo 调用与 CarryAddPairBlockCore 的每段守卫，改在 FinalizeBlockCore 里 out = hi + lo 之前插入一次 ZeroBadLo(loReg, hiReg, mask)；本 run 只改这一个 kernel 文件，标量 carry 守卫保持不变
2. 退化段（分量 b）：新增 ScanPairStep1BlockCore / ScanPairStep1PartialVF / ScanPairStep1FullVF——扫描第 1 步不读 lo 源、全量写 dst lo（active lane 写 two-sum 误差 e、masked lane 写 0，保留 ZeroBadLo），RunScan 对 step==1 专用分派
3. 新增 FinalizeNoCarryBlockCore / FinalizeNoCarryVF / RunFinalizeNoCarry（load hi、load lo、add、store）；numSeg==1 的 fp32/fp16 档删除 per-row carry 机件（GetValue×2 + 标量 two-sum + 非有限分支）与 loA 清零（保留 N==1 守卫）
4. bf16 档在删除 carry 机件后，把 RunCarryAddFinalizeHi + outStg 中转替换为直接 Cast(outTile, hiResT[ubPad], CAST_RINT)
5. 段路径 Compute() 与 RunCarryAddFinalize / RunCarryAddFinalizeHi（跨段 carry 的活路径）逐字保留；以 bitcmp 双口径（IEEE 相等 + raw-bit）与 6 对平衡交替配对验收

## 6. LLM 前置问题

- 目标实现是否满足：扫描是补偿（two-sum）Hillis-Steele，且防御指令逐块逐步重复（本 run 每块每步 ~22 条向量指令中 ZeroBadLo 占 ~7，4096 元素段要跑 768 个块步）？
- 目标实现是否满足：精度契约把非有限元素排除在比较之外（本 run _finite_pairs / atol_rtol_pass）？
- 目标实现是否满足：存在可证的退化不变量（本 run numSeg==1 行批路径的整条 carry 链是死代码，19/20 case 走该路径）？
- 目标实现是否满足：向量管是该算子的实测瓶颈（本 run aiv_vec_ratio 0.66-0.96 覆盖全部匹配 launch；c13 0.946）？
- 是否命中排除条件：守卫结果不满足前缀单调性时不适用？
- 是否命中排除条件：精度契约把 NaN/Inf 纳入比较时不适用？
- 是否命中排除条件：路径不存在恒零 carry 不变量时不适用（本 run c12 段路径跨段 carry 是活路径）？
- 是否命中排除条件：外提对象是向量不变量构造（tap-loop-invariant-vector-hoisting）或用已有中间量替换整遍归约（max-identity-substitution）时不属于本机制？

## 7. 验收标准

正确性：

- 守卫外提：20/20 PASS（0 次修复），5 对配对中全部 20 case 均改善、逐 case ratio 0.8695-0.9729，零回归；标量 carry 守卫（Compute / ComputeBlockOffset）未改，且只改了 kernel/cumulativetrapezoid_kernel.h 一个文件
- 退化段：20/20 PASS 首次通过（0 次修复）；与冻结基线 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素为 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False）
- 退化段的两条代码事实：carry==0 时 two-sum 恒等于 0（s=hi+0 逐位等于 hi、e=0），且扫描每步存 hi 前已对该步 sReg 做过 ZeroBadLo（hi 非有限 ⇒ 同步 lo==0），故 out=hi+lo 与现 finalize 逐位一致；bf16 档 RunCarryAddFinalizeHi(carry=0) 退化为 hi 的纯拷贝后再 CAST_RINT，可改为直接从 resHi CAST
- 段路径 Compute() 与 RunCarryAddFinalize / RunCarryAddFinalizeHi（c12 跨段 carry 的活路径）逐字未动

性能：

- 守卫外提：formal 5 对 ABBA / 10 次独立 msprof（顺序 B,A / A,B / B,A / A,B / B,A；base 独立构建 ext sha 507c58c374104500、cand 7fed8b22e0a26107），kernel geomean 101.076 -> 90.348us（speedup 1.1187，improvement 11.87%）；base 区间 [101.056,101.094]、cand 区间 [90.322,90.381] 完全不重叠，逐 case ratio 0.8695-0.9729
- 退化段：formal 12 次 / 6 对（顺序 A,B,B,A,A,B,B,A,B,A,A,B；A=冻结基线独立构建 sha c2ce3e4a、B=候选 sha 459048fe），geomean 199.128 -> 187.7663us（speedup 1.0605，improvement 5.70%，逐对 ratio 1.0599-1.0610，spread <0.11%）
- 退化段按 dtype 均值：bf16 281.6154 -> 280.6900us（+0.3%）、fp16 85.8168 -> 79.8598us（+7.5%）、fp32 326.7142 -> 295.3234us（+10.6%，c13 1606->1424us）
- 退化段独立筛选口径复核：全量测试入口 geomean 197.7114 -> 186.2828（-5.78%），19 个 numSeg==1 case 全部下降（c13 -11.35%、c20 -7.66%、c5 -6.82%、c17 -7.89%），c12 -0.02% 持平

回滚信号：

- 非有限 lane 的输出形态变化被精度判据看到（说明精度契约或前缀单调性论证不成立）
- 任一 case 的逐位/逐值对照不再与冻结基线一致（退化段路线：±0 符号位以外的位差）
- numSeg 不再恒为 1 而行批路径仍走无 carry finalize（carry 链已变成活路径）
- 删除后 vec 忙时不降或 duration 回退：说明被删的不是 pacing 工作，例如 bf16 档 finalize-hi 本就只有 3 op/块，收益接近于零

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：tap-loop-invariant-vector-hoisting, max-identity-substitution

- loop_20260917_024611（round=01, status=accepted, speedup=1.1187, precision=20/20 PASS（0 次修复）；5 对配对中全部 20 case 均改善、逐 case ratio 0.8695-0.9729，零回归）— operator=cumulativetrapezoid__v2, mechanism=per-step-nan-guard-hoist
- loop_20260917_024611（round=01, status=accepted, speedup=1.0605, precision=20/20 PASS 首次通过（0 次修复）；与冻结基线 18/20 case 逐位一致，case 3/16 共 12/44.6M 元素为 ±0 符号位模式差（IEEE 相等），case 11/12/13 为全 NaN/稀疏 inf（raw-bit 一致，torch.equal 因 NaN≠NaN 语义报 False））— operator=cumulativetrapezoid, mechanism=single-seg-zero-carry-deadwork-elimination

## 检索卡（短卡）

动作：把逐块逐步重复的 NaN/Inf 守卫外提到段末消费点一次，并把退化段恒零的 carry 链整段删掉
适用：补偿 two-sum Hillis-Steele 扫描，守卫逐步重复；精度契约排除非有限元素；numSeg==1 恒零 carry
限制：外提须同时成立前缀单调性与精度契约排除非有限元素；退化段删除须以 numSeg==1 为门；守卫只留消费点一次且不得改 hi 通道
范围：补偿前缀扫描类算子的逐块守卫与退化段 carry 链
检索词：ZeroBadLo、FinalizeBlockCore、FinalizeNoCarry、Hillis-Steele、CAST_RINT、前缀单调性
机会：每块每步约 22 条向量指令中约 7 条用于重复的 NaN/Inf 守卫，而只有段末消费的 (hi,lo) 对需要它
代价：收益取决于被删区域在向量管上的份额；bf16 档 finalize-hi 仅 3 op/块，收益接近零
