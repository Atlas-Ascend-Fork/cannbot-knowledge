---
type: Optimization
title: 均衡余数行划分：把 tokens%blockDim 余数按 +1 行摊到前 rem 个核，替代尾核全量堆余
description: 把 tokens%blockDim 余数从堆给尾核改为按 +1 行摊到前 rem 个核，删失效尾核特判。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/balanced-remainder-row-partition.md
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
      "仅整数 mul/add/min/cmp；coreIdx、base 的乘积必须在 kernel 整数域安全",
      "host 侧按旧尾核行数推导的批参数（如 rowsPerTile）不重键到均衡划分时，必须确认功能惰性（尾裁剪覆盖、缓冲尺寸不变）——刻意最小 diff 边界，重做 R 时需 revisit",
      "均衡后全核并发 MTE2 突发受聚合带宽争用约束，收益按争用封顶而非理论上限；Init/launch 地板限制小 shape 收益上限"
    ],
    "excluded_conditions": [
      "tokens 整除 blockDim（rem==0）：划分逐字节不变，机制为 no-op",
      "并行度不足（存在根本未发射的核）：那是唤醒空闲核/次轴二次切分的问题，不是余数偏斜；本机制要求全部核已发射且 blockDim 不变",
      "下游存在假设尾核特殊的代码路径（本 kernel 的尾 tile 裁剪对 base/base+1 核通用，无尾核假设，故安全）"
    ],
    "required_conditions": [
      "余数偏斜存在：tokens % blockDim != 0，且 baseline 划分把余数堆给单一尾核",
      "每核行区间连续性保持：start = c*base + min(c,rem) 与 count = base + (c<rem) 产生的区间连续不重叠，下游按 myTokenStart_+rowBase 寻址即可",
      "rem 可由既有 TilingData 字段在 kernel 内推导（tokensNum/perCoreTokens/blockDim），不需要新字段或 host 改动",
      "瓶颈归属用 wall 算术确认：device 时长 ≈ 尾核行数 × 同 H/dtype 整除 sibling 标定的每行成本（op_summary 按 op 聚合无法直接显示 per-core 偏斜，需跨 dtype 交叉验证）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-01",
  "evidence": [
    {
      "comparison_sha256": "fcc5c0c088dd617a502b729974a18fe21ee7e7ac7db7c69083f2a71999bb3395",
      "decision_sha256": "7e7b47a0bfd510585b32ed06297df185d1b9fb60266106d9aaf6e5ac56dac1d8",
      "operator_class": "fused-composite",
      "performance_sha256": "4bbd96e107b3d2fc05f96f159042a3b813d8b81fd04c9193c26d48b01a84bb8e",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "6b5fa477e490e2114e03a55b6db871684ec941d49d677d9334e02d363c726ceb",
      "verify_sha256": "c9491e4b548de44eb4291bd27244b322675746be09e4f19b852e6557fb637ebe"
    },
    {
      "comparison_sha256": "c4a778cdfb7bffd3fcdd73b8b41ee495bcc67f60514c1fe570e1ad893a6e693d",
      "decision_sha256": "ec0261ba9a589152db6522d5c4c8712cf6b038f71085a92085a81b746a7aa00c",
      "operator_class": "fused-composite",
      "performance_sha256": "5620b0f3494f09f2e3ceb098afd1035f652ba4d34ffe4ef95b22cdc2ea4a1ff3",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "fdf2c50e7bf99325660e70fabb91d11e19e0bd4e2897f9f297d2cca89e2cd1a8",
      "verify_sha256": "d9ef9b5a9fe6b1cdd227201e1d622bbac2b37f6c9ed5fc23d5284c7d44aa118e"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-load-skew",
      "remainder-tail-dump"
    ],
    "dtypes": [
      "int32",
      "fp16",
      "bf16"
    ],
    "pattern": "balanced-remainder-row-partition",
    "structure": [
      "kernel-init-index-arithmetic",
      "contiguous-row-intervals",
      "fixed-blockdim"
    ]
  },
  "generality": "op_class",
  "id": "DSQ-R2-BALANCED-REMAINDER-ROW-PARTITION",
  "implementation_steps": [
    "用 op_summary wall 算术确认偏斜（时长 ≈ 尾核行数 × sibling 标定每行成本，跨 dtype 交叉验证），并预注册证伪信号（偏斜 case 未降到 >=2x 即假设证伪）",
    "kernel Init 把尾核堆余替换为均衡摊余（两行索引算术），删除失效尾核成员",
    "确认整除 case 划分逐字节一致（作为 control）且 Block Num 不变",
    "全量 correctness（共享 Init 路径，范围 all_cases）+ target/control measure；官方路径 spot_check 复核最大收益 case"
  ],
  "intent": "消除 tokens%blockDim != 0 时余数全部堆给尾核造成的核间负载偏斜：wall 由尾核串行行数决定而非流水吞吐。",
  "mechanism": "kernel Init 仅改每核行块派生：rem = tokensNum − perCoreTokens*blockDim（∈[0, blockDim)），myTokenStart_ = coreIdx*tokenStart_ + min(coreIdx, rem)，myCoreTokens_ = perCoreTokens_ + (coreIdx < rem ? 1 : 0)；删除失效的尾核特判成员。无 host tiling、无 TilingData/tiling key、无拷贝描述符、无 VF 体改动；新代码仅 mul/add/min/cmp（无除法），乘积在 kernel 整数域安全（coreIdx<64、base<=tokens 上界下 <2^21 uint32）。",
  "name": "均衡余数行划分：把 tokens%blockDim 余数按 +1 行摊到前 rem 个核，替代尾核全量堆余",
  "op": "dequant_swiglu_quant",
  "operator_class": "fused-composite",
  "operator_scope": "host 按行轴分核（blockDim = min(coreNum, tokensNum)、每核连续行区间）的行式数据流；kernel Init 从既有 TilingData 字段派生 per-core 行块，tokens 不能被 blockDim 整除时存在余数偏斜",
  "principle": "全部核已发射时，wall = 最忙核的串行行数；余数堆尾使最忙核持有 base+rem 行而其它核只有 base 行。把余数按 +1 行摊到前 rem 个核后每核行数差至多 1，最忙核降为 ceil(tokens/blockDim)。rem==0（整除）时 min(coreIdx,0)==0、尾核计数==base，划分与旧代码逐字节相同，因此整除 case 是天然零影响 control；摊余后的区间保持连续，所有下游（批拷贝描述符、逐行路径、workspace）无需感知。",
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "根因由 wall 算术推断而非 per-core profiling：必须预注册证伪信号并按其裁决",
    "均衡后聚合带宽需求上升可能使收益显著低于理论（中央估计按争用封顶）",
    "sub-10us case 处于微核噪声地板：control 按绝对抖动与 same-state scatter 判定，不单独按相对门禁"
  ],
  "slug": "balanced-remainder-row-partition",
  "summary": "当 host tiling 给前 blockDim-1 个核各 base=tokens/blockDim 行、把全部余数行堆给尾核时，wall 等于尾核的串行行数（核间负载偏斜，op_summary 按 op 聚合不可见）；在 kernel Init 用纯整数运算把余数摊开——前 rem 个核各 base+1 行、其余 base 行——使最忙核降到 ceil(tokens/blockDim) 行；rem==0 时与原划分逐字节一致，整除 case 天然零影响 control。",
  "verification": {
    "correctness": [
      "rounds/002 verify 20/20 通过（all_cases，kernel d31481a2d3fb0d5e）；改动为共享 Init 路径的纯索引算术，行区间错误会整行错位并立即失败精度门禁",
      "整除 control 聚合 1.0055x 佐证划分逐字节一致；Block Num 全程 64"
    ],
    "performance": [
      "incremental total_speedup 1.8417x（2243.5→1218.2us/step；target 8 case 合计 2.9491x，regressed 0）；最大 case 16 7.78x、case 8 6.91x、case 15 3.35x、case 7 3.34x、case 5 3.01x、case 13 2.90x",
      "cumulative vs baseline 2.4087x；spot_check case 16 官方路径复现（9.03 vs 9.04us，ratio 0.999）",
      "边界：control case 2 incremental 0.9548x（绝对 +0.573us/inv 略高于 ~0.5us/inv 抖动地板；其 cumulative 漂移始于 r1，非本机制回归，判定记录于 rounds/002/decision.json）"
    ],
    "rollback_signals": [
      "整除 control 中位数 <0.95x（划分应逐字节一致）或任一 correctness 失败",
      "偏斜 target case 未降到 >=2x（尾核墙假设证伪，回退并重排策略）",
      "意外 device error（区间越界 bug，非机制边界）"
    ]
  }
}
-->

# 性能优化策略：均衡余数行划分：把 tokens%blockDim 余数按 +1 行摊到前 rem 个核，替代尾核全量堆余

单一优化点：当 host tiling 给前 blockDim-1 个核各 base=tokens/blockDim 行、把全部余数行堆给尾核时，wall 等于尾核的串行行数（核间负载偏斜，op_summary 按 op 聚合不可见）；在 kernel Init 用纯整数运算把余数摊开——前 rem 个核各 base+1 行、其余 base 行——使最忙核降到 ceil(tokens/blockDim) 行；rem==0 时与原划分逐字节一致，整除 case 天然零影响 control。

## 1. 原理

全部核已发射时，wall = 最忙核的串行行数；余数堆尾使最忙核持有 base+rem 行而其它核只有 base 行。把余数按 +1 行摊到前 rem 个核后每核行数差至多 1，最忙核降为 ceil(tokens/blockDim)。rem==0（整除）时 min(coreIdx,0)==0、尾核计数==base，划分与旧代码逐字节相同，因此整除 case 是天然零影响 control；摊余后的区间保持连续，所有下游（批拷贝描述符、逐行路径、workspace）无需感知。

实现机制：kernel Init 仅改每核行块派生：rem = tokensNum − perCoreTokens*blockDim（∈[0, blockDim)），myTokenStart_ = coreIdx*tokenStart_ + min(coreIdx, rem)，myCoreTokens_ = perCoreTokens_ + (coreIdx < rem ? 1 : 0)；删除失效的尾核特判成员。无 host tiling、无 TilingData/tiling key、无拷贝描述符、无 VF 体改动；新代码仅 mul/add/min/cmp（无除法），乘积在 kernel 整数域安全（coreIdx<64、base<=tokens 上界下 <2^21 uint32）。

## 2. 性能问题模式

- 优化目标：消除 tokens%blockDim != 0 时余数全部堆给尾核造成的核间负载偏斜：wall 由尾核串行行数决定而非流水吞吐。
- 适用数据流：host 按行轴分核（blockDim = min(coreNum, tokensNum)、每核连续行区间）的行式数据流；kernel Init 从既有 TilingData 字段派生 per-core 行块，tokens 不能被 blockDim 整除时存在余数偏斜
- Feature signature：`{"bottleneck": ["core-load-skew", "remainder-tail-dump"], "dtypes": ["int32", "fp16", "bf16"], "pattern": "balanced-remainder-row-partition", "structure": ["kernel-init-index-arithmetic", "contiguous-row-intervals", "fixed-blockdim"]}`

## 3. 正确性红线

- 根因由 wall 算术推断而非 per-core profiling：必须预注册证伪信号并按其裁决
- 均衡后聚合带宽需求上升可能使收益显著低于理论（中央估计按争用封顶）
- sub-10us case 处于微核噪声地板：control 按绝对抖动与 same-state scatter 判定，不单独按相对门禁

资源与硬件约束：

- 仅整数 mul/add/min/cmp；coreIdx、base 的乘积必须在 kernel 整数域安全
- host 侧按旧尾核行数推导的批参数（如 rowsPerTile）不重键到均衡划分时，必须确认功能惰性（尾裁剪覆盖、缓冲尺寸不变）——刻意最小 diff 边界，重做 R 时需 revisit
- 均衡后全核并发 MTE2 突发受聚合带宽争用约束，收益按争用封顶而非理论上限；Init/launch 地板限制小 shape 收益上限

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 余数偏斜存在：tokens % blockDim != 0，且 baseline 划分把余数堆给单一尾核
- 每核行区间连续性保持：start = c*base + min(c,rem) 与 count = base + (c<rem) 产生的区间连续不重叠，下游按 myTokenStart_+rowBase 寻址即可
- rem 可由既有 TilingData 字段在 kernel 内推导（tokensNum/perCoreTokens/blockDim），不需要新字段或 host 改动
- 瓶颈归属用 wall 算术确认：device 时长 ≈ 尾核行数 × 同 H/dtype 整除 sibling 标定的每行成本（op_summary 按 op 聚合无法直接显示 per-core 偏斜，需跨 dtype 交叉验证）

不适用：

- tokens 整除 blockDim（rem==0）：划分逐字节不变，机制为 no-op
- 并行度不足（存在根本未发射的核）：那是唤醒空闲核/次轴二次切分的问题，不是余数偏斜；本机制要求全部核已发射且 blockDim 不变
- 下游存在假设尾核特殊的代码路径（本 kernel 的尾 tile 裁剪对 base/base+1 核通用，无尾核假设，故安全）

## 5. 实施步骤

1. 用 op_summary wall 算术确认偏斜（时长 ≈ 尾核行数 × sibling 标定每行成本，跨 dtype 交叉验证），并预注册证伪信号（偏斜 case 未降到 >=2x 即假设证伪）
2. kernel Init 把尾核堆余替换为均衡摊余（两行索引算术），删除失效尾核成员
3. 确认整除 case 划分逐字节一致（作为 control）且 Block Num 不变
4. 全量 correctness（共享 Init 路径，范围 all_cases）+ target/control measure；官方路径 spot_check 复核最大收益 case

## 6. LLM 前置问题

- 目标实现是否满足：余数偏斜存在：tokens % blockDim != 0，且 baseline 划分把余数堆给单一尾核？
- 目标实现是否满足：每核行区间连续性保持：start = c*base + min(c,rem) 与 count = base + (c<rem) 产生的区间连续不重叠，下游按 myTokenStart_+rowBase 寻址即可？
- 目标实现是否满足：rem 可由既有 TilingData 字段在 kernel 内推导（tokensNum/perCoreTokens/blockDim），不需要新字段或 host 改动？
- 是否命中排除条件：tokens 整除 blockDim（rem==0）：划分逐字节不变，机制为 no-op？

## 7. 验收标准

正确性：

- rounds/002 verify 20/20 通过（all_cases，kernel d31481a2d3fb0d5e）；改动为共享 Init 路径的纯索引算术，行区间错误会整行错位并立即失败精度门禁
- 整除 control 聚合 1.0055x 佐证划分逐字节一致；Block Num 全程 64

性能：

- incremental total_speedup 1.8417x（2243.5→1218.2us/step；target 8 case 合计 2.9491x，regressed 0）；最大 case 16 7.78x、case 8 6.91x、case 15 3.35x、case 7 3.34x、case 5 3.01x、case 13 2.90x
- cumulative vs baseline 2.4087x；spot_check case 16 官方路径复现（9.03 vs 9.04us，ratio 0.999）
- 边界：control case 2 incremental 0.9548x（绝对 +0.573us/inv 略高于 ~0.5us/inv 抖动地板；其 cumulative 漂移始于 r1，非本机制回归，判定记录于 rounds/002/decision.json）

回滚信号：

- 整除 control 中位数 <0.95x（划分应逐字节一致）或任一 correctness 失败
- 偏斜 target case 未降到 >=2x（尾核墙假设证伪，回退并重排策略）
- 意外 device error（区间越界 bug，非机制边界）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：tile-ub-budget-mismatch

- dequant_swiglu_quant-20260831_113139-0cf99e（round=2, status=accepted）
- moe_finalize_routing-20260902_124740-ebd397（round=1, status=accepted）

## 检索卡（短卡）

动作：把 tokens%blockDim 余数从堆给尾核改为按 +1 行摊到前 rem 个核，删失效尾核特判
适用：host 按行轴分核、每核连续行区间，rem 可由既有 TilingData 字段在 kernel 内推导
限制：仅整数 mul/add/min/cmp 且乘积在 kernel 整数域安全；rem==0 时划分须与旧码逐字节相同
范围：fused-composite 行式数据流的 kernel Init 每核行块派生
检索词：均衡余数、myTokenStart_、perCoreTokens、min(coreIdx,rem)、blockDim
机会：wall 由尾核串行行数决定而非流水吞吐，op_summary 聚合看不到 per-core 偏斜
代价：全核并发 MTE2 突发受聚合带宽争用，收益按争用封顶
