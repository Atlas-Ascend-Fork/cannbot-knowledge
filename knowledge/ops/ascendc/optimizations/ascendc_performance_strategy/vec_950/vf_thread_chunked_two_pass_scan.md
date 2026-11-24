---
type: Optimization
title: VF 线程级线内分段两遍扫描（精确 int64 combine + 段内自包含回退）
description: 把 thread-per-line 的线内串行链按段切给空闲 VF 线程槽，用两遍扫描（段内扫状态加跨段精确归并）并行化。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/vf-thread-chunked-two-pass-scan.md
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
      "段边界必须以精确 int64 状态 (accM,accE,latch) 落 GM workspace（16B 槽），Pass2 归并依赖 int64 align-min 的结合律等价于串行折叠",
      "Pass1 命中非有限 break 的段必须由段内慢链锁存语义接管，逐段自包含，禁止跨线程写竞争",
      "片内快链须与既有 dd 快链同构（本 run 复用 d002 的 (hi,lo) 快链 + 慢链回退），保证有限值段位级 = champion"
    ],
    "excluded_conditions": [
      "segs < 4 时净负：两遍扫描总计算量翻倍，净并行增益 = segs/2 再扣 x 双读 +50% 流量；segs=2 实测 case 4 -36% / case 5 -10% 必负",
      "linesPerCore 已接近 256（VF 线程槽已占满）：无空闲线程槽可兑现，切段只增加双读流量",
      "split 路径（跨核线拆分，totalLines*4<=coreNum 极少线域）不在本机制范围"
    ],
    "required_conditions": [
      "热路径为 thread-per-line 线模型且 linesPerCore < 256，存在大量空闲 VF 线程槽（本 run case 4/5 每核 128/256、case 2 每核 32/256、case 15 每核 8/256）",
      "线内串行依赖链是主要时延来源（每元素 ~16-18 条 VF 指令的 dd 链），有可切分的线内并行度",
      "段间状态可精确 combine（int64 满足结合律，本代码库 split 路径已有现役 combine 先例）",
      "宿上位级仿真可验证：命中 case 段结果与 golden、与 champion 输出三方零差异"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 395.3,
      "before_us": 470.7,
      "operator": "cumsum_minimum",
      "operator_class": "reduction",
      "pairs": 200,
      "pairs_per_case": 10,
      "precision": "20/20 PASS (host_sim_seg.py: routed cases bit-identical to golden AND champion chain, 0 diff points)",
      "run_id": "<run-id>",
      "session_ids": ["ses_f792272a6ffeex38vATqjJwRLO"],
      "speedup": 1.191,
      "status": "accepted",
      "worst_case_ratio": 0.978
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vf-thread-slot-underutilized",
      "intra-line-serial-dependency-chain",
      "line-internal-parallelism"
    ],
    "pattern": "vf-thread-chunked-two-pass-scan",
    "structure": [
      "thread-per-line-model",
      "intra-line-segmentation",
      "exact-int64-state-combine",
      "per-segment-self-contained-fallback"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-VF-THREAD-CHUNKED-TWO-PASS",
  "implementation_steps": [
    "op_kernel tiling_data：新增 segSplitMode/segCount/segSlotStride 字段",
    "op_host tiling：seg 路由 segs = min(256/lpcMax, scanLen/512)，下限钳 segs>=4（下限是净收益正域的必要条件），split 路径优先；计算 16B 槽 workspace 尺寸",
    "op_kernel kernel.cpp：新增 segSplitMode 入口分支（InitSeg/ProcessSeg + GetUserWorkspace）",
    "op_kernel t1.h：新增 KdDdStep/KdDdToInt64/KdInt64ToDd/KdSlowStepF32/KdSegBounds helper（含零值加数跳过防护）+ ScanSegStateVF/ScanSegMergeVF 两遍 VF；原 ScanLinesGmVF 与 split 路径逐字未动",
    "Pass1 各线程扫段只推进状态，段末精确 int64 (accM,accE,latch) 落 GM workspace；SyncAll 后 Pass2 归并同线前序段状态，latch==0 由精确前缀重建 (hi0,lo0) 后段内 dd 快链逐点写 y"
  ],
  "intent": "在 thread-per-line 线模型下，把线内串行 dd 依赖链按段切分给空闲的 VF 线程槽，用两遍扫描（段内扫状态 + 跨段精确归并）把线内串行改为线程间并行，直接缩短关键路径。",
  "mechanism": "线内分段两遍扫描：每线切 segs 段（segs=min(256/lpcMax, scanLen/512)，路由下限 segs>=4），Pass1 各 VF 线程以 champion 同构混合链（dd 快链 + 段内 break 慢链接管）扫段只推进状态，段末精确 int64 (accM,accE,latch) 落 GM workspace（16B 槽）；SyncAll 后 Pass2 归并同线前序段状态（int64 align-min 结合律 = 串行折叠等价），latch!=0 走段内慢链锁存语义（位级=champion），latch==0 由精确前缀重建 (hi0,lo0) 后段内 dd 快链逐点写 y；理论角点 break 时段内 int64 慢链从段首重扫（逐段自包含，无跨线程写竞争）。",
  "name": "VF 线程级线内分段两遍扫描（精确 int64 combine + 段内自包含回退）",
  "operator_class": "reduction",
  "operator_scope": "thread-per-line 线模型的扫描/前缀类算子热路径，linesPerCore < 256 导致 VF 线程槽大量空闲、线内为串行依赖链、段间状态可精确 combine 的场景",
  "principle": "线内串行链长度是 wall 的决定项，而 VF 的并行度由线程槽数（256）决定；当 linesPerCore < 256 时空闲线程槽即未兑现的并行度。把线切段分给线程，串行链长度除以 segs，但两遍扫描使总计算量翻倍、且 x 被双读（+50% 流量），故净增益 ≈ segs/2 − 双读流量。据此 segs 存在一个下限（本 run 实测 segs>=4），低于该下限必负——路由下限是机制成立的前提而非调参。",
  "related_anti_patterns": [],
  "risks": [
    "segs 下限估计偏保守会丢失收益、偏激进会引入回退：本 run r1（segs>=2）被筛选否决（case 4 -36% / case 5 -10%），r2 收敛 segs>=4 后 case 4/5 回到持平、segs>=4 全域显著收益",
    "case 12（未触碰的 split 路径）稳定 -2.2%，归因二进制体积副作用，量级与 d002 已接受先例相同",
    "两遍扫描的 workspace 读写与 SyncAll 增加 GM 流量，极端紧 UB 场景需重新对账预算"
  ],
  "slug": "vf-thread-chunked-two-pass-scan",
  "summary": "把 T1 fast/gen 路径的 thread-per-line 线模型（linesPerCore<256 时 VF 256 线程槽大量空闲）升级为线内分段两遍扫描：每线切 segs 段，Pass1 各线程以 champion 同构混合链扫段只推进状态、段末精确 int64 (accM,accE,latch) 落 GM workspace；SyncAll 后 Pass2 归并同线前序段状态（int64 align-min 结合律=串行折叠等价），latch==0 由精确前缀重建后段内 dd 快链逐点写 y。20 case geomean 470.7→395.3us（1.191x）。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS；宿上位级仿真 host_sim_seg.py：命中 9 case 采样线 vs torch golden 与 vs champion 输出均 0 差异",
      "含 case 11 的 245 次 Pass2 理论角点 break 被段内慢链正确接管；未命中域零影响",
      "仿真发现 champion KdAccAddState 防御降级在 (mw=0, ew=-149) 且指数差>62 时钳位 -2^62 的休眠角点（测试集从未触发），新路径以零值加数跳过防护"
    ],
    "performance": [
      "形式化 ABAB 平衡交替配对（A1 B1 A2 B2，新鲜构建，5 runs/case/block）：200 对，geomean 470.7→395.3us（1.191x）",
      "6 个路由 case 全 10/10 胜（1.016-3.160x）；case 11 溢出回退线 3.16x、case 18/10 1.91/1.82x、case 3/15 1.79/1.69x、case 2 1.016x",
      "去路由/未路由 case 0.997-1.003 零差异噪声；case 12 0/10 at 0.978（未触碰 split 路径，二进制体积副作用）",
      "best_case_ratio 3.16 / worst_case_ratio 0.978"
    ],
    "rollback_signals": [
      "segs 下限低于净收益正域（segs=2 类配置）导致多 case 回退——本 run r1 已实证",
      "段间 combine 与串行折叠不再等价（int64 结合律被破坏或 latch 语义走错分支）",
      "宿上位级仿真出现段结果与 golden/champion 差异",
      "未命中域出现超出噪声的回退"
    ]
  }
}
-->

# 性能优化策略：VF 线程级线内分段两遍扫描（精确 int64 combine + 段内自包含回退）

把 T1 fast/gen 路径的 thread-per-line 线模型（linesPerCore<256 时 VF 256 线程槽大量空闲）升级为线内分段两遍扫描：每线切 segs 段，Pass1 各线程以 champion 同构混合链扫段只推进状态、段末精确 int64 (accM,accE,latch) 落 GM workspace；SyncAll 后 Pass2 归并同线前序段状态（int64 align-min 结合律=串行折叠等价），latch==0 由精确前缀重建后段内 dd 快链逐点写 y。20 case geomean 470.7→395.3us（1.191x）。

## 1. 原理

线内串行链长度是 wall 的决定项，而 VF 的并行度由线程槽数（256）决定；当 linesPerCore < 256 时空闲线程槽即未兑现的并行度。把线切段分给线程，串行链长度除以 segs，但两遍扫描使总计算量翻倍、且 x 被双读（+50% 流量），故净增益 ≈ segs/2 − 双读流量。据此 segs 存在一个下限（本 run 实测 segs>=4），低于该下限必负——路由下限是机制成立的前提而非调参。

实现机制：线内分段两遍扫描：每线切 segs 段（segs=min(256/lpcMax, scanLen/512)，路由下限 segs>=4），Pass1 各 VF 线程以 champion 同构混合链（dd 快链 + 段内 break 慢链接管）扫段只推进状态，段末精确 int64 (accM,accE,latch) 落 GM workspace（16B 槽）；SyncAll 后 Pass2 归并同线前序段状态（int64 align-min 结合律 = 串行折叠等价），latch!=0 走段内慢链锁存语义（位级=champion），latch==0 由精确前缀重建 (hi0,lo0) 后段内 dd 快链逐点写 y；理论角点 break 时段内 int64 慢链从段首重扫（逐段自包含，无跨线程写竞争）。

## 2. 性能问题模式

- 优化目标：在 thread-per-line 线模型下，把线内串行 dd 依赖链按段切分给空闲的 VF 线程槽，用两遍扫描（段内扫状态 + 跨段精确归并）把线内串行改为线程间并行，直接缩短关键路径
- 适用数据流：thread-per-line 线模型的扫描/前缀类算子热路径，linesPerCore < 256 导致 VF 线程槽大量空闲、线内为串行依赖链、段间状态可精确 combine 的场景
- Feature signature：`{"bottleneck": ["vf-thread-slot-underutilized", "intra-line-serial-dependency-chain", "line-internal-parallelism"], "pattern": "vf-thread-chunked-two-pass-scan", "structure": ["thread-per-line-model", "intra-line-segmentation", "exact-int64-state-combine", "per-segment-self-contained-fallback"]}`

## 3. 正确性红线

- segs 下限估计偏保守会丢失收益、偏激进会引入回退：本 run r1（segs>=2）被筛选否决（case 4 -36% / case 5 -10%），r2 收敛 segs>=4 后 case 4/5 回到持平、segs>=4 全域显著收益
- case 12（未触碰的 split 路径）稳定 -2.2%，归因二进制体积副作用，量级与 d002 已接受先例相同
- 两遍扫描的 workspace 读写与 SyncAll 增加 GM 流量，极端紧 UB 场景需重新对账预算

资源与硬件约束：

- 段边界必须以精确 int64 状态 (accM,accE,latch) 落 GM workspace（16B 槽），Pass2 归并依赖 int64 align-min 的结合律等价于串行折叠
- Pass1 命中非有限 break 的段必须由段内慢链锁存语义接管，逐段自包含，禁止跨线程写竞争
- 片内快链须与既有 dd 快链同构（本 run 复用 d002 的 (hi,lo) 快链 + 慢链回退），保证有限值段位级 = champion

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- 热路径为 thread-per-line 线模型且 linesPerCore < 256，存在大量空闲 VF 线程槽（本 run case 4/5 每核 128/256、case 2 每核 32/256、case 15 每核 8/256）
- 线内串行依赖链是主要时延来源（每元素 ~16-18 条 VF 指令的 dd 链），有可切分的线内并行度
- 段间状态可精确 combine（int64 满足结合律，本代码库 split 路径已有现役 combine 先例）
- 宿上位级仿真可验证：命中 case 段结果与 golden、与 champion 输出三方零差异

不适用：

- segs < 4 时净负：两遍扫描总计算量翻倍，净并行增益 = segs/2 再扣 x 双读 +50% 流量；segs=2 实测 case 4 -36% / case 5 -10% 必负
- linesPerCore 已接近 256（VF 线程槽已占满）：无空闲线程槽可兑现，切段只增加双读流量
- split 路径（跨核线拆分，totalLines*4<=coreNum 极少线域）不在本机制范围

## 5. 实施步骤

1. op_kernel tiling_data：新增 segSplitMode/segCount/segSlotStride 字段
2. op_host tiling：seg 路由 segs = min(256/lpcMax, scanLen/512)，下限钳 segs>=4（下限是净收益正域的必要条件），split 路径优先；计算 16B 槽 workspace 尺寸
3. op_kernel kernel.cpp：新增 segSplitMode 入口分支（InitSeg/ProcessSeg + GetUserWorkspace）
4. op_kernel t1.h：新增 KdDdStep/KdDdToInt64/KdInt64ToDd/KdSlowStepF32/KdSegBounds helper（含零值加数跳过防护）+ ScanSegStateVF/ScanSegMergeVF 两遍 VF；原 ScanLinesGmVF 与 split 路径逐字未动
5. Pass1 各线程扫段只推进状态，段末精确 int64 (accM,accE,latch) 落 GM workspace；SyncAll 后 Pass2 归并同线前序段状态，latch==0 由精确前缀重建 (hi0,lo0) 后段内 dd 快链逐点写 y

## 6. LLM 前置问题

- 目标实现是否满足：热路径为 thread-per-line 线模型且 linesPerCore < 256，存在大量空闲 VF 线程槽（本 run case 4/5 每核 128/256、case 2 每核 32/256、case 15 每核 8/256）？
- 目标实现是否满足：线内串行依赖链是主要时延来源（每元素 ~16-18 条 VF 指令的 dd 链），有可切分的线内并行度？
- 目标实现是否满足：段间状态可精确 combine（int64 满足结合律，本代码库 split 路径已有现役 combine 先例）？
- 目标实现是否满足：宿上位级仿真可验证：命中 case 段结果与 golden、与 champion 输出三方零差异？
- 是否命中排除条件：segs < 4 时净负：两遍扫描总计算量翻倍，净并行增益 = segs/2 再扣 x 双读 +50% 流量；segs=2 实测 case 4 -36% / case 5 -10% 必负？

## 7. 验收标准

正确性：

- 精度 20/20 PASS；宿上位级仿真 host_sim_seg.py：命中 9 case 采样线 vs torch golden 与 vs champion 输出均 0 差异
- 含 case 11 的 245 次 Pass2 理论角点 break 被段内慢链正确接管；未命中域零影响
- 仿真发现 champion KdAccAddState 防御降级在 (mw=0, ew=-149) 且指数差>62 时钳位 -2^62 的休眠角点（测试集从未触发），新路径以零值加数跳过防护

性能：

- 形式化 ABAB 平衡交替配对（A1 B1 A2 B2，新鲜构建，5 runs/case/block）：200 对，geomean 470.7→395.3us（1.191x）
- 6 个路由 case 全 10/10 胜（1.016-3.160x）；case 11 溢出回退线 3.16x、case 18/10 1.91/1.82x、case 3/15 1.79/1.69x、case 2 1.016x
- 去路由/未路由 case 0.997-1.003 零差异噪声；case 12 0/10 at 0.978（未触碰 split 路径，二进制体积副作用）
- best_case_ratio 3.16 / worst_case_ratio 0.978

回滚信号：

- segs 下限低于净收益正域（segs=2 类配置）导致多 case 回退——本 run r1 已实证
- 段间 combine 与串行折叠不再等价（int64 结合律被破坏或 latch 语义走错分支）
- 宿上位级仿真出现段结果与 golden/champion 差异
- 未命中域出现超出噪声的回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-003（operator=cumsum_minimum, status=accepted, speedup=1.191, 470.7→395.3us, 200 对 ABAB）

## 检索卡（短卡）

动作：把 thread-per-line 的线内串行链按段切给空闲 VF 线程槽，用两遍扫描（段内扫状态加跨段精确归并）并行化。
适用：thread-per-line 且 linesPerCore<256；线内串行链为主要时延；段间状态可精确 combine。
限制：segs<4 净负，路由下限须钳 segs>=4；线槽接近 256 时不适用；段边界须以精确 int64 状态落 GM。
范围：thread-per-line 线模型的扫描/前缀类算子热路径
检索词：segSplitMode、ScanSegStateVF、ScanSegMergeVF、int64 align-min 结合律、SyncAll
机会：linesPerCore<256 时空闲 VF 线程槽即未兑现的并行度，线内串行链决定 wall
代价：两遍扫描使总计算量翻倍且 x 被双读（+50% 流量）
