---
type: Guide
title: Qwen3 Tool Agent RL（verl-retool：SFT→RL 两阶段 Sandbox 工具 Agent，昇腾 A3）
description: 基于 veRL recipe/retool 项目，在昇腾 NPU 上完成端到端 agent RL 训练：让 Qwen3-4B-Instruct-2507 学会在推理过程中调用 Sandbox 代码工具进行 python 编程，把代码执行结果回灌为新一轮输入，辅助自身推理思考。整条流程使能 veRL 的 asyncLLM（异步生成）+ agent_loop（多轮工具调用）特性，这两个执行特性的机制见 Agent RL 执行范式。
tags:
- task.implementation
- topic.reinforcement_learning
- topic.model_serving
- topic.model_adaptation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/patches/0004-Fix-local-parquet-loading-for-retool-datasets.patch
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-train/merge_requests/210
  role: evidence
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a3
---

# Qwen3 Tool Agent RL（verl-retool：SFT→RL 两阶段 Sandbox 工具 Agent，昇腾 A3）

## Summary

基于 [veRL](../../concepts/frameworks/verl.md) `recipe/retool` 项目，在昇腾 NPU 上完成**端到端 agent RL 训练**：让 **Qwen3-4B-Instruct-2507** 学会在推理过程中**调用 Sandbox 代码工具进行 python 编程**，把代码执行结果回灌为新一轮输入，辅助自身推理思考。整条流程使能 veRL 的 **`asyncLLM`**（异步生成）+ **`agent_loop`**（多轮工具调用）特性，这两个执行特性的机制见 [Agent RL 执行范式](../../concepts/techniques/agent_rl_loop.md)。

训练分两步：

- **SFT 训练**：使用 `ReTool-SFT` 数据集对 Qwen3-4B-Instruct-2507 做 SFT，让模型先学会调用 Sandbox 工具进行 python 编程；
- **RL 训练**：使用 `DAPO-Math-17k` 数据集对前一步 SFT 过的模型做 RL，帮助模型更好地使用 Sandbox 工具辅助自身推理思考，RL 算法见 [DAPO](../../concepts/techniques/grpo_dapo.md)。

## 训练配置

| 维度 | 取值 |
|---|---|
| 基座模型 | Qwen3-4B-Instruct-2507（HF `Qwen/Qwen3-4B-Instruct-2507`，**dense** 模型；跨域结构对照 [qwen-dense](../../../inference/concepts/models/qwen_dense.md)） |
| 阶段 | SFT（ReTool-SFT）→ RL（DAPO-Math-17k）两阶段 |
| RL 算法 | DAPO（`run_qwen3_4b_dapo_npu.sh`） |
| 执行范式 | `asyncLLM` + `agent_loop`（multi-turn 工具调用） |
| 工具后端 | SandboxFusion（python 代码执行沙盒，常驻 `http://0.0.0.0:8080`） |
| 平台 / 卡数 | Atlas A3 系列；本样例所需计算资源 **8 卡 A3（16die）** |
| 训练后端 | FSDP（SFT 后 `verl.model_merger merge --backend fsdp`） |
| 验证数据集 | `yentinglin/aime_2025`（RL `val`），训练数据 `BytedTsinghua-SIA/DAPO-Math-17k` |

当前样例附带四个 patch（`git am` 入 verl）：`0001-Fix-reward-function-not-accessing-num_turns.patch`（修复奖励函数获取不到 `num_turns` 值的 bug）、`0002-Update-paths-in-retool_sft_preprocess.py.patch`（修改数据预处理路径配置）、`0003-Modify-compute_score-to-encourage-tool-call.patch`（修改奖励函数，鼓励工具调用）、`0004-Fix-local-parquet-loading-for-retool-datasets.patch`（显式 parquet 加载并隔离默认数据配置）。

## 环境与 verl 准备

环境：`quay.io/ascend/vllm-ascend:v0.10.2rc1-a3` 镜像（A3）。

承重事实：retool **已从 verl 迁出至 verl-recipe 仓库，最新分支无该项目**，故装 verl 时必须 checkout 含 retool 的历史版本 `95470480` 再 `git am ../patches/*.patch` 打入四个 patch，之后 `pip install -e .` 并进 `recipe/retool`：

```shell
git checkout 95470480   # 含 retool 的历史版本（最新分支已无该项目）
git am ../patches/*.patch
```

（docker run 设备挂载、`git clone`/`pip install -r requirements.txt` 等纯搭建命令见 Evidence README。）

## SFT 阶段（ReTool-SFT 冷启动）

冷启动 SFT 让模型先学会工具调用的格式与时机（范式见 [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)）。四步：

```shell
# 1. 数据集处理
python3 retool_sft_preprocess.py

# 2. 模型权重
hf download Qwen/Qwen3-4B-Instruct-2507 --local-dir ReTool-SFT/model/Qwen3-4B-Instruct-2507

# 3. 将 run_qwen3_4b_sft_npu.sh 从 qwen3_tool_agent 移动到 verl/recipe/retool 后启动
mkdir -p log/sft_run_log
bash run_qwen3_4b_sft_npu.sh

# 4. 合并训练好的模型权重（FSDP 后端）
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir checkpoint/multiturn-sft-qwen-3-4b-instruct/global_step_186 \
    --target_dir checkpoint/multiturn-sft-qwen-3-4b-instruct/global_step_186/huggingface
```

SFT 取 `global_step_186` 检查点合并为 HuggingFace 格式权重，作为 RL 阶段的初始权重。

## RL 阶段（DAPO-Math-17k + Sandbox 工具）

**1. 准备 Sandbox 环境。** 当前固定 recipe 选择 SandboxFusion 的 `feat/runtime` 分支，按对应 Manual 流程创建 `sandbox`（Python 3.12），安装 poetry 依赖并准备 `docs/build`，随后运行服务。该流程不要求额外创建 `sandbox-runtime` conda 环境；`make run-online` 也依赖该分支，不能在任意上游 main 上照抄。

```shell
git clone --branch feat/runtime https://github.com/bytedance/SandboxFusion.git
cd SandboxFusion
conda activate sandbox
make run-online
# 成功后显示：Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

> Sandbox 服务启动后**不要关闭**——agent 在训练时需要与其实时交互；另开一个终端进容器和 `verl/recipe/retool` 目录后再执行后续命令。`ToolAgentLoop` 经 `verl/recipe/retool` 的 sandbox 工具封装与该 SandboxFusion 服务（`github.com/bytedance/SandboxFusion`）交互。

**2. 准备训练 / 验证数据集。**

```shell
# train
hf download BytedTsinghua-SIA/DAPO-Math-17k --repo-type=dataset --local-dir dataset/BytedTsinghua-SIA/DAPO-Math-17k
# val
hf download yentinglin/aime_2025 --repo-type=dataset --local-dir dataset/yentinglin/aime_2025
```

**3. 启动 RL 训练**（同样把 `run_qwen3_4b_dapo_npu.sh` 移到 `verl/recipe/retool` 后执行）：

```shell
mkdir -p log/rl_run_log
bash run_qwen3_4b_dapo_npu.sh
```

启动脚本内含 TensorBoard 配置：`trainer.logger=['console','tensorboard']`（默认开 TensorBoard）、`trainer.log_val_generations=10`（每次验证查看的 response 数，默认 10）；TensorBoard 日志输出至 `qwen3_tool_agent/verl/recipe/retool/tensorboard_log/retool`，训练曲线在 `TIME SERIES` 页签、验证 response 文本在 `TEXT` 页签。

## 当前准备步骤与失败检查

运行 SFT/RL 前先把两个启动脚本按固定 README 的命令放到历史 verl 的 `recipe/retool` 目录，核对当前工作目录再启动。预处理脚本来自外部 verl checkout，不是 Recipes 根中的独立文件。国内网络可按来源使用 HF_ENDPOINT 或 modelscope，不能据此省略权重/数据完整性检查。

PR210 同时新增本地 parquet 的 0004 patch，避免自动加载器推断错误及 AIME 其他配置 schema 混入，诊断和验收见 [ReTool parquet 加载失败](../../runbooks/runtime/retool_local_parquet_loading.md)。来源作者报告 A3 8 卡 SFT/RL 验证，本批未复测。下列 0.29→0.57 等曲线保留原观测口径，不作为本次新实验。

## 训练结果

RL 在 `aime_2025` 上的验证指标：

| 指标 | `val_before_train`（step 0） | 130 个 step 后 |
|---|---|---|
| `val-core/aime_2025/acc/mean@30`（准确率） | 0.29 | **0.57** |
| `val-aux/num_turns/mean`（平均交互轮数） | 7.0 | **5.4** |

`num_turns` 指每一次 user 或 assistant 输入都算一次 num_turn 的均值——训练后准确率近乎翻倍，同时模型学会用**更少轮数**解题。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.assets/image-20251127110205011.png" width="80%">
<sub>图：关键验证曲线——`val-core/aime_2025/acc/mean@30`（验证集准确率）与 `val-aux/num_turns/mean`（验证 num_turns）随训练推进的变化（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.md">verl-retool agent 样例 README</a>·关键训练曲线）</sub>

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.assets/image-20251127110452948.png" width="80%">
<sub>图：训练曲线——`critic/rewards/mean`（训练时单 step 平均奖励）与 `response_length/mean`（单 step 平均响应长度）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.md">verl-retool agent 样例 README</a>·关键训练曲线）</sub>

训练后的模型 response 遵循多轮工具调用流程：

> 问题输入 → 模型思考 → 调用代码工具 → 返回结果作为新一轮的输入 → 模型思考 → 生成答案

即模型先用大段文本推理分析问题，再调用代码工具处理复杂的动态规划计算，代码工具算出结果作为新输入回传给模型，模型校验后输出最终答案。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.assets/response样例.png" width="72%">
<sub>图：训练后模型 response 样例——文本推理（图中省略）后调用代码工具做动态规划计算、校验结果再输出答案（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.md">verl-retool agent 样例 README</a>·训练后模型 response 样例）</sub>

## 执行机制

RL 阶段的多轮工具调用执行流水完全由 `asyncLLM` + `agent_loop` 承载，机制见 [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)，在本 recipe 的落点：

- **`agent_loop`**：`ToolAgentLoop`（agent RL 核心类）以 `_handle_generating_state()`（调模型生成 + 检查是否调工具）和 `_handle_processing_tools_state()`（执行工具调用 + 格式化结果作下一轮输入）两状态交替驱动 multi-turn 轨迹。
- **`asyncLLM`**：vLLM 引擎以 HTTP Server 形态暴露，`AsyncLLMServerManager` 做**负载均衡**（首轮选请求最少的 Server）+ **粘性会话**（多轮会话补全请求发往同一 Server 复用 KV cache）；据此实现 vLLM 推理与 Python CI 工具调用的**异步并行**。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/README.md)（primary）
- [0004-Fix-local-parquet-loading-for-retool-datasets.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/patches/0004-Fix-local-parquet-loading-for-retool-datasets.patch)（implementation）
- [远程来源](https://gitcode.com/cann/cann-recipes-train/merge_requests/210)（evidence）

## Links

- [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)（承载执行范式：`asyncLLM`+`agent_loop` 的 `ToolAgentLoop` 状态机、`AsyncLLMServerManager` 负载均衡/粘性会话、推理与工具执行异步并行——本 recipe 的多轮工具调用机制全在此）
- [verl](../../concepts/frameworks/verl.md)（承载框架：经 `git checkout 95470480`+`git am patches/*.patch` 使能 retool；SFT 后 `verl.model_merger merge --backend fsdp`，RL 由 `run_qwen3_4b_dapo_npu.sh` 拉起）
- [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（RL 算法：本 recipe RL 阶段用 DAPO + DAPO-Math-17k，奖励函数经 patch 鼓励工具调用）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：基座 Qwen3-4B-Instruct-2507 属 Qwen Dense（非 MoE）模型族，结构/家族对照）
