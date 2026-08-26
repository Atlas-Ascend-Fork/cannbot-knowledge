---
type: Concept
title: AgiBot Arm World Model（机械臂世界模型，昇腾 A2 训练+推理）
description: 'AgiBot Arm World Model 是本仓打包的一个机械臂世界模型工作流样例，基于 Wan2.1-Fun-V1.1-1.3B-Control 视频扩散模型，在 AgiBotWorld 风格数据上做轨迹条件（trajectory-conditioned）的视频世界生成。提供多卡训练样例 + 基于 PyTorch 的单卡推理样例，面向昇腾 NPU（README 标注 Device: Ascend910，对应 Atlas A2 级硬件）。训练默认 8 NPU，推理默认单卡。模型本体复用上游 modelscope/DiffSynth-Studio 中的 Wan 系列实现，本仓自带训练/推理脚本、数据加载、轨迹/动作工具与 lvdm/ 第三方模块。'
tags:
- task.design
- topic.model_architecture
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/world_model/agibot-arm-world-model/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/world_model/agibot-arm-world-model/doc/optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
- '910'
---

# AgiBot Arm World Model（机械臂世界模型，昇腾 A2 训练+推理）

## Summary

AgiBot Arm World Model 是本仓打包的一个**机械臂世界模型**工作流样例，基于 `Wan2.1-Fun-V1.1-1.3B-Control` 视频扩散模型，在 AgiBotWorld 风格数据上做轨迹条件（trajectory-conditioned）的视频世界生成。提供**多卡训练样例 + 基于 PyTorch 的单卡推理样例**，面向昇腾 NPU（README 标注 Device: Ascend910，对应 Atlas A2 级硬件）。训练默认 8 NPU，推理默认单卡。模型本体复用上游 `modelscope/DiffSynth-Studio` 中的 Wan 系列实现，本仓自带训练/推理脚本、数据加载、轨迹/动作工具与 `lvdm/` 第三方模块。

> 当前验证范围仅为轻量工程检查：训练脚本 import smoke test、推理脚本 import smoke test、shell 语法检查；完整性能与精度结果需在目标 release 环境正式端到端运行后补充。

## 外部依赖

- 框架：`modelscope/DiffSynth-Studio`（`pip install -e .`，外部上游仓），Wan 模型支持参考其文档；本样例不拷入 DiffSynth 源码树，推荐二者同级放在同一 workspace。
- 软件栈（README）：`CANN==8.5.1`、`torch==2.1.0`、`torch-npu==2.1.0.post12`、Python 3.10；`torch`/`torch_npu` 按目标昇腾环境安装、不盲目 pin。
- 模型权重需备齐：`diffusion_pytorch_model.safetensors`、`models_t5_umt5-xxl-enc-bf16.pth`、`Wan2.1_VAE.pth`、`models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth`。

## 训练设计（一手）

- **49 帧训练组织**：训练样本固定 49 帧；加载器合并同一 episode 的**两个连续 clip**（two consecutive clips），再从合并段采样一个随机连续 49 帧窗口（两 clip 的 text prompt 始终拼接）——为机械臂运动预测提供更长时序连续性、改善运动一致性。**fallback**：当 episode 内下一 clip 不存在时，退回单 clip 采样，并对不足的帧做末帧 padding（last-frame padding）。
- **多条件输入**：`control_video`（渲染的轨迹监督）+ `reference_image`（保留场景外观）+ `input_image`（维持时序续接）+ text prompt（保留语言条件兼容性），显式分离「场景外观」与「运动控制」，提升机械臂运动生成可控性。
- **启动**：`accelerate launch` + `configs/accelerate_config_zero2.yaml`（ZeRO-2），8 NPU，`NUM_PROCESSES` 必须与 accelerate config 一致。关键超参（`run_train.sh`）：`--height 480 --width 640 --num_frames 49 --learning_rate 1e-5 --num_epochs 100 --save_steps 2000 --trainable_models dit --extra_inputs control_video,reference_image,input_image --text_dropout_prob 0.1 --gradient_accumulation_steps 2`；脚本设 `TORCHINDUCTOR_DISABLE=1` / `NPU_DISABLE_TORCHINDUCTOR=1`（关闭 inductor）。

## 推理设计（一手 · 分块自回归）

推理按 chunk 逐段进行，而非一次生成整段长序列：
- chunk 0 用 ground-truth 首帧作 `input_image`；
- 后续 chunk 用上一段生成的最后一帧作为下一段 `input_image`；
- 首帧始终作为固定 `reference_image`；
- 轨迹图按 chunk 切片。

收益：相比一次性长视频生成显著降低 NPU 实际推理压力，续接逻辑更清晰、贴合 rollout 式预测。这种「整段输出后递推续接」的分块思路与本域 [action-chunking](../modules/action_chunking.md) 的动作分块在颗粒度组织上同源（一个产视频帧块、一个产动作块）。

- **复现关键参数**：推理 `infer_fun_control_1_3b_text.py` 的 argparse **默认** `--cfg_scale 5.0 --seed 42 --chunk_size 49`（`chunk_size` 默认 `=CHUNK_SIZE`，`CHUNK_SIZE=49`，需满足 `(N-1)%4==0`）；脚本 docstring 用法示例与 `run_infer.sh`（`CFG_SCALE:-3.0`）实际**传入** `--cfg_scale 3.0`——区分「脚本默认 5.0」与「示例/shell 传入 3.0」。训练 `train_fun_control_1_3b_text_49frames.py` 传 `--remove_prefix_in_ckpt "pipe.dit."`（存 ckpt 时剥离 `pipe.dit.` 前缀，仅落 DiT 权重）。

单卡推理（`run_infer.sh`，`ASCEND_RT_VISIBLE_DEVICES=0`）关键参数：`--cfg_scale 3.0 --num_inference_steps 50 --chunk_size 49 --device npu`，并**同时传 `--only_mp4` 与 `--save_mp4`**。源码 `if not args.only_mp4: save_frames_as_jpg(...)`——`--only_mp4` 生效时**不落中间帧 jpg、仅出 mp4**（mp4 在 `OUTPUT_DIR/mp4/`）；仅当**不加 `--only_mp4`** 时才把帧写到 `OUTPUT_DIR/<task>/<episode>/<rollout>/video/`。

## 数据布局（一手）

训练数据 `DATA_ROOT` 下按 `task_id/episode_id/clip_idx/` 组织，含 `text.txt`、`annotation.json`、`proprio_stats.h5`、`head_intrinsic_params.json`、`head_extrinsic_params_aligned.json`、`videos/`；可选 `split.json`。测试输入按 `task_id/episode_id/` 含 `frame.png` 等。

## 架构定位与跨链

- 去噪主干为 Wan2.1 系视频扩散 DiT 结构（`--trainable_models dit`），属 DiT 类世界模型；参见 cann-infer [dit](../../../inference/concepts/modules/dit.md)。
- 与 Cosmos 系不同，本样例未做 NPU 融合算子替换或图模式适配；优化集中在训练数据组织、多条件设计与分块自回归推理。
- VAE（`Wan2.1_VAE.pth`）做视频隐空间编解码，参见 cann-infer [vae](../../../inference/concepts/modules/vae.md)。

## 相关页面

- 同分类 Cosmos 世界模型：[cosmos-predict2.5](cosmos_predict2_5.md)｜[cosmos-transfer2.5](cosmos_transfer2_5.md)
- 动作分块思想：[action-chunking](../modules/action_chunking.md)
- DiT 模块：[dit](../../../inference/concepts/modules/dit.md)｜VAE：[vae](../../../inference/concepts/modules/vae.md)
- A2 平台（空间智能域同款硬件页）：[atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
