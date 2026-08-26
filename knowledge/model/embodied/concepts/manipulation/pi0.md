---
type: Concept
title: Pi0（π0 · VLA 流匹配模型 · 昇腾训练/在线推理/OM 离线三链路）
description: cann-recipes-embodied-ai 的操作类（manipulation）VLA 模型样例，演示 Pi0（π0） 在昇腾上的 训练（Atlas A2）/ 在线 torch 推理（A2）/ OM 离线推理（310P） 三条完整链路。本页是模型枢纽，架构与算子机制下放到 canonical 概念页，模型页只链接 + 记录 Pi0 专属配置与性能数字。
tags:
- task.design
- topic.model_architecture
- topic.graph_execution
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi0/train/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi0/infer_with_torch/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi0/infer_with_om/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
- 310p
---

# Pi0（π0 · VLA 流匹配模型 · 昇腾训练/在线推理/OM 离线三链路）

`cann-recipes-embodied-ai` 的操作类（manipulation）VLA 模型样例，演示 **Pi0（π0）** 在昇腾上的 **训练（Atlas A2）/ 在线 torch 推理（A2）/ OM 离线推理（310P）** 三条完整链路。架构与算子机制见各概念页；以下记录 Pi0 专属配置与性能数字。

> 论文：π0: A Vision-Language-Action Flow Model for General Robot Control（arXiv:2410.24164）。上游开源本体 OpenPI https://github.com/Physical-Intelligence/openpi ；仓内基于 HuggingFace LeRobot 对 Pi0 的迁移实现（固定 commit）。

## 模型简介

Pi0 是面向通用机器人控制的视觉-语言-动作（VLA）模型：基于预训练 VLM（PaliGemma）结合**流匹配（flow matching）/ 条件去噪扩散**机制，生成高频连续动作。整合 OXE 等开源数据集与自有数据共超 10,000 小时操作数据；在叠衣服、桌面清理、装盒等复杂长时序任务上，零样本与微调下均优于 OpenVLA / Octo / ACT 等基线。

架构是「慢系统 VLM 主干（PaliGemma）+ 快系统流匹配动作专家（Gemma）」双流结构，VLM 一次提取多模态前缀 KV cache，动作专家在其上**多步去噪**（默认 `num_steps=10`）输出动作块。完整架构、输入输出契约与昇腾算子融合机制详见 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)；动作块（action-chunking）思想对照 [action-chunking](../modules/action_chunking.md)。

## 链路一：Atlas A2 训练（LIBERO 模仿学习）

`manipulation/pi0/train/`：基于 LeRobot 在 `HuggingFaceVLA/libero` 上做离线模仿学习分布式训练。

- 硬件：昇腾 Atlas A2 8 卡；CANN 8.3.0+；任务 LIBERO 离线训练。
- 外部依赖：LeRobot 单独 clone，固定 commit `58f70b6bd370864139a3795ac3497a9eae8c42d5`（2025-11-27）；`setup.sh` 依次应用通用 Ascend 训练补丁与 PI0 专属补丁。预训练权重 `pi0_base` + tokenizer `google/paligemma-3b-pt-224`（gated model）需本地化。
- 长训配置 `pi0_libero.yaml`：`steps=30000`、每卡 `batch_size=8`、`policy.dtype=bfloat16`、`gradient_checkpointing=true`、`compile_model=false`。smoke 配置 `pi0_libero_smoke.yaml`（每卡 `batch_size=16`、`steps=20`）用于验证链路。
- `run_train.sh` 默认导出三项已验证优化开关：`LEROBOT_PI0_USE_FAST_BETA_SAMPLE=1`、`LEROBOT_PI0_USE_NPU_FUSION_ATTENTION=1`、`LEROBOT_PI0_DISABLE_OUTER_SUFFIX_CHECKPOINT=1`。

**训练吞吐对比**（Atlas A2 8 卡，每卡 `batch_size=24`，全局 batch 192，`steps=30`，`manipulation/pi0/train/doc/README.md`）：

| 优化项 | 吞吐 |
| --- | --- |
| baseline | 66 samples/s |
| NPU fusion attention | 71.11 samples/s |
| disable outer suffix checkpoint | 77.64 samples/s |
| 两者同时开启 | 81.77 samples/s（较基线端到端约 +24%） |

机制下放：disable-outer-suffix-checkpoint（单项收益最大）见 [gradient-checkpoint-refine](../techniques/gradient_checkpoint_refine.md)；NPU fusion attention 的 Pi0 局部接法（`_repeat_kv_heads` + `_npu_fusion_attention_forward`，实例级 `use_npu_fusion_attention` 开关，不全局 monkey-patch Gemma）同见该页。

**训练特有迁移点**（`manipulation/pi0/train/doc/README.md` §3）：NPU 不支持 INT64 `cumsum`——attention mask / `position_ids` 构造路径统一转 `int32`（`torch.cumsum(..., dtype=torch.int32)`），`pad_masks` 转 bool 后再 `logical_and`，规避 `aclnnCumsum failed ... DT_INT64`、`aclnnBitwiseAndTensor ... DT_FLOAT` 报错。

**评测**：CPU 跑 MuJoCo 仿真与渲染（`MUJOCO_GL=osmesa`）、NPU 跑 policy 推理（`--policy.device=npu`）。LIBERO 四 suite 粗评（每 task 1 次，共 40 case，`policy.n_action_steps=10`）：spatial 80%(8/10)、object 100%、goal 100%、libero_10 90%，聚合 **37/40 = 92.5%**。

## 链路二：A2 在线 torch 推理（单卡，80 ms）

`manipulation/pi0/infer_with_torch/`：单机单卡 A2 上跑 Pi0 torch 推理（koch 机械臂数据集，CANN 8.3.RC1，`torch-npu==2.1.0.post12`）。

- 输入：双路 RGB 图像 + 机器人本体状态 + 语言文本指令；输出：50×6 关节角度序列（koch 机械臂 6 自由度，`shape=[50,6]`）。
- 基于 `torch_npu` 的 `transfer_to_npu` 自动适配；float64 → float32 以打通并保精度。
- **性能：单次推理时间下降至约 80 ms**（达到优化目标）。优化后 profiling：昇腾计算时间总占比 94%，AI_CORE 融合算子占比 50%，单次计算耗时 71.6 ms，空闲 4.58 ms。
- 精度：固定 action_expert 高斯噪声采样，基于 koch 末端位姿 ATE（绝对误差）验证——位置 ATE 参考 [0, +0.03] m，姿态 ATE 参考 [0, +0.2] rad。

在线优化的核心是把原生 host-bound 的逐算子推理改造为昇腾亲和路径：Rotary（`npu_rotary_mul`）/ FA（`npu_prompt_flash_attention`）/ RMSNorm+残差（`npu_add_rms_norm`）/ QKV 融合 + torchair 整图编译。机制与代码片段集中在 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)；图模式 / 整图编译入口跨链 [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md) 与 [torchair](../../../inference/concepts/frameworks/torchair.md)；注意力融合对照 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。

## 链路三：310P OM 离线推理

`manipulation/pi0/infer_with_om/`：在 Ascend 310P 上做 PyTorch → ONNX → ATC → OM 离线部署（CANN 8.0.0~8.2.RC1）。示例模型 `BrunoM42/pi0_aloha_transfer_cube`（MuJoCo 双臂递方块微调，1 路摄像头 480×640，`chunk_size=50`，动作维 14）；适配基于 LeRobot commit `577cd10974b84bea1f06b6472eb9e5e74e07f77a`。

- **两段 OM 切分**：part1 VLM（`modeling_pi0_vlm.py`，输出 `past_kv_tensor` + `prefix_pad_masks`）+ part2 action expert（`modeling_pi0_action_expert.py`，10 步去噪，循环调用），`run_om_e2e.py` 端到端串联。VLM 导出落盘 `runtime_save/{past_kv_tensor,prefix_pad_masks}.pth`，action expert 导出读取它们（两步须同一 `--runtime-save-dir`）。
- ATC：`--soc_version=Ascend310P1`（须与 `npu-smi info` 一致）、`--precision_mode_v2=origin`，产出 `pi0_vlm.om` / `pi0_action_expert.om`。
- 为 ONNX/ATC 导出做的算子退化（融合算子改回基础算子）、KV cache 展平、dtype/mask/position-ids 约束、ONNX↔OM 逐段精度对齐、Gemma 补丁、`acl.mdl.execute 507011` 等部署阻塞——全部集中在 [om-atc-offline](../techniques/om_atc_offline.md)。
- 仿真评测：`eval_pi0_ascend.py` 接入 LeRobot eval / Aloha 仿真（`MUJOCO_GL=osmesa`）；微调后 Jaka 实机示例可跑通。

> 三种「静态图/图模式」对照：链路二的 torchair 整图编译是「torch 运行时入图」，链路三的 ATC OM 是「图固化离线执行」，二者目标都为消除逐算子下发开销，但 OM 路线更适合 310P 边缘且与训练/在线代码解耦。

## Links

- 网络结构：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)、[action-chunking](../modules/action_chunking.md)
- 升级模型：[pi05](pi05.md)
- 训练优化：[gradient-checkpoint-refine](../techniques/gradient_checkpoint_refine.md)
- 离线部署范式 / 平台：[om-atc-offline](../techniques/om_atc_offline.md)、[ascend-310p](../platforms/ascend_310p.md)
- 跨域：[npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md)、[torchair](../../../inference/concepts/frameworks/torchair.md)、[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
