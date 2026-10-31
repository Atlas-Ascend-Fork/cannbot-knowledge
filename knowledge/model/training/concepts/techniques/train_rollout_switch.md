---
type: Concept
title: RL 训推切换（Train/Rollout Switch：reshard / offload / D2D）
description: 大模型 on-policy RL 训推切换包含训练态与推理态之间的权重重切分（reshard）、显存装卸（offload/onload）及任务间 D2D 张量直传。DeepSeek-R1 671B 全共卡部署中，Megatron+MindSpeed 承载 actor update / ref log_prob，训练侧为 TP4EP8PP8；vLLM+vLLM-Ascend 承载 rollout，推理侧为 DP64TP2EP128（真实权重）或 DP128TP2EP256（随机权重）。更新后的权重须转换为推理布局，各态模型通过 host/device 装卸分时复用显存。MindSpeed-RL 原生 MegatronShardingManager 负责 Megatron↔vLLM 权重重切分，onload/offload 接口管理权重与优化器状态以降低峰值显存。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- a3
---

# RL 训推切换（Train/Rollout Switch：reshard / offload / D2D）

## Summary

大模型 on-policy RL 训练中，**同一组卡**要在「训练态」（actor update / ref log_prob，由 Megatron+MindSpeed 承载）与「推理态」（rollout/generate，由 vLLM+vLLM-Ascend 承载）之间反复交替——这就是**训推切换**。两态对同一份 671B 权重采用**不同并行策略**：训练侧 `TP4EP8PP8`，推理侧 `DP64TP2EP128`（真实权重场景）甚至 `DP128TP2EP256`（随机权重场景）。每完成一次训练更新，新权重必须先**重新切分（reshard）**成推理布局再喂给 rollout；又因 ActorRolloutRef 三模型采用**全共卡部署**（分时复用计算资源），切换时还要把上一态模型 **offload 到 host**、把下一态模型 **onload 到 device**。训推切换由三个机制构成：**reshard**（训→推权重重切分，[§reshard 优化](#reshard-优化训推权重重切分)）、**offload**（训练态权重/KV 显存卸载，[§offload 优化](#offload-优化全共卡分时复用显存)），以及任务间**任务间输入输出张量 D2D 直传**（device 间直传消除 host 中转，[§D2D 数据传输](#d2d-数据传输任务间张量直传)）。

> 训推切换是 DeepSeek-R1 与 Qwen3 等模型共享的 RL 系统优化问题。端到端配置、训推并行策略及性能结果分别见 [DeepSeek-R1 RL](../../guides/recipes/deepseek_r1_rl.md) 与 [Qwen3 RL](../../guides/recipes/qwen3_rl.md)。

## 为什么训推切换是 RL 性能瓶颈

DeepSeek-R1 每步训练分三个计算密集阶段：**rollout/generate（推理生成问答）→ ref（参考模型算参考概率分布）→ update（训练模型算 loss 反向更新）**。对 671B 模型这三阶段都吃满算力，故全共卡分时复用是简单高效的部署策略——但代价是每次阶段切换都要做权重布局转换 + 显存搬运。模型完成一次训练更新后，推理需使用更新后的参数；由于训练和推理采用不同并行策略，参数传递给推理侧时需重新划分调整（reshard）；又因 ActorRolloutRef 三模型全共卡部署，切换间还需把前一模型 offload 至 host、再加载后续模型至 device。

两个 128 卡 A3 基线的训推切换耗时拆解如下（系统吞吐 = 数据生成 + 训练 + 训推切换合算）：

| 场景 | 部署 | 数据生成 | 训练(update) | reshard | offload 等 | 系统吞吐 |
|------|------|---------|--------------|---------|-----------|---------|
| 真实权重（deepscaler，1K 推 3K，部分优化） | rollout `DP64TP2EP128` / actor·ref `TP4EP8PP8` | 523.38s | 319.3s | 11.5s | 5.5s | **123.16 TPS/卡** |
| 随机权重（gsm8k，强制专家均衡，全量优化） | rollout `DP128TP2EP256` / actor·ref `TP4EP8PP8` | 436.86s | 328.8s | 11.18s | 24.45s | **250.2 TPS/卡** |

训推切换本身（17s / 35.63s）相对单步总耗时占比不高，但它与 rollout/update 强耦合——切换不畅会让 worker 互相等待、放大 update 阶段的串行下发时差（见下文 D2D）。reshard / offload / D2D 三项优化都是把这块耗时连同其引发的等待压到最低。两态的并行策略 / 框架分工详见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)。

## D2D 数据传输（任务间张量直传）

RL 各阶段（generate_sequences / compute_ref_log_prob / update_actor）的输入大多由前序任务在 **device 侧**产生。[verl](../frameworks/verl.md) 的单控制器用 Ray 在 host 主进程做 `dispatch_fn`（按 DP size 切 batch）+ `execute_fn`（逐 worker 下发）+ `collect_fn`（拼接结果）——大 tensor 经历「device→序列化→host→反序列化→device」的往返，且 worker 任务是**串行下发**：256Die 实测 0 卡与 255 卡的 update 启动时差可达 **96 秒**（与 profiling 首个超长通信耗时吻合）。根因是 Ray 给单个 worker 下发任务至少包括输入数据序列化、数据传输、输出数据序列化三步；当输入 tensor 数据量很大时，大量 worker 的任务下发耗时不断累积，形成训练性能瓶颈。

优化思路：**控制流维持 verl 单控制器逻辑不变，数据流解耦出来用 D2D 直传加速**。具体用 `TensorCache`（每个 worker 一个，device 侧管理前后任务共用 tensor），后续任务按需从缓存拉取，必须经 host 的数据才走原 Ray 通路。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/deepseek_figures/image12.png" width="55%"></p>
<p align="center"><sub>图：细化后的任务间数据流——gen 输出（attention_mask/input_ids/position_ids/responses）原地缓存供 ref 用，ref 输出（ref_log_prob）缓存供 update 用，仅必要 tensor（responses/advantages 等）经 host 主进程（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·性能优化：D2D 数据传输）</sub></p>

`TensorCache.get_cached_tensors()` 是否触发通信取决于前后任务 DP rank 排布：

- **排布一致**（update 用 ref 更新过的缓存）：actor 与 ref 并行策略一致、DP rank 排布完全相同，「ref 使用过的输入输出数据与 update 所需输入数据完全一致」，**无需任何通信**直接复用。
- **排布不一致**（ref 用 generate 更新过的缓存）：需在 batch 维对缓存做 reshard，用 **AlltoAllV** 在 device 间一次性完成 verl 原本主进程做的 dispatch+collect。

> 该方案当前限制：不支持 `balance_batch` / pack 序列；只考虑 ActorRolloutRef 共 worker 实例场景；只支持 **GRPO on-policy**（off-policy 需 batch_size 细节调整）。

收益（A3 128 卡、随机权重、prompt 0.075K / response 3K）：训练侧任务下发耗时**基本被消除**——`compute_ref_log_prob` 启动最大时差 ~57s→<1s（~98.2%）、`update_actor` ~73s→~5s（~93.2%）；端到端 ref 阶段 -33.0%、update_actor -16.6%、整体吞吐 208.5→238.46 TPS（**+14.4%**）。

## reshard 优化（训推权重重切分）

671B 是典型 MoE，**专家层参数占比超 70%** 且动态路由，故专家参数（EP）的分片迁移是训→推的关键瓶颈。reshard 分两类参数处理：路由专家走 **AlltoAllV 定向路由**，TP 切分参数走 **TP-先-PP 重排**。

### 专家参数：AlltoAllV 定向路由（零冗余迁移）

**原方案**靠识别参数名含 `.mlp.experts.linear_fc` 触发 EP 迁移：先在 `ep_group` 内 `all_gather` 拿到全部 256 个路由专家，再用推理侧 `load_weight` 加载本卡所需的单个专家。全量广播有两大局限——**通信冗余**（训练 EP4→推理 EP8 时，训练 rank0 只需发给推理 rank0/rank1，全量广播却也发给 rank2/rank3，50% 带宽浪费且随 ep_size 增大而攀升）与**内存峰值放大**（全聚合 256 个 7168×4096 路由专家 W1，单卡增量内存达 `0.0547G*256=14G`，极易 OOM）。

**优化方案**基于 AlltoAllV 设计**定向路由**，按训练侧全局 rank 的专家归属生成稀疏发送/接收表，只把分片送到目标推理 rank：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/deepseek_figures/image16.png" width="55%"></p>
<p align="center"><sub>图：路由专家 AlltoAllV 定向路由——训练 EP4PP2→推理 EP8PP1，各训练 rank 仅向目标推理 rank 直传所持专家，无冗余通信（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·reshard 优化 / 专家参数定向路由）</sub></p>

以单卡路由专家 W1 为例（单层 256 专家、推理 EP256），优化前 AllGather 需备齐全部专家空间 `0.0547*256=14G`，优化后 AlltoAllV **最多只需一个专家空间** `0.0547*(256/256)=0.0547G`——增量内存与通信量**相对收益均达 99.6%**。约束：当前只支持 Megatron 使能 `moe_tp_extend_ep`；训练 EP 须整除推理 EP。

### TP 参数：TP-先-PP 重排（PP 域 Broadcast 优化）

推理侧不用 PP，故训练 PP 域内的参数需聚合。**原方案**「先广播再聚合」：先 Broadcast 把参数分发到各训练 PP rank（每卡持有全 layer 切片），再逐 layer 做 TP 域 AllGather——同名参数在不同 PP rank 上**重复做 TP 域 AllGather**，通信冗余显著。**优化方案**重构为**先 TP 域 AllGather 局部聚合、再 PP 域一次 AlltoAll 广播**：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/deepseek_figures/image18.png" width="62%"></p>
<p align="center"><sub>图：TP 参数 reshard（PP4TP2）——Step1 各 TP 域内 AllGather 聚合分片，Step2 PP 域内一次 AlltoAll 即广播 PP 个参数，每卡获得整网参数（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·reshard 优化 / PP 域 Broadcast 通信优化）</sub></p>

两点收益：先 TP 后 PP 的顺序调整减小总通信量与次数；原本 PP 域内一个参数一次 Broadcast，优化后**一次 AlltoAll 完成 PP 个参数的广播**。通信对比（n 层、单层完整参数量 m、单层 TP 参数数 k、训练 PP=p、TP=t，以每卡接收量计）：

| | Step1 | Step2 |
|---|---|---|
| 优化前 | PP Broadcast：通信量 ≈ `n*m/t`、次数 `n*k` | TP AllGather：通信量 ≈ `n*m`、次数 `n*k` |
| 优化后 | TP AllGather：通信量 ≈ `n*m/p`、次数 `n*k/p` | PP AlltoAll：通信量 ≈ `n*m`、次数 `n*k/p` |

通常 p>t（如 p=8/t=4），优化后 Step1 通信量**减半**；TP 域 AllGather 与 PP 域通信**次数各减少 `(p-1)/p · n*k`**；Step2 通信量不变。注：`.mlp.experts.weight` 走上面的专家 AlltoAllV；`embedding`/`output_layer` 及 MLP dense 层暂未纳入，后续迭代。

## offload 优化（全共卡分时复用显存）

vLLM 的 `wake_up`/`sleep` 在 NPU 多机实测仍有问题（无法释放显存），故本实践参考 [mindspeed](../frameworks/mindspeed.md) 生态的 MindSpeed-RL 实现：用 `onload_model_weight` + `init_cache_engine` 替代 `wake_up`，用 `offload_model_weight` + `free_cache_engine` 替代 `sleep`。在此基础上做两点细节优化：

- 训练后紧接着 reshard 时仍需训练模型权重，因此训练后无需卸载 Megatron 权重、推理前也无需再次加载，这两步冗余的 offload/onload 可省去。
- `init_cache_engine` 尽量后置（例如放在 reshard 结束、卸载 Megatron 训练权重之后执行），可降低峰值内存、提高 vLLM 内存利用率，有助于提升推理性能。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/figures/deepseek_figures/image19.png" width="55%"></p>
<p align="center"><sub>图：offload/onload 流程调整——「训练后」由卸载权重+梯度改为「仅卸载梯度、权重保留」供 reshard 复用，`init_cache_engine` 后置到 reshard 与训练权重卸载之后以降峰值（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·offload 优化）</sub></p>

注意，verl 适配 vLLM-Ascend 时须**显式关闭 sleep 模式**——否则 weight 与 kv_cache 会被 vLLM 自定义内存池管理，后续无法用 torch_npu 手动卸载（详见 [verl](../frameworks/verl.md) 适配）。从 reshard 后的视角看，「权重保留」让训练权重与推理 cache 在切换瞬间的显存峰值通过**时序错开 + 后置 cache 分配**被压低，间接提升 rollout 阶段可用显存与吞吐。

## 配置与启用

reshard 的离线前置——训练权重切分须与训练侧 `TP4EP8PP8` 对齐，并使能 `--moe-tp-extend-ep`（对应专家 AlltoAllV 定向路由优化的约束「moe_tp_extend_ep」，是 reshard 专家迁移正确性的承重项）。随机/真实权重两套启动脚本与逐项切分超参（层数划分、首层 dense 替换等纯运行参数）见 recipe README，整体配置枢纽归 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)。

## MindSpeed-RL 实现

[mindspeed-rl](../frameworks/mindspeed_rl.md) 走的是另一条路线：训推切换不以补丁形式插进 veRL 单控制器，而是固化成一组挂在训推共卡混合 worker（`ActorHybridWorker` / `IntegratedWorker`，Actor·Reference·Reward 三角色分时复用同一批 NPU）上的**显式状态机接口** `MegatronShardingManager`。一轮 RL 迭代里，rollout 前后包 `enter_infer_mode` / `exit_infer_mode`，`update` 包 `enter_train_mode` / `exit_train_mode`，ref/actor 的 logprob 前向包 `enter_forward_mode` / `exit_forward_mode`；Actor 用 `ActorState{NONE, INFER}` 跟踪状态并打 `timing/resharding_*` 指标。rollout 与各态间的实验数据流由 [transferdock-data-scheduling](transferdock_data_scheduling.md) 承载。

切换的四类职责由 `MegatronShardingManager` 聚合的子模块分担，且彼此与训推引擎解耦（可换 Megatron/vLLM 之外的引擎）：`MegatronStyleVllmWeightContainer`（WeightContainer，把训练态权重按推理并行策略重切分）、`WeightAdaptor`（按模型族做 Megatron ↔ vLLM 权重命名/格式适配）、`MegatronOffLoader`（训练态权重/优化器/梯度的显存装卸）、以及 vLLM 推理引擎本身（持有推理权重 + KV Cache）。

### 原生 resharding：状态机 + 参数分桶 0 冗余

`enter_infer_mode` 的四步与 veRL 侧「权重保留 + cache 后置」同构：① `onload_infer_params` 重建推理参数桶 → ② `get_infer_params()` 执行重切分、把训练权重灌进桶 → ③ `train_param_offload` 时 `megatron_offloader.offload_param()` 卸训练权重 → ④ `inference_engine.sync_model_weights(load_format='megatron')` 灌进 vLLM。`exit_infer_mode` 反向：卸推理权重 + `offload_infer_params` 销毁推理桶。`exit_train_mode` 只卸优化器与梯度、训练权重保留（供随后 `enter_infer_mode` 的 reshard 复用、不重复卸载再装回），`enter_train_mode` 反向把（被 forward 卸过的）权重连同优化器/梯度一并装回；`enter/exit_forward_mode` 只装卸权重，供 ref/actor 算 logprob。

**参数分桶 0 冗余**解决形状变化引发的残留显存：TP/EP 改变会让权重张量形状变化，变形后的权重塞不回 Megatron 给训练权重分配的连续 `MemoryBuffer`，会留下卸不掉的冗余空间。方案是按**推理引擎权重元信息（MetaInfo）**为每个 PP Stage 单独申请推理参数桶（`ModelWeightBuffer.rebuild()` / `destroy()`，对应 `onload/offload_infer_params`）——桶尺寸严格贴合推理布局、无冗余；推理态申请推理桶并把训练权重/优化器/梯度全卸到 CPU，训练态再从 CPU 装回训练桶、释放推理桶，训练与推理显存物理隔离，得到 0 冗余切换。

`get_infer_params()` 内部按参数类型分三路重切（结果同构于 veRL 侧的「专家 AlltoAllV + TP-先-PP」，但落在 vLLM 进程组上）：

- **TP 参数**：训练 TP > 推理 TP 走 `allgather_tp_param`（TP 组内 `all_gather` 后按推理 rank 切片）；训练 TP < 推理 TP 走 `split_tp_params`（`chunk` 细分，gate/up 单独处理）。
- **PP 参数**：推理侧 PP=1，故 `_update_weight_buffers_inter_pp` 用 `dist.broadcast` 在 `pp_group` 上把各 PP rank 的层广播齐全（PP→DP）。
- **EP / 专家参数**（`moe_tp_extend_ep` 且 `infer_ep ≥ train_ep`）：`trans_ep_params_to_tp` 把 GroupedMLP 的 EP 切分经 `torch.distributed.all_to_all`（在 `ep_group` 上）转成 TP 切分——weight1 列切含 gate+up、weight2 行切转置后统一处理；EP 成倍增大时再由 `_send_receive_experts` 按 `get_expert_router` 算出的 src/dst 做 P2P `isend/irecv` 重分发专家，EPLB 冗余专家则按 `eplb_map` 走 `_send_receive_redundancy_experts` 的 P2P 收发。

已支持的训→推并行变换（推理侧 vLLM 限 PP=1）：TP 成倍增大或减小（增大需 $DP_{train}\times TP_{train}\ge TP_{infer}$）、PP 转 DP、EP 成倍增大（靠 TP/PP 成倍减小来增大 DP）。启用方式是直接在 `actor_config`（训练 `tensor/pipeline/expert_model_parallel_size`）与 `generate_config`（推理 `infer_*_parallel_size`）配不同并行策略即自动触发 resharding，无需显式开关。

### 原生 offload：storage-resize 换页 + 分粒度开关

`MegatronOffLoader` 用 `offload_train_optimizer` / `offload_train_grad` / `offload_train_param` 三个 `generate_config` 开关分别控制优化器状态、梯度、权重的卸载。底层换页是 `swap_tensors_to_host` / `swap_tensors_to_device`：为每个张量预留一份 CPU 镜像（`tensor_to_cpu_states_map`），卸载 = 拷贝到 CPU 后 `tensor.storage().resize_(0)`（真正释放 NPU 显存），加载 = `resize_` 回原大小再从 CPU 拷回；梯度走 `copy_data=False`（只要回原空间、不需搬内容，省一次拷贝）。开 `reuse_fp32_param` 的 distributed-optimizer 场景还需 `reuse_data_ptr` 重映射 fp32 主权重与 res buffer 的地址。效果是把训练态优化器/梯度/权重卸到 Host、给 vLLM 推理腾出充足 KV Cache 空间，压低 NPU 峰值显存、避免 OOM。

veRL 侧之所以「用 `onload_model_weight` + `init_cache_engine` 替代 vLLM `wake_up`、`offload_model_weight` + `free_cache_engine` 替代 `sleep`」（见 [§offload 优化](#offload-优化全共卡分时复用显存)），范式正来自 MindSpeed-RL 这套显式装卸——vLLM 原生 `wake_up` / `sleep` 在 NPU 多机释放不掉显存，故两条线都改用可被 `torch_npu` 手动管理的权重/cache 装卸接口。

### 与 veRL 侧对照

| 维度 | veRL 侧（cann-recipes-train） | MindSpeed-RL 原生 |
|------|------------------------------|-------------------|
| 切换载体 | 给 veRL 单控制器打补丁（控制流不变、数据流 D2D 解耦） | 挂在共卡 hybrid worker 上的显式状态机 `MegatronShardingManager` |
| 专家 reshard | AlltoAllV 定向路由（稀疏发送表，零冗余迁移） | `all_to_all`（`ep_group` 上 EP→TP）+ EP↑ 时 P2P `isend/irecv` 专家路由 |
| TP/PP reshard | TP-先-PP 重排（PP 域一次 AlltoAll 广播） | TP `all_gather` / `split` + PP 域 `broadcast`（PP→DP） |
| 显存隔离 | 训练后「权重保留」+ `init_cache_engine` 后置降峰值 | 推理参数桶按推理 MetaInfo 0 冗余 + storage-resize 换页 |
| offload 装卸 | onload_model_weight / init_cache_engine 替代 wake_up/sleep | `MegatronOffLoader` 分粒度 `offload_train_{optimizer,grad,param}` |
| 配置入口 | recipe 启动脚本 + `--moe-tp-extend-ep` | `actor_config` / `generate_config`（`infer_*` + `offload_train_*`） |

两条线解的是同一问题——训练态（大 TP/PP、小 EP）与推理态（小 TP/PP、大 EP）权重在线重切 + 全共卡分时复用显存；MindSpeed-RL 把它做成框架内建的状态机接口，veRL 侧则以补丁形式获得等价能力。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/README.md)（primary）
- [deepseek_rl_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_rl/deepseek_rl_train_optimization.md)（supporting）

## Links

- [verl](../frameworks/verl.md)（单控制器/多控制器框架，D2D 解耦的对象、TensorCache 接入点、sleep 模式关闭）
- [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)（所属 RL 实践：128 卡 A3 全共卡、训推并行策略、123.16/250.2 TPS 系统吞吐枢纽）
- [mindspeed](../frameworks/mindspeed.md)（训练侧引擎；本实践训练优化复用来源——内存/通信/计算优化、融合算子）
- [swap-optimizer](swap_optimizer.md)（训练态优化器状态卸载，与训推切换的推理态显存卸载互补的显存优化）
- [expert-parallel](../../../inference/concepts/parallelism/expert_parallel.md)（跨域：MoE 专家并行；reshard 把训练 EP 布局重切到推理 EP）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba) — DeepSeek-R1 RL 训练昇腾优化实践
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（Qwen3 235B RL 训推切换）
- [mindspeed-rl](../frameworks/mindspeed_rl.md)（MindSpeed-RL 训推共卡引擎实现训推态切换；onload/offload 范式来源——`onload_model_weight`/`init_cache_engine` 替代 `wake_up`、`offload_model_weight`/`free_cache_engine` 替代 `sleep`）
- [vllm-ascend](../frameworks/vllm_ascend.md)（MindSpeed-RL rollout 经 vLLM-Ascend adapter 切换）
