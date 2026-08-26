---
type: Guide
title: Qwen2.5-1.5B veRL GRPO 单卡 A2 数学 RL 入门样例
description: 昇腾 RL 训练的最小上手样例：用 verl（release/v0.6.1）框架，对 Qwen2.5-1.5B-Instruct 在 MATH-lighteval 数学推理数据集上跑 grpo-dapo（GRPO），最低只需单卡 Atlas A2（A3 同样可跑）即可完整走通「数据预处理 → RL 训练 → 权重合并 → 效果验证」全流程。它与 128 卡 A3 上的 671B 大规模实践 deepseek-r1-rl 同属一套框架（veRL + GRPO）：后者是工程极限，本样例面向用最少的卡、最少的步骤把昇腾 RL 跑通的入门场景。
tags:
- task.implementation
- topic.reinforcement_learning
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a2
---

# Qwen2.5-1.5B veRL GRPO 单卡 A2 数学 RL 入门样例

## Summary

昇腾 RL 训练的最小上手样例：用 [verl](../../concepts/frameworks/verl.md)（`release/v0.6.1`）框架，对 **Qwen2.5-1.5B-Instruct** 在 **MATH-lighteval** 数学推理数据集上跑 [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（GRPO），最低只需单卡 Atlas A2（A3 同样可跑）即可完整走通「数据预处理 → RL 训练 → 权重合并 → 效果验证」全流程。它与 128 卡 A3 上的 671B 大规模实践 [deepseek-r1-rl](deepseek_r1_rl.md) 同属一套框架（veRL + GRPO）：后者是工程极限，本样例面向用最少的卡、最少的步骤把昇腾 RL 跑通的入门场景。

与大规模实践的关键差异：训练后端用 veRL 原生 **FSDP**（而非 MindSpeed+Megatron），推理后端用 **vLLM + vLLM-Ascend**（`vllm==0.11.0` / `vllm-ascend==0.11.0`），单卡下 actor / rollout / ref 自然共卡、无需手写训推切换 reshard。Qwen2.5 本体作为推理模型见跨域页 [qwen-dense](../../../inference/concepts/models/qwen_dense.md)。

## 训练配置

| 维度 | 配置 |
| --- | --- |
| 模型 | Qwen2.5-1.5B-Instruct（dense） |
| 阶段 / 算法 | RL / GRPO（`algorithm.adv_estimator=grpo`） |
| 框架 | veRL `release/v0.6.1`；训练后端 FSDP，推理后端 vLLM `0.11.0` + vLLM-Ascend `0.11.0` |
| 数据集 | MATH-lighteval（数学推理，在线预处理为 `train.parquet` / `test.parquet`） |
| 平台 / 卡数 | 单卡 Atlas A2（最低）或 A3；亦提供 4 卡 A2 脚本 |
| 镜像 | A2 `quay.io/ascend/cann:8.5.0-910b-openeuler24.03-py3.11`；A3 `…8.5.0-a3-…` |

环境依赖（**先装推理后端再装 veRL**）：vLLM `0.11.0` + vLLM-Ascend `0.11.0`，veRL 取 `release/v0.6.1` 源码下载到 `verl_npu_demo/` 后 `pip install -e .`。

> 一站式平台（CANNLab）路径见 `README_single.md`：网页点击 CANNLab 创建开发环境，镜像选 `cann_8.5.2-A3` 或 `cann_8.5.2-A2`，免去本地 Docker，其余步骤一致。

## 数据 / 权重 / 奖励三件准备

1. **权重**：优先 ModelScope 命令行下载到 `verl/model/Qwen2_5_1_5B_Instruct/`，再把样例优化过的 `tokenizer_config.json` 覆盖进去（`mv -f tokenizer_config.json verl/model/Qwen2_5_1_5B_Instruct/`）。
2. **数据集**：用 veRL 自带预处理脚本在线拉取并转 parquet——

   ```shell
   cd verl/examples/data_preprocess
   # 若网络无法连通 huggingface，先执行：export HF_ENDPOINT=https://hf-mirror.com
   python3 math_dataset.py --local_dir ../../data/math/data
   ```

   产出 `train.parquet` 与 `test.parquet`。`release/v0.6.1` 的 `math_dataset.py` 原生支持 `--local_dataset_path` 从本地原始 parquet 离线加载，无需改源码。
3. **奖励函数**：把样例重写的 `new_math_reward.py` 放进 `verl/verl/utils/reward_score/`，由训练脚本 `custom_reward_function.path` 调用（见下「新奖励函数」节）。

## 拉起训练

把启动脚本移到 `verl_npu_demo/verl` 目录后执行：

```shell
cd verl
mkdir run_log
# 单卡：bash run_qwen2_5_1_5b_single.sh ；4 卡：bash run_qwen2_5_1_5b.sh
bash run_qwen2_5_1_5b_single.sh
```

训练 checkpoint 落在 `verl/checkpoints/verl_grpo_example_math/qwen2_5_1_5b_math/`。单卡脚本 `run_qwen2_5_1_5b_single.sh` 的 GRPO 核心配置（与 4 卡脚本仅在并行/资源项不同，见下表）：

```shell
export VLLM_ASCEND_ENABLE_NZ=0
export VLLM_USE_V1=1

python3 -m verl.trainer.main_ppo \
    algorithm.adv_estimator=grpo \
    data.train_files=./data/math/data/train.parquet \
    data.val_files=./data/math/data/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=512 \
    data.max_response_length=1024 \
    custom_reward_function.path=./verl/utils/reward_score/new_math_reward.py \
    actor_rollout_ref.model.path=./model/Qwen2_5_1_5B_Instruct \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.ppo_mini_batch_size=256 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.001 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.enforce_eager=True \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.8 \
    actor_rollout_ref.rollout.n=8 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    trainer.logger='["console","tensorboard"]' \
    trainer.n_gpus_per_node=1 \
    trainer.nnodes=1 \
    trainer.save_freq=70 \
    trainer.total_epochs=5 \
    trainer.device=npu 2>&1 | tee ./run_log/qwen2_5_1_5b_math_single.log
# llm_rl/qwen2_5/verl_npu_demo/run_qwen2_5_1_5b_single.sh
```

GRPO 语义体现在脚本里：`adv_estimator=grpo`（组内相对优势，无 critic）、`rollout.n=8`（每 prompt 采 8 条组成一组）、`use_kl_loss=True` + `kl_loss_coef=0.001` + `kl_loss_type=low_var_kl`（KL 正则约束，原理见 [grpo-dapo](../../concepts/techniques/grpo_dapo.md)）。单卡与 4 卡脚本的差异仅在于：

| 项 | 单卡 `run_qwen2_5_1_5b_single.sh` | 4 卡 `run_qwen2_5_1_5b.sh` |
| --- | --- | --- |
| `ASCEND_RT_VISIBLE_DEVICES` | `0` | `0,1,2,3` |
| `rollout.tensor_model_parallel_size` | `1`（无需 TP） | `2` |
| `rollout.enforce_eager` | `True`（关图模式） | 不设（默认） |
| `trainer.n_gpus_per_node` | `1` | `4` |
| `trainer.save_freq` | `70` | `28` |
| `experiment_name` | `qwen2_5_1_5b_math_single` | `qwen2_5_1_5b_math` |

`data.train_batch_size=256` / `ppo_mini_batch_size=256` / `total_epochs=5` 等其余超参两脚本一致。

## 新奖励函数：语义等价 + 分级信号

veRL 原生 MATH 奖励仅做「字符串等价性」二元打分，会把 `0.25` 与 `1/4` 判为不等、且 0/1 信号过稀疏。样例重写的 `new_math_reward.py` 修正两点：一是引入基于数学语义等价性的判断机制提升准确性；二是在准确度基础上新增格式规范性、思维链完整性两类分级奖励，用多维度信号缓解奖励稀疏。设计原则为「答案正确性优先」——若答案本身不正确，则不纳入格式规范性与思维链质量的评分。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/figures/qwen2_5/reward_score.png" width="55%"></p>
<p align="center"><sub>图：样例 MATH 新奖励函数设计——答案正确性优先，正确后再叠加格式规范性 / 思维链完整性分级奖励（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/README.md">Qwen2.5 veRL RL 样例 README</a>·附录·新奖励函数介绍）</sub></p>

它通过训练脚本的 `custom_reward_function.path=./verl/utils/reward_score/new_math_reward.py` 注入，故 GRPO 的 reward 阶段调用的是这套自定义打分而非 veRL 原生 MATH 奖励。

## 效果验证与可视化

多卡训练完需用 `verl.model_merger`（`--backend fsdp`）合并 FSDP 分片 checkpoint 为 HuggingFace 权重；单卡可直接用。验证用 OpenCompass（`0.5.2`）对**基模**与**RL 模型**同集对比，`max_out_len=1024` / `batch_size=32` 适配 64GB NPU。效果对比：

| model | step | dataset | metric | accuracy |
| --- | --- | --- | --- | --- |
| qwen2.5-1.5b-instruct（基模） | 0 | MATH-lighteval | accuracy | **43.48** |
| qwen2.5-1.5b-instruct-rl-140 | 140 | MATH-lighteval | accuracy | **53.26** |

即经 GRPO 后 MATH 准确率相对提升 **22.5%**。训练过程可用 SwanLab / TensorBoard 追踪（脚本 `trainer.logger` 配 `console,tensorboard`，切 SwanLab 改为 `console,swanlab`）；`actor/entropy`、`actor/kl_loss`、`actor/pg_loss`、`response_length/mean` 等是调参时关注的健康度指标，可据其健康区间识别「奖励黑客 / 模式崩溃」等异常信号。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen2_5/verl_npu_demo/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/README.md)（Qwen2.5-1.5B veRL GRPO 样例：环境/权重/数据/奖励准备、A2·A3 镜像、`verl release/v0.6.1` 安装、`math_dataset.py` 预处理、`model_merger` 合并、OpenCompass 43.48→53.26 验证、SwanLab/TensorBoard 指标解读、新奖励函数）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen2_5/verl_npu_demo/README_single.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/README_single.md)（一站式 CANNLab 平台单卡快速启动版：镜像 `cann_8.5.2-A2/A3`、`run_qwen2_5_1_5b_single.sh`）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen2_5/verl_npu_demo/run_qwen2_5_1_5b_single.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/run_qwen2_5_1_5b_single.sh) / `run_qwen2_5_1_5b.sh`（GRPO 单卡 / 4 卡启动脚本）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen2_5/verl_npu_demo/new_math_reward.py`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen2_5/verl_npu_demo/new_math_reward.py)（样例自定义 MATH 奖励函数，由 `custom_reward_function.path` 注入）
- [verl](https://github.com/volcengine/verl) — 上游 veRL 代码仓（`release/v0.6.1`，本样例训练/推理调度框架）

## Links

- [verl](../../concepts/frameworks/verl.md)（本样例所用 RL 框架：单/多控制器、actor/rollout/ref 角色、FSDP×vLLM 可插拔后端）
- [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（本样例 RL 算法：GRPO 组内相对优势、KL 正则、on-policy，脚本 `adv_estimator=grpo` 即其入口）
- [deepseek-r1-rl](deepseek_r1_rl.md)（同框架的大规模对照：128 卡 A3、671B、MindSpeed+vLLM-Ascend 全共卡 GRPO，对应工程极限端）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：Qwen2.5 dense 模型的昇腾推理部署）
- [qwen2-code-rl-scalebox](qwen2_code_rl_scalebox.md)（同域并列:Code RL(ScaleBox)）
- [deltanet-pretrain](deltanet_pretrain.md)（同域并列：DeltaNet 预训练）
- [qwen3-sft](qwen3_sft.md)（同域并列：Qwen3-1.7B SFT 入门）
