---
type: Concept
title: ScaleBox（可扩展分布式代码执行沙盒 + veRL 融合部署）
description: ScaleBox（icip-cas/ScaleBox）是一个开源的可扩展分布式代码执行沙盒，在 cann-recipes-train 中作为昇腾平台上 Code RL（代码强化学习）的代码执行环境。Code RL 的奖励信号来自「让模型生成代码 → 在沙盒里真跑测试用例 → 用通过率打分」，因此一个能扛住 RL rollout 海量并发请求、又能跨机扩展的安全执行沙盒，是 Code RL / Agent RL 训练链路里和训练框架同等重要的一环。ScaleBox 的核心特性可概括为三点：可扩展的分布式代码沙盒体系（多机分布式部署 + 请求负载均衡、单元测试并行 + 实例级并行）、面向 Code RL 的统一训练接口和评估套件（批量评估接口 common_evaluate_batch、内置 LiveCodeBench/HumanEval/MBPP 一键评估）、灵活的 Special Judge 判题机制（自定义判题逻辑，适配多正确答案的复杂编程题）。
tags:
- task.implementation
- topic.architecture
- topic.reinforcement_learning
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen2_code_rl/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a2
- a3
---

# ScaleBox（可扩展分布式代码执行沙盒 + veRL 融合部署）

## Summary

**ScaleBox**（[icip-cas/ScaleBox](https://gitcode.com/icip-cas/ScaleBox)）是一个开源的**可扩展分布式代码执行沙盒**，在 cann-recipes-train 中作为**昇腾平台上 Code RL（代码强化学习）的代码执行环境**。Code RL 的奖励信号来自「让模型生成代码 → 在沙盒里真跑测试用例 → 用通过率打分」，因此一个能扛住 RL rollout 海量并发请求、又能跨机扩展的安全执行沙盒，是 Code RL / Agent RL 训练链路里和训练框架同等重要的一环。ScaleBox 的核心特性可概括为三点：**可扩展的分布式代码沙盒体系**（多机分布式部署 + 请求负载均衡、单元测试并行 + 实例级并行）、**面向 Code RL 的统一训练接口和评估套件**（批量评估接口 `common_evaluate_batch`、内置 LiveCodeBench/HumanEval/MBPP 一键评估）、**灵活的 Special Judge 判题机制**（自定义判题逻辑，适配多正确答案的复杂编程题）。

在昇腾 NPU 上，ScaleBox 与训练框架 [veRL](verl.md) 融合部署（单节点同跑 ScaleBox 服务 + veRL 训练、可零成本迁 ModelArts），并在 veRL 侧通过自定义奖励函数 `scalebox.py` 接入 RL 训练流。具体的 Code RL 端到端实践（数据集、训练脚本、benchmark）见 [qwen2-code-rl-scalebox](../../guides/recipes/qwen2_code_rl_scalebox.md) 与 [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)。

## 为什么 Code RL 需要一个代码执行沙盒

Code RL 走的是 RLVR（可验证奖励）路线：模型对一道编程题生成代码后，奖励不靠人标、也不靠 reward model 打分，而是把代码**真正执行**在测试用例上、按通过率给可验证奖励。这把「执行环境」从评测附属设施提升为训练主回路的一环——RL rollout 每步要对一大批 prompt 各采样 `n_samples` 个回复（recipe 中 `n_samples=8`），每个回复又要跑多条测试用例，沙盒承受的是 rollout 级别的高并发代码执行压力。ScaleBox 正是为这一负载设计的：可扩展、可并行、可负载均衡的分布式沙盒，配合面向 Code RL 优化的批量接口与统一评估套件。

cann-recipes-train 在此基础上提供三件套：(1) 可扩展分布式代码执行沙盒 ScaleBox，支持大规模多机部署、主流 RL 框架兼容训练及多模型/基准的高效统一评估；(2) 融合 veRL 与 ScaleBox 的统一部署镜像，支持单节点同时运行 ScaleBox 服务与 veRL 训练任务，并零成本迁移至华为云 ModelArts；(3) 在昇腾环境验证基于 veRL + ScaleBox 的 Code RL 训练效果。

## ScaleBox 三大核心特性

ScaleBox 的核心特性分三类：

**可扩展的分布式代码沙盒体系。**
- 支持多机分布式沙盒部署与**请求负载均衡**——rollout 高并发请求可摊到多机多 worker，不让单点成为瓶颈。
- 支持**单元测试并行**与**实例级并行**——一道题的多条测试用例可并行执行，多个代码实例也可并行评估。

**面向 Code RL 的统一训练接口和评估套件。**
- 提供高效**批量评估接口 `common_evaluate_batch`**：相较逐条 `run_code`，通过**单次请求处理多个测试用例**，显著提升训练效率（RL rollout 每步成百上千次代码执行，批量化是吞吐关键）。
- 内置对 **LiveCodeBench、HumanEval、MBPP** 等主流代码评测基准的支持，实现一键式快速评估——训练用的执行环境与评测用的执行环境统一，避免训测口径漂移。

**灵活的 Special Judge 判题机制。**
- 支持自定义判题逻辑，能灵活适应**具有多种正确答案**的复杂编程题目（如答案不唯一、需特判输出的题），而非只做字符串/精确比对。

## veRL × ScaleBox 融合部署

ScaleBox 不是独立训练框架，而是与训练框架 [veRL](verl.md) 配合：veRL 负责 actor/rollout/ref RL 主回路（rollout 用 [vLLM-Ascend](vllm_ascend.md) 在 NPU 上生成代码），ScaleBox 作为外部 HTTP 服务承接「执行生成代码、返回测试通过情况」的奖励计算。recipe 的关键工程点是**单节点融合部署**——同一台机器、同一镜像里既跑 ScaleBox 服务又跑 veRL 训练，且可零成本迁 ModelArts。

**融合镜像分两层构建**：先用 `verl.Dockerfile` 构建支持 Code RL 的 verl 基础镜像，再在其上用 `verl_sandbox.Dockerfile` 叠 ScaleBox，得到单镜像内同跑 veRL 训练 + ScaleBox 服务的 `verl_sandbox` 融合镜像（具体镜像 tag、`docker run` 设备挂载等部署流水见 recipe README）。

软件版本：veRL commit `c651b7b4207e408875f132c4226969ef3495d408`（基于 v0.7.0.dev）、`vllm==0.11.0`、`vllm_ascend==v0.11.0rc1`；硬件为 Atlas A2/A3 系列、单机八卡。

**部署 ScaleBox 服务**：拉起 `verl_sandbox` 融合镜像后，先激活沙盒环境再起服务（单节点部署；更多分布式部署见 ScaleBox 仓库）：

```bash
source /home/ma-user/miniconda3/bin/activate sandbox-base

export HOST=0.0.0.0           # 服务器主机地址
export PORT=8080              # 服务端口
export WORKERS=32             # Uvicorn 服务并行 Worker 数量
export MAX_MEM=unlimited      # 单进程最大内存占用

cd ScaleBox
make run-online > deploy_${HOST}:${PORT}.log 2>&1 &
```

服务起在 `http://0.0.0.0:8080`，对外暴露 HTTP 接口（`WORKERS=32` 说明服务侧由 Uvicorn 多 worker 承接并发）。`make run-online` 是 ScaleBox 仓库提供的在线服务入口。

承重的接口语义：单条执行端点 `/run_code` 以 JSON 传入 `code`+`language`，返回 `compile_result` 与 `run_result`（含 `status`/`return_code`/`stdout`/`stderr`）；批量端点 `common_evaluate_batch` 单次请求处理多条测试用例。这两类返回的编译/运行状态正是 RL 奖励函数读取「测试是否通过」、算可验证奖励的数据来源（`curl /run_code` 连通性验证命令见 recipe README）。

## veRL 适配：自定义奖励函数 `scalebox.py`

ScaleBox 接入 veRL 训练流的核心适配点是 recipe 自带的 **`scalebox.py`——verl 适配 ScaleBox 的自定义奖励函数文件**。它把 veRL 的 reward 计算桥接到 ScaleBox 的代码执行服务上：veRL rollout 出代码后，由该奖励函数调用 ScaleBox（如批量接口 `common_evaluate_batch`）执行测试用例、按通过情况算可验证奖励，回填 GRPO 优势计算（本 recipe 所有 run 脚本实测 `algorithm.adv_estimator=grpo`；算法见 [grpo-dapo](../techniques/grpo_dapo.md)，DAPO 为同族对照、不参与 ScaleBox Code RL 回路）。

为让 veRL 更好地跑 Code RL，recipe 还对 veRL 打了 patch `0001-verl-feature-improve_rl_usability.patch`，其改动**直接围绕沙盒资源治理与超时**：

- 在 `prime reward manager` 中增加对 `code_contests` 数据源的支持；
- 调整 `prime reward manager` 并发进程数从 **64 降至 32**，以**避免沙盒资源竞争**；
- 延长 `prime reward manager` 任务超时时间从 **300s 延长至 3000s**，以支持更大批量数据下的代码执行；
- 增强训练过程日志打印，便于调试。

可见 veRL↔ScaleBox 的工程难点不在算法、而在**沙盒并发与执行超时的协调**——reward manager 的并发要压到沙盒能稳定承载的水平（32），单次代码执行的超时要放宽到能跑完大批量用例（3000s）。应用方式：`git apply patches/verl/0001-verl-feature-improve_rl_usability.patch`。

## 数据与统一评估

训练数据基于 [PrimeIntellect/verifiable-coding-problems](https://huggingface.co/datasets/PrimeIntellect/verifiable-coding-problems)，过滤其中较高质量的 Python 代码部分作训练集（verifiable-coding-problems-python-only），由 `build_dataset.py` 构建。评测复用 ScaleBox 作为执行后端，与训练同口径：LiveCodeBench `release_version=v5`、`start_date=2024-08-01`、`code_execution=ScaleBox`；推理参数 `n=4`、`temperature=0.6`、`top_p=0.95`、`max_tokens=32768`。

ScaleBox + veRL 的 Code RL 训练在 LiveCodeBench(pass@1) 上的端到端效果：

| Model | 机器 | GBS | n_samples | step | LiveCodeBench(pass@1) |
|---|---|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-1.5B | Atlas A2 8 卡 | 128 | 8 | 500 | 19.80 |
| Qwen3-4B-Instruct-2507 | Atlas A3 16 卡 | 128 | 8 | 450 | 44.18 |
| Qwen3-30B-A3B-Instruct-2507 | Atlas A3 32 卡 | 128 | 8 | 450 | 56.27 |

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen2_code_rl/figures/training_progress_qwen3_4b.png" width="55%"></p>
<p align="center"><sub>图：Qwen3-4B-Instruct-2507 在 veRL + ScaleBox 上的 Code RL 训练进度曲线（LiveCodeBench pass@1 最终 44.18）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen2_code_rl/README.md">qwen2_code_rl recipe·模型评测</a>）</sub></p>

## 在工具调用 Code RL 中的复用

ScaleBox 也是**多轮工具调用 Code RL**（Agent RL）实践的代码执行后端：recipe `agent_rl/qwen3_code_toolcall` 让 Qwen3-1.7B 把 ScaleBox 当成「Python 工具」在推理过程中多轮调用（首个开源的、基于 veRL 支持多轮工具调用的 Coding Agent RL recipe，详见 [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)）。此场景下：

- ScaleBox 服务部署方式与基础样例一致（`make run-online`、`/run_code` 验证），区别仅在 `MAX_MEM=50000000`（限单进程内存）而非 `unlimited`，且工具调用由 `tool_config/scalebox_tool_config.yaml` 配置；
- `scalebox.py` 自定义奖励函数与 `0001-verl-feature-improve_rl_usability.patch` **直接沿用基础样例、未作修改**，叠加 `0002-enable-tool-agent-loop.patch`（多轮工具调用）与 `0003-toolcall-reward.patch`（工具调用奖励）支撑 agent-loop；
- 推测解码扩展（Suffix/EAGLE3，见 [sam-speculative](../techniques/sam_speculative.md) 的同类 Suffix 路线）换用更新的 `vllm 0.13.0` / `vllm_ascend v0.13.0`，但 ScaleBox 服务与奖励桥接逻辑不变——说明 ScaleBox 与 rollout 引擎版本解耦，沙盒侧无需随推理栈升级而改。

可见 ScaleBox 在「单轮 Code RL」与「多轮工具调用 Agent RL」两类实践中是**同一个可复用的执行底座**，靠 `scalebox_tool_config.yaml` 与奖励函数差异适配不同 RL 形态。

## Evidence

- [scalebox](https://gitcode.com/icip-cas/ScaleBox) — ScaleBox 上游开源仓 `gitcode.com/icip-cas/ScaleBox`（`make run-online` 在线服务入口、`/run_code` 与 `common_evaluate_batch` 接口、分布式部署）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`agent_rl/qwen2_code_rl/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen2_code_rl/README.md)（ScaleBox 三大核心特性、融合镜像 `verl.Dockerfile`/`verl_sandbox.Dockerfile`、`make run-online` 部署 + `/run_code` 验证、`scalebox.py` 自定义奖励函数、`0001-verl-feature-improve_rl_usability.patch`（并发 64→32 避沙盒竞争、超时 300s→3000s）、数据集 `build_dataset.py`、LiveCodeBench benchmark）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`agent_rl/qwen3_code_toolcall/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md)（ScaleBox 作工具调用后端：`tool_config/scalebox_tool_config.yaml`、`scalebox.py`/patch 沿用基础样例、`MAX_MEM=50000000`、`0002-enable-tool-agent-loop.patch`/`0003-toolcall-reward.patch`、推测解码扩展 vllm 0.13.0）
- 上游开源仓：ScaleBox `gitcode.com/icip-cas/ScaleBox`、veRL `github.com/volcengine/verl @ c651b7b`、华为云 ModelArts（迁移目标平台）

## Links

- [verl](verl.md)（融合的训练框架：veRL 跑 RL 主回路 + rollout，ScaleBox 经自定义奖励函数 `scalebox.py` 接入其 reward 计算；patch 在 `prime reward manager` 调沙盒并发/超时）
- [qwen2-code-rl-scalebox](../../guides/recipes/qwen2_code_rl_scalebox.md)（承载实践：veRL + ScaleBox 单轮 Code RL，DeepSeek-R1-Distill-1.5B / Qwen3-4B / Qwen3-30B-A3B 在 LiveCodeBench 上的端到端验证）
- [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（承载实践：ScaleBox 作多轮工具调用后端的 Coding Agent RL，Qwen3-1.7B 首个开源 verl 多轮工具调用 recipe）
- [vllm-ascend](vllm_ascend.md)（同实践 rollout 推理后端：veRL 用 vLLM-Ascend 在 NPU 生成代码，ScaleBox 执行其产出）
- [grpo-dapo](../techniques/grpo_dapo.md)（承载 RL 算法：ScaleBox 返回的测试通过率作可验证奖励，回填 GRPO 优势计算；DAPO 为同族对照，不在 ScaleBox Code RL 回路）
- [agent-rl-loop](../techniques/agent_rl_loop.md)（agent RL 多轮工具调用用 Sandbox/ScaleBox）

<!-- cannbot:related:start -->
## 相关

- [Qwen3-1.7B 多轮工具调用 Code RL（verl + ScaleBox 沙盒 + EAGLE3/Suffix 投机解码）](../../guides/recipes/qwen3_code_toolcall_rl.md)（`related`）：训练时模型把 ScaleBox 沙盒当成「Python 工具」在推理过程中多轮调用（写代码→执行→看结果→续推）；**ScaleBox**（［icip-cas/ScaleBox］(https://gitcode.com/icip-cas/ScaleBox)）是一个开源的**可扩展分布式代码执行沙盒**。实践页把 ScaleBox 作为 Python 工具嵌入多轮 Code RL，框架页补齐其分布式执行、评估和奖励后端职责。
- [veRL + ScaleBox 沙盒长上下文 Code RL（DeepSeek-R1-Distill-1.5B / Qwen3-4B / Qwen3-30B-A3B）](../../guides/recipes/qwen2_code_rl_scalebox.md)（`related`）：“在昇腾 NPU 上，ScaleBox 与训练框架 ［veRL］(verl.md) 融合部署（单节点同跑 ScaleBox 服务 + veRL 训练、可零成本迁 ModelArts），并在 veRL 侧通过自定义奖励函数 `scalebox.py` 接入 RL 训练流。”与“ScaleBox 接入 veRL 训练流的核心适配点是 recipe 自带的 `scalebox.py`——verl 适配 ScaleBox 的自定义奖励函数文件：veRL rollout 出代码后，由该奖励函数调用 ScaleBox（如批量接口 `common_evaluate_batch`）执行测试用例、按通过情况算可验证奖励，回填 GRPO/DAPO 优势计算。”是双方正文中的具体合同。框架卡指出 `scalebox.py` 是 veRL 接入点，recipe 继续给出 rollout、批量执行测试和奖励回填链，能直接推进 Code RL 集成落地。
<!-- cannbot:related:end -->
