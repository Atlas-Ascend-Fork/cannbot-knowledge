---
type: Concept
title: Spirit-v1.5（千寻智能 VLA · 310P 在线推理）
description: cann-recipes-embodied-ai 的操作类 VLA 模型样例：在 Ascend 310P 平台上适配 Spirit-v1.5 并做推理。一手源：manipulation/spirit-v1.5/infer_with_torch/README.md。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/spirit-v1.5/infer_with_torch/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- 310p
---

# Spirit-v1.5（千寻智能 VLA · 310P 在线推理）

`cann-recipes-embodied-ai` 的操作类 VLA 模型样例：在 **Ascend 310P** 平台上适配 **Spirit-v1.5** 并做推理。一手源：`manipulation/spirit-v1.5/infer_with_torch/` 下的昇腾适配源 `attention_processor_patch.py`、`modeling_spirit_vla.py` 与 `README.md`。

> Spirit-v1.5 是千寻智能（Spirit AI）自研的具身智能模型，在 2026.1.12 的 RoboChallenge 评测中取得综合排名第一，在多任务连续执行、复杂指令拆解、跨构型迁移等维度表现稳定（据 `cann-recipes-embodied-ai` 适配 README）。上游开源仓 https://github.com/Spirit-AI-Team/spirit-v1.5。

## 部署形态：310P 在线 torch 推理

与同域 [openvla](openvla.md) 的 OM 离线路线不同，Spirit-v1.5 走 **`infer_with_torch`**（torch 在线推理）路线，目标平台同为 [ascend-310p](../platforms/ascend_310p.md) 系列。CANN 版本要求 `8.3.RC1`，依赖 cann-toolkit 与 `Atlas-cann-kernels_310p` 二进制算子包。

## 代码与权重准备

样例采用「Spirit AI 官方仓 + `cann-recipes-embodied-ai` 昇腾适配文件覆盖」的方式：

1. clone `cann-recipes-embodied-ai` + 千寻官方仓 `spirit-v1.5`；
2. 将 `cann-recipes-embodied-ai/manipulation/spirit-v1.5/` 下列文件拷贝（同名替换）进官方仓对应位置：

   | 昇腾适配文件 | Spirit AI 官方仓位置 |
   | --- | --- |
   | `infer_with_torch/pyproject.toml` | `pyproject.toml` |
   | `infer_with_torch/requirements.txt` | `requirements.txt` |
   | `infer_with_torch/modeling_spirit_vla.py` | `model/modeling_spirit_vla.py` |
   | `infer_with_torch/attention_processor_patch.py` | `model/attention_processor_patch.py` |
   | `infer_with_torch/infer_mozrobot_ascend.py` | `scripts/infer_mozrobot_ascend.py` |

3. 下载权重：Base `Spirit-v1.5`、微调 `Spirit-v1.5-for-RoboChallenge-move-objects-into-box`；可选 `Qwen/Qwen3-VL-4B-Instruct`（VLM 主干）。

昇腾适配机制集中在上述两份覆盖文件里：

## 昇腾适配机制

**AttnProcessorNPU：SDPA → npu_prompt_flash_attention。** `attention_processor_patch.py` 定义 `class AttnProcessorNPU(AttnProcessor2_0)`，完全复用 diffusers `AttnProcessor2_0` 的前后逻辑（group_norm / to_q,k,v / norm_q,k / to_out），**只把中间的注意力计算替换为** `torch_npu.npu_prompt_flash_attention`：

- q/k/v 先 `.to(torch.float16)` 再入算子（fp16 计算，输出回 origin_dtype）；
- `input_layout="BSND"`、`num_heads=attn.heads`、`scale_value=1/sqrt(head_dim)`；
- `pre_tokens=65535, next_tokens=65535`（全可见，非因果），`atten_mask` 透传。

**模型本体：DiT 流匹配 action expert + Qwen3-VL 主干。** `modeling_spirit_vla.py` 顶部 `from torch_npu.contrib import transfer_to_npu` 做全局设备迁移、`from attention_processor_patch import AttnProcessorNPU`。动作生成网络是 `class BaseDiT(ModelMixin, ConfigMixin)`，由若干 `BasicTransformerBlock` 堆叠（配 `TimestepEncoder` / `AdaLayerNorm` 注入时间步条件）；每个 block 在构造其 attention 时传入 `processor=AttnProcessorNPU()`，从而把昇腾 FA 注入到 DiT 的每一层。VLM 主干为 `Qwen3VLForConditionalGeneration`（默认 `Qwen/Qwen3-VL-4B-Instruct`），`select_action` 里以 `self.qwen.forward(..., output_hidden_states=True)` 取末几层 hidden 拼成 `vlm_last_embed`，经 `proj_vlm_output` 投影后作为 DiT 的 `encoder_hidden_states`（视觉-语言条件）。

**推理：flow-matching Euler 去噪迭代。** `_sample_actions_unified` 从噪声 `x_t` 起步，`dt = -1.0/num_steps`（默认 `num_steps=10`），每步 `_denoise_step` 调 DiT 预测速度场 `v_t`、按 Euler `x_t += dt * v_t` 更新，迭代 `num_steps` 步得到去噪后的动作序列。

## 环境

与千寻官方一致用 `uv` 管理环境：进入官方仓执行 `uv sync` 自动解析依赖，根目录生成 `.venv`，`source .venv/bin/activate` 激活后 `uv pip list` 检查。推理按官方仓 README 指导执行推理脚本（`infer_mozrobot_ascend.py`）。

## 关联

- 同为 310P 操作类 VLA 样例（OM 离线对照）：[openvla](openvla.md)
- 目标平台：[ascend-310p](../platforms/ascend_310p.md)
- 动作生成范式参考：[action-chunking](../modules/action_chunking.md)
- 同走 torch 在线 + 昇腾算子化路线（A3 推理）：[isaac-gr00t](isaac_gr00t.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)

<!-- cannbot:related:start -->
## 相关

- [Action Chunking（动作分块 / ACT Transformer）](../modules/action_chunking.md)（`related`）：**推理：flow-matching Euler 去噪迭代。** `_sample_actions_unified` 从噪声 `x_t` 起步，`dt = -1.0/num_steps`（默认 `num_steps=10`），每步 `_denoise_step` 调 DiT 预测速度场 `v_t`、按 Euler `x_t += dt * v_t` 更新，迭代 `num_steps` 步得到去噪后的动作序列。；VLA 模仿学习策略的核心结构思想：**一次性预测一段连续动作序列（动作块，action chunk）**，而不是逐步预测，从而缓解逐步预测带来的误差累积。前者生成完整动作序列，后者说明这种序列的块级控制语义；Spirit 的多步 DiT 去噪不等于 ACT 单次前向。
<!-- cannbot:related:end -->
