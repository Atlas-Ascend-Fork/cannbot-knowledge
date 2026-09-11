---
type: Concept
title: ACT (Action Chunking with Transformers) · 昇腾训练 + 310P OM 离线推理
description: ACT 是论文 Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware（arXiv:2304.13705）提出的基于 Transformer 的模仿学习控制策略。核心思想是动作分块（Action Chunking）：一次性预测一段连续动作序列（action chunk），从而缓解逐步预测的误差累积，在多个双臂精细操作任务上验证有效。cann-recipes-embodied-ai 提供两条样例链路：Atlas A2 训练（基于 HuggingFace LeRobot）+ Ascend 310P OM 离线推理。
tags:
- task.design
- topic.model_architecture
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/act/train/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/act/infer_with_om/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
- 310p
---

# ACT (Action Chunking with Transformers)

ACT 是论文 *Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware*（arXiv:2304.13705）提出的基于 **Transformer** 的模仿学习控制策略。核心思想是**动作分块（Action Chunking）**：一次性预测一段连续动作序列（action chunk），从而缓解逐步预测的误差累积，在多个双臂精细操作任务上验证有效。`cann-recipes-embodied-ai` 提供两条样例链路：**Atlas A2 训练**（基于 HuggingFace LeRobot）+ **Ascend 310P OM 离线推理**。

> 上游算法仓 https://github.com/tonyzhaozh/act；仓内实现基于 HuggingFace LeRobot 的 ACT policy。动作分块结构详见 [action-chunking](../modules/action_chunking.md)。

## 输入 / 输出契约

输入/输出契约取自模型 `config.json.input_features`：

| 输入数据名 | dtype | shape |
| --- | --- | --- |
| `observation.images_xxx`（摄像头图像） | Float32 | `[1, N_c, 3, H, W]` |
| `observation.state`（机器人位姿） | Float32 | `[1, N_k]` |

| 输出数据名 | shape |
| --- | --- |
| `actions` | `[1, chunk_size, N_k]` |

- `N_c`：摄像头路数（训练决定，通常 1~3 路）；`N_k`：自由度（机器人构型决定）；`H,W`：RGB 分辨率；`chunk_size`：一次输出的执行步数。
- 样例模型 `lerobot/act_aloha_sim_transfer_cube_human`（ALOHA 仿真微调）：1 路 `observation.images.top` `[3,480,640]` + `observation.state` `[14]`，`action` `[14]`，`chunk_size: 100`。
- 视觉 backbone 默认 `pretrained_backbone_weights: ResNet18_Weights.IMAGENET1K_V1`；无网环境需预缓存 `resnet18-f37072fd.pth` 到 `~/.cache/torch/hub/checkpoints/`，否则模型构建阶段失败。

## Atlas A2 训练（LeRobot）

- 硬件 Atlas A2；CANN 8.3.0+；任务 `AlohaTransferCube-v0`；数据集 `lerobot/aloha_sim_transfer_cube_human`；外部框架 `huggingface/lerobot`（固定 commit `58f70b6bd370864139a3795ac3497a9eae8c42d5`，由 `setup.sh` checkout + `git apply` 已验证的 Ascend 训练补丁，含 `torchcodec` 视频解码容忍度修正）。
- 仓内只保存样例目录/配置/脚本/文档/补丁，**不内嵌 lerobot 源码**；`torch`/`torch_npu` 默认复用已激活的 Ascend 环境或由 `--torch-npu-wheel` 等参数注入本地 wheel（不硬编码下载链接，因有效组合依赖宿主架构/CANN/Ascend 软件栈）。
- 关键配置（`act_aloha.yaml`）：`policy.type: act`、`policy.device: npu`、`dataset.video_backend: torchcodec`、`steps: 100000`、`batch_size: 8`、`num_workers: 4`、`wandb.enable: true`；smoke 配置 `act_aloha_smoke.yaml`：`steps: 20`、`save_freq: 20`、`wandb.enable: false`。
- 启动：`run_train.sh act_aloha --port 29510`（`--resume` 续训）；smoke：`run_train.sh act_aloha_smoke --port 29510`。

### 已验证训练结果

- 配置：ALOHA `transfer_cube`，50 episodes / 20000 frames，**Atlas A2 8 卡**，`steps=100000`，per-device `batch_size=8`、全局 batch size 64，统计区间 W&B `train/steps=5000~20000`。
- 评测 `5×100` episodes，**总成功率 68.0%**（`MUJOCO_GL=osmesa` CPU 渲染 + `--policy.device=npu`）。

100-step 快速吞吐参考（`8 cards × bs64 × torchcodec`，`step 10~100`）：

| mean_updt_s | mean_data_s | end-to-end samples/s |
| ---: | ---: | ---: |
| 0.3191 | 0.3544 | 760.24 |

### 在线评测（仿真在 CPU，推理在 NPU）

ALOHA 在线评测依赖 MuJoCo 无头渲染。推荐做法：**MuJoCo 仿真与渲染走 CPU**（`export MUJOCO_GL=osmesa`），**policy 前向推理继续走 NPU**（`--policy.device=npu`）。`run_eval.sh` 仅轻量封装 `lerobot-eval`，参数透传：`--env.type=aloha --env.task=AlohaTransferCube-v0 --eval.n_episodes=100 --eval.batch_size=20`。

## Ascend 310P OM 离线推理

CANN 8.0.0~8.2.RC1；样例模型 `lerobot/act_aloha_sim_transfer_cube_human`；离线侧 lerobot 固定 commit `d9e74a9d374a8f26582ad326c699740a227b483c`（**与训练侧 `58f70b6` 不同**）。三阶段单机链路（OM/ATC 离线范式详见 [om-atc-offline](../techniques/om_atc_offline.md)）：

1. **导出 ONNX**（Host CPU）：`convert_and_verify_onnx.py --pretrained-policy-path act_model --output outputs/onnx/act.onnx --device cpu --opset 14`。默认用 ONNXRuntime CPU 对比 PyTorch，打印 max/mean abs diff（`--no-validate` 跳过）。样例：output shape `(1,100,14)`，Max abs diff `0.000371844`，Mean abs diff `0.000106432`。
2. **ATC 转 OM**（310P）：`atc --model=outputs/onnx/act.onnx --framework=5 --output=outputs/om/act --soc_version=Ascend310P1`，得到整模型单个 `act.om`。
3. **OM-backend sim-evaluator 评测**（310P，需 ACL/ACLLite）：`eval_act_ascend.py --policy.path=act_model --om_model_path=outputs/om/act.om --env.type=aloha --env.task=AlohaTransferCube-v0 --eval.batch_size=1 --eval.n_episodes=1 --env.episode_length=600 --seed=4412`，结果写 `outputs/eval/.../eval_info.json` 并打印 `Aggregated eval metrics`。

> 与 ACT 训练侧不同，310P 安装包用 `Ascend-cann-kernels-310b`；ACT 离线为**整模型单 OM**（不像 Pi0/Pi0.5 多段切分，对照 [om-atc-offline](../techniques/om_atc_offline.md)）。

### 精度验证

- mock 输入相似度对比：`verify_om_onnx.py --pretrained-policy-path act_model --onnx-model-path outputs/onnx/act.onnx --om-model-path outputs/om/act.om --seed 42`，按 `config.json` 生成确定性 dummy 输入（支持多摄像头），对比 ONNXRuntime(CPU) vs OM(NPU) 余弦相似度。
- Aloha 仿真功能测试：复用 `eval_act_ascend.py`，NPU 推理 + Host CPU 渲染。

### 归一化处理器（OM 部署必需）

OM 输出 action 要正确落回环境动作空间、OM 输入 observation 要与训练一致，需两份处理器产物：`policy_preprocessor.json`（推理前归一化）+ `policy_postprocessor.json`（输出 action 反归一化），各配 `*.safetensors`。模型目录可能自带；若只有 `model.safetensors + config.json`，在 lerobot 根目录运行 `src/lerobot/processor/migrate_policy_normalization.py --pretrained-path act_model` 生成 `act_model_migrated/`。`eval_act_ascend.py` 优先在 `--policy.path` 查找，否则回退同级 `<dir>_migrated/`。

## 相关页面

- 结构思想：[action-chunking](../modules/action_chunking.md)；对照另一种动作生成范式 [diffusion-policy](diffusion_policy.md)（扩散动作）与 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)（Pi0/Pi0.5 流匹配）。
- 离线部署：[om-atc-offline](../techniques/om_atc_offline.md)、[ascend-310p](../platforms/ascend_310p.md)。
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)