---
type: Optimization
title: 归约结构重构：极值状态逐 lane 寄存器驻留 + 跨 lane 合并推迟到切片末
description: 把切片归约从逐块 Reduce+Duplicate 广播合并链改为极值状态逐 lane 寄存器驻留，跨 lane 合并推迟到切片末一次。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/per-lane-running-argmax-scan.md
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
      "运行值寄存器（runMax/runIdx/runNan）必须每 lane 跨块驻留，切片末才做一次跨 lane 合并；stat 槽布局与标量合并层须逐字不变",
      "并列语义须显式保留：lane 内严格 GT 保首现；跨 lane 用 EQ 掩码 + Select(posLarge) + ReduceMin 取最小索引",
      "NaN 轨迹须逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片的 firstIdx 不被标量层消费，行为须与原实现一致",
      "int64 与 fp 两条路径的块内指令数不同（b64 段更贵），但结构同构，应分别实现而非强行统一"
    ],
    "excluded_conditions": [
      "T2 路径不适用（本 run case10 为 T2，mte2 125.77us 主导，本机制不改 T2 且不影响其语义与性能）",
      "若归约本身很短（每核块数很少），逐块合并链的重复成本本就不显著，per-lane 化的收益不足以覆盖跨 lane 合并的固定开销",
      "若块内指令已无可合并的 Reduce/Duplicate 广播，则不存在该结构性冗余"
    ],
    "required_conditions": [
      "profiling 显示 aiv_vec 发射主导该切片归约路径（本 run：case5 [4096,8192] int64 dim=-1 T1 b64 路径 kernel 1484.281us 中 aiv_vec 1421.18us；case1 [1048576] fp16 dim=-1 T1 fp 路径单核 kernel 193.135us 中 aiv_vec 176.51us）",
      "现实现为逐块重复的合并链：每 64/32 元素块执行 ~16(b64)/~25(fp) 条向量指令，其中 2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select，逐块重复",
      "切片内可维持逐 lane 的运行极值状态（argmax/argmin 类天然满足），使跨 lane 合并可推迟到切片末一次",
      "存在与竞品实现对照的语义锚点（本 run 与 torch/triton argmax 的并列取首个、NaN 传播语义逐一对齐）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 171.675,
      "before_us": 336.119,
      "operator": "arg_max",
      "operator_class": "sort-select",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.9579,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-block-merge-chain",
      "redundant-reduce-and-broadcast",
      "vec-instruction-issue-bound"
    ],
    "pattern": "per-lane-running-reduce-scan",
    "structure": [
      "lane-resident-running-extremum",
      "deferred-cross-lane-merge",
      "strict-gt-first-occurrence-tie-break",
      "nan-track-min-scan"
    ]
  },
  "generality": "op_class",
  "id": "ARGMAX-PER-LANE-RUNNING-SCAN",
  "implementation_steps": [
    "确认瓶颈归因：统计现实现每块的指令构成（本 run ~16 条 b64 / ~25 条 fp，含 2-3 Reduce + 5-6 Duplicate 广播 + 6 Compare + 4-8 Select），确认重复合并在总指令中占主导",
    "重写切片归约 VF 的三条路径（fp / int32 / int64）：runMax/runIdx(/runNan) 每 lane 寄存器驻留；块内为 Load(+Cast) + NaN 掩码 + GT + 2×Select（int 路径 5 条/块，fp 路径 ~10 条/块），取消块级 Reduce/Duplicate 广播",
    "切片末做唯一的跨 lane 合并：ReduceMax → Duplicate → EQ 掩码 → Select(posLarge) → ReduceMin → Duplicate",
    "保持 stat 槽布局与 ComputeT1 标量合并层逐字不变，使标量层零改动",
    "逐条核对语义：lane 内严格 GT 保首现；跨 lane EQ 并列取 min(runIdx)；NaN 轨迹逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片 firstIdx 不被标量层消费",
    "T2 路径与 host/tiling 零改动"
  ],
  "intent": "把切片归约从「逐块 Reduce + Duplicate 广播 + 多路 Compare-Select」的重复合并链，改为「极值状态逐 lane 寄存器驻留、跨 lane 合并推迟到切片末一次」，把每块的合并指令全部消掉。",
  "mechanism": "argmax 切片归约的 per-lane 运行扫描重构：runMax/runIdx(/runNan) 每 lane 寄存器驻留，块内只做 Load(+Cast) + NaN 掩码 + GT + 2×Select（int 路径 5 条/块，fp 路径 ~10 条/块），替代原先每 64/32 元素块重复的 ~16(b64)/~25(fp) 条合并指令（2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select）；切片末做唯一一次跨 lane 合并（ReduceMax → Duplicate → EQ 掩码 → Select(posLarge) → ReduceMin → Duplicate）。语义靠 lane 内严格 GT 保首现 + 跨 lane EQ 并列取 min(runIdx) + NaN 逐 lane min 扫描（首个 NaN 胜出）来保持。",
  "name": "归约结构重构：极值状态逐 lane 寄存器驻留 + 跨 lane 合并推迟到切片末",
  "operator_class": "sort-select",
  "operator_scope": "切片式（slice-wise）归约类算子的 T1 路径：现实现以逐块重复的 Reduce/Duplicate 广播/多路 Compare-Select 合并链完成归约，且切片内可维持逐 lane 运行极值状态",
  "principle": "逐块归约合并链的问题在于它把「状态推进」和「跨 lane 合并」绑在一起每块做一次：每块的 Reduce 与 Duplicate 广播是为把 lane 局部结果摊到全 lane，而下一块又要重新摊开。但 argmax 这类归约的状态是可逐 lane 累进的——一旦把运行极值驻留在 lane 寄存器里，块内只需 GT + 2×Select，跨 lane 合并推迟到切片末做一次即可。收益量级由「块数 × 每块合并指令数」决定，因此块越细收益越大（本 run 每核 16384 块 × 5 条）。",
  "related_anti_patterns": [],
  "risks": [
    "并列与 NaN 语义易错：必须逐条对照原实现（严格 GT vs GE 决定首现/末现、跨 lane EQ 后取 min 索引、NaN 用 min 扫描而非 max）",
    "退化切片（全 NaN / 全 -inf / INT_MIN）的 firstIdx 虽不被标量层消费，仍需与行为一致以免后续消费方变更时静默出错",
    "三条路径（fp/int32/int64）结构同构但块内指令数不同，若强行模板化为一份代码会引入不必要的分支开销"
  ],
  "slug": "per-lane-running-argmax-scan",
  "summary": "把 argmax 切片归约从逐块重复的合并链（每 64/32 元素块 ~16(b64)/~25(fp) 条指令：2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select）重构为 per-lane 运行扫描：runMax/runIdx(/runNan) 每 lane 寄存器驻留，块内只做 Load+NaN 掩码+GT+2×Select（int 5 条 / fp ~10 条），切片末一次跨 lane 合并。case5 int64 2.843x、case1 fp16 2.644x，kernel_geomean 336.119→171.675us（×1.9579），case10（T2）不变；精度 20/20 一次通过（编译 0 修复、精度 0 修复）。",
  "verification": {
    "correctness": [
      "编译 0 修复、精度 0 修复，20/20 一次通过",
      "语义等价论证逐条覆盖：lane 内严格 GT 保首现；跨 lane EQ 并列取 min(runIdx)；NaN 轨迹逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片 firstIdx 不被标量层消费，行为一致",
      "stat 槽布局与 ComputeT1 标量合并层逐字不变（标量层零改动）"
    ],
    "performance": [
      "形式化 10 对 ABBA 平衡交替配对校验全对正向",
      "case5 [4096,8192] int64 dim=-1（T1 b64 路径）2.843x；case1 [1048576] fp16 dim=-1（T1 fp 路径，单核）2.644x",
      "kernel_geomean 336.119→171.675us（1.9579x）；case10（T2 路径，mte2 主导）不变"
    ],
    "rollback_signals": [
      "并列（EQ）或 NaN 语义与原实现不一致（须以含并列/NaN 的精度样本覆盖）",
      "跨 lane 合并推迟后切片边界状态交接错误",
      "T2 或其它未触碰路径出现回退",
      "块内指令未见下降（说明归因错误）"
    ]
  }
}
-->

# 性能优化策略：归约结构重构：极值状态逐 lane 寄存器驻留 + 跨 lane 合并推迟到切片末

把 argmax 切片归约从逐块重复的合并链（每 64/32 元素块 ~16(b64)/~25(fp) 条指令：2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select）重构为 per-lane 运行扫描：runMax/runIdx(/runNan) 每 lane 寄存器驻留，块内只做 Load+NaN 掩码+GT+2×Select（int 5 条 / fp ~10 条），切片末一次跨 lane 合并。case5 int64 2.843x、case1 fp16 2.644x，kernel_geomean 336.119→171.675us（×1.9579），case10（T2）不变；精度 20/20 一次通过。

## 1. 原理

逐块归约合并链的问题在于它把「状态推进」和「跨 lane 合并」绑在一起每块做一次：每块的 Reduce 与 Duplicate 广播是为把 lane 局部结果摊到全 lane，而下一块又要重新摊开。但 argmax 这类归约的状态是可逐 lane 累进的——一旦把运行极值驻留在 lane 寄存器里，块内只需 GT + 2×Select，跨 lane 合并推迟到切片末做一次即可。收益量级由「块数 × 每块合并指令数」决定，因此块越细收益越大（本 run 每核 16384 块 × 5 条）。

实现机制：argmax 切片归约的 per-lane 运行扫描重构：runMax/runIdx(/runNan) 每 lane 寄存器驻留，块内只做 Load(+Cast) + NaN 掩码 + GT + 2×Select（int 路径 5 条/块，fp 路径 ~10 条/块），替代原先每 64/32 元素块重复的 ~16(b64)/~25(fp) 条合并指令（2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select）；切片末做唯一一次跨 lane 合并（ReduceMax → Duplicate → EQ 掩码 → Select(posLarge) → ReduceMin → Duplicate）。语义靠 lane 内严格 GT 保首现 + 跨 lane EQ 并列取 min(runIdx) + NaN 逐 lane min 扫描（首个 NaN 胜出）来保持。

## 2. 性能问题模式

- 优化目标：把切片归约从「逐块 Reduce + Duplicate 广播 + 多路 Compare-Select」的重复合并链，改为「极值状态逐 lane 寄存器驻留、跨 lane 合并推迟到切片末一次」，把每块的合并指令全部消掉
- 适用数据流：切片式（slice-wise）归约类算子的 T1 路径：现实现以逐块重复的 Reduce/Duplicate 广播/多路 Compare-Select 合并链完成归约，且切片内可维持逐 lane 运行极值状态
- Feature signature：`{"bottleneck": ["per-block-merge-chain", "redundant-reduce-and-broadcast", "vec-instruction-issue-bound"], "pattern": "per-lane-running-reduce-scan", "structure": ["lane-resident-running-extremum", "deferred-cross-lane-merge", "strict-gt-first-occurrence-tie-break", "nan-track-min-scan"]}`

## 3. 正确性红线

- 并列与 NaN 语义易错：必须逐条对照原实现（严格 GT vs GE 决定首现/末现、跨 lane EQ 后取 min 索引、NaN 用 min 扫描而非 max）
- 退化切片（全 NaN / 全 -inf / INT_MIN）的 firstIdx 虽不被标量层消费，仍需与行为一致以免后续消费方变更时静默出错
- 三条路径（fp/int32/int64）结构同构但块内指令数不同，若强行模板化为一份代码会引入不必要的分支开销

资源与硬件约束：

- 运行值寄存器（runMax/runIdx/runNan）必须每 lane 跨块驻留，切片末才做一次跨 lane 合并；stat 槽布局与标量合并层须逐字不变
- 并列语义须显式保留：lane 内严格 GT 保首现；跨 lane 用 EQ 掩码 + Select(posLarge) + ReduceMin 取最小索引
- NaN 轨迹须逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片的 firstIdx 不被标量层消费，行为须与原实现一致
- int64 与 fp 两条路径的块内指令数不同（b64 段更贵），但结构同构，应分别实现而非强行统一

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- profiling 显示 aiv_vec 发射主导该切片归约路径（本 run：case5 [4096,8192] int64 dim=-1 T1 b64 路径 kernel 1484.281us 中 aiv_vec 1421.18us；case1 [1048576] fp16 dim=-1 T1 fp 路径单核 kernel 193.135us 中 aiv_vec 176.51us）
- 现实现为逐块重复的合并链：每 64/32 元素块执行 ~16(b64)/~25(fp) 条向量指令，其中 2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select，逐块重复
- 切片内可维持逐 lane 的运行极值状态（argmax/argmin 类天然满足），使跨 lane 合并可推迟到切片末一次
- 存在与竞品实现对照的语义锚点（本 run 与 torch/triton argmax 的并列取首个、NaN 传播语义逐一对齐）

不适用：

- T2 路径不适用（本 run case10 为 T2，mte2 125.77us 主导，本机制不改 T2 且不影响其语义与性能）
- 若归约本身很短（每核块数很少），逐块合并链的重复成本本就不显著，per-lane 化的收益不足以覆盖跨 lane 合并的固定开销
- 若块内指令已无可合并的 Reduce/Duplicate 广播，则不存在该结构性冗余

## 5. 实施步骤

1. 确认瓶颈归因：统计现实现每块的指令构成（本 run ~16 条 b64 / ~25 条 fp，含 2-3 Reduce + 5-6 Duplicate 广播 + 6 Compare + 4-8 Select），确认重复合并在总指令中占主导
2. 重写切片归约 VF 的三条路径（fp / int32 / int64）：runMax/runIdx(/runNan) 每 lane 寄存器驻留；块内为 Load(+Cast) + NaN 掩码 + GT + 2×Select（int 路径 5 条/块，fp 路径 ~10 条/块），取消块级 Reduce/Duplicate 广播
3. 切片末做唯一的跨 lane 合并：ReduceMax → Duplicate → EQ 掩码 → Select(posLarge) → ReduceMin → Duplicate
4. 保持 stat 槽布局与 ComputeT1 标量合并层逐字不变，使标量层零改动
5. 逐条核对语义：lane 内严格 GT 保首现；跨 lane EQ 并列取 min(runIdx)；NaN 轨迹逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片 firstIdx 不被标量层消费
6. T2 路径与 host/tiling 零改动

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示 aiv_vec 发射主导该切片归约路径（本 run：case5 [4096,8192] int64 dim=-1 T1 b64 路径 kernel 1484.281us 中 aiv_vec 1421.18us；case1 [1048576] fp16 dim=-1 T1 fp 路径单核 kernel 193.135us 中 aiv_vec 176.51us）？
- 目标实现是否满足：现实现为逐块重复的合并链：每 64/32 元素块执行 ~16(b64)/~25(fp) 条向量指令，其中 2-3 次 Reduce + 5-6 次 Duplicate 广播 + 6 次 Compare + 4-8 次 Select，逐块重复？
- 目标实现是否满足：切片内可维持逐 lane 的运行极值状态（argmax/argmin 类天然满足），使跨 lane 合并可推迟到切片末一次？
- 目标实现是否满足：存在与竞品实现对照的语义锚点（本 run 与 torch/triton argmax 的并列取首个、NaN 传播语义逐一对齐）？
- 是否命中排除条件：T2 路径不适用（本 run case10 为 T2，mte2 125.77us 主导，本机制不改 T2 且不影响其语义与性能）？

## 7. 验收标准

正确性：

- 编译 0 修复、精度 0 修复，20/20 一次通过
- 语义等价论证逐条覆盖：lane 内严格 GT 保首现；跨 lane EQ 并列取 min(runIdx)；NaN 轨迹逐 lane min 扫描 + 末次 ReduceMin（首个 NaN 胜出）；全 NaN / 全 -inf / INT_MIN 退化切片 firstIdx 不被标量层消费，行为一致
- stat 槽布局与 ComputeT1 标量合并层逐字不变（标量层零改动）

性能：

- 形式化 10 对 ABBA 平衡交替配对校验全对正向
- case5 [4096,8192] int64 dim=-1（T1 b64 路径）2.843x；case1 [1048576] fp16 dim=-1（T1 fp 路径，单核）2.644x
- kernel_geomean 336.119→171.675us（1.9579x）；case10（T2 路径，mte2 主导）不变

回滚信号：

- 并列（EQ）或 NaN 语义与原实现不一致（须以含并列/NaN 的精度样本覆盖）
- 跨 lane 合并推迟后切片边界状态交接错误
- T2 或其它未触碰路径出现回退
- 块内指令未见下降（说明归因错误）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260907_170122-free-001（operator=arg_max, mechanism=per-lane-running-argmax-scan, status=accepted, speedup=1.9579, 336.119→171.675us, 10 对 ABBA）

## 检索卡（短卡）

动作：把切片归约从逐块 Reduce+Duplicate 广播合并链改为极值状态逐 lane 寄存器驻留，跨 lane 合并推迟到切片末一次。
适用：aiv_vec 发射主导切片归约路径、现实现为逐块重复合并链（每块 ~16(b64)/~25(fp) 条向量指令）。
限制：lane 内严格 GT 保首现、跨 lane 用 EQ 掩码取最小索引；NaN 须逐 lane min 扫描；stat 槽布局须逐字不变。
范围：sort-select 切片式归约算子的 T1 路径。
检索词：runMax、runIdx、runNan、ReduceMax、ReduceMin、Duplicate、Select(posLarge)
机会：逐块把 lane 局部结果摊到全 lane、下一块又重新摊开，每核 16384 块重复合并。
代价：T2 与短归约不适用：收益不足以覆盖跨 lane 合并的固定开销。
