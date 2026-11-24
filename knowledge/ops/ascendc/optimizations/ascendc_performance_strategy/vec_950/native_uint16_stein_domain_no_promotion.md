---
type: Optimization
title: int16 T1 原生 uint16 Stein 计算域（废除 int16→int32 提升）
description: 对 int16 实例废除 int16→int32 提升，在 uint16 无符号域重实例化 Stein 轮体与归一化阶梯，出口按位视图存回 int16。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/native-uint16-stein-domain-no-promotion.md
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
      "T2/T3 共享模板必须以 if constexpr(sizeof(T)==2) 隔离，else 臂文本不得改动（防编译面泄漏回归全部 dtype 实例）",
      "出口 A*P 回绕位形需与提升域 wrap-cast 出口逐位一致（含 0x8000/-32768 角点：32768=0x8000 两路同为 int16 位 0x8000）",
      "零新增缓冲：uint16 视图复用现有 prom/g 窗口，不得引入新 TBuf"
    ],
    "excluded_conditions": [
      "staging/组装段主导的 case（组装税不随计算域减半收缩）——收益封顶，应叠加 staging 税削减机制",
      "目标硬件 16 位 ALU 无 lane 宽度/吞吐增益（gate-0 探测不过即中止并归档边界）",
      "需要保持有符号排序的中间量：必须用 uint16 而非 int16 域承载计算（Min/|a-b| 语义）"
    ],
    "required_conditions": [
      "dtype=int16 且现实现把每元素提升到 int32 计算域（存在 TW 提升类型条件）",
      "向量核 16 位 ALU 确以 2x lane 或更高吞吐发射（实现前 gate-0 探测：16 位 vs int32 等元素合成链 vec cycles 比 <=0.75）",
      "窄域算术封闭：abs 后值域与中间量在 uint16 内不溢出，归一化阶梯宽度恰覆盖可能公共尾零数（值域不变则最坏轮数不变）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "846833e1ceb0bfd84af99f427cb1997c0ec9c9a93cc0a2836662ea65da236d65",
      "decision_sha256": "a98d5a81854de2734871a810e0c0aa4ed834aa7ece597a91304513b2d1b27ffa",
      "operator_class": "broadcast",
      "performance_sha256": "75f6573cc52b54351501171c6c45192ed4d307021e74007fb601fe2213ab4dba",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "7b94d098d07e7cf59f5807725bdded02cd0774ca3dcc4ef420df2a9978583c40",
      "verify_sha256": "9b5b570a6511bd7d1bf672750a55af07ce272a03124112d650723d5fc9e9ed38"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "promotion-width-waste",
      "fixed-round-loop"
    ],
    "dtypes": [
      "int16"
    ],
    "pattern": "native-narrow-domain-no-promotion",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "unsigned-native-domain",
      "dtype-scoped-dispatch"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-NATIVE-U16-STEIN-DOMAIN-NO-PROMOTION",
  "implementation_steps": [
    "gate-0 探测：uint16 原语链可编译运行；16 位 vs int32 等元素量合成链 vec cycles 比 <=0.75；角点（含 -32768/0x8000/(0,0)）对 int32 参考逐位一致",
    "改写 T1 专属函数为 uint16 域（abs 公式、归一化阶梯、{2,1} 轮体、wrap-cast 出口）",
    "A/B 逐位差分 + 宿主穷举等价检查（2^32 int16 pair 空间：0 值 / 0 轮数 mismatch，最坏轮数 < MAX_ROUNDS）",
    "核对 T2/T3 else 臂编译产物字节不变"
  ],
  "intent": "消除提升域下每向量 op 只处理一半元素、每次进出块各付一条 cast 的纯计算浪费（16 位 ALU 以 2x lane 发射时提升即浪费）。",
  "mechanism": "改写 T1 专属函数（ComputeGcdAbsInitT1 / ComputeGcdChunkedT1 / ComputeGcdFinalVFT1）：abs 以 (a^mask)-mask 无符号公式（Abs 无 u16 变体时用 GE+Sub+Select 等价）；轮体在 RegTensor<uint16_t> 上重实例化（尾零剥离 {8,4,2,1} + 奇偶交换收缩，收缩用无符号 Max-Min 差，因 Sub+Abs 在 uint16 会回绕）；出口 A*P 回绕后按位视图存 int16。T2/T3 走 if constexpr(sizeof(T)==2) 的 else 臂零文本改动。零新增 TBuf、零数据分支、零回退路径。",
  "name": "int16 T1 原生 uint16 Stein 计算域（废除 int16→int32 提升）",
  "operator_class": "broadcast",
  "operator_scope": "SIMD RegBase 逐 lane 收敛的二进制 gcd/Stein 轮体中 dtype=int16（DT_INT16）且现实现存在 TW 提升（int16→int32）的实例；适用于『宽提升域由 ALU 链主导』的同类 16 位算术核。",
  "principle": "当硬件向量核 16 位 ALU 以两倍 lane 发射、且轮体中间量在无符号 16 位内算术封闭（abs 后 |x|<=32768，min/|a-b| 与 P=2^g 不溢出，g<=15 被阶梯宽度覆盖，值域不变则轮数不变）时，把整条 dtype 实例迁回原生窄域可在不改变收敛轮数与出口位形的前提下减半每 slice VEC 计算段；收益上界由计算段占比决定。",
  "related_anti_patterns": [],
  "risks": [
    "共享模板改动泄漏到全部 dtype/BCT 实例（编译面泄漏）；本卡只改 T1-only 函数规避共享面",
    "出口位形偏差在 32768=0x8000 角点静默损坏；abs 公式（vabs 回绕 vs (a^mask)-mask）需显式核对",
    "uint16 轮体内误用有符号 Min 或 Sub+Abs 使 32768 变负 / 回绕破坏排序与收敛"
  ],
  "slug": "native-uint16-stein-domain-no-promotion",
  "summary": "对 int16 dtype 实例废除 int16→int32 提升：在 uint16 无符号域重实例化已验证的 {2,1} Stein 轮体 + {8,4,2,1} 归一化阶梯，出口 A*P mod 2^16 按位视图存回 int16，与提升域 wrap-cast 出口逐位一致；16 位原生 ALU 以 2x lane 发射使每 slice VEC 计算段减半，T2/T3 实例经 if constexpr(sizeof(T)==2) 隔离字节不变。",
  "verification": {
    "correctness": [
      "verify 20/20；A/B 逐位差分 + 2^32 int16 pair 穷举宿主等价 0 value / 0 round mismatch，最坏轮数 19 < MAX_ROUNDS"
    ],
    "performance": [
      "T1 目标聚合约 1.48x（预测带 [1.47,1.65] 下缘），5/6 目标 1.47-1.59x；T2/T3 控制在 [0.993,1.006] 噪声带；gate-0 VEC-segment cycles 比 0.60-0.64x vs int32"
    ],
    "rollback_signals": [
      "任一目标 case median 改善 <15% → 机制证伪（lane 未加宽或固定段占比超模型），回退",
      "任一 T2/T3 控制出 [0.98,1.02] → sizeof(T)==2 隔离泄漏，回退检查 else 臂",
      "探针通过而实现失败 → 收窄到已探测原语集"
    ]
  }
}
-->

# 性能优化策略：int16 T1 原生 uint16 Stein 计算域（废除 int16→int32 提升）

单一优化点：对 int16 dtype 实例废除 int16→int32 提升：在 uint16 无符号域重实例化已验证的 {2,1} Stein 轮体 + {8,4,2,1} 归一化阶梯，出口 A*P mod 2^16 按位视图存回 int16，与提升域 wrap-cast 出口逐位一致；16 位原生 ALU 以 2x lane 发射使每 slice VEC 计算段减半，T2/T3 实例经 if constexpr(sizeof(T)==2) 隔离字节不变。

## 1. 原理

当硬件向量核 16 位 ALU 以两倍 lane 发射、且轮体中间量在无符号 16 位内算术封闭（abs 后 |x|<=32768，min/|a-b| 与 P=2^g 不溢出，g<=15 被阶梯宽度覆盖，值域不变则轮数不变）时，把整条 dtype 实例迁回原生窄域可在不改变收敛轮数与出口位形的前提下减半每 slice VEC 计算段；收益上界由计算段占比决定。

实现机制：改写 T1 专属函数（ComputeGcdAbsInitT1 / ComputeGcdChunkedT1 / ComputeGcdFinalVFT1）：abs 以 (a^mask)-mask 无符号公式（Abs 无 u16 变体时用 GE+Sub+Select 等价）；轮体在 RegTensor<uint16_t> 上重实例化（尾零剥离 {8,4,2,1} + 奇偶交换收缩，收缩用无符号 Max-Min 差，因 Sub+Abs 在 uint16 会回绕）；出口 A*P 回绕后按位视图存 int16。T2/T3 走 if constexpr(sizeof(T)==2) 的 else 臂零文本改动。零新增 TBuf、零数据分支、零回退路径。

## 2. 性能问题模式

- 优化目标：消除提升域下每向量 op 只处理一半元素、每次进出块各付一条 cast 的纯计算浪费（16 位 ALU 以 2x lane 发射时提升即浪费）。
- 适用数据流：SIMD RegBase 逐 lane 收敛的二进制 gcd/Stein 轮体中 dtype=int16（DT_INT16）且现实现存在 TW 提升（int16→int32）的实例；适用于『宽提升域由 ALU 链主导』的同类 16 位算术核。
- Feature signature：`{"bottleneck": ["vec-bound", "promotion-width-waste", "fixed-round-loop"], "dtypes": ["int16"], "pattern": "native-narrow-domain-no-promotion", "structure": ["vec-iterative-loop", "streaming-elementwise", "unsigned-native-domain", "dtype-scoped-dispatch"]}`

## 3. 正确性红线

- 共享模板改动泄漏到全部 dtype/BCT 实例（编译面泄漏）；本卡只改 T1-only 函数规避共享面
- 出口位形偏差在 32768=0x8000 角点静默损坏；abs 公式（vabs 回绕 vs (a^mask)-mask）需显式核对
- uint16 轮体内误用有符号 Min 或 Sub+Abs 使 32768 变负 / 回绕破坏排序与收敛

资源与硬件约束：

- T2/T3 共享模板必须以 if constexpr(sizeof(T)==2) 隔离，else 臂文本不得改动（防编译面泄漏回归全部 dtype 实例）
- 出口 A*P 回绕位形需与提升域 wrap-cast 出口逐位一致（含 0x8000/-32768 角点：32768=0x8000 两路同为 int16 位 0x8000）
- 零新增缓冲：uint16 视图复用现有 prom/g 窗口，不得引入新 TBuf

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- dtype=int16 且现实现把每元素提升到 int32 计算域（存在 TW 提升类型条件）
- 向量核 16 位 ALU 确以 2x lane 或更高吞吐发射（实现前 gate-0 探测：16 位 vs int32 等元素合成链 vec cycles 比 <=0.75）
- 窄域算术封闭：abs 后值域与中间量在 uint16 内不溢出，归一化阶梯宽度恰覆盖可能公共尾零数（值域不变则最坏轮数不变）

不适用：

- staging/组装段主导的 case（组装税不随计算域减半收缩）——收益封顶，应叠加 staging 税削减机制
- 目标硬件 16 位 ALU 无 lane 宽度/吞吐增益（gate-0 探测不过即中止并归档边界）
- 需要保持有符号排序的中间量：必须用 uint16 而非 int16 域承载计算（Min/|a-b| 语义）

## 5. 实施步骤

1. gate-0 探测：uint16 原语链可编译运行；16 位 vs int32 等元素量合成链 vec cycles 比 <=0.75；角点（含 -32768/0x8000/(0,0)）对 int32 参考逐位一致
2. 改写 T1 专属函数为 uint16 域（abs 公式、归一化阶梯、{2,1} 轮体、wrap-cast 出口）
3. A/B 逐位差分 + 宿主穷举等价检查（2^32 int16 pair 空间：0 值 / 0 轮数 mismatch，最坏轮数 < MAX_ROUNDS）
4. 核对 T2/T3 else 臂编译产物字节不变

## 6. LLM 前置问题

- 目标实现是否满足：dtype=int16 且现实现把每元素提升到 int32 计算域（存在 TW 提升类型条件）？
- 目标实现是否满足：向量核 16 位 ALU 确以 2x lane 或更高吞吐发射（实现前 gate-0 探测：16 位 vs int32 等元素合成链 vec cycles 比 <=0.75）？
- 目标实现是否满足：窄域算术封闭：abs 后值域与中间量在 uint16 内不溢出，归一化阶梯宽度恰覆盖可能公共尾零数（值域不变则最坏轮数不变）？
- 是否命中排除条件：staging/组装段主导的 case（组装税不随计算域减半收缩）——收益封顶，应叠加 staging 税削减机制？

## 7. 验收标准

正确性：

- verify 20/20；A/B 逐位差分 + 2^32 int16 pair 穷举宿主等价 0 value / 0 round mismatch，最坏轮数 19 < MAX_ROUNDS

性能：

- T1 目标聚合约 1.48x（预测带 [1.47,1.65] 下缘），5/6 目标 1.47-1.59x；T2/T3 控制在 [0.993,1.006] 噪声带；gate-0 VEC-segment cycles 比 0.60-0.64x vs int32

回滚信号：

- 任一目标 case median 改善 <15% → 机制证伪（lane 未加宽或固定段占比超模型），回退
- 任一 T2/T3 控制出 [0.98,1.02] → sizeof(T)==2 隔离泄漏，回退检查 else 臂
- 探针通过而实现失败 → 收窄到已探测原语集

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260901_132104-7bcd41（round=2, status=accepted）

## 检索卡（短卡）

动作：对 int16 实例废除 int16→int32 提升，在 uint16 无符号域重实例化 Stein 轮体与归一化阶梯，出口按位视图存回 int16。
适用：dtype=int16 且现实现提升到 int32、gate-0 探测 16 位/int32 vec cycles <=0.75。
限制：共享模板须以 if constexpr(sizeof(T)==2) 隔离且 else 臂不得改动；出口须与 wrap-cast 逐位一致。
范围：broadcast 类 16 位算术核的 RegBase 逐 lane 收敛轮体。
检索词：Stein、RegTensor<uint16_t>、wrap-cast、gate-0、Max-Min 差、DT_INT16
机会：提升域下每向量 op 只处理一半元素，每次进出块各付一条 cast。
代价：staging/组装段主导的 case 收益封顶，组装税不随计算域减半。
