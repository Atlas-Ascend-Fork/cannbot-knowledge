---
type: Optimization
title: HCCL AIV 算子展开与 prefill micro-batch 双流互斥（A3 开 AIV、微批关 AIV、多机放宽超时）
description: HCCL AIV 算子展开与 prefill micro-batch 双流互斥（A3 开 AIV、微批关 AIV、多机放宽超时）。HCCL_OP_EXPANSION_MODE=AIV（HCCL AIV 算子展开）借用 Device 的 Vector Core（AI Vector core）来加速集合通信操作。它在昇腾多机多卡推理里该不该开，取决于同时有没有并行计算跟它抢 Vector Core： 核心互斥：prefill 开 micro-batch 双流优化时，不要设 HCCL_OP_EXPANSION_MODE=AIV，保持默认 SDMA 模式。
tags:
- task.optimization
- topic.parallelism
- topic.data_movement.communication.collective_communication
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/72
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/8
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# HCCL AIV 算子展开与 prefill micro-batch 双流互斥（A3 开 AIV、微批关 AIV、多机放宽超时）

## 条件 → 怎么配 `HCCL_OP_EXPANSION_MODE`

`HCCL_OP_EXPANSION_MODE=AIV`（HCCL AIV 算子展开）借用 Device 的 Vector Core（AI Vector core）来加速集合通信操作。它在昇腾多机多卡推理里该不该开，取决于同时有没有并行计算跟它抢 Vector Core：

| 场景 | AIV 展开 | 依据 |
|---|---|---|
| Atlas A3（910c）多机多卡基线 | **开** `export HCCL_OP_EXPANSION_MODE=AIV` | 910c 需显式开 HCCL AIV（脚本注释 "910c needs enable HCCL aiv"）|
| [prefill-micro-batch](../../../concepts/techniques/prefill_micro_batch.md) 双流并行 | **关**（`unset`） | AIV 抢 Vector Core 与并行计算冲突，时延变长 |
| decode 集合通信 | **开**（推荐） | decode 未做计算/通信双流并行，无资源抢占 |

核心互斥：**prefill 开 micro-batch 双流优化时，不要设 `HCCL_OP_EXPANSION_MODE=AIV`，保持默认 SDMA 模式**。

## 为何

- [micro-batch 双流](../../../concepts/techniques/prefill_micro_batch.md)的目的是让 MoE dispatch/combine 的 AllToAll 通信与计算**并行**、互相掩盖（见 [multi-stream](../../../concepts/techniques/multi_stream.md)）。
- AIV 展开借用 Device 的 Vector Core 计算单元来加速通信。
- 二者叠加时，通信占用的 Vector Core 与并行的计算争抢同一类硬件资源，反而使时延变长——通信/计算硬件资源抢占。
- decode 取向相反：decode 未做计算/通信双流并行，AIV 加速通信无抢占问题，故 decode 推荐开 AIV。两处取向不同源于"是否存在并行计算争抢"，非矛盾。

## 做什么（启动脚本约定）

`executor/scripts/function.sh` 的 `check_env_vars` 把这条互斥固化进部署脚本——A3 默认开 AIV，读 yaml `model_config.micro_batch_mode`，等于 1 时 `unset`：

```bash
# 910c needs enable HCCL aiv
export HCCL_OP_EXPANSION_MODE=AIV

if [[ ${micro_batch_mode} -eq 1 ]]; then
    # if enable micro_batch, disable AIV
    unset HCCL_OP_EXPANSION_MODE
fi
```

配套的分布式超时放宽（规避多机建链 / 长算子导致的 [HCCL](../../../concepts/frameworks/cann_executor.md) 分布式超时，默认更短、多机易踩）：

```bash
export HCCL_CONNECT_TIMEOUT=1200
export HCCL_EXEC_TIMEOUT=1200
```

## 边界 / rollback

- 平台上下文：`910c` ≈ [Atlas A3](../../../concepts/platforms/atlas_a3.md)（本仓当前仅支持 A3 系列）。DeepSeek-R1 / Kimi-K2 等走 micro-batch 的模型适用。
- 该互斥是脚本内固化的部署约定：AIV 与微批的**底层互斥机理**（Vector Core 抢占）来自脚本注释 + 实现者披露，"时延变长"量级无独立复测——只主张"该条件下应如此配置"，不作绝对机制断言。
- rollback：不开 micro-batch 时 AIV 照常开（A3 基线）；要开 micro-batch 则确保 `HCCL_OP_EXPANSION_MODE` 被 unset。

## 相关经验
- [大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)](ascend_deploy_parallel_variant_and_nondefault_platform.md)

## Evidence

- **文档事实**（clone `@f5bf59cf`）：`deepseek_r1_prefill_optimization.md` micro-batch「通信处理」步原文——"由于通信和计算并行，此时不能使能 HCCL_OP_EXPANSION_MODE 的 AIV 模式，采用默认 SDMA 模式。如果采用 AIV 模式，则会导致通信和计算硬件资源抢占，时延变长。"；`deepseek_r1_decode_optimization.md`「集合通信使能 AIV 展开」佐证 decode 相反取向。
- **代码事实**（clone `@d23e91732136`）：`executor/scripts/function.sh` `check_env_vars` diff——上述 export/unset AIV（含 `micro_batch_mode==1` 时 unset）、`HCCL_*_TIMEOUT=1200` 均为脚本 diff 事实。
- **仓自报**："910c 需 AIV""微批需禁 AIV"的底层原因来自脚本注释（非独立一手规格）。
- 溯源下探：
  - [cann-recipes-infer-pr-72-feat-add-deepseek-r1-kimi-k2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/72)
  - [cann-recipes-infer-pr-8-refactor-add-common-development](https://gitcode.com/cann/cann-recipes-infer/merge_requests/8)