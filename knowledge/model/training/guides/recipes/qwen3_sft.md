---
type: Guide
title: Qwen3-1.7B MindSpeed-LLM SFT 单卡 A3 alpaca 入门样例
description: Qwen3-1.7B（dense）使用 MindSpeed-LLM + Megatron-LM core_v0.12.1 的 mcore 训练栈，在单卡 A3 上对 alpaca 指令数据集执行 SFT（监督微调）。流程包含 HF 模型转 mcore、alpaca 数据转换、SFT 训练及 mcore 转回 HF，需要 HF↔mcore 权重格式互转。与 Qwen2.5 的 veRL 原生 FSDP+vLLM 单卡 RL 路线不同，SFT 不包含 rollout 或奖励函数环节。
tags:
- task.implementation
- topic.model_adaptation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a2
- a3
---

# Qwen3-1.7B MindSpeed-LLM SFT 单卡 A3 alpaca 入门样例

## Summary

昇腾 SFT（监督微调）最小上手样例：用 [mindspeed](../../concepts/frameworks/mindspeed.md) 系的 **MindSpeed-LLM**（叠加 Megatron-LM `core_v0.12.1` 的 mcore 训练栈），对 **Qwen3-1.7B**（dense）在 **alpaca** 指令数据集上跑监督微调，**单卡即可**——硬件要求为「卡数：1张A3」。把昇腾上「HF 模型转 mcore → alpaca 数据转换 → SFT 训练 → mcore 转回 HF」的全链路压到一台机器、一张卡上跑通，是 dense 模型微调的入门梯子；同框架的大规模实践（DeepSeek-V3 HiF8/MXFP8 低精度预训练）见 [mindspeed](../../concepts/frameworks/mindspeed.md)。Qwen3 dense 本体作为推理模型见跨域页 [qwen-dense](../../../inference/concepts/models/qwen_dense.md)。

与 [qwen2.5-rl](qwen2_5_rl.md)（veRL 原生 FSDP+vLLM 的单卡 RL 入门）的关键差异：训练栈走 **MindSpeed-LLM + Megatron mcore**（Megatron 风格、需要 HF↔mcore 权重格式互转），阶段是 **SFT 而非 RL**，无 rollout / 奖励函数环节。

## 训练配置

| 维度 | 配置 |
| --- | --- |
| 模型 | Qwen3-1.7B（dense，HF 权重 `Qwen/Qwen3-1.7B`） |
| 阶段 | SFT（监督微调，`--stage sft`） |
| 框架 | MindSpeed-LLM（commit `6fe0df7`）+ Megatron-LM `core_v0.12.1`（mcore） |
| 数据集 | alpaca（指令微调，`OmniData/alpaca`，AlpacaStyleInstructionHandler） |
| 平台 / 卡数 | 单卡 A3（「卡数：1张A3」）；一站式平台镜像可选 A3 或 A2 |
| 序列长度 | 4K（训练脚本 `tune_qwen3_4K_full_A3_ptd.sh`；数据预处理 `--seq-length` 默认 4096） |

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

> 需按实际情况在以上脚本中修改 `ascend-toolkit` 路径。默认配置为 `source /usr/local/Ascend/ascend-toolkit/set_env.sh`；一站式平台（以 CANN 8.5.0 为例）需改为 `source /home/developer/Ascend/cann-8.5.0/set_env.sh`。

四步中的两次权重转换是 Megatron mcore 栈的固有要求：`hf2mcore` 把 HF 权重切成训练用的 mcore 张量/流水线并行布局（`--target-tensor-parallel-size` / `--target-pipeline-parallel-size`），训练完再 `mcore2hf` 合回 HF 格式以便部署/推理。两次转换统一由 `convert_ckpt_v2.py` 经 `--load-model-type` / `--save-model-type` 切方向（`hf→mg` 与 `mg→hf`），其中 `mcore2hf` 还需 `--hf-cfg-dir` 指向原 HF 配置目录来回填 `config`。

SFT 训练由 `posttrain_gpt.py` 拉起（区别于 pretrain 入口）。关键参数：路径配置 `CKPT_LOAD_DIR`（加载预训练权重）/ `CKPT_SAVE_DIR`（保存微调模型）/ `DATA_PATH` / `TOKENIZER_PATH`；并行配置 `TP` / `PP` / `CP` / `CP_TYPE` **需与模型转换参数保持一致**；微调标志 `--finetune` / `--stage sft` / `--is-instruction-dataset` / `--prompt-type qwen3`，并显式 `--no-load-optim` / `--no-load-rng`（从 base 权重起 finetune，不续载优化器与 RNG 态）。此外 `--sequence-parallel` 即便在样例 `TP=1` 下仍开启，序列长度走 `--no-pad-to-seq-lengths`。

> SFT 训练脚本里的并行配置（TP/PP/CP）必须和 `hf2mcore` 模型转换时的并行参数**保持一致**，否则权重布局不匹配。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_sft/qwen3/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/README.md)（Qwen3-1.7B SFT 样例：硬件要求「1张A3」、Dockerfile 与一站式平台两条环境构建路径、alpaca/ModelScope 数据与权重准备、`data_convert`/`hf2mcore`/`tune`/`mcore2hf` 四步脚本、附录数据/转换/SFT 参数说明）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_sft/qwen3/Dockerfile.cann.mindspeed.qwen3`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/Dockerfile.cann.mindspeed.qwen3)（基础镜像 `cann:8.5.0-a3-openeuler24.03-py3.11`、torch 2.8.0/torch-npu 2.8.0.post2、MindSpeed master、MindSpeed-LLM `6fe0df7...` + Megatron-LM `core_v0.12.1`、transformers 5.1.0/datasets 2.16.0）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_sft/qwen3/build_docker.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/build_docker.sh) / [`build_project_platform.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/build_project_platform.sh)（容器拉起与一站式平台依赖构建脚本，`cp -r qwen3_dense MindSpeed-LLM/examples/mcore`）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_sft/qwen3/qwen3_dense/`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_sft/qwen3/qwen3_dense)（四步脚本 `data_convert_qwen3_instruction.sh` / `ckpt_convert_qwen3_hf2mcore.sh` / `tune_qwen3_4K_full_A3_ptd.sh` / `ckpt_convert_qwen3_mcore2hf.sh`）

## Links

- [mindspeed](../../concepts/frameworks/mindspeed.md)（训练框架：MindSpeed Core/LLM、Megatron `core_v0.12.1` mcore 栈、HF↔mcore 权重转换血缘；dense SFT 入门用法）
- [qwen2.5-rl](qwen2_5_rl.md)（同域并列入门样例：单卡 RL/GRPO，veRL+FSDP+vLLM；单卡 SFT/MindSpeed 对照面）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：Qwen2/Qwen3 dense 模型的昇腾推理部署——微调产出的 HF 权重可流向该部署路径）
- [qwen3-sft-torchtitan](qwen3_sft_torchtitan.md)（对照：torchtitan-npu 版 Qwen3-30B-A3B SFT（vs 本 MindSpeed 1.7B dense））
- [peft-lora](../../concepts/techniques/peft_lora.md)（参数高效微调：LoRA/CC-LoRA/QLoRA/LU-LoRA，可替代全参 SFT 省显存）

<!-- cannbot:related:start -->
## 相关

- [MindSpeed（昇腾大模型训练加速框架 + 低精度训练）](../../concepts/frameworks/mindspeed.md)（`related`）：Qwen3-1.7B SFT 使用 **MindSpeed-LLM + Megatron mcore**，需要 HF↔mcore 权重格式互转；MindSpeed-LLM 是面向 LLM 的上层套件，承载四步 SFT 流程所需的模型、数据处理与训练入口。
- [PEFT / LoRA 家族（LoRA / CC-LoRA / QLoRA / LU-LoRA / LoRA-MoE）](../../concepts/techniques/peft_lora.md)（`related`）：Qwen3 全参 SFT 的数据转换、权重转换、训练与导出流程可作为基线；LoRA 家族通过低秩适配替代全参更新以节省显存，需按训练框架选择对应参数。
- [Qwen3-30B-A3B torchtitan-npu SFT（GSM8K + Ulysses CP 开箱配置）](qwen3_sft_torchtitan.md)（`related`）：Qwen3-1.7B dense 使用 MindSpeed-LLM + Megatron-LM `core_v0.12.1`，在单卡 A3 上以 alpaca 执行 SFT；Qwen3-30B-A3B 使用 torchtitan-npu 的 MoE 多卡路线。两者是模型规模、数据集与训练框架不同的 SFT 选型。
<!-- cannbot:related:end -->
