---
type: Optimization
title: T1 单行/长 scanLen 的两级分块并行扫描（块内前缀 + 跨核归并 + 带偏移重扫）
description: T1 单行/长 scanLen（outerRowCount=1）默认单核串行扫描，case 13 [1000003] bf16 dim=-1 冻结基线 4316.2us。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scan-row-split-two-level-cross-core.md
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
      "kernel 须声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用",
      "聚合中转 val/idx 分置两个 32B 对齐 TBuf，DataCopyPad UB 侧保持 32B 对齐",
      "Pass2 读前序聚合的写侧同步用 PipeBarrier<PIPE_ALL>，勿用 S_MTE3/MTE2_S 事件"
    ],
    "excluded_conditions": [
      "短行（scanLen 无法切出足够多能填满核数的块）直接回退单核串行，不启用分块",
      "非 MIX_AIV_1_0 任务类型下 SyncAll() 语义不同，需重新验证硬同步与 S_MTE3 兼容性"
    ],
    "required_conditions": [
      "T1 模式（dimNorm == rank-1）且 outerRowCount==1，scanLen >> coreNum 粒度（长行）",
      "scanLen 可按 UB 预算切成 >= blockDim 的 scanBlocks，每块独立前缀扫描并携带运行 min/argmin",
      "跨核块尾聚合经 GM workspace 写出 + SyncAll() 硬同步后对 Pass2 可见"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "13",
      "env": {
        "device": "5",
        "op_name": "Cummin",
        "post_eval_score": 60.87859925160219,
        "pre_eval_score": 57.42744371577807,
        "score_delta": "+3.45"
      },
      "operator_class": "reduction",
      "precision": "20/20 passed",
      "run_id": "<run-id>",
      "speedup": "23.0x",
      "status": "accepted",
      "task_dir": "cann-bench_rpy/strategies/cummin_opt_20260821"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "scalar-serial-scan",
      "single-row-collapse"
    ],
    "pattern": "scan-row-split-two-level-cross-core",
    "structure": [
      "t1-contiguous-axis-scan",
      "block-prefix-scan",
      "workspace-aggregate",
      "hard-syncall",
      "compute-block-offset",
      "rescan-with-offset"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-ROW-SPLIT-TWO-LEVEL",
  "implementation_steps": [
    "host tiling 识别 T1 且 outerRowCount==1 的长 scanLen，按 UB 预算切 scanBlocks，blockDim=min(coreNum, scanBlocks)",
    "kernel 声明 KERNEL_TYPE_MIX_AIV_1_0；Pass1 每核做块内 RegTensor 标量寄存器前缀扫描",
    "块尾 val/idx 聚合分置两个 32B 对齐 TBuf 写 GM workspace",
    "SyncAll() 硬同步（写侧 PipeBarrier<PIPE_ALL>，不用 S_MTE3 事件）",
    "Pass2（block>0）ComputeBlockOffset 读前序 exclusive-min 聚合（NaN sticky + <= tie-break），带 offset 重扫；短行条件路由回退单核串行"
  ],
  "intent": "消除 T1 退化长行（outerRowCount=1）时核利用率塌缩：64 核只有 1 核串行扫整个扫描轴，baseline 4316us 而 t_hw 仅 ~1.25us。",
  "mechanism": "host tiling 识别 T1 且 outerRowCount==1 的长 scanLen，按 UB 预算切 scanBlocks、blockDim=min(coreNum, scanBlocks)。kernel 须声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用。Pass1 每核做块内前缀扫描 -> 块尾 val/idx 聚合写入 GM workspace（分置两个 32B 对齐 TBuf，见 NEG-AGG-BUFFER-ALIAS-WAR）-> SyncAll() 硬同步 -> Pass2（block>0）各核 ComputeBlockOffset 读前序聚合（exclusive-min，NaN sticky + 同值取小 idx 的 <= tie-break）-> 带 offset 载入重扫。块内仍走 RegTensor 标量寄存器流水。写侧可见性用 PipeBarrier<PIPE_ALL>（勿用 S_MTE3 事件，见 NEG-S-MTE3-MIX-SYNCALL）。短行（scanLen 无法填满核数）按条件路由回退单核串行。",
  "name": "T1 单行/长 scanLen 的两级分块并行扫描（块内前缀 + 跨核归并 + 带偏移重扫）",
  "operator_class": "reduction",
  "operator_scope": "末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）中 outerRowCount==1 的退化长行：单核串行扫一个超长 scanLen（如 1M 元素）时把该行按 scanBlocks 切块分发到多核",
  "principle": "前缀扫描的块尾聚合值（running-min/argmin）可经 GM workspace 写出并被跨核归并得到各块的 exclusive 前缀偏移（exclusive-min），因此每个块可在带 offset 的情况下独立并行扫描；块内仍保持原标量寄存器流水（RegTensor），正确性语义（NaN sticky、同值取小索引的 <= tie-break）在归并规则中显式保留。",
  "related_anti_patterns": [],
  "risks": [
    "同址 WAR：聚合中转若用单 32B TBuf 存 val@0/idx@0，idx SetValue（PIPE_S）会覆盖未搬出的 val —— case 13 精度失败根因，须分置两个 32B 对齐 TBuf（见 NEG-AGG-BUFFER-ALIAS-WAR）",
    "写侧 S_MTE3 SetFlag/WaitFlag 在 MIX_AIV_1_0 + 硬 SyncAll 并发下致设备 507035（build1/build2 二分证实）-> 回退 PipeBarrier<PIPE_ALL>（见 NEG-S-MTE3-MIX-SYNCALL）",
    "scanLen 必须足够大使每块元素数能填满核数，否则分块同步/归并开销不摊销"
  ],
  "slug": "scan-row-split-two-level-cross-core",
  "summary": "T1 单行/长 scanLen（outerRowCount=1）默认单核串行扫描，case 13 [1000003] bf16 dim=-1 冻结基线 4316.2us。把单行按 scanBlocks 切块分发 64 核，两级扫描：Pass1 块内前缀 + 块尾聚合写 workspace + SyncAll 硬同步 + Pass2 ComputeBlockOffset 读前序 exclusive-min 带偏移重扫，实测 187.8us（23.0x），其余 19 case 无回归（<=±2%）。",
  "verification": {
    "correctness": [
      "case 13 [1000003] bf16 dim=-1 精度通过；全量 20/20 passed（build -> install -> pytest）",
      "LE 并列（同值取小 idx）+ fp32 NaN sticky 语义在归并规则中显式保留"
    ],
    "performance": [
      "case 13：4316.2us -> 187.8us（23.0x，5 采样中位数对冻结基线）",
      "其余 19 case 无回归（<=±2%）；S-A+S-B 合计全量 219482.4 -> 16376.8us = 13.40x",
      "post-eval official score 60.88（post - pre = +3.45，20/20 passed）"
    ],
    "rollback_signals": [
      "聚合读到陈旧值/覆盖（同址 WAR 复现）或 Pass2 偏移错误导致索引/值错位",
      "SyncAll 悬挂或设备 507035（S_MTE3 复用）",
      "短行误走分块路径引入回归"
    ]
  }
}
-->

# 性能优化策略：T1 单行/长 scanLen 的两级分块并行扫描（块内前缀 + 跨核归并 + 带偏移重扫）

单一优化点：T1 单行/长 scanLen（outerRowCount=1）默认单核串行扫描，case 13 [1000003] bf16 dim=-1 冻结基线 4316.2us。把单行按 scanBlocks 切块分发 64 核，两级扫描：Pass1 块内前缀 + 块尾聚合写 workspace + SyncAll 硬同步 + Pass2 ComputeBlockOffset 读前序 exclusive-min 带偏移重扫，实测 187.8us（23.0x），其余 19 case 无回归（<=±2%）。

## 1. 原理

前缀扫描的块尾聚合值（running-min/argmin）可经 GM workspace 写出并被跨核归并得到各块的 exclusive 前缀偏移（exclusive-min），因此每个块可在带 offset 的情况下独立并行扫描；块内仍保持原标量寄存器流水（RegTensor），正确性语义（NaN sticky、同值取小索引的 <= tie-break）在归并规则中显式保留。

实现机制：host tiling 识别 T1 且 outerRowCount==1 的长 scanLen，按 UB 预算切 scanBlocks、blockDim=min(coreNum, scanBlocks)。kernel 须声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用。Pass1 每核做块内前缀扫描 -> 块尾 val/idx 聚合写入 GM workspace（分置两个 32B 对齐 TBuf，见 NEG-AGG-BUFFER-ALIAS-WAR）-> SyncAll() 硬同步 -> Pass2（block>0）各核 ComputeBlockOffset 读前序聚合（exclusive-min，NaN sticky + 同值取小 idx 的 <= tie-break）-> 带 offset 载入重扫。块内仍走 RegTensor 标量寄存器流水。写侧可见性用 PipeBarrier<PIPE_ALL>（勿用 S_MTE3 事件，见 NEG-S-MTE3-MIX-SYNCALL）。短行（scanLen 无法填满核数）按条件路由回退单核串行。

## 2. 性能问题模式

- 优化目标：消除 T1 退化长行（outerRowCount=1）时核利用率塌缩：64 核只有 1 核串行扫整个扫描轴，baseline 4316us 而 t_hw 仅 ~1.25us。
- 适用数据流：末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）中 outerRowCount==1 的退化长行：单核串行扫一个超长 scanLen（如 1M 元素）时把该行按 scanBlocks 切块分发到多核
- Feature signature：`{"bottleneck": ["core-underutilization", "scalar-serial-scan", "single-row-collapse"], "pattern": "scan-row-split-two-level-cross-core", "structure": ["t1-contiguous-axis-scan", "block-prefix-scan", "workspace-aggregate", "hard-syncall", "compute-block-offset", "rescan-with-offset"]}`

## 3. 正确性红线

- 同址 WAR：聚合中转若用单 32B TBuf 存 val@0/idx@0，idx SetValue（PIPE_S）会覆盖未搬出的 val —— case 13 精度失败根因，须分置两个 32B 对齐 TBuf（见 NEG-AGG-BUFFER-ALIAS-WAR）
- 写侧 S_MTE3 SetFlag/WaitFlag 在 MIX_AIV_1_0 + 硬 SyncAll 并发下致设备 507035（build1/build2 二分证实）-> 回退 PipeBarrier<PIPE_ALL>（见 NEG-S-MTE3-MIX-SYNCALL）
- scanLen 必须足够大使每块元素数能填满核数，否则分块同步/归并开销不摊销

资源与硬件约束：

- kernel 须声明 KERNEL_TYPE_MIX_AIV_1_0 使 SyncAll() 硬同步可用
- 聚合中转 val/idx 分置两个 32B 对齐 TBuf，DataCopyPad UB 侧保持 32B 对齐
- Pass2 读前序聚合的写侧同步用 PipeBarrier<PIPE_ALL>，勿用 S_MTE3/MTE2_S 事件

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- T1 模式（dimNorm == rank-1）且 outerRowCount==1，scanLen >> coreNum 粒度（长行）
- scanLen 可按 UB 预算切成 >= blockDim 的 scanBlocks，每块独立前缀扫描并携带运行 min/argmin
- 跨核块尾聚合经 GM workspace 写出 + SyncAll() 硬同步后对 Pass2 可见

不适用：

- 短行（scanLen 无法切出足够多能填满核数的块）直接回退单核串行，不启用分块
- 非 MIX_AIV_1_0 任务类型下 SyncAll() 语义不同，需重新验证硬同步与 S_MTE3 兼容性

## 5. 实施步骤

1. host tiling 识别 T1 且 outerRowCount==1 的长 scanLen，按 UB 预算切 scanBlocks，blockDim=min(coreNum, scanBlocks)
2. kernel 声明 KERNEL_TYPE_MIX_AIV_1_0；Pass1 每核做块内 RegTensor 标量寄存器前缀扫描
3. 块尾 val/idx 聚合分置两个 32B 对齐 TBuf 写 GM workspace
4. SyncAll() 硬同步（写侧 PipeBarrier<PIPE_ALL>，不用 S_MTE3 事件）
5. Pass2（block>0）ComputeBlockOffset 读前序 exclusive-min 聚合（NaN sticky + <= tie-break），带 offset 重扫；短行条件路由回退单核串行

## 6. LLM 前置问题

- 目标实现是否满足：T1 模式（dimNorm == rank-1）且 outerRowCount==1，scanLen >> coreNum 粒度（长行）？
- 目标实现是否满足：scanLen 可按 UB 预算切成 >= blockDim 的 scanBlocks，每块独立前缀扫描并携带运行 min/argmin？
- 目标实现是否满足：跨核块尾聚合经 GM workspace 写出 + SyncAll() 硬同步后对 Pass2 可见？
- 是否命中排除条件：短行（scanLen 无法切出足够多能填满核数的块）直接回退单核串行，不启用分块？

## 7. 验收标准

正确性：

- case 13 [1000003] bf16 dim=-1 精度通过；全量 20/20 passed（build -> install -> pytest）
- LE 并列（同值取小 idx）+ fp32 NaN sticky 语义在归并规则中显式保留

性能：

- case 13：4316.2us -> 187.8us（23.0x，5 采样中位数对冻结基线）
- 其余 19 case 无回归（<=±2%）；S-A+S-B 合计全量 219482.4 -> 16376.8us = 13.40x
- post-eval official score 60.88（post - pre = +3.45，20/20 passed）

回滚信号：

- 聚合读到陈旧值/覆盖（同址 WAR 复现）或 Pass2 偏移错误导致索引/值错位
- SyncAll 悬挂或设备 507035（S_MTE3 复用）
- 短行误走分块路径引入回归

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260821（status=accepted, case=13, speedup=23.0x）

## 检索卡（短卡）

动作：按UB预算把长行切成scanBlocks；块尾经GM workspace跨核归并为exclusive偏移，再让各块独立扫描。
适用：T1末轴模式、仅一行，且scanLen远大于核心粒度。
限制：须声明KERNEL_TYPE_MIX_AIV_1_0以用SyncAll；聚合val/idx不得同址产生WAR。
范围：scan-reduce的T1单行长scanLen路径。
检索词：T1、scanBlocks、GM workspace、exclusive-min、SyncAll、RegTensor。
机会：T1仅有一个长输出行，按行切核只产生一个任务。
