---
type: Concept
title: Action Chunking（动作分块 / ACT Transformer）
description: VLA 模仿学习策略的核心结构思想：一次性预测一段连续动作序列（动作块，action chunk），而不是逐步预测，从而缓解逐步预测带来的误差累积。cann-recipes-embodied-ai 中由 ACT（Action Chunking with Transformers，act）模型直接体现，Pi0/Pi0.5 的 flow-matching 动作专家也以 chunk 形式整段输出动作，因此本页作为 canonical 概念页被多模型复用。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/act/infer_with_om/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Action Chunking（动作分块）

VLA 模仿学习策略的核心结构思想：**一次性预测一段连续动作序列（动作块，action chunk）**，而不是逐步预测，从而缓解逐步预测带来的误差累积。`cann-recipes-embodied-ai` 中由 **ACT**（Action Chunking with Transformers，[act](../manipulation/act.md)）模型直接体现，Pi0/Pi0.5 的 flow-matching 动作专家也以 chunk 形式整段输出动作，这一概念被多模型复用。

> 论文：Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware（ACT，arXiv:2304.13705）；上游开源仓 https://github.com/tonyzhaozh/act 。仓内适配基于 HuggingFace LeRobot 的 ACT 实现。

## 机制

ACT 是一种基于 **Transformer** 的模仿学习控制策略。核心思想（原文）：

> 以「动作分块（Action Chunking）」的方式一次性预测一段连续动作序列，从而有效缓解逐步预测带来的误差累积问题，并在多个双臂精细操作任务中验证了其有效性。

学术上 ACT 在训练时用一个 **CVAE**（条件变分自编码器）建模动作块分布、推理时只用解码器 Transformer 预测动作块；本仓 README 只表述到「Transformer + 动作分块」与端到端输入输出，CVAE 细节属上游模型本体语义，此处不展开。

## 输入 / 输出契约

| 项 | 说明 | shape |
| --- | --- | --- |
| `observation.images.*` | 多路 RGB 图像（1～3 路） | `[1, N_c, 3, H, W]`（示例 480×640） |
| `observation.state` | 机器人本体位姿 | `[1, N_k]`（示例 14，双臂自由度） |
| `actions`（输出） | 一次预测的动作块 | `[1, chunk_size, N_k]`（示例 `chunk_size=100`） |

- `chunk_size`：一次输出的机器人执行步数。ACT 示例 `chunk_size=100`，Pi0/Pi0.5 为 50。
- ResNet18 视觉 backbone：ACT 默认 `pretrained_backbone_weights: ResNet18_Weights.IMAGENET1K_V1`，离线/无网环境需提前缓存 `resnet18-f37072fd.pth` 到 `~/.cache/torch/hub/checkpoints/`。

## 与 flow-matching 动作专家的关系

Pi0/Pi0.5 的 [flow-matching-action-expert](flow_matching_action_expert.md) 同样以 chunk 形式整段输出动作（`actions [chunk_size, action_dim]`），区别在动作块的**生成方式**：

| 模型 | 动作块生成 | 输出形态 |
| --- | --- | --- |
| ACT | Transformer 单次前向直接回归整段动作块 | `[1, chunk_size, N_k]` |
| Pi0 / Pi0.5 | flow-matching / 扩散，对动作块多步去噪（10 步） | `[1, chunk_size, max_action_dim]` 后截断 |

二者共享「动作分块缓解误差累积」的思想，但 ACT 不走多步去噪，因此推理路径更短、更易整图导出为单个 OM（见下）。

## 昇腾部署

ACT 在 `cann-recipes-embodied-ai` 仅提供 OM 离线推理样例（无独立 torch 推理优化文档），整模型一次性导出为单个 `act.om`（不像 Pi0/Pi0.5 拆两段），ATC 命令简单：

```bash
atc --model=outputs/onnx/act.onnx --framework=5 --output=outputs/om/act --soc_version=Ascend310P1
```

OM 输出 action 需配 `policy_preprocessor` / `policy_postprocessor` 做归一化/反归一化才能落回环境动作空间；缺失时用 `migrate_policy_normalization.py` 生成 `<模型目录>_migrated/`。OM 部署范式详见 [om-atc-offline](../techniques/om_atc_offline.md)。训练侧（Atlas A2 8 卡，ALOHA transfer_cube）见 [act](../manipulation/act.md)。

## Links

- 模型页：[act](../manipulation/act.md)
- 同类动作块结构：[flow-matching-action-expert](flow_matching_action_expert.md)
- 离线部署：[om-atc-offline](../techniques/om_atc_offline.md)、[ascend-310p](../platforms/ascend_310p.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
