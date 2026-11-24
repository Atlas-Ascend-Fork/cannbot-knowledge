---
type: Optimization
title: In-kernel self-select 激活 latent 向量排序路径
description: 在 kernel Init 中镜像已验证的 K1/K3 自选择模式：按可靠的运行时字段（sortLen/k/largest/chunkLen/dtype）在 kernel 内自选 useVectorSort_=1，激活 kernel 内已存在但宿主 tiling 未分发的 T1 ES1 向量排序路径；不匹配时逐字节回退原标量路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-inkernel-selfselect-latent-vecsort.md
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
      "self-select 赋值必须在 vectorSortPath 缓冲分配之前执行",
      "不匹配时必须逐字节回退原标量路径，不得改动任何路径内部逻辑"
    ],
    "excluded_conditions": [
      "dtype 不在向量路径支持集（如 int64 被 host gate 8.5 排除）",
      "整行 Sort 的 LCM 超过 kLcmReserve（如 bf16 [4096] 行 LCM 70144 > 68608）——需改用分块路径而非直接 self-select",
      "case 运行时已由其他机制路由到向量路径（重复激活无收益）"
    ],
    "required_conditions": [
      "kernel 内已存在被 host gate 字段选择的完整向量 top-k 路径（AscendC::TopK RADIX_SELECT / AscendC::Sort RADIX）",
      "运行时字段 sortLen/k/largest/chunkLen/dtype 可靠可解码",
      "目标 case geometry 满足向量路径的 UB 峰值与 32B 对齐约束"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "cb77cf7a9f5548ab9c409b15284dd8cefb95003c39d4128f41c8db741f606e05",
      "decision_sha256": "a635aa4df15887b7e43eb4fe3eefda9a93708c35c0798d5b29d656e0fae74b57",
      "operator_class": "sort-select",
      "performance_sha256": "a0f308fe630ff21ea9625d95e4c2ec4a3b0e1bb9b01cca2935ff7600c16d3280",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "15e90474a3e3461584bc41e7293732476b9cd9d9cb57be349e27a42f2a3ebbc9",
      "verify_sha256": "3597b2ac576875a2f9b88a6e7c664278c7136a018aa6624d476ef351c75d9605"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bounded-heap-when-vector-path-latent",
      "host-gate-not-honored"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32",
      "uint8"
    ],
    "pattern": "inkernel-selfselect-latent-vecsort",
    "structure": [
      "t1-es1-whole-row",
      "vector-sort-latent-path"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-INKERNEL-SELFSELECT-LATENT-VECSORT",
  "implementation_steps": [
    "确认目标 case 的运行时 route 与 dtype，读取 op_summary 确认 aiv_vec=0（向量路径未激活）",
    "在 Init 解码可靠运行时字段后添加 self-select gate（route/chunkLen/dtype/sortLen/k/对齐/UB）",
    "把 self-select 放在向量路径缓冲分配之前，复用既有 topkTmpBuf_/topKIdxBuf_",
    "单 case probe 验证激活后走向量路径且正确性不变",
    "全量 verify + measure + 官方路径 spot_check 确认无控制回归"
  ],
  "intent": "消除宿主 useVectorSort tiling 字段运行时未生效导致的错误标量有界堆（baseline aiv_scalar 0.71-1.0 / vec 0.0-0.26）——已有向量路径被闲置，case 在标量堆上空耗。",
  "mechanism": "Init 中解码 sortLen/k/largest/chunkLen/dtype 后设 useVectorSort_=1，条件：route==1 && chunkLen==0 && dtype∈{half,float,uint8,bf16} && (k*5>=sortLen || sortLen∈[512,4096]) && k*sT 与 k*8 均 32B 对齐 && UB 峰值可容纳；self-select 必须放在 vectorSortPath 缓冲分配（topkTmpBuf_/topKIdxBuf_）之前。",
  "name": "In-kernel self-select 激活 latent 向量排序路径",
  "operator_class": "sort-select",
  "operator_scope": "top_k T1 ES1 整行 case：kernel 内已编译进完整向量 top-k 路径（AscendC::TopK RADIX_SELECT / AscendC::Sort RADIX），但宿主设置的 useVectorSort tiling gate 在运行时未被遵守导致错误落入标量有界堆。",
  "principle": "当 kernel 二进制内已含完整向量 top-k 路径、只是宿主分发的 gate 字段运行时不被遵守时，可以在 kernel Init 依据可靠的 shape/dtype 字段自行路由到该路径，消除对宿主 tiling 正确性的依赖；回退保持逐字节一致则零编辑风险。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize"
  ],
  "risks": [
    "gate 过宽会把低收益 case（k 很小或 sortLen 超 LCM 预算）导入向量路径造成回归",
    "REAL regression observed: case_19 (uint8 [4097,511] k=256 sortLen=511, highRatio 1280>=511 fires) 从标量堆（baseline aiv_scalar 0.89, 400us）被导入 RADIX_SELECT 后 ~2x 变慢（official 792.8us 可复现）。highRatio 单独不足以保证向量路径收益，需 dtype×sortLen 联合约束或对每个控制 case 做官方路径 spot_check。",
    "LCM/UB 预算判断错误会导致编译失败或设备错误 507035",
    "依赖运行时字段的稳定性，shape 解析错误会误路由",
    "measure.py 轮次窗口可能把真实回归误报为环境噪声——控制 case 必须用官方路径 spot_check 复核"
  ],
  "slug": "topk-inkernel-selfselect-latent-vecsort",
  "summary": "在 kernel Init 中镜像已验证的 K1/K3 自选择模式：按可靠的运行时字段（sortLen/k/largest/chunkLen/dtype）在 kernel 内自选 useVectorSort_=1，激活 kernel 内已存在但宿主 tiling 未分发的 T1 ES1 向量排序路径；不匹配时逐字节回退原标量路径。",
  "verification": {
    "correctness": [
      "verify 20/20 通过；未激活 case 逐字节回退",
      "case_9 官方路径 spot_check 125.5us 可复现（measure 116.7us）"
    ],
    "performance": [
      "case_9 3748.7us -> 116.7us（measure）/ 125.5us（official-path）≈30x",
      "score_model 边际 +0.23 官方 pts（estimate；官方 final eval 为准）"
    ],
    "rollback_signals": [
      "任何 case 在向量路径上相对原标量路径真实回归即收紧 gate 回退",
      "spot_check verdict=not_reproducible 时回退",
      "case_19 型回归（uint8 sortLen~511 k~256 被 highRatio 导入向量路径 ~2x 变慢）触发时收紧 gate（如排除 uint8 低 sortLen 几何）"
    ]
  }
}
-->

# 性能优化策略：In-kernel self-select 激活 latent 向量排序路径

单一优化点：在 kernel Init 中镜像已验证的 K1/K3 自选择模式：按可靠的运行时字段（sortLen/k/largest/chunkLen/dtype）在 kernel 内自选 useVectorSort_=1，激活 kernel 内已存在但宿主 tiling 未分发的 T1 ES1 向量排序路径；不匹配时逐字节回退原标量路径。

## 1. 原理

当 kernel 二进制内已含完整向量 top-k 路径、只是宿主分发的 gate 字段运行时不被遵守时，可以在 kernel Init 依据可靠的 shape/dtype 字段自行路由到该路径，消除对宿主 tiling 正确性的依赖；回退保持逐字节一致则零编辑风险。

实现机制：Init 中解码 sortLen/k/largest/chunkLen/dtype 后设 useVectorSort_=1，条件：route==1 && chunkLen==0 && dtype∈{half,float,uint8,bf16} && (k*5>=sortLen || sortLen∈[512,4096]) && k*sT 与 k*8 均 32B 对齐 && UB 峰值可容纳；self-select 必须放在 vectorSortPath 缓冲分配（topkTmpBuf_/topKIdxBuf_）之前。

## 2. 性能问题模式

- 优化目标：消除宿主 useVectorSort tiling 字段运行时未生效导致的错误标量有界堆（baseline aiv_scalar 0.71-1.0 / vec 0.0-0.26）——已有向量路径被闲置，case 在标量堆上空耗。
- 适用数据流：top_k T1 ES1 整行 case：kernel 内已编译进完整向量 top-k 路径（AscendC::TopK RADIX_SELECT / AscendC::Sort RADIX），但宿主设置的 useVectorSort tiling gate 在运行时未被遵守导致错误落入标量有界堆。
- Feature signature：`{"bottleneck": ["scalar-bounded-heap-when-vector-path-latent", "host-gate-not-honored"], "dtypes": ["fp16", "bf16", "fp32", "uint8"], "pattern": "inkernel-selfselect-latent-vecsort", "structure": ["t1-es1-whole-row", "vector-sort-latent-path"]}`

## 3. 正确性红线

- gate 过宽会把低收益 case（k 很小或 sortLen 超 LCM 预算）导入向量路径造成回归
- REAL regression observed: case_19 (uint8 [4097,511] k=256 sortLen=511, highRatio 1280>=511 fires) 从标量堆（baseline aiv_scalar 0.89, 400us）被导入 RADIX_SELECT 后 ~2x 变慢（official 792.8us 可复现）。highRatio 单独不足以保证向量路径收益，需 dtype×sortLen 联合约束或对每个控制 case 做官方路径 spot_check。
- LCM/UB 预算判断错误会导致编译失败或设备错误 507035
- 依赖运行时字段的稳定性，shape 解析错误会误路由
- measure.py 轮次窗口可能把真实回归误报为环境噪声——控制 case 必须用官方路径 spot_check 复核

资源与硬件约束：

- self-select 赋值必须在 vectorSortPath 缓冲分配之前执行
- 不匹配时必须逐字节回退原标量路径，不得改动任何路径内部逻辑

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- kernel 内已存在被 host gate 字段选择的完整向量 top-k 路径（AscendC::TopK RADIX_SELECT / AscendC::Sort RADIX）
- 运行时字段 sortLen/k/largest/chunkLen/dtype 可靠可解码
- 目标 case geometry 满足向量路径的 UB 峰值与 32B 对齐约束

不适用：

- dtype 不在向量路径支持集（如 int64 被 host gate 8.5 排除）
- 整行 Sort 的 LCM 超过 kLcmReserve（如 bf16 [4096] 行 LCM 70144 > 68608）——需改用分块路径而非直接 self-select
- case 运行时已由其他机制路由到向量路径（重复激活无收益）

## 5. 实施步骤

1. 确认目标 case 的运行时 route 与 dtype，读取 op_summary 确认 aiv_vec=0（向量路径未激活）
2. 在 Init 解码可靠运行时字段后添加 self-select gate（route/chunkLen/dtype/sortLen/k/对齐/UB）
3. 把 self-select 放在向量路径缓冲分配之前，复用既有 topkTmpBuf_/topKIdxBuf_
4. 单 case probe 验证激活后走向量路径且正确性不变
5. 全量 verify + measure + 官方路径 spot_check 确认无控制回归

## 6. LLM 前置问题

- 目标实现是否满足：kernel 内已存在被 host gate 字段选择的完整向量 top-k 路径（AscendC::TopK RADIX_SELECT / AscendC::Sort RADIX）？
- 目标实现是否满足：运行时字段 sortLen/k/largest/chunkLen/dtype 可靠可解码？
- 目标实现是否满足：目标 case geometry 满足向量路径的 UB 峰值与 32B 对齐约束？
- 是否命中排除条件：dtype 不在向量路径支持集（如 int64 被 host gate 8.5 排除）？

## 7. 验收标准

正确性：

- verify 20/20 通过；未激活 case 逐字节回退
- case_9 官方路径 spot_check 125.5us 可复现（measure 116.7us）

性能：

- case_9 3748.7us -> 116.7us（measure）/ 125.5us（official-path）≈30x
- score_model 边际 +0.23 官方 pts（estimate；官方 final eval 为准）

回滚信号：

- 任何 case 在向量路径上相对原标量路径真实回归即收紧 gate 回退
- spot_check verdict=not_reproducible 时回退
- case_19 型回归（uint8 sortLen~511 k~256 被 highRatio 导入向量路径 ~2x 变慢）触发时收紧 gate（如排除 uint8 低 sortLen 几何）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize

- top_k-20260831_151225-dbf26e（round=1, status=accepted）

## 检索卡（短卡）

动作：在 kernel Init 按可靠运行时字段自选 useVectorSort_=1，激活已编译进 kernel 但宿主 gate 未分发的向量排序路径。
适用：kernel 内已存在被 host gate 选择的完整向量 top-k 路径；运行时字段可靠可解码。
限制：self-select 赋值须在 vectorSortPath 缓冲分配之前；gate 过宽会把低收益 case 导入向量路径。
范围：top_k T1 ES1 整行 case 的路径自选择
检索词：useVectorSort_、RADIX_SELECT、AscendC::Sort、self-select、chunkLen、32B 对齐
机会：宿主 gate 运行时未生效，已有向量路径闲置而 case 在标量有界堆上空耗
代价：gate 过宽实测 case_19（uint8 sortLen=511 k=256）约 2x 变慢
