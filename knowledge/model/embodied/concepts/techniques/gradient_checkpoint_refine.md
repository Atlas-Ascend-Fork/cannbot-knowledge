---
type: Concept
title: 梯度检查点精细化（disable outer suffix checkpoint）
description: Pi0 / Pi0.5 在昇腾 Atlas A2 多卡 DDP 训练上收益最大的单项性能优化：关闭位置不合适的外层 suffix checkpoint，避免反向阶段整段后缀被重复重算。cann-recipes-embodied-ai 的 Pi0/Pi0.5 训练样例共享此优化，由本页 canonical 描述。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi0/train/doc/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi05/train/doc/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-13T00:00:00Z'
platforms:
- a2
---

# 梯度检查点精细化（disable outer suffix checkpoint）

Pi0 / Pi0.5 在昇腾 **Atlas A2** 多卡 DDP 训练上**收益最大的单项性能优化**：关闭位置不合适的外层 suffix checkpoint，避免反向阶段整段后缀被重复重算。`cann-recipes-embodied-ai` 的 Pi0/Pi0.5 训练样例共享此优化，由本页 canonical 描述。

> 入口参数：`--disable-outer-suffix-checkpoint`（Pi0.5 `run_train.sh`/`run_profiling.sh` 命令行开关）/ 环境变量 `LEROBOT_PI0_DISABLE_OUTER_SUFFIX_CHECKPOINT=1`（Pi0 `run_train.sh` 默认导出）。

## 问题：双层 checkpoint 叠加导致反向重复重算

Pi0/Pi0.5 训练默认开启 gradient checkpointing（`policy.gradient_checkpointing: true`），模型内部已保留**更细粒度**的 checkpoint。但 suffix 分支外层还套了**一层大 checkpoint**——它会把整段后缀在反向时重新执行一遍（`manipulation/pi05/train/doc/README.md`）：

> suffix 分支外层那一层大 checkpoint 会把整段后缀在反向时重新执行一遍，而模型内部本来已经保留了更细粒度的 checkpoint；两者叠加后，反向阶段会出现位置不合适的重复重算。

这是 Pi0.5 profiling 暴露的「训练图反向阶段重复 recomputation 与 DDP 同步成本」一类开销。

## 优化：关闭外层 suffix checkpoint

关闭这层「外包式」大 checkpoint 后，显存策略仍可控（模型内部细粒度 checkpoint 仍在），但反向计算明显变快——因此是当前收益最直接的一项。

```bash
# Pi0.5：显式命令行开关
./run_train.sh pi05 --nproc 2 --disable-outer-suffix-checkpoint
./run_profiling.sh pi05 --nproc 2 --foreground --disable-outer-suffix-checkpoint \
  --profile-wait 1 --profile-warmup 1 --profile-active 2 --profile-repeat 1
```

```bash
# Pi0：run_train.sh 默认导出环境变量
LEROBOT_PI0_DISABLE_OUTER_SUFFIX_CHECKPOINT=1
```

## 在 Pi0 训练的应用 — 实测吞吐（Atlas A2 8 卡）

`manipulation/pi0/train/doc/README.md`（每卡 `batch_size=24`，全局 batch `192`，`steps=30`）：

| 优化项 | 吞吐 |
| --- | --- |
| baseline | 66 samples/s |
| NPU fusion attention | 71.11 samples/s |
| **disable outer suffix checkpoint** | **77.64 samples/s** |
| 两者同时开启 | 81.77 samples/s |

单看本项就把吞吐从 66 提到 77.64 samples/s（约 +18%）；与 NPU fusion attention 叠加后端到端较基线提升约 24%。可见 disable-outer-suffix-checkpoint 是比 fusion attention 更大的单项收益。

## 在 Pi0.5 训练的应用 — 与其它优化的关系

`manipulation/pi05/train/doc/README.md` 把它列为默认状态「推荐显式开启」、「当前提升最大的单项性能优化」。Pi0.5 训练默认还吸收了下列优化（已进 `modeling_pi05.py`/脚本，无需手工开）：`sample_beta` fast path、`PI05_FUSE_PALIGEMMA_QKV`、`PI05_USE_NPU_FUSION_ATTENTION`（约 +5%）、`PI05_USE_NPU_GROUPED_GEMMA_INPROJ`（Gemma MLP `gate_proj`/`up_proj` 合并 grouped GEMM，约 +1%~1.2%）以及 DDP 静态图（见 [ddp-static-graph](ddp_static_graph.md)）。

> Gemma MLP grouped GEMM 之所以有效，与本页相关：Pi0.5 默认开 gradient checkpointing，MLP 前向在反向阶段还会被重算一次，把 `gate_proj`/`up_proj` 两段前向 matmul 压成一次 grouped kernel，能在一个 step 内同时吃到「正向一次 + 反向重算一次」的收益。

这两项融合都关联 [flow-matching-action-expert](../modules/flow_matching_action_expert.md) 的 VLM 主干（PaliGemma）与动作专家（Gemma）。Pi0 的 fused attention 还需注意迁移方式：不能全局 monkey-patch Gemma `eager_attention_forward`，需局部接法（`_repeat_kv_heads` + `_npu_fusion_attention_forward`，实例级 `use_npu_fusion_attention` 开关，仅在 PI0 `compute_layer_complete` 调用点切换），不影响其他 Gemma 路径。

> **NPU 迁移坑：不支持 INT64 `cumsum`**（`manipulation/pi0/train/doc/README.md` §3.2，跨训练/推理共性）。Pi0 构造 attention mask / `position_ids` 时触发 `torch.cumsum`，走 int64 报 `aclnnCumsum failed ... DT_INT64`。修法：`att_masks` 统一转 `torch.int32` + `torch.cumsum(..., dtype=torch.int32)`，`pad_masks` 转 bool 后做 logical_and（规避 `aclnnBitwiseAndTensor failed ... DT_FLOAT`）。

## Links

- 配套训练优化：[ddp-static-graph](ddp_static_graph.md)
- 受益模型：[pi0](../manipulation/pi0.md)、[pi05](../manipulation/pi05.md)
- 网络结构：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 训练平台：[atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)（Pi0/Pi0.5 多卡训练实际平台）；[ascend-310p](../platforms/ascend_310p.md) / [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（family 对照）
- 跨域 attention 融合 canonical：[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
