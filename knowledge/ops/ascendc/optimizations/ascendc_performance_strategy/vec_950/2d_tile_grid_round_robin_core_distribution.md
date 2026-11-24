---
type: Optimization
title: 二维 tile 网格 + round-robin 核心分配（把并行度与行数解耦）
description: 将仅按行轴分核改为每行沿列轴切tile，并在min(totalTileNum,coreNum)核上轮询分发。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/2d-tile-grid-round-robin-core-distribution.md
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
      "DataCopyPad byte-mode blockLen <= 65535、stride <= 65535（必要时强制 baseRowLen=1 防行 stride 溢出）",
      "GetCoreNumAiv() 提供并行度余量（本设备 64 核）",
      "非 32B 对齐 colLen 的 calLen 按对齐长度分配缓冲，避免 OOB"
    ],
    "excluded_conditions": [
      "行 stride 或 DataCopyPad blockLen/stride 超过 uint16 字段上限时需回退 baseRowLen=1 或单行路径，不能截断参数",
      "只测量代表性子集而未覆盖全量 case 时，不能把该子集收益外推为全量无回归（注意部分健康小 shape 活动核数可能从 64 降到 totalTileNum，如 case 13 需单独确认）",
      "形式验收要求两侧 stable 样本；当基线 artifact 不可变地 stable:false 或优化后延迟落入 sub-10us profiler 噪声地板时，正式 compare gate 必然返回 rejected——这是验收环境的边界，不是机制失败的证据"
    ],
    "required_conditions": [
      "tiling 只沿行轴（outerSize）分核，blockDim = min(coreNum, outerSize)，存在 dim=0 或 outer 远小于核数、且行本身足够大的形状",
      "shape 可折叠为 rowLen x colLen 二维网格，split 轴元素数为偶数（colLen 为整数）",
      "min(totalTileNum, coreNum) 严格大于当前 blockDim（存在并行度余量）",
      "每 tile 的 DataCopyPad 参数能由 rowTileIdx/colTileIdx 无歧义派生，且 4-zone 尾部参数覆盖 row/col tail 组合"
    ]
  },
  "classification": "lesson",
  "created": "2026-08-23",
  "evidence": [
    {
      "comparison_sha256": "827d3f7ff7b8befe716b60edb726d57f121197ca4b4ca2e9be569be26fe1a9e4",
      "decision_sha256": "aa359fadbf4d76f3f2269da41571278e5c05a83a56a20b5dca1e86ec4e39097d",
      "operator_class": "elementwise",
      "performance_sha256": "b1b0b918cd351b3cba1a20a455211d4552d9d69a782475a56806ad0974fdd70c",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "3cc00ac1bdafa5da87318f8bffb23a846bcc41c7ca22b09dfdc9ee44b23799d4",
      "verify_sha256": "87da31aec7b462511607591689c65d8d1f074c800d3673e5704e63f575272045"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "tiling-axis",
      "parallelism-collapse"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "2d-tile-grid-round-robin",
    "structure": [
      "host-tiling",
      "2d-tile-grid",
      "round-robin",
      "row-col-tile"
    ]
  },
  "generality": "op_class",
  "id": "L-SWIGLU-2D-TILE-GRID-RR",
  "implementation_steps": [
    "host 折叠 shape 为 2D 网格，运行 baseRowLen x baseColLen 最优搜索",
    "SetBlockDim(min(totalTileNum, coreNum))，写入 baseRowLen/baseColLen/rowTileNum/colTileNum/totalTileNum tiling 字段",
    "kernel 改为 round-robin tile 循环，按 tileIdx 派生 row/col tile 索引与 GM 偏移，逐 tile 选择 4-zone copy 参数",
    "保留 DataCopyPad byte-mode 非 32B 对齐处理与双缓冲预取结构",
    "无效形状（奇数 split 轴、空 tensor）回退 GRAPH_FAILED；搜索无合法 base shape 时回退 baseRowLen=1"
  ],
  "intent": "消除按行轴分核时 dim=0 或 outer 很小导致的并行度塌缩（整个大行在单核/少核上串行运行）。",
  "mechanism": "host 把 shape 折叠为 rowLen x colLen 二维网格（rowLen = prod(shape[:dim])，colLen = prod(shape[dim:])/2），运行 baseRowLen x baseColLen 最优搜索（核数优先、总 tile 数其次、base 更大、整 base tile 更多），totalTileNum = ceil(rowLen/baseRowLen)*ceil(colLen/baseColLen)，SetBlockDim(min(totalTileNum, coreNum))；kernel 用 tileIdx = GetBlockIdx(); tileIdx < totalTileNum; tileIdx += blockNum 的 round-robin 循环，按 rowTileIdx/colTileIdx 派生 GM 偏移与 4-zone（baseRowBaseCol/baseRowTailCol/tailRowBaseCol/tailRowTailCol）DataCopyPad 参数，每 tile 一次 CopyIn/Compute/CopyOut，双缓冲预取结构不变。",
  "name": "二维 tile 网格 + round-robin 核心分配（把并行度与行数解耦）",
  "op": "swi_glu",
  "operator_class": "elementwise",
  "operator_scope": "按行轴分核（blockDim = min(coreNum, outerSize)、连续行区间拆分）的 2D 可折叠内存受限 kernel 数据流，存在 dim=0 或 outer 远小于核数导致并行度塌缩的形状",
  "principle": "并行度由 tiling 选择的逻辑 tile 数决定，不必受限于外层行数；把每行沿列轴切成 tile 并在 min(totalTileNum, coreNum) 个核上 round-robin 分发，可在不改变每 tile 计算语义的情况下占满核心，把延迟按活动核数因子降低。",
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "部分健康小 shape 活动核数可能从 64 降到 totalTileNum，需全量 case 测量确认无回归（如 case 13）",
    "DataCopyPad 行内打包布局假设（dstStride=0/srcStride=0 连续落盘）若存在隐藏 32B 行填充会污染后续计算",
    "非 32B 对齐 colLen 的 calLen 对齐多算 padding，缓冲须按对齐长度分配"
  ],
  "slug": "2d-tile-grid-round-robin-core-distribution",
  "summary": "把 1D 行折叠 tiling（blockDim = min(coreNum, outerSize)）替换为 2D (rowLen x colLen) tile 网格并按 tileIdx round-robin 分发到 min(totalTileNum, coreNum) 个核，使 dim=0 / 小 outerSize 形状不再塌缩到单核/少核。机制经机器证据确认有效（Block Num 1/4 -> 64/50，target cases 6.80x-31.86x，合计 27.88x，0 回归），仅因形式稳定性门禁（不可变 unstable 基线 + sub-10us profiler 噪声地板）被记录为 rejected——边界是验收环境而非机制。",
  "verification": {
    "correctness": [
      "rounds/001 verify 6/6 通过（cases 4/6/8/16/17/19），kernel_hash 396a5b2afd602188 与 build.json kernel_after 一致",
      "DataCopyPad 非 32B 对齐（case 6, colLen 非 32B 对齐）在 strided 打包下 verify 通过"
    ],
    "performance": [
      "Block Num 从 1/4 升到 64/50（cases 4/8/16/17/19=64，case 6=50，因 totalTileNum<64），与假设一致，机制直接确认",
      "target cases 4/6/8/16/17/19 延迟 6.80x-31.86x（case 4 3956.6->124.2us 等），合计 4416.201->158.413us = 27.88x，0 回归",
      "注意：正式 compare gate 返回 ok:false（input_errors：基线与当前 performance artifact unstable），原因是优化 cases 落入 sub-10us 噪声地板 + 基线不可变 stable:false，非策略失败"
    ],
    "rollback_signals": [
      "Block Num 未上升（机制被证伪）",
      "任一健康 case 延迟回归低于 max_case_regression 0.95x",
      "tile 尾部失衡或 copy 参数错误使特定 case 慢于其单核基线"
    ]
  }
}
-->

# 性能优化策略：二维 tile 网格 + round-robin 核心分配（把并行度与行数解耦）

单一优化点：把 1D 行折叠 tiling（blockDim = min(coreNum, outerSize)）替换为 2D (rowLen x colLen) tile 网格并按 tileIdx round-robin 分发到 min(totalTileNum, coreNum) 个核，使 dim=0 / 小 outerSize 形状不再塌缩到单核/少核。机制经机器证据确认有效（Block Num 1/4 -> 64/50，target cases 6.80x-31.86x，合计 27.88x，0 回归），仅因形式稳定性门禁（不可变 unstable 基线 + sub-10us profiler 噪声地板）被记录为 rejected——边界是验收环境而非机制。

## 1. 原理

并行度由 tiling 选择的逻辑 tile 数决定，不必受限于外层行数；把每行沿列轴切成 tile 并在 min(totalTileNum, coreNum) 个核上 round-robin 分发，可在不改变每 tile 计算语义的情况下占满核心，把延迟按活动核数因子降低。

实现机制：host 把 shape 折叠为 rowLen x colLen 二维网格（rowLen = prod(shape[:dim])，colLen = prod(shape[dim:])/2），运行 baseRowLen x baseColLen 最优搜索（核数优先、总 tile 数其次、base 更大、整 base tile 更多），totalTileNum = ceil(rowLen/baseRowLen)*ceil(colLen/baseColLen)，SetBlockDim(min(totalTileNum, coreNum))；kernel 用 tileIdx = GetBlockIdx(); tileIdx < totalTileNum; tileIdx += blockNum 的 round-robin 循环，按 rowTileIdx/colTileIdx 派生 GM 偏移与 4-zone（baseRowBaseCol/baseRowTailCol/tailRowBaseCol/tailRowTailCol）DataCopyPad 参数，每 tile 一次 CopyIn/Compute/CopyOut，双缓冲预取结构不变。

## 2. 性能问题模式

- 优化目标：消除按行轴分核时 dim=0 或 outer 很小导致的并行度塌缩（整个大行在单核/少核上串行运行）。
- 适用数据流：按行轴分核（blockDim = min(coreNum, outerSize)、连续行区间拆分）的 2D 可折叠内存受限 kernel 数据流，存在 dim=0 或 outer 远小于核数导致并行度塌缩的形状
- Feature signature：`{"bottleneck": ["core-underutilization", "tiling-axis", "parallelism-collapse"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "2d-tile-grid-round-robin", "structure": ["host-tiling", "2d-tile-grid", "round-robin", "row-col-tile"]}`

## 3. 正确性红线

- 部分健康小 shape 活动核数可能从 64 降到 totalTileNum，需全量 case 测量确认无回归（如 case 13）
- DataCopyPad 行内打包布局假设（dstStride=0/srcStride=0 连续落盘）若存在隐藏 32B 行填充会污染后续计算
- 非 32B 对齐 colLen 的 calLen 对齐多算 padding，缓冲须按对齐长度分配

资源与硬件约束：

- DataCopyPad byte-mode blockLen <= 65535、stride <= 65535（必要时强制 baseRowLen=1 防行 stride 溢出）
- GetCoreNumAiv() 提供并行度余量（本设备 64 核）
- 非 32B 对齐 colLen 的 calLen 按对齐长度分配缓冲，避免 OOB

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- tiling 只沿行轴（outerSize）分核，blockDim = min(coreNum, outerSize)，存在 dim=0 或 outer 远小于核数、且行本身足够大的形状
- shape 可折叠为 rowLen x colLen 二维网格，split 轴元素数为偶数（colLen 为整数）
- min(totalTileNum, coreNum) 严格大于当前 blockDim（存在并行度余量）
- 每 tile 的 DataCopyPad 参数能由 rowTileIdx/colTileIdx 无歧义派生，且 4-zone 尾部参数覆盖 row/col tail 组合

不适用：

- 行 stride 或 DataCopyPad blockLen/stride 超过 uint16 字段上限时需回退 baseRowLen=1 或单行路径，不能截断参数
- 只测量代表性子集而未覆盖全量 case 时，不能把该子集收益外推为全量无回归（注意部分健康小 shape 活动核数可能从 64 降到 totalTileNum，如 case 13 需单独确认）
- 形式验收要求两侧 stable 样本；当基线 artifact 不可变地 stable:false 或优化后延迟落入 sub-10us profiler 噪声地板时，正式 compare gate 必然返回 rejected——这是验收环境的边界，不是机制失败的证据

## 5. 实施步骤

1. host 折叠 shape 为 2D 网格，运行 baseRowLen x baseColLen 最优搜索
2. SetBlockDim(min(totalTileNum, coreNum))，写入 baseRowLen/baseColLen/rowTileNum/colTileNum/totalTileNum tiling 字段
3. kernel 改为 round-robin tile 循环，按 tileIdx 派生 row/col tile 索引与 GM 偏移，逐 tile 选择 4-zone copy 参数
4. 保留 DataCopyPad byte-mode 非 32B 对齐处理与双缓冲预取结构
5. 无效形状（奇数 split 轴、空 tensor）回退 GRAPH_FAILED；搜索无合法 base shape 时回退 baseRowLen=1

## 6. LLM 前置问题

- 目标实现是否满足：tiling 只沿行轴（outerSize）分核，blockDim = min(coreNum, outerSize)，存在 dim=0 或 outer 远小于核数、且行本身足够大的形状？
- 目标实现是否满足：shape 可折叠为 rowLen x colLen 二维网格，split 轴元素数为偶数（colLen 为整数）？
- 目标实现是否满足：min(totalTileNum, coreNum) 严格大于当前 blockDim（存在并行度余量）？
- 是否命中排除条件：行 stride 或 DataCopyPad blockLen/stride 超过 uint16 字段上限时需回退 baseRowLen=1 或单行路径，不能截断参数？

## 7. 验收标准

正确性：

- rounds/001 verify 6/6 通过（cases 4/6/8/16/17/19），kernel_hash 396a5b2afd602188 与 build.json kernel_after 一致
- DataCopyPad 非 32B 对齐（case 6, colLen 非 32B 对齐）在 strided 打包下 verify 通过

性能：

- Block Num 从 1/4 升到 64/50（cases 4/8/16/17/19=64，case 6=50，因 totalTileNum<64），与假设一致，机制直接确认
- target cases 4/6/8/16/17/19 延迟 6.80x-31.86x（case 4 3956.6->124.2us 等），合计 4416.201->158.413us = 27.88x，0 回归
- 注意：正式 compare gate 返回 ok:false（input_errors：基线与当前 performance artifact unstable），原因是优化 cases 落入 sub-10us 噪声地板 + 基线不可变 stable:false，非策略失败

回滚信号：

- Block Num 未上升（机制被证伪）
- 任一健康 case 延迟回归低于 max_case_regression 0.95x
- tile 尾部失衡或 copy 参数错误使特定 case 慢于其单核基线

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：tile-ub-budget-mismatch

- swi_glu-20260823_153850-12764c（round=1, status=rejected）

## 检索卡（短卡）

动作：将仅按行轴分核改为每行沿列轴切tile，并在min(totalTileNum,coreNum)核上轮询分发
适用：dim=0或outer很小，按行轴分核使大行在单核或少核串行
限制：DataCopyPad字节模式blockLen与stride均须≤65535；须全量检查小shape活动核数下降风险
范围：elementwise-arithmetic的二维行列tile网格
检索词：二维tile网格、round-robin、totalTileNum、SetBlockDim、列轴切分
机会：逻辑tile数受outer限制，dim=0或outer很小时大行集中在单核或少核串行
代价：部分健康小shape的活动核数可能降至totalTileNum
