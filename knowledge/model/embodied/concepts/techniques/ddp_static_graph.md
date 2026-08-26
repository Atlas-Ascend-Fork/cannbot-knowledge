---
type: Concept
title: DDP 静态图训练优化（static_graph=True）
description: Pi0.5 在昇腾 Atlas A2 多卡 DDP（DistributedDataParallel）训练中的图固定优化：通过固定训练图、关闭无用参数探测、复用梯度 bucket view，减少 DDP 反向通信侧的额外开销。cann-recipes-embodied-ai 的 Pi0.5 训练样例默认开启，由本页 canonical 描述。
tags:
- task.optimization
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi05/train/doc/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# DDP 静态图训练优化（static_graph=True）

Pi0.5 在昇腾 **Atlas A2** 多卡 DDP（DistributedDataParallel）训练中的图固定优化：通过固定训练图、关闭无用参数探测、复用梯度 bucket view，减少 DDP 反向通信侧的额外开销。`cann-recipes-embodied-ai` 的 Pi0.5 训练样例默认开启，由本页 canonical 描述。

> 来源：`manipulation/pi05/train/doc/README.md`「优化项」表与正文。属于 Pi0.5 profiling 暴露的「训练图反向阶段重复 recomputation 与 DDP 同步成本」一类开销的优化。

## DDP 默认配置

Pi0.5 在 DDP 包装层默认开启三项，由训练脚本（`run_train.sh` / `run_profiling.sh`）默认配置，经 `lerobot_train.py` 中 `_resolve_ddp_settings(policy_type)`（自 `lerobot.utils.utils` 导入）解析后，通过 `accelerate.utils.DistributedDataParallelKwargs` 应用到 DDP 包装层。注意：`modeling_pi05.py` 本身不含任何 DDP/static_graph 设置，它承载的是 in-model 的 QKV 融合 / NPU fusion-attention / grouped-gemma in-proj（受 `PI05_FUSE_PALIGEMMA_QKV` / `PI05_USE_NPU_FUSION_ATTENTION` / `PI05_USE_NPU_GROUPED_GEMMA_INPROJ` 控制），与本页三项 DDP 设置分属不同层。

| 配置 | 作用 |
| --- | --- |
| `find_unused_parameters=False` | 关闭无用参数探测，省去动态图额外探测开销 |
| `static_graph=True` | 固定训练图，减少 bucket 重建 |
| `gradient_as_bucket_view=True` | 梯度复用 bucket 内存视图，降低梯度通信侧额外开销 |

原文表述（`manipulation/pi05/train/doc/README.md`）：

> 对于 `pi05`，DDP 默认采用 `find_unused_parameters=False`、`static_graph=True` 和 `gradient_as_bucket_view=True`，目的是减少动态图额外探测、稳定 bucket 组织并降低梯度通信侧的额外开销。

接线机制：三项默认值由 `policy_type == "pi05"`（`is_pi05`）驱动——`is_pi05=True` 时分别得到 `find_unused=not is_pi05`（关闭探测）、`static_graph=is_pi05`（开图固定）、`gradient_as_bucket_view=is_pi05`（开 bucket-view），非 pi05 模型则三项反向、默认关闭。脚本以 `LEROBOT_DDP_FIND_UNUSED_PARAMETERS` / `LEROBOT_DDP_STATIC_GRAPH` / `LEROBOT_DDP_GRADIENT_AS_BUCKET_VIEW` 三个环境变量暴露覆盖入口（默认值 `auto`，由 `_resolve_ddp_settings` 按 `is_pi05` 解析）；显式置 `0` / `1` 即可强制关闭或开启对应项，无需改代码。

实测结论：**保留，但不是主要瓶颈**——相比同样属于反向阶段优化的「关闭外层 suffix checkpoint」（见 [gradient-checkpoint-refine](gradient_checkpoint_refine.md)，当前收益最大单项），DDP 静态图属于稳态收益项，已默认开启、无需手工切换。

## 适用前提

- `static_graph=True` 要求每个训练 step 的计算图结构固定（参数参与/跳过模式不随 step 变化）。Pi0.5 训练图满足该前提，因此可安全固定；若模型中存在条件分支导致每 step 参数参与集变化，则不适用。
- `find_unused_parameters=False` 与 `static_graph=True` 配合：既然图固定且无未用参数，就不必每 step 探测未用参数，省去探测与 bucket 重建。

## 在 Pi0.5 训练的应用 — 多卡启动

`manipulation/pi05/train/doc/README.md` 推荐训练命令（2 卡示例，配合 disable-outer-suffix-checkpoint）：

```bash
cd cann-recipes-embodied-ai/manipulation/pi05/train/src/scripts
./run_train.sh pi05 --nproc 2 --disable-outer-suffix-checkpoint
```

样例面向昇腾 Atlas A2，CANN 8.3.RC1，LeRobot v0.4.4（commit `8fff0fde7c79f23a93d845d1a50e985de01f8b8a`）。多卡训练 profiling 会产出 `profiling/rank0/...`、`profiling/rank1/...`（每卡一份）；默认配置下 Pi0.5 稳定训练区间约 `5.75 ~ 5.85 s/it`。

> Pi0 训练样例（`manipulation/pi0/train/`）未在文档中显式列出这三项 DDP 配置，故本页主要锚定 Pi0.5；Pi0 的反向优化以 disable-outer-suffix-checkpoint 与 NPU fusion attention 为主（见 [gradient-checkpoint-refine](gradient_checkpoint_refine.md)）。

## Links

- 配套训练优化：[gradient-checkpoint-refine](gradient_checkpoint_refine.md)
- 受益模型：[pi05](../manipulation/pi05.md)
- 网络结构：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 训练平台：[atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)（Pi0.5 多卡训练实际平台）；[ascend-310p](../platforms/ascend_310p.md) / [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（family 对照）
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
