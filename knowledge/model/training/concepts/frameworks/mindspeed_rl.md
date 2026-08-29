---
type: Concept
title: MindSpeed-RL
description: >-
  MindSpeed-RL 是昇腾 RL 后训练框架，包含原生 mindspeed_rl 和以运行时 patch 适配上游 verl 的 verl_npu。
  原生路径用 Ray 编排 Megatron 训练态与 vLLM 推理态；IntegratedWorker 让 actor、reference 和 reward
  分时复用同批 NPU，LoRA share_backbone 时 reference 通过关闭 adapter 得到基座输出，共卡模式不支持
  独立 reward 资源。Actor 在 generate、infer-logprob 和 train 之间用显式状态机切换，由 sharding manager
  重切分训练与推理所需的不同 TP/PP/EP 布局，空闲模块可卸载到 Host。各 Ray worker 通过
  TransferDock 与 ZMQ 交换数据，框架支持 GRPO、DAPO、PPO 和 DPO。
tags:
- task.implementation
- topic.architecture
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/features/integrated_worker.md
  role: supporting
created_at: '2026-06-24T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MindSpeed-RL

MindSpeed-RL 是昇腾 NPU 的 **RL 后训练加速框架**，支持 GRPO / DAPO / PPO / DPO。它以 Ray 编排 Megatron 训练态与 vLLM 推理态的**训推共卡混合引擎**，用显式的训推态切换接口与分层配置体系驱动一轮 RL 迭代，并提供两条并行代码线（原生 `mindspeed_rl` + `verl_npu`）。在线重切分细节、partial-rollout、TransferDock 数据调度见 [train-rollout-switch](../techniques/train_rollout_switch.md)；GRPO/DAPO 算法见 [grpo-dapo](../techniques/grpo_dapo.md)。

## 两条并行代码线

仓库同时提供两套互不依赖的昇腾 RL 路径，共用 vLLM 推理后端（[vllm-ascend](vllm_ascend.md)）：

1. **原生 `mindspeed_rl/`** —— 基于 Ray 编排的 **Megatron 训练态 + vLLM 推理态训推共卡混合引擎**。训练侧基于 [mindspeed](mindspeed.md)/Megatron。
2. **`verl_npu/`** —— 给上游 [verl](verl.md) 打昇腾 patch 的非侵入适配层。

## 训推共卡混合引擎

### 全共卡部署（Integrated Worker）

主推部署形态是**全共卡**：Actor / Reference / Reward 三角色**分时复用同一批 NPU**，交替计算，空闲数据卸载到 Host 内存。落地为 `IntegratedWorker`（`workers/integrated_worker.py`），它**多继承** `ActorHybridWorkerBase + ReferenceWorkerBase + RewardWorkerBase`，以 Actor 为主 worker。**`share_backbone` 是 LoRA 场景专用开关**：开启时 reference 与 actor 共用同一份 base 权重（`ref_model = self.model`、`ref_manager = self.actor_offloader`），reference forward 通过 `disable_adapter()` 关闭 LoRA 适配器即得基座输出，故不需单独加载/卸载 ref 权重；关闭时（全量微调）单独加载 ref 权重并默认 offload。Reference forward 仅当配了 `ref_forward_micro_batch_size` 时用 `temporary_micro_batch_size` 上下文临时改 mbs；`share_backbone=False` 时算完 `offload_param()` 释放显存。

`use_integrated_worker=true`（默认开）下 `validate_config.validate_rl_args` 强制：未配 `reference_resource` 时**强制复用** `actor_resource`；而配置 `reward_resource` 直接**报错**（共卡态不支持独立 reward 模型——规则奖励由 `RewardWorkerBase` 提供，不另占资源）。`actor_resource.num_npus` 即全共卡总卡数。`integrated_mode_config.ref_model_load_path` 支持续训时单独加载 ref 权重。

### 训推共卡 Actor（ActorHybridWorker）

Actor 在一轮内**串行**经历 generate→infer-logprob→train 三态，核心成员（`workers/actor_hybrid_worker.py::ActorHybridWorkerBase.initialize`）：

- `model` / `optimizer` —— 训练态，Megatron 实现；
- `inference_model` —— 推理态，`VLLMInferEngine`（`_build_rollout`）；
- `sharding_manager` —— `MegatronShardingManager`，负责训→推权重重切分 + 显存编排；
- `actor_offloader` —— `MegatronOffLoader`，按 `offload_train_optimizer/grad/param` 分别卸载优化器/梯度/权重。

训推态切换是一组**显式状态机接口**（`MegatronShardingManager`），Actor 用 `ActorState{NONE,INFER}` 跟踪并打 `timing/resharding_*` 指标：

| 接口 | 语义（before→after） |
|---|---|
| `enter_infer_mode` | onload 推理权重 → 从训练权重重切分出推理权重 → offload 训练权重（`train_param_offload` 时）→ `sync_model_weights(load_format='megatron')` 灌权重，给 KV Cache 腾显存 |
| `exit_infer_mode` | offload 推理权重（还原 cpu_model、清 MLA 缓存权重 w_kc/w_vc/W_UV）+ 销毁推理 weight buffer |
| `enter_train_mode` | onload 训练权重 + 优化器 + 梯度 |
| `exit_train_mode` | offload 优化器 + 梯度（权重保留） |
| `enter/exit_forward_mode` | logprob 阶段只 onload/offload 训练权重，不动优化器 |

`generate_sequences` 进出包裹 `enter/exit_infer_mode`（仅 `not filter_groups_enable` 时；动态过滤模式下重切分由外层托管）；`update` 包裹 `enter_train_mode`。该设计可对**训练态（大 TP/PP、小 EP）与推理态（小 TP/PP、大 EP）配不同并行**，配合在线 EP→TP 重切分缓解 MoE 大权重 OOM（细节见 [train-rollout-switch](../techniques/train_rollout_switch.md)）。

## Ray 角色编排

Worker 都是 Ray actor：`@ray.remote(resources={"NPU": 0.7})` 标注的 `IntegratedWorker` 由 Ray placement group 调度，每 worker 从 `WORLD_SIZE`/`RANK` 环境变量与 `ray.get_runtime_context().get_accelerator_ids()["NPU"][0]` 取首卡 `set_device`（`base_worker.py::BaseRayWorker`）；`MASTER_ADDR/PORT` 仅在 `MASTER_ADDR=='localhost'` 时自协商（取本机 IP + 空闲端口），否则沿用环境变量。角色间经 **TransferDock**（Ray actor 数据队列，`init_transfer_dock` 注入引用）与 **ZMQ**（`zmq_communication=true` 时 dispatch 数据）通信；`num_cpus_for_placement_group` / `num_cpus_for_local_task` 控 Ray CPU 配额。非共卡分离模式下 `actor/reference/reward/critic/vit_resource` 各自申请独立 NPU 组。

## vLLM 推理引擎适配

`models/rollout/vllm_engine.py::VLLMInferEngine`（继承 `BaseInferEngine`）封装 vLLM `LLM`，按 `infer_{tensor,pipeline,expert}_parallel_size` 独立配置推理并行，喂 `SamplingParams`。关键适配在 `models/rollout/vllm_adapter/`：

- **megatron weight loaders**（`megatron_weight_loaders.py`）：`load_format='megatron'`，按模型族（llama/qwen 等）把 Megatron 分片权重在线灌进 vLLM 模型，含 QKV fused 拆分；EPLB 专家映射则在 `resharding/vllm_weight_container.py`（`eplb_map` / 冗余专家收发），二者配合完成训→推权重重组织。
- **acl graph**：`enforce_eager` 控是否禁用 ACL graph，另有 `torchair_graph` 开关（[vllm-ascend](vllm_ascend.md) 提供 NPU 后端与图模式）。
- `vllm_parallel_state.py` / `engine_core.py` / `fused_moe.py`：vLLM 昇腾并行状态、引擎核心与 fused-MoE 适配。

## 分层配置体系

配置拆成多个 `BaseConfig`（`config_cls/base_config.py`，dataclass 风格、`update()` 把 YAML dict 注入、未注册 key 直接报错），按职责分层：

| Config 类 | 文件 | 职责 |
|---|---|---|
| `MegatronConfig` | `megatron_config.py` | 训练态：`global_batch_size` / `micro_batch_size` / `tensor·pipeline·expert_model_parallel_size` / `stage` |
| `GenerateConfig` | `generate_config.py` | 推理态：`infer_*_parallel_size` / `gpu_memory_utilization` / `offload_train_*` / `enforce_eager` / `torchair_graph` / `sampling_config` |
| `RLConfig` | `rl_config.py` | RL：`*_resource` 角色卡数、`adv_estimator`/`kl_*`/`clip_*` 算法超参、`use_integrated_worker`、各阶段 `*_dispatch_size` |
| `ValidateConfig` | `validate_config.py` | 跨配置一致性校验（共卡资源约束、CP 算法、DP 整除等） |

**batch_size 语义**（三级）：`micro_batch_size`=单次 forward 单卡批；`mini_batch_size`=PPO 更新粒度，构造时乘 `n_samples_per_prompt`（`rl_config.py` 末行 `mini_batch_size = config_dict.get('mini_batch_size', 1) * n_samples_per_prompt`），按 DP world size 切成 `mini_batch_size_per_dp`；`global_batch_size`=跨 DP 全局批。`actor_forward_micro_batch_size` / `ref_forward_micro_batch_size` / `vit_forward_micro_batch_size` 允许在 logprob/ViT 阶段单独覆盖 mbs。各阶段 `*_dispatch_size`（`actor_rollout_dispatch_size` / `ref_dispatch_size` / `actor_update_dispatch_size` …）控每个 forward step 从 TransferDock 取的 experience 条数。

## verl_npu 适配线

`verl_npu/`（独立子包）以**运行时 monkey-patch** 方式给上游 verl 打昇腾适配，不改 verl 源树：`import verl_npu` 即触发 `_initialize_npu_plugin()`→`apply_npu_plugin()`（`plugin.py`）。机制：`patch_summary.yaml` 声明各依赖（verl / vllm / vllm_ascend / megatron-core / mindspeed / transformers / mbridge）的 **commit_id + patch 目录**，`apply_repo_patches` 先校验已装版本 commit 匹配，再 `patch -p1 -N` 逐个打 `.patch`（已打过自动跳过），`after_patch_check` 回查新增行是否落地；另含 tensordict NPU 同步 hook 修精度。patch 覆盖 `main_ppo`/`main_dapo`/`ray_trainer`/`ppo_megatron_trainer`/`vllm_rollout_spmd`/`agent_loop` 等。verl 框架本体语义见 [verl](verl.md)。

## Evidence

源页 [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL)。blob base `https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/`：

- 全共卡多继承 / share_backbone：`mindspeed_rl/workers/integrated_worker.py`（`IntegratedWorker`、`initialize`、`compute_ref_log_prob`、`temporary_micro_batch_size`）
- 训推共卡 Actor：`mindspeed_rl/workers/actor_hybrid_worker.py`（`ActorHybridWorkerBase.initialize`、`enter_infer_mode`、`generate_sequences`、`update`、`_build_rollout`、`_build_sharding_manager`）
- Ray 角色 / 设备绑定：`mindspeed_rl/workers/base_worker.py`（`BaseRayWorker`）
- 训推态切换状态机：`mindspeed_rl/workers/resharding/megatron_sharding_manager.py`（`MegatronShardingManager.enter_infer_mode`/`enter_train_mode`/`enter_forward_mode`）
- vLLM 适配 + megatron weight loader：`mindspeed_rl/models/rollout/vllm_engine.py`（`VLLMInferEngine`）、`mindspeed_rl/models/rollout/vllm_adapter/megatron_weight_loaders.py`（`load_megatron_weights`）
- 分层配置 / batch 语义：`mindspeed_rl/config_cls/{rl_config,megatron_config,generate_config,base_config,validate_config}.py`
- verl 适配线：`verl_npu/verl_npu/plugin.py`（`apply_npu_plugin`、`apply_repo_patches`）、`verl_npu/verl_npu/__init__.py`、`verl_npu/verl_npu/patch/`
- 特性文档：[`integrated_worker.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/features/integrated_worker.md)（全共卡 Integrated Worker 设计）、[`offload.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/features/offload.md)（训推态 offload/onload 编排）

## Links

- 训练框架基座：[mindspeed](mindspeed.md)
- 推理后端：[vllm-ascend](vllm_ascend.md)
- 并行适配线：[verl](verl.md)
- 训推态在线重切分：[train-rollout-switch](../techniques/train_rollout_switch.md)
- RL 算法（GRPO/DAPO）：[grpo-dapo](../techniques/grpo_dapo.md)
- [transferdock-data-scheduling](../techniques/transferdock_data_scheduling.md)（承载的 RL 数据面：列存 + 状态矩阵驱动各 worker 异步取放样本）
- [partial-rollout](../techniques/partial_rollout.md)（承载的长尾 rollout 暂停续跑机制）
- [rule-reward-verifier](../techniques/rule_reward_verifier.md)（承载的无模型规则奖励 / Verifier）
- [eplb](../techniques/eplb.md)（承载的 RL 训推共卡 MoE 专家负载均衡）

<!-- cannbot:related:start -->
## 相关

- [EPLB（专家并行负载均衡器，MoE 专家动态负载均衡）](../techniques/eplb.md)（`related`）：焦点卡写明“EPLB **动态调整专家复制策略与分配方案**”，候选卡写明“EPLB 专家映射则在 `resharding/vllm_weight_container.py`（`eplb_map` / 冗余专家收发）”。概念卡解释动态复制与落卡，框架卡定位 eplb_map 在训推权重重组织中的集成点。
- [GRPO / DAPO（组相对策略优化 RL 算法）](../techniques/grpo_dapo.md)（`related`）：焦点卡写明“去掉 PPO 的 critic（价值网络）”，候选卡写明“支持 GRPO / DAPO / PPO / DPO”。算法卡定义 GRPO/DAPO 与 PPO 的差异，框架卡定位这些算法在 MindSpeed-RL 共卡引擎中的承载范围。
- [Partial Rollout（长尾 rollout 暂停续跑）](../techniques/partial_rollout.md)（`related`）：“在线重切分细节、partial-rollout、TransferDock 数据调度见 ［train-rollout-switch］(../techniques/train_rollout_switch.md)”；“**Partial Rollout** 给单步生成设一个 token 预算上限”。候选卡说明框架开关如何截断、保存并跨轮续推长尾响应。
- [RL 训推切换（Train/Rollout Switch：reshard / offload / D2D）](../techniques/train_rollout_switch.md)（`related`）：“用显式的训推态切换接口与分层配置体系驱动一轮 RL 迭代”；“**同一组卡**要在「训练态」（actor update / ref log_prob，由 Megatron+MindSpeed 承载）与「推理态」（rollout/generate，由 vLLM+vLLM-Ascend 承载）之间反复交替”。候选卡解释框架核心切换接口的 reshard、offload 与 D2D 合同。
- [TransferDock（RL 数据面：训推各 worker 间样本调度交换）](../techniques/transferdock_data_scheduling.md)（`related`）：“TransferDock 数据调度见 ［train-rollout-switch］(../techniques/train_rollout_switch.md)”；“TransferDock 是 ［mindspeed-rl］(../frameworks/mindspeed_rl.md) 一轮 GRPO/DAPO 迭代的**数据面**”。候选卡直接定义框架各 Ray worker 间 experience 的生产、就绪与消费合同。
- [vLLM-Ascend（veRL RL 的 rollout 推理后端）](vllm_ascend.md)（`related`）：“共用 vLLM 推理后端（［vllm-ascend］(vllm_ascend.md)）”；“它充当 ［verl］(verl.md) 框架的 **rollout（on-policy 采样生成）推理后端**”。候选卡是框架 rollout 阶段的直接执行后端并给出图模式/大 EP 边界。
- [veRL（火山引擎开源 LLM RL 后训练框架 + 昇腾适配）](verl.md)（`related`）：“**`verl_npu/`** —— 给上游 ［verl］(verl.md) 打昇腾 patch 的非侵入适配层”；“veRL 在昇腾 NPU 上跑通靠替换它的两个可插拔引擎”。前者是仓内适配入口，后者定义 veRL worker 与训练/推理引擎插拔边界。
- [规则奖励 / Verifier（数学·格式校验的无模型奖励）](../techniques/rule_reward_verifier.md)（`related`）：Verifier 卡指出“MindSpeed-RL 的 `RuleReward` worker 就是这条路径的落地”；框架卡说明“Actor / Reference / Reward 三角色**分时复用同一批 NPU**”。框架部署解释规则奖励为何能由共卡 RewardWorkerBase 承载而不配置独立 reward NPU。
<!-- cannbot:related:end -->
