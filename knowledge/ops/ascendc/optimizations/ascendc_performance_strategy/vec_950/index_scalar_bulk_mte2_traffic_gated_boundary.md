---
type: Optimization
title: host 侧流量门控消除 microkernel 回归有效，但 TQue 逐 chunk 同步 + 索引块挤占 UB 预算使批量路径反而变慢
description: host tiling 按 numRowsTotal*topK >= 4096 设置 useBulkIdxPath flag 的流量门控机制本身验证有效：ORIG 路径 6 个 case（6/13/14/18/5/7）回到 baseline 附近（0.985-1.117x），完全消除轮次 1 D1 的 microkernel 回归。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/index-scalar-bulk-mte2-traffic-gated-boundary.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "硬件边界：结论采集自 ascend950 (Ascend950DT, 64 AIV 核), device 1",
      "阈值 4096 是本 run case 分布的分离点，复用时须按目标 workload 的回归/收益 traffic 分布重求",
      "本轮 patch.diff 被 checkpoint rollback 覆盖丢失（27005B→1B），源码级 diff 证据缺失，替代证据链见 rounds/002/audit-note.md；正确顺序为 snapshot→record-attempt→rollback 前另行归档 patch.diff",
      "scales TQue 统一用 int32_t 载体 ReinterpretCast 多 dtype，避免多模板实例；DeQue 结果须先存局部变量再 FreeTensor（左值要求）"
    ],
    "excluded_conditions": [
      "批量路径缓冲用 TQue<VECIN,1> 逐 chunk AllocTensor/EnQue/DeQue/FreeTensor：per-chunk 队列同步开销随 chunk 数线性放大，热 case 相对 TBuf 实现慢 10-22%",
      "索引块 UB 预算从主循环 usableUb 中扣除挤占 ubFactorH：主循环 tile 收缩、hTileNum 增大，热 case 主循环效率下降",
      "by-column 编址下行块尾块非 8 行对齐且无安全 2D 拷贝参数（dstStride!=0 触发设备错误 507035）时只能逐行回退，产生分治抖动"
    ],
    "required_conditions": [
      "host 可在 tiling 阶段计算 per-row traffic（如 R*K）并与回归/收益 case 的 traffic 分布存在可分离阈值（本例回归 case R*K {512,1024,256,4036} < 4096 < 收益 case R*K {8184..262144}）",
      "原始路径代码保持与 baseline 完全一致（零编辑风险），gate 只做路径选择不改动任一路径内部逻辑",
      "批量路径已单独验证正确性与收益（如 D1 的 20/20 精度与热 case 收益）"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "audit_note": "rounds/002/audit-note.md",
      "baseline_analysis": "baseline/analysis.md",
      "baseline_performance": "baseline/performance.json",
      "build": "rounds/002/build.json",
      "comparison": "rounds/002/comparison.json",
      "decision": "rounds/002/decision.json",
      "implementation": "rounds/002/implementation.md",
      "operator_class": "fused-composite",
      "performance": "rounds/002/performance.json",
      "review": "rounds/002/review.json",
      "round": 2,
      "round1_comparison": "rounds/001/comparison.json",
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy": "rounds/002/strategy.json",
      "verify": "rounds/002/verify.json"
    },
    {
      "comparison_sha256": "077d5b897883ef9a74e2c611b9ced9420579e8b35e52ffee80a840e498be3790",
      "decision_sha256": "c37424b6130a6fe710dfc43450b99086aa605de58fb9d2425322437a388723c3",
      "operator_class": "fused-composite",
      "performance_sha256": "4f4fde614fa4090ff8558b2d0308de5c9feba7a5daac58a0974805e4977b9fe7",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "7144922b328b858d51dbbb73841a22a580230640397de32ca1c973a6f26e1830",
      "verify_sha256": "399dcb4634dfef2ca19aabfc7ece7f77d68da4ba806941742f5f9d8c38ba80ae"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-gm-getvalue-dominant",
      "tque-per-chunk-sync-overhead",
      "ub-budget-contention-ubfactor-shrink"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "index-scalar-bulk-mte2-traffic-gated",
    "structure": [
      "host-tiling-traffic-threshold-gate",
      "dual-path-orig-bulk-fork",
      "tque-chunk-sync-vs-tbuf-resident",
      "idx-chunk-ub-budget-squeeze",
      "tail-chunk-8row-alignment-fallback"
    ]
  },
  "generality": "op_class",
  "id": "NB-MFR-D2-TRAFFIC-GATED-BULK-PATH",
  "implementation_steps": [
    "host tiling 新增 useBulkIdxPath/idxChunkRows 字段，按 R*K 阈值判定，ORIG 分支的 tiling 输出与 baseline 完全一致",
    "BULK 分支批量路径沿用已验证的 TBuf 常驻实现（D1 载体），不要改为 TQue 逐 chunk Alloc/EnQue/DeQue/Free",
    "idxChunkRows 用独立 UB 预算求解，不挤占主循环 ubFactorH；若无法独立则重新权衡 chunk 行数与主循环 tile 的平衡",
    "尾块非 8 行对齐时保留逐行回退，但需评估回退占比对分治收益的稀释",
    "分路径核对性能：ORIG case 应回 baseline±噪声，BULK case 应保持原批量实现收益（相对上轮不劣化）",
    "rollback 前 checkpoint snapshot 并另行归档 patch.diff"
  ],
  "intent": "在保留 D1 热 case 收益的同时消除其 microkernel noise-floor case 回归（D1 case 6/13/14 回归 5-6% 触发 max_case_regression gate）",
  "mechanism": "host tiling：TilingData 新增 useBulkIdxPath(uint8) 与 idxChunkRows(uint32)；numRowsTotal*topK >= 4096 时 useBulkIdxPath=1；BULK 路径 idxBudgetBytes=UB/4 求解 idxChunkRows（FloorAlign 8），从剩余 UB 重解 ubFactorH。kernel：PrefetchRowScalars 按 flag 分支——BULK 路径 TQue<VECIN,1>(estdrQue_/efsrQue_/scalesQue_) LoadIndexChunk/FreeIndexChunk（AllocTensor→DataCopy→EnQue / DeQue→FreeTensor），2D DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 批量搬索引、UB LocalTensor.GetValue 读标量；尾块 rowsInChunk%8!=0 回退 ORIG；ORIG 路径保持 baseline GM GetValue 不变。",
  "name": "host 侧流量门控消除 microkernel 回归有效，但 TQue 逐 chunk 同步 + 索引块挤占 UB 预算使批量路径反而变慢",
  "operator_class": "fused-composite",
  "operator_scope": "行切分 index-gather kernel 中按 R*K 流量分治（大 traffic 走 UB 批量索引搬运、小 traffic 走原始 GM 逐元素 GetValue）的 host 门控 + 双路径实现",
  "principle": "host 侧按 per-row traffic（R*K）阈值门控可以把固定开销主导的小流量 case 隔离在原始路径上，实现零回归分治——本轮 ORIG 路径证据支持该机制。但批量路径的索引缓冲载体选择决定成败：(a) TQue 队列语义引入逐 chunk AllocTensor/EnQue/DeQue/FreeTensor 同步开销，随 chunk 数线性放大（case 15 R*K 最大回归最多 0.821x 符合该因果）；(b) 索引块从主循环 UB 预算中扣除使 ubFactorH 收缩、主循环 tile 变小、hTileNum 增大，热 case 主循环效率下降；(c) by-column 尾块 rowsInChunk%8!=0 时 dstStride=0 2D 拷贝不安全，需回退逐行 GM GetValue，产生分治抖动。三者叠加使 BULK 路径相对 D1 净回归。回归 case cv 0.001-0.010 极稳定，reviewer 确认不可翻案（retry_recommended=false）。",
  "related_anti_patterns": [
    "dk-split-scalar-address-remap"
  ],
  "risks": [
    "把 D1 的 TBuf 改成 TQue 以求'规范性'：引入 per-chunk 同步开销，收益被抵消并反超（本轮总加速 0.9587）",
    "索引块预算挤占 ubFactorH：热 case 主循环 tile 收缩导致净回归，且与 TQue 开销叠加",
    "门控阈值直接复用 4096 而不按目标 workload traffic 分布重求",
    "rejected 轮次 rollback 时 rounds/NNN/patch.diff 被脚本覆盖丢失证据"
  ],
  "slug": "index-scalar-bulk-mte2-traffic-gated-boundary",
  "summary": "host tiling 按 numRowsTotal*topK >= 4096 设置 useBulkIdxPath flag 的流量门控机制本身验证有效：ORIG 路径 6 个 case（6/13/14/18/5/7）回到 baseline 附近（0.985-1.117x），完全消除轮次 1 D1 的 microkernel 回归。但本轮把 D1 的 TBuf 索引缓冲改为 TQue<VECIN,1> 逐 chunk AllocTensor/EnQue/DeQue/FreeTensor，且 idxChunkRows 占用 1/4 UB 预算导致 ubFactorH 收缩、hTileNum 增大，BULK 路径相对 D1 普遍慢 10-22%（case 2/3/8/15 相对 D1 0.852/0.780/0.821/0.821），case 2/3/15 相对 baseline 也降至 0.857/0.781/0.915，总加速 0.9587，三项性能门禁两项失败，rejected。正确载体是 D1 的 TBuf（无队列同步）实现；idxChunkRows 应使用独立 UB 预算而非挤占 ubFactorH。",
  "verification": {
    "correctness": [
      "rounds/002/verify.json: 20/20 passed，6 flag route 全部精度通过",
      "fingerprint kernel_hash=6f72870b5dac739b、device=1、git_diff_sha256=c6527915b7c6cfd3 在 build/verify/performance 间一致（review.json）"
    ],
    "performance": [
      "门控正向证据：ORIG 路径 case 6/13/14/18/5/7 相对 baseline 0.985/1.013/1.117/0.996/1.027/1.007，轮次 1 的 microkernel 回归被完全消除",
      "BULK 路径负向证据：相对轮次 1 (D1) case 1/2/3/4/8/9/12/15 = 0.890/0.852/0.780/0.900/0.821/0.914/0.871/0.821；case 2/3/15 相对 baseline 0.857/0.781/0.915",
      "总加速 0.9587，improved_speedup/minimum_total_speedup/max_case_regression 三门禁中前两项失败，decision=rejected；回归 case cv 0.001-0.010，reviewer 确认 retry_recommended=false 不可翻案"
    ],
    "rollback_signals": [
      "BULK 路径 case 相对既有批量实现（上轮）median 变慢超过 5%：载体退化（TQue 化）或 UB 预算挤占",
      "ORIG 路径 case 相对 baseline < 0.95x：gate 逻辑错误导致误启用批量路径",
      "rowsInChunk%8!=0 尾块出现 [1,0,1,0,...] 零值伪影或设备错误 507035：2D 拷贝参数不安全，回退逐行路径"
    ]
  }
}
-->

# 性能优化策略：host 侧流量门控消除 microkernel 回归有效，但 TQue 逐 chunk 同步 + 索引块挤占 UB 预算使批量路径反而变慢

单一优化点：host tiling 按 numRowsTotal*topK >= 4096 设置 useBulkIdxPath flag 的流量门控机制本身验证有效：ORIG 路径 6 个 case（6/13/14/18/5/7）回到 baseline 附近（0.985-1.117x），完全消除轮次 1 D1 的 microkernel 回归。但本轮把 D1 的 TBuf 索引缓冲改为 TQue<VECIN,1> 逐 chunk AllocTensor/EnQue/DeQue/FreeTensor，且 idxChunkRows 占用 1/4 UB 预算导致 ubFactorH 收缩、hTileNum 增大，BULK 路径相对 D1 普遍慢 10-22%（case 2/3/8/15 相对 D1 0.852/0.780/0.821/0.821），case 2/3/15 相对 baseline 也降至 0.857/0.781/0.915，总加速 0.9587，三项性能门禁两项失败，rejected。正确载体是 D1 的 TBuf（无队列同步）实现；idxChunkRows 应使用独立 UB 预算而非挤占 ubFactorH。

## 1. 原理

host 侧按 per-row traffic（R*K）阈值门控可以把固定开销主导的小流量 case 隔离在原始路径上，实现零回归分治——本轮 ORIG 路径证据支持该机制。但批量路径的索引缓冲载体选择决定成败：(a) TQue 队列语义引入逐 chunk AllocTensor/EnQue/DeQue/FreeTensor 同步开销，随 chunk 数线性放大（case 15 R*K 最大回归最多 0.821x 符合该因果）；(b) 索引块从主循环 UB 预算中扣除使 ubFactorH 收缩、主循环 tile 变小、hTileNum 增大，热 case 主循环效率下降；(c) by-column 尾块 rowsInChunk%8!=0 时 dstStride=0 2D 拷贝不安全，需回退逐行 GM GetValue，产生分治抖动。三者叠加使 BULK 路径相对 D1 净回归。回归 case cv 0.001-0.010 极稳定，reviewer 确认不可翻案（retry_recommended=false）。

实现机制：host tiling：TilingData 新增 useBulkIdxPath(uint8) 与 idxChunkRows(uint32)；numRowsTotal*topK >= 4096 时 useBulkIdxPath=1；BULK 路径 idxBudgetBytes=UB/4 求解 idxChunkRows（FloorAlign 8），从剩余 UB 重解 ubFactorH。kernel：PrefetchRowScalars 按 flag 分支——BULK 路径 TQue<VECIN,1>(estdrQue_/efsrQue_/scalesQue_) LoadIndexChunk/FreeIndexChunk（AllocTensor→DataCopy→EnQue / DeQue→FreeTensor），2D DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 批量搬索引、UB LocalTensor.GetValue 读标量；尾块 rowsInChunk%8!=0 回退 ORIG；ORIG 路径保持 baseline GM GetValue 不变。

## 2. 性能问题模式

- 优化目标：在保留 D1 热 case 收益的同时消除其 microkernel noise-floor case 回归（D1 case 6/13/14 回归 5-6% 触发 max_case_regression gate）
- 适用数据流：行切分 index-gather kernel 中按 R*K 流量分治（大 traffic 走 UB 批量索引搬运、小 traffic 走原始 GM 逐元素 GetValue）的 host 门控 + 双路径实现
- Feature signature：`{"bottleneck": ["scalar-gm-getvalue-dominant", "tque-per-chunk-sync-overhead", "ub-budget-contention-ubfactor-shrink"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "index-scalar-bulk-mte2-traffic-gated", "structure": ["host-tiling-traffic-threshold-gate", "dual-path-orig-bulk-fork", "tque-chunk-sync-vs-tbuf-resident", "idx-chunk-ub-budget-squeeze", "tail-chunk-8row-alignment-fallback"]}`

## 3. 正确性红线

- 把 D1 的 TBuf 改成 TQue 以求'规范性'：引入 per-chunk 同步开销，收益被抵消并反超（本轮总加速 0.9587）
- 索引块预算挤占 ubFactorH：热 case 主循环 tile 收缩导致净回归，且与 TQue 开销叠加
- 门控阈值直接复用 4096 而不按目标 workload traffic 分布重求
- rejected 轮次 rollback 时 rounds/NNN/patch.diff 被脚本覆盖丢失证据

资源与硬件约束：

- 硬件边界：结论采集自 ascend950 (Ascend950DT, 64 AIV 核), device 1
- 阈值 4096 是本 run case 分布的分离点，复用时须按目标 workload 的回归/收益 traffic 分布重求
- 本轮 patch.diff 被 checkpoint rollback 覆盖丢失（27005B→1B），源码级 diff 证据缺失，替代证据链见 rounds/002/audit-note.md；正确顺序为 snapshot→record-attempt→rollback 前另行归档 patch.diff
- scales TQue 统一用 int32_t 载体 ReinterpretCast 多 dtype，避免多模板实例；DeQue 结果须先存局部变量再 FreeTensor（左值要求）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- host 可在 tiling 阶段计算 per-row traffic（如 R*K）并与回归/收益 case 的 traffic 分布存在可分离阈值（本例回归 case R*K {512,1024,256,4036} < 4096 < 收益 case R*K {8184..262144}）
- 原始路径代码保持与 baseline 完全一致（零编辑风险），gate 只做路径选择不改动任一路径内部逻辑
- 批量路径已单独验证正确性与收益（如 D1 的 20/20 精度与热 case 收益）

不适用：

- 批量路径缓冲用 TQue<VECIN,1> 逐 chunk AllocTensor/EnQue/DeQue/FreeTensor：per-chunk 队列同步开销随 chunk 数线性放大，热 case 相对 TBuf 实现慢 10-22%
- 索引块 UB 预算从主循环 usableUb 中扣除挤占 ubFactorH：主循环 tile 收缩、hTileNum 增大，热 case 主循环效率下降
- by-column 编址下行块尾块非 8 行对齐且无安全 2D 拷贝参数（dstStride!=0 触发设备错误 507035）时只能逐行回退，产生分治抖动

## 5. 实施步骤

1. host tiling 新增 useBulkIdxPath/idxChunkRows 字段，按 R*K 阈值判定，ORIG 分支的 tiling 输出与 baseline 完全一致
2. BULK 分支批量路径沿用已验证的 TBuf 常驻实现（D1 载体），不要改为 TQue 逐 chunk Alloc/EnQue/DeQue/Free
3. idxChunkRows 用独立 UB 预算求解，不挤占主循环 ubFactorH；若无法独立则重新权衡 chunk 行数与主循环 tile 的平衡
4. 尾块非 8 行对齐时保留逐行回退，但需评估回退占比对分治收益的稀释
5. 分路径核对性能：ORIG case 应回 baseline±噪声，BULK case 应保持原批量实现收益（相对上轮不劣化）
6. rollback 前 checkpoint snapshot 并另行归档 patch.diff

## 6. LLM 前置问题

- 目标实现是否满足：host 可在 tiling 阶段计算 per-row traffic（如 R*K）并与回归/收益 case 的 traffic 分布存在可分离阈值（本例回归 case R*K {512,1024,256,4036} < 4096 < 收益 case R*K {8184..262144}）？
- 目标实现是否满足：原始路径代码保持与 baseline 完全一致（零编辑风险），gate 只做路径选择不改动任一路径内部逻辑？
- 目标实现是否满足：批量路径已单独验证正确性与收益（如 D1 的 20/20 精度与热 case 收益）？
- 是否命中排除条件：批量路径缓冲用 TQue<VECIN,1> 逐 chunk AllocTensor/EnQue/DeQue/FreeTensor：per-chunk 队列同步开销随 chunk 数线性放大，热 case 相对 TBuf 实现慢 10-22%？

## 7. 验收标准

正确性：

- rounds/002/verify.json: 20/20 passed，6 flag route 全部精度通过
- fingerprint kernel_hash=6f72870b5dac739b、device=1、git_diff_sha256=c6527915b7c6cfd3 在 build/verify/performance 间一致（review.json）

性能：

- 门控正向证据：ORIG 路径 case 6/13/14/18/5/7 相对 baseline 0.985/1.013/1.117/0.996/1.027/1.007，轮次 1 的 microkernel 回归被完全消除
- BULK 路径负向证据：相对轮次 1 (D1) case 1/2/3/4/8/9/12/15 = 0.890/0.852/0.780/0.900/0.821/0.914/0.871/0.821；case 2/3/15 相对 baseline 0.857/0.781/0.915
- 总加速 0.9587，improved_speedup/minimum_total_speedup/max_case_regression 三门禁中前两项失败，decision=rejected；回归 case cv 0.001-0.010，reviewer 确认 retry_recommended=false 不可翻案

回滚信号：

- BULK 路径 case 相对既有批量实现（上轮）median 变慢超过 5%：载体退化（TQue 化）或 UB 预算挤占
- ORIG 路径 case 相对 baseline < 0.95x：gate 逻辑错误导致误启用批量路径
- rowsInChunk%8!=0 尾块出现 [1,0,1,0,...] 零值伪影或设备错误 507035：2D 拷贝参数不安全，回退逐行路径

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap

- moe_finalize_routing-20260826_014147-27927d（round=2, status=rejected）
- moe_finalize_routing-20260826_014147-27927d（round=2, status=rejected）

## 检索卡（短卡）

动作：由 host 按 R*K 流量阈值门控批量索引 staging，小流量从无条件批量改为保留原路径
适用：host 可在 tiling 阶段计算 R*K 等每行流量，且测量能分离不同流量区间
限制：ORIG 分支的 tiling 输出必须与 baseline 完全一致
范围：host tiling 的批量索引 staging 路径
检索词：per-row traffic、R*K、useBulkIdxPath、idxChunkRows、批量索引 staging、TQue
机会：批量索引 staging 在小流量输入上仍有固定分配和描述符成本
代价：TQue 会增加队列、逐 chunk 同步及固定开销，使用前须证明必要性
