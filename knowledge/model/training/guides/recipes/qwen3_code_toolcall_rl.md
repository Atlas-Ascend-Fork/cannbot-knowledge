---
type: Guide
title: Qwen3-1.7B 多轮工具调用 Code RL（verl + ScaleBox 沙盒 + EAGLE3/Suffix 投机解码）
description: 基于 Qwen3-1.7B，用 verl RL 框架 + 适配昇腾的代码执行沙盒 ScaleBox，在 Atlas A2/A3 单机八卡上实现长上下文多轮工具调用 Code RL 训练，是首个开源的、基于 verl 支持多轮工具调用的 Coding Agent RL 实践。训练时模型把 ScaleBox 沙盒当成「Python 工具」在推理过程中多轮调用（写代码→执行→看结果→续推），由含工具调用奖励的奖励信号驱动策略提升。实践分两部分——(1) 基础样例：SFT 冷启动 + 含工具调用奖励的多轮工具调用 Code RL；(2) 推测解码扩展：把 EAGLE3 + Suffix 投机解码集成进 verl + vLLM-Ascend 的 rollout 流水线，端到端吞吐最高 +38%、训练步时间 -25%、精度无损。
tags:
- task.implementation
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# Qwen3-1.7B 多轮工具调用 Code RL（verl + ScaleBox 沙盒 + EAGLE3/Suffix 投机解码）

## Summary

基于 **Qwen3-1.7B**，用 [verl](../../concepts/frameworks/verl.md) RL 框架 + 适配昇腾的代码执行沙盒 [ScaleBox](../../concepts/frameworks/scalebox.md)，在 Atlas A2/A3 单机八卡上实现**长上下文多轮工具调用 Code RL** 训练，是首个开源的、基于 verl 支持多轮工具调用的 Coding Agent RL 实践。训练时模型把 ScaleBox 沙盒当成「Python 工具」在推理过程中多轮调用（写代码→执行→看结果→续推），由含**工具调用奖励**的奖励信号驱动策略提升。实践分两部分——(1) 基础样例：SFT 冷启动 + 含工具调用奖励的多轮工具调用 Code RL；(2) 推测解码扩展：把 **EAGLE3 + Suffix 投机解码**集成进 verl + [vLLM-Ascend](../../concepts/frameworks/vllm_ascend.md) 的 rollout 流水线，端到端吞吐最高 **+38%**、训练步时间 **-25%**、精度无损。

机制本身链向各自页面：多轮工具调用循环见 [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)，沙盒侧见 [scalebox](../../concepts/frameworks/scalebox.md)，RL 框架与训推共卡见 [verl](../../concepts/frameworks/verl.md)，rollout 推理后端见 [vllm-ascend](../../concepts/frameworks/vllm_ascend.md)。EAGLE3+Suffix 与无模型检索式的 [SAM 投机](../../concepts/techniques/sam_speculative.md)形成投机方法对照（详见下文）。

## 硬件与软件

- **硬件**：Atlas A2/A3 系列，**单机八卡**。
- **软件**：基础样例与 SD 扩展共用同一个 verl commit，但 vLLM 版本不同——SD 扩展用更新的 vLLM `0.13.0` + vLLM-Ascend `v0.13.0`，带来更稳定的推测解码支持和异步实现。

| 组件 | 基础样例 | 推测解码扩展 |
|---|---|---|
| 环境 | Docker | Conda |
| verl | commit `c651b7b`（基于 v0.7.0.dev） | commit `c651b7b`（基于 v0.7.0.dev） |
| vllm | `0.11.0` | `0.13.0` |
| vllm-ascend | `v0.11.0rc1` | `v0.13.0` |
| CANN | `8.3.RC1` | `8.5.0` |

verl 锁定 commit `c651b7b4207e408875f132c4226969ef3495d408`；SD 扩展锁 vllm-ascend commit `6281c1207a7a499e9f23a42b3a1e7027469f2b10`。CANN `8.3.RC1` 预计同样适用于 SD 扩展。

## 基础样例：含工具调用奖励的多轮工具调用 Code RL

### 部署形态：verl + ScaleBox 融合镜像

**融合 verl 与 ScaleBox 的统一部署镜像**支持在单节点中同时运行 ScaleBox 服务与 verl 训练任务，并支持零成本迁移至华为云 ModelArts——融合镜像在 `agent_rl/qwen2_code_rl` 的 verl 镜像基础上叠加 ScaleBox（`verl_sandbox.Dockerfile`）构建，使沙盒与训练共处同一节点。沙盒服务的单节点/分布式部署细节见 [scalebox](../../concepts/frameworks/scalebox.md)。

### verl 补丁（Code RL 适配点）

verl `git checkout c651b7b...` 后依次应用三个补丁：

```bash
git apply patches/verl/0001-verl-feature-improve_rl_usability.patch
git apply patches/verl/0002-enable-tool-agent-loop.patch
git apply patches/verl/0003-toolcall-reward.patch
```

- `0001-verl-feature-improve_rl_usability.patch`（通用可用性，**共享**）：在 `prime reward manager` 中增加对 `code_contests` 数据源支持；并发进程数从 64 降至 32 避免沙盒资源竞争；任务超时从 300s 延长至 3000s 以支持更大批量代码执行；增强训练日志便于调试。
- `0002-enable-tool-agent-loop.patch`（多轮工具调用，**共享**）：支持 Coding 多轮工具调用训练逻辑（agent-loop 机制见 [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)）。
- `0003-toolcall-reward.patch`（**仅基础样例**）：增加 Toolcall reward，增强训练稳定性。

ScaleBox 的工具调用配置在 `tool_config/scalebox_tool_config.yaml`，verl 侧自定义奖励函数为 `scalebox.py`（接入逻辑见 [scalebox](../../concepts/frameworks/scalebox.md)）。

### 数据与 SFT 冷启动

- **SFT 工具调用数据**：基于 `Gen-Verse/Open-AgentRL-SFT-3K`，过滤其中含多轮 Python 工具调用的 Coding 推理数据并转格式（`build_toolcall_sft_data.py`）。
- **RL 数据**：基于 `PrimeIntellect/verifiable-coding-problems`，过滤较高质量的 Python 代码数据（`verifiable-coding-problems-python-only`，`build_rl_dataset.py`）。
- **SFT 冷启动**：`run_toolcall_sft_demo.sh` 训练后选 `sft_step_50` 的 ckpt，用 `python3 -m verl.model_merger merge --backend fsdp ...` 合并 FSDP 权重为 HuggingFace 格式，作为 RL 初始权重。

### RL 训练与结果

RL 由 `bash run_code_rl_demo.sh` 拉起。训练指标（下图三联：训练数据得分 / 推理长度·截断比例 / 工具调用交互轮次）显示，随训练推进 `score`、`response_length_non_aborted_mean`、`num_turns_mean` 同步上升——模型学会更长链路、更多轮工具调用来解题：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/figures/training_progress.png" width="55%">
<sub>图：基础样例训练指标（steps 0–250）——上 `accuracy/score`（训练数据得分，无重复数据）、中 `response_length_non_aborted_mean`（非截断推理长度）、下 `num_turns_mean`（工具调用交互轮次均值），三者随训练上升（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md">Qwen3 Code Toolcall RL README</a>·训练结果）</sub>

模型评测在 **LiveCodeBench**（release v5、start_date 2024-08-01、代码执行用 ScaleBox），推理参数遵循 DeepSeek-R1 设置（n=4、temperature=0.6、top_p=0.95、max_tokens=32768）。LiveCodeBench pass@1 随训练步数从 step20 的 **16.03** 单调爬升到 step240 的 **28.39**（step60 18.08 / 120 20.14 / 160 24.45 / 200 25.97 / 240 28.39）：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/figures/evaluation_progress.png" width="55%">
<sub>图：训练各 ckpt 在 LiveCodeBench（n=4, temperature=0.6, top_p=0.95, max_tokens=32768, v5, start_date 2024-08-01）上的 pass@1——从 16.03（step20）升至 28.39（step240）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md">Qwen3 Code Toolcall RL README</a>·模型评测）</sub>

## 推测解码扩展（EAGLE3 + Suffix）

### 动机：rollout 是 RL 步时间瓶颈

**rollout 阶段占总 RL 步时间的 78.3%**（Qwen3-1.7B 每步 3596.5s 中的 2816.6s）。推测解码通过加速 vLLM rollout 阶段的 token 生成直接解决这一瓶颈，目标是在**不损失精度**前提下实现 **≥25% 端到端训练加速**。该扩展直接用 HuggingFace 公开 Qwen3-1.7B 权重，**无需基础样例的 SFT 微调步骤**；`0001`/`0002` 补丁、`build_rl_dataset.py`、`scalebox.py` 均直接沿用基础样例未作修改，工具调用奖励步骤也不需要。

### 集成补丁与脚本

SD 扩展在 Conda 环境（`verl-specrl`）下验证。verl 侧 `0003-toolcall-reward.patch` 换成 `0004-enable-specrl-clean.patch`（Suffix/EAGLE3 投机解码集成），vLLM 侧另应用 `patches/vllm/0001-enable-eagle-sprl.patch`（vLLM 侧 EAGLE3 投机支持）。EAGLE3 草稿模型由 `download_eagle.py` 下载，三个训练脚本对照拉起：

```bash
bash no_spec_rl_run.sh   # 基线：不含投机解码
bash eagle3_rl_run.sh    # 含 EAGLE3 投机解码（需 DRAFT_MODEL_PATH）
bash suffix_rl_run.sh    # 含 Suffix 投机解码
```

该补丁实现了**无累计开销的逐步投机解码指标采集**——草稿 token 数、接受 token 数、草稿接受率、平均接受长度及逐位置接受率；训练后用 `process_all_the_logs_sprl.py <logs> -o combined_metrics.csv` 对 SD/基线两次训练分别处理生成对比 CSV。

### 结果：端到端吞吐 +38% / 步时间 -25% / 精度无损

与基线相比，Suffix 与 EAGLE3 投机解码端到端吞吐量**最高提升 38%**、训练步时间缩短 **25%**，且精度无损失。逐 step 吞吐提升曲线显示 eagle3 与 suffix 的均值提升均在 +35% 量级（图内标注 eagle3 mean ≈ +34.9%、suffix mean ≈ +35.6%），单步峰值可达 ~56%：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/figures/throughput_speedup.png" width="55%">
<sub>图：相对基线（0% nospec）的逐 RL step 吞吐提升（tokens/s）——eagle3 与 suffix 均值约 +35%，峰值约 +56%，最高 +38%（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md">Qwen3 Code Toolcall RL README</a>·训练结果）</sub>

精度对照（critic score 均值随 RL step）显示 nospec / eagle3 / suffix 三条曲线高度重合、终点差异在 ±1.0% 噪声内，印证「精度无损」：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/figures/sd_nosd_accuracy.png" width="55%">
<sub>图：投机 vs 无投机精度对照（critic score 均值随 RL step）——nospec/eagle3/suffix 曲线高度重合，终点差 ±1.0%，投机解码精度无损（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md">Qwen3 Code Toolcall RL README</a>·训练结果）</sub>

### 局限：冻结草稿模型导致接受率衰减

由于 **EAGLE3 草稿模型在 RL 训练期间保持冻结**，随着 Actor 策略逐渐偏离草稿模型的训练分布，草稿接受率呈**缓慢下降趋势**（图中从约 0.46 随训练步数滑落到约 0.35）：

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/figures/acceptance_rate_overall.png" width="55%">
<sub>图：RL 训练过程中整体草稿接受率（Raw）——冻结的 EAGLE3 草稿模型因 Actor 策略漂移，接受率从约 0.46 缓慢降至约 0.35（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md">Qwen3 Code Toolcall RL README</a>·训练结果）</sub>

据此可行的缓解方向：**在线草稿模型训练**（RL 中联合训练 EAGLE3 草稿模型对抗策略漂移）、**弹性投机**（自适应调整投机 token 数）、块验证、Ngram 投机修复、在线 MTP。

## 投机方法对照：EAGLE3/Suffix vs SAM

本实践走**辅助草稿模型（EAGLE3）+ 后缀匹配（Suffix）**路线，与 cann-train 另一投机实践 [SAM 无损投机](../../concepts/techniques/sam_speculative.md) 的**无模型检索**路线形成对照：

| 维度 | EAGLE3 | Suffix | SAM（[sam-speculative](../../concepts/techniques/sam_speculative.md)） |
|---|---|---|---|
| 草稿来源 | 依附主模型的轻量 EAGLE3 草稿模型（独立权重，需下载） | 从已生成文本做后缀匹配取草稿 | 动态后缀自动机检索「最长后缀+后续序列」 |
| 额外组件 | 需草稿模型权重 + vLLM EAGLE patch | 无额外模型 | 无额外模型参数 |
| RL 中的隐患 | **草稿模型冻结→策略漂移→接受率随训练衰减**（实测 0.46→0.35） | 受生成文本重复性影响 | 不引入草稿分布漂移，对权重频繁更新天然友好 |
| 缓解/演进 | 探索在线草稿模型训练、弹性投机 | — | 动态 SAM 随序列变长接受率反而上升 |

两者都瞄准 RL rollout 采样瓶颈（此处 rollout 占步时间 78.3%，SAM 路线同样针对 rollout 这一 RL 主要耗时来源）。EAGLE3 在训推共卡 + 权重持续更新的 RL 场景需额外应对草稿漂移，这正是 SAM 无模型路线的设计动机所在——两者互为补充。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`agent_rl/qwen3_code_toolcall/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/README.md)（概述与贡献点、硬件 A2/A3 单机八卡、软件版本表（verl c651b7b / vllm 0.11.0·0.13.0 / vllm-ascend v0.11.0rc1·v0.13.0 / CANN 8.3.RC1·8.5.0）、文件说明、基础样例 verl 三补丁与修改清单、SFT 冷启动 sft_step_50 + model_merger、RL `run_code_rl_demo.sh`、训练/评测结果（LiveCodeBench 16.03→28.39）、SD 扩展 rollout 占比 78.3%、`0004`/vllm `0001-enable-eagle-sprl` 补丁、eagle3/suffix/no_spec 脚本、`process_all_the_logs_sprl.py`、吞吐 +38%/步时间 -25%/精度无损、接受率衰减与未来工作）
- recipe 文件（`agent_rl/qwen3_code_toolcall/` 目录下）：[`patches/verl/0001-verl-feature-improve_rl_usability.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/patches/verl/0001-verl-feature-improve_rl_usability.patch)、[`patches/verl/0002-enable-tool-agent-loop.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/patches/verl/0002-enable-tool-agent-loop.patch)、[`patches/verl/0003-toolcall-reward.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/patches/verl/0003-toolcall-reward.patch)、[`patches/verl/0004-enable-specrl-clean.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/patches/verl/0004-enable-specrl-clean.patch)、[`patches/vllm/0001-enable-eagle-sprl.patch`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/patches/vllm/0001-enable-eagle-sprl.patch)、[`tool_config/scalebox_tool_config.yaml`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/tool_config/scalebox_tool_config.yaml)、[`scalebox.py`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/scalebox.py)、[`build_rl_dataset.py`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/build_rl_dataset.py)、[`download_eagle.py`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/download_eagle.py)、[`run_code_rl_demo.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/run_code_rl_demo.sh)、[`run_toolcall_sft_demo.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/run_toolcall_sft_demo.sh)、[`run_multi_turn_livecodebench_eval.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/run_multi_turn_livecodebench_eval.sh)、[`eagle3_rl_run.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/eagle3_rl_run.sh)、[`suffix_rl_run.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/suffix_rl_run.sh)、[`no_spec_rl_run.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/no_spec_rl_run.sh)、[`process_all_the_logs_sprl.py`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/agent_rl/qwen3_code_toolcall/process_all_the_logs_sprl.py)
- [verl](https://github.com/volcengine/verl) — 上游 RL 框架仓（commit `c651b7b4207e408875f132c4226969ef3495d408`）
- [vllm-ascend](https://github.com/vllm-project/vllm-ascend) — 上游 rollout 推理引擎仓（SD 扩展 v0.13.0、commit `6281c1207a7a499e9f23a42b3a1e7027469f2b10`）
- [scalebox](https://gitcode.com/icip-cas/ScaleBox) — ScaleBox 代码执行沙盒仓（`gitcode.com/icip-cas/ScaleBox`）

## Links

- [scalebox](../../concepts/frameworks/scalebox.md)（代码执行沙盒后端：工具调用 `tool_config/scalebox_tool_config.yaml` + 奖励函数 `scalebox.py`，融合镜像单节点同跑 verl 训练与沙盒服务）
- [agent-rl-loop](../../concepts/techniques/agent_rl_loop.md)（多轮工具调用循环机制：`0002-enable-tool-agent-loop.patch` 承载的 agent-loop，写码→执行→观测→续推）
- [verl](../../concepts/frameworks/verl.md)（RL 框架本体：actor/rollout/ref/reward 角色、训推共卡、commit c651b7b 锁定）
- [vllm-ascend](../../concepts/frameworks/vllm_ascend.md)（rollout 推理后端：SD 扩展用 v0.13.0 的异步实现与更稳定投机解码支持）
- [sam-speculative](../../concepts/techniques/sam_speculative.md)（投机方法对照：无模型后缀自动机检索路线，与 EAGLE3 草稿模型路线互补，规避草稿分布漂移）
- [qwen3-rl](qwen3_rl.md)（同模型族 Qwen3 的纯 RL 实践，SAM 投机在其上 +10%）
- [qwen2-code-rl-scalebox](qwen2_code_rl_scalebox.md)（同域并列:ScaleBox Code RL）
- [qwen-dense](../../../inference/concepts/models/qwen_dense.md)（跨域：基座 Qwen3-1.7B 属 Qwen Dense（非 MoE）模型族，结构/家族对照）