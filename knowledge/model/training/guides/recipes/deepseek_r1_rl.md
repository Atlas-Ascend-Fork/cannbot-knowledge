---
type: Guide
title: DeepSeek-R1 veRL + MindSpeed + vLLM-Ascend 全共卡 GRPO RL 训练
description: DeepSeek-R1（671B）强化学习后训练在 Atlas A3 SuperPoD 超节点 128 卡集群跑通。整套系统以 verl 为前端（单控制器调度 RL 控制流）、mindspeed + Megatron-LM 为训练后端（actor / ref 的 update 与 log_prob）、vllm-ascend 为 rollout 推理后端（采样生成），用 grpo-dapo 算法在 ActorRolloutRef 三模型全共卡、分时复用部署下完成训练，加载真实权重时系统吞吐达 120+ TPS/卡（初始 112，长稳后 120+，单点详测 123.16），随机权重峰值场景达 250.2 TPS/卡。
tags:
- task.implementation
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# DeepSeek-R1 veRL + MindSpeed + vLLM-Ascend 全共卡 GRPO RL 训练

## Summary

DeepSeek-R1（671B）强化学习后训练在 **Atlas A3 SuperPoD 超节点 128 卡集群**跑通。整套系统以 [verl](../../concepts/frameworks/verl.md) 为前端（单控制器调度 RL 控制流）、[mindspeed](../../concepts/frameworks/mindspeed.md) + Megatron-LM 为训练后端（actor / ref 的 update 与 log_prob）、[vllm-ascend](../../concepts/frameworks/vllm_ascend.md) 为 rollout 推理后端（采样生成），用 [grpo-dapo](../../concepts/techniques/grpo_dapo.md) 算法在 ActorRolloutRef **三模型全共卡、分时复用**部署下完成训练，加载真实权重时**系统吞吐达 120+ TPS/卡**（初始 112，长稳后 120+，单点详测 123.16），随机权重峰值场景达 250.2 TPS/卡。

**R1 专属**的两块优化在本页展开：[「训练任务下发慢」根因诊断](#训练任务下发慢的根因诊断)与 GRPO on-policy 的 [**old_log_prob 免计算**](#old_log_prob-免计算grpo-on-policy)。通用机制——GRPO 算法、reshard/offload/D2D 训推切换、rollout 推理算子优化——见各自概念页。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image6.png" width="55%"></p>
<p align="center"><sub>图：generate_sequences（gen）与训练侧任务（ref/update）的输入数据量对比——gen 输入仅 prompt、DP=总卡数、batch 未被 n_sample 放大，故下发数据量远小于训练侧（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·性能问题分析结论）</sub></p>

## 训练配置

recipe（[`llm_rl/deepseek/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/README.md)）给出的样例规格：基础模型加载 **DeepSeek-V3-671B** 真实权重（去掉量化与 MTP 的 config），数据集 deepscaler，Prefill/Decode 长度 1K/3K。

| 项 | 取值 |
|---|---|
| 基础模型 | DeepSeek-V3-671B（61 层，加载为 R1 的初始权重） |
| 机器型号 | Atlas A3 128 卡（= 256 die，每卡 2 die） |
| GBS / n_samples / step | 512 / 16 / 2 |
| max_prompt_length / max_response_length | 1024 / 3072 |
| 数据集 | deepscaler（数学，规则/答案匹配 reward） |
| RL 算法 | GRPO（on-policy） |
| 端到端 TPS | 120 TPS/卡（初始 112，训练 ~13 步后达 120+） |

各角色的并行策略（全共卡分时复用同一组 256 die）：

| 角色 | 框架 | 真实权重并行 | 随机权重并行 |
|------|------|-------------|-------------|
| rollout（generate） | vLLM + vLLM-Ascend | 256die · DP64TP2EP128（2 个 DP 实例） | 256die · DP128TP2EP256 |
| actor（update） | Megatron + MindSpeed | 256die · TP4EP8PP8 | 256die · TP4EP8PP8 |
| ref（log_prob） | Megatron + MindSpeed | 256die · TP4EP8PP8 | 256die · TP4EP8PP8 |

> actor 与 ref 并行策略完全一致、DP rank 排布相同——这是 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md) 中「update 复用 ref 缓存无需通信」的前提。训练态↔推理态并行不同（TP4EP8PP8 ↔ DP·TP2·EP128/256）正是 reshard 的来由。

## 拉起的两个承重点

数据/权重下载、`json_to_parquet.py` 转换、依赖 checkout 与版本矩阵等复现操作见 recipe README（Evidence）。两处影响并行/精度正确性的承重约束在此展开。

**patch 注入点**：本样例只发放 patch 代码，需手动在 `verl/workers/megatron_workers.py: line21` 处插入 `from verl_patches import prelude_patch` 才能使能改动。

**权重离线切分须对齐训练态并行**：`convert_ckpt_deepseek3.py` 把 BF16 权重按训练侧 `TP4PP8EP8`（`--num-layer-list 7,7,8,8,8,8,8,7`、`--first-k-dense-replace 3`、`--num-layers 61`）离线切分，并开 `--moe-tp-extend-ep`——专家维不走 TP 切而扩到 EP，与训推切换里专家 AlltoAllV 定向路由的 reshard 约束一致，否则训练态↔推理态的 reshard 无法成立（机制见 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)）。

## 四向优化总览

对 veRL 从四个方面优化（总览图见 [verl](../../concepts/frameworks/verl.md)）：

| 方向 | 机制 | 详见 |
|------|------|-------------|
| 模型间调度 | 训练任务下发慢的根因诊断 + D2D TensorCache 数据直传 | 诊断见下文；D2D 见 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md) |
| 训推切换 | reshard（专家 AlltoAllV 定向路由 / PP 域 Broadcast）+ offload | [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md) |
| 训练 | 复用 MindSpeed 内存/通信/计算优化 + old_log_prob 免计算 | [mindspeed](../../concepts/frameworks/mindspeed.md) / 下文 old_log_prob 免计算 |
| 推理（rollout） | TorchAir 整图下沉 / MoE·MLA 多流 / 零冗余 TP 转 EP / KVCache NZ / 大 EP 冗余算子消除 / 调度 bound Gloo→HCCL | [vllm-ascend](../../concepts/frameworks/vllm_ascend.md) |

## 训练任务下发慢的根因诊断

调测中发现 verl 训练侧（`compute_ref_log_prob`、`update_actor`）性能不及预期：profiling 显示**一些卡的第一个通信耗时极长**——ref 首个通信 50s+、update 首个通信 90s+。对每张卡的三个阶段做时间打点后定位现象：`generate_sequences`/`compute_ref_log_prob` 在各卡的**结束时间一致**，但 `compute_ref_log_prob`→`update_actor` 的**启动时间不一致**，0 卡最早、最后一张卡最晚、各卡串行启动，且训练侧最大启动时差非常接近 profiling 里那段超长通信。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image4.png" width="55%"></p>
<p align="center"><sub>图：256Die 训练中 0 卡与 255 卡的 update 启动时差可达 96 秒——串行任务下发导致 worker 启动时差，被 profiling 误记为「首个超长通信」（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·训练侧任务启动时差过大现象）</sub></p>

根因在 verl 单控制器的任务下发逻辑。`verl/single_controller/ray/base.py` 的 `func_generator` 把一次任务接口拆为三步：`dispatch_fn`（主进程按 DP size 切 batch）→ `execute_fn`（逐 worker 下发，对应 `execute_all_async`）→ `collect_fn`（收集拼接）。split/concat 实测很快，**瓶颈在 `execute_all_async` 串行给每个 worker 下发任务**：

> ray 给一个 worker 下发任务都包括至少三步：输入数据序列化、数据传输、输出数据序列化。因此，当任务的输入 tensor 数据量很大时，大量 worker 的任务下发耗时会不断累积，从而造成训练性能瓶颈。

为何 **gen 任务下发不慢（1 秒内）而训练侧慢**——侧面印证「下发耗时与数据量正相关」：gen 的 dispatch DP 等于总卡数（如 256，远大于训练侧 DP=8）、GRPO 中 gen 输入 batch 未被 `n_sample` 倍数放大、gen 输入仅 prompt 而训练侧输入含 prompt+response。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image8.png" width="62%"></p>
<p align="center"><sub>图：verl 框架任务下发的性能瓶颈时序——主进程串行向各 worker 序列化+传输大 tensor，后启动的 worker 长时间空等（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·verl 控制器逻辑总结）</sub></p>

这一诊断**直接催生** D2D TensorCache 方案：把训练侧任务输入这类「device 产、又要回 device」的大 tensor 在 device 侧原地缓存 / AlltoAllV 直传，消除 host 往返与串行下发时差（机制见 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)）。实测 `compute_ref_log_prob` 启动最大时差 ~57s→<1s、`update_actor` ~73s→~5s，端到端吞吐 +14.4%。本实践也试过把 ray 下发改多线程并行，但 ref 下发仅从 66s 降到 24s、且部分 worker tensor 序列化出错，不满足需要——故走 D2D 路线。

## old_log_prob 免计算（GRPO on-policy）

GRPO 是 on-policy 算法：每步 update 用的就是产出这批 rollout 的同一份参数，因此 `old_log_prob` 的计算结果与 `update_actor` 前向所得 `log_prob` **数值相同**。据此为 verl 补充 old_log_prob 免计算特性——直接用 `log_prob.detach()` 替代 old_log_prob，省去一次训练模型前向：

```shell
# 置 False 即启用 old_log_prob 免计算（on-policy 专用）
config.actor_rollout_ref.actor.recompute_old_log_prob = False
```

效果直接体现在性能表的 `old_log_prob (s)` 列**恒为 0**（见下文 Benchmark 两张表）。算法侧重要性比 $\rho\equiv1$ 的推导、目标函数图等见 [grpo-dapo](../../concepts/techniques/grpo_dapo.md)。

## 复用 MindSpeed 训练优化

训练侧（actor/ref 的 Megatron 计算）经 [mindspeed](../../concepts/frameworks/mindspeed.md) 的 repatch 直接复用其内存/通信/计算优化，在 verl 启动脚本里以 `override_transformer_config` 打开，节选：

```shell
+actor_rollout_ref.actor.megatron.override_transformer_config.use_flash_attn=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.moe_token_dispatcher_type='alltoall' \
+actor_rollout_ref.actor.megatron.override_transformer_config.moe_grouped_gemm=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.use_fused_rotary_pos_emb=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.use_fused_swiglu=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.swap_optimizer=True
```

其中 `swap_optimizer=True` 即 Ascend Swap Optimizer（优化器状态 Host 卸载，见 [swap-optimizer](../../concepts/techniques/swap_optimizer.md)），其余为融合算子 / AlltoAll dispatcher / GroupedGEMM 等亲和特性。

## Benchmark

两个 128 卡 A3（256 die）场景，系统吞吐 = 数据生成 + 训练 + 训推切换合算。

**加载真实权重**（DeepSeek-V3 真实权重，deepscaler，限最大推理长度 3K，部分优化）—— **系统吞吐 123.16 TPS/卡**（推理 271.05、训练 331.6）：

| 数据生成 | rollout | old_log_prob | ref prefill | reward | adv | 训练(update) | reshard | offload 等 | 总耗时 | 系统吞吐 |
|---------|---------|-------------|-------------|--------|-----|--------------|---------|-----------|--------|---------|
| 523.38s | 373.65s | **0** | 144.5s | 5.0s | 0.21s | 319.3s | 11.5s | 5.5s | 859.68s | **123.16 TPS/卡** |

> 上为训练侧重计算 4 层的性能；为长稳训练改重计算 8 层，训练约 13 步后吞吐可从初始 **112 TPS/卡提升至 120+ TPS/卡**。

**加载随机权重**（gsm8k，固定推 3K，强制专家负载均衡 + 全部性能优化，峰值理想态）—— **系统吞吐 250.2 TPS/卡**（推理 686.8、训练 607.2）：

| 数据生成 | rollout | old_log_prob | ref prefill | reward | adv | 训练(update) | reshard | offload 等 | 总耗时 | 系统吞吐 |
|---------|---------|-------------|-------------|--------|-----|--------------|---------|-----------|--------|---------|
| 436.86s | 318.27s | **0** | 104.7s | 13.7s | 0.188s | 328.8s | 11.18s | 24.45s | 796.8s | **250.2 TPS/卡** |

读表要点：rollout（数据生成）是大头（真实权重 1K 推 3K 下约占总耗时一半，长序列场景可达 80%+），故推理优化是重中之重（rollout 单点经 vLLM-Ascend 调度 bound 优化 519→618 token/p/s，整体推理吞吐达 610+ token/p/s）；`old_log_prob` 因免计算恒为 0；`adv` 因 GRPO 去 critic 仅 ~0.2s；训推切换（reshard+offload≈17s / 35.63s）占比不高但与 rollout/update 强耦合。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/deepseek_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md)（§1.1 框架表；§1.2 全共卡 / 选型 vLLM-Ascend / 不做 PD 分离；§1.3 四向优化总览；§1.4 真实权重 123.16 / 随机权重 250.2 TPS 详细性能表 + 并行策略 + 112→120+ 长稳说明；§3.1 训练任务下发慢根因诊断（首通信 50s+/90s+、256Die 启动时差 96s、`execute_all_async` 串行、gen vs 训练侧数据量）；§5.1 复用 MindSpeed 优化脚本；§5.2 old_log_prob 免计算）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/deepseek/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/README.md)（DeepSeek-V3-671B / Atlas A3 128 卡 / GBS512 / n_samples16 / deepscaler / 120 TPS recipe；`from verl_patches import prelude_patch` 注入；`convert_ckpt_deepseek3.py` 权重切分 `--moe-tp-extend-ep` TP4PP8EP8；`json_to_parquet.py` 数据；`train_deepseekv3_256die_{random_init,true_weight}.sh` 拉起；依赖框架版本/checkout 与 CANN 8.2.RC1 / torch_npu 7.1.0）

## Links

- [verl](../../concepts/frameworks/verl.md)（RL 前端：单控制器调度 rollout/ref/update 三阶段，四向优化总览枢纽）
- [mindspeed](../../concepts/frameworks/mindspeed.md)（训练后端：经 MegatronWorker repatch 使能 Megatron-LM + MindSpeed 亲和优化，本页 §5.1 复用入口）
- [vllm-ascend](../../concepts/frameworks/vllm_ascend.md)（rollout 推理后端：图模式 / 大 EP / 多流 / KVCache NZ，rollout 519→618 token/p/s）
- [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（RL 算法：组内相对 advantage、去 critic、on-policy 下 $\rho\equiv1$）
- [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)（训推切换：本页 §3.1 诊断催生的 D2D TensorCache + reshard + offload）
- [swap-optimizer](../../concepts/techniques/swap_optimizer.md)（§5.1 `swap_optimizer=True` 复用的优化器状态 Host 卸载）
- [deepseek-r1](../../../inference/concepts/models/deepseek_r1.md)（跨域：本 RL 实践训练/部署的目标模型，加载 DeepSeek-V3-671B 权重，R1 推理部署）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：SuperPoD 超节点 128 卡训练平台，HCCS 高带宽是训推切换与多流掩盖的硬件前提）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — DeepSeek-R1 RL 训练优化实践（veRL + A3 集群）
- [qwen2.5-rl](qwen2_5_rl.md)（同域并列 RL：Qwen2.5 入门(单卡 A2)）
- [qwen3-rl](qwen3_rl.md)（同域并列 RL：Qwen3 235B/32B 长序列）