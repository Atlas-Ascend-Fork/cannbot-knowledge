---
type: Guide
title: Qwen3 长序列 RL 训练实践（235B-A22B 2K 推 32K + 32B SAM 投机，veRL/MindSpeed/vLLM-Ascend，GRPO/DAPO）
description: Qwen3-235B-A22B（MoE，22B 激活）：在 64 卡 A3（128die） 上跑 GRPO/DAPO，GRPO Prompt/Response 最大2K/32K、DAPO最大2K/34K 的长序列场景，加载真实权重的 GRPO 系统吞吐达 122 TPS/卡（recipe README 标称 120 TPS/卡）。技术栈为 veRL 前端 + Megatron+MindSpeed 训练引擎 + vLLM+vLLM-Ascend 推理引擎，全共卡部署。 Qwen3-32B（dense）：在 16 卡 A3（32die） 上跑 GRPO/DAPO 2K 推 34K，使能 SAM 无模型投机解码，端到端约 +10%、叠加 npugraph_ex 后两者叠加后相对均关闭基线，首步推理耗时下降约29%~33%。
tags:
- task.implementation
- topic.speculative_decoding
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0005-verl-feature-moe_alltoallv.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0016-verl-bugfix-hot_swap_expandable_segments.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/sam_decoding.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/README.md
  role: implementation
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a3
---

# Qwen3 长序列 RL 训练实践（235B-A22B 2K 推 32K + 32B SAM 投机）

## Summary

Qwen3 系列长序列强化学习（RL）训练在昇腾 Atlas A3 上有两条主线（`llm_rl/qwen3` recipe）：

- **Qwen3-235B-A22B**（MoE，22B 激活）：在 **64 卡 A3（128die）** 上跑 GRPO/DAPO，**GRPO Prompt/Response 最大2K/32K、DAPO最大2K/34K** 的长序列场景，加载真实权重的 GRPO 系统吞吐达 **122 TPS/卡**（recipe README 标称 120 TPS/卡）。技术栈为 veRL 前端 + Megatron+MindSpeed 训练引擎 + vLLM+vLLM-Ascend 推理引擎，全共卡部署。
- **Qwen3-32B**（dense）：在 **16 卡 A3（32die）** 上跑 GRPO/DAPO 2K 推 34K，使能 **SAM 无模型投机解码**，端到端约 **+10%**、叠加 npugraph_ex 后两者叠加后相对均关闭基线，首步推理耗时下降约29%~33%。

RL 系统底座沿用 [deepseek-r1-rl](deepseek_r1_rl.md)（同样的 veRL 全共卡 + 训推切换 + 零冗余 reshard），新增长序列特有问题的优化：**长尾序列负载不均**、**HBM 随序列线性增长的显存瓶颈**。算法、框架、训推切换、投机、负载均衡等通用机制各有概念页（见下方链接）；Qwen3-235B 专属的推理内存部署/计算调度与训练 HDP 混合数据并行见后文专节。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/qwen3_figures/image1.png" width="72%">
<sub>图：Qwen3-235B RL 长序列推理/训练优化总览——推理侧（切分策略/图模式/FIA 负载均衡/Rollout Rebalance/EPLB/Expert Parallelism Load Balance）与训练侧（MindSpeed 内存与性能优化 + Hybrid Data Parallelism）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 32K 长序列 RL 训练优化文档·§1.2 优化实践总览</a>）</sub>

## 训练配置

| 模型 | 阶段/算法 | 卡数 | RL 框架 | 推理引擎 | 训练引擎 | 数据集 | rollout 部署 | actor/ref 部署 | GBS | n |
|------|----------|------|---------|----------|----------|--------|-------------|---------------|-----|---|
| Qwen3-235B-A22B | GRPO（2K 推 32K） | 64 A3（128die） | veRL | vLLM+vLLM-Ascend | Megatron+MindSpeed | deepscaler | DP32TP4EP128 | TP4PP4CP4EP32 | 512 | 16 |
| Qwen3-235B-A22B | DAPO（2K 推 34K） | 64 A3（128die） | veRL | vLLM+vLLM-Ascend | Megatron+MindSpeed | dapo-math-17k | DP32TP4EP128 | TP4PP4CP4EP32 | 128 | 16 |
| Qwen3-32B | GRPO/DAPO（2K 推 34K，+SAM） | 16 A3（32die） | veRL | vLLM+vLLM-Ascend | Megatron+MindSpeed | deepscaler / dapo-math-17k | TP8 | — | 128 | 16 |

- **算法**：[grpo-dapo](../../concepts/techniques/grpo_dapo.md)（GRPO on-policy + DAPO 的 clip-higher / token-level IS / 动态样本过滤）。DAPO 配置：`clip_low=0.2`、`clip_higher=0.28`、`rollout_is_threshold=2.0`、`use_kl_loss=False`、`loss_agg_mode="token-mean"`、`algorithm.filter_groups.enable=True`（去除 group 内 reward 全 0 或全 1 的样本）（doc §1.3.2）。
- **框架**：veRL 前端（[verl](../../concepts/frameworks/verl.md)）+ MindSpeed 训练引擎（[mindspeed](../../concepts/frameworks/mindspeed.md)）+ vLLM-Ascend 推理引擎（[vllm-ascend](../../concepts/frameworks/vllm_ascend.md)）。本实践对 veRL 的适配与前序工作一致：原生支持 MindSpeed 训练引擎（修复了 `moe_alltoall_overlap` 下专家权重加载异常）、推理 sleep 用前序的 `onload/offload` 替代、GRPO 下 old_log_prob 免计算（doc §1.2）。
- **训推切换**：[train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)（reshard / offload / D2D，与 DeepSeek-R1 通用，含基于 AlltoAllV 的零冗余专家 reshard，支撑 `moe_alltoall_overlap_comm` 下的权重命名变化）。
- **平台**：Atlas A3 系列（[atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)）；镜像 `cann:8.5.0-a3-openeuler24.03-py3.11`，驱动 Ascend HDK 25.3.X。235B 最少 64 卡、32B 最少 16 卡（README 硬件要求）。

### 权重切分（零冗余 reshard）

235B 权重离线 HF→mcore 切分时设置 `USE_ALLTOALL_OVERLAP=1` 以生成匹配 moe_alltoall_overlap_comm 的专家权重布局；运行时是否走 AlltoAllV 零冗余专家 reshard 另由 `ALL_TO_ALL_RESHARD=1` 选择。两者由 qwen3_235b_env.sh 分别设置，0005补丁按 ALL_TO_ALL_RESHARD 选通信分支；离线布局对齐不触发运行时通信，是235B训推切换的两个不同条件，详见 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)。

## Benchmark（§1.3 详细性能）

**GRPO（235B，64 卡，2K 推 32K，真实权重，deepscaler）**：单步数据生成 5351.17s（其中 rollout 4065.71s、ref prefill 1262.27s、reward 21.54s、adv 1.65s），训练update 2353.23s；来源另记总耗时7780.36s（前两项合计7704.40s，未提供差额计时，不能写直接相加等式）；推理吞吐 233.56、训练吞吐 403.5、**系统吞吐 122.05 TPS/卡**（doc §1.3.1）。

**DAPO（235B，64 卡，2K 推 34K，真实权重，dapo-math-17k）**：因回复变长调 GBS=128；打开样本过滤后首个 step 做 2 个 batch 推理（单轮 3262.39s，总推理 6619.78s），update 797.93s，单步总耗时 7833.16s，推理吞吐 100.56、系统吞吐 41.88 TPS/卡（doc §1.3.2）。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/qwen3_figures/image4.png" width="60%">
<sub>图：Qwen3-235B 推理优化历程（系统吞吐）——base 59 → prompt balance & 多档位编图 78 → 数据及模型并行策略优化 97 → 使能 FIA 算子负载均衡 109 → HostBound 优化 118 → RolloutRebalance 优化 122 TPS（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 32K 长序列 RL 训练优化文档·§2 推理优化</a>）</sub>

**Qwen3-32B SAM（16 卡，2K 推 34K）**：首步推理时间 GRPO 2444→开 SAM 2106（13%）→ 再开 npugraph_ex 1621（33%）；DAPO 4562→4109（10%）→3261（29%）（README）。SAM 单独收益另见 sam_decoding 文档实测：32B 32die DAPO相对加速收益8.13%（4730.86→4374.99s，耗时下降7.52%）、235B 128die DAPO相对加速10.60%（15441.45→13960.98s，耗时下降9.59%），长尾阶段达非投机 **1.35X**（[sam-speculative](../../concepts/techniques/sam_speculative.md)）。

## 关键优化

### 算法：GRPO / DAPO

GRPO（组内相对优势 + on-policy）与 DAPO（在 GRPO 上加 clip-higher、token-level 重要性采样、动态样本过滤）的算法机制见 [grpo-dapo](../../concepts/techniques/grpo_dapo.md)。本实践在 on-policy GRPO 下复用 `log_prob.detach()` 免算 old_log_prob（`recompute_old_log_prob` patch，开启时校验 `ppo_epochs=1`），与 [deepseek-r1-rl](deepseek_r1_rl.md) 一致。

### 框架适配与训推切换

veRL × MindSpeed × vLLM-Ascend 的角色/数据流、repatch、additional_config 等见三张框架页；本实践相对 DeepSeek-R1 的两点新适配：(1) veRL 开启 `moe_alltoall_overlap` 后专家权重加载异常的修复（doc §1.2）；(2) 旧 GE 优化实践当时因 torch_npu 虚拟内存动态切换限制沿用 onload/offload；当前固定 CANN8.5.0 recipe 已包含0016-verl-bugfix-hot_swap_expandable_segments.patch，为 NPU allocator 动态切换 expandable_segments、支持 sleep mode 热切换，不能把旧限制推广到当前启动链路（见 [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)）。reshard 的零冗余 AlltoAllV 专家路由是 235B 训推切换的关键（专家层参数占比高、`moe_alltoall_overlap_comm` 会改 GMM 权重命名）。

### 投机解码：SAM（Qwen3-32B 为主，235B 亦验证）

SAM 是基于**动态后缀自动机**的**无模型（draft-model-free）投机解码**，无需辅助模型、不担心 RL 权重更新导致分布漂移、训推共卡下即插即用，对数学/代码/Agent 这类结构化重复的 RL 数据天然亲和。原理、接受率、拒绝采样向量化加速、自适应 batch 开关见 [sam-speculative](../../concepts/techniques/sam_speculative.md)。本 recipe 通过 patch（`0002-vllm-feature-enable_sam_decoding`、`sam_proposer.py`、`bs_threshold_for_spec_decode`）使能；32B 推荐自适应阈值 8、投机 token 数 3，客户 128die 场景阈值 4、投机数 4。

### Rollout 负载均衡（长序列长尾）

长序列 RL 的核心新问题是 response 长尾分布导致的「木桶效应」。本实践用两层互补机制缓解，各机制详见对应技术页：

- **推理时动态重均衡** [rollout-rebalance](../../concepts/techniques/rollout_rebalance.md)：vLLM 引擎内每个推理 Step 前做「负载均衡检查 + Rebalance 调度」，结合多档位编图让全局 DP 组尽快切到更低 BS 档位；128die deepscaler 实测多档位编图单独相对 base 提升 30% → 叠加 Rebalance 共 67%（doc §2.3.1 实验2）。Rebalance「额外 +20%」是另一组实验的数字——DeepSeekV3 / OpenR1-Math-220K / 256Die（多档位单独 56% → 叠加 Rebalance 共 64%，doc §2.3.1 实验1），勿与 deepscaler 67% 实验交叉拼接。
- **历史长度重采样** [length-aware-resampler](../../concepts/techniques/length_aware_resampler.md)：用上一轮 rollout 的 response 长度统计在下一 epoch 前重排 prompt，减少同一 generation batch 内「极长 + 极短」混排（README 可选特性，含 `length_bucket_sampler` 与 `VLLM_ROLLOUT_EARLY_STOP_*` 长尾保护）。

此外 doc §2.3.3 给出与 Rebalance 互补的 **DataBalance**（输入数据重排序）：veRL 默认把 n 份采样作相邻排布，导致长/短回复 prompt 聚到不同 DP 域、负载严重不均；本实践改为**按采样数 n 复制后作间隔排布**，把各 prompt 均匀分散到不同 DP 域，训练前再按原顺序还原。BS128 下端到端时延 -25%；叠加 DataBalance 后还可把 BS 从 128→192→256 进一步提吞吐（92→132→160→186 tokens/s/卡，doc §2.3.3 表）。

## Qwen3-235B 推理优化（doc §2）

### 内存占用分析与部署策略

235B-A22B 在 TP4DP32EP128 下权重仅占 **7.09GB**（Embedding/LmHead 0.58 + QKV 1.65 + O 1.47 + MoE 3.30 + Gate 0.09）。KV Cache 按激活与权重之外的剩余内存按比例分配。TP4 下单 BS 的 32K KV Cache 占 **1.47GB**，单卡 BS 上限保守估算仅 30~40。但实测 response 长尾分布——多数序列早退释放 KVCache，故按最大长度严格限 `max_num_seqs` 会严重损初期吞吐。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/qwen3_figures/image7.png" width="62%">
<sub>图：左为 DeepScalar 单次推理 256 条回复的长度分布（仅少数长尾达最大长度），右为「各长度下剩余序列数」实测蓝线始终位于「给定 KVCache 容量下序列长度-最大序列数」红色反比例曲线之下，故 max_num_seqs=256 仍不触发 OOM（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 32K 长序列 RL 训练优化文档·§2.1 内存占用分析与部署策略选择</a>）</sub>

据此最终配置：**TP4DP32EP128**（大 TP 降单卡权重占比、Decode 访存 bound 下缓解瓶颈并留更多 KV Cache 空间）+ `max_num_seqs=256` + `max_num_batched_tokens=32768` + `gpu_memory_utilization=0.87`（配合 Chunk-MoE 特性降 prefill 峰值内存，doc §2.1）。

### 计算与调度优化（doc §2.2）

- **切分策略** §2.2.1：长尾低 BS 下 Matmul 访存 bound（实测随 request 减少、shape 变小但耗时不等比下降）。非 MoE 部分用更大 TP（TP4DP32 vs TP1DP128）让每卡只加载小权重、提高计算占比——TP1 切分 Matmul 严重访存 bound，TP4DP32 整网更优、更不易 KVCache 换出。
- **图模式路径** §2.2.2：veRL+vLLM 有 5 种图模式路径，Qwen3-235B 长序列优化文档对比 Full_decode_only ACLGraph 与 TorchAir GE，选 **GE 图模式**——GE 可配更大 `max_num_seqs` 并开多档位编图，总体推理耗时最优；且 Full Graph 要求 kernel 地址固定、必须用 vLLM 原生 sleep mode（依赖关闭虚拟内存，与训练侧冲突易 OOM），大集群 RL 训练下无法正常运行。版本注记：优化文档（来源工作项）采用 TorchAir GE；同一来源版本的 recipe README 与启动脚本采用 **npugraph_ex**。README 注明部分 GE 相关 patch 已不适用，完整 GE 实现见 v0.1.0；235B 128die 启动脚本使用 `CUDAGRAPH_SIZES` + `cudagraph_capture_sizes`，无 TorchAir GE 配置。因此，GE 实验结果与 npugraph_ex 启动配置不能作为同一图模式使用。
- **FIA 算子负载均衡** §2.2.3：长序列 decode 各 batch cache 长度不一，IFA（IncreFlashAttention）多核负载不均（部分核空闲）。改用 **FIA（FusedInferAttention）**，基于核数循环模拟求最优核数 + 贪心块分配均衡各核开销；该优化已集成 CANN 8.3.RC1。系统吞吐 105→117（**+11.4%**）。算法/公式见下方专节。
- **Decode HostBound** §2.2.4：Decode 通信拖尾根因是 Host 侧 GC 与内存操作引入空泡导致下发延迟。**Decode step 临时禁用 GC + taskset 绑核**（Ray 拉起时 device id 都被设 0，`CPU_AFFINITY_CONF` 失效，改用 taskset）：forward 137.64→124.66ms（-9.4%）、总推理 4851.98→4192.09s（-13.6%）。

#### FIA 多核负载均衡算法/公式（doc §2.2.3）

优化前 IFA 逻辑：decode 场景下各 batch 的 KV cache `sequence_length` 不一（示例 GQA：`batch_size=4`、KV 头 4、Query 头 64，其中两组已推到 28672、另两组已推理完成），按计算性能要求做数据切块后，由于未做负载均衡，最大可调动 4 核时仅 2 核活跃、其余 2 核已退出——有些核仍有大量计算、另一些空闲，负载不均、算力浪费。

FIA（FusedInferAttention）当前支持更优的负载均衡逻辑，本实践采用**基于核数的循环模拟**方案。关键问题：(1) 分块——不同大小负载有不同开销（权重），不能统一视为 1；(2) 分核——所有核默认全启动、未考虑调度与同步开销，可能性能劣化。优化两方向：**确定最优核数**（增核降单核负载缩短慢核时间，但过多核引入调度/同步开销反使 FA 总耗时上升）与**优化块分配策略**（块合理分配到每核、确保各核总计算开销基本均衡）。

**1. 计算最优核数**（`TotalBlocks`=分块总数，`TotalCores`=总核数）：

- 当 `TotalBlocks >= (TotalCores-2)·TotalCores`：可保证大任务收益稳定，直接启用全部核心满负荷计算。例如 `TotalBlocks=8`、`TotalCores=4`，则直接用 4 核。
- 当 `TotalBlocks < (TotalCores-2)·TotalCores`：需做核数评估（例 `TotalCores=8`、`TotalBlocks=8`）。
  1. **核数范围确定** `MinCore ~ MaxCore`（实验拟合得的需分块的最大最小核数公式）：

     $$MinCore = \min\left(\sqrt{TotalBlocks + \tfrac{1}{4}} + \tfrac{1}{2},\ TotalCores\right)$$

     $$MaxCore = \min\left(TotalBlocks,\ TotalCores\right)$$

     按上例 `TotalBlocks=8` 计算，得需遍历的核数范围为 [3, 8]。
  2. **确定最优分核数**：最小化 FA 总时间 $TotalTime$，其中 $CoreCost$ 是核计算开销，$CoreUsePlan$ 是核调度成本（只和分核数 $k$ 成正比，记作 $\rho\times k$，$\rho$ 为常数）：

     $$TotalTime = \max\left(CoreCost_{0}\ldots CoreCost_{k}\right) + CoreUsePlan(\rho \times k)$$

     按硬件约束对 attention score 矩阵二维切分得 N 个 Block 分块，基于模拟公式算每块实际开销，按次序记为 $LoadCost_{j}$。循环遍历核数范围，对每个 $k$ 核方案用**贪心算法**算总开销：

     - 对每核 $i \in [0, k-1]$，算该核开销上限 $CostLimit$（$UndistributedLoad$=剩余未分配总开销，$k-i$=剩余未分配核数）：

       $$CostLimit = \frac{UndistributedLoad}{k - i}$$

     - 把 block 依次加入当前核，当前核累计总开销 $CoreCost_{i}$ 满足下式时：

       $$CoreCost_{i} + LoadCost_{j} \times 0.5 < CostLimit$$

       则把当前 $Block_{j}$ 分给当前 $Core_{i}$ 并更新累计开销，否则给下一个核：

       $$Core_{i} = CoreCost_{i} + LoadCost_{j}$$

     - 记录当前分核方案的最慢核计算开销：

       $$CurMaxCost = \max\left(CoreCost_{0}\ldots CoreCost_{k}\right)$$

     - 最后算出所有分核方案的 $TotalTime$，取最小开销成本即得最优分核数。

**2. 应用最优分核数、分配最佳分块数**：将块按上述贪心规则分配到各核。该优化已集成 CANN 8.3.RC1，上层代码调用对应 FIA 算子（`npu_fused_infer_attention_score`）即可适配。

测试结果（同等配置，TP4 PP4 CP4 EP32 / GBS512 / 采样 16 / 64 卡 / deepscaler / 2K 推 32K / 开多档位编图）：启用负载均衡优化后系统吞吐 **105→117（+11.4%）**，`generate_sequence/s` 4919→4153（doc §2.2.3 优化效果表）。

### EPLB（链 [eplb](../../concepts/techniques/eplb.md)）

本实践适配 EPLB（`VLLM_ENABLE_EPLB`）：Qwen3-30B/235B 真实权重实测**无明显收益**（各卡负载本身无明显不均），人工极端负载实验观测耗时下降17.78%；三组观测未建立中等不均负载的收益阈值。EPLB 原理、分层/全局双调度与三组实验详见 [eplb](../../concepts/techniques/eplb.md)。

## Qwen3-235B 训练优化（doc §3）

### 内存分析与切分（§3.1）

训练静态内存（权重+梯度+优化器状态）相对固定，动态内存（激活）正比于序列长度，长序列下成为瓶颈。本实践用 MindSpeed **swap optimizer** 卸载绝大部分优化器静态内存（见 [swap-optimizer](../../concepts/techniques/swap_optimizer.md)），TP4PP4EP32 下静态内存仅留 BF16 权重+梯度约 **12.51GB**（叠加推理后残留 8~9GB，训练态单卡约 21.5GB）。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/qwen3_figures/image28.png" width="68%">
<sub>图：Qwen3-235B 单层动态激活内存来源——ATTN（QKVO/RingAttention）与 MoE（AllToAll Dispatch/GroupedMatMul/SwiGLU/Combine）；MoE 激活含 SMoE 因子（S/Tp·TopK ~ S/Tp·E），负载越不均膨胀越大（8~128 倍间波动）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 32K 长序列 RL 训练优化文档·§3.1 内存占用分析和模型切分策略选择</a>）</sub>

动态内存上不开 CP 时首个 PP rank 仅 ATTN 激活就 55.07GB（32K 下必须开 CP）；MoE 层重计算 `moe_zero_memory`（前置依赖 `moe_alltoall_overlap_comm`，后者改 GMM 权重命名、靠前序零冗余 reshard 支撑）消除随负载剧变的 MoE 激活。最终选 **TP4PP4CP4EP32**：CP2 实测 OOM、CP4 可正常执行；相比 CP8，CP4 把 DP 翻倍并减少 RingAttention 通信次数，训练吞吐 263→412（**+30%+**，doc §3.1 表）。

### HDP 混合数据并行（§3.2）

纯 CP 的效率缺陷：序列打包到 `max_packing_token_size` 后无论长短都走相同 CP 划分与通信，短序列被强制切分引入不必要通信。**HDP（Hybrid Data Parallelism）**把 DP 与 CP 融合统一调度，内置装箱算法按序列长度自动选最优并行——长序列走 CP、短序列尽量划到 DP 组避免无谓通信。

<img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/qwen3_figures/image32.png" width="72%">
<sub>图：CP4 vs HDP——seq packing 后 batch2 [seq0 24k, seq1 8k] 在 CP4 下 seq1 仍被 4 卡切分产生冗余通信（Redundant Comm.），HDP 装箱后 seq0 占 rank0~2 做 CP3、seq1 单独占 rank3 无通信（Efficient Comm.）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 32K 长序列 RL 训练优化文档·§3.2 HDP 混合数据并行</a>）</sub>

HDP 装箱按序列预估占用 rank 数动态分组、溢出部分轮转合并并设上下阈值保鲁棒；框架侧需改 Positional Embedding（RoPE CP 通信范围调到组内）与 Ring Attention（`rank/cp_rank/cp_global_ranks/cp_outer_ranks`）。**收益强依赖数据长度分布**：Deepscaler（序列普遍 >3000，难均衡分组）下前 3 step 训练仅约 5%、端到端更小；而 DeepSeek-V3 + openr1-220k（序列普遍 <3000，大量纯 CP8 转 DP）训练耗时收益 **25%+**（178.234→133.139s，吞吐 77→107，doc §3.2 表）。recipe 通过 `USE_HDP` 环境变量 + megatron/mindspeed/verl 三处 `enable_hdp` patch（含 `0015-verl-feature-hdp_binpack_optimization`）使能。

## 未来方向（doc 长尾内存/线性注意力延展）

针对 Device 侧内存与长尾负载限制，可考虑以下优化方向；它们不等于 Qwen3-235B 训练配置中已启用的能力，仍需按目标模型和部署条件验证：

- **KVP 切分**（[kvp](../../../inference/concepts/parallelism/kvp.md)）：Qwen3-235B RL 配置通过分析推理侧实际内存、设置 `max_num_seqs=256` 不触发 continuous batching 来规避 OOM；对 Device 侧内存不够、必须 continuous batching 的极端长序列场景，沿 KV/序列维度做 KV-Parallel 切分可在单实例内进一步摊薄单卡 KV Cache 压力，与 Seer 的 Divided Rollout（每块最多推 8K token、推完放回缓存池再分配，规避 OOM 与中途 preempt）思路一致，是 Rollout Rebalance 之外的另一条长尾/显存缓解方向（doc §2.2.2、§2.3.1 与 Seer 论文对比）。
- **Qwen-Next gated_delta_rule**（[recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md)）：上述训练配置使用标准 attention 的 Qwen3-235B-A22B；Qwen-Next 引入的 **gated delta rule 线性/递归注意力**使 KV Cache 不再随序列长度线性增长，可缓解 §2.1 所述「HBM 随序列长度线性增长」的长序列显存瓶颈，是长序列 RL 后续模型迭代的算子方向（doc §1.1 背景）。

## 当前目录与可选 Dynamic RL

本实践入口现位于 `llm_rl/qwen3/verl-mindspeed/`，依赖准备、`apply_all_patches.sh` 和 `internal/` 启动脚本均在该目录执行。当前新增 `train_grpo_qwen3_30b_16die_dynamic_rl.sh`，提供 History Tree 响应复用与 EAGLE3 chain 草稿的动态切换；它是 Qwen3-30B 的独立可选配置，不能当作上文 235B 观测已经启用的特性。配置、预热和可比指标见 [History Tree Dynamic RL](../../concepts/techniques/history_tree_dynamic_rl.md)。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md)（primary）
- [qwen3_235B_32k_longseq_rl_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md)（supporting）
- [0005-verl-feature-moe_alltoallv.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0005-verl-feature-moe_alltoallv.patch)（implementation）
- [0016-verl-bugfix-hot_swap_expandable_segments.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0016-verl-bugfix-hot_swap_expandable_segments.patch)（implementation）
- [sam_decoding.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/sam_decoding.md)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/README.md)（implementation）

## Links
- [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md)（跨域：Qwen3 RL 训练使能的 npugraph_ex 图模式，SAM与npugraph_ex叠加后，相对两者均关闭基线首步推理耗时约下降29%~33%）

- [grpo-dapo](../../concepts/techniques/grpo_dapo.md)（本实践 RL 算法：同批一次参数更新条件下 GRPO old_log_prob 免计算 + DAPO clip-higher/token-IS/样本过滤）
- [sam-speculative](../../concepts/techniques/sam_speculative.md)（Qwen3-32B/235B 使能的无模型 SAM 投机，长尾 1.35X）
- [train-rollout-switch](../../concepts/techniques/train_rollout_switch.md)（全共卡 RL 的 reshard/offload/D2D，长序列 235B 训推切换基础）
- [rollout-rebalance](../../concepts/techniques/rollout_rebalance.md)（推理时序列级动态重均衡，缓解长尾木桶效应）
- [length-aware-resampler](../../concepts/techniques/length_aware_resampler.md)（基于历史 response 长度的 epoch 重采样，README 可选特性）
- [swap-optimizer](../../concepts/techniques/swap_optimizer.md)（MindSpeed 优化器状态卸载，训练静态内存压到 12.51GB）
- [verl](../../concepts/frameworks/verl.md)（veRL 前端：角色/数据流/MindSpeed repatch/vLLM-Ascend additional_config）
- [mindspeed](../../concepts/frameworks/mindspeed.md)（训练引擎：CP/moe_zero_memory/swap_optimizer/HDP）
- [vllm-ascend](../../concepts/frameworks/vllm_ascend.md)（推理引擎：TorchAir GE 图模式 / 多档位编图 / FIA / Chunk-MoE）
- [deepseek-r1-rl](deepseek_r1_rl.md)（同底座姊妹实践：DeepSeek-R1 671B veRL RL，通用训推切换/reshard 来源）
- [qwen3-moe](../../../inference/concepts/models/qwen3_moe.md)（跨域：Qwen3-235B MoE 推理部署）
- [kvp](../../../inference/concepts/parallelism/kvp.md)（跨域·未来方向：KV-Parallel 切分，Device 侧内存不足时摊薄单卡 KV Cache，长尾/continuous-batching 场景延展）
- [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md)（跨域·未来方向：Qwen-Next gated delta rule 线性/递归注意力，KV Cache 不随序列长度线性增长，从根上缓解长序列显存瓶颈）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：Atlas A3 硬件平台）
- [verl](https://github.com/volcengine/verl) / [mindspeed](https://gitcode.com/ascend/MindSpeed) / [vllm-ascend](https://github.com/vllm-project/vllm-ascend)（上游框架仓，下探）
- [qwen3-code-toolcall-rl](qwen3_code_toolcall_rl.md)（同域并列:多轮工具调用 Code RL）
