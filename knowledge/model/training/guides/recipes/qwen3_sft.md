---
type: Guide
title: Qwen3-1.7B MindSpeed-LLM SFT 单卡 A3 alpaca 入门样例
description: Qwen3-1.7B（dense）使用 MindSpeed-LLM + Megatron-LM core_v0.12.1 的 mcore 训练栈，在单卡 A3 上对 alpaca 指令数据集执行 SFT（监督微调）。流程包含 HF 模型转 mcore、alpaca 数据转换、SFT 训练及 mcore 转回 HF，需要 HF↔mcore 权重格式互转。与 Qwen2.5 的 veRL 原生 FSDP+vLLM 单卡 RL 路线不同，SFT 不包含 rollout 或奖励函数环节。
tags:
- task.implementation
- topic.model_adaptation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_sft/qwen3/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a2
- a3
---

# Qwen3-1.7B MindSpeed-LLM SFT 单卡 A3 alpaca 入门样例

## Summary

昇腾 SFT（监督微调）最小上手样例：用 [mindspeed](../../concepts/frameworks/mindspeed.md) 系的 **MindSpeed-LLM**（叠加 Megatron-LM `core_v0.12.1` 的 mcore 训练栈），对 **Qwen3-1.7B**（dense）在 **alpaca** 指令数据集上跑监督微调，默认启动 **1 个 NPU 逻辑设备上的训练进程**。把昇腾上「HF 模型转 mcore → alpaca 数据转换 → SFT 训练 → mcore 转回 HF」的全链路压到一台机器的单个 NPU 逻辑设备上跑通，是 dense 模型微调的入门梯子；同框架的大规模实践（DeepSeek-V3 HiF8/MXFP8 低精度预训练）见 [mindspeed](../../concepts/frameworks/mindspeed.md)。Qwen3 dense 本体作为推理模型见跨域页 [qwen-dense](../../../inference/concepts/models/qwen_dense.md)。

与 [qwen2.5-rl](qwen2_5_rl.md)（veRL 原生 FSDP+vLLM 的单卡 RL 入门）的关键差异：训练栈走 **MindSpeed-LLM + Megatron mcore**（Megatron 风格、需要 HF↔mcore 权重格式互转），阶段是 **SFT 而非 RL**，无 rollout / 奖励函数环节。

## 训练配置

| 维度 | 配置 |
| --- | --- |
| 模型 | Qwen3-1.7B（dense，HF 权重 `Qwen/Qwen3-1.7B`） |
| 阶段 | SFT（监督微调，`--stage sft`） |
| 框架 | MindSpeed-LLM（commit `6fe0df7`）+ Megatron-LM `core_v0.12.1`（mcore） |
| 数据集 | alpaca（指令微调，`OmniData/alpaca`，AlpacaStyleInstructionHandler） |
| 平台 / 卡数 | Atlas A3；脚本 `NPUS_PER_NODE=1`，表示 1 个 NPU 逻辑设备；一站式平台镜像另提供 A3/A2 选项 |
| 序列长度 | 训练脚本配置 4K；数据预处理 `--seq-length` 缺省 None，不指定时不截断，二者分开设置 |

## 环境与数据准备

环境二选一：本地基于样例 `Dockerfile.cann.mindspeed.qwen3` 构建镜像，或在一站式平台直接跑 `build_project_platform.sh`——两条路最终都落到同一栈：`torch==2.8.0` / `torch-npu==2.8.0.post2`、MindSpeed（master）、MindSpeed-LLM（`6fe0df7`）+ Megatron-LM `core_v0.12.1`（其 `megatron` 目录拷入 MindSpeed-LLM，样例 `qwen3_dense` 放到 `examples/mcore` 下）、`transformers==5.1.0` / `datasets==2.16.0`。alpaca 数据集（`OmniData/alpaca`）与 Qwen3-1.7B 权重（`Qwen/Qwen3-1.7B`）均从魔搭社区（ModelScope）下载。逐条 docker / clone / download 命令见 Evidence 指向的 README 与构建脚本。

alpaca 风格数据每条含 `instruction`（必填）/ `input`（选填）/ `output`（必填）/ `system`（选填）/ `history`（选填多轮）字段；数据转换由 `AlpacaStyleInstructionHandler` 按 `--map-keys` 提取对应列。

## 拉起训练：四步脚本

样例把 SFT 全链路拆成四个现成脚本，均位于 `examples/mcore/qwen3_dense/` 下，依次执行：

```bash
# 1. 数据转换：原始 alpaca 转为 mcore 训练数据格式
bash examples/mcore/qwen3_dense/data_convert_qwen3_instruction.sh

# 2. 模型转换：HuggingFace 格式 → Mcore 训练格式
bash examples/mcore/qwen3_dense/ckpt_convert_qwen3_hf2mcore.sh

# 3. SFT 训练启动
bash examples/mcore/qwen3_dense/tune_qwen3_4K_full_A3_ptd.sh

# 4. 训练后模型转换回 HuggingFace 格式
bash examples/mcore/qwen3_dense/ckpt_convert_qwen3_mcore2hf.sh
```

> 固定脚本默认值分别为：data_convert 使用 `/usr/local/Ascend/cann/set_env.sh`，两份权重转换脚本使用 `/usr/local/Ascend/ascend-toolkit/set_env.sh`；训练脚本不包含 source 环境语句，需在父 shell 预先加载环境。请按实际安装位置调整；一站式平台示例为 `/home/developer/Ascend/cann-8.5.0/set_env.sh`，不能把某个转换脚本的默认路径推广到四步全部。

四步中的两次权重转换是 Megatron mcore 栈的固有要求：`hf2mcore` 把 HF 权重切成训练用的 mcore 张量/流水线并行布局（`--target-tensor-parallel-size` / `--target-pipeline-parallel-size`），训练完再 `mcore2hf` 合回 HF 格式以便部署/推理。两次转换统一由 `convert_ckpt_v2.py` 经 `--load-model-type` / `--save-model-type` 切方向（`hf→mg` 与 `mg→hf`），其中 `mcore2hf` 还需 `--hf-cfg-dir` 指向原 HF 配置目录来回填 `config`。

SFT 训练由 `posttrain_gpt.py` 拉起（区别于 pretrain 入口）。关键参数：路径配置 `CKPT_LOAD_DIR`（加载预训练权重）/ `CKPT_SAVE_DIR`（保存微调模型）/ `DATA_PATH` / `TOKENIZER_PATH`；并行配置 `TP` / `PP` / `CP` / `CP_TYPE` **需与模型转换参数保持一致**；微调标志 `--finetune` / `--stage sft` / `--is-instruction-dataset` / `--prompt-type qwen3`，并显式 `--no-load-optim` / `--no-load-rng`（从 base 权重起 finetune，不续载优化器与 RNG 态）。此外 `--sequence-parallel` 即便在样例 `TP=1` 下仍开启，序列长度走 `--no-pad-to-seq-lengths`。

> SFT 训练脚本里的并行配置（TP/PP/CP）必须和 `hf2mcore` 模型转换时的并行参数**保持一致**，否则权重布局不匹配。

## 容器映射与当前工作目录

宿主机先进入 `llm_sft/qwen3` 构建镜像和容器，样例目录挂载为容器内 `/workspace/qwen3`。`build_docker.sh` 默认映射 `/dev/davinci0`～`/dev/davinci15`，表示可见的设备节点数，训练实际仍由 `NPUS_PER_NODE=1` 控制；部分设备环境须按实际节点修改映射，多设备训练还要同步进程与并行配置。

复制依赖和脚本后进入 `MindSpeed-LLM`，后续数据集、权重转换和训练命令均以它为工作目录。一站式平台构建后额外安装 `pyarrow==21.0.0`，构建完成还需继续执行完整的数据准备和四步训练流程。Qwen3-1.7B 是稠密模型，不应从通用参数表推断需要开启 `--moe-grouped-gemm`；本样例未开启 CP。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_sft/qwen3/README.md)（supporting）

## Links

- [mindspeed](../../concepts/frameworks/mindspeed.md)（训练框架：MindSpeed Core/LLM、Megatron `core_v0.12.1` mcore 栈、HF↔mcore 权重转换血缘；dense SFT 入门用法）
- [qwen2.5-rl](qwen2_5_rl.md)（同域并列入门样例：单卡 RL/GRPO，veRL+FSDP+vLLM；单卡 SFT/MindSpeed 对照面）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：Qwen2/Qwen3 dense 模型的昇腾推理部署——微调产出的 HF 权重可流向该部署路径）
- [qwen3-sft-torchtitan](qwen3_sft_torchtitan.md)（对照：torchtitan-npu 版 Qwen3-30B-A3B SFT（vs 本 MindSpeed 1.7B dense））
- [peft-lora](../../concepts/techniques/peft_lora.md)（参数高效微调：LoRA/CC-LoRA/QLoRA/LU-LoRA，可替代全参 SFT 省显存）
