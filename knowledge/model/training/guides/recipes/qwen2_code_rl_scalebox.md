---
type: Guide
title: veRL + ScaleBox 沙盒长上下文 Code RL（DeepSeek-R1-Distill-1.5B / Qwen3-4B / Qwen3-30B-A3B）
description: 昇腾平台上 基于代码沙盒的 Code RL（代码强化学习） 端到端实践：用 veRL 强化学习框架 + 适配昇腾的代码沙盒服务 ScaleBox，跑 长上下文 Code RL 训练。「长上下文」体现在 prompt 2048 + response 8192 的 2k+8k 序列配置（recipe agent_rl/qwen2_code_rl）。Code RL 走的是 RLVR（可验证奖励）路线——模型对编程题生成代码、在 ScaleBox 沙盒里真跑测试用例、按通过率打可验证奖励回填 GRPO 优势计算（三脚本均 algorithm.adv_estimator=grpo，仅借用 DAPO 的 clip-higher，非纯 DAPO）——因此一个能扛 rollout 海量并发、可跨机扩展的安全执行沙盒是训练主回路的一环。
tags:
- task.implementation
- topic.reinforcement_learning
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a2
- a3
---

# veRL + ScaleBox 沙盒长上下文 Code RL（DeepSeek-R1-Distill-1.5B / Qwen3-4B / Qwen3-30B-A3B）

## Summary

昇腾平台上 **基于代码沙盒的 Code RL（代码强化学习）** 端到端实践：用 [veRL](../../concepts/frameworks/verl.md) 强化学习框架 + 适配昇腾的代码沙盒服务 [ScaleBox](../../concepts/frameworks/scalebox.md)，跑 **长上下文 Code RL** 训练。「长上下文」体现在 prompt 2048 + response 8192 的 2k+8k 序列配置（recipe `agent_rl/qwen2_code_rl`）。Code RL 走的是 RLVR（可验证奖励）路线——模型对编程题生成代码、在 ScaleBox 沙盒里真跑测试用例、按通过率打可验证奖励回填 [GRPO](../../concepts/techniques/grpo_dapo.md) 优势计算（三脚本均 `algorithm.adv_estimator=grpo`，仅借用 DAPO 的 clip-higher，非纯 DAPO）——因此一个能扛 rollout 海量并发、可跨机扩展的安全执行沙盒是训练主回路的一环。

该实践以 1.5B 深思考模型为起点，采用 veRL 强化学习框架与适配昇腾平台的代码沙盒服务 ScaleBox，实现高效且稳定的 **长上下文 Code RL** 训练。

该 recipe 在昇腾上验证了三个模型：**DeepSeek-R1-Distill-Qwen-1.5B**（Atlas A2 8 卡）、**Qwen3-4B-Instruct-2507**（Atlas A3 16 卡）、**Qwen3-30B-A3B-Instruct-2507**（Atlas A3 32 卡）。沙盒本身的特性与 veRL 融合部署机制见 [scalebox](../../concepts/frameworks/scalebox.md)。

## 训练配置

三个模型的训练参数与 LiveCodeBench(pass@1) 终值：

| Model | 机器 | GBS | n_samples | training_step | max_prompt_length | max_response_length | LiveCodeBench(pass@1) |
|---|---|---|---|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-1.5B | Atlas A2 8 卡 | 128 | 8 | 500 | 2048 | 8192 | 19.80 |
| Qwen3-4B-Instruct-2507 | Atlas A3 16 卡 | 128 | 8 | 450 | 2048 | 8192 | 44.18 |
| Qwen3-30B-A3B-Instruct-2507 | Atlas A3 32 卡 | 128 | 8 | 450 | 2048 | 8192 | 56.27 |

| 维度 | 配置 |
| --- | --- |
| 模型 | DeepSeek-R1-Distill-Qwen-1.5B（dense 深思考）/ Qwen3-4B-Instruct-2507（dense）/ Qwen3-30B-A3B-Instruct-2507（MoE） |
| 阶段 / 算法 | RL / GRPO（`algorithm.adv_estimator=grpo`）借用 DAPO clip-higher（`clip_ratio_high=0.28` 放宽上裁剪）并保留低方差 KL loss（`use_kl_loss=True` / `kl_loss_coef=0.001` / `kl_loss_type=low_var_kl`）——非典型 DAPO（DAPO 通常去 KL）；reward 来自 ScaleBox 沙盒可验证执行，取舍见 [grpo-dapo](../../concepts/techniques/grpo_dapo.md) |
| 框架 | veRL commit `c651b7b4207e408875f132c4226969ef3495d408`（基于 v0.7.0.dev）+ ScaleBox 沙盒 |
| 推理后端 | `vllm==0.11.0`、`vllm_ascend==v0.11.0rc1` |
| 数据集 | verifiable-coding-problems-python-only（基于 PrimeIntellect/verifiable-coding-problems 过滤高质量 Python 部分） |
| 序列长度 | max_prompt 2048 + max_response 8192（2k+8k 长上下文） |
| 平台 / 卡数 | 仅 DeepSeek-R1-Distill-1.5B 为 Atlas A2 单机 8 卡（`NNODES=1` / `n_gpus_per_node=8`）；Qwen3-4B 为 Atlas A3 单节点 16 卡（`NNODES=1` / `n_gpus_per_node=16`）；Qwen3-30B-A3B 为 Atlas A3 2 节点共 32 卡（`NNODES=2` / `n_gpus_per_node=16`，多机） |

该实践的三条核心工作：(1) 开发可扩展分布式代码执行沙盒 ScaleBox，支持大规模多机部署、主流 RL 框架兼容训练及多模型/基准的高效统一评估；(2) 提供融合 veRL 与 ScaleBox 的统一部署镜像，支持单节点同时运行 ScaleBox 服务与 veRL 训练任务，并零成本迁移至华为云 ModelArts；(3) 在昇腾环境验证了基于 veRL + ScaleBox 的 Code RL 训练效果。

## 环境准备：融合镜像

融合镜像分两层构建：先构建支持 Code RL 的 verl 镜像，再在其上叠 ScaleBox 得到融合镜像（实现 ScaleBox 与 verl 在单节点的融合部署）：

```bash
# 1) 构建支持 Code RL 的 verl 镜像
docker build --network=host -f verl.Dockerfile -t verl:main-c651b7b-py311-cann8.3.RC1 .

# 2) 在 verl 镜像基础上构建支持 ScaleBox 的镜像（先拉 ScaleBox 拿配置脚本和数据）
git clone https://gitcode.com/icip-cas/ScaleBox
# 仍在 recipe 目录，Dockerfile 来自此处，构建上下文必须指向 ScaleBox 仓库
docker build --network=host -f "$(pwd)/verl_sandbox.Dockerfile" -t verl_sandbox:main-c651b7b-py311-cann8.3.RC1 ./ScaleBox
```

veRL 框架需切到指定版本并应用 patch：

```bash
git clone https://github.com/volcengine/verl
cd verl
git checkout c651b7b4207e408875f132c4226969ef3495d408
cd ..
git apply patches/verl/0001-verl-feature-improve_rl_usability.patch
```

patch `0001-verl-feature-improve_rl_usability.patch` 的改动**直接围绕沙盒资源治理与超时**：在 `prime reward manager` 中增加对 `code_contests` 数据源的支持；并发进程数从 **64 降至 32** 以避免沙盒资源竞争；任务超时时间从 **300s 延长至 3000s** 以容纳大批量奖励任务的排队与执行等待；这不是单次代码执行时限；增强训练过程日志打印便于调试。可见 veRL↔ScaleBox 的工程难点不在算法，而在沙盒并发与执行超时的协调（机制详见 [scalebox](../../concepts/frameworks/scalebox.md)）。

## 部署 ScaleBox 服务

拉起 `verl_sandbox` 融合镜像后，先激活沙盒环境再起服务（单节点部署命令；更多分布式部署见 ScaleBox 仓库）：

```bash
source /home/ma-user/miniconda3/bin/activate sandbox-base

export HOST=0.0.0.0           # 服务器主机地址
export PORT=8080              # 服务端口
export WORKERS=32             # Uvicorn 服务并行 Worker 数量
export MAX_MEM=unlimited      # 单进程最大内存占用

cd ScaleBox
make run-online > deploy_${HOST}:${PORT}.log 2>&1 &
```

服务成功部署至 `http://0.0.0.0:8080`。用 `/run_code` 端点验证连通：

```bash
curl 'http://0.0.0.0:8080/run_code' \
  -H 'Content-Type: application/json' \
  --data-raw '{"code": "print(\"Hello, world!\")", "language": "python"}'
```

预期返回：

```json
{"status":"Success","message":"","compile_result":null,"run_result":{"status":"Finished","execution_time":0.02984905242919922,"return_code":0,"stdout":"Hello, world!\n","stderr":""}}
```

即 ScaleBox 以 JSON 传入 `code`+`language`、返回编译/运行状态与 stdout/stderr——这里只用于服务连通性验证，stdout/stderr 是执行元数据。训练 scalebox.py 调用 /common_evaluate_batch，按 accepted 或 tests[].passed 计算测试通过率，不能仅根据代码正常退出判奖励。

## 数据集与拉起训练

训练数据基于 [PrimeIntellect/verifiable-coding-problems](https://huggingface.co/datasets/PrimeIntellect/verifiable-coding-problems)，过滤其中较高质量的 Python 代码部分作为训练数据（verifiable-coding-problems-python-only），由 `build_dataset.py` 构建：

```bash
python build_dataset.py
```

recipe 提供三个示例训练脚本：`run_code_rl_qwen2_5_1_5b.sh`（DeepSeek-R1-Distill-Qwen-1.5B）、`run_code_rl_qwen3_4b.sh`、`run_code_rl_qwen3_30b_a3b.sh`。以 1.5B 样例脚本为例，涉及模型 DeepSeek-R1-Distill-Qwen-1.5B、数据 verifiable-coding-problems-python-only、最大输出长度 8k；配置好参数后拉起训练：

```bash
source /home/ma-user/miniconda3/bin/activate base  # 激活训练环境
bash run_code_rl_qwen2_5_1_5b.sh
```

ScaleBox 接入 veRL 训练流的核心适配点是 recipe 自带的 `scalebox.py`——verl 适配 ScaleBox 的自定义奖励函数文件：veRL rollout 出代码后，由该奖励函数调用 ScaleBox（如批量接口 `common_evaluate_batch`）执行测试用例、按通过情况算可验证奖励，回填 GRPO/DAPO 优势计算。

## 模型评测

评测复用 ScaleBox 作为执行后端，与训练同口径。基于 [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) 评测代码生成能力，推理参数遵循 DeepSeek-R1 实验设置：

- LiveCodeBench 数据：`release_version=v5`、`start_date=2024-08-01`、`code_execution=ScaleBox`；
- 推理参数：`n=4`、`temperature=0.6`、`top_p=0.95`、`max_tokens=32768`。

**DeepSeek-R1-Distill-Qwen-1.5B**（Atlas A2 8 卡，500 step）：LiveCodeBench(Pass@1) 从 0 步 **15.41** 升至 500 步 **19.80**（中间 350 步 18.91、400 步 18.37）。

**Qwen3-4B-Instruct-2507**（Atlas A3 16 卡，450 step）：从 0 步 **33.60** 升至 450 步 **44.18**（100 步 37.63、300 步 40.23）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/figures/reward_qwen3_4b.png" width="55%"></p>
<p align="center"><sub>图：Qwen3-4B-Instruct-2507 在 veRL + ScaleBox 上 Code RL 的训练奖励折线（reward 随 step 上升）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/README.md">qwen2_code_rl recipe·模型评测·Qwen3-4B</a>）</sub></p>

**Qwen3-30B-A3B-Instruct-2507**（MoE，Atlas A3 32 卡，450 step）是 recipe 的旗舰结果：LiveCodeBench(Pass@1) 从 0 步 **46.59** 逐步升至 450 步 **56.27**（关键节点 100 步 50.45、300 步 54.12、400 步 54.21）——450 步净增 **9.68 个百分点**。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/figures/reward_qwen3_30b_a3b.png" width="55%"></p>
<p align="center"><sub>图：Qwen3-30B-A3B-Instruct-2507 Code RL 的训练奖励折线——reward 随 step 稳步上升（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/README.md">qwen2_code_rl recipe·模型评测·Qwen3-30B-A3B</a>）</sub></p>

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/figures/training_progress_qwen3_30b_a3b.png" width="55%"></p>
<p align="center"><sub>图：Qwen3-30B-A3B-Instruct-2507 在 LiveCodeBench(Pass@1) 上的训练进度——0 步 46.59 → 450 步 56.27（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/README.md">qwen2_code_rl recipe·模型评测·Qwen3-30B-A3B</a>）</sub></p>

三个模型的 reward 与 LiveCodeBench(Pass@1) 总体改善，但评测存在波动（如1.5B 350→400步18.91→18.37、4B 41.67→40.50、30B 200→250步51.88→51.52），并非单调上升，验证了 veRL + ScaleBox 在昇腾上做长上下文 Code RL 的有效性。

## 与多轮工具调用 Agent RL 的关系

该实践是 **单轮 Code RL**——模型一次性生成完整代码、由 ScaleBox 执行打分。ScaleBox 还作为 **多轮工具调用 Code RL**（Agent RL）实践的执行后端：recipe `agent_rl/qwen3_code_toolcall` 让 Qwen3-1.7B 把 ScaleBox 当 Python 工具在推理过程中多轮调用（0001补丁与单轮保持一致；多轮 scalebox.py 在共享代码执行/通过率逻辑上新增 compute_reward，将通过率与工具调用奖励相加，训练脚本每次奖励0.005、最多奖励4次，不能称奖励函数原样沿用），是其「单轮基线」底座，详见 [qwen3-code-toolcall-rl](qwen3_code_toolcall_rl.md)。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen2_code_rl/README.md)（supporting）

## Links

- [scalebox](../../concepts/frameworks/scalebox.md)（承载的代码执行沙盒：三大核心特性、veRL×ScaleBox 融合镜像、`scalebox.py` 奖励桥接、`0001` patch 并发 64→32·超时 300s→3000s 机制集中在此页）
- [verl](../../concepts/frameworks/verl.md)（承载的 RL 框架：actor/rollout/ref 角色，rollout 用 vLLM-Ascend 生成代码，reward 经 `scalebox.py` 接 ScaleBox）
- [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（RL 算法：ScaleBox 返回的测试通过率作可验证奖励，回填 GRPO/DAPO 组内优势计算）
- [vllm-ascend](../../concepts/frameworks/vllm_ascend.md)（rollout 推理后端：`vllm==0.11.0` / `vllm_ascend==v0.11.0rc1`，在 NPU 上生成代码供 ScaleBox 执行）
- [qwen3-code-toolcall-rl](qwen3_code_toolcall_rl.md)（同沙盒底座的多轮工具调用 Agent RL：Qwen3-1.7B 把 ScaleBox 当工具多轮调用，此单轮 Code RL 为其基线）
- [qwen2.5-rl](qwen2_5_rl.md)（同框架 veRL 的数学 RL 入门样例，与此 Code RL 实践互为不同任务域参照）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：基座 DeepSeek-R1-Distill-1.5B / Qwen3-4B 均属 Qwen Dense（非 MoE）模型族，结构/家族对照；30B-A3B 变体则属 MoE）
