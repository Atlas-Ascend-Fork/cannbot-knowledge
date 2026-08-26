---
type: Concept
title: SmolVLA（SmolVLM 主干 · Atlas A2 LIBERO 训练）
description: cann-recipes-embodied-ai 的操作类 VLA 训练样例：在 昇腾 Atlas A2（910b） 上用 LeRobot 训练框架对 SmolVLA 做 LIBERO 离线模仿学习训练 + 在线评测。一手源：manipulation/smolvla/train/README.md 与 manipulation/smolvla/train/doc/README.md。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/smolvla/train/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# SmolVLA（SmolVLM 主干 · Atlas A2 LIBERO 训练）

`cann-recipes-embodied-ai` 的操作类 VLA **训练**样例：在 **昇腾 Atlas A2（910b）** 上用 **LeRobot** 训练框架对 **SmolVLA** 做 LIBERO 离线模仿学习训练 + 在线评测。

> SmolVLA 是基于 **SmolVLM 主干**（`HuggingFaceTB/SmolVLM2-500M-Video-Instruct`）的轻量 VLA。本样例是仓内少数走 **训练**（非推理）的操作类样例。上游训练框架 `huggingface/lerobot`，固定 commit `58f70b6bd370864139a3795ac3497a9eae8c42d5`。

## 适用场景

- 硬件：昇腾 [ascend-310p](../platforms/ascend_310p.md) 之外的训练形态 —— **Atlas A2 8 卡**；CANN `8.3.0+`
- 任务：`HuggingFaceVLA/libero` 离线训练
- 框架：外部 `lerobot`（不内嵌源码，`setup.sh` clone 并 checkout 固定 commit，再叠加通用 Ascend 训练补丁 + SmolVLA 专属补丁）

仓内只保存 recipe / 配置 / 文档 / 补丁；`lerobot`、数据集、base 模型、VLM 权重均通过工作区相对路径引用，需自行准备 `dataset/` `models/` `ckpt/` 三目录。

## 训练配置与样本预算

两份配置：`smolvla_libero_smoke.yaml`（冒烟，`steps:20`/`batch_size:32`/`num_workers:0`/`wandb.enable:false`）和 `smolvla_libero.yaml`（正式，`batch_size:32`/`num_workers:4`/`steps:1600`/`policy.empty_cameras:1`/`save_freq:500`，base 与 VLM 均用本地目录）。

训练范式（两份配置 `policy` 段一致）：**冻结 SmolVLM 视觉编码器、仅训练 action expert 与 state projection**（`freeze_vision_encoder:true` + `train_expert_only:true` + `train_state_proj:true`），并加载 VLM 权重（`load_vlm_weights:true`、`tokenizer_max_length:48`、内层 `num_steps:10`）——这是该样例承重的训练设计取舍，而非流水账超参。

样本预算换算：LeRobot 官方 `SmolVLA + LIBERO` 常见口径 `100000 steps × batch_size 4 = 400000 samples`；本样例 8 卡、每卡 `batch_size=32`、全局 batch `256`，对齐步数 `400000 / 256 ≈ 1562.5`，取整为 `1600 steps`。

> `run_train.sh` 仅解析 `output_dir` / `job_name` 的「单行简单键值」写法（不支持块标量、嵌套、YAML 锚点），并自动追加时间戳；格式不符直接报错退出。

## 关键迁移点（Ascend 适配补丁）

迁移问题与处理（均落到 SmolVLA 专属 patch）：

- **权重加载 `copy_d2d / 507001`**：原 `PreTrainedPolicy.from_pretrained()` 可能直接把 safetensors 加载到 NPU 触发设备间 copy 失败；补丁在 `modeling_smolvla.py` 增加自定义 `from_pretrained()`，先在 CPU 完成读取与 `load_state_dict()`，再迁移到目标设备。
- **相机键名不一致**：SmolVLA base 预训练图像键名为 `camera1/camera2/camera3`，而 LIBERO 常见 `observation.images.image / image2`；910b 稳定训练口径**不带 `rename_map`**，保留 `policy.empty_cameras:1` 补齐缺失第三路相机。出现 `All image features are missing from the batch` 时应先核对 batch 键名与 `policy.config.image_features`。
- **本地模型 / `local_files_only`**：无网环境补充本地目录判断，本地场景用 `local_files_only=True` 减少在线访问（依赖 `smolvla_base` 与 `SmolVLM2-500M-Video-Instruct` 两类本地目录）。
- **磁盘配额**：`XDG_CACHE_HOME` / `HF_HOME` / `HF_DATASETS_CACHE` / `HF_HUB_CACHE` 指向工作区大盘路径，规避 `Disk quota exceeded`。
- **评测断言临时放宽**：SmolVLA patch 对 `lerobot_eval.py` 的 rollout policy 类型 / `action_numpy.ndim` 与 `episode_data` 拼接连续性的少量 `assert` 临时放宽（保留原始位置便于后续恢复）。
- **无头渲染排障**：评测报 `Failed to load library ('libOSMesa.so.0')` 时，装 OSMesa 运行库 + `export MUJOCO_GL=osmesa`；`run_eval.sh` 传 `--policy.device=npu` / `npu:x` 时会在启动前自动同步设置 `LEROBOT_EVAL_NPU_DEVICE`，免去评测脚本内部硬编码设备号。

## 已验证结果

训练吞吐对比（`samples/s` 为总吞吐，非单卡）：

| 平台 | 训练硬件 | 训练配置 | 全局 batch | 稳定阶段 `updt_s` | 训练吞吐 |
| --- | --- | --- | --- | --- | --- |
| 910b | 昇腾 Atlas A2 8 卡 | 每卡 `batch_size:32` | `256` | `1.05 ~ 1.10s` | `233 ~ 244 samples/s` |
| h20 | 2 卡 | 每卡 `batch_size:8` | `16` | `0.176 ~ 0.181s` | `88.4 ~ 90.9 samples/s` |

基于 `100000` step checkpoint、`seed=3000`、`eval.n_episodes=1` 的一轮 LIBERO 在线评测（policy 走 NPU、仿真 CPU 侧 `MUJOCO_GL=osmesa`；CUDA 主机评测可用 `rename_map` 映射 image→camera）：`libero_spatial 90.0%` / `libero_object 100.0%` / `libero_goal 90.0%` / `libero_10 80.0%`，平均 `90.0%`。

## Evidence

- [cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1) — [`manipulation/smolvla/train/README.md`](https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/smolvla/train/README.md)、[`manipulation/smolvla/train/doc/README.md`](https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/smolvla/train/doc/README.md)（训练样例 README 与迁移文档）。

## 关联

- 动作生成范式对照：[action-chunking](../modules/action_chunking.md)、[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 同为 LIBERO 操作类、走 VLM 主干的 VLA 样例：[openvla](openvla.md)
- 多卡训练静态图相关（同仓训练侧技术）：[ddp-static-graph](../techniques/ddp_static_graph.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
