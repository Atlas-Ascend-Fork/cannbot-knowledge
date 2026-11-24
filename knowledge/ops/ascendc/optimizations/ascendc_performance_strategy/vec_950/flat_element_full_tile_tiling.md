---
type: Optimization
title: foreach TensorList 元素平铺满 tile 化：消除细粒度 tiling 的 per-tile 开销伪影
description: 把细粒度 row/chunk tiling 改为每张量按满块容量平铺，1 segment/tile，32B 对齐走 DataCopy 快路。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/flat-element-full-tile-tiling.md
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
      "DataCopy/DataCopyPad blockLen 与 stride 的 uint16 字段上限；尾段对齐判定必须与 32B 快路条件一致，否则精度或 OOB",
      "TensorList meta memo 必须单调，否则退化为每 tile 重扫",
      "扁平寻址改写触碰全部 dtype/路由实例（16-bit 与 fp32 行为不同），须每路由 no-regression 验证"
    ],
    "excluded_conditions": [
      "单张量元素量已小（约 1-2M 元素、每核仅 2-3 tile）的 launch-floor case：tile 数无压缩空间，收益落入 launch/tiling-parse 结构性地板（本 run r4 证伪链，参 ELEM-SINGLE-TILE-TQUE-DIRECT-PATH-LIMITED-GAIN 同类边界）",
      "tile 放大致每核 loopTimes<2 且瓶颈在双缓冲重叠的形状（参 tile-enlarge-double-buffer-overlap-loss）",
      "存在不可折叠的内层 stride/广播语义时须保留分段寻址与对齐判定"
    ],
    "required_conditions": [
      "kernel 由 tilingData 完全参数化 tile 划分（tile 表可由 host 重写生效）",
      "满块字节数 F_max 受 UB 预算约束并留出双缓冲与辅助槽（253952B UB 按最大 dtype 实例化）",
      "元素总量远大于核数（tile 数可从数千压缩到每核个位数），形状可折叠为一维扁平段（无内层 stride 语义）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "9beecd073c1cd3f4b34fb422128ea06f2670b79f0a09879e181df96227feaa04",
      "decision_sha256": "39c38d97897cad640cd663d08f6c046c13ed09f720f22e7981f56606e3ed020a",
      "operator_class": "fused-composite",
      "performance_sha256": "863843d143f8f3ba4f180cf3839453485ef0ade0b5029685394bb8f156663470",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "b3e361e2dda4caaf1446c5e192462becec55b42606a6e9ad1db4d97ed0913fc2",
      "verify_sha256": "a3d33e91eb5396ac51090d27da5447859c6b78f09ab300571c74a2e4d41e4e12"
    },
    {
      "comparison_sha256": "d3c3e90f009459359c881ffe8df4f182d38f5d37aa6a3893c998ed6c5482c4c9",
      "decision_sha256": "39c38d97897cad640cd663d08f6c046c13ed09f720f22e7981f56606e3ed020a",
      "operator_class": "fused-composite",
      "performance_sha256": "863843d143f8f3ba4f180cf3839453485ef0ade0b5029685394bb8f156663470",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "b3e361e2dda4caaf1446c5e192462becec55b42606a6e9ad1db4d97ed0913fc2",
      "verify_sha256": "a3d33e91eb5396ac51090d27da5447859c6b78f09ab300571c74a2e4d41e4e12"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-tile-fixed-cost-artifact",
      "mte2-bandwidth-after-flattening"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "flat-element-full-tile",
    "structure": [
      "tensorlist-elementwise-stream"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-FLAT-ELEMENT-FULL-TILE-TILING",
  "implementation_steps": [
    "op_summary 确认墙形态：mte2_ratio 低而 tile 数千级（伪带宽墙），而非 MTE2 饱和",
    "host 重写 tile 表为每张量 CeilDiv(elems, F_max) 满块序列，保持 tiling 结构布局兼容",
    "kernel 改扁平段寻址：1 segment/tile，32B 对齐走 DataCopy，尾段 DataCopyPad；meta walk 单调 memoized",
    "全量 verify + 大小 case 分层对比：大 case 期望 10x+（去伪影），小 case 无回归（tile 数本已少）；官方路径 spot_check 复现最大 case 收益"
  ],
  "intent": "消除 per-tile 固定开销（TensorList desc/meta 标量载入、队列事件、Pad 事务、尾 chunk 残段）随 tile 数线性放大的伪影，让大 case 吞吐逼近 MTE2 带宽。",
  "mechanism": "host tiling 生成扁平 tile 表：每张量 perTensorTiles=CeilDiv(elems, F_max)，40B tiling 结构不变；kernel 按扁平段寻址，每 tile 1 个连续 segment，32B 对齐元素走 DataCopy 快路、非对齐尾段走 DataCopyPad；TensorList meta walk 单调 memoized（tile 序内每张量元数据至多失效一次）。",
  "name": "foreach TensorList 元素平铺满 tile 化：消除细粒度 tiling 的 per-tile 开销伪影",
  "operator_class": "fused-composite",
  "operator_scope": "多 TensorList foreach 型 elementwise 流（addcmul/div/scalar 融合类），host tiling 完全参数化 tile 划分且 kernel 可按扁平元素段寻址",
  "principle": "若 (固定成本/tile) x tile 数与数据搬运成本同量级，则 tile 数本身就是墙；在 UB 预算内把每核 tile 数压到个位数（满块直拷 + 对齐快路）比任何 issue 端重排（顺序 r1 / 指令数 r2 / desc+TQue 瘦身 r4，均证伪）更根本。",
  "related_anti_patterns": [],
  "risks": [
    "尾段 Pad 语义变化影响位精确性（对齐边界两侧 dtype size 不同时）",
    "F_max 过大使小张量活动核数下降，需确认 min(totalTileNum, coreNum) 覆盖",
    "probe 先行（tile 压缩预期最大的 case + dtype 覆盖 case）避免全量花费"
  ],
  "slug": "flat-element-full-tile-tiling",
  "summary": "当 row/chunk 细粒度 tiling 产生数千个微 tile + 尾 chunk + Pad 拷贝时，per-tile 固定成本本身成为伪带宽墙；改为每张量按满块容量平铺（perTensorTiles=CeilDiv(elems, F_max)，1 segment/tile，32B 对齐走 DataCopy 快路，单调 memoized meta walk）后墙移至真实 MTE2 聚合带宽（3.2-4.2 TB/s）。",
  "verification": {
    "correctness": [
      "official_eval correctness 20/20 全过（r3 轮与 final 两次复验）"
    ],
    "performance": [
      "incremental 49.03x（big-5 16-79x、16-bit 4.8-9.8x、mids 2-4.3x、smalls 1.6-2.2x），零回归（min 1.62x）；官方路径 spot_check 复现最大 case；final 官方 post_score 151.4405 vs pre_score 64.4555"
    ],
    "rollback_signals": [
      "任一 case 相对 parent <0.95x；精度失败；活动核数意外下降致小 case 回归"
    ]
  }
}
-->

# 性能优化策略：foreach TensorList 元素平铺满 tile 化：消除细粒度 tiling 的 per-tile 开销伪影

单一优化点：当 row/chunk 细粒度 tiling 产生数千个微 tile + 尾 chunk + Pad 拷贝时，per-tile 固定成本本身成为伪带宽墙；改为每张量按满块容量平铺（perTensorTiles=CeilDiv(elems, F_max)，1 segment/tile，32B 对齐走 DataCopy 快路，单调 memoized meta walk）后墙移至真实 MTE2 聚合带宽（3.2-4.2 TB/s）。

## 1. 原理

若 (固定成本/tile) x tile 数与数据搬运成本同量级，则 tile 数本身就是墙；在 UB 预算内把每核 tile 数压到个位数（满块直拷 + 对齐快路）比任何 issue 端重排（顺序 r1 / 指令数 r2 / desc+TQue 瘦身 r4，均证伪）更根本。

实现机制：host tiling 生成扁平 tile 表：每张量 perTensorTiles=CeilDiv(elems, F_max)，40B tiling 结构不变；kernel 按扁平段寻址，每 tile 1 个连续 segment，32B 对齐元素走 DataCopy 快路、非对齐尾段走 DataCopyPad；TensorList meta walk 单调 memoized（tile 序内每张量元数据至多失效一次）。

## 2. 性能问题模式

- 优化目标：消除 per-tile 固定开销（TensorList desc/meta 标量载入、队列事件、Pad 事务、尾 chunk 残段）随 tile 数线性放大的伪影，让大 case 吞吐逼近 MTE2 带宽。
- 适用数据流：多 TensorList foreach 型 elementwise 流（addcmul/div/scalar 融合类），host tiling 完全参数化 tile 划分且 kernel 可按扁平元素段寻址
- Feature signature：`{"bottleneck": ["per-tile-fixed-cost-artifact", "mte2-bandwidth-after-flattening"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "flat-element-full-tile", "structure": ["tensorlist-elementwise-stream"]}`

## 3. 正确性红线

- 尾段 Pad 语义变化影响位精确性（对齐边界两侧 dtype size 不同时）
- F_max 过大使小张量活动核数下降，需确认 min(totalTileNum, coreNum) 覆盖
- probe 先行（tile 压缩预期最大的 case + dtype 覆盖 case）避免全量花费

资源与硬件约束：

- DataCopy/DataCopyPad blockLen 与 stride 的 uint16 字段上限；尾段对齐判定必须与 32B 快路条件一致，否则精度或 OOB
- TensorList meta memo 必须单调，否则退化为每 tile 重扫
- 扁平寻址改写触碰全部 dtype/路由实例（16-bit 与 fp32 行为不同），须每路由 no-regression 验证

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- kernel 由 tilingData 完全参数化 tile 划分（tile 表可由 host 重写生效）
- 满块字节数 F_max 受 UB 预算约束并留出双缓冲与辅助槽（253952B UB 按最大 dtype 实例化）
- 元素总量远大于核数（tile 数可从数千压缩到每核个位数），形状可折叠为一维扁平段（无内层 stride 语义）

不适用：

- 单张量元素量已小（约 1-2M 元素、每核仅 2-3 tile）的 launch-floor case：tile 数无压缩空间，收益落入 launch/tiling-parse 结构性地板（本 run r4 证伪链，参 ELEM-SINGLE-TILE-TQUE-DIRECT-PATH-LIMITED-GAIN 同类边界）
- tile 放大致每核 loopTimes<2 且瓶颈在双缓冲重叠的形状（参 tile-enlarge-double-buffer-overlap-loss）
- 存在不可折叠的内层 stride/广播语义时须保留分段寻址与对齐判定

## 5. 实施步骤

1. op_summary 确认墙形态：mte2_ratio 低而 tile 数千级（伪带宽墙），而非 MTE2 饱和
2. host 重写 tile 表为每张量 CeilDiv(elems, F_max) 满块序列，保持 tiling 结构布局兼容
3. kernel 改扁平段寻址：1 segment/tile，32B 对齐走 DataCopy，尾段 DataCopyPad；meta walk 单调 memoized
4. 全量 verify + 大小 case 分层对比：大 case 期望 10x+（去伪影），小 case 无回归（tile 数本已少）；官方路径 spot_check 复现最大 case 收益

## 6. LLM 前置问题

- 目标实现是否满足：kernel 由 tilingData 完全参数化 tile 划分（tile 表可由 host 重写生效）？
- 目标实现是否满足：满块字节数 F_max 受 UB 预算约束并留出双缓冲与辅助槽（253952B UB 按最大 dtype 实例化）？
- 目标实现是否满足：元素总量远大于核数（tile 数可从数千压缩到每核个位数），形状可折叠为一维扁平段（无内层 stride 语义）？
- 是否命中排除条件：单张量元素量已小（约 1-2M 元素、每核仅 2-3 tile）的 launch-floor case：tile 数无压缩空间，收益落入 launch/tiling-parse 结构性地板（本 run r4 证伪链，参 ELEM-SINGLE-TILE-TQUE-DIRECT-PATH-LIMITED-GAIN 同类边界）？

## 7. 验收标准

正确性：

- official_eval correctness 20/20 全过（r3 轮与 final 两次复验）

性能：

- incremental 49.03x（big-5 16-79x、16-bit 4.8-9.8x、mids 2-4.3x、smalls 1.6-2.2x），零回归（min 1.62x）；官方路径 spot_check 复现最大 case；final 官方 post_score 151.4405 vs pre_score 64.4555

回滚信号：

- 任一 case 相对 parent <0.95x；精度失败；活动核数意外下降致小 case 回归

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- foreach_addcdiv_scalar-20260831_113139-72b284（round=3, status=accepted）
- foreach_addcdiv_scalar-20260831_113139-72b284（round=3, status=accepted）

## 检索卡（短卡）

动作：把细粒度 row/chunk tiling 改为每张量按满块容量平铺，1 segment/tile，32B 对齐走 DataCopy 快路
适用：kernel 由 tilingData 参数化、元素总量远大于核数、可折叠为一维扁平段
限制：blockLen/stride 受 uint16 上限，尾段对齐须与 32B 快路一致；memo 须单调
范围：fused-composite 的多 TensorList elementwise 流
检索词：满 tile 平铺、F_max、DataCopy 快路、DataCopyPad 尾段、meta memo
机会：数千微 tile 的 per-tile 固定开销（desc/meta、队列事件）成为伪带宽墙
代价：F_max 过大使小张量核数下降，须确认 min(totalTileNum,coreNum)
