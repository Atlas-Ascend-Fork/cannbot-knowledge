---
type: Concept
title: OpenVLA（自回归 VLA · 310P OM 离线推理）
description: cann-recipes-embodied-ai 的操作类 VLA 模型样例，演示 OpenVLA 在 Ascend 310P 上的离线模型转换、推理、精度验证与仿真评测。一手源：manipulation/openvla/infer_with_om/README.md。
tags:
- task.design
- topic.model_architecture
- topic.graph_execution
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/openvla/infer_with_om/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- 310p
---

# OpenVLA（自回归 VLA · 310P OM 离线推理）

`cann-recipes-embodied-ai` 的操作类 VLA 模型样例，演示 **OpenVLA** 在 **Ascend 310P** 上的离线模型转换、推理、精度验证与仿真评测。一手源：`manipulation/openvla/infer_with_om/README.md`。

> 论文：《OpenVLA: An Open-Source Vision-Language-Action Model》（arXiv:2406.09246）；上游开源仓 https://github.com/openvla/openvla。本样例使用官方在 `libero_object` 上微调的权重 `openvla/openvla-7b-finetuned-libero-object`。

## 模型范式：自回归 VLA

OpenVLA 是典型的 **视觉-语言-动作通用控制模型**：把视觉观测与语言指令统一编码到同一序列表示，用 **自回归（autoregressive）生成** 输出动作表示（动作 token / 离散化动作序列），再解码为可执行的连续控制量。它通过在大规模多任务机器人示范数据上学习「从感知与语义到动作」的统一映射，提升跨任务、跨场景泛化，降低逐任务单独训练策略的成本。

这与 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)（Pi0/Pi0.5 的流匹配动作专家）和 [action-chunking](../modules/action_chunking.md)（ACT 一次预测整段动作块）是两条不同的动作生成范式：OpenVLA 走自回归 token 解码，逐 token 生成动作 id。

## 输入 / 输出契约

源 README 给出的 OM 离线接口契约（`B`=batch size，离线验证常为 1；`T`=文本 token 长度；`C`=图像通道；`A`=动作维度）：

| 输入 | 含义 | dtype | shape | 备注 |
| --- | --- | --- | --- | --- |
| `input_ids` | 指令 / 提示词 token 序列 | `int64` | `[B, T]` | 含特殊 token |
| `attention_mask` | 文本有效位掩码 | `bool`（或 int） | `[B, T]` | 1/True 为有效 |
| `pixel_values` | RGB 图像经 processor 预处理后的张量 | `float16` | `[B, C, H, W]` | 启用 *fused vision backbone* 时 `C=6（3+3）`（两套视觉塔输入在通道维拼接），否则 `C=3`；分辨率常见 224×224 |

| 输出 | 含义 | dtype | shape | 备注 |
| --- | --- | --- | --- | --- |
| `actions` / `generated_ids` | 动作 token（离散动作序列 id） | `int64` | `[B, A]` | 后续用 `bin_centers` + `action_norm_stats` 反归一化得连续动作 |

## 昇腾 310P OM 离线部署链路

OpenVLA 遵循本域共享的 **OM/ATC 离线静态图范式** [om-atc-offline](../techniques/om_atc_offline.md)，部署在 [ascend-310p](../platforms/ascend_310p.md)。CANN 版本要求 `8.0.0 ~ 8.2.RC1`。推荐单机链路三步：

1. **导出 ONNX**（310P 宿主机用 Host CPU）：`convert_and_verify_onnx.py`，按结构切分为 **vision / llama_prefill / llama_decode** 三段子图分别导出。导出前需 `git apply -p1 modeling_llama.patch` 打到 conda 环境的 `site-packages/transformers/models/llama/`（补的是 **transformers 库的 LLaMA 实现，非 openvla 仓本身**），使算子匹配昇腾亲和算子。默认用 ONNXRuntime CPU 对比 PyTorch 输出打印 max/mean diff（可 `--no-validate` 跳过）。ONNX 导出把视觉投影 embedding 拼接进文本 embedding 序列首 token 之后（`torch.cat([input_embeddings[:, :1], projected_patch_embeddings, input_embeddings[:, 1:]], dim=1)`），再 pad 到固定 `target_seq_len`（pad 位 `position_id` 冻结于末位 `original_effective_seq_len-1`、非 0），以满足 OM 静态图定长输入——这是定长 shape 化自回归 VLA 的承重取舍。
2. **ATC 转 OM**（310P 上，`source` CANN 后）：`convert_onnx_to_om.sh`，`--soc-version Ascend310P3`，产出 vision_backbone.om / projector.om / embedding.om / vla_prefill.om / vla_decoder.om 等多段 OM。
3. **OM-backend sim-evaluator 仿真评测**：在 OpenVLA 官方 LIBERO 评测基础上改造，套用仓内 `sim/` 三个 patch（`robot_utils.patch` / `openvla_utils.patch` / `run_libero_eval.patch`）+ 新增 `openvla_om_utils.py`，把多段 OM 接入 `experiments.robot.libero.run_libero_eval`。

> 注意：OpenVLA 的 OM 路线把模型切成 vision 编码 + LLaMA prefill + LLaMA decode 多段子图分别转 OM、组合执行，是自回归生成（prefill/decode 分离）在 OM 离线静态图下的典型切分方式；这与 Pi0/ACT 等单段或少段 OM 切分不同。

## 精度验证

源 README 给出两种 NPU 验证法：

- **Mock 输入对齐**（`verify_om_onnx.py`）：构造固定输入（全 0 图像 + 固定指令 token），对比 PyTorch CPU/GPU 与 OM 310P NPU 输出。ONNX 导出环节的全流程对齐样例显示 `full_pipeline_action: max/mean abs diff = 0.000000e+00 ✓ MATCH`（rtol=0.001/atol=0.001）。
- **仿真功能测试**（MuJoCo / LIBERO）：policy 在 NPU 推理、Host CPU 渲染；无显示环境时设 `export MUJOCO_GL=egl` 走 EGL 无头渲染。评测日志（成功率）写入 `experiments/logs`，rollout 视频落 `rollout/<date>`。

## 关联

- 部署范式与平台：[om-atc-offline](../techniques/om_atc_offline.md)、[ascend-310p](../platforms/ascend_310p.md)
- 动作生成范式对照：[action-chunking](../modules/action_chunking.md)、[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 同为 310P OM 离线 / 310P 在线的操作类样例：[spirit-v1.5](spirit_v1_5.md)
- 昇腾亲和算子改造的同源思想（torch 在线路线）：[isaac-gr00t](isaac_gr00t.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
