---
type: Optimization
title: T2 跨步扫描核心的 int32 argmin carry 表示 + laneChunkW 32->64 解封（numLaneChunks 减半、MTE 块宽翻倍）
description: 把 T2 VF 核心的 runningArgmin/idxCand 改为 int32 表示，解封 laneChunkW 32->64，出口逐行 Cast 加宽回 int64。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/int32-carry-64lane-scan-core.md
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
      "host tiling 改动在 isolated install 下必须经 opp overlay 生效（runtime 按绝对路径加载 tiling 库），rebuild 后须刷新 overlay，否则静默按陈旧 tiling 显示约 1.0x",
      "tile 公式按 idx32 单缓冲计数并留安全 headroom；首版无 headroom 的 tile 公式曾把目标 case 推入回归",
      "dtype/lanePerCore 门控留在 host 单常量处，回退等价于还原封顶值"
    ],
    "excluded_conditions": [
      "fp32/int64 值 dtype：UB tile 行数减半 + 每 chunk 固定开销（PIPE_ALL + Cast）主导使其回归，留在旧核心；int64 另有 b64 掩码无法降粒度的表示障碍",
      "lanePerCore <= 32 的窄 lane 任务（无宽度增益）",
      "沿扫描轴的行数本已很少、(chunk,tile) 轮固定开销权重高的任务"
    ],
    "required_conditions": [
      "T2 模式（dimNorm != rank-1）VF 核心且 argmin 值域 int32 可承载（扫描轴长度 < 2^31）",
      "值 dtype 为 2B（fp16/bf16）：64 lane 的值行宽仍能维持 UB tile 行数（4B 值 dtype 的行宽翻倍会把 UB tile 行数减半，per-chunk 固定开销占比升高而回归）",
      "lanePerCore > 32（存在宽度增益；窄 lane 任务无增益只付 Cast 与轮数开销）",
      "host ubScanTile 预算显式计入 idx32 单缓冲并留 headroom（tile 收缩会直接反噬为回归）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "T2 目标子集（level2/cummin_14/17/10/5）",
      "note": "correctness 20/20；kernel_details：case14 墙钟 797.9->527.9us（mte2+mte3 566->312us、scalar 260.5->198.9us），机制预测被证实。门控边界：fp32 case19 probe 0.781x（64-lane 值行宽使 UB tile 128->64 行、per-core 固定开销主导）与 int64（b64 掩码不可降粒度）回旧核后恢复 1.0x；lanePerCore<=32（wc=16）门控保护。首测 tile 公式曾致 case5 0.9409x，补 idx32 headroom 后复测 1.0149x。host tiling 经 opp symlink-farm overlay 生效（isolated install 下 runtime 按绝对路径加载 tiling 库，rebuild 后必须刷新）。",
      "operator_class": "reduction",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "case14 1.5117x、case17 1.2162x、case10 1.1884x、case5 1.0149x（idx-widen 双写 UB 带宽封顶）；incremental 1.0399x、cumulative 1.2483x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "7da941bdea21e0513bdc96b2d9ac2cde54337e6277e00bda74172d40a78b0f30",
      "decision_sha256": "529777c7ece2cd84fa79bdfc3b88e5fbb7de767ea29d40f8eca43da19e4a2bfd",
      "operator_class": "reduction",
      "performance_sha256": "b6a7a47a62a8ba89f8dd7946c11aeced2bfaba7ff11b260e4d144f60ba6f626b",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ee336f3674c2ec20be92ec86413eaf8222ecb0821155a7e0b6559b2bb6c8b246",
      "verify_sha256": "44c8b7f5481b880b96e0f1577f217afcaadf19e47e65a5d36c7f9edfb6a89c0c"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "lane-width-cap",
      "int64-carry-register-overhead",
      "mte-transaction-count"
    ],
    "pattern": "int32-carry-64lane-core-widen",
    "structure": [
      "t2-strided-mid-axis-scan",
      "int32-argmin-carry",
      "lanechunkw-32-to-64",
      "idx32-tile-resident",
      "copyout-cast-widen",
      "dtype-and-lane-gated"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-INT32-CARRY-64LANE-CORE",
  "implementation_steps": [
    "复制旧 VF 核心为 int32-carry 变体：runningArgmin/idxCand 改 int32、掩码 UpgradeMaskToB32、idx 行 StoreAlign 到 idx32 tile；旧核心整段保留",
    "Process 按 laneChunkW_>32 分派新旧核心；Init 增加 idx32Buf_ 与 slotBytesIdx32_ 推导",
    "host DoTilingT2 把 laneChunkW 封顶 32->64，门控条件 dtypeSize<4 且 lanePerCore>32；ubScanTile 分母加 idx32 项并留 headroom",
    "CopyOut 前逐行 Cast(int32->int64) 加宽（复用行并路径已验证管线），idx 描述符形态不变",
    "probe 逐 case 验证（含全 NaN 值域的 NaN 粘性与 bf16 窄尾），对回归 case 先做 tile 公式/门控修正再复测；全量 verify + T1 control 字节级不动"
  ],
  "intent": "消除 T2 跨步扫描核心的 laneChunkW=32 硬封顶与 int64 carry 寄存器开销：carry 用 int64 表示使单 lane 占用翻倍，lane 宽度被封在 32，numLaneChunks 与 MTE 事务数翻倍。",
  "mechanism": "kernel 新增 int32-carry VF 核心（ComputePrefixMinCarryVF32RegImpl + wrapper，骨架复制旧核心，差异仅 runningArgmin/idxCand 为 int32、掩码升级 UpgradeMaskToB32、idx 行 StoreAlign 到 idx32 tile），旧 int64 核心整段保留，Process 按 laneChunkW_>32 分派；Init 增加 idx32Buf_ TBuf 与 slotBytesIdx32_ 推导；host DoTilingT2 把 laneChunkW 封顶 32->64（dtypeSize<4 且 lanePerCore>32 才放开），ubScanTile 分母加 idx32 单缓冲项并留 headroom；CopyOutStrided idx 描述符形态不变。",
  "name": "T2 跨步扫描核心的 int32 argmin carry 表示 + laneChunkW 32->64 解封（numLaneChunks 减半、MTE 块宽翻倍）",
  "operator_class": "reduction",
  "operator_scope": "跨 stride 中轴扫描（dimNorm != rank-1，T2 路径）的 VF 核心：running min/argmin 以寄存器 carry 沿扫描轴推进、每 (trajectory, laneChunk) 任务独立；argmin 值域可由 int32 承载（扫描轴长度 < 2^31）",
  "principle": "argmin 索引的值域由扫描轴长度决定，int32 通常足以承载；把 carry 表示从 int64 收窄到 int32 后，同一寄存器预算可承载 2 倍 lane（laneChunkW 32->64），每个任务的 lane 块数减半——沿扫描轴的 Gather/Scatter 微码 step 数近似减半，MTE 搬运块宽翻倍（描述符与同步开销同步减半）。符号/宽度语义在出口恢复：idx 以 int32 驻留工作 tile，CopyOut 前逐行 Cast 加宽 int64（与行并路径已验证的同一套管线）。",
  "related_anti_patterns": [],
  "risks": [
    "tile 公式遗漏 idx32 缓冲项或 headroom 不足导致目标 case 回归（表现为目标 route 内个别 case 低于 1.0x）",
    "4B 值 dtype 误放开 64 lane：UB tile 行数减半 + 每 chunk PIPE_ALL/Cast 固定开销主导而回归，probe 必须覆盖该 dtype 再决定门控",
    "窄 lane 任务（lanePerCore<=32）无增益只付 Cast 与轮数开销",
    "host tiling 改动经 isolated install 静默失效（opp overlay 未刷新），测量显示约 1.0x 而非机制回归——先核对 overlay 再归因机制"
  ],
  "slug": "int32-carry-64lane-scan-core",
  "summary": "把 T2 VF 核心的 runningArgmin/idxCand 从 int64 改为 int32 表示，寄存器压力下降后解除 laneChunkW=32 硬封顶到 64 lane：每任务的 lane 块数减半、MTE 搬运块宽翻倍，Gather/Scatter 微码 step 数与 MTE 描述符开销同时近似减半；int64 语义在出口恢复（idx 走 int32 工作 tile，CopyOut 前逐行 Cast 加宽）；host tiling 的 ubScanTile 分母补 idx32 项，dtype/lanePerCore 双门控保护不获益 shape。",
  "verification": {
    "correctness": [
      "全量 all_cases verify 通过（含全 NaN 值域的 NaN 粘性、int32 符号域、窄尾 chunk）",
      "T1 路径与门控回退 case 字节级不动/恢复约 1.0x",
      "idx 加宽后 int64 值与 argmin 精确（符号扩展位等价）"
    ],
    "performance": [
      "incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升",
      "kernel_details 级机制归因：MTE2+MTE3 绝对时长下降与 lane 块数减半一致",
      "门控回退 case 恢复 parent 行为"
    ],
    "rollback_signals": [
      "任一精度失败或目标 route 内 case 回归（先查 tile 公式与门控，再查 opp overlay 新鲜度）",
      "4B dtype/窄 lane case 回归超阈值（门控条件泄漏）",
      "机制收益远低于按 lane 块数减半折算的预期时重新评估固定开销权重"
    ]
  }
}
-->

# 性能优化策略：T2 跨步扫描核心的 int32 argmin carry 表示 + laneChunkW 32->64 解封（numLaneChunks 减半、MTE 块宽翻倍）

单一优化点：把 T2 VF 核心的 runningArgmin/idxCand 从 int64 改为 int32 表示，寄存器压力下降后解除 laneChunkW=32 硬封顶到 64 lane：每任务的 lane 块数减半、MTE 搬运块宽翻倍，Gather/Scatter 微码 step 数与 MTE 描述符开销同时近似减半；int64 语义在出口恢复（idx 走 int32 工作 tile，CopyOut 前逐行 Cast 加宽）；host tiling 的 ubScanTile 分母补 idx32 项，dtype/lanePerCore 双门控保护不获益 shape。

## 1. 原理

argmin 索引的值域由扫描轴长度决定，int32 通常足以承载；把 carry 表示从 int64 收窄到 int32 后，同一寄存器预算可承载 2 倍 lane（laneChunkW 32->64），每个任务的 lane 块数减半——沿扫描轴的 Gather/Scatter 微码 step 数近似减半，MTE 搬运块宽翻倍（描述符与同步开销同步减半）。符号/宽度语义在出口恢复：idx 以 int32 驻留工作 tile，CopyOut 前逐行 Cast 加宽 int64（与行并路径已验证的同一套管线）。

实现机制：kernel 新增 int32-carry VF 核心（ComputePrefixMinCarryVF32RegImpl + wrapper，骨架复制旧核心，差异仅 runningArgmin/idxCand 为 int32、掩码升级 UpgradeMaskToB32、idx 行 StoreAlign 到 idx32 tile），旧 int64 核心整段保留，Process 按 laneChunkW_>32 分派；Init 增加 idx32Buf_ TBuf 与 slotBytesIdx32_ 推导；host DoTilingT2 把 laneChunkW 封顶 32->64（dtypeSize<4 且 lanePerCore>32 才放开），ubScanTile 分母加 idx32 单缓冲项并留 headroom；CopyOutStrided idx 描述符形态不变。

## 2. 性能问题模式

- 优化目标：消除 T2 跨步扫描核心的 laneChunkW=32 硬封顶与 int64 carry 寄存器开销：carry 用 int64 表示使单 lane 占用翻倍，lane 宽度被封在 32，numLaneChunks 与 MTE 事务数翻倍。
- 适用数据流：跨 stride 中轴扫描（dimNorm != rank-1，T2 路径）的 VF 核心：running min/argmin 以寄存器 carry 沿扫描轴推进、每 (trajectory, laneChunk) 任务独立；argmin 值域可由 int32 承载（扫描轴长度 < 2^31）
- Feature signature：`{"bottleneck": ["lane-width-cap", "int64-carry-register-overhead", "mte-transaction-count"], "pattern": "int32-carry-64lane-core-widen", "structure": ["t2-strided-mid-axis-scan", "int32-argmin-carry", "lanechunkw-32-to-64", "idx32-tile-resident", "copyout-cast-widen", "dtype-and-lane-gated"]}`

## 3. 正确性红线

- tile 公式遗漏 idx32 缓冲项或 headroom 不足导致目标 case 回归（表现为目标 route 内个别 case 低于 1.0x）
- 4B 值 dtype 误放开 64 lane：UB tile 行数减半 + 每 chunk PIPE_ALL/Cast 固定开销主导而回归，probe 必须覆盖该 dtype 再决定门控
- 窄 lane 任务（lanePerCore<=32）无增益只付 Cast 与轮数开销
- host tiling 改动经 isolated install 静默失效（opp overlay 未刷新），测量显示约 1.0x 而非机制回归——先核对 overlay 再归因机制

资源与硬件约束：

- host tiling 改动在 isolated install 下必须经 opp overlay 生效（runtime 按绝对路径加载 tiling 库），rebuild 后须刷新 overlay，否则静默按陈旧 tiling 显示约 1.0x
- tile 公式按 idx32 单缓冲计数并留安全 headroom；首版无 headroom 的 tile 公式曾把目标 case 推入回归
- dtype/lanePerCore 门控留在 host 单常量处，回退等价于还原封顶值

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- T2 模式（dimNorm != rank-1）VF 核心且 argmin 值域 int32 可承载（扫描轴长度 < 2^31）
- 值 dtype 为 2B（fp16/bf16）：64 lane 的值行宽仍能维持 UB tile 行数（4B 值 dtype 的行宽翻倍会把 UB tile 行数减半，per-chunk 固定开销占比升高而回归）
- lanePerCore > 32（存在宽度增益；窄 lane 任务无增益只付 Cast 与轮数开销）
- host ubScanTile 预算显式计入 idx32 单缓冲并留 headroom（tile 收缩会直接反噬为回归）

不适用：

- fp32/int64 值 dtype：UB tile 行数减半 + 每 chunk 固定开销（PIPE_ALL + Cast）主导使其回归，留在旧核心；int64 另有 b64 掩码无法降粒度的表示障碍
- lanePerCore <= 32 的窄 lane 任务（无宽度增益）
- 沿扫描轴的行数本已很少、(chunk,tile) 轮固定开销权重高的任务

## 5. 实施步骤

1. 复制旧 VF 核心为 int32-carry 变体：runningArgmin/idxCand 改 int32、掩码 UpgradeMaskToB32、idx 行 StoreAlign 到 idx32 tile；旧核心整段保留
2. Process 按 laneChunkW_>32 分派新旧核心；Init 增加 idx32Buf_ 与 slotBytesIdx32_ 推导
3. host DoTilingT2 把 laneChunkW 封顶 32->64，门控条件 dtypeSize<4 且 lanePerCore>32；ubScanTile 分母加 idx32 项并留 headroom
4. CopyOut 前逐行 Cast(int32->int64) 加宽（复用行并路径已验证管线），idx 描述符形态不变
5. probe 逐 case 验证（含全 NaN 值域的 NaN 粘性与 bf16 窄尾），对回归 case 先做 tile 公式/门控修正再复测；全量 verify + T1 control 字节级不动

## 6. LLM 前置问题

- 目标实现是否满足：T2 模式（dimNorm != rank-1）VF 核心且 argmin 值域 int32 可承载（扫描轴长度 < 2^31）？
- 目标实现是否满足：值 dtype 为 2B（fp16/bf16）：64 lane 的值行宽仍能维持 UB tile 行数（4B 值 dtype 的行宽翻倍会把 UB tile 行数减半，per-chunk 固定开销占比升高而回归）？
- 目标实现是否满足：lanePerCore > 32（存在宽度增益；窄 lane 任务无增益只付 Cast 与轮数开销）？
- 是否命中排除条件：fp32/int64 值 dtype：UB tile 行数减半 + 每 chunk 固定开销（PIPE_ALL + Cast）主导使其回归，留在旧核心；int64 另有 b64 掩码无法降粒度的表示障碍？

## 7. 验收标准

正确性：

- 全量 all_cases verify 通过（含全 NaN 值域的 NaN 粘性、int32 符号域、窄尾 chunk）
- T1 路径与门控回退 case 字节级不动/恢复约 1.0x
- idx 加宽后 int64 值与 argmin 精确（符号扩展位等价）

性能：

- incremental total_speedup 达任务阈值且无 case 低于 max_case_regression；目标 route 子集聚合提升
- kernel_details 级机制归因：MTE2+MTE3 绝对时长下降与 lane 块数减半一致
- 门控回退 case 恢复 parent 行为

回滚信号：

- 任一精度失败或目标 route 内 case 回归（先查 tile 公式与门控，再查 opp overlay 新鲜度）
- 4B dtype/窄 lane case 回归超阈值（门控条件泄漏）
- 机制收益远低于按 lane 块数减半折算的预期时重新评估固定开销权重

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260831_113913-196633（round=3, status=accepted, case=T2 目标子集（level2/cummin_14/17/10/5）, speedup=case14 1.5117x、case17 1.2162x、case10 1.1884x、case5 1.0149x（idx-widen 双写 UB 带宽封顶）；incremental 1.0399x、cumulative 1.2483x）
- cummin-20260831_113913-196633（round=3, status=accepted）

## 检索卡（短卡）

动作：把 T2 VF 核心的 runningArgmin/idxCand 改为 int32 表示，解封 laneChunkW 32->64，出口逐行 Cast 加宽回 int64。
适用：T2（dimNorm!=rank-1）VF 核心、扫描轴长 < 2^31、值 dtype 2B、lanePerCore > 32。
限制：4B 值 dtype 误放开 64 lane 会因 UB tile 行数减半而回归；tile 公式须计入 idx32 单缓冲。
范围：reduction 跨 stride 中轴扫描（T2）的 VF 核心。
检索词：laneChunkW、runningArgmin、UpgradeMaskToB32、CopyOutStrided、ubScanTile、MTE 块宽
机会：carry 以 int64 表示使单 lane 占用翻倍、lane 宽被封 32，MTE 事务数翻倍。
