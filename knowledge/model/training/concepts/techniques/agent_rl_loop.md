---
type: Concept
title: Agent RL 执行范式（asyncLLM 异步生成 + agent_loop 多轮工具调用）
description: Agent RL 与朴素 RLVR 的根本区别在 rollout 阶段的执行形态：朴素 RL 一个 prompt 一次性生成完整 response 再算 reward；Agent RL 让模型在生成过程中调用外部工具/代码沙盒，把工具返回结果作为新一轮输入继续推理，多轮交互收敛后才算 reward。veRL 通过参考其 recipe/retool 项目，用两个特性把这套执行机制落到昇腾 NPU 上：asyncLLM（异步生成——以 HTTP Server 形态暴露 vLLM 引擎，让每个 prompt 的 request 独立异步推进）+ agent_loop（多轮 agent 循环——ToolAgentLoop 驱动「模型推理 → 检查是否要调工具 → 执行工具 → 结果回灌」状态机直到终止）。
tags:
- task.optimization
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Agent RL 执行范式（asyncLLM 异步生成 + agent_loop 多轮工具调用）

## Summary

**Agent RL** 与朴素 RLVR 的根本区别在 rollout 阶段的执行形态：朴素 RL 一个 prompt 一次性生成完整 response 再算 reward；Agent RL 让模型在生成过程中**调用外部工具/代码沙盒**，把工具返回结果作为新一轮输入继续推理，**多轮交互**收敛后才算 reward。[veRL](../frameworks/verl.md) 通过参考其 `recipe/retool` 项目，用两个特性把这套执行机制落到昇腾 NPU 上：**`asyncLLM`**（异步生成——以 HTTP Server 形态暴露 vLLM 引擎，让每个 prompt 的 request 独立异步推进）+ **`agent_loop`**（多轮 agent 循环——`ToolAgentLoop` 驱动「模型推理 → 检查是否要调工具 → 执行工具 → 结果回灌」状态机直到终止）。

该范式由多轮交互（problem → reason → tool call → result → reason → answer）、`asyncLLM` 的 HTTP Server 化与负载均衡/粘性会话、`agent_loop` 的 `ToolAgentLoop` 状态机、模型推理与工具执行的**异步并行流水**、以及代码沙盒（[Sandbox / SandboxFusion / ScaleBox](https://gitcode.com/icip-cas/ScaleBox)）作为工具后端组成。两个落地 recipe 见 [qwen3-tool-agent-rl](../../guides/recipes/qwen3_tool_agent_rl.md)（verl-retool，Qwen3-4B 数学工具 Agent，SFT+RL）与 [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（Qwen3-1.7B 长上下文多轮工具调用 Code RL + ScaleBox）。

## 为什么 Agent RL 需要异步 + 多轮

朴素 RLVR 的 rollout 是「输入 prompt → 一次性生成 response → 算 reward」的单轮过程。Agent RL 要求模型把**工具调用嵌进生成链路**——例如做数学/编程题时先用文本推理分析，再调用代码工具执行复杂计算，把代码返回结果当作新一轮输入校验后输出答案。verl-retool 样例训出的 Qwen3-4B 模型 response 即遵循：

> 问题输入 → 模型思考 → 调用代码工具 → 返回结果作为新一轮的输入 → 模型思考 → 生成答案

这带来两个 RL 系统层面的需求。其一，单轮生成被切成「生成片段 + 工具执行 + 再生成」多段，整条轨迹是**多轮（multi-turn）对话**——验证指标 `val-aux/num_turns/mean` 即「每一次 user 或 assistant 的输入算一次 num_turn」的平均轮数（verl-retool 训练后从 7.0 降到 5.4，模型学会用更少轮数解题；同期 `aime_2025` `acc/mean@30` 从 0.29 升到 0.57）。其二，工具执行（Python CI / 代码沙盒）是**外部阻塞 I/O**，若同步等待会让 NPU 推理空转，因此必须让推理与工具执行**异步并行**。`asyncLLM` 与 `agent_loop` 正是分别解决这两个需求。

## agent_loop：ToolAgentLoop 多轮状态机

`agent_loop` 特性下，每个 prompt 的 agent 轨迹由 **`ToolAgentLoop`** 类驱动——它是 agent RL 训练中的核心类，实现 multi-turn 交互中 Agent reasoning → tool call 循环。其关键状态处理两个方法：

- **`_handle_generating_state()`**：负责调用大模型生成响应，并**检查是否需要调用工具**。
- **`_handle_processing_tools_state()`**：负责**执行工具调用**，并将工具返回结果**格式化作为下一轮的输入**。

两个状态交替推进，直到模型不再请求工具（输出最终答案），整条多轮轨迹拼成一条 response 序列送去算 reward。下图给出 README 附录的 ToolAgent 代码结构——`ToolAgentLoop` 在生成态经 `AsyncLLMServerManager` 拿模型响应、在工具态把代码送进 SandboxFusion 沙盒服务并回灌结果：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.assets/ToolAgent代码结构图.png" width="78%">
<sub>图：ToolAgent 代码结构——`ToolAgentLoop` 的 `_handle_generating_state` 经 `AsyncLLMServerManager` 拿模型响应（output→res），`_handle_processing_tools_state` 把代码送 SandboxFusion 沙盒；底层 vLLM 引擎由 `vLLMHttpServer` 暴露（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.md">verl-retool agent 样例 README</a>·附录 ToolAgent 代码结构）</sub>

## asyncLLM：HTTP Server 化的异步生成

`asyncLLM` 把 rollout 的 vLLM 引擎从「批量同步 `generate`」改造成**以 HTTP Server 形态独立服务**：每个 vLLM 引擎实例由一个 `vLLMHttpServer` 暴露，多个 Server 实例之上由 **`AsyncLLMServerManager`** 统一调度，它有两个功能：

- **负载均衡**：在首轮请求时，选择请求最少的 Server 实例发送；
- **粘性会话（sticky session）**：将多轮会话的补全请求发送到**同一个** Server 实例，从而**复用之前对话的缓存（KV cache）**，提高硬件利用率。

粘性会话是 agent 多轮场景的关键优化——同一条 agent 轨迹的后续轮次落回同一 Server，可直接复用前几轮 prompt+response 已算好的 KV cache，避免重复 prefill。这一 HTTP Server + per-request 异步推进的形态，正是让「某些 prompt 在等工具执行」与「另一些 prompt 在 NPU 上推理」能并行的前提。

## SFT 冷启动 + RL：两阶段训出工具调用能力

Agent RL 在 RL 之前通常需要一个 **SFT 冷启动**阶段——纯靠 RL 从零探索工具调用格式收敛慢且不稳，先用带工具调用轨迹的数据 SFT，让模型**学会调用工具的格式与时机**，再用 RL **改进对工具的使用**。两个样例都遵循这一两阶段范式（数据集不同）：

- **verl-retool**（[qwen3-tool-agent-rl](../../guides/recipes/qwen3_tool_agent_rl.md)）：SFT 用 `ReTool-SFT` 数据集训 Qwen3-4B-Instruct-2507，「帮助模型学会调用 Sandbox 工具进行 python 编程」；RL 用 `DAPO-Math-17k` 训前一步 SFT 过的模型，「帮助模型更好地使用 Sandbox 工具，辅助自身推理思考」。SFT 后用 `verl.model_merger merge --backend fsdp` 合并 `global_step_186` 权重再进 RL。
- **Code RL 基础样例**（[qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)）：SFT 基于 `Gen-Verse/Open-AgentRL-SFT-3K` 过滤出含多轮 Python 工具调用的 Coding 推理数据（`run_toolcall_sft_demo.sh`，选 `sft_step_50` ckpt 合并）；RL 数据基于 `PrimeIntellect/verifiable-coding-problems` 过滤高质量 Python 题（`run_code_rl_demo.sh`）。它是首个开源的基于 verl 支持多轮工具调用的 Coding Agent RL Recipe。

两阶段的产物在 RL 阶段才进入 `asyncLLM` + `agent_loop` 多轮执行流水；SFT 阶段仍是普通单轮序列训练。注意 Code RL 的推测解码扩展直接用 HuggingFace 公开 Qwen3-1.7B 权重、**跳过 SFT**，因其目标是验证 rollout 加速而非工具能力本身。

## 异步流水：推理与工具执行并行

在 ToolAgent 异步流水中，每个 prompt 的 request 都遵循 `AsyncLLMServerManager` 的调度规则，在此基础上实现 **vLLM 推理与 Python CI（代码沙盒）工具调用的异步并行**。下图给出 rollout 过程中模型推理与外部工具执行的并行情况：上半部多个 `vLLMHttpServer`（gen 0/1/2）持续生成 token，下半部多个 Python CI worker 在不同时刻执行被触发的 tool call——当某请求进入工具执行（外部阻塞），NPU 推理流不空等，转去推进其它请求，工具结果就绪后再回灌对应轨迹：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.assets/ToolAgent异步流水图.png" width="58%">
<sub>图：ToolAgent 异步流水——vLLM 推理（蓝色 token 块）与 Python CI worker 的工具调用/返回（黄色 tool req）在时间轴上交错并行，prompt/res/tool call/tool res 四类事件异步推进（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.md">verl-retool agent 样例 README</a>·附录 ToolAgent 异步流水）</sub>

## 工具后端：代码沙盒（Sandbox / ScaleBox）

`agent_loop` 调的「工具」在两个样例里都是**代码执行沙盒**——模型生成的 Python 代码送进沙盒执行、回传 stdout 作为下一轮输入。两个 recipe 用了不同沙盒实现，但接口范式一致（HTTP 服务 + `run_code` 风格 API）：

- **SandboxFusion**（verl-retool 样例）：字节跳动开源沙盒，以 HTTP 服务暴露 `run_code`（默认 `http://0.0.0.0:8080`）；`ToolAgentLoop` 在工具态把模型生成的代码送进该 SandboxFusion 服务执行、回传 stdout 作为下一轮输入。Sandbox 服务在训练期间需常驻，「agent 在训练时需要实时交互」。

- **[ScaleBox](../frameworks/scalebox.md)**（Code RL 样例）：面向 Code RL 的可扩展分布式代码沙盒，支持多机分布式部署 + 请求负载均衡、单元测试并行、批量评估接口 `common_evaluate_batch`、Special Judge 判题，内置 LiveCodeBench/HumanEval/MBPP 评测。样例提供 verl + ScaleBox 融合镜像（`verl_sandbox.Dockerfile`），单节点内同时跑沙盒服务与训练；verl 侧由 `scalebox.py` 实现自定义奖励函数、`patches/verl/0002-enable-tool-agent-loop.patch` 使能多轮工具调用。沙盒以 `run_code` 验证（示例返回 `{"status":"Success",...,"stdout":"Hello, world!\n"}`）。

两个样例都通过 verl patch 把 reward 与工具调用挂钩：verl-retool 用 `0003-Modify-compute_score-to-encourage-tool-call.patch` 修改奖励函数鼓励工具调用、`0001-Fix-reward-function-not-accessing-num_turns.patch` 让奖励函数能拿到 `num_turns`；Code RL 用 `0003-toolcall-reward.patch` 增加 Toolcall reward 增强训练稳定性。

## verl 使能：版本、patch 与启动

`asyncLLM` + `agent_loop` + retool 不在 verl 主分支默认可用，需 checkout 特定历史版本并打 patch：

- **verl-retool 样例**：retool 已从 verl 迁出，「最新分支无该项目」，需 `git checkout 95470480`（含 retool 的历史版本），`git am ../patches/*.patch` 打三个 fix/path/reward patch，`pip install -e .` 后进 `recipe/retool`。RL 启动 `bash run_qwen3_4b_dapo_npu.sh`（[DAPO](grpo_dapo.md) 算法 + DAPO-Math-17k）。TensorBoard 用 `trainer.logger=['console','tensorboard']` + `trainer.log_val_generations=10` 看训练曲线与每次验证的 response。

- **Code RL 样例**：`git checkout c651b7b4207e408875f132c4226969ef3495d408`（基于 v0.7.0.dev），`git apply` 三个 patch——其中 `0002-enable-tool-agent-loop.patch` 即「支持 Coding 多轮工具调用的训练逻辑」。基础样例用 vLLM `0.11.0` / vLLM-Ascend `v0.11.0rc1`；推测解码扩展换 vLLM `0.13.0` / vLLM-Ascend `v0.13.0`（「更稳定的推测解码支持和异步实现」）。

> Code RL 样例同时验证了在 agent_loop 多轮工具调用流水上叠加推测解码（EAGLE3 / Suffix）：分析表明 **Rollout 阶段占总 RL 训练步骤时间的 78.3%**（Qwen3-1.7B 每步 3596.5s 中的 2816.6s），推测解码直接加速 vLLM rollout，端到端吞吐量最高提升 **38%**、训练步骤时间缩短 **25%**、精度无损失。其局限在于：EAGLE3 草稿模型在 RL 训练期间保持冻结，随 Actor 策略逐渐偏离草稿模型训练分布，**草稿接受率呈缓慢下降趋势**（源给出在线草稿模型训练作为后续缓解方向）。Suffix 路线与 [SAM 无损投机](sam_speculative.md) 同属基于检索的 Model-Free 方案，无独立草稿模型——推断不受此策略漂移影响（源未直接对比 Suffix 漂移特性）。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`agent_rl/qwen3_tool_agent/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_tool_agent/README.md)（verl-retool agent 样例：`asyncLLM`/`agent_loop` 概述、SFT(ReTool-SFT)+RL(DAPO-Math-17k) 两步、Sandbox(SandboxFusion) 部署、`git checkout 95470480` + `git am patches/*.patch`、验证指标 `num_turns`/`acc@30`、附录 `ToolAgentLoop`/`_handle_generating_state`/`_handle_processing_tools_state`/`AsyncLLMServerManager`(负载均衡+粘性会话) 代码结构图与异步流水图、TensorBoard）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`agent_rl/qwen3_code_toolcall/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md)（Qwen3-1.7B 长上下文多轮工具调用 Code RL：ScaleBox 沙盒特性、verl `c651b7b` + `0002-enable-tool-agent-loop.patch`/`0003-toolcall-reward.patch`、SFT+RL、LiveCodeBench 评测、推测解码扩展 Rollout 78.3% / +38% / -25% / 精度无损 / EAGLE3 冻结草稿接受率缓降）
- 图：两图取自 `agent_rl/qwen3_tool_agent/README.assets/`（ToolAgent 代码结构图 / 异步流水图）
- 外部参考：[ScaleBox](https://gitcode.com/icip-cas/ScaleBox)、[SandboxFusion](https://github.com/bytedance/SandboxFusion)、[verl/recipe retool](https://github.com/volcengine/verl)

## Links

- [verl](../frameworks/verl.md)（承载框架：`asyncLLM`+`agent_loop` 是 veRL retool 经 patch 使能的 rollout 执行特性，核心类 `ToolAgentLoop` 驱动多轮状态机）
- [scalebox](../frameworks/scalebox.md)（Code RL 样例的工具后端：分布式代码执行沙盒，融合镜像 verl_sandbox + `scalebox.py` 奖励函数）
- [qwen3-tool-agent-rl](../../guides/recipes/qwen3_tool_agent_rl.md)（落地实践：verl-retool Qwen3-4B 数学工具 Agent，SFT+RL，SandboxFusion，acc@30 0.29→0.57）
- [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（落地实践：Qwen3-1.7B 长上下文多轮工具调用 Code RL + ScaleBox，叠推测解码 +38% 吞吐）
- [grpo-dapo](grpo_dapo.md)（承载 RL 算法：verl-retool 用 DAPO 在 agent_loop 多轮轨迹上算优势/奖励）
- [sam-speculative](sam_speculative.md)（可叠加：Code RL 样例在 agent_loop rollout 上叠 Suffix/EAGLE3 推测解码，Suffix 与 SAM 同属 Model-Free 检索路线）
