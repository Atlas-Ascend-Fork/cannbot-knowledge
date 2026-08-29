---
type: Concept
title: EPLB（专家并行负载均衡器，MoE 专家动态负载均衡）
description: EPLB（Expert Parallelism Load Balancer，专家并行负载均衡器）最早由 DeepSeek 针对大规模 MoE 模型训练中「负载不均」核心痛点推出，是一种动态负载均衡解决方案。MoE 门控网络把样本分配给适配专家，导致专家负载两极分化（热/冷专家分化），且「冷热」身份随数据批次切换动态漂移形成负载热点；在专家并行架构下专家固定分配至 NPU 节点，这种冷热分化直接传导为节点利用率失衡。EPLB 的核心目标是通过智能调度策略消除专家模块及计算节点间的负载差异、最大化 NPU 资源利用率。它提供分层 / 全局两种调度模式，并依托历史负载估计动态调整专家复制与分配方案，快速适配批次切换、领域迁移导致的负载热点漂移。 本页是 EPLB 概念的 canonical 页，依 Qwen3-235B 32K 长序列 RL 训练优化文档 §2.3.2 讲透其现象分析、双模式调度、动态估计机制，以及——最关键的实测诚实结论：在 Qwen3-30B / 235B 加载真实权重的 RL rollout 推理场景下，实测各卡负载本身并无明显不均衡，开启 EPLB 无明显性能收益；只有在人为构造的极端负载不均场景下 EPLB 才带来推理耗时 -17.78% 的提升。即「负载均衡时 EPLB 不带收益，仅极端不均才有效」。MindSpeed-RL workers/eplb 在 RL 训推共卡下做 MoE 专家负载均衡：采集各专家负载→重排/复制热专家→更新 device 映射，与训练态 balanced/placement（moe-load-balance）互补。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.reinforcement_learning
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-06-30T00:00:00Z'
platforms:
- a3
---

# EPLB（专家并行负载均衡器，MoE 专家动态负载均衡）

## Summary

**EPLB（Expert Parallelism Load Balancer，专家并行负载均衡器）**最早由 **DeepSeek** 针对大规模 MoE 模型训练中「负载不均」核心痛点推出，是一种**动态负载均衡**解决方案。MoE 门控网络把样本分配给适配专家，导致专家负载**两极分化**（热/冷专家分化），且「冷热」身份随数据批次切换**动态漂移**形成负载热点；在专家并行架构下专家固定分配至 NPU 节点，这种冷热分化直接传导为节点利用率失衡。EPLB 的核心目标是通过智能调度策略消除专家模块及计算节点间的负载差异、最大化 NPU 资源利用率。它提供**分层 / 全局两种调度模式**，并依托**历史负载估计动态调整专家复制与分配方案**，快速适配批次切换、领域迁移导致的负载热点漂移。需说明的是：DeepSeek 对 EPLB 的原生定位是 **MoE 训练态**的专家负载均衡器，而本实践把它落地于 **RL 的 rollout 推理子阶段**（vLLM-Ascend 推理引擎），下文三组实验的观测对象均为推理 `generate_sequences` 耗时与每卡 token 分布——「训练负载均衡器」与「推理实测」属不同语境，勿混淆。

在 Qwen3-30B / 235B **加载真实权重**的 RL rollout 推理场景下，各卡负载本身并无明显不均衡，**开启 EPLB 无明显性能收益**；只有在**人为构造的极端负载不均场景**下 EPLB 才带来推理耗时 -17.78% 的提升。即「负载均衡时 EPLB 不带收益，仅极端不均才有效」。它与 [Rollout Rebalance](rollout_rebalance.md)（序列级长尾均衡）同属 RL rollout 推理的负载均衡优化方向但作用对象不同——EPLB 作用于**专家/节点维度**，Rebalance 作用于**请求序列维度**。

## 现象分析：专家冷热分化传导为节点负载失衡

EPLB 要解决的问题在 MoE + 专家并行（[EP](../../../inference/concepts/parallelism/expert_parallel.md)）架构下分两层：

- **专家模块——负载「冷热分化」**：MoE 门控网络将样本分配给适配专家，导致专家负载两极分化。极端场景下，头部 20% 的「热专家」承担 80% 以上计算任务、队列长期饱和；尾部 30% 的「冷专家」调用率常低于 5%、多数时间闲置。且「冷热」身份会随数据批次切换**动态转移**，形成负载热点漂移。
- **计算节点——NPU 利用率两极失衡**：专家并行架构中专家固定分配至 NPU 节点，「冷热分化」直接传导为节点负载不均。极端场景下承载热专家的节点利用率长期超 90%、易现 NPU 内存溢出；承载冷专家的节点利用率多低于 30%、甚至不足 10%。节点负载还随专家「冷热」切换动态波动，**静态调度无法适配**。

正因热点是动态漂移的，静态的专家-节点映射无法长期保持均衡，这是 EPLB 采用「动态」调整的根本动机。

## 优化方案：双模式调度 + 实时负载估计

### 双模式负载均衡调度

EPLB 提供**分层**与**全局**两种调度模式，适配不同训练/推理场景：

- **分层负载均衡策略**：当**专家组数量可以被服务器节点数整除**时，EPLB 采用分层策略，充分利用 DeepSeek-V3 中**组限制路由（Group-Limited Expert Routing）**的特性，分三步：
  1. 将专家组均匀分配到各个节点，确保**节点间**的负载平衡；
  2. 在每个节点内**复制冗余专家**；
  3. 节点内将专家分配到不同的 NPU 上，确保 **NPU 间**的负载均衡。
- **全局负载均衡策略**：在其他情况下（如解码阶段），EPLB 切换到全局策略，**忽略专家组的限制**，直接在所有 NPU 上复制和分配专家。适用于更大规模的专家并行场景，灵活应对复杂的负载分布情况。

两种模式的本质区别在于「是否尊重专家组（expert group）的物理边界」：

- 分层策略以**节点**为粒度逐层均衡（组→节点→NPU 三级），保留组限制路由结构，约束是「专家组数量须能被节点数整除」；它把均衡问题分解为「节点间均衡 + 节点内冗余复制 + NPU 间均衡」三个子问题，避免跨组的全局重排，调度开销相对可控。
- 全局策略放弃组边界，把所有 NPU 视作一个扁平的专家承载池直接复制/分配，自由度更高、能应对更复杂的不均分布，代价是更大的重分配范围；它适用于不满足分层前提（专家组数可被节点数整除）的其他情况——源文档以解码阶段为例，此时 EPLB 回退到全局策略而非把它当作一个固定的「decode→全局」配置。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image20.png" width="72%"></p>
<p align="center"><sub>图：EPLB 分层负载均衡策略——专家组均匀分配到各节点（节点间均衡）→ 节点内复制冗余热专家 → 节点内专家分配到不同 NPU（NPU 间均衡）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B 长序列 RL 训练优化文档</a>·2.3.2 Expert Parallelism Load Balance）</sub></p>

### 实时负载估计与动态调整

EPLB 依托**历史计算数据**（如任务耗时、调用频率）构建负载估计模型，通过**移动平均值**等算法实时输出各专家及节点的负载值。基于该估计结果，EPLB **动态调整专家复制策略与分配方案**，快速适配训练数据分布变化（如批次切换、领域迁移）导致的负载热点漂移。

这是 EPLB「动态」二字的落点——区别于一次性的静态映射，专家的复制份数与落卡随历史负载滚动调整。其闭环可概括为「估计→调整」两步：

1. **负载估计**：以历史的任务耗时 / 调用频率为观测量，移动平均平滑掉单批次抖动，得到各专家、各节点的稳定负载画像，从而识别出当前的「热专家」与饱和节点；
2. **动态调整**：据画像把热专家复制更多份、铺到利用率低的节点 / NPU 上，把整体负载向均衡推。当下一批数据使冷热身份漂移时，估计随之更新、复制方案再次调整——这正是它能对抗「负载热点漂移」而静态调度不能的原因。

## 实测效果：真实权重无收益，仅极端不均才有效

三组实验显示——EPLB 在真实权重场景下并未带来收益，并非普遍正收益。

**实验一（Qwen3-30B 真实权重）**：测试开启 EPLB 前后的推理耗时，结果**开启 EPLB 并无性能提升**。

| 模型 | 训练集 | 序列长度 | batch size*n | die 数 | infer DP | infer EP | infer TP | 使能 EPLB | generate_sequences / step（s） |
|--|--|--|--|--|--|--|--|--|--|
| Qwen3-30B | gsm8k | 1K 推 3K | 32*16 | 16 | 16 | 16 | 1 | 否 | 80.19 |
| Qwen3-30B | gsm8k | 1K 推 3K | 32*16 | 16 | 16 | 16 | 1 | 是 | 83.16 |

推理第 1000 个迭代的负载（每卡专家分到的 token 总和）显示**每卡负载并无特别大的差异**，故 EPLB 无从优化。三个代表性 layer 的逐卡（16 die）token 总和（单位 token）：

| | rank0 | rank1 | rank2 | rank3 | rank4 | rank5 | rank6 | rank7 | rank8 | rank9 | rank10 | rank11 | rank12 | rank13 | rank14 | rank15 |
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| layer0 | 202117 | 151740 | 223832 | 220797 | 131111 | 180507 | 175831 | 286109 | 210812 | 297418 | 205835 | 173824 | 237945 | 272396 | 199340 | 345822 |
| layer20 | 200978 | 213408 | 326325 | 317587 | 245067 | 220074 | 298096 | 176724 | 201202 | 246980 | 282587 | 102573 | 170262 | 142857 | 94099 | 419867 |
| layer47 | 232567 | 326583 | 121142 | 253510 | 316796 | 108912 | 211056 | 212969 | 101383 | 313065 | 223130 | 213813 | 175164 | 355333 | 176536 | 182247 |

各卡负载虽有波动但同处一个数量级（约 10 万~42 万），不存在「某卡饱和、某卡近零」的极端不均，这正是真实权重下 EPLB 无收益的直接证据；实验三作为对比实验构造负载不均衡场景、验证 EPLB 的有效性。

**实验二（Qwen3-235B 真实权重）**：结果**开启 EPLB 并无明显性能提升**。

| 模型 | 训练集 | 序列长度 | batch size*n | die 数 | infer DP | infer EP | infer TP | 使能 EPLB | generate_sequences / step（s） |
|--|--|--|--|--|--|--|--|--|--|
| Qwen3-235B | deepscaler | 2K 推 32K | 256*16 | 128 | 64 | 64 | 4 | 否 | 2291 |
| Qwen3-235B | deepscaler | 2K 推 32K | 256*16 | 128 | 64 | 64 | 4 | 是 | 2273 |

**实验三（构造极端负载不均）**：作为对比实验，**人为将选择的专家全部固定为 0-15 号专家**，此时 rank0、rank1 承载高负载、其余卡负载为 0。结果推理耗时缩短 **17.78%**。

| 模型 | 训练集 | 序列长度 | batch size*n | die 数 | infer DP | infer EP | infer TP | 使能 EPLB | generate_sequences / step（s） |
|--|--|--|--|--|--|--|--|--|--|
| Qwen3-30B | gsm8k | 1K 推 3K | 32*16 | 16 | 16 | 16 | 1 | 否 | 127.52 |
| Qwen3-30B | gsm8k | 1K 推 3K | 32*16 | 16 | 16 | 16 | 1 | 是 | 104.85 |

**实验结论**：Qwen3-30B 和 Qwen3-235B 基于加载真实权重场景测试，并无明显性能提升，推理过程中每卡负载并无明显负载不均衡情况；实验三构造明显的负载不均衡场景，显示**在极端场景下 EPLB 有明显的性能提升**。即**当负载并无明显不均衡情况，EPLB 不能带来性能收益**。

## 适用性判断

由上可得 EPLB 的工程取舍：它的收益**完全取决于实际负载是否真的不均衡**，而非「开了就快」。

- 在真实权重 RL rollout 推理中，门控路由本身已使各卡负载较为均衡（无热点漂移到数量级差异），EPLB 的复制/重分配只增加调度开销而无均衡收益（实验一甚至略有劣化 80.19→83.16）。
- 只有当负载存在**明显不均衡**（如实验三人为固定专家、或数据分布导致真实热点漂移）时，EPLB 才把热专家复制到空闲节点、拉平利用率，从而缩短端到端 `generate_sequences` 耗时。

因此 EPLB 应作为**条件触发**的优化，建议的判定流程：

1. 在目标负载（真实权重 + 真实数据）下打印推理过程中每卡的负载（每卡专家分到的 token 总和，可取代表性 layer 多次采样）；
2. 若各卡负载同处一个数量级、无饱和/近零的极端分化 → **不开 EPLB**（实验一/二即此情形，开启反而引入调度开销，Qwen3-30B 实测 80.19→83.16 略劣化）；
3. 仅当观测到明显不均衡（数量级差、热点漂移）→ 开启 EPLB，按场景选分层（组数可被节点数整除时）或全局（解码 / 复杂分布）模式。

这与负载均衡类优化「效果与数据集长尾分布强相关」的一贯判断一致：[Rollout Rebalance](rollout_rebalance.md) 同样指出，若数据集本身或经 data balancing 已使负载均衡，则均衡特性能带来的额外收益会降低。两者共同的工程启示是——**负载均衡类优化的价值不是恒定的，必须先量化不均衡程度再决定是否投入**。

## MindSpeed-RL EPLB 实现

MindSpeed-RL 在 RL rollout 推理路径（vLLM-Ascend 引擎）上把 DeepSeek 开源 EPLB 算法落成一套**离线三步管线**：采集每卡专家负载 → 离线生成冗余专家映射表 → 加载/resharding 时按映射用 P2P 重分发专家权重。它与 cann-recipes-train 的 vLLM-Ascend 落地是同一类问题的另一框架实现，目标场景是 DeepSeek-R1-671B / Atlas A3 16 节点 256 卡的 GRPO RL。框架侧的 Ray 训推共卡编排见 [mindspeed-rl](../frameworks/mindspeed_rl.md)。

```mermaid
flowchart LR
    A["rollout 前向<br/>开 eplb_token_collects"] -->|每卡统计 topk_ids| B["eplb_token_collects_{rank}.json<br/>层→专家→token 数"]
    B -->|collect_json_file.sh scp 汇聚| C["主节点 json_folder"]
    C -->|cli/eplb_generate_map_ds.py 离线| D["rebalance_experts<br/>分层/全局 + 去重"]
    D --> E["expert_map.json<br/>层→device→device_expert"]
    E -->|generate.expert_map_path| F["resharding 时<br/>_send_receive_redundancy_experts"]
    F -->|同卡 copy / 跨卡 P2P| G["专家权重落到目标冗余映射"]
```

### 负载采集：rollout 前向拦截 topk_ids

`generate` 配置开 `eplb_token_collects: true` + `eplb_token_save_path` 后，rollout 前向时 `AscendUnquantizedFusedMoEMethod.apply`（`fused_moe.py`）经 `set_EPLB_args` / `get_EPLB_args` 拿到开关；门控算出 `topk_ids` 后用 `torch.unique(topk_ids, return_counts=True)` 统计每个 expert 收到的 token 数，按当前层 `layer.moe_instance_id` 累加进 `experts_loads[layer][expert_id]`，落每卡一份 JSON `eplb_token_collects_{rank}.json`（外层 key = MoE 层号，内层 key = expert id，值 = 该专家被分到的 token 数）。每卡本地写：读出已有同名 JSON、按当前层累加后整文件覆盖写（`open(filepath, "w")` + `json.dump`）；`examples/eplb/collect_json_file.sh` 用 scp 把各节点 JSON 汇到主节点（共享存储场景免汇聚）。这步是 profiling 用途，带统计与 JSON I/O 开销，仅在采样负载画像时开。

### 离线生成冗余专家映射

`cli/eplb_generate_map_ds.py` 离线运行（不在训练 loop 内）：`load_and_aggregate` 把所有每卡 JSON 聚合成 `[num_layers, num_experts]` 负载张量 → 调 `eplb.rebalance_experts(weight, num_replicas, num_groups, num_nodes, num_gpus)` 算出冗余专家与落卡 → `find_replacement` 去重（同一 NPU 内不重复放同一逻辑专家，命中重复就换成「负载最接近且未用过」的专家）→ `tensor_to_json` 落 `expert_map.json`，结构为 `moe_layer_count / layer_list[].{layer_id, device_count, device_list[].{device_id, device_expert}}`。

关键参数（`examples/eplb/eplb.sh`，671B 案例取 num_replicas 512 / num_groups 16 / num_nodes 16 / num_gpus 256）：

- `num_replicas`：冗余后的物理专家总数（含原始专家），须被 `num_gpus` 整除——`num_replicas − num_logical` 即冗余副本数；
- `num_groups`：专家分组数，须被 `num_nodes` 整除、且须整除逻辑专家数（代码 `rebalance_experts_hierarchical` 校验 `num_logical_experts % num_groups == 0` 与 `num_groups % num_nodes == 0`），是分层策略复用 DeepSeek-V3 组限制路由的入口；
- `num_nodes` / `num_gpus`：节点数 / 总 NPU 数，`num_gpus` 须被 `num_nodes` 整除。

### rebalance_experts：分层/全局双策略的代码落点

入口 `rebalance_experts`（`eplb.py`，移植自 DeepSeek 开源 EPLB）在 `num_groups % num_nodes == 0` 时走分层 `rebalance_experts_hierarchical`，否则退全局策略——以 `num_groups=1, num_nodes=1` 调同一函数、放弃专家组边界做扁平复制。返回 `phy2log`（physical_to_logical_map，每个物理副本对应的逻辑专家）、`log2phy`（logical_to_physical_map）、`logcnt`（每个逻辑专家的副本数）。分层三步正是上文优化方案「组→节点→NPU 三级均衡」的代码实现：

1. **节点间均衡**：`balanced_packing` 把专家组按负载贪心打包到节点——每层先按权重降序排序，逐个把组塞给「当前最轻且未满」的包（每包恰好 `num_groups/num_nodes` 个组）；
2. **节点内复制冗余热专家**：`replicate_experts` 从 `num_log` 到 `num_phy` 每多加一个物理副本，就分给当前**每副本负载 `weight/logcnt` 最大**的逻辑专家，使「最大副本负载」最小化——这就是「复制热专家」的精确判据；
3. **NPU 间均衡**：再用 `balanced_packing` 把物理专家打包到各 NPU。

由此 MindSpeed-RL 实现的正是上文 DeepSeek 分层/全局 EPLB 算法，区别只在它在 RL rollout 推理侧以离线管线落地。

### 加载时按映射 P2P 重分发权重

启用阶段把 `generate` 的 token 采集关掉、给 `expert_map_path: <expert_map.json>`（该字段为 `None` 即不启用 EPLB）。`vllm_engine` 起 vLLM 引擎时透传 `expert_map_path`，读出 `fused_moe.expert_load_balancer.expert_map_tensor` 存为 `eplb_map`。训推切换 resharding 时（`megatron_sharding_manager` → `vllm_weight_container`），在 `moe_tp_extend_ep` 且 `infer_ep_size >= ep_size` 前提下由 `_send_receive_redundancy_experts` 把专家权重从初始均匀映射重排到目标 `eplb_map`：

- `create_initial_map` 按 rank 顺序连续切专家，构造推理侧初始（未均衡）的专家落卡映射；
- 单实例的 `eplb_map` 经 `eplb_map.repeat(...)` 按 EP-TP 建组组数扩展为多实例 `eplb_map_expanded`；
- 逐层逐专家比对初始与目标映射：同 rank 直接 `tensor_to_replace[idx] = tensor_to_send[src_idx]` 内存拷贝，跨 rank 用 `dist.P2POp(dist.irecv/dist.isend)` 收发、`dist.batch_isend_irecv` 批量提交，把每份冗余专家权重搬到目标卡。

### 适用边界

推理目前只支持单实例；每个 NPU 上的专家数须一致（去重逻辑保证）；权重重分发涉及 P2P 通信，建议资源充足时使用；`yaml` 配置优先于代码默认值。整体是一条 **profile-then-apply 的离线管线**——采集是一次性 profiling、映射离线由 CLI 生成、权重在加载/resharding 时重分发一次，区别于训练 loop 内逐 step 在线滚动调整。

与同域 [moe-load-balance](moe_load_balance.md)（MindSpeed **训练态**原生：`--balanced-moe-experts` 广播复制热专家 + token 本地化、`--enable-expert-placement` EMA 预测 + 物理迁移专家及优化器状态，均在训练 loop 内按频率在线触发）的关系：两者同解「专家冷热分化传导为 device 负载不均」，但作用阶段（训练 vs RL rollout 推理）、调度时机（在线逐步 vs 离线一次）与机制（placement 物理迁移不复制 / EPLB 与 balanced 走复制冗余）不同——本节是 RL rollout 推理侧借 DeepSeek 分层/全局 EPLB 算法的离线 collect→map→redistribute。

## 跨域对照：推理侧的 perfect eplb

EPLB 概念在 cann-infer 推理侧也有落地：DeepSeek-R1 推理 benchmark 在 **perfect eplb** 条件下采集性能数据（Prefill 64×4K 输入达 6522 tokens/卡/s，Decode 128 卡 W8A8C8+MTP1 达 TPOT 44.9 ms），并通过 decode 配置 `force_eplb: True` 强制专家均衡（见 [deepseek-r1](../../../inference/concepts/models/deepseek_r1.md)）。推理侧用「perfect/force eplb」作为构造均衡负载的基准条件来逼近峰值吞吐；训练侧本实践则反向验证了——真实权重负载本就均衡时，动态 EPLB 不带来额外收益。两侧互为印证：EPLB 的价值锚定在「负载确实不均」这一前提上。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md)（§2.3.2 Expert Parallelism Load Balance：现象分析（专家冷热分化 / 节点利用率失衡）、优化方案（分层/全局双模式调度 + 实时负载估计动态调整）、优化效果（实验一 Qwen3-30B 真实权重无收益 + 逐卡负载表、实验二 Qwen3-235B 真实权重无明显收益、实验三构造极端不均 -17.78%、实验结论）；分层策略图 `docs/llm_rl/figures/qwen3_figures/image20.png`）
- recipe 文件：`llm_rl/qwen3`（Qwen3 RL recipe 目录，承载本优化文档与配置）
- 外部参考：EPLB 由 DeepSeek 针对 MoE 训练负载不均提出（文档 §2.3.2 表述），分层策略依托 DeepSeek-V3 组限制路由（Group-Limited Expert Routing）

MindSpeed-RL 实现（钉定版 `398fd9a5`）：

- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`docs/zh/features/EPLB.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/features/EPLB.md)（三步使用流程：MoE Token Collect / Eplb_map Generate / EPLB Usage，含 JSON 格式、参数说明与单实例限制）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/workers/eplb/eplb.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/workers/eplb/eplb.py)（`rebalance_experts` 入口分层/全局分流、`rebalance_experts_hierarchical` 组→节点→NPU 三步、`balanced_packing` 贪心打包、`replicate_experts` 按 `weight/logcnt` 最大复制热专家）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`cli/eplb_generate_map_ds.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/cli/eplb_generate_map_ds.py)（`load_and_aggregate` 聚合每卡 JSON 成 `[layers,experts]`、调 `rebalance_experts`、`find_replacement` 同卡去重、`tensor_to_json` 落 `expert_map.json`）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/models/rollout/vllm_adapter/fused_moe.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/rollout/vllm_adapter/fused_moe.py)（`apply` 内 `get_EPLB_args` 触发 token 采集、`torch.unique(topk_ids)` 按 `moe_instance_id` 累计、写 `eplb_token_collects_{rank}.json`）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/workers/resharding/vllm_weight_container.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/workers/resharding/vllm_weight_container.py)（`create_initial_map` 构造初始均匀映射、`_send_receive_redundancy_experts` 按 `eplb_map` 用 `dist.P2POp` + `batch_isend_irecv` 跨卡重分发专家权重）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/config_cls/generate_config.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/config_cls/generate_config.py)（`eplb_token_collects` / `eplb_token_save_path` / `expert_map_path` 三个 generate 配置项，`expert_map_path` 为 None 即不启用）+ [`examples/eplb/`](https://gitcode.com/Ascend/MindSpeed-RL/tree/398fd9a5fa6358c50071db2d09919e414accea90/examples/eplb)（`eplb.sh` num_replicas 512/num_groups 16/num_nodes 16/num_gpus 256、`collect_json_file.sh` scp 汇聚、`grpo_trainer_deepseek_r1_671b_eplb.sh` 16×16 卡启动；配 `configs/grpo_deepseek_r1_671b_A3_eplb.yaml`）

## Links

- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（落地实践：Qwen3-235B 32K 长序列 / 30B RL，EPLB 是其 §2.3 负载均衡优化的一环，真实权重实测无收益）
- [rollout-rebalance](rollout_rebalance.md)（同节 §2.3.1 的负载均衡优化：作用于请求序列维度的长尾均衡，与 EPLB 的专家/节点维度互补）
- [vllm-ascend](../frameworks/vllm_ascend.md)（rollout 推理引擎：EPLB 在 vLLM-Ascend 推理路径上使能，作用于 EP 专家分布）
- [deepseek-r1](../../../inference/concepts/models/deepseek_r1.md)（跨域对照：推理侧 perfect eplb / `force_eplb: True` 强制专家均衡作为峰值吞吐基准条件）
- [moe-load-balance](moe_load_balance.md)（同类 MoE 负载均衡的训练态原生实现：MindSpeed `balanced-moe-experts` 与本机制「复制冗余热专家」同源、`enable-expert-placement` 与「重排专家落卡」同源但不复制）
- [mindspeed-rl](../frameworks/mindspeed_rl.md)（MindSpeed-RL EPLB 实现的承载框架：Ray 训推共卡 RL，rollout 推理走 vLLM-Ascend，EPLB 在其 resharding 阶段重分发专家权重）

<!-- cannbot:related:start -->
## 相关

- [EPLB 专家重映射漏搬独立 scale 张量：per-expert 参数清单缺 scale 致权重/scale 失配、静默掉精度](../../../inference/runbooks/precision/eplb_remap_drops_independent_scale_tensor.md)（`related`）：EPLB 靠一份 **per-expert 参数名清单**（如 `expert_weight_names`）决定「哪些逐专家张量需要随专家一起被搬运/重映射」。；EPLB 的核心目标是通过智能调度策略消除专家模块及计算节点间的负载差异、最大化 NPU 资源利用率。；故障卡给出 EPLB 重映射的参数完整性约束，概念卡解释为何会动态调整专家复制与分配，二者共同支撑触发条件与修复边界。
- [MindSpeed-RL](../frameworks/mindspeed_rl.md)（`related`）：焦点卡写明“EPLB **动态调整专家复制策略与分配方案**”，候选卡写明“EPLB 专家映射则在 `resharding/vllm_weight_container.py`（`eplb_map` / 冗余专家收发）”。概念卡解释动态复制与落卡，框架卡定位 eplb_map 在训推权重重组织中的集成点。
- [MoE 负载均衡（Balanced-MoE 路由均衡 + 专家放置 + Router 修正）](moe_load_balance.md)（`related`）：焦点卡写明“负载均衡时 EPLB 不带收益，仅极端不均才有效”，候选卡写明“EPLB 落地 vLLM-Ascend 在 **RL rollout 推理**侧做专家重分布”。EPLB 卡提供推理判据，训练态卡对照热专家复制与物理迁移语境，帮助选择实现栈。
- [Qwen3 长序列 RL 训练实践（235B-A22B 2K 推 32K + 32B SAM 投机，veRL/MindSpeed/vLLM-Ascend，GRPO/DAPO）](../../guides/recipes/qwen3_rl.md)（`related`）：焦点卡写明“开启 EPLB 无明显性能收益”，候选卡写明“Qwen3-30B/235B 真实权重实测**无明显收益**”。概念卡给出收益判据，Qwen3 实践提供真实权重与极端不均对照，直接支撑启用决策。
<!-- cannbot:related:end -->
