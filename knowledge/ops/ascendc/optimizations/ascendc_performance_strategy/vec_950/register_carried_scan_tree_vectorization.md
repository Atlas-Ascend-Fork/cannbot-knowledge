---
type: Optimization
title: T1 连续轴前缀扫描的寄存器驻留向量化扫描树（Hillis-Steele）
description: 把 T1 快路径 per-element 串行扫描（每元素 ~11-12 条 1-lane 向量指令、向量宽度未利用，单核吞吐恒 ~100-114M elem/s/core）替换为寄存器驻留 Hillis-Steele 64-lane 前缀扫描树，每 64 元素块 O(1) 全宽指令。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/register-carried-scan-tree-vectorization.md
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
      "全块 load/store 必须 256B 对齐（blockStart 为 64 的倍数、4B dtype）；DIST_INTLV_B32 store 目标 int64 索引缓冲 32B 对齐",
      "全块 blockStart+64 <= tileLen 禁止越界；串行尾块用原 first-element store",
      "serial tail 读 carry slot 需 LocalMemBar<VEC_STORE, VEC_LOAD> 保证 store->load 可见"
    ],
    "excluded_conditions": [
      "短/非对齐 int32 扫描（如 scanLen=1013、5D [3,7,11,13,1013]、全零值的 case 15）：固定 per-tile 树设置与 DIST_INTLV_B32 store 未摊销，实测回归 0.7354x 超过 max_case_regression 0.95",
      "fp16/bf16/int8/int16（sizeof!=4）路径未向量化，采用原串行扫描（round 2 case 1/3/13/18 实测 ~1.0x 无变化）",
      "int64 输入路径走 ComputeScanPrefixVFRegImplI64，不在本机制范围内"
    ],
    "required_conditions": [
      "T1 模式（dimNorm == rank-1）且 sizeof(DX)==4（fp32/int32），tileLen >= 64（扫描树 64-lane 块对齐 + 串行尾）",
      "running-min/argmin 可跨 tile 经 32B 对齐 UB carry 槽交接（现有契约保持不变）",
      "LE 并列（后出现索引胜）与 fp32 NaN sticky 语义在 tree combine 规则中显式保留"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "comparison_sha256": "0fc51962a04db4aacabedefbf1231007d91c30b203627ba6490d0b3ca48f2929",
      "decision_sha256": "81ab898091c70e65e06b08e917ed997f352a419980c01026cddc2bc188c3381d",
      "operator_class": "reduction",
      "performance_sha256": "62636f77a5d209f6add92fba177aa599d1aa17721f6780cf32542fd9661ccd6e",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "998ab59e60ec88eddb9021a27bd1c23fe85359c6100e718a479dd1fba8ec6d15",
      "verify_sha256": "0dd0a8cf0d03569e8472e367b8f27d5cc6d01be5ffc4914022464e20a982d47d"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-serial-scan",
      "instruction-issue-bound",
      "vector-width-unused"
    ],
    "pattern": "register-carried-scan-tree",
    "structure": [
      "t1-contiguous-axis-scan",
      "hillis-steele-64-lane",
      "reg-carried-carry",
      "int32-in-register"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-REG-CARRIED-VECTORIZED-TREE",
  "implementation_steps": [
    "在 ComputeScanPrefixVFRegImpl 分派 sizeof(DX)==4 && tileLen>=64 -> 扫描树 + 串行尾；否则原串行扫描",
    "把原 per-element 串行循环重构为 SerialScanVFRegRangeImpl 供尾块与非 4-byte 回退使用",
    "预构建 clamp 索引寄存器 gi_d[i]=max(i-d,0)（d=1,2,4,8,16,32）与 sentinel 初始化",
    "实现 ScanTreeStep64：Gather + Compare<LE>（fp32 加 NaN Compare<NE>/MaskOr）+ Select 值/索引",
    "每个 64 元素块用双寄存器 DIST_INTLV_B32 store 写出 int64 索引；tile 边界 carry 交接不变"
  ],
  "intent": "消除 T1 快路径 per-element 串行扫描的指令发射受限（每元素 ~12 条 1-lane 向量指令只处理 1 个 lane），把单核吞吐从恒 ~100M elem/s/core 提升到全向量扫描",
  "mechanism": "sizeof(DX)==4 && tileLen>=64 时：runValReg/runIdxReg 全宽 RegTensor 跨块与跨 tile 驻留；每个 64 元素块做 6 步 tree（Gather vselr 右移 + Compare<LE> + fp32 NaN Compare<NE>/MaskOr + Select 值 + Gather 索引 + Select 索引）+ 一次 carry-apply + 两次全块 store；int64 索引块用单条双寄存器 StoreAlign<uint32, DIST_INTLV_B32>（low=runIdx, high=sign-extended）；lane 用预计算 clamp 索引寄存器 gi_d[i]=max(i-d,0)（d=1,2,4,8,16,32）与 +inf/INT_MAX sentinel 使无效 lane 永不赢；串行尾块与非 4-byte dtype（fp16/bf16/int8/int16）保留原 per-element 扫描；tile 边界 carry 经 32B 对齐 UB 槽交接不变",
  "name": "T1 连续轴前缀扫描的寄存器驻留向量化扫描树（Hillis-Steele）",
  "operator_class": "reduction",
  "operator_scope": "连续末轴前缀扫描（dimNorm == rank-1，T1 快路径）的 reduction 类算子 fp32/int32（sizeof(DX)==4）且 tileLen>=64 路径；running-min/argmin 在 full-width 寄存器中跨块/跨 tile 驻留",
  "origin": {
    "candidate_id": "CUM-1",
    "evidence_status": "tested-rejected",
    "note": "Derived from baseline/reference-extraction/strategy_candidates.json CUM-1 and the reference register-carried DoCompare row scan (reference-source/op_kernel/arch35/cummin.h:419-506, 296-323). Round 2 tested and rolled back (patch.diff, rollback.json); 8/8 correctness, large aligned fp32/int32 gains 2.29-3.03x and neutral fp16/bf16 (~1.0x), but a genuine short/unaligned int32 regression (case 15, 0.7354x, stable samples) plus frozen baseline instability. Do not adopt as-is; scope to large aligned scans above an amortization threshold.",
    "reference_label": "mainline-cann",
    "type": "reference_diff"
  },
  "principle": "前缀扫描的 running-min/argmin 可携带在 full-width 寄存器中跨扫描驻留；Hillis-Steele 扫描树把 per-element 串行 O(n) 指令降为 per-64-block O(log n) 全宽向量步。LE 并列（right wins on <=，后出现索引胜）与 fp32 NaN sticky 语义在 combine 规则中显式保留，可在指令/延迟受限的串行扫描上获得与向量宽度成比例的加速。",
  "related_anti_patterns": [],
  "risks": [
    "DIST_INTLV_B32 交错顺序假设 (src0,src1) 为 int64 低/高 word；若相反则索引损坏（只被正确性 gate 捕获）",
    "case 15（int32, 5D [3,7,11,13,1013], scanLen=1013, 非对齐, 全零值）实测回归 0.7354x（round 样本稳定 cv=0.000811, relative_mad=0.000310）——固定 per-tile 树设置/DIST_INTLV_B32 store 在短扫描长度未摊销，不能按现状整体采用",
    "Gather/vselr issue 成本与 L0 datapath 未测量；fp16/bf16 128-lane 树未采用（跨半索引移位正确性风险高）"
  ],
  "slug": "register-carried-scan-tree-vectorization",
  "summary": "把 T1 快路径 per-element 串行扫描（每元素 ~11-12 条 1-lane 向量指令、向量宽度未利用，单核吞吐恒 ~100-114M elem/s/core）替换为寄存器驻留 Hillis-Steele 64-lane 前缀扫描树，每 64 元素块 O(1) 全宽指令。round 2 实测大对齐 fp32/int32 扫描 2.29-3.03x、fp16/bf16 未改路径 ~1.0x，但短非对齐 int32（case 15，scanLen=1013）真实回归 0.7354x（稳定样本）——边界：固定 per-tile 树设置与 DIST_INTLV_B32 双寄存器 int64 索引 store 在短扫描长度未摊销（详见 verification）。",
  "verification": {
    "correctness": [
      "round 2 verify ok=true，8/8 目标 case（1,2,3,4,6,13,15,18）通过；kernel_hash 5467ec1ce35cf9ad 与 build.json kernel_after 一致，git_diff_sha256 ce534d2b0d61940b",
      "LE 并列（后出现索引胜）+ fp32 NaN sticky + int64 索引值精确（low/high word）"
    ],
    "performance": [
      "大对齐 fp32/int32 扫描（round 样本全稳定）：case 2（fp32）591.2 -> 206.0us（2.87x）、case 4（int32）6083.4 -> 2662.4us（2.29x）、case 6（fp32）9272.4 -> 3063.2us（3.03x）",
      "fp16/bf16 未改路径 case 1/3/13/18 ~1.0x（无回归无提升）；case 15（int32 短非对齐）296.9 -> 403.8us（0.7354x）真实回归；target total_speedup 1.7372",
      "形式 comparison ok=false（冻结基线 case 8 不稳定 + case 15 回归），收益为指示性而非正式接受；机制按边界记录为 negative_boundary"
    ],
    "rollback_signals": [
      "任一 case 正确性失败（NaN-sticky/tie-break 顺序或 mask 粒度回归、索引损坏）",
      "case 15 类短/非对齐 int32 几何回归低于 max_case_regression 0.95",
      "T2 guard case（5,8,10,14,17,19）或非目标 T1 case 回归超噪声"
    ]
  }
}
-->

# 性能优化策略：T1 连续轴前缀扫描的寄存器驻留向量化扫描树（Hillis-Steele）

单一优化点：把 T1 快路径 per-element 串行扫描（每元素 ~11-12 条 1-lane 向量指令、向量宽度未利用，单核吞吐恒 ~100-114M elem/s/core）替换为寄存器驻留 Hillis-Steele 64-lane 前缀扫描树，每 64 元素块 O(1) 全宽指令。round 2 实测大对齐 fp32/int32 扫描 2.29-3.03x、fp16/bf16 未改路径 ~1.0x，但短非对齐 int32（case 15，scanLen=1013）真实回归 0.7354x（稳定样本）——边界：固定 per-tile 树设置与 DIST_INTLV_B32 双寄存器 int64 索引 store 在短扫描长度未摊销（详见 verification）。

## 1. 原理

前缀扫描的 running-min/argmin 可携带在 full-width 寄存器中跨扫描驻留；Hillis-Steele 扫描树把 per-element 串行 O(n) 指令降为 per-64-block O(log n) 全宽向量步。LE 并列（right wins on <=，后出现索引胜）与 fp32 NaN sticky 语义在 combine 规则中显式保留，可在指令/延迟受限的串行扫描上获得与向量宽度成比例的加速。

实现机制：sizeof(DX)==4 && tileLen>=64 时：runValReg/runIdxReg 全宽 RegTensor 跨块与跨 tile 驻留；每个 64 元素块做 6 步 tree（Gather vselr 右移 + Compare<LE> + fp32 NaN Compare<NE>/MaskOr + Select 值 + Gather 索引 + Select 索引）+ 一次 carry-apply + 两次全块 store；int64 索引块用单条双寄存器 StoreAlign<uint32, DIST_INTLV_B32>（low=runIdx, high=sign-extended）；lane 用预计算 clamp 索引寄存器 gi_d[i]=max(i-d,0)（d=1,2,4,8,16,32）与 +inf/INT_MAX sentinel 使无效 lane 永不赢；串行尾块与非 4-byte dtype（fp16/bf16/int8/int16）保留原 per-element 扫描；tile 边界 carry 经 32B 对齐 UB 槽交接不变

## 2. 性能问题模式

- 优化目标：消除 T1 快路径 per-element 串行扫描的指令发射受限（每元素 ~12 条 1-lane 向量指令只处理 1 个 lane），把单核吞吐从恒 ~100M elem/s/core 提升到全向量扫描
- 适用数据流：连续末轴前缀扫描（dimNorm == rank-1，T1 快路径）的 reduction 类算子 fp32/int32（sizeof(DX)==4）且 tileLen>=64 路径；running-min/argmin 在 full-width 寄存器中跨块/跨 tile 驻留
- Feature signature：`{"bottleneck": ["scalar-serial-scan", "instruction-issue-bound", "vector-width-unused"], "pattern": "register-carried-scan-tree", "structure": ["t1-contiguous-axis-scan", "hillis-steele-64-lane", "reg-carried-carry", "int32-in-register"]}`

## 3. 正确性红线

- DIST_INTLV_B32 交错顺序假设 (src0,src1) 为 int64 低/高 word；若相反则索引损坏（只被正确性 gate 捕获）
- case 15（int32, 5D [3,7,11,13,1013], scanLen=1013, 非对齐, 全零值）实测回归 0.7354x（round 样本稳定 cv=0.000811, relative_mad=0.000310）——固定 per-tile 树设置/DIST_INTLV_B32 store 在短扫描长度未摊销，不能按现状整体采用
- Gather/vselr issue 成本与 L0 datapath 未测量；fp16/bf16 128-lane 树未采用（跨半索引移位正确性风险高）

资源与硬件约束：

- 全块 load/store 必须 256B 对齐（blockStart 为 64 的倍数、4B dtype）；DIST_INTLV_B32 store 目标 int64 索引缓冲 32B 对齐
- 全块 blockStart+64 <= tileLen 禁止越界；串行尾块用原 first-element store
- serial tail 读 carry slot 需 LocalMemBar<VEC_STORE, VEC_LOAD> 保证 store->load 可见

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- T1 模式（dimNorm == rank-1）且 sizeof(DX)==4（fp32/int32），tileLen >= 64（扫描树 64-lane 块对齐 + 串行尾）
- running-min/argmin 可跨 tile 经 32B 对齐 UB carry 槽交接（现有契约保持不变）
- LE 并列（后出现索引胜）与 fp32 NaN sticky 语义在 tree combine 规则中显式保留

不适用：

- 短/非对齐 int32 扫描（如 scanLen=1013、5D [3,7,11,13,1013]、全零值的 case 15）：固定 per-tile 树设置与 DIST_INTLV_B32 store 未摊销，实测回归 0.7354x 超过 max_case_regression 0.95
- fp16/bf16/int8/int16（sizeof!=4）路径未向量化，采用原串行扫描（round 2 case 1/3/13/18 实测 ~1.0x 无变化）
- int64 输入路径走 ComputeScanPrefixVFRegImplI64，不在本机制范围内

## 5. 实施步骤

1. 在 ComputeScanPrefixVFRegImpl 分派 sizeof(DX)==4 && tileLen>=64 -> 扫描树 + 串行尾；否则原串行扫描
2. 把原 per-element 串行循环重构为 SerialScanVFRegRangeImpl 供尾块与非 4-byte 回退使用
3. 预构建 clamp 索引寄存器 gi_d[i]=max(i-d,0)（d=1,2,4,8,16,32）与 sentinel 初始化
4. 实现 ScanTreeStep64：Gather + Compare<LE>（fp32 加 NaN Compare<NE>/MaskOr）+ Select 值/索引
5. 每个 64 元素块用双寄存器 DIST_INTLV_B32 store 写出 int64 索引；tile 边界 carry 交接不变

## 6. LLM 前置问题

- 目标实现是否满足：T1 模式（dimNorm == rank-1）且 sizeof(DX)==4（fp32/int32），tileLen >= 64（扫描树 64-lane 块对齐 + 串行尾）？
- 目标实现是否满足：running-min/argmin 可跨 tile 经 32B 对齐 UB carry 槽交接（现有契约保持不变）？
- 目标实现是否满足：LE 并列（后出现索引胜）与 fp32 NaN sticky 语义在 tree combine 规则中显式保留？
- 是否命中排除条件：短/非对齐 int32 扫描（如 scanLen=1013、5D [3,7,11,13,1013]、全零值的 case 15）：固定 per-tile 树设置与 DIST_INTLV_B32 store 未摊销，实测回归 0.7354x 超过 max_case_regression 0.95？

## 7. 验收标准

正确性：

- round 2 verify ok=true，8/8 目标 case（1,2,3,4,6,13,15,18）通过；kernel_hash 5467ec1ce35cf9ad 与 build.json kernel_after 一致，git_diff_sha256 ce534d2b0d61940b
- LE 并列（后出现索引胜）+ fp32 NaN sticky + int64 索引值精确（low/high word）

性能：

- 大对齐 fp32/int32 扫描（round 样本全稳定）：case 2（fp32）591.2 -> 206.0us（2.87x）、case 4（int32）6083.4 -> 2662.4us（2.29x）、case 6（fp32）9272.4 -> 3063.2us（3.03x）
- fp16/bf16 未改路径 case 1/3/13/18 ~1.0x（无回归无提升）；case 15（int32 短非对齐）296.9 -> 403.8us（0.7354x）真实回归；target total_speedup 1.7372
- 形式 comparison ok=false（冻结基线 case 8 不稳定 + case 15 回归），收益为指示性而非正式接受；机制按边界记录为 negative_boundary

回滚信号：

- 任一 case 正确性失败（NaN-sticky/tie-break 顺序或 mask 粒度回归、索引损坏）
- case 15 类短/非对齐 int32 几何回归低于 max_case_regression 0.95
- T2 guard case（5,8,10,14,17,19）或非目标 T1 case 回归超噪声

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260823_213117-d2da41（round=2, status=rejected）

## 检索卡（短卡）

动作：将逐元素串行扫描改为寄存器驻留的64-lane Hillis-Steele全宽扫描树，尾部串行处理并保持LE后索引胜。
适用：T1末轴路径，DX为4字节且tileLen≥64。
限制：全块搬运须256B对齐；DIST_INTLV_B32须保持低/高word顺序。
范围：scan-reduce的T1连续末轴前缀扫描。
检索词：running-min/argmin、Hillis-Steele扫描树、全宽寄存器、串行尾。
机会：T1快路径仍以大量单lane指令逐元素串行扫描。
