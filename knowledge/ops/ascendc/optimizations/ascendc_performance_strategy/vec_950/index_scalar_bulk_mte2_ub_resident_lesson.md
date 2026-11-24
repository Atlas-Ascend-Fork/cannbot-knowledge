---
type: Optimization
title: 标量索引数组整块 MTE2 进 UB 替代逐元素 GetValue 的适用边界与 microkernel 回归
description: 将本核行块对应的 estdr/efsr/scales 索引片段按行块 chunk 整块 MTE2 搬入 UB 常驻 TBuf，PrefetchRowScalars 改读 UB LocalTensor.GetValue 替代逐元素标量 GM GetValue。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/index-scalar-bulk-mte2-ub-resident-lesson.md
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
      "DataCopyExtParams dstStride 语义：srcStride 单位 = bytes（GM 侧），dstStride 单位 = 32B datablocks（UB 侧）。列优先 2D 拷贝 blockLen 已 32B 对齐时 dstStride=0 正确（UB 自动 32B 对齐每块）。误用 dstStride=blockLen/32 会在每块后引入完整 block 间隙，导致 UB 空间加倍与 [1,0,1,0,...] 交替零值伪影（奇数 k 正确偶数 k 读到间隙零值）。参考 knowledge base atlasascendc_api_07_0265 Table 4",
      "host 侧 chunk 行数必须 8 对齐（FloorAlign to 8）以保证 blockLen 32B 对齐",
      "optional input 缺席时对应数组跳过拷贝，保持 flag 语义不变",
      "max_case_regression gate 阈值 0.95 对全部 case 生效（不区分目标/控制/非验证 case）"
    ],
    "excluded_conditions": [
      "microkernel noise-floor case（median < 15us, K=1 或小 fp32）：UB chunk 分配 + 2D 描述符发射固定开销在极小工作量下占比放大，产生 5-6% 单点回归（case 6: 0.944x, case 13: 0.944x, case 14: 0.947x, 均在 microkernel noise-floor 内且 stable, re_sampling_prohibited=true）",
      "K*rowsThisCore 低于阈值时不应启用 UB-chunk 路径（应回退原始 GM 逐元素路径）",
      "UB 预算不足以容纳 chunk + 现有 buffer 共存时（InitBuffer 断言失败或设备错误 507015）"
    ],
    "required_conditions": [
      "kernel 每行通过 PrefetchRowScalars 逐元素标量 GM GetValue 读取 3 个索引数组（estdr/efsr/scales），每行 3K 次离散 GM 标量访问",
      "baseline profile 显示 Scalar 引擎为主导瓶颈（aiv_scalar_ratio >= 0.80）",
      "UB 预算可容纳 3 个索引数组 chunk（idxChunkRows * K * (4+4+scaleBytes)）与现有 termQueue/biasQueue/outFp32Buf 共存",
      "estdr 两种编址（mode<=1 by-column k*R+rowIdx / mode>=2 by-row rowIdx*K+k）在行块内各自连续，可整块拷贝",
      "per-row 标量 GM GetValue 次数 = 3*K，当 K>=4 且 median > 50us 时收益覆盖固定开销"
    ]
  },
  "classification": "lesson",
  "evidence": [
    {
      "baseline_analysis": "baseline/analysis.md",
      "baseline_op_profile": "baseline/op_profile.json",
      "baseline_performance": "baseline/performance.json",
      "build": "rounds/001/build.json",
      "comparison": "rounds/001/comparison.json",
      "decision": "rounds/001/decision.json",
      "implementation": "rounds/001/implementation.md",
      "operator_class": "fused-composite",
      "performance": "rounds/001/performance.json",
      "review": "rounds/001/review.json",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy": "rounds/001/strategy.json",
      "verify": "rounds/001/verify.json"
    },
    {
      "comparison_sha256": "1bb4e4239b74ef68086721756f43b4f484aaa7bd76d353164063cc99859addc7",
      "decision_sha256": "bd820d8b046bdfec95c87d16b48d8f36dfafb9d71ae129ffedf392ac53862e71",
      "operator_class": "fused-composite",
      "performance_sha256": "4d01c140fbc42eb5c4befa970ba41c4b3605d3d6cea057ddc65cf3430feba7c5",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "31aa3e0ede6397c388e57d6c03a6b08e6ff8a6b35aa269fb5988602e04612ec7",
      "verify_sha256": "ebdea571d4e461e20e288687397072c5b5662fd40ea2ee11532cab78f20aab04"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-gm-getvalue-dominant",
      "ub-chunk-fixed-overhead-microkernel-regression"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "index-scalar-bulk-mte2-ub-resident",
    "structure": [
      "per-row-scalar-gm-getvalue",
      "row-block-chunk-mte2-to-ub",
      "ub-resident-localtensor-getvalue",
      "host-tiling-chunk-budget-solve",
      "datacopyextparams-dststride-semantics",
      "microkernel-noise-floor-non-retryable"
    ]
  },
  "generality": "op_class",
  "id": "L-MFR-D1-INDEX-SCALAR-BULK-MTE2",
  "implementation_steps": [
    "在 tiling_data struct 新增 uint32_t idxChunkRows 字段",
    "host 侧 tiling 计算 idxBudgetBytes = UB/4，idxChunkRows = FloorAlign(FloorDiv(budget, K*(8+scaleTypeSize)), 8)，从 usableUb 中减去 chunk footprint",
    "kernel 新增 estdrQue_/efsrQue_/scalesQue_ (TQue<VECIN, 1>)，在 InitBuffer 中分配",
    "实现 LoadIndexChunk：用 DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 整块 MTE2 搬入 UB。验证 dstStride=0 而非 blockLen/32，否则 UB 空间加倍与零值伪影",
    "实现 PrefetchRowScalarsUb：从 UB LocalTensor.GetValue 读取替代 GM GetValue",
    "chunk-aligned body 走 UB 路径，尾行回退 GM PrefetchRowScalars",
    "用 isolated per-config probe 验证 index chunk copy 正确性（非 [1,0,1,0,...] 交替零值模式）",
    "验证精度全过（drop sentinel -1 跳过、eid OOB 屏蔽、bf16 scales 位级转换）",
    "验证热 case 中位数提升 + 控制 case 无回归 + max_case_regression gate 通过",
    "后续轮次：加 host 侧 per-row traffic 阈值门控（K*rowsThisCore >= N_min），低流量 case 回退 GM 逐元素路径"
  ],
  "intent": "消除逐元素标量 GM GetValue 导致的 Scalar 引擎瓶颈（baseline aiv_scalar_ratio 0.80-0.998，case_15 共 786432 次标量 GM 读，非带宽受限 257GB/s），同时记录该机制的适用边界和实施陷阱",
  "mechanism": "host 侧 tiling 新增 idxChunkRows 字段：idxBudgetBytes = UB/4，idxChunkRows = FloorAlign(FloorDiv(budget, K*(8+scaleTypeSize)), 8)；从 usableUb 中减去 chunk footprint 后求解 ubFactorH。kernel 侧新增 estdrQue_/efsrQue_/scalesQue_ (depth-1 VECIN)，UB-resident LocalTensor views，LoadScaleFromUb/PrefetchRowScalarsUb/LoadIndexChunk/FreeIndexChunk 方法。LoadIndexChunk 用 DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 整块 MTE2 搬入 UB（dstStride=0 是列优先 2D 拷贝的正确值，UB 硬件自动 32B 对齐每块）。chunk-aligned body 通过 UB 路径读取索引（LocalTensor.GetValue），chunk 外尾行回退 GM PrefetchRowScalars。optional-input/mixed-dtype/drop-sentinel/eid-OOB 分支保持不变（use* flag 为 0 时跳过对应 chunk 数组拷贝）。",
  "name": "标量索引数组整块 MTE2 进 UB 替代逐元素 GetValue 的适用边界与 microkernel 回归",
  "operator_class": "fused-composite",
  "operator_scope": "行切分 kernel 中每行通过 PrefetchRowScalars 逐元素标量 GM GetValue 读取 estdr/efsr/scales 索引数组（每行 3K 次离散 GM 标量访问），baseline profile 显示 scalar_ratio 0.80-0.998 标量引擎主导的场景",
  "principle": "逐元素标量 GM GetValue 在 Scalar 引擎上完全串行化，每行 3K 次离散 GM 标量访问占据 kernel 主时间。将索引片段整块 MTE2 搬入 UB 后，逐元素标量 GM 读被替换为 UB LocalTensor.GetValue（UB 访问延迟远低于 GM 标量读），加上少量整块 MTE2 描述符（每 chunk 每数组 1 条），Scalar 引擎占比与时延显著下降。因果由热 case 的 median_us 与 scalar_ratio 变化证实。但该机制引入两类固定开销：(1) UB TBuf 分配（3 个 depth-1 TQue 各占 K*elemSize*idxChunkRows 字节，减少 usableUb 影响 ubFactorH 求解）；(2) 2D DataCopyExtParams 描述符发射（每 chunk 每数组 1 条 MTE2 命令）。在 microkernel 量级 case（<15us, K=1, 每行仅 3 次标量 GM 读），省下的标量时间仅 0.3-0.5us，而固定开销超过此收益，净回归 0.3-0.5us。该因果由 3 个回归 case 的 absolute_diff (0.338-0.532us) 与 gap to 0.95 threshold (0.027-0.050us) 证实。review 确认回归是真实固定开销导致，不是测量噪声 (stable=true, CV 0.017-0.121 均在阈值内)。",
  "related_anti_patterns": [
    "dk-split-scalar-address-remap"
  ],
  "risks": [
    "microkernel noise-floor case 回归：UB chunk 分配 + 2D 描述符发射固定开销在 <15us case 上占比放大 5-6%，触发 max_case_regression gate。3 个回归 case 均 stable=true 且在 microkernel noise-floor 内，re_sampling_prohibited=true，无法通过重采翻案",
    "DataCopyExtParams dstStride 误用为 blockLen/32：导致 UB 空间加倍（可能触发 UB 预算溢出）与 [1,0,1,0,...] 交替零值伪影（奇数 k 正确偶数 k 为零）。正确值为 dstStride=0（blockLen 已 32B 对齐时）",
    "从热 case 收益外推到全部 case：K=8 热 case 的 1.335x 不能证明 K=1 microkernel case 同样有效",
    "忽略 max_case_regression gate 对全部 case 生效：即使 3 个回归 case 是非验证 case (13/14)，gate 仍然适用",
    "UB 预算冲突：chunk footprint 与 termQueue/biasQueue/outFp32Buf 共存可能导致 InitBuffer 断言失败",
    "mode 0/1 (by-column) 行块编址错误导致 3D drop_pad case 结果错误"
  ],
  "slug": "index-scalar-bulk-mte2-ub-resident-lesson",
  "summary": "将本核行块对应的 estdr/efsr/scales 索引片段按行块 chunk 整块 MTE2 搬入 UB 常驻 TBuf，PrefetchRowScalars 改读 UB LocalTensor.GetValue 替代逐元素标量 GM GetValue。机制在热 case（traffic-heavy, scalar-bound）证明有效：case 15 1.115x、case 9 1.335x、case 8 1.216x、case 12 1.302x、case 4 1.298x、case 1 1.293x，总加速 1.125x，精度 20/20 通过。但 round 因 max_case_regression gate (>=0.95) 失败被 rejected：microkernel noise-floor case (6/13/14, baseline median 5.99-8.97us) 因 UB chunk 分配 + 2D 描述符发射固定开销在极小工作量下占比放大，产生 5-6% 单点回归 (0.944/0.944/0.947)，review 确认 3 个回归 case 均稳定 (stable=true, retry_recommended=false, re_sampling_prohibited=true)。实施中确认 DataCopyExtParams 的 dstStride 语义：列优先 2D 拷贝 dstStride=0 正确，误用 blockLen/32 导致 UB 空间加倍与零值伪影。后续轮次应在 host 侧加 per-row traffic 阈值门控，仅当 K*rowsThisCore >= N_min 时启用 UB-chunk 路径，低流量 case 回退原始 GM 逐元素路径。",
  "verification": {
    "correctness": [
      "verify.json: 20/20 passed (21.63s), 6 个 flag route (R-A full params, R-B no-skip2, R-C no-skip, R-D no-bias, R-E no-scales K=1, R-F 3D drop_pad mode1/3) 全部精度通过",
      "fingerprint (git_commit e919da1, git_diff_sha256 0b105653210a2448, kernel_hash 9eaebe55bc4ab17e) 在 build.json/verify.json/performance.json 间一致",
      "isolated per-config probes (R=1024 K=8 m=0, R=512 K=4 m=0, R=100 K=4 m=0, R=1009 K=4 m=0, R=8192 K=4 m=0, R=256 K=4 m=2, R=32768 K=8 m=0) 全部 bad=1/N（仅 raw-UB debug-dump row bad），确认 dstStride=0 列优先拷贝正确"
    ],
    "performance": [
      "总加速 1.125x (2628.9us -> 2336.6us)，improved_speedup gate (>=1.05) PASS, minimum_total_speedup gate (>=1.02) PASS",
      "热 case 正向: case 15 1.115x (1446.6->1297.4us), case 9 1.335x (312.5->234.2us), case 8 1.216x (189.1->155.5us), case 12 1.302x (50.9->39.1us), case 4 1.298x (49.2->37.9us), case 1 1.293x (45.3->35.0us)",
      "max_case_regression gate (>=0.95) FAIL: case 6 (R-E no-scales K=1) 0.944x (7.969->8.441us, +0.472us), case 13 (small fp32) 0.944x (8.910->9.442us, +0.532us), case 14 (small fp32) 0.947x (5.996->6.334us, +0.338us)",
      "3 个回归 case 均 stable=true, retry_recommended=false, gap to 0.95 threshold 0.027-0.050us, re_sampling_prohibited=true (microkernel noise-floor)",
      "target route aggregate 1.128x, control route aggregate 1.101x"
    ],
    "rollback_signals": [
      "max_case_regression < 0.95 触发 rollback（已执行 git checkout 回退至 baseline e919da1）",
      "精度门禁失败（drop sentinel / eid OOB / bf16 scales 位级转换任一语义回归）",
      "UB 预算冲突导致设备错误 507015 或 InitBuffer 断言失败",
      "出现 [1,0,1,0,...] 交替零值模式时检查 dstStride 是否误设为 blockLen/32"
    ]
  }
}
-->

# 性能优化策略：标量索引数组整块 MTE2 进 UB 替代逐元素 GetValue 的适用边界与 microkernel 回归

单一优化点：将本核行块对应的 estdr/efsr/scales 索引片段按行块 chunk 整块 MTE2 搬入 UB 常驻 TBuf，PrefetchRowScalars 改读 UB LocalTensor.GetValue 替代逐元素标量 GM GetValue。机制在热 case（traffic-heavy, scalar-bound）证明有效：case 15 1.115x、case 9 1.335x、case 8 1.216x、case 12 1.302x、case 4 1.298x、case 1 1.293x，总加速 1.125x，精度 20/20 通过。但 round 因 max_case_regression gate (>=0.95) 失败被 rejected：microkernel noise-floor case (6/13/14, baseline median 5.99-8.97us) 因 UB chunk 分配 + 2D 描述符发射固定开销在极小工作量下占比放大，产生 5-6% 单点回归 (0.944/0.944/0.947)，review 确认 3 个回归 case 均稳定 (stable=true, retry_recommended=false, re_sampling_prohibited=true)。实施中确认 DataCopyExtParams 的 dstStride 语义：列优先 2D 拷贝 dstStride=0 正确，误用 blockLen/32 导致 UB 空间加倍与零值伪影。后续轮次应在 host 侧加 per-row traffic 阈值门控，仅当 K*rowsThisCore >= N_min 时启用 UB-chunk 路径，低流量 case 回退原始 GM 逐元素路径。

## 1. 原理

逐元素标量 GM GetValue 在 Scalar 引擎上完全串行化，每行 3K 次离散 GM 标量访问占据 kernel 主时间。将索引片段整块 MTE2 搬入 UB 后，逐元素标量 GM 读被替换为 UB LocalTensor.GetValue（UB 访问延迟远低于 GM 标量读），加上少量整块 MTE2 描述符（每 chunk 每数组 1 条），Scalar 引擎占比与时延显著下降。因果由热 case 的 median_us 与 scalar_ratio 变化证实。但该机制引入两类固定开销：(1) UB TBuf 分配（3 个 depth-1 TQue 各占 K*elemSize*idxChunkRows 字节，减少 usableUb 影响 ubFactorH 求解）；(2) 2D DataCopyExtParams 描述符发射（每 chunk 每数组 1 条 MTE2 命令）。在 microkernel 量级 case（<15us, K=1, 每行仅 3 次标量 GM 读），省下的标量时间仅 0.3-0.5us，而固定开销超过此收益，净回归 0.3-0.5us。该因果由 3 个回归 case 的 absolute_diff (0.338-0.532us) 与 gap to 0.95 threshold (0.027-0.050us) 证实。review 确认回归是真实固定开销导致，不是测量噪声 (stable=true, CV 0.017-0.121 均在阈值内)。

实现机制：host 侧 tiling 新增 idxChunkRows 字段：idxBudgetBytes = UB/4，idxChunkRows = FloorAlign(FloorDiv(budget, K*(8+scaleTypeSize)), 8)；从 usableUb 中减去 chunk footprint 后求解 ubFactorH。kernel 侧新增 estdrQue_/efsrQue_/scalesQue_ (depth-1 VECIN)，UB-resident LocalTensor views，LoadScaleFromUb/PrefetchRowScalarsUb/LoadIndexChunk/FreeIndexChunk 方法。LoadIndexChunk 用 DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 整块 MTE2 搬入 UB（dstStride=0 是列优先 2D 拷贝的正确值，UB 硬件自动 32B 对齐每块）。chunk-aligned body 通过 UB 路径读取索引（LocalTensor.GetValue），chunk 外尾行回退 GM PrefetchRowScalars。optional-input/mixed-dtype/drop-sentinel/eid-OOB 分支保持不变（use* flag 为 0 时跳过对应 chunk 数组拷贝）。

## 2. 性能问题模式

- 优化目标：消除逐元素标量 GM GetValue 导致的 Scalar 引擎瓶颈（baseline aiv_scalar_ratio 0.80-0.998，case_15 共 786432 次标量 GM 读，非带宽受限 257GB/s），同时记录该机制的适用边界和实施陷阱
- 适用数据流：行切分 kernel 中每行通过 PrefetchRowScalars 逐元素标量 GM GetValue 读取 estdr/efsr/scales 索引数组（每行 3K 次离散 GM 标量访问），baseline profile 显示 scalar_ratio 0.80-0.998 标量引擎主导的场景
- Feature signature：`{"bottleneck": ["scalar-gm-getvalue-dominant", "ub-chunk-fixed-overhead-microkernel-regression"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "index-scalar-bulk-mte2-ub-resident", "structure": ["per-row-scalar-gm-getvalue", "row-block-chunk-mte2-to-ub", "ub-resident-localtensor-getvalue", "host-tiling-chunk-budget-solve", "datacopyextparams-dststride-semantics", "microkernel-noise-floor-non-retryable"]}`

## 3. 正确性红线

- microkernel noise-floor case 回归：UB chunk 分配 + 2D 描述符发射固定开销在 <15us case 上占比放大 5-6%，触发 max_case_regression gate。3 个回归 case 均 stable=true 且在 microkernel noise-floor 内，re_sampling_prohibited=true，无法通过重采翻案
- DataCopyExtParams dstStride 误用为 blockLen/32：导致 UB 空间加倍（可能触发 UB 预算溢出）与 [1,0,1,0,...] 交替零值伪影（奇数 k 正确偶数 k 为零）。正确值为 dstStride=0（blockLen 已 32B 对齐时）
- 从热 case 收益外推到全部 case：K=8 热 case 的 1.335x 不能证明 K=1 microkernel case 同样有效
- 忽略 max_case_regression gate 对全部 case 生效：即使 3 个回归 case 是非验证 case (13/14)，gate 仍然适用
- UB 预算冲突：chunk footprint 与 termQueue/biasQueue/outFp32Buf 共存可能导致 InitBuffer 断言失败
- mode 0/1 (by-column) 行块编址错误导致 3D drop_pad case 结果错误

资源与硬件约束：

- 硬件边界：结论采集自 ascend950 (Ascend950DT, 64 AIV 核), device 1
- DataCopyExtParams dstStride 语义：srcStride 单位 = bytes（GM 侧），dstStride 单位 = 32B datablocks（UB 侧）。列优先 2D 拷贝 blockLen 已 32B 对齐时 dstStride=0 正确（UB 自动 32B 对齐每块）。误用 dstStride=blockLen/32 会在每块后引入完整 block 间隙，导致 UB 空间加倍与 [1,0,1,0,...] 交替零值伪影（奇数 k 正确偶数 k 读到间隙零值）。参考 knowledge base atlasascendc_api_07_0265 Table 4
- host 侧 chunk 行数必须 8 对齐（FloorAlign to 8）以保证 blockLen 32B 对齐
- optional input 缺席时对应数组跳过拷贝，保持 flag 语义不变
- max_case_regression gate 阈值 0.95 对全部 case 生效（不区分目标/控制/非验证 case）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- kernel 每行通过 PrefetchRowScalars 逐元素标量 GM GetValue 读取 3 个索引数组（estdr/efsr/scales），每行 3K 次离散 GM 标量访问
- baseline profile 显示 Scalar 引擎为主导瓶颈（aiv_scalar_ratio >= 0.80）
- UB 预算可容纳 3 个索引数组 chunk（idxChunkRows * K * (4+4+scaleBytes)）与现有 termQueue/biasQueue/outFp32Buf 共存
- estdr 两种编址（mode<=1 by-column k*R+rowIdx / mode>=2 by-row rowIdx*K+k）在行块内各自连续，可整块拷贝
- per-row 标量 GM GetValue 次数 = 3*K，当 K>=4 且 median > 50us 时收益覆盖固定开销

不适用：

- microkernel noise-floor case（median < 15us, K=1 或小 fp32）：UB chunk 分配 + 2D 描述符发射固定开销在极小工作量下占比放大，产生 5-6% 单点回归（case 6: 0.944x, case 13: 0.944x, case 14: 0.947x, 均在 microkernel noise-floor 内且 stable, re_sampling_prohibited=true）
- K*rowsThisCore 低于阈值时不应启用 UB-chunk 路径（应回退原始 GM 逐元素路径）
- UB 预算不足以容纳 chunk + 现有 buffer 共存时（InitBuffer 断言失败或设备错误 507015）

## 5. 实施步骤

1. 在 tiling_data struct 新增 uint32_t idxChunkRows 字段
2. host 侧 tiling 计算 idxBudgetBytes = UB/4，idxChunkRows = FloorAlign(FloorDiv(budget, K*(8+scaleTypeSize)), 8)，从 usableUb 中减去 chunk footprint
3. kernel 新增 estdrQue_/efsrQue_/scalesQue_ (TQue<VECIN, 1>)，在 InitBuffer 中分配
4. 实现 LoadIndexChunk：用 DataCopyExtParams{blockCount=idxChunkRows, blockLen=K*elemSize, srcStride=srcGapBytes, dstStride=0} 整块 MTE2 搬入 UB。验证 dstStride=0 而非 blockLen/32，否则 UB 空间加倍与零值伪影
5. 实现 PrefetchRowScalarsUb：从 UB LocalTensor.GetValue 读取替代 GM GetValue
6. chunk-aligned body 走 UB 路径，尾行回退 GM PrefetchRowScalars
7. 用 isolated per-config probe 验证 index chunk copy 正确性（非 [1,0,1,0,...] 交替零值模式）
8. 验证精度全过（drop sentinel -1 跳过、eid OOB 屏蔽、bf16 scales 位级转换）
9. 验证热 case 中位数提升 + 控制 case 无回归 + max_case_regression gate 通过
10. 后续轮次：加 host 侧 per-row traffic 阈值门控（K*rowsThisCore >= N_min），低流量 case 回退 GM 逐元素路径

## 6. LLM 前置问题

- 目标实现是否满足：kernel 每行通过 PrefetchRowScalars 逐元素标量 GM GetValue 读取 3 个索引数组（estdr/efsr/scales），每行 3K 次离散 GM 标量访问？
- 目标实现是否满足：baseline profile 显示 Scalar 引擎为主导瓶颈（aiv_scalar_ratio >= 0.80）？
- 目标实现是否满足：UB 预算可容纳 3 个索引数组 chunk（idxChunkRows * K * (4+4+scaleBytes)）与现有 termQueue/biasQueue/outFp32Buf 共存？
- 是否命中排除条件：microkernel noise-floor case（median < 15us, K=1 或小 fp32）：UB chunk 分配 + 2D 描述符发射固定开销在极小工作量下占比放大，产生 5-6% 单点回归（case 6: 0.944x, case 13: 0.944x, case 14: 0.947x, 均在 microkernel noise-floor 内且 stable, re_sampling_prohibited=true）？

## 7. 验收标准

正确性：

- verify.json: 20/20 passed (21.63s), 6 个 flag route (R-A full params, R-B no-skip2, R-C no-skip, R-D no-bias, R-E no-scales K=1, R-F 3D drop_pad mode1/3) 全部精度通过
- fingerprint (git_commit e919da1, git_diff_sha256 0b105653210a2448, kernel_hash 9eaebe55bc4ab17e) 在 build.json/verify.json/performance.json 间一致
- isolated per-config probes (R=1024 K=8 m=0, R=512 K=4 m=0, R=100 K=4 m=0, R=1009 K=4 m=0, R=8192 K=4 m=0, R=256 K=4 m=2, R=32768 K=8 m=0) 全部 bad=1/N（仅 raw-UB debug-dump row bad），确认 dstStride=0 列优先拷贝正确

性能：

- 总加速 1.125x (2628.9us -> 2336.6us)，improved_speedup gate (>=1.05) PASS, minimum_total_speedup gate (>=1.02) PASS
- 热 case 正向: case 15 1.115x (1446.6->1297.4us), case 9 1.335x (312.5->234.2us), case 8 1.216x (189.1->155.5us), case 12 1.302x (50.9->39.1us), case 4 1.298x (49.2->37.9us), case 1 1.293x (45.3->35.0us)
- max_case_regression gate (>=0.95) FAIL: case 6 (R-E no-scales K=1) 0.944x (7.969->8.441us, +0.472us), case 13 (small fp32) 0.944x (8.910->9.442us, +0.532us), case 14 (small fp32) 0.947x (5.996->6.334us, +0.338us)
- 3 个回归 case 均 stable=true, retry_recommended=false, gap to 0.95 threshold 0.027-0.050us, re_sampling_prohibited=true (microkernel noise-floor)
- target route aggregate 1.128x, control route aggregate 1.101x

回滚信号：

- max_case_regression < 0.95 触发 rollback（已执行 git checkout 回退至 baseline e919da1）
- 精度门禁失败（drop sentinel / eid OOB / bf16 scales 位级转换任一语义回归）
- UB 预算冲突导致设备错误 507015 或 InitBuffer 断言失败
- 出现 [1,0,1,0,...] 交替零值模式时检查 dstStride 是否误设为 blockLen/32

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：dk-split-scalar-address-remap

- moe_finalize_routing-20260826_014147-27927d（round=1, status=rejected）
- moe_finalize_routing-20260826_014147-27927d（round=1, status=rejected）

## 检索卡（短卡）

动作：将索引片段整块 MTE2 搬入 UB，以 UB LocalTensor.GetValue 取代逐元素标量 GM 读取
适用：索引可整块搬入 UB，且固定搬运成本能被复用摊销
限制：须重新核对目标平台核心数、UB 容量和 API 支持范围，不得沿用单设备上限
范围：index-gather 的 estdr/efsr/scales 索引读取
检索词：MTE2、UB、LocalTensor.GetValue、Scalar 引擎依赖链、PrefetchRowScalars
机会：逐元素标量 GM GetValue 形成或可能形成 Scalar 引擎依赖链
代价：UB chunk 分配和二维描述符发射有固定开销，微小输入需单独验证
