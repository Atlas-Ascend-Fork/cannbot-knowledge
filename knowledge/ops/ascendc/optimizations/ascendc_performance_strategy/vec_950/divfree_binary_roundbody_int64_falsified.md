---
type: Optimization
title: 无除法二进制 GCD（Stein）轮体在 int64 计算域的负向边界：B64 软件移位阶梯比被替换的软件除法更贵
description: 负向边界：int64/B64 域用 Stein 无除法轮体替换 Div/Mul 轮体被证伪；int64 域改值域窄化 int32 快路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/divfree-binary-roundbody-int64-falsified.md
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
      "结论基于 gcd 单算子（broadcast 类）15-case 验证集；跨算子类复用前须在目标宽度用编译产物/逐指令 msprof 核实被移除与新增指令的真实发射序列与单价",
      "共享轮体改动影响所有 dtype/BCT 模板实例，回退判定必须按 dtype 域分别声明，不能以 aggregate net gain 掩盖目标域回归",
      "int64 域每轮收益上界必须先估算 dominant 指令周期占比，低于 improved_speedup 阈值则放弃立项"
    ],
    "excluded_conditions": [
      "计算在 TW=int32（单指令 vdiv）或提升域（int16 提升 int32）执行时本负向边界不适用——同一 Stein 轮体在 int32 域是 validated（见 ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED）",
      "int64 域应改用数据域窄化快路径（值域 <2^31 的 slice 按 int32 视图执行，见 ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH），而非在 B64 上替换轮体",
      "轮体被非 dominant 指令主导或编译器已 CSE 冗余指令时，指令计数模型失效的其它边界见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN"
    ],
    "required_conditions": [
      "热链是 VEC-bound 的固定/分块轮体逐 lane 迭代（如截断欧几里得 GCD），轮体在 TW=int64（B64）原生域执行",
      "计划以'无除法轮体/多指令序列'替换轮体中的 dominant 向量整数除法，并声称收益来自每轮指令数/单价下降",
      "被移除的 dominant 指令与新增的'廉价'操作在目标宽度下都是软件展开的多指令序列（sizeof(T)==8 的 ShiftRights/Div 等）",
      "轮体替换会同时改变每轮指令构成与轮数结构（Stein ≈ bitlen vs Euclid ≈ 商位数），两者都需纳入收益估算"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "case": "T3(3,6,9,13,17,20) int64 target + T1/T2(2,4,5,7,11,12,14,16,18) int32",
      "operator_class": "broadcast",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "int32 domain 1.61-2.91x validated; int64 domain 0.8799x aggregate (0.817-0.833x on 4 T3 cases); incremental total 1.0610x, target aggregate 0.9669x",
      "status": "rejected"
    },
    {
      "comparison_sha256": "16c95148f21145a321effff00e8ac9442b6d825b84c89c44d1ce8d263e968331",
      "decision_sha256": "5e800c3d3e197348b9170e4c7bb24d8068fa8db1536e66900f381a72257f54df",
      "operator_class": "broadcast",
      "performance_sha256": "66a89cffa8d5e601d9eaf2567188101558e69a9c425081300694c7bb975992a3",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "a9c84a1cbdaab1d7120650b9bfc8bc4990df8c6b11d9e7886ebf2e571a4c8c9e",
      "verify_sha256": "7449faa86afffaf51dc95eca8dd745d170b1b86f428bf50d3b5a0828931a8bee"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "fixed-round-loop",
      "div-dominant",
      "int64-software-shift"
    ],
    "dtypes": [
      "int64"
    ],
    "pattern": "divfree-roundbody-int64-falsified",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "software-emulated-b64"
    ]
  },
  "generality": "op_class",
  "id": "NEG-ELEM-DIVFREE-BINARY-ROUNDBODY-INT64",
  "implementation_steps": [
    "对计划替换的轮体，在目标 dtype 域（尤其 int64/B64）用编译产物或逐指令 msprof 核实被移除的 dominant 指令（DivB64Impl）与新增序列（6 步 ShiftRights 阶梯）各自的每轮周期与发射指令数",
    "在共享轮体上实施替换，保持既有分块早退/停止保护/同步结构逐字不变",
    "以目标 dtype 域的验证集做增量 compare（相对上一 accepted 状态），按 dtype 域拆分归因（cyc/el、vec_ratio、route 级速度比）",
    "任一目标 route 回归超阈值即按预注册 rollback 回退，不保留'仅控制域收益'的全局编辑",
    "全局替换失败时，把已验证的 dtype 域剥离为 scoped 变体重落地（见 ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED），失败域留给独立机制（如数据域窄化）"
  ],
  "intent": "记录'轮体替换/指令数削减必然转化为 VEC 收益'假设在 int64/B64 计算域的失效边界：当被移除的 dominant 指令本身是软件序列、新增指令单价不低于它、且替换改变轮数结构时，指令计数模型给出错误的收益预期。",
  "mechanism": "在 gcd 共享轮体上把 GcdEuclidStep 的 Div/Mul 轮体替换为 GcdSteinStep：GcdStripOddLadder 以 5 步（int32 {16,8,4,2,1}）或 6 步（int64 {32,16,8,4,2,1}）条带阶梯把 B 右移 tz(B) 剥到奇，随后 D=|A-B|、M=min(A,B)、Compares(B!=0) 守卫 Select 更新 A/B；GcdSteinNormalize 以 P=2^g 携带公共尾零并在 final 用 Mul(A,A,P) 折回。实测 TW=int32 域（T1 提升 + T2 原生）1.61-2.91x；TW=int64 域（T3）aiv_total_cycles/element 上升 20-22%（case 9: 197.5->241.7、case 13: 203.5->249.0、case 17: 197.8->241.8、case 20: 207.7->249.6），四条 route 0.817-0.833x，Block Num 恒定 64，属轮体内部成本。该边界把最终落地机制限定到 int32 计算域（ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED），int64 域改用数据域窄化快路径（ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）。",
  "name": "无除法二进制 GCD（Stein）轮体在 int64 计算域的负向边界：B64 软件移位阶梯比被替换的软件除法更贵",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为编译期固定/分块轮数的逐 lane 迭代循环（如截断欧几里得 GCD，已有 chunk 早退/停止保护），轮体在 TW=int64（B64）原生域执行（32 lane/block，int64 原语多为软件展开序列）",
  "principle": "VEC-bound 下轮体替换的收益取决于'被移除指令的每轮周期'与'新增指令序列的每轮周期'之差。在 int64/B64 原生域，向量整数除法 DivB64Impl 与向量移位（sizeof(T)==8 的 ShiftRights）都是软件展开的多指令序列；若新增的'廉价'操作单价不低于被移除的除法，且 Stein 轮数（≈bitlen）还高于 Euclid 轮数（≈商位数），则轮体替换在 int64 域净回归。指令计数模型（把每条 API 当作常数成本）对 int32（单指令 vdiv）成立、对 int64 失效；共享轮体改动必须按 dtype 域分别验证。",
  "related_anti_patterns": [],
  "risks": [
    "把 int32 域的验证外推到 int64：指令计数模型对 B64 软件序列失效，int64 域净回归 20-22%",
    "以 aggregate net gain 掩盖目标域回归：T3 两条 route 承载 73.7% 运行时间权重，target aggregate 0.9669x 即 net 回归于自身目标，不可接受",
    "轮数假设错误：Stein ≈ bitlen 高于 Euclid ≈ 商位数，在中小值域（case 集主体）尤其不利",
    "跨测量会话噪声（0.5-8%）干扰 18-22% 级回归归因时，用多重独立采集与 aiv_total_cycles 列交叉验证"
  ],
  "slug": "divfree-binary-roundbody-int64-falsified",
  "summary": "在 int64/TW=int64 计算域，用 6 步条带阶梯（6 条 int64 ShiftRights，每条都是 B64 软件序列）+ And/Compare/Select/Sub/Abs/Min 替换 Div/Mul 截断欧几里得轮体被实测证伪：per-element 向量成本上升 20-22%，四条 T3 route 0.817-0.833x 回归、仅最大值域 case 持平，T3 合计 0.8799x。原因：被替换的 DivB64Impl 软件除法并非每轮 dominant 成本，而 B64 软件移位序列单价不低于它，且 Stein 轮数 ≈ bitlen 高于 Euclid ≈ 商位数——'26-30 个廉价操作/轮'的指令计数模型在 int64 域失效。",
  "verification": {
    "correctness": [
      "round 1 verify ok=true，20/20（run.json.all_cases），在 frozen producer 上对已安装 kernel 526e12bece4fc9a1 复验"
    ],
    "performance": [
      "int64 域（T3）6 case：4 条回归 0.8171-0.8329x（case 9/13/17/20，三个为目标 case），case 3 1.032x 持平、case 6 0.9902 持平，T3 合计 0.8799x",
      "int32 域（T1+T2）9 case：1.61-2.91x 全部改善（同一轮体在 int32 域 validated，见 round-2 卡片）",
      "归因：aiv_total_cycles/element 在 T3 上升 20-22%（case 9: 197.5->241.7、case 13: 203.5->249.0、case 17: 197.8->241.8、case 20: 207.7->249.6），Block Num 恒定 64，vec_ratio 99.3-99.6% 不变——轮体内部成本，非 tiling/同步/memory",
      "增量 compare：total 1.0610x，但 target aggregate 0.9669x（net 回归于自身目标），触发预注册 rollback 条件"
    ],
    "rollback_signals": [
      "任一 target route 相对上一 accepted 回归超阈值（本 round 四条 T3 case 0.817-0.833x 触发）",
      "dtype 域拆分后目标域净回归（target aggregate 0.9669x）",
      "被替换的 dominant 指令并非每轮成本主导（int64 Div 非 dominant）或新增序列单价不低于它，收益模型失效"
    ]
  }
}
-->

# 性能优化策略：无除法二进制 GCD（Stein）轮体在 int64 计算域的负向边界：B64 软件移位阶梯比被替换的软件除法更贵

单一优化点：在 int64/TW=int64 计算域，用 6 步条带阶梯（6 条 int64 ShiftRights，每条都是 B64 软件序列）+ And/Compare/Select/Sub/Abs/Min 替换 Div/Mul 截断欧几里得轮体被实测证伪：per-element 向量成本上升 20-22%，四条 T3 route 0.817-0.833x 回归、仅最大值域 case 持平，T3 合计 0.8799x。原因：被替换的 DivB64Impl 软件除法并非每轮 dominant 成本，而 B64 软件移位序列单价不低于它，且 Stein 轮数 ≈ bitlen 高于 Euclid ≈ 商位数——'26-30 个廉价操作/轮'的指令计数模型在 int64 域失效。

## 1. 原理

VEC-bound 下轮体替换的收益取决于'被移除指令的每轮周期'与'新增指令序列的每轮周期'之差。在 int64/B64 原生域，向量整数除法 DivB64Impl 与向量移位（sizeof(T)==8 的 ShiftRights）都是软件展开的多指令序列；若新增的'廉价'操作单价不低于被移除的除法，且 Stein 轮数（≈bitlen）还高于 Euclid 轮数（≈商位数），则轮体替换在 int64 域净回归。指令计数模型（把每条 API 当作常数成本）对 int32（单指令 vdiv）成立、对 int64 失效；共享轮体改动必须按 dtype 域分别验证。

实现机制：在 gcd 共享轮体上把 GcdEuclidStep 的 Div/Mul 轮体替换为 GcdSteinStep：GcdStripOddLadder 以 5 步（int32 {16,8,4,2,1}）或 6 步（int64 {32,16,8,4,2,1}）条带阶梯把 B 右移 tz(B) 剥到奇，随后 D=|A-B|、M=min(A,B)、Compares(B!=0) 守卫 Select 更新 A/B；GcdSteinNormalize 以 P=2^g 携带公共尾零并在 final 用 Mul(A,A,P) 折回。实测 TW=int32 域（T1 提升 + T2 原生）1.61-2.91x；TW=int64 域（T3）aiv_total_cycles/element 上升 20-22%（case 9: 197.5->241.7、case 13: 203.5->249.0、case 17: 197.8->241.8、case 20: 207.7->249.6），四条 route 0.817-0.833x，Block Num 恒定 64，属轮体内部成本。该边界把最终落地机制限定到 int32 计算域（ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED），int64 域改用数据域窄化快路径（ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH）。

## 2. 性能问题模式

- 优化目标：记录'轮体替换/指令数削减必然转化为 VEC 收益'假设在 int64/B64 计算域的失效边界：当被移除的 dominant 指令本身是软件序列、新增指令单价不低于它、且替换改变轮数结构时，指令计数模型给出错误的收益预期。
- 适用数据流：VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链为编译期固定/分块轮数的逐 lane 迭代循环（如截断欧几里得 GCD，已有 chunk 早退/停止保护），轮体在 TW=int64（B64）原生域执行（32 lane/block，int64 原语多为软件展开序列）
- Feature signature：`{"bottleneck": ["vec-bound", "fixed-round-loop", "div-dominant", "int64-software-shift"], "dtypes": ["int64"], "pattern": "divfree-roundbody-int64-falsified", "structure": ["vec-iterative-loop", "streaming-elementwise", "software-emulated-b64"]}`

## 3. 正确性红线

- 把 int32 域的验证外推到 int64：指令计数模型对 B64 软件序列失效，int64 域净回归 20-22%
- 以 aggregate net gain 掩盖目标域回归：T3 两条 route 承载 73.7% 运行时间权重，target aggregate 0.9669x 即 net 回归于自身目标，不可接受
- 轮数假设错误：Stein ≈ bitlen 高于 Euclid ≈ 商位数，在中小值域（case 集主体）尤其不利
- 跨测量会话噪声（0.5-8%）干扰 18-22% 级回归归因时，用多重独立采集与 aiv_total_cycles 列交叉验证

资源与硬件约束：

- 结论基于 gcd 单算子（broadcast 类）15-case 验证集；跨算子类复用前须在目标宽度用编译产物/逐指令 msprof 核实被移除与新增指令的真实发射序列与单价
- 共享轮体改动影响所有 dtype/BCT 模板实例，回退判定必须按 dtype 域分别声明，不能以 aggregate net gain 掩盖目标域回归
- int64 域每轮收益上界必须先估算 dominant 指令周期占比，低于 improved_speedup 阈值则放弃立项

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 热链是 VEC-bound 的固定/分块轮体逐 lane 迭代（如截断欧几里得 GCD），轮体在 TW=int64（B64）原生域执行
- 计划以'无除法轮体/多指令序列'替换轮体中的 dominant 向量整数除法，并声称收益来自每轮指令数/单价下降
- 被移除的 dominant 指令与新增的'廉价'操作在目标宽度下都是软件展开的多指令序列（sizeof(T)==8 的 ShiftRights/Div 等）
- 轮体替换会同时改变每轮指令构成与轮数结构（Stein ≈ bitlen vs Euclid ≈ 商位数），两者都需纳入收益估算

不适用：

- 计算在 TW=int32（单指令 vdiv）或提升域（int16 提升 int32）执行时本负向边界不适用——同一 Stein 轮体在 int32 域是 validated（见 ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED）
- int64 域应改用数据域窄化快路径（值域 <2^31 的 slice 按 int32 视图执行，见 ELEM-INT64-NARROW-INT32-DOMAIN-FASTPATH），而非在 B64 上替换轮体
- 轮体被非 dominant 指令主导或编译器已 CSE 冗余指令时，指令计数模型失效的其它边界见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN

## 5. 实施步骤

1. 对计划替换的轮体，在目标 dtype 域（尤其 int64/B64）用编译产物或逐指令 msprof 核实被移除的 dominant 指令（DivB64Impl）与新增序列（6 步 ShiftRights 阶梯）各自的每轮周期与发射指令数
2. 在共享轮体上实施替换，保持既有分块早退/停止保护/同步结构逐字不变
3. 以目标 dtype 域的验证集做增量 compare（相对上一 accepted 状态），按 dtype 域拆分归因（cyc/el、vec_ratio、route 级速度比）
4. 任一目标 route 回归超阈值即按预注册 rollback 回退，不保留'仅控制域收益'的全局编辑
5. 全局替换失败时，把已验证的 dtype 域剥离为 scoped 变体重落地（见 ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED），失败域留给独立机制（如数据域窄化）

## 6. LLM 前置问题

- 目标实现是否满足：热链是 VEC-bound 的固定/分块轮体逐 lane 迭代（如截断欧几里得 GCD），轮体在 TW=int64（B64）原生域执行？
- 目标实现是否满足：计划以'无除法轮体/多指令序列'替换轮体中的 dominant 向量整数除法，并声称收益来自每轮指令数/单价下降？
- 目标实现是否满足：被移除的 dominant 指令与新增的'廉价'操作在目标宽度下都是软件展开的多指令序列（sizeof(T)==8 的 ShiftRights/Div 等）？
- 是否命中排除条件：计算在 TW=int32（单指令 vdiv）或提升域（int16 提升 int32）执行时本负向边界不适用——同一 Stein 轮体在 int32 域是 validated（见 ELEM-DIVFREE-BINARY-ROUNDBODY-INT32-SCOPED）？

## 7. 验收标准

正确性：

- round 1 verify ok=true，20/20（run.json.all_cases），在 frozen producer 上对已安装 kernel 526e12bece4fc9a1 复验

性能：

- int64 域（T3）6 case：4 条回归 0.8171-0.8329x（case 9/13/17/20，三个为目标 case），case 3 1.032x 持平、case 6 0.9902 持平，T3 合计 0.8799x
- int32 域（T1+T2）9 case：1.61-2.91x 全部改善（同一轮体在 int32 域 validated，见 round-2 卡片）
- 归因：aiv_total_cycles/element 在 T3 上升 20-22%（case 9: 197.5->241.7、case 13: 203.5->249.0、case 17: 197.8->241.8、case 20: 207.7->249.6），Block Num 恒定 64，vec_ratio 99.3-99.6% 不变——轮体内部成本，非 tiling/同步/memory
- 增量 compare：total 1.0610x，但 target aggregate 0.9669x（net 回归于自身目标），触发预注册 rollback 条件

回滚信号：

- 任一 target route 相对上一 accepted 回归超阈值（本 round 四条 T3 case 0.817-0.833x 触发）
- dtype 域拆分后目标域净回归（target aggregate 0.9669x）
- 被替换的 dominant 指令并非每轮成本主导（int64 Div 非 dominant）或新增序列单价不低于它，收益模型失效

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260826_015717-b0d16d（round=1, status=rejected, case=T3(3,6,9,13,17,20) int64 target + T1/T2(2,4,5,7,11,12,14,16,18) int32, speedup=int32 domain 1.61-2.91x validated; int64 domain 0.8799x aggregate (0.817-0.833x on 4 T3 cases); incremental total 1.0610x, target aggregate 0.9669x）
- gcd-20260826_015717-b0d16d（round=1, status=rejected）

## 检索卡（短卡）

动作：负向边界：int64/B64 域用 Stein 无除法轮体替换 Div/Mul 轮体被证伪；int64 域改值域窄化 int32 快路径。
适用：热链为 VEC-bound 固定/分块轮体逐 lane 迭代（如截断 GCD），轮体在 TW=int64（B64）域执行。
限制：勿把 int32 域验证外推到 int64；勿以 aggregate net gain 掩盖目标域回归；共享轮体须按 dtype 域分别验证。
范围：elementwise-arithmetic 类整数迭代算子（如 gcd）。
检索词：Stein、GcdSteinStep、DivB64Impl、ShiftRights、条带阶梯、B64、软件展开序列。
机会：计划以无除法轮体替换 dominant 向量整数除法并声称收益来自指令数下降。
代价：int64 域 per-element 成本升 20-22%，四条 route 0.817-0.833x。
