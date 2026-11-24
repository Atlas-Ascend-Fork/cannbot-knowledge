---
type: Optimization
title: 2D 行对合并搬运在 MTE2 带宽饱和满核场景的负向边界
description: 先检查MTE2带宽饱和与关键路径，再比较h0/h1两次DataCopyPad合并为2D行对搬运是否减少实际工作。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/2d-rowpair-datacopy-mte2-saturation-boundary.md
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
      "硬件边界：结论采集自 ascend950（Ascend950DT, 64 AIV 核）；其他芯片需重新验证满核带宽饱和点",
      "路由边界：负向结论主要约束 R1-buffer-mode1-ow-blocked 路由（高描述符密度场景），R0-buffer-mode0-whole-row 路由描述符密度低，case15 R0 路径 1.001x 同样无收益",
      "正反边界：case2（R1, 16核, 131.9->113.0us=1.167x）证明机制在低核数/高描述符密度/小数据量场景有效；case12/15（64核 MTE2-bound）证明机制在满核带宽饱和场景无效。收益不可跨场景外推。",
      "与 S4（strategies/common/2d-bulk-data-copy.md）的关系：S4 是同一机制的正向 validated_strategy（scatter-update, 1.0-1.3x），本条目是同一机制在 index-gather 满核 MTE2-bound 场景的负向边界。S4 risks 已预警'只减少描述符而未减少等待或队列往返时收益可能被其他固定开销限制'，本条目是该预警的实测确认。"
    ],
    "excluded_conditions": [
      "N*C >= 64 满核 MTE2 带宽饱和场景（case12 2048-wide 64核、case15 127-plane 64核）：已实测证伪，描述符发射开销被带宽延迟掩盖，减半描述符无墙钟收益",
      "MTE2 时间由数据量主导而非描述符密度主导的 case：不可从描述符密度假设推导收益",
      "h0 == h1 时不可合并（srcStride=0 导致两次读同一行写入不同 buffer，2D 批量不适用）",
      "段非 32B 对齐时不可合并（DataCopyPadExtParams blockCount=2 padding 行为不确定）"
    ],
    "required_conditions": [
      "（本条为负向边界，记录的是不适用条件）h0/h1 行在 GM 中地址连续（间隔 = wIn_ 个元素），可用固定 srcStride 表达——双线性插值 h0/h1 是相邻行，天然满足",
      "DataCopyExtParams blockCount=2 时 blockLen=segW*ds、srcStride=(wIn_-segW)*ds、dstStride=0 均落在接口合法范围",
      "h0 != h1 时合并写入连续 UB 区域（合并 buffer 前半 h0、后半 h1），消费方按实际 segW 派生 h1 偏移"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "artifacts": {
        "baseline_performance": "baseline/performance.json",
        "build": "rounds/003/build.json",
        "comparison": "rounds/003/comparison.json",
        "decision": "rounds/003/decision.json",
        "implementation": "rounds/003/implementation.md",
        "patch": "rounds/003/patch.diff",
        "performance": "rounds/003/performance.json",
        "round2_performance": "rounds/002/performance.json",
        "strategy": "rounds/003/strategy.json",
        "verify": "rounds/003/verify.json"
      },
      "operator_class": "fused-composite",
      "round": 3,
      "run_id": "<run-id>",
      "status": "rejected"
    },
    {
      "comparison_sha256": "1e6b8c1e41f7c191e7a16a8be432f7cbbc5a80e947614d886de46be0a843523b",
      "decision_sha256": "e0dd7a206be9189eb5e1f46b27ed7a6f005f364f08182e29cdea12151df73847",
      "operator_class": "fused-composite",
      "performance_sha256": "33f9852207b163a5d55d7be088eb06f3289011b9cff62a4f1ea1b818688c27a6",
      "round": 3,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "973bcd17b1062b972dd02b1328d7f1ad0d2bc3595cb211bb739708a6466a57d9",
      "verify_sha256": "7aad01604c261394ff85cecbd120679292a034e96b0f3cf60b934ad88540d274"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "mte2-bandwidth-saturation",
      "descriptor-issue-latency-masked"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "2d-rowpair-datacopy-merge",
    "structure": [
      "bilinear-interpolation",
      "index-gather-resampling",
      "ow-block-inner-loop",
      "mte2-descriptor-merge"
    ]
  },
  "generality": "op_class",
  "id": "NEG-RB-2D-ROWPAIR-MTE2-SAT",
  "implementation_steps": [
    "用 msprof pipe_utilization 确认目标 case 的 aiv_mte2_time 占比及绝对值，判断 MTE2 是否带宽饱和（case12 aiv_mte2_time 29%、case15 37%）",
    "估算描述符发射开销占 MTE2 时间的比例：若 MTE2 带宽已饱和（满核大数据量），描述符发射开销占比极低，减半描述符不会产生可测量收益",
    "若带宽未饱和（低核数/小数据量/高描述符密度），合并可尝试——case2（16核, 1.167x）证明此场景有效",
    "若带宽已饱和，转向数据量削减方向（如 C5 降采样采样窗拷贝减少搬运数据量）而非描述符合并",
    "验证目标 case 中位数 >= 1.03x、总加速 >= 1.02x、控制 case >= 0.95x、精度全过——本 run case12/15 未达 1.03x、总加速 1.013x < 1.02x，rollback 触发"
  ],
  "intent": "消除 MTE2 描述符发射开销瓶颈：R1 ow-block 路径 CopyIn 对每输出行发射 2 条独立 DataCopyPad（h0 行 + h1 行），假设描述符发射延迟是 MTE-bound case 的显著开销分量，合并后 MTE2 描述符数减半可降低描述符发射开销。",
  "mechanism": "kernel 侧 CopyIn 修改：将 inQueueH0/inQueueH1 合并为单一 inQueuePair（TQue<VECIN, BUFFER_NUM>），每 slot 分配 2*inSegBytes 连续 UB 区域。h0 != h1 且段 32B 对齐时，用单条 DataCopyExtParams{blockCount=2, blockLen=segW*ds, srcStride=(wIn_-segW)*ds, dstStride=0} 一次发射 h0/h1 行对；h0 == h1 或非对齐段时回退为 2 条独立搬运到合并 buffer 的前/后半段。Compute 中从 pairLocal 拆出 h0/h1 指针（__ubuf__ 指针算术，元素偏移）。host 侧不改、tiling 不改、VF 计算路径不改、CopyOut 不改。实现经历 3 次迭代修复精度（DataCopyPadExtParams blockCount=2 padding 行为不确定 -> 仅对齐段启用合并；segW 动态值与 segWMax_ 不一致 -> 用实际 segW 计算 segBytesActual；uint8_t* reinterpret_cast 编译失败 -> 改用 __ubuf__ D_T_X* 元素偏移），最终精度 20/20。",
  "name": "2D 行对合并搬运在 MTE2 带宽饱和满核场景的负向边界",
  "operator_class": "fused-composite",
  "operator_scope": "双线性插值类重采样 dataflow，R1 ow-block 路由下 h0/h1 行对合并搬运，N*C >= 64 满核 MTE2-bound 场景",
  "principle": "假设被证伪的因果链：MTE2 描述符发射开销（per-descriptor issue latency）是 MTE-bound case 的显著时间分量。实测证伪：在 N*C >= 64 满核 MTE2 带宽饱和场景（case12/15），MTE2 时间由数据量主导而非描述符密度主导——描述符数减半未转化为墙钟收益。描述符发射开销在满核带宽饱和时被带宽延迟完全掩盖。反例（case2 1.167x）证明在低核数/小数据量/高描述符密度场景机制仍有效，但收益不可外推到满核 MTE2-bound 场景。核心 lesson：MTE2 描述符数减半未必带来墙钟收益，描述符发射开销是否为瓶颈需逐 case 用 pipeline 数据验证，不能从描述符密度假设直接推导。",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray"
  ],
  "risks": [
    "从描述符密度假设直接推导收益：描述符数减半不等于墙钟收益，MTE2 带宽饱和时描述符发射开销被掩盖",
    "DataCopyPadExtParams blockCount=2 的 padding 行为不确定：非对齐段合并会导致精度失败，必须限定 32B 对齐段",
    "合并 buffer 后 Compute 中 h1 偏移需用实际 segW 动态计算（不可用 segWMax_ 静态值），否则块间间距不匹配导致精度失败",
    "uint8_t* 到 __ubuf__ 的 reinterpret_cast 被编译器拒绝：必须用 __ubuf__ D_T_X* 元素偏移",
    "case2 1.167x 的正向收益不可外推到满核 case：低核数高密度场景的有效性不能证明满核场景同样有效"
  ],
  "slug": "2d-rowpair-datacopy-mte2-saturation-boundary",
  "summary": "将 R1 ow-block 路径下 h0/h1 行对从 2 条独立 DataCopyPad 描述符合并为 1 条 DataCopyExtParams{blockCount=2} 2D 批量描述符，MTE2 描述符数减半但墙钟收益为零：case12 0.997x、case15 1.001x（MTE2 带宽饱和，描述符发射开销非瓶颈），总加速 1.013x < 1.02 最低门禁，rollback signals 触发，已回退。case2 1.167x 说明机制在低描述符密度/小数据量场景有效，但不足以拉高总体。",
  "verification": {
    "correctness": [
      "rounds/003/verify.json ok=true，20/20 通过，fingerprint 与 build.json kernel_hash db671b6ece6b85b8 一致",
      "3 次精度迭代修复后全通过：blockCount=2 padding 不确定 -> 仅对齐段合并；segW 动态值 -> 用实际 segW 计算 segBytesActual；uint8_t* reinterpret_cast -> __ubuf__ 元素偏移"
    ],
    "performance": [
      "负向证据：整体 1.013x（round2 3840.7us -> round3 3790.9us），低于 minimum_total_speedup 1.02x",
      "目标 case：case2 1.167x（超标，R1 低核数高描述符密度场景有效）、case12 0.997x（64核 MTE2-bound 无收益）、case15 1.001x（64核 MTE2 带宽饱和无收益），target_cases all_pass=false",
      "控制 case：case3 1.010x、case5 1.043x、case16 1.000x、case20 0.972x，all_pass=true max_regression=0.972x >= 0.95x",
      "样本稳定：除 case8 microkernel_noise_floor、case14 insufficient_samples 外全部 18 case stable（validation_cases 2/3/5/12/15/16/20 全部 stable），retry_recommended=false",
      "rollback_signals 触发：case12_below_1_03x=true、case15_below_1_03x=true、total_speedup_below_minimum=true；control_case_below_0_95x=false"
    ],
    "rollback_signals": [
      "case12/15 中位数 <1.03x -> 证伪（MTE2 描述符发射开销非瓶颈假设不成立）",
      "总加速 <1.02x -> 最低门禁未过",
      "精度门禁失败 -> 回退（stride/pad 错误导致行错位或越界读）",
      "本 run 已触发并 rollback：worktree 单 commit 承载策略，revert 后 round2 性能 3840.7us 不受影响"
    ]
  }
}
-->

# 性能优化策略：2D 行对合并搬运在 MTE2 带宽饱和满核场景的负向边界

单一优化点：将 R1 ow-block 路径下 h0/h1 行对从 2 条独立 DataCopyPad 描述符合并为 1 条 DataCopyExtParams{blockCount=2} 2D 批量描述符，MTE2 描述符数减半但墙钟收益为零：case12 0.997x、case15 1.001x（MTE2 带宽饱和，描述符发射开销非瓶颈），总加速 1.013x < 1.02 最低门禁，rollback signals 触发，已回退。case2 1.167x 说明机制在低描述符密度/小数据量场景有效，但不足以拉高总体。

## 1. 原理

假设被证伪的因果链：MTE2 描述符发射开销（per-descriptor issue latency）是 MTE-bound case 的显著时间分量。实测证伪：在 N*C >= 64 满核 MTE2 带宽饱和场景（case12/15），MTE2 时间由数据量主导而非描述符密度主导——描述符数减半未转化为墙钟收益。描述符发射开销在满核带宽饱和时被带宽延迟完全掩盖。反例（case2 1.167x）证明在低核数/小数据量/高描述符密度场景机制仍有效，但收益不可外推到满核 MTE2-bound 场景。核心 lesson：MTE2 描述符数减半未必带来墙钟收益，描述符发射开销是否为瓶颈需逐 case 用 pipeline 数据验证，不能从描述符密度假设直接推导。

实现机制：kernel 侧 CopyIn 修改：将 inQueueH0/inQueueH1 合并为单一 inQueuePair（TQue<VECIN, BUFFER_NUM>），每 slot 分配 2*inSegBytes 连续 UB 区域。h0 != h1 且段 32B 对齐时，用单条 DataCopyExtParams{blockCount=2, blockLen=segW*ds, srcStride=(wIn_-segW)*ds, dstStride=0} 一次发射 h0/h1 行对；h0 == h1 或非对齐段时回退为 2 条独立搬运到合并 buffer 的前/后半段。Compute 中从 pairLocal 拆出 h0/h1 指针（__ubuf__ 指针算术，元素偏移）。host 侧不改、tiling 不改、VF 计算路径不改、CopyOut 不改。实现经历 3 次迭代修复精度（DataCopyPadExtParams blockCount=2 padding 行为不确定 -> 仅对齐段启用合并；segW 动态值与 segWMax_ 不一致 -> 用实际 segW 计算 segBytesActual；uint8_t* reinterpret_cast 编译失败 -> 改用 __ubuf__ D_T_X* 元素偏移），最终精度 20/20。

## 2. 性能问题模式

- 优化目标：消除 MTE2 描述符发射开销瓶颈：R1 ow-block 路径 CopyIn 对每输出行发射 2 条独立 DataCopyPad（h0 行 + h1 行），假设描述符发射延迟是 MTE-bound case 的显著开销分量，合并后 MTE2 描述符数减半可降低描述符发射开销。
- 适用数据流：双线性插值类重采样 dataflow，R1 ow-block 路由下 h0/h1 行对合并搬运，N*C >= 64 满核 MTE2-bound 场景
- Feature signature：`{"bottleneck": ["mte2-bandwidth-saturation", "descriptor-issue-latency-masked"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "2d-rowpair-datacopy-merge", "structure": ["bilinear-interpolation", "index-gather-resampling", "ow-block-inner-loop", "mte2-descriptor-merge"]}`

## 3. 正确性红线

- 从描述符密度假设直接推导收益：描述符数减半不等于墙钟收益，MTE2 带宽饱和时描述符发射开销被掩盖
- DataCopyPadExtParams blockCount=2 的 padding 行为不确定：非对齐段合并会导致精度失败，必须限定 32B 对齐段
- 合并 buffer 后 Compute 中 h1 偏移需用实际 segW 动态计算（不可用 segWMax_ 静态值），否则块间间距不匹配导致精度失败
- uint8_t* 到 __ubuf__ 的 reinterpret_cast 被编译器拒绝：必须用 __ubuf__ D_T_X* 元素偏移
- case2 1.167x 的正向收益不可外推到满核 case：低核数高密度场景的有效性不能证明满核场景同样有效

资源与硬件约束：

- 硬件边界：结论采集自 ascend950（Ascend950DT, 64 AIV 核）；其他芯片需重新验证满核带宽饱和点
- 路由边界：负向结论主要约束 R1-buffer-mode1-ow-blocked 路由（高描述符密度场景），R0-buffer-mode0-whole-row 路由描述符密度低，case15 R0 路径 1.001x 同样无收益
- 正反边界：case2（R1, 16核, 131.9->113.0us=1.167x）证明机制在低核数/高描述符密度/小数据量场景有效；case12/15（64核 MTE2-bound）证明机制在满核带宽饱和场景无效。收益不可跨场景外推。
- 与 S4（strategies/common/2d-bulk-data-copy.md）的关系：S4 是同一机制的正向 validated_strategy（scatter-update, 1.0-1.3x），本条目是同一机制在 index-gather 满核 MTE2-bound 场景的负向边界。S4 risks 已预警'只减少描述符而未减少等待或队列往返时收益可能被其他固定开销限制'，本条目是该预警的实测确认。

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- （本条为负向边界，记录的是不适用条件）h0/h1 行在 GM 中地址连续（间隔 = wIn_ 个元素），可用固定 srcStride 表达——双线性插值 h0/h1 是相邻行，天然满足
- DataCopyExtParams blockCount=2 时 blockLen=segW*ds、srcStride=(wIn_-segW)*ds、dstStride=0 均落在接口合法范围
- h0 != h1 时合并写入连续 UB 区域（合并 buffer 前半 h0、后半 h1），消费方按实际 segW 派生 h1 偏移

不适用：

- N*C >= 64 满核 MTE2 带宽饱和场景（case12 2048-wide 64核、case15 127-plane 64核）：已实测证伪，描述符发射开销被带宽延迟掩盖，减半描述符无墙钟收益
- MTE2 时间由数据量主导而非描述符密度主导的 case：不可从描述符密度假设推导收益
- h0 == h1 时不可合并（srcStride=0 导致两次读同一行写入不同 buffer，2D 批量不适用）
- 段非 32B 对齐时不可合并（DataCopyPadExtParams blockCount=2 padding 行为不确定）

## 5. 实施步骤

1. 用 msprof pipe_utilization 确认目标 case 的 aiv_mte2_time 占比及绝对值，判断 MTE2 是否带宽饱和（case12 aiv_mte2_time 29%、case15 37%）
2. 估算描述符发射开销占 MTE2 时间的比例：若 MTE2 带宽已饱和（满核大数据量），描述符发射开销占比极低，减半描述符不会产生可测量收益
3. 若带宽未饱和（低核数/小数据量/高描述符密度），合并可尝试——case2（16核, 1.167x）证明此场景有效
4. 若带宽已饱和，转向数据量削减方向（如 C5 降采样采样窗拷贝减少搬运数据量）而非描述符合并
5. 验证目标 case 中位数 >= 1.03x、总加速 >= 1.02x、控制 case >= 0.95x、精度全过——本 run case12/15 未达 1.03x、总加速 1.013x < 1.02x，rollback 触发

## 6. LLM 前置问题

- 目标实现是否满足：（本条为负向边界，记录的是不适用条件）h0/h1 行在 GM 中地址连续（间隔 = wIn_ 个元素），可用固定 srcStride 表达——双线性插值 h0/h1 是相邻行，天然满足？
- 目标实现是否满足：DataCopyExtParams blockCount=2 时 blockLen=segW*ds、srcStride=(wIn_-segW)*ds、dstStride=0 均落在接口合法范围？
- 目标实现是否满足：h0 != h1 时合并写入连续 UB 区域（合并 buffer 前半 h0、后半 h1），消费方按实际 segW 派生 h1 偏移？
- 是否命中排除条件：N*C >= 64 满核 MTE2 带宽饱和场景（case12 2048-wide 64核、case15 127-plane 64核）：已实测证伪，描述符发射开销被带宽延迟掩盖，减半描述符无墙钟收益？

## 7. 验收标准

正确性：

- rounds/003/verify.json ok=true，20/20 通过，fingerprint 与 build.json kernel_hash db671b6ece6b85b8 一致
- 3 次精度迭代修复后全通过：blockCount=2 padding 不确定 -> 仅对齐段合并；segW 动态值 -> 用实际 segW 计算 segBytesActual；uint8_t* reinterpret_cast -> __ubuf__ 元素偏移

性能：

- 负向证据：整体 1.013x（round2 3840.7us -> round3 3790.9us），低于 minimum_total_speedup 1.02x
- 目标 case：case2 1.167x（超标，R1 低核数高描述符密度场景有效）、case12 0.997x（64核 MTE2-bound 无收益）、case15 1.001x（64核 MTE2 带宽饱和无收益），target_cases all_pass=false
- 控制 case：case3 1.010x、case5 1.043x、case16 1.000x、case20 0.972x，all_pass=true max_regression=0.972x >= 0.95x
- 样本稳定：除 case8 microkernel_noise_floor、case14 insufficient_samples 外全部 18 case stable（validation_cases 2/3/5/12/15/16/20 全部 stable），retry_recommended=false
- rollback_signals 触发：case12_below_1_03x=true、case15_below_1_03x=true、total_speedup_below_minimum=true；control_case_below_0_95x=false

回滚信号：

- case12/15 中位数 <1.03x -> 证伪（MTE2 描述符发射开销非瓶颈假设不成立）
- 总加速 <1.02x -> 最低门禁未过
- 精度门禁失败 -> 回退（stride/pad 错误导致行错位或越界读）
- 本 run 已触发并 rollback：worktree 单 commit 承载策略，revert 后 round2 性能 3840.7us 不受影响

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：per-element-mte-descriptor-spray

- resize_bilinear-20260825_024131-b12642（round=3, status=rejected）
- resize_bilinear-20260825_024131-b12642（round=3, status=rejected）

## 检索卡（短卡）

动作：先检查MTE2带宽饱和与关键路径，再比较h0/h1两次DataCopyPad合并为2D行对搬运是否减少实际工作
适用：h0/h1行在GM连续且间隔可用固定srcStride表达；先核验MTE2是否带宽饱和
限制：须重新核对目标平台核心数、UB容量及API支持范围，不得把单设备配置作为通用上限
范围：index-gather的ow-block CopyIn路径
检索词：2D行对搬运、MTE2、DataCopyPad、描述符发射、带宽饱和、pipe_utilization
机会：CopyIn对每个输出行分别发射h0与h1两条DataCopyPad描述符
代价：描述符减少未必降低墙钟时间；MTE2带宽饱和时耗时可能由数据量主导
