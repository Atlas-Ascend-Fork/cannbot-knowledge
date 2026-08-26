---
type: Concept
title: Rollout Rebalance（RL On-Policy rollout 序列级均衡调度引擎）
description: RLHF 的 rollout（数据生成）阶段面临典型的「木桶效应」：同一批 prompt 生成的 response 长度呈长尾分布，少数极长的生成任务远超普通任务耗时，拖慢整个 DP 组的同步进度；先完成短序列的卡只能空转等待，造成算力浪费。Rollout Rebalance 是 cann-recipes-train 在 vllm-ascend 推理引擎内实现的一套序列级均衡调度引擎：在每个推理 Step 前周期性感知全局 DP 组负载，当检测到组间负载不均满足条件时，主动把单个请求（Sequence，含其 KVCache）在 rank 间迁移、重排，配合 vLLM-Ascend 的多档位编图能力让全局尽快切换到更小 BatchSize 档位（更低 TPOT），从而提升进入长尾状态后的整体推理效率。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Rollout Rebalance（RL On-Policy rollout 序列级均衡调度引擎）

## Summary

RLHF 的 rollout（数据生成）阶段面临典型的**「木桶效应」**：同一批 prompt 生成的 response 长度呈**长尾分布**，少数极长的生成任务远超普通任务耗时，拖慢整个 DP 组的同步进度；先完成短序列的卡只能空转等待，造成算力浪费。**Rollout Rebalance** 是 cann-recipes-train 在 [vllm-ascend](../frameworks/vllm_ascend.md) 推理引擎内实现的一套**序列级均衡调度引擎**：在每个推理 Step 前周期性感知全局 DP 组负载，当检测到组间负载不均满足条件时，主动把**单个请求（Sequence，含其 KVCache）**在 rank 间迁移、重排，配合 vLLM-Ascend 的**多档位编图**能力让全局尽快切换到更小 BatchSize 档位（更低 TPOT），从而提升进入长尾状态后的整体推理效率。

Rollout Rebalance 由环境变量 `ROLLOUT_REBALANCE_ENABLE` + `RolloutRebalanceConfig` 控制：先做条件检测与调度策略生成，再做序列级数据搬迁与 KVCache 恢复，最后还原结果。它由 [verl](../frameworks/verl.md) 前端发起、跑在 [qwen3-rl](../../guides/recipes/qwen3_rl.md) 实践上，Qwen3-235B 64 卡 A3 单轮推理耗时降约 60%，与同样针对长尾的 [length-aware-resampler](length_aware_resampler.md) 互补。

## 为什么 rollout 长尾是负载均衡问题

rollout 长尾的本质是 RL 训练系统的负载均衡问题：

> RLHF的Rollout阶段面临典型的"木桶效应"：由于输入Prompt所生成的响应（Response）长度存在长尾分布，少数极长的生成任务会拖慢整个DP组的进展。这使得处理短序列的节点在完成计算后不得不进入长时间的闲置等待，造成算力浪费。长尾问题优化的本质是RL训练系统的负载均衡，对此，我们针对单轮推理的同步场景，优化目标是提升进入长尾状态后的推理效率。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image15.png" width="55%"></p>
<p align="center"><sub>图：rollout 长尾「木桶效应」——少数长序列任务拖慢整个 DP 组，短序列节点完成后空转等待（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>）</sub></p>

在 [grpo-dapo](grpo_dapo.md) 这类**单轮推理同步**（on-policy）场景下，整组必须等最慢的长尾序列推完才能进入下一轮，故优化目标不是缩短单条最长序列，而是**让全局尽快进入低档位高效状态**。

## 初始化与配置项

### 初始化使能

在 `verl/workers/megatron_workers.py` 文件开头追加以下代码，通过环境变量 `ROLLOUT_REBALANCE_ENABLE=1` 使能本特性：

```python
from patches.verl.features.rollout_optimize import init_rollout_rebalance
init_rollout_rebalance()
```

### 配置项 `RolloutRebalanceConfig`

可直接在 `config.py` 中修改，或把以下配置写入 verl 启动的 yaml、在初始化位置提取并传入 `init_rollout_rebalance`：

```python
class RolloutRebalanceConfig:
    enable = int(os.environ.get("ROLLOUT_REBALANCE_ENABLE", "0"))  # RolloutRebalance特性总开关
    check_interval = 1000  # 间隔多少个step进行一次rebalance检查

    multi_graph = True  # 是否开启多档位编图，如果关闭，rebalance依然会按预编图的档位做均衡调度，但是不会形成明显的性能收益
    graph_batch_sizes = [64, 32, 16, 8, 4]  # 预编图的档位设置

    profile = True  # 是否打印过程中的性能数据
    profile_interval = 100   # 打印间隔步长
```

关键点：`multi_graph` 关闭后 rebalance 仍会按预编图档位做均衡调度，但**不会形成明显性能收益**——多档位编图是 rebalance 收益的前提依赖。

### 前置依赖：vLLM-Ascend 多档位编图

[vllm-ascend](../frameworks/vllm_ascend.md) 在 `torchair_graph_config` 中提供 `use_cached_graph` 和 `graph_batch_sizes`，支持提前配置多档位 BatchSize 的图（如 64/32/16/8/4），随剩余序列减少自动匹配更小 BatchSize 的图进行推理。图模式下 Qwen3-235B 默认 TPOT 会从 125ms 上升到 200ms，而开启 Rebalance + 多档位编图后能在 **1~2K 推理长度**时就快速降低推理档位，把单 step TPOT 降到 **60ms** 量级，长尾场景下差距被持续放大。

## 实现方案

核心目标是：在 On Policy 场景中，针对部分 Rollout 提前结束导致各 rank 间负载不均时，对未结束的 Rollout 进行负载均衡的策略分析和重调度，包含三个关键功能：

1. **Rebalance 条件检测与调度策略生成**；
2. **Request(SEQ) 级的数据搬迁与恢复**（含对应 KVCache）；
3. **Rollout 后的结果还原**。

为什么把逻辑放在 vLLM 内层而非 verl 外层：verl 调用 vLLM 存在两个循环——**外层循环**按 Epoch 加载数据集，**内层循环**是 vLLM 接收单批请求后的推理循环；关键的「DP 组推理进度」信息**只能在内层循环精确感知**，故在每个推理 Step 前追加「负载均衡检查 + Rebalance 调度」环节。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image17.png" width="55%"></p>
<p align="center"><sub>图：在 vLLM 内层推理循环每个 Step 前追加「负载均衡检查 + Rebalance 调度」，实现推理任务的实时动态均衡（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>）</sub></p>

### 全局状态感知

每个 rank 周期性向全局共享调度器核心状态（请求队列深度 running/waiting、KVCache 使用率），经 HCCL 在 DP 组间用 `all_gather_object` 同步：

```python
def get_current_state(self):
    return dict(
        rank=self.rank,
        req_ids=list(self.llm_engine.output_processor.request_states.keys()),
    )

def sync_group_states(self):
    if self.world_size == 1:
        return [self.get_current_state()]
    group_states = [None for _ in range(self.world_size)]
    dist.all_gather_object(group_states, self.get_current_state(), group=self.dp_group)
    return group_states
```

DP 组间状态同步开销 **< 2ms**；为平衡「调度及时性」与「性能开销」，引入可配置周期检测（伴随 step 计数 / 异步线程周期；`check_interval` 默认每 1000 step 检测一次）。

### 基于档位预设的「最大档位最小化」均衡算法

`calc_balancing_tasks` 计算最优请求迁移清单，docstring 给出三层目标：

> 1. 主要目标：将整个DP组所需的最大档位(max_bs)降至最低。
> 2. 次要目标：在满足1的前提下，使迁移的请求数量(cost)最少。
> 3. 补充目标：在满足1和2的前提下，使得各个rank间的数据搬迁流向尽可能均匀，避免多对一阻塞。

该算法采用**两阶段均衡调度**：**阶段一**先解决「忙闲不均」——把 Waiting 队列积压任务从高负载 rank 迁到有空闲容量的 rank（`need_kv_cache=False`，因尚未运行无 KVCache）；**阶段二**仅当**全局所有 DP 组**都满足「最大档位可下降」时才触发，对 Running 任务做迁移（`need_kv_cache=True`），用「全体一致」原则避免局部优化引发的频繁 KVCache 搬运。算法约束：选目标时**最小化点对点连接**（优先一次完成多任务交换的节点对）、**避免「多对一」拥塞**。

`calc_balancing_tasks` 的具体决策规则落实上述三层目标，是该均衡算法的核心：

- **目标档位选择**：`max_bs_next = min(当前最大档, graph_batch_sizes[0], scheduler.max_num_running_reqs)`，再从档位表逆序取满足 `avg_bs ≤ target_bs < max_bs_next` 的**最小档**（"够用的最小档"，`avg_bs` 为 DP 组各 rank `running+waiting` 的均值）。仅当该档**严格小于**当前最大档（`max_bs_next < max_bs_before`）时阶段二才迁移 Running 任务，否则不动。
- **接收方资格与容量**：有 Waiting 积压的 rank 只作 donor 不作 receiver；**KVCache 占用率 `block_usage > 0.8` 的 rank 直接跳过**（自身濒临 OOM、不接收）；其余 rank 接收容量 `capacity = min(max_bs_next − running, int(running·(1−usage)/usage))`——按当前 KVCache 占用反推「还能再纳入多少请求而不爆显存」，与「填到目标档位还差多少」取小。
- **流向均匀**：阶段二先把 receiver 按 `capacity` 降序遍历（`sorted(receivers, key=lambda r: r['capacity'], reverse=True)`，优先填满容量最大的接收方以减少点对点连接数），再把多个 donor 的盈余按 `donor_index = (donor_index+1) % len(donors)` 轮转分给各 receiver，从机制上落实「搬迁流向均匀、避免多对一」。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image16.png" width="55%"></p>
<p align="center"><sub>图：verl 调用 vLLM 的外层（Epoch 数据集）/ 内层（单批请求推理）双循环——DP 组推理进度只能在内层循环精确感知（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>）</sub></p>

### 序列请求的跨 Rank 发送/接收（含 KVCache）

迁移用 HCCL 的 `all_to_all_single` 一次性完成请求元信息（req_id、已输出 tokens 等）交换，再对需迁移 KVCache 的请求建独立 Send/Recv 点对点通信。发送侧把请求 `pickle` 序列化为 uint8 张量、两次 `all_to_all_single`（先换 size 再换数据），并 `trigger_abort()` 在源 rank 撤下请求：

```python
def all_to_all_v_tasks(self, schedule_tasks):
    objects_to_send = [[] for _ in range(dist.get_world_size())]
    send_tasks = []
    for schedule_task in schedule_tasks:
        if self.rank != schedule_task['from_rank']:
            continue
        for request in [*self.scheduler.running, *self.scheduler.waiting][-schedule_task['num_to_move']:]:
            request_task = RebalanceRequestTask(self.llm_engine).load_by_req_id(request.request_id,
                            schedule_task['need_kv_cache'])
            send_tasks.append((request_task, schedule_task['to_rank']))
            objects_to_send[schedule_task['to_rank']].append(request_task.get_transfer_dict())
            request_task.trigger_abort()
    # ... 两次 dist.all_to_all_single 交换 size 与序列化数据 ...
    self.send_kv_caches(send_tasks)
    self.load_received_tasks(received_tasks)
```

KVCache 按 block 逐层 `dist.send` / `dist.recv` 搬迁；接收方利用 vLLM 的请求与 BlockTable 管理机制，在本地 NPU 上精准还原 KVCache 状态，使任务无缝在新节点续推（`send_kv_caches` / `load_received_tasks`）。对 Running 任务的 KVCache **须随之迁移**，否则搬迁后 rePrefill 会带来较大负向开销。

### 对外无感知的结果还原

所有 Worker 推理完成后执行一次统一 All2All，把被迁移任务的最终结果**准确传回其原始 rank**——从外部 verl 框架看，请求处理流程与未发生调度时完全一致，实现真正的无感知调度。

## 收益评估

### 理论模拟

通过 OpenR1-Math-220K 答案长度作为推理输出长度、结合各 BS 档位 TPOT，预估「多档位编图」+「Rebalance」收益：单独开启多档位编图，BatchSize 档位要推到 **16K** 长度才开始下降；额外开启 Rebalance 后档位下降时机提前到 **6K**。综合：单独多档位编图 4%~8% 收益，结合 Rebalance 后整体可达 **15%~17%**（Rebalance 在多档位基础上额外贡献 9%~14%）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image18.png" width="55%"></p>
<p align="center"><sub>图：多档位编图 + Rebalance 的理论性能收益模拟——Rebalance 把 BatchSize 档位下降时机从 16K 提前到 6K（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>）</sub></p>

### 实测效果

**主结果**：Atlas A3 集群 **64 卡**、Qwen3 235B、deepscaler、`train_batch_size=512` / `max_response_length=32768` / `rollout.n=16` / `TP=4` / `DP=32`，开启后单轮推理耗时从约 **10200s** 优化到约 **6100s**，**性能收益约 60%**。

**实验 2**（128Die、Qwen3-235B、Deepscaler、TP4/DP32/EP128、多档位 256/128/64/32/16/8/4）：

| 优化 | generate_sequence/s | Rollout 性能提升 |
|------|---------------------|------------------|
| base 配置（verl 默认） | 10213 | - |
| 单独开启多档位编图 | 7841 | 30% |
| 多档位编图 + Rollout Rebalance | 6102 | 67% |

**实验 1**（早期穿刺，DeepSeekV3、256Die、OpenR1-Math-220K、TP2/DP128/EP256、多档位 64/32/16/8/4）：verl 默认 6482s → 多档位编图 2861s（+56%）→ 多档位 + Rebalance 2291s；与基线相比共 **64%** 提升，Rebalance 在多档位基础上额外贡献 **20%**。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image19.png" width="55%"></p>
<p align="center"><sub>图：DeepSeekV3 / 256Die 穿刺实验——红线 verl 默认、橙线多档位编图、绿线多档位+Rebalance，绿橙曲线间面积即 Rebalance 额外收益（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md">Qwen3-235B RL 优化文档（图源）</a>）</sub></p>

> 收益强依赖数据集长尾分布：若数据本身或经 data balancing 已较均衡，Rebalance 额外收益会降低。Rebalance 同时支持「大 EP 部署的单实例内负载均衡」与「多实例场景的跨实例负载均衡」。

## DataBalance：输入数据重排序（互补的离线侧均衡）

Rollout Rebalance 在 vLLM **推理过程中**动态迁移序列；与之互补的 **DataBalance** 则在 prompt **分发之前**重排输入数据，从源头降低 DP 域间负载不均。二者同属负载均衡优化，常叠加使用。

### Roofline 依据（为何要提 BS + 为何要均衡）

Roofline 模型描述理想情况下算子执行耗时受计算量与访存量影响：固定访存量，设备计算吞吐随**计算强度**提升呈「先线性上升后趋于平稳」。对 Matmul/GroupedMatmul，其计算强度恰为输入左矩阵的 bs 维度大小，理论上可通过提升 bs 提升整网 Matmul 计算吞吐；而 **FIA 算子因每个 bs 维度拥有独立 KV Cache 缓存，其计算强度不随 bs 增长而变化**。RL 所依赖的离线推理只关心一批给定数据的端到端完成耗时，不受在线推理 SLO（如 TPOT）制约，故无需顾虑大 bs 带来的单 token 时延上升——这为「提 BS + DataBalance」的离线侧组织方式提供了理论依据。

基于访存 bound 友好的 TP4DP32EP128 切分，逐步扩大推理 batch size，Deepscaler 数据集实测**首 DP 空闲时间占比**诊断如下：

| GBS | 实际推理 BS | 推理总耗时 | 首 DP 完成时间 | 首 DP 空闲时间 | 首 DP 空闲时间占比 |
|-----|------------|-----------|---------------|---------------|-------------------|
| 256 | 24  | 02:27:11 | 01:08:53 | 01:16:18 | 50.84% |
| 256 | 64  | 01:22:32 | 00:40:57 | 00:41:35 | 50.38% |
| 256 | 128 | 01:18:18 | 00:27:32 | 00:50:46 | 64.84% |

- BS 提升初期（24→64）：首 DP 完成时间与推理总耗时均明显下降——契合 Roofline，访存 bound 阶段提升计算强度可在相近时间内完成更多数据批次，提示离线推理应选最优 BS 充分利用算力。
- BS 进一步扩大（64→128）：首 DP 完成时间进一步降低，但**推理总耗时仅降 5%、几乎未变**——结合 MoE 大 EP 部署下各 DP 锁步执行的特性，表明各 DP 间数据生成长度差异显著，**部分卡在超过 64% 的时间里处于空闲**，提示同步 RL 场景必须缓解推理数据集负载不均，避免长尾导致的巨大算力浪费。

### DataBalance 方案与收益

veRL 默认把推理 prompt 数据按采样数 n 复制后**作相邻排布**，使各 DP 域处理完全不同的 prompt——当倾向生成长回复与倾向生成短回复的 prompt 被分到不同 DP 域时，便出现极严重负载不均。**DataBalance** 改为把 prompt 按采样数 n 复制后**作间隔排布**，尽可能把各 prompt 均匀分散到不同 DP 域；训练阶段开始前再按原方式重排 response，保证同一条 prompt 的不同采样结果仍彼此相邻。

prompt 排布调整后，BS128 配置下推理长尾大幅改善、各 DP 域负载更均衡，端到端时延 **-25%**；缓解长尾瓶颈后又为进一步扩大 BS（128→192→256）提升吞吐创造空间：

| GBS | BS | 推理吞吐 | 推理总耗时 | 首 DP 完成时间 | 首 DP 空闲时间 | 首 DP 空闲时间占比 |
|-----|----|---------|-----------|---------------|---------------|-------------------|
| 256 | 128 | 92 | 01:18:18 | 00:27:32 | 00:50:46 | 64.84% |
| 256 | 128(DataBalance) | 132 | 00:58:03 | 00:43:38 | 00:14:25 | **24.83%** |
| 384 | 192(DataBalance) | 160 | 01:10:00 | 00:57:17 | 00:12:43 | 18.16% |
| 512 | 256(DataBalance) | 186 | 01:21:54 | 01:08:33 | 00:13:21 | 16.30% |

> 即首 DP 空闲时间占比从 64.84% 被 DataBalance 压到 **24.83%**（推理吞吐 92→132，源表此列仅标「推理吞吐」未给单位，疑为 TPS/卡），再叠加 BS 提升后空闲占比降至 16.30%、吞吐升至 186。

### 与 Seer（Kimi/清华）方案的对比

月之暗面 & 清华《Seer: Online Context Learning for Fast Synchronous LLM Reinforcement Learning》（arXiv 2511.14617）的多项长序列 RL 优化与本实践高度契合，对比如下：

- **KV Cache 跨实例不均**：Seer 基于 **Mooncake** 构建 DRAM/SSD **两级 KV Cache 池**，允许跨实例迁移请求 chunk 时无需 Prefill 重算——与本实践 Rollout Rebalance 的「序列含 KVCache 迁移、避免 rePrefill」实现了类似功能。
- **Divided Rollout**：Seer 把长序列请求切成多个子块、每块最多推理 8K token，推完放回缓存池再分配给其他实例直到推理完毕——是对 continuous batching 场景非常有效的加速方案，解决 OOM 与中途 preempt 风险；**未来对 Device 侧内存不够的场景使用该方案将带来很大收益**。本实践则通过分析推理侧实际内存、配置合适 `max_num_seqs` 不触发 continuous batching，对长尾问题的解决**更加有效**。
- **Longest-First Scheduling**：Seer 基于「同一 group 内不同输出长度高度相关」，先从每个 group 选一个 prompt 组成「探测响应」实时估计该组其余请求长度，再执行近似 **Longest-First Scheduling** 优先推理长文本，显著压缩长尾。
- **同一 group 输出长度强相关**：Seer 据此把一组 prompt 请求进一步切 chunk 调度到最空闲实例，实现实例间均衡。**本实践 DataBalance 的差异**：无需在实例间做请求调度，仅需在 prompt 分发前按采样数 n 复制后**作间隔排布**即可实现类似效果，实现非常简单；虽当前实践仅一个实例、在 DP 域间实现 data balance，未来也可方便扩展到多集群多实例方案。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/features/rollout_rebalance.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/features/rollout_rebalance.md)（§1 简介/木桶效应；§2.1 `init_rollout_rebalance` 初始化使能；§2.2 `RolloutRebalanceConfig` 配置项；§3 实现方案：前置依赖多档位编图、全局状态感知 `sync_group_states`、最大档位最小化算法 `calc_balancing_tasks`、跨 rank `all_to_all_v_tasks` + KVCache send/recv 与恢复；§4 使能效果 64 卡 A3 单轮推理 10200s→6100s ~60%、TPOT 200ms→60ms）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md`（§2.3.3 输入数据重排序 DataBalance + Seer 对比）](https://gitcode.com/cann/cann-recipes-train/blob/ece44cf36b1a980649a0ca9931d2695eb8e27e8f/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md)（Roofline 依据 / 首 DP 空闲时间占比诊断表 GBS256 BS24-64-128：50.84%/50.38%/64.84%；DataBalance 间隔排布把空闲占比压到 24.83%、端到端 -25%、BS 128→192→256 吞吐 92→132→160→186；Seer Mooncake 两级 KV 池 / Divided Rollout 8K chunk / Longest-First Scheduling 对比）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/qwen3_235B_32k_longseq_rl_train_optimization.md)（§2.3.1 RL rollout 长尾负载不均场景优化：内外层双循环、关键设计点 1 周期检测 <2ms、关键设计点 2 两阶段调度、关键设计点 3 序列迁移 All2AllSingle + KVCache 点对点、关键设计点 4 无感知结果还原；理论模拟 15%~17%；实验 1 DSV3 256Die +64%/Rebalance 额外 20%、实验 2 Qwen3 128Die 10213→6102s +67%；与 Seer 论文长尾优化对比。注：实验 2 项目符号写 `TP=4/DP=32/EP=128`，紧随的结果表「模型切分」列却写 `TP4 PP4 CP4 EP32`，源内 EP 标注不一致，本页取项目符号侧 EP128）
- 代码符号：`verl/workers/megatron_workers.py`、`patches/verl/features/rollout_optimize.py`、`config.py`、`rollout_rebalance.py`（`calc_balancing_tasks` / `all_to_all_v_tasks` / `send_kv_caches` / `load_received_tasks`）

## Links

- [verl](../frameworks/verl.md)（RL 前端：Rollout Rebalance 由 verl 发起、patch 注入 `megatron_workers.py`，on-policy 单轮同步语义来源）
- [vllm-ascend](../frameworks/vllm_ascend.md)（推理引擎 + 多档位编图（`torchair_graph_config` 的 `use_cached_graph`/`graph_batch_sizes`）能力的承载者，本特性的前置依赖）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（承载实践：Qwen3-235B 32K 长序列 GRPO，64 卡 A3，Rebalance 贡献单轮推理 -60%）
- [length-aware-resampler](length_aware_resampler.md)（同样针对 rollout 长尾的负载均衡技术，与推理时动态迁移互补）
- [grpo-dapo](grpo_dapo.md)（本特性服务的 on-policy RL 算法：单轮推理同步场景才有「整组等长尾」问题）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — Rollout Rebalance 特性 + Qwen3-235B 长序列 RL 优化实践
- [eplb](eplb.md)（同属负载均衡:EPLB 专家级 vs rollout 序列级）
- [partial-rollout](partial_rollout.md)（互补的长尾处理：partial rollout 时间维截断续跑、本页空间维带 KV 搬迁重排）
