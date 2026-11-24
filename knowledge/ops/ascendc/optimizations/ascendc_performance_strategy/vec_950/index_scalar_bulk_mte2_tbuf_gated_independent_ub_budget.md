---
type: Optimization
title: host 流量门控 + TBuf 常驻 BULK 索引搬运 + idxChunkRows 独立 UB 预算封顶每核行数的零回归分治
description: 将索引数组整块 MTE2 搬入常驻 UB TBuf；host 按每行流量门控，小流量保留原路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget.md
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
      "硬件边界：结论采集自 ascend950 (Ascend950DT, 64 AIV 核), device 1，本机 ubSize=253952",
      "DataCopyExtParams dstStride 单位为 32B datablocks，列优先 2D 拷贝 blockLen 已对齐时 dstStride=0",
      "FloorAlign/CeilAlign 模板要求两参同型（int64 字面量需 cast）；SetFlag/WaitFlag 需要 eventID 实参且 TPipe 无成员版本；GlobalTensor 无 GetAddr",
      "EVENT_ID7 用于 MTE2→Scalar 可见性同步，避开 TPipe 队列事件 ID 池",
      "门控阈值 4096 是本 run case 分布分离点，复用时须按目标 workload 重求"
    ],
    "excluded_conditions": [
      "fp32 大流量 case：主循环 InitBuffer 占用（5 个 DT 槽 + fp32 累加器）几乎占满 UB，host 求解 chunk=0 自动回退 ORIG；且 fp32 数据搬运本身主导（case_2 对索引批量搬运无响应，R1/R3 均 ~1.006x），此边界在两个独立轮次复现",
      "microkernel noise-floor case（median < 15us）：由门控隔离在 ORIG 路径，不得进入 BULK",
      "idxChunkRows > numRowsPerCore：整 chunk 循环不进、全部行落尾块 ORIG 回退，BULK 等效关闭且无报错（本轮第 2 版实测总加速退化为 0.9946x，热 case 与 baseline 完全重合）",
      "host 用 NUM_PEAK_BUFFERS*max(dtype,4)*ubFactorH 保守预算估算剩余：fp32/fp16 下为负，门控永不触发（第 1 版实测 1.0063x）"
    ],
    "required_conditions": [
      "kernel 每行 O(K) 次逐元素标量 GM GetValue 读取索引/缩放数组且 Scalar 引擎主导（aiv_scalar_ratio >= 0.80）",
      "host 可在 tiling 阶段计算 per-row traffic 并与回归/收益 case 分布存在可分离阈值（本例回归 case R*K {512..4036} < 4096 < 收益 case R*K {8184..262144}）",
      "UB 实际剩余预算（按 kernel InitBuffer 实占计算）可容纳至少一个 8 行对齐索引 chunk",
      "原始路径代码与 baseline 逐行等价，gate 只做路径选择",
      "chunk 行数求解必须封顶 min(预算解, numRowsPerCore)，并 FloorAlign 到 8"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "baseline_analysis": "baseline/analysis.md",
      "baseline_performance": "baseline/performance.json",
      "build": "rounds/003/build.json",
      "comparison": "rounds/003/comparison.json",
      "decision": "rounds/003/decision.json",
      "implementation": "rounds/003/implementation.md",
      "operator_class": "fused-composite",
      "patch": "rounds/003/patch.diff",
      "performance": "rounds/003/performance.json",
      "review": "rounds/003/review.json",
      "round": 3,
      "round4_selection": "rounds/004/selection.json",
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy": "rounds/003/strategy.json",
      "verify": "rounds/003/verify.json"
    },
    {
      "comparison_sha256": "f44082c49433b387ce85ec94967dd398e99f80be2c65a21c529b235058590c5b",
      "decision_sha256": "595e88c49ae3bfc009c92090f2b1519e7ebff91eb9feea445973e9cd320f6627",
      "operator_class": "fused-composite",
      "performance_sha256": "7bcf80973325b106e960bb20898f6c3d0776f519af524ccf999e9f4705867e0c",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "36ca2fd94c2a74f68ec1cdf46daa8810d532745e96f39a18232c116651c0192c",
      "verify_sha256": "6186c034bdf949b1c0cd2ef6c94acf194948840977a9bb8d854ea2452dc01edb"
    },
    {
      "comparison_sha256": "7f619b69ff3a01f97cc9385251f5335bc35dcf40f330e10b7437480516c2ac33",
      "decision_sha256": "e7107b7e12160dfdb04f903c1b0f09ac89ac89a80dd13565a5ca7ad32e4ebe6c",
      "operator_class": "fused-composite",
      "performance_sha256": "b8bd36bac6a43c34c2cb92923ba4eaa94159dce9cf71cb193536db880a6eae03",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "705b5b4ea54cb253c57697ce706bb5a841e2ac62563ec0297e6bb5f3375ad825",
      "verify_sha256": "86cd2ae329e98c5c1582ced91a071aed542d9010b736f0ad9d570203015b2660"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-gm-getvalue-dominant",
      "mte2-bandwidth-dominant-fp32-no-response"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "index-scalar-bulk-mte2-tbuf-gated",
    "structure": [
      "host-tiling-traffic-threshold-gate",
      "tbuf-resident-bulk-mte2-no-queue-sync",
      "idx-chunk-independent-ub-budget-after-ubfactorh",
      "idx-chunk-capped-by-rows-per-core",
      "branch-execution-pollution-probe",
      "fp32-no-ub-residual-auto-fallback-orig"
    ]
  },
  "generality": "op_class",
  "id": "S-MFR-D3-TBUF-GATED-INDEPENDENT-UB-BUDGET",
  "implementation_steps": [
    "tiling struct 新增 useBulkIdxPath/idxChunkRows 字段，R*K 阈值门控，ORIG 分支 tiling 输出与 baseline 完全一致",
    "ubFactorH 求解保持不变；idxBudgetBytes 按 kernel 实际 InitBuffer 占用（DT 槽 + 累加器 CeilAlign 32）计算剩余，勿用保守峰值预算",
    "idxChunkRows = FloorAlign(min(FloorDiv(idxBudget, idxRowBytes), numRowsPerCore), 8)；为 0 时回退 ORIG",
    "kernel 新增 TBuf<VECCALC> 索引缓冲（仅 BULK 启用且对应 flag 时 InitBuffer），LoadIndexChunk 每 chunk 3 条 DataCopyPad + 一次 SetFlag/WaitFlag<MTE2_S> 同步，禁止 TQue 逐 chunk Alloc/EnQue/DeQue/Free",
    "PrefetchRowScalarsUb 从 UB 读行标量，drop sentinel/eid OOB/scales 缺席语义与 GM 版逐条一致；尾块逐行回退 ORIG",
    "用'污染 UB 读值后精度仍通过'探针验证 BULK 分支确实执行（比读 profiling 更决定性），验证后移除探针",
    "分路径核对性能：BULK case 恢复既有批量实现收益（相对上轮不劣化），ORIG case 回 baseline±噪声，全 case >= 0.95"
  ],
  "intent": "消除逐元素标量 GM GetValue 的 Scalar 引擎瓶颈，同时通过 host 门控和独立 UB 预算保证小流量 case 与主循环 tiling 零回归",
  "mechanism": "host tiling：TilingData 新增 useBulkIdxPath(uint8)/idxChunkRows(uint32)；R*K >= 4096 进入求解；ubFactorH 公式逐字节不变；idxBudgetBytes = ubSize - kernel 实际 InitBuffer 占用 - 5*32 余量；idxChunkRows = FloorAlign(min(FloorDiv(idxBudget, idxRowBytes), numRowsPerCore), 8)；求解为 0 时回退 ORIG。kernel：useBulkIdxPath=1 时 estdrBuf_/efsrBuf_/scalesBuf_（TBuf<VECCALC>，仅启用且对应 flag 时分配）LoadIndexChunk 每 chunk 3 条 DataCopyPad + 一次 SetFlag/WaitFlag<MTE2_S>(EVENT_ID7) 同步，无 TQue 逐 chunk 队列操作；estdr by-column 2D 拷贝 {blockCount=K, blockLen=rows*4, dstStride=0} / by-row 1D；scales 混合 dtype 分视图拷贝后 LoadScaleFromUb 转 fp32（bf16 位级转换）；尾块逐行回退 ORIG GM 路径；useBulkIdxPath=0 走 baseline 原始循环；workspace/blockDim/H tiling 公式/tiling key 均不改动。",
  "name": "host 流量门控 + TBuf 常驻 BULK 索引搬运 + idxChunkRows 独立 UB 预算封顶每核行数的零回归分治",
  "operator_class": "fused-composite",
  "operator_scope": "行切分 index-gather kernel（每行 O(K) 次逐元素标量 GM GetValue 读取索引/缩放数组）按 host 侧流量门控分治到大流量 UB 批量路径与小流量原始路径的场景",
  "principle": "三条因果各自独立验证：(1) 索引数组整块 MTE2 进 UB 常驻 TBuf 消除标量 GM 串行读（R1 热 case 1.11-1.34x）；(2) host 按 per-row traffic 阈值门控把固定开销主导的小流量 case 隔离在原始路径（R2 ORIG case 零回归）；(3) 索引 chunk 预算在主循环 ubFactorH 求解之后按 UB 实际剩余预算独立求解，主循环 tile 不收缩。关键补充因果（本轮发现）：idxChunkRows 若不封顶每核行数，kernel 整 chunk 循环一次都不进，全部行落入尾块 ORIG 回退，BULK 路径等效关闭且无任何报错——必须 min(chunk, numRowsPerCore) + FloorAlign(8) 封顶；用'故意污染 UB 读值后精度仍 20/20 通过'的探针证明了分支未执行。host 剩余预算必须按 kernel 实际 InitBuffer 占用计算（5*CeilAlign(ubFactorH*typeSize,32)+CeilAlign(ubFactorH*4,32)），不能用 NUM_PEAK_BUFFERS*max(dtype,4)*ubFactorH 保守估计——后者在 fp32 下恰好占满 UB，门控永不触发。",
  "related_anti_patterns": [
    "dk-split-scalar-address-remap"
  ],
  "risks": [
    "idxChunkRows 未封顶每核行数：BULK 静默失效（无报错、精度全过、性能与 baseline 重合），必须 min(·, numRowsPerCore) 封顶；该机制可能是 R2 BULK 回归的真正主因（假说：R2 同为预算制求解未按 rows/core 封顶，R2 review 归因的 TQue 逐 chunk 同步未必是主因——探针证据自报，未经 R2 代码复测证实）",
    "host 保守峰值预算使门控永不触发：剩余预算必须按 kernel 实际 InitBuffer 占用计算",
    "把 TBuf 改为 TQue 或让索引 chunk 挤占 ubFactorH：回到 R2 的负边界",
    "fp32 下无 UB 剩余属预期行为（自动回退 ORIG），不应强行压缩主循环 tile 换取 chunk 空间"
  ],
  "slug": "index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget",
  "summary": "组合三条已分别验证的半边：host 按 R*K >= 阈值门控（R2 已验证 ORIG 零回归）+ BULK 分支 TBuf 常驻整块 MTE2（R1 已验证热 case 收益，无 TQue 逐 chunk 同步）+ idxChunkRows 在 ubFactorH 之后按 UB 剩余预算独立求解（不挤占主循环 tile）且封顶 min(chunk, numRowsPerCore)。实测总加速 1.1113x，最低 case ratio 0.9637（无 case 低于 0.95），精度 20/20，三项性能门禁全过，热 case 恢复 D1 量级收益（1.11-1.25x）且小 case 零回归。",
  "verification": {
    "correctness": [
      "rounds/003/verify.json: 20/20 passed，6 个 flag route（R-A full params / R-B no-skip2 / R-C no-skip / R-D no-bias / R-E no-scales K=1 / R-F 3D drop_pad mode0-3）全部精度通过",
      "污染 UB 读值 (-12345) 探针使精度必然错误，20/20 通过即证明 BULK 分支未执行的静默失效被定位并修复（探针已移除）"
    ],
    "performance": [
      "总加速 1.1113x（2628.9us -> 2365.5us），improved_speedup >= 1.05 PASS、minimum_total_speedup >= 1.02 PASS、max_case_regression 最低 0.9637 >= 0.95 PASS，回归 case 列表为空",
      "热 case（BULK）：case 15 1.115x、case 9 1.248x、case 8 1.137x、case 12 1.215x、case 4 1.213x、case 1 1.209x，恢复 D1 量级（D1 1.115-1.335x）",
      "小 case（ORIG 门控）：case 6 1.006x、13 0.964x、14 1.016x、18 1.002x、5 1.026x、7 1.005x、10 0.977x，零回归",
      "case 2/3（R*K>=4096 但 fp32 无 UB 剩余 → chunk=0 → ORIG）1.006x/1.007x，与 R1 的 1.006x/1.001x 一致：fp32 数据搬运主导，对索引批量搬运无响应（负边界独立复现）"
    ],
    "rollback_signals": [
      "任一 BULK case 相对既有批量实现 median 慢 >5%（载体退化或 UB 预算挤占）",
      "任一 ORIG case 相对 baseline < 0.95x（门控误路由）",
      "精度门禁失败（drop sentinel / eid OOB / bf16 scales 位级转换）",
      "热 case 性能与 baseline 完全重合且精度全过：怀疑 chunk 行数超每核行数导致 BULK 静默关闭，用污染探针确认"
    ]
  }
}
-->

# 性能优化策略：host 流量门控 + TBuf 常驻 BULK 索引搬运 + idxChunkRows 独立 UB 预算封顶每核行数的零回归分治

单一优化点：组合三条已分别验证的半边：host 按 R*K >= 阈值门控（R2 已验证 ORIG 零回归）+ BULK 分支 TBuf 常驻整块 MTE2（R1 已验证热 case 收益，无 TQue 逐 chunk 同步）+ idxChunkRows 在 ubFactorH 之后按 UB 剩余预算独立求解（不挤占主循环 tile）且封顶 min(chunk, numRowsPerCore)。实测总加速 1.1113x，最低 case ratio 0.9637（无 case 低于 0.95），精度 20/20，三项性能门禁全过，热 case 恢复 D1 量级收益（1.11-1.25x）且小 case 零回归。

## 1. 原理

三条因果各自独立验证：(1) 索引数组整块 MTE2 进 UB 常驻 TBuf 消除标量 GM 串行读（R1 热 case 1.11-1.34x）；(2) host 按 per-row traffic 阈值门控把固定开销主导的小流量 case 隔离在原始路径（R2 ORIG case 零回归）；(3) 索引 chunk 预算在主循环 ubFactorH 求解之后按 UB 实际剩余预算独立求解，主循环 tile 不收缩。关键补充因果（本轮发现）：idxChunkRows 若不封顶每核行数，kernel 整 chunk 循环一次都不进，全部行落入尾块 ORIG 回退，BULK 路径等效关闭且无任何报错——必须 min(chunk, numRowsPerCore) + FloorAlign(8) 封顶；用'故意污染 UB 读值后精度仍 20/20 通过'的探针证明了分支未执行。host 剩余预算必须按 kernel 实际 InitBuffer 占用计算（5*CeilAlign(ubFactorH*typeSize,32)+CeilAlign(ubFactorH*4,32)），不能用 NUM_PEAK_BUFFERS*max(dtype,4)*ubFactorH 保守估计——后者在 fp32 下恰好占满 UB，门控永不触发。

实现机制：host tiling：TilingData 新增 useBulkIdxPath(uint8)/idxChunkRows(uint32)；R*K >= 4096 进入求解；ubFactorH 公式逐字节不变；idxBudgetBytes = ubSize - kernel 实际 InitBuffer 占用 - 5*32 余量；idxChunkRows = FloorAlign(min(FloorDiv(idxBudget, idxRowBytes), numRowsPerCore), 8)；求解为 0 时回退 ORIG。kernel：useBulkIdxPath=1 时 estdrBuf_/efsrBuf_/scalesBuf_（TBuf<VECCALC>，仅启用且对应 flag 时分配）LoadIndexChunk 每 chunk 3 条 DataCopyPad + 一次 SetFlag/WaitFlag<MTE2_S>(EVENT_ID7) 同步，无 TQue 逐 chunk 队列操作；estdr by-column 2D 拷贝 {blockCount=K, blockLen=rows*4, dstStride=0} / by-row 1D；scales 混合 dtype 分视图拷贝后 LoadScaleFromUb 转 fp32（bf16 位级转换）；尾块逐行回退 ORIG GM 路径；useBulkIdxPath=0 走 baseline 原始循环；workspace/blockDim/H tiling 公式/tiling key 均不改动。

## 2. 性能问题模式

- 优化目标：消除逐元素标量 GM GetValue 的 Scalar 引擎瓶颈，同时通过 host 门控和独立 UB 预算保证小流量 case 与主循环 tiling 零回归
- 适用数据流：行切分 index-gather kernel（每行 O(K) 次逐元素标量 GM GetValue 读取索引/缩放数组）按 host 侧流量门控分治到大流量 UB 批量路径与小流量原始路径的场景
- Feature signature：`{"bottleneck": ["scalar-gm-getvalue-dominant", "mte2-bandwidth-dominant-fp32-no-response"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "index-scalar-bulk-mte2-tbuf-gated", "structure": ["host-tiling-traffic-threshold-gate", "tbuf-resident-bulk-mte2-no-queue-sync", "idx-chunk-independent-ub-budget-after-ubfactorh", "idx-chunk-capped-by-rows-per-core", "branch-execution-pollution-probe", "fp32-no-ub-residual-auto-fallback-orig"]}`

## 3. 正确性红线

- idxChunkRows 未封顶每核行数：BULK 静默失效（无报错、精度全过、性能与 baseline 重合），必须 min(·, numRowsPerCore) 封顶；该机制可能是 R2 BULK 回归的真正主因（假说：R2 同为预算制求解未按 rows/core 封顶，R2 review 归因的 TQue 逐 chunk 同步未必是主因——探针证据自报，未经 R2 代码复测证实）
- host 保守峰值预算使门控永不触发：剩余预算必须按 kernel 实际 InitBuffer 占用计算
- 把 TBuf 改为 TQue 或让索引 chunk 挤占 ubFactorH：回到 R2 的负边界
- fp32 下无 UB 剩余属预期行为（自动回退 ORIG），不应强行压缩主循环 tile 换取 chunk 空间

资源与硬件约束：

- 硬件边界：结论采集自 ascend950 (Ascend950DT, 64 AIV 核), device 1，本机 ubSize=253952
- DataCopyExtParams dstStride 单位为 32B datablocks，列优先 2D 拷贝 blockLen 已对齐时 dstStride=0
- FloorAlign/CeilAlign 模板要求两参同型（int64 字面量需 cast）；SetFlag/WaitFlag 需要 eventID 实参且 TPipe 无成员版本；GlobalTensor 无 GetAddr
- EVENT_ID7 用于 MTE2→Scalar 可见性同步，避开 TPipe 队列事件 ID 池
- 门控阈值 4096 是本 run case 分布分离点，复用时须按目标 workload 重求

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- kernel 每行 O(K) 次逐元素标量 GM GetValue 读取索引/缩放数组且 Scalar 引擎主导（aiv_scalar_ratio >= 0.80）
- host 可在 tiling 阶段计算 per-row traffic 并与回归/收益 case 分布存在可分离阈值（本例回归 case R*K {512..4036} < 4096 < 收益 case R*K {8184..262144}）
- UB 实际剩余预算（按 kernel InitBuffer 实占计算）可容纳至少一个 8 行对齐索引 chunk
- 原始路径代码与 baseline 逐行等价，gate 只做路径选择
- chunk 行数求解必须封顶 min(预算解, numRowsPerCore)，并 FloorAlign 到 8

不适用：

- fp32 大流量 case：主循环 InitBuffer 占用（5 个 DT 槽 + fp32 累加器）几乎占满 UB，host 求解 chunk=0 自动回退 ORIG；且 fp32 数据搬运本身主导（case_2 对索引批量搬运无响应，R1/R3 均 ~1.006x），此边界在两个独立轮次复现
- microkernel noise-floor case（median < 15us）：由门控隔离在 ORIG 路径，不得进入 BULK
- idxChunkRows > numRowsPerCore：整 chunk 循环不进、全部行落尾块 ORIG 回退，BULK 等效关闭且无报错（本轮第 2 版实测总加速退化为 0.9946x，热 case 与 baseline 完全重合）
- host 用 NUM_PEAK_BUFFERS*max(dtype,4)*ubFactorH 保守预算估算剩余：fp32/fp16 下为负，门控永不触发（第 1 版实测 1.0063x）

## 5. 实施步骤

1. tiling struct 新增 useBulkIdxPath/idxChunkRows 字段，R*K 阈值门控，ORIG 分支 tiling 输出与 baseline 完全一致
2. ubFactorH 求解保持不变；idxBudgetBytes 按 kernel 实际 InitBuffer 占用（DT 槽 + 累加器 CeilAlign 32）计算剩余，勿用保守峰值预算
3. idxChunkRows = FloorAlign(min(FloorDiv(idxBudget, idxRowBytes), numRowsPerCore), 8)；为 0 时回退 ORIG
4. kernel 新增 TBuf<VECCALC> 索引缓冲（仅 BULK 启用且对应 flag 时 InitBuffer），LoadIndexChunk 每 chunk 3 条 DataCopyPad + 一次 SetFlag/WaitFlag<MTE2_S> 同步，禁止 TQue 逐 chunk Alloc/EnQue/DeQue/Free
5. PrefetchRowScalarsUb 从 UB 读行标量，drop sentinel/eid OOB/scales 缺席语义与 GM 版逐条一致；尾块逐行回退 ORIG
6. 用'污染 UB 读值后精度仍通过'探针验证 BULK 分支确实执行（比读 profiling 更决定性），验证后移除探针
7. 分路径核对性能：BULK case 恢复既有批量实现收益（相对上轮不劣化），ORIG case 回 baseline±噪声，全 case >= 0.95

## 6. LLM 前置问题

- 目标实现是否满足：kernel 每行 O(K) 次逐元素标量 GM GetValue 读取索引/缩放数组且 Scalar 引擎主导（aiv_scalar_ratio >= 0.80）？
- 目标实现是否满足：host 可在 tiling 阶段计算 per-row traffic 并与回归/收益 case 分布存在可分离阈值（本例回归 case R*K {512..4036} < 4096 < 收益 case R*K {8184..262144}）？
- 目标实现是否满足：UB 实际剩余预算（按 kernel InitBuffer 实占计算）可容纳至少一个 8 行对齐索引 chunk？
- 是否命中排除条件：fp32 大流量 case：主循环 InitBuffer 占用（5 个 DT 槽 + fp32 累加器）几乎占满 UB，host 求解 chunk=0 自动回退 ORIG；且 fp32 数据搬运本身主导（case_2 对索引批量搬运无响应，R1/R3 均 ~1.006x），此边界在两个独立轮次复现？

## 7. 验收标准

正确性：

- rounds/003/verify.json: 20/20 passed，6 个 flag route（R-A full params / R-B no-skip2 / R-C no-skip / R-D no-bias / R-E no-scales K=1 / R-F 3D drop_pad mode0-3）全部精度通过
- 污染 UB 读值 (-12345) 探针使精度必然错误，20/20 通过即证明 BULK 分支未执行的静默失效被定位并修复（探针已移除）

性能：

- 总加速 1.1113x（2628.9us -> 2365.5us），improved_speedup >= 1.05 PASS、minimum_total_speedup >= 1.02 PASS、max_case_regression 最低 0.9637 >= 0.95 PASS，回归 case 列表为空
- 热 case（BULK）：case 15 1.115x、case 9 1.248x、case 8 1.137x、case 12 1.215x、case 4 1.213x、case 1 1.209x，恢复 D1 量级（D1 1.115-1.335x）
- 小 case（ORIG 门控）：case 6 1.006x、13 0.964x、14 1.016x、18 1.002x、5 1.026x、7 1.005x、10 0.977x，零回归
- case 2/3（R*K>=4096 但 fp32 无 UB 剩余 → chunk=0 → ORIG）1.006x/1.007x，与 R1 的 1.006x/1.001x 一致：fp32 数据搬运主导，对索引批量搬运无响应（负边界独立复现）

回滚信号：

- 任一 BULK case 相对既有批量实现 median 慢 >5%（载体退化或 UB 预算挤占）
- 任一 ORIG case 相对 baseline < 0.95x（门控误路由）
- 精度门禁失败（drop sentinel / eid OOB / bf16 scales 位级转换）
- 热 case 性能与 baseline 完全重合且精度全过：怀疑 chunk 行数超每核行数导致 BULK 静默关闭，用污染探针确认

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap

- moe_finalize_routing-20260826_014147-27927d（round=3, status=accepted）
- moe_finalize_routing-20260826_014147-27927d（round=3, status=accepted）
- moe_finalize_routing-20260902_124740-ebd397（round=2, status=accepted）

## 检索卡（短卡）

动作：将索引数组整块 MTE2 搬入常驻 UB TBuf；host 按每行流量门控，小流量保留原路径
适用：每行有 O(K) 次标量 GM GetValue 读取索引或缩放数组，且 Scalar 引擎主导
限制：idxChunkRows 按每核有效行数封顶；索引缓冲使用独立 UB 预算，不得挤占主循环 tile
范围：行切分 index-gather 的索引/缩放读取路径
检索词：MTE2、UB 常驻 TBuf、per-row traffic、独立 UB 预算、GetValue
机会：逐元素标量 GM GetValue 形成 Scalar 引擎瓶颈
代价：批量路径有固定开销，小流量需保留原实现
