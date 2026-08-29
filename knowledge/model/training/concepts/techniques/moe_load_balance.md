---
type: Concept
title: MoE 负载均衡（Balanced-MoE 路由均衡 + 专家放置 + Router 修正）
description: MindSpeed 训练态 MoE 负载均衡的三套独立机制。balanced-moe-experts（数参互寻）：每层选 N 个热专家（≤本地专家数）把权重广播复制到所有 EP rank，远端热专家 token 改本地副本计算降 All-to-All，热专家用 SharedParamsForHotExperts 共享且 requires_grad_(False)、梯度异步 reduce 回持有者，靠 trans_hot_expert_group_num 份 EP 组并发广播；依赖 moe-fb-overlap+grouped-gemm+alltoall、ETP=1、Dropless、非二进制对齐，EP≥32 且不均才有收益。enable-expert-placement（专家迁移）：EMA(θ=0.9) 预测负载、DP allgather 求均值、贪心打散热专家，按 expert_placement_freq=50 触发，细粒度门控用变异系数(std/mean)下降阈值 0.08 跳过低收益层，专家权重 all2all 互换、router 逆映射重排、优化器状态 allgather+all2all 迁移；须分布式优化器+EP>1。fix-router：patch topk_softmax_with_capacity 用 arange%num_experts round-robin 覆盖真实路由强制均匀，作基准对照。关键术语：热专家复制 vs 物理迁移 vs 路由覆盖、EMA 负载预测、变异系数门控、与 DeepSeek EPLB 同类不同实现（训练态 vs vLLM-Ascend RL rollout 推理）。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/docs/zh/features/balanced_moe.md
  role: supporting
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# MoE 负载均衡（Balanced-MoE 路由均衡 + 专家放置 + Router 修正）

## Summary

MoE 门控网络按 token 内容把样本路由到 top-k 专家，导致各专家收到的 token 数严重分化（热专家过载、冷专家闲置），且冷热身份随数据批次漂移。在专家并行（EP）下，专家固定落卡，这种分化直接变成 device 级负载不均——慢卡拖累整步、出现「快慢卡」，吞吐受限。MindSpeed 在训练态给出三套独立机制，分别从「复制热专家」「物理迁移专家」「确定性路由覆盖」三个角度切入：

- **`--balanced-moe-experts`（Balanced-MoE，「数参互寻」）**：动态识别每层负载最重的 N 个热专家，把它们的参数**广播复制**到所有 EP rank，再把原本要跨卡发往远端热专家的 token 改在**本地副本上算**，从而压缩 All-to-All 通信量；新增的广播 / 梯度归约用算-通重叠与流水线掩盖。这里的「数参互寻」即「数据找计算 + 计算找数据」双向决策。
- **`--enable-expert-placement`（专家放置 / 迁移）**：不复制，而是**物理重排**专家与 device 的映射——用指数滑动平均（EMA）预测各专家负载，贪心地把热专家打散到不同卡，再通过 All-to-All 把专家权重与其优化器状态在卡间互换，并重映射 router 的 topk id。
- **`--fix-router`（Router 修正）**：用确定性的 round-robin 覆盖门控网络的真实 top-k 选择，强制 token 在所有专家上**均匀分布**，给性能/精度对比一个「无路由不均」的基线。

前两套是真负载均衡器（一个靠复制、一个靠迁移），第三套是为基准测试服务的路由覆盖工具。三者均承自 [mindspeed](../frameworks/mindspeed.md) 的 MoE 特性模块，属 [moe-training-optim](moe_training_optim.md) 的负载均衡维度。它们与 [EPLB](eplb.md) 是同一类问题的不同实现——EPLB 页讲 DeepSeek EPLB 落地 vLLM-Ascend 的 **RL rollout 推理**侧，本页讲 MindSpeed 的**训练态**原生三套；`balanced-moe-experts` 与 EPLB 的「复制热专家」思路同源，`enable-expert-placement` 与 EPLB 的「重排专家」思路同源但**不复制**。详见文末对照。

## 现象：专家冷热分化传导为 device 级快慢卡

MoE 训练里专家负载「冷热不均」尤以预训练阶段剧烈——不同 device 上专家处理的 token 数差异大、负载随批次剧烈变化，造成快慢卡问题拖累吞吐。根因有三：输入数据分布的不确定性、router 初始偏好、并发请求的随机性。EP 把专家固定切到各卡后，专家维度的冷热分化就一一映射成 device 维度的利用率失衡。这一现象与 [eplb](eplb.md) 「现象分析」一节同源，区别只在本页观测的是**训练**每步的 device 负载，而非推理 `generate_sequences` 耗时。

## balanced-moe-experts：热专家复制 + 数参互寻

核心是「复制 + 本地化」：每个 MoE 层除常规的 `num_local_experts` 个本地专家外，再建 `balanced_moe_hot_expert_num`（N）个**热专家槽**。前向时从 router 拿到全局 token 分布，选出负载最重的 N 个专家，把它们的权重从「持有者 rank」广播到 EP 组内所有 rank；本该跨卡发往这些热专家的 token 不再走 All-to-All，而是落到本地热专家副本上计算。这样热专家的算力被摊到所有 EP rank，远端通信量随之下降。

热专家参数不是常驻的独立可训练权重：`BalancedMoELayer` 把热专家槽的 `weight1/weight2` 接到一份全局共享参数 `SharedParamsForHotExperts`（单例），并 `requires_grad_(False)`——这样 Megatron 不会为它们分配 `ParamGradBuffer` 和 DP 梯度累加 hook，热专家的梯度改由机制自己管理：每个 rank 用本地 token 算出热专家梯度后，经 `torch.distributed.reduce` **异步归约回持有者 rank**，再并入持有者那份真专家的梯度。热专家权重也不进 checkpoint——`state_dict` 删掉所有 `hot_experts.weight` 键、`load_state_dict` 容忍其缺失。

广播与归约的「持有者」由专家号定位：`src_rank_idx = hot_expert_id // num_local_experts` 取出该热专家所在 rank。为让多个热专家的广播并发起来，`parallel_state` 会**克隆出 `trans_hot_expert_group_num`（M）份 EP 通信组**（`_HOT_EXPERT_GROUP_LIST`），按 `src_rank % M` 轮转选组，使不同热专家的广播/归约走不同通信组并行，缩短传输时间。`BalancedMoELayer.forward` 本身是空的——实际前反向计算走 [moe-fb-overlap](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_feature/balanced_moe/overlap_funcs/fwdbwd.py) 的 overlap 函数，热专家广播被嵌进 micro-batch 的前反向调度里掩盖。

```mermaid
flowchart LR
  R["router 全局 token 分布"] --> H["选 N 个热专家"]
  H --> B["持有者 rank 广播热专家权重<br/>(M 份 EP 组并行, src=id//num_local)"]
  B --> C["各 EP rank 持热专家副本"]
  C --> L["远端热专家 token 改本地副本计算<br/>All-to-All 通信量↓"]
  L --> G["各 rank 本地算热专家梯度<br/>→ reduce 异步归约回持有者"]
```

参数与约束（`balanced_moe.md` 使用限制 + `BalancedMoEFeature.validate_args` 落地校验的部分项）：

- `--balanced-moe-hot-expert-num N`（默认 3）每层维护的热专家数，**必须 ≤ 每 EP rank 本地专家数** `num_local_experts = num_experts / expert_model_parallel_size`；设过大只增广播开销与显存、不增收益，建议 3-8。
- `--trans-hot-expert-group-num M`（默认 3）广播分组数，约束 `1 ≤ M ≤ N`；超过 N 自动夹到 N，超过 `MAX_GROUP_NUM=8` 自动夹到 8。
- 依赖：**必须开 `--moe-fb-overlap` 与 `--moe-grouped-gemm`**（GroupedMatmul）；仅支持 `--moe-token-dispatcher-type=alltoall`（不支持 allgather / alltoall_seq）。
- 并行约束：`--expert-tensor-parallel-size=1`（暂不支持专家张量并行）、需关 `--overlap-grad-reduce`。
- 内存/模型：仅 `--moe-zero-memory=level0`，不支持 `moe-zero-memory-num-layers`；仅 Mcore（关 `--use_legacy_models`）。
- MoE 模式：仅 Dropless，与 `moe_expert_capacity_factor`（Token Drop & Pad）互斥；冲突特性 `--moe-alltoall-overlap-comm` / `--moe-hierarchical-alltoallv` / `--recompute-in-advance` / `--recompute-in-bubble`；不建议叠 `--swap-attention`。
- VPP 下需 `GBS > 1 × DP × PP × MBS`；noop layers 必须置于尾部最后一个 VPP 阶段。
- **非二进制对齐**：token 改本地计算改变了正向计算图路径、热专家梯度跨 rank 并行异步归约改变了累加序，浮点加法无结合律使逐次结果有微小差异；即便设 `--npu-deterministic` 也不保证比特级可复现，需严格确定性的场景不适用。

适用判据与 [eplb](eplb.md) 一致——**EP 规模大（≥32）且负载显著不均**才有正收益；EP≤8 且负载相对均匀时，参数广播等额外开销可能抵消甚至超过均衡收益。DSKv3 减层 4 机 Atlas A3 场景 loss 误差 <1%，但小尺寸模型累加序误差可能被放大、不推荐。

## enable-expert-placement：物理专家迁移（规划器 + 执行器）

与 Balanced-MoE 的「复制」相反，专家放置走「迁移」：周期性地把热专家**打散搬到不同 device**，用热专家混搭抹平 device 级负载，没有冗余副本。分规划器、执行器两半。

**规划器（`planner.py`）** 负责算映射：

- **负载预测**用 EMA（`predict_expert_load`）：`ELP_{t+1} = θ·ELP_t + (1−θ)·EL_t`，θ=0.9——偏重当前负载特征，对变化负载适应快，且迭代式更新不需存历史、计算轻量。
- 迁移前在 **DP 域**（`get_data_modulo_expert_parallel_group`）对预测做 allgather 后取均值（`gather_expert_load_data_parallel`），保证所有 DP rank 的预测与据此算出的分配映射一致。
- **贪心分配**（`ExpertDynamicplacement.expert_placement_greedy`）：每 device 初始 0 专家 0 token；按负载降序取最重专家，分给「专家数未满 `num_experts/num_devices` 且当前 token 最少」的 device，更新后重复直至分完。规划器另备 `expert_placement_dp`（精确 DP）、`expert_placement_mix`（虚拟设备分层）两种算法，执行器当前接的是贪心。

**执行器（`executor.py`）** 在 `curr_iteration % expert_placement_freq == freq−1` 触发（`--expert-placement-freq` 默认 50），按映射迁移：

- **细粒度门控**：`--enable-fine-grained-expert-placement` 开启后，用**负载预测的变异系数**（变异系数 = 标准差/均值，无量纲）衡量迁移收益——比较迁移前后变异系数下降量，低于阈值 `--fine-grained-expert-placement-thre`（默认 0.08）的层**跳过迁移**（`expert_placement_layer_permission=False`），省下不值得的迁移开销；负载稳定的 SFT 阶段尤其受益。关闭则所有 MoE 层按固定频率迁移。
- **专家权重迁移**：`expert_weight_placement` 把本地专家权重按新映射经 `all_to_all` 在 EP（或 tp-extend-ep 的 tp×ep）组内互换。
- **Router 重映射**：`router_weight_placement` / `expert_bias_and_local_token_count_placement` 按 `relative_mapping` 的逆序重排 router 权重、`expert_bias`、`local_tokens_per_expert`，使门控选出的 topk id 跟着专家落卡一起重映射。
- **优化器状态迁移**：对每个 bucket，主参（或 `reuse_fp32_param` 下与 bf16 主参拼回 fp32 的 bf16 残差）、一阶 `exp_avg`、二阶 `exp_avg_sq` 都走「DP 域 allgather 凑齐完整状态 → EP 域 all2all 搬运 → 写回本地切片」，临时缓冲由 `OptimizerStatePlacementMemoryPool` 复用后释放；兼容 `--swap-optimizer`（从 `param_to_cpu_states_map` 取换出到 Host 的状态）。
- `--print-expert-load` 打印每层每 device 的专家负载（min/max/std），开启迁移时还分别打印迁移前后，便于量化不均程度。

支持参数副本复用（`reuse_fp32_param`）、分布式优化器（`use_distributed_optimizer`）、`tp_extend_ep`；要求开分布式优化器、EP>1，且与 `moe_extended_tp` 不兼容。

## fix-router：确定性 Router 覆盖

`--fix-router` 不均衡负载，而是给基准测试一个确定的路由：它 patch `topk_softmax_with_capacity`，在算完 `top_indices` 后用

```python
top_indices = torch.arange(top_indices.numel(), ...).view(top_indices.shape) % logits.shape[-1]
```

把门控选出的专家号整体覆盖成 round-robin——token 按 `0,1,2,…,num_experts−1,0,…` 循环钉到各专家，强制**完全均匀**的专家分配，同时结果确定可复现。它把性能/精度观测从「数据相关的真实路由不均」里剥离出来，相当于构造一个「理想均衡」基线（对照 [eplb](eplb.md) 实验三反向**构造极端不均**来验证 EPLB 收益，本机制是另一端：构造极端均衡）。约束很轻——仅要求 `expert_model_parallel_size > 1`。

## 三套机制对照

| 机制 | 开关 | 思路 | 是否改训练数值 | 关键依赖/约束 |
|---|---|---|---|---|
| Balanced-MoE | `--balanced-moe-experts` | 复制热专家 + token 本地化，降 All-to-All | 是（非二进制对齐） | 须 moe-fb-overlap + grouped-gemm + alltoall + ETP=1；Dropless；EP≥32 且不均才有收益 |
| 专家放置 | `--enable-expert-placement` | 物理迁移专家+优化器状态，热专家打散 | 否（仅重排落卡，数值等价） | 须分布式优化器 + EP>1；EMA 预测 + 变异系数门控（默认 0.08）按频率触发 |
| Router 修正 | `--fix-router` | round-robin 覆盖路由，强制均匀 | 是（覆盖真实路由，仅供基准） | EP>1；基准/对照用，非生产负载均衡 |

三者可独立使用，解决「专家/device 负载不均」的同一目标，但代价与语义不同：复制以广播+显存换通信、迁移以周期性 all2all 换均衡、覆盖只为对照。

## 与 EPLB 的关系

本页三套与 [EPLB](eplb.md) 同属 MoE 负载均衡，但实现栈与语境不同：

- **语境不同**：EPLB 落地 vLLM-Ascend 在 **RL rollout 推理**侧做专家重分布（观测推理耗时与每卡 token），而 balanced-MoE / expert-placement / fix-router 是 MindSpeed 的**训练态**原生实现（观测训练每步 device 负载）。
- **思路对应**：`balanced-moe-experts` 与 EPLB 的「复制冗余热专家」同源——都把热专家多铺几份摊负载；`enable-expert-placement` 与 EPLB 的「重排专家落卡」同源——但**不复制**，纯物理迁移。EPLB 还提供分层/全局双模式与历史负载移动平均估计，本页的专家放置则用 EMA 预测 + 贪心 + 变异系数门控。
- **共识判据**：两侧都指向同一工程结论——负载均衡类优化收益**完全取决于负载是否真不均**，须先量化不均程度（打印每卡专家负载 / 变异系数）再决定是否启用，「开了就快」不成立。

## Evidence

- [mindspeed](https://gitcode.com/ascend/MindSpeed) — [`docs/zh/features/balanced_moe.md`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/docs/zh/features/balanced_moe.md)（数参互寻原理：实时监控/热专家动态选择/参数广播共享/token 分发优化/计算-通信重叠；`--balanced-moe-experts` / `--balanced-moe-hot-expert-num`(默认3,≤本地专家数) / `--trans-hot-expert-group-num`(默认3,1≤M≤N)；使用限制：moe-fb-overlap+grouped-gemm、alltoall、ETP=1、关 overlap-grad-reduce、zero-memory level0、Dropless、冲突特性表、非二进制对齐说明、VPP GBS 约束、EP≥32 推荐场景）、[`docs/zh/features/moe_expert_load_balance_placeemnt.md`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/docs/zh/features/moe_expert_load_balance_placeemnt.md)（专家迁移：规划器（EMA 预测 θ=0.9、DP allreduce 一致、贪心分配五步）+ 执行器（细粒度控制器/变异系数下降 0.08 阈值、专家参数 alltoall 交换、优化器状态 allgather+alltoall 六步）；`enable_expert_placement` / `enable_fine_grained_expert_placement` / `expert_placement_freq=50` / `fine_grained_expert_placement_thre=0.08` / `print_expert_load`；支持 reuse_fp32_param、distributed optimizer、tp_extend_ep）
- [`mindspeed/features_manager/moe/balanced_moe.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/moe/balanced_moe.py) — `BalancedMoEFeature`：参数注册、`validate_args`（N ≤ num_local_experts、M 夹到 N 与 `MAX_GROUP_NUM=8`、EP 规模建议、依赖 moe_fb_overlap/moe_grouped_gemm、仅 alltoall、与 moe_expert_capacity_factor 互斥）、`register_patches`（替换 moe_module_spec 与 initialize_model_parallel）
- [`mindspeed/core/transformer/moe/moe_feature/balanced_moe/modules/moe_layer.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_feature/balanced_moe/modules/moe_layer.py) — `BalancedMoELayer`（`experts` + `hot_experts` 槽、`SharedParamsForHotExperts` 全局共享参数、`requires_grad_(False)` 免 ParamGradBuffer、`state_dict`/`load_state_dict` 剔除 hot_experts.weight、`forward` 为空走 fb-overlap）
- [`mindspeed/core/transformer/moe/moe_feature/balanced_moe/communication.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_feature/balanced_moe/communication.py) — `_groupedmlp_hot_expert_params_broadcast`（`src_rank = hot_expert_id // num_local_experts`、发送/接收判定）、`_multiple_broadcast`（按 `src_rank % trans_hot_expert_group_num` 选组并发广播）、`_groupedmlp_hot_expert_gradient_reduce`（异步 reduce 热专家梯度回持有者）
- [`mindspeed/core/transformer/moe/moe_feature/balanced_moe/parallel_state.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_feature/balanced_moe/parallel_state.py) — `initialize_model_parallel_impl` 克隆 `trans_hot_expert_group_num` 份 EP 组为 `_HOT_EXPERT_GROUP_LIST`、`get_expert_model_parallel_global_ranks`/`get_hot_expert_group_list`
- [`mindspeed/core/transformer/moe/moe_feature/balanced_moe/adaptor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_feature/balanced_moe/adaptor.py) — `get_moe_module_spec_wrapper`（spec 换 `BalancedMoELayer` + fb-overlap experts/shared_experts）、`mindspeed_initialize_model_parallel_wrapper`
- [`mindspeed/features_manager/moe/experts_placement.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/moe/experts_placement.py) — `ExpertsPlacementFeature`：`--enable-expert-placement` / `--expert-placement-freq=50` / `--enable-fine-grained-expert-placement` / `--print-expert-load` / `--fine-grained-expert-placement-thre=0.08` 注册、要求分布式优化器与 EP>1、与 moe_extended_tp 不兼容
- [`mindspeed/core/transformer/moe/expert_placement/planner.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/expert_placement/planner.py) — `predict_expert_load`（EMA `ema_weight=0.9`）、`gather_expert_load_data_parallel`（DP allgather 取均值）、`print_expert_load`、`ExpertDynamicplacement.expert_placement_greedy`/`_dp`/`_mix` 三种分配算法
- [`mindspeed/core/transformer/moe/expert_placement/executor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/expert_placement/executor.py) — `expert_weight_and_optimizer_state_placement`（`curr_iteration % freq == freq-1` 触发）、`initialize_expert_placement_dispatcher`（贪心映射 + 变异系数 std/mean 下降阈值门控）、`expert_weight_placement`（all2all 专家权重）、`router_weight_placement`/`expert_bias_and_local_token_count_placement`（逆映射重排 router）、`relocate_expert_optimization_states`（主参/残差/exp_avg/exp_avg_sq 经 DP allgather + EP all2all 迁移，复用 `OptimizerStatePlacementMemoryPool`、兼容 swap_optimizer）
- [`mindspeed/features_manager/moe/moe_fix_router.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/moe/moe_fix_router.py) — `MoEFixRouterFeature`：`--fix-router` 注册、`validate_args`（要求 EP>1）、patch `topk_softmax_with_capacity`
- [`mindspeed/core/transformer/moe/moe_utils.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/transformer/moe/moe_utils.py) — `topk_softmax_with_capacity` 的 `fix_router` 分支（`top_indices = arange(numel) % num_experts` round-robin 覆盖真实路由，强制均匀分配）

## Links

- [moe-training-optim](moe_training_optim.md)（MoE 训练优化总览：本页三套属其负载均衡维度，与通信重叠 / GMM / zero-memory 等并列）
- [eplb](eplb.md)（同类 MoE 负载均衡：DeepSeek EPLB 落 vLLM-Ascend RL rollout 推理侧；balanced-moe-experts 与其「复制热专家」同源、enable-expert-placement 与其「重排专家」同源但不复制）
- [mindspeed](../frameworks/mindspeed.md)（三套机制所在框架：MoE 特性模块 features_manager/moe 下的 balanced_moe / experts_placement / moe_fix_router）

<!-- cannbot:related:start -->
## 相关

- [EPLB（专家并行负载均衡器，MoE 专家动态负载均衡）](eplb.md)（`related`）：焦点卡写明“负载均衡时 EPLB 不带收益，仅极端不均才有效”，候选卡写明“EPLB 落地 vLLM-Ascend 在 **RL rollout 推理**侧做专家重分布”。EPLB 卡提供推理判据，训练态卡对照热专家复制与物理迁移语境，帮助选择实现栈。
- [MoE 训练优化（TP-Extend-EP / Zero-Memory / GMM 分组矩阵乘 / Shared-Experts）](moe_training_optim.md)（`related`）：三者均承自 ［mindspeed］(../frameworks/mindspeed.md) 的 MoE 特性模块，属 ［moe-training-optim］(moe_training_optim.md) 的负载均衡维度。；共性是都把优化压在专家层这一 MoE 训练最贵的环节：TP-Extend-EP 还专家 GEMM 一个完整权重、GMM 合多专家为一个算子、Zero-Memory 把激活换成可掩盖的重算/重通信、共享专家用并行计算与参数复用降冗余。专家负载在专家间是否均衡由路由侧的负载均衡机制决定，见 ［moe-load-balance］(moe_load_balance.md)。。负载均衡卡处理路由侧专家分配，训练优化卡处理专家层计算与内存，两者在同一 MoE 训练链上互补且明确互引。
<!-- cannbot:related:end -->
