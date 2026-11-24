---
type: Optimization
title: T2 多 chunk 大轴分块向量排序 + 归并
description: 对 T2 Q>1 多 chunk 大轴 case，各 chunk 独立向量排序，再把各 chunk 前 k 归并池排序合并输出——把 round-4 门控排除的多 chunk 大轴 case 的 AIV Scalar 有界堆改为向量排序+归并。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-t2-chunked-vector-sort-merge.md
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
      "chunk 排序索引错误改用 Reg 基 GenGlobalSrcIdx；in-place Adds 索引修正"
    ],
    "excluded_conditions": [
      "归并池排序 LCM 超 ~64KB 栈（如 case_6 poolLen=4096）——收紧门控回退标量",
      "case_18 非真目标（shape 误读）"
    ],
    "required_conditions": [
      "T2 Q>1 多 chunk 大轴、chunkCount>1",
      "各 chunk 可独立向量排序",
      "归并池 LCM 满足 UB 预算"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 5,
      "run_id": "<run-id>",
      "speedup": "incremental 1.1756x; case_4 8.32x",
      "status": "accepted"
    },
    {
      "comparison_sha256": "c4e4a60591b4f1ec049318bcbf1955a7095da8e0ca8c4ebf165985f280eb448d",
      "decision_sha256": "d39edda7fa3ad77236069a10e57e86019f2d54ef9e651bb6524e496569860f1a",
      "operator_class": "sort-select",
      "performance_sha256": "16e12944e140506f6d80dc698ddf77ee7e042ddaf56409944fc6799b5462844b",
      "round": 5,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "e41e442af4be673310ad2cb793e3e8edd07cf93fa2c7dbbf2302318763092b23",
      "verify_sha256": "90c116498ab57319ca475a45cd2ba552710bd3d9d10a4373c469dcadefefc7a2"
    },
    {
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "incremental 1.3634x; case5 official 5.66x (37433.9->6616.77us); cumulative 4.1086",
      "status": "accepted"
    },
    {
      "comparison_sha256": "ff001c0ad916397355ef36fabeefa71577579c0a6ad56094617a24a171fcd4e8",
      "decision_sha256": "7ee228e030040941c3263d4d71b546b04982519c83d29245232c33b22996c20a",
      "operator_class": "sort-select",
      "performance_sha256": "c588b3069e326b3e4f184ff10400df889cf84f811d1f45e451a61a7aa19e8817",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "5c46f9878ca0baed157125df93496a227d2fbed18454a5a967ab7bcc9c7db4ae",
      "verify_sha256": "fc51dac5bb5967a99916bbec5f1be2fbcf54e1157f7b1fcb750388d3f89f7edd"
    },
    {
      "comparison_sha256": "5251c10f7e804e217845f9d298bac5b915cd42be9505c0b6c346f89712a6904d",
      "decision_sha256": "3f85f3bcaaed0a1a414e106a9b5deaefea92cdfb8a6fba5eba09bced61a1a8d6",
      "operator_class": "sort-select",
      "performance_sha256": "fe8a6ab4c62e7adfaab8e7523da39182afc6a431373b0b80d014dae02e3fe1a8",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "191f0f3d6e6c2ab821b69db0bc323eab11e63b2f554ee8ff89af052d0c1f4f13",
      "verify_sha256": "06d7777e34d88f27487023c7f95d9f2703d7de9cab124aded72a924530224ce6"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "multi-chunk-scalar-heap",
      "t2-large-axis"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "chunked-vector-sort-merge",
    "reduce_mode": "top-k",
    "structure": [
      "per-chunk-vector-sort",
      "merge-pool",
      "t2-multi-chunk"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-T2-CHUNKED-SORT-MERGE",
  "implementation_steps": [
    "门控 T2 多 chunk 大轴 + 归并池 UB 预算",
    "各 chunk 向量排序取前 k",
    "归并池排序合并写输出",
    "UB 溢出→收紧门控回退标量路径"
  ],
  "intent": "消除 case_4/6/18（sortLen 8192/8192/8193，chunkCount 3/4/3，合计 ~285ms）的标量有界堆（aiv_scalar 98-99.6%、aiv_vec 0）。",
  "mechanism": "每 chunk 向量排序（AscendC::Sort）取前 k；各 chunk 前 k 进归并池排序（LCM）合并写输出；归并池超 UB 预算（~64KB LCM 栈）时按自身回退信号收紧门控。",
  "name": "T2 多 chunk 大轴分块向量排序 + 归并",
  "operator_class": "sort-select",
  "operator_scope": "TopK T2 Q>1 多 chunk 大轴（sortLen~8192、chunkCount>1）case",
  "principle": "大轴不整行驻留 → 分 chunk 各自向量排序，再合并各 chunk 头部——把串行标量堆替换为可向量化/可合并的排序。",
  "related_anti_patterns": [
    "multi-chunk-scalar-bounded-heap"
  ],
  "risks": [
    "case_6 归并池超预算未覆盖（仍 211ms 标量，剩余最大耗时 ~52%）",
    "case_13 0.9443× 为跨会话漂移（本轮 0.9844× unchanged）"
  ],
  "slug": "topk-t2-chunked-vector-sort-merge",
  "summary": "对 T2 Q>1 多 chunk 大轴 case，各 chunk 独立向量排序，再把各 chunk 前 k 归并池排序合并输出——把 round-4 门控排除的多 chunk 大轴 case 的 AIV Scalar 有界堆改为向量排序+归并。",
  "verification": {
    "correctness": [
      "verify 20/20 通过"
    ],
    "performance": [
      "case_4 8.32×，incremental 1.1756×，regressed=0；管道 case_4 aiv_scalar 62815→1433us、aiv_vec 0→3948us"
    ],
    "rollback_signals": [
      "归并池 UB 溢出→收紧门控；非目标 case 回归则回退"
    ]
  }
}
-->

# 性能优化策略：T2 多 chunk 大轴分块向量排序 + 归并

单一优化点：对 T2 Q>1 多 chunk 大轴 case，各 chunk 独立向量排序，再把各 chunk 前 k 归并池排序合并输出——把 round-4 门控排除的多 chunk 大轴 case 的 AIV Scalar 有界堆改为向量排序+归并。

## 1. 原理

大轴不整行驻留 → 分 chunk 各自向量排序，再合并各 chunk 头部——把串行标量堆替换为可向量化/可合并的排序。

实现机制：每 chunk 向量排序（AscendC::Sort）取前 k；各 chunk 前 k 进归并池排序（LCM）合并写输出；归并池超 UB 预算（~64KB LCM 栈）时按自身回退信号收紧门控。

## 2. 性能问题模式

- 优化目标：消除 case_4/6/18（sortLen 8192/8192/8193，chunkCount 3/4/3，合计 ~285ms）的标量有界堆（aiv_scalar 98-99.6%、aiv_vec 0）。
- 适用数据流：TopK T2 Q>1 多 chunk 大轴（sortLen~8192、chunkCount>1）case
- Feature signature：`{"bottleneck": ["multi-chunk-scalar-heap", "t2-large-axis"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "chunked-vector-sort-merge", "reduce_mode": "top-k", "structure": ["per-chunk-vector-sort", "merge-pool", "t2-multi-chunk"]}`

## 3. 正确性红线

- case_6 归并池超预算未覆盖（仍 211ms 标量，剩余最大耗时 ~52%）
- case_13 0.9443× 为跨会话漂移（本轮 0.9844× unchanged）

资源与硬件约束：

- chunk 排序索引错误改用 Reg 基 GenGlobalSrcIdx；in-place Adds 索引修正

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- T2 Q>1 多 chunk 大轴、chunkCount>1
- 各 chunk 可独立向量排序
- 归并池 LCM 满足 UB 预算

不适用：

- 归并池排序 LCM 超 ~64KB 栈（如 case_6 poolLen=4096）——收紧门控回退标量
- case_18 非真目标（shape 误读）

## 5. 实施步骤

1. 门控 T2 多 chunk 大轴 + 归并池 UB 预算
2. 各 chunk 向量排序取前 k
3. 归并池排序合并写输出
4. UB 溢出→收紧门控回退标量路径

## 6. LLM 前置问题

- 目标实现是否满足：T2 Q>1 多 chunk 大轴、chunkCount>1？
- 目标实现是否满足：各 chunk 可独立向量排序？
- 目标实现是否满足：归并池 LCM 满足 UB 预算？
- 是否命中排除条件：归并池排序 LCM 超 ~64KB 栈（如 case_6 poolLen=4096）——收紧门控回退标量？

## 7. 验收标准

正确性：

- verify 20/20 通过

性能：

- case_4 8.32×，incremental 1.1756×，regressed=0；管道 case_4 aiv_scalar 62815→1433us、aiv_vec 0→3948us

回滚信号：

- 归并池 UB 溢出→收紧门控；非目标 case 回归则回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：multi-chunk-scalar-bounded-heap

- top_k-20260828_120811-77cf84（round=5, status=accepted, speedup=incremental 1.1756x; case_4 8.32x）
- top_k-20260828_120811-77cf84（round=5, status=accepted）
- top_k-20260830_063304-535f59（round=4, status=accepted, speedup=incremental 1.3634x; case5 official 5.66x (37433.9->6616.77us); cumulative 4.1086）
- top_k-20260830_063304-535f59（round=4, status=accepted）
- top_k-20260831_151225-dbf26e（round=2, status=accepted）

## 检索卡（短卡）

动作：将大轴串行标量堆改为各chunk向量排序取前k，再归并各chunk头部。
适用：T2 Q>1多chunk大轴且chunkCount>1，各chunk可独立向量排序，归并池满足UB预算。
限制：归并池不得超出UB；溢出时收紧门控并回退标量路径。
范围：selection-sort-top-k的T2 Q>1多chunk大轴路径。
检索词：T2，多chunk大轴，AscendC::Sort，chunk前k，归并池，chunkCount>1
机会：T2多chunk大轴路径仍使用标量有界堆，且整行无法驻留。
