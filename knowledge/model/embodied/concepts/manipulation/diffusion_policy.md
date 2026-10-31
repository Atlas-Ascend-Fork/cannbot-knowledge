---
type: Concept
title: Diffusion Policy (DP) · 310P OM 离线推理
description: 'Diffusion Policy（DP）出自论文 Diffusion Policy: Visuomotor Policy Learning via Action Diffusion（RSS 2023）。它把机器人策略表示为一个条件去噪扩散过程：相比传统自回归形式，具备更好的多模态动作分布处理能力和高维空间稳定性，是许多后续研究（如 3D 扩散策略）的基石。cann-recipes-embodied-ai 提供其 Ascend 310P OM 离线推理样例（基于 HuggingFace LeRobot 的 DP policy）。'
tags:
- task.design
- topic.model_architecture
- topic.graph_execution
- topic.diffusion
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/diffusion-policy/infer_with_om/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/diffusion-policy/infer_with_om/eval_dp_ascend.py
  role: implementation
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:37Z'
platforms:
- 310p
---

# Diffusion Policy (DP)

Diffusion Policy（DP）出自论文 *Diffusion Policy: Visuomotor Policy Learning via Action Diffusion*（RSS 2023）。它把机器人策略表示为一个**条件去噪扩散过程**：相比传统自回归形式，具备更好的多模态动作分布处理能力和高维空间稳定性，是许多后续研究（如 3D 扩散策略）的基石。`cann-recipes-embodied-ai` 提供其 **Ascend 310P OM 离线推理**样例（基于 HuggingFace LeRobot 的 DP policy）。

> 上游算法主页 https://diffusion-policy.cs.columbia.edu/；扩散式动作生成与 [action-chunking](../modules/action_chunking.md)（ACT 一次性整段预测）、[flow-matching-action-expert](../modules/flow_matching_action_expert.md)（Pi0/Pi0.5 流匹配）并列为三种动作生成范式。

源：`cann-recipes-embodied-ai/manipulation/diffusion-policy/infer_with_om/README.md`（仅提供 OM 离线推理样例，**未提供 DP 训练样例**）。

## 模型级契约（config.json）

下表是 DP **策略级**（端到端）的输入/输出，取自模型 `config.json.input_features`——**注意它不是 OM 图的 I/O**（OM 只替换内部 UNet 单步，见下文「OM 化边界」）：

| 输入数据名 | dtype | shape |
| --- | --- | --- |
| `observation.images_xxx`（摄像头图像） | Float32 | `[1, N_c, 3, H, W]` |
| `observation.state`（机器人位姿） | Float32 | `[1, N_k]` |

| 输出数据名 | shape |
| --- | --- |
| `actions` | `[1, n_action_steps, N_k]` |

- `N_c` 摄像头路数；`N_k` 自由度；`H,W` RGB 分辨率；`n_action_steps` 策略实际执行的动作步数（≠ UNet 采样长度 `horizon`，见下）。
- 样例模型 `lerobot/diffusion_pusht`（MuJoCo `PushT` 任务微调）：1 路 `observation.image` `[3,96,96]` + `observation.state` `[2]`，`action` `[2]`，`n_action_steps: 8`，`horizon: 16`。

### OM 化边界（只 OM 化 UNet 去噪器）

导出 / ATC 转换 / OM 推理的对象**只是扩散 UNet 去噪器本身**，不是端到端策略。DP 的视觉/状态编码器、噪声调度器（scheduler）、整个去噪循环与动作队列**仍跑在 PyTorch 侧**，OM 只在每个去噪步被调用一次替换 UNet 的单步前向：

- ONNX/OM 图的输入是 `sample`（`(1, horizon, action_dim)`）、`t`、`global_cond`，输出 `model_output`——即 UNet 单步去噪，而非 `observation.* → actions`。
- `convert_and_verify_onnx.py` docstring：`Export ONLY the UNet forward to ONNX with inputs (sample, t, global_cond)`；`global_cond = policy.diffusion._prepare_global_conditioning(observation)` 由编码器在 PyTorch 侧算出后喂给 UNet。
- `eval_dp_ascend.py` 用 `class OmUnetModule(nn.Module)`（`"UNet replacement that calls Ascend OM"`）在 `policy.diffusion.unet = OmUnetModule(om_model_path)` 处热替换 UNet，其余 `Loads a PyTorch DiffusionPolicy (for encoders, scheduler logic, and queueing)`。
- **`horizon` 与 `n_action_steps` 的关系**：UNet 在 `horizon` 长度上去噪（`sample=torch.zeros((1, horizon, action_dim))`），样例 `horizon=16` 故 ONNX 输出 `(1,16,2)`；策略再从中切片 `n_action_steps=8` 步实际执行。

## Ascend 310P OM 离线推理

源：`manipulation/diffusion-policy/infer_with_om/README.md`。CANN 8.0.0~8.2.RC1（安装包 `Ascend-cann-kernels-310p`）；需 lerobot 可编辑安装（钉定 commit）+ aloha/pusht 仿真依赖，MuJoCo 无头渲染 `export MUJOCO_GL=egl`；其中 `pymunk<7.0.0`（版本过高不兼容）为唯一需注意的约束。三阶段单机链路（OM/ATC 离线范式详见 [om-atc-offline](../techniques/om_atc_offline.md)）：

1. **导出 ONNX**（Host CPU）：`convert_and_verify_onnx.py --pretrained-policy-path dp_model --output outputs/onnx/dp.onnx --device cpu --opset 14`，导出对象只是 UNet 去噪器（输入 `sample`/`t`/`global_cond`，输出 `model_output`；`sample` 取 `(1, horizon, action_dim)`），默认 ONNXRuntime CPU 对比 PyTorch（`--no-validate` 跳过）。样例 `diffusion_pusht` `horizon=16`，故 output shape `(1,16,2)`，**Max abs diff `1.22935e-07`，Mean abs diff `3.55503e-08`，余弦相似度 min/max/mean = 1.000000**（UNet 单步去噪精度对齐极好）。
2. **ATC 转 OM**（310P）：`atc --model=outputs/onnx/dp.onnx --framework=5 --output=outputs/om/dp --soc_version=Ascend310P1`，得 `dp.om`。`soc_version` 据 `npu-smi info` 的芯片型号填写（如 `310P1` → `Ascend310P1`）。
3. **OM-backend sim-evaluator 评测**（310P，需 ACL/ACLLite）：`eval_dp_ascend.py --policy.path=dp_model --om_model_path=outputs/om/dp.om --env.type=pusht --eval.batch_size=1 --eval.n_episodes=1 --env.episode_length=600 --seed=4412`，结果写 `outputs/eval/.../eval_info.json` 并打印 `Aggregated eval metrics`。

### 精度验证

mock 输入相似度对比：`verify_om_onnx.py --onnx-model-path outputs/onnx/dp.onnx --om-model-path outputs/om/dp.om --seed 42 --n-action-steps 16`。脚本按命令行参数（默认 `--n-action-steps 8` / `--action-dim 2` / `--global-cond-dim 132`）用固定 `--seed` 经 `rng.standard_normal` 造确定性 **UNet 级** dummy 输入（`sample`/`global_cond`），对比 ONNXRuntime(CPU) vs OM(NPU)，**不读 `config.json`**。

> 上游 README 称该脚本「据 `config.json` 生成」dummy 输入，与 `verify_om_onnx.py` 实现不符：脚本不读取 `config.json`，全部输入维度由 CLI 参数构造。

> README 仅给出 ONNX 导出阶段的 diff/相似度数字，**未提供 OM(NPU) 端到端 PushT 任务成功率**（unverified）。

### 归一化处理器（OM 部署必需）

与 ACT 一致：策略输入 observation 预归一化、策略生成 action 反归一化（处理器位于 policy.select_action 前后；OM 只接收 UNet 的 sample/t/global_cond 并返回单步去噪输出）需 `policy_preprocessor.json` + `policy_postprocessor.json`（各配 `*.safetensors`）。若模型只带 `model.safetensors + config.json`，运行 `../lerobot/src/lerobot/processor/migrate_policy_normalization.py --pretrained-path dp_model` 生成 `dp_model_migrated/`。`eval_dp_ascend.py` 优先在 `--policy.path` 查找，否则回退同级 `<dir>_migrated/`。

## 相关页面

- 动作生成范式对照：[act](act.md)（动作分块 Transformer）、[action-chunking](../modules/action_chunking.md)、[flow-matching-action-expert](../modules/flow_matching_action_expert.md)。
- 离线部署：[om-atc-offline](../techniques/om_atc_offline.md)、[ascend-310p](../platforms/ascend_310p.md)。
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1)
