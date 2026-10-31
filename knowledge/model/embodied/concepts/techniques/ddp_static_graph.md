---
type: Concept
title: DDP 静态图训练优化（static_graph=True）
description: Pi0.5 在昇腾 Atlas A2 多卡 DDP（DistributedDataParallel）训练中的图固定优化：通过固定训练图、关闭无用参数探测、复用梯度 bucket view，减少 DDP 反向通信侧的额外开销。cann-recipes-embodied-ai 文档声明 Pi0.5 默认开启；固定快照的解析器接线存在缺陷，使用前须修复。
tags:
- task.optimization
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/pi05/train/doc/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/pi05/train/src/lerobot_train.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/pi05/train/src/utils.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/pi05/train/src/scripts/setup_lerobot.sh
  role: implementation
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a2
---

# DDP 静态图训练优化（static_graph=True）

Pi0.5 在昇腾 **Atlas A2** 多卡 DDP（DistributedDataParallel）训练中的图固定优化：通过固定训练图、关闭无用参数探测、复用梯度 bucket view，减少 DDP 反向通信侧的额外开销。`cann-recipes-embodied-ai` 文档声明 Pi0.5 默认开启；固定快照的解析器接线存在缺陷，使用前须修复。

> 来源：`manipulation/pi05/train/doc/README.md`「优化项」表与正文。属于 Pi0.5 profiling 暴露的「训练图反向阶段重复 recomputation 与 DDP 同步成本」一类开销的优化。

## DDP 默认配置

文档声明 Pi0.5 的 DDP 默认配置如下，设计上通过 accelerate.utils.DistributedDataParallelKwargs 应用。固定 21a5ed7 快照不能据此视为可直接运行：lerobot_train.py 从 lerobot.utils.utils 导入 _resolve_ddp_settings，随后又本地定义同名函数并调用未定义的 _env_flag；setup_lerobot.sh 安装的 utils.py 也没有被导入的解析器。这会在导入或解析阶段阻断启动，必须先修正接线并验证，不能仅设置环境变量绕过。modeling_pi05.py 的模型内部融合与 DDP 包装属于不同层。

| 配置 | 作用 |
| --- | --- |
| `find_unused_parameters=False` | 关闭无用参数探测，省去动态图额外探测开销 |
| `static_graph=True` | 固定训练图，减少 bucket 重建 |
| `gradient_as_bucket_view=True` | 梯度复用 bucket 内存视图，降低梯度通信侧额外开销 |

原文表述（`manipulation/pi05/train/doc/README.md`）：

> 对于 `pi05`，DDP 默认采用 `find_unused_parameters=False`、`static_graph=True` 和 `gradient_as_bucket_view=True`，目的是减少动态图额外探测、稳定 bucket 组织并降低梯度通信侧的额外开销。

设计中的默认值以 policy_type == "pi05" 判定：find_unused=False、static_graph=True、gradient_as_bucket_view=True；非 pi05 的默认值相反。LEROBOT_DDP_FIND_UNUSED_PARAMETERS / LEROBOT_DDP_STATIC_GRAPH / LEROBOT_DDP_GRADIENT_AS_BUCKET_VIEW 是预期覆盖入口，当前快照没有完整可用的解析实现。本卡没有登记并验证其修正版，因此不能承诺 0/1 覆盖已可用。

训练文档将此项列为保留的稳态优化，收益小于关闭外层 suffix checkpoint；这属于来源记录，不能作为当前接线可运行的证据。

## 适用前提

- `static_graph=True` 要求每个训练 step 的计算图结构固定（参数参与/跳过模式不随 step 变化）。Pi0.5 训练图满足该前提，因此可安全固定；若模型中存在条件分支导致每 step 参数参与集变化，则不适用。
- `find_unused_parameters=False` 与 `static_graph=True` 配合：既然图固定且无未用参数，就不必每 step 探测未用参数，省去探测与 bucket 重建。

## 在 Pi0.5 训练的应用 — 多卡启动

`manipulation/pi05/train/doc/README.md` 记录的训练命令（2 卡示例；先修复上述接线并验证，再配合 disable-outer-suffix-checkpoint）：

```bash
cd cann-recipes-embodied-ai/manipulation/pi05/train/src/scripts
./run_train.sh pi05 --nproc 2 --disable-outer-suffix-checkpoint
```

样例面向昇腾 Atlas A2，CANN 8.3.RC1，LeRobot v0.4.4（commit `8fff0fde7c79f23a93d845d1a50e985de01f8b8a`）。多卡训练 profiling 会产出 `profiling/rank0/...`、`profiling/rank1/...`（每卡一份）；文档记录的 Pi0.5 稳定训练区间约 `5.75 ~ 5.85 s/it`。

> Pi0 训练样例（`manipulation/pi0/train/`）未在文档中显式列出这三项 DDP 配置，不能据 Pi0.5 配置推定 Pi0 的默认值；Pi0 的反向优化以 disable-outer-suffix-checkpoint 与 NPU fusion attention 为主（见 [gradient-checkpoint-refine](gradient_checkpoint_refine.md)）。

## Links

- 配套训练优化：[gradient-checkpoint-refine](gradient_checkpoint_refine.md)
- 受益模型：[pi05](../manipulation/pi05.md)
- 网络结构：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 训练平台：[atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)（Pi0.5 多卡训练实际平台）；[ascend-310p](../platforms/ascend_310p.md) / [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（family 对照）
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1)
