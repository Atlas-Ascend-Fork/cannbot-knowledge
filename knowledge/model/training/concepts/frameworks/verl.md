---
type: Concept
title: veRL（火山引擎开源 LLM RL 后训练框架 + 昇腾适配）
description: veRL（volcengine/verl）是开源 LLM 强化学习后训练框架，结合单控制器（控制流）与多控制器（计算流）优势，简化 PPO / GRPO 等 RL 算法的实现。一次 RL 迭代包含 actor（被训练模型）/ rollout（推理生成）/ reference（参考模型）/ reward（奖励）等 worker 角色，由 Ray 单控制器调度并传递数据。训练后端支持 FSDP / FSDP2 / Megatron-LM，推理后端支持 vLLM / SGLang / HFTransformers。昇腾适配采用 MindSpeed 使能 Megatron-LM 训练后端，以 vLLM-Ascend 承载图模式与大 EP rollout 推理；DeepSeek-R1 RL 使用 Atlas A3 SuperPoD 128 卡集群。verl_npu 适配层在 import 时触发 apply_npu_plugin，经 patch_summary.yaml commit 校验后逐个执行 patch -p1，衔接 MindSpeed 训练后端。
tags:
- task.implementation
- topic.architecture
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# veRL（火山引擎开源 LLM RL 后训练框架 + 昇腾适配）

## Summary

veRL（[volcengine/verl](https://github.com/volcengine/verl)）是开源 LLM 强化学习后训练框架，**结合单控制器（控制流）与多控制器（计算流）优势**，简化了 PPO / GRPO 等 RL 算法的实现。它把一次 RL 迭代抽象为多个 worker 角色——**actor**（被训练模型）/ **rollout**（推理生成）/ **reference**（参考模型）/ **reward**（奖励）——上层用 Ray 做单控制器调度、在 worker 间传递数据驱动 RL 控制流。veRL 训练后端支持 FSDP / FSDP2 / Megatron-LM，推理后端支持 vLLM / SGLang / HFTransformers，这种「训练引擎 × 推理引擎」可插拔结构正是昇腾适配的接口。

veRL 在昇腾 NPU 上跑通靠替换它的两个可插拔引擎：训练后端 [mindspeed](mindspeed.md)（经 MindSpeed 使能 Megatron-LM 拿 NPU 训练性能）与 rollout 推理后端 [vllm-ascend](vllm_ascend.md)（vLLM 的昇腾插件，图模式 + 大 EP 推理）。[deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 在 Atlas A3 SuperPoD 128 卡集群上跑 [grpo-dapo](../techniques/grpo_dapo.md) 高吞吐 RL，总体技术路径是全共卡部署 + 选型 vLLM-Ascend；其任务下发、训推切换 reshard、推理算子优化的机制细节见 [train-rollout-switch](../techniques/train_rollout_switch.md) 与各 technique 页。

## veRL 的 RL 角色与数据流

DeepSeek-R1 的每一步 RL 训练可大致分为三个计算密集阶段，对应 veRL 的 worker 角色：

> 推理生成完整问答数据（rollout/generate）-> 参考模型计算参考概率分布（ref）-> 训练模型计算 loss 并反向更新（update）。

一步 GRPO 迭代的数据流因此是：**rollout** 用当前 actor 权重对一批 prompt 采样生成 response（`generate_sequences`）→ **reference** 模型对 prompt+response 算参考 log-prob（`compute_ref_log_prob`）→ **reward** 给样本打分（`reward`）+ 算优势（`adv`）→ **actor** 计算 loss 反向更新（`update_actor`）。这些任务在 CPU 侧主进程（单控制器）择机调用，由 Ray 在 worker 间 dispatch 输入 / collect 输出；计算本身在各 device worker（多控制器）上跑。

> veRL 单控制器的优势是架构清晰，简化不同的 RL 算法在框架下的实现：只需要写好 worker 的方法，然后在主进程训练流程中择机调用即可。

DeepSeek-R1 671B 三个阶段都吃大量算力，因此 **rollout / ref / update 三模型全共卡部署、分时复用计算资源**（详见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)）。rollout 部分**未采用** PD 分离部署，因为整个 RL 训练中推理 Prefill 耗时占比很小、优化收益不高。

## 昇腾适配总览：两条后端 + 四向优化

veRL NPU 适配的核心是替换它的两个可插拔引擎：

- **训练引擎**：NPU 上通过 MindSpeed 使能 Megatron-LM，以获得较好的 NPU 训练性能。
- **推理引擎**：适配 vLLM-Ascend 图模式与大 EP 推理；由于多机场景的 sleep 特性暂未支持，需要手动实现 offload 与 onload、init_cache 与 free_cache。

在此之上，veRL 的 NPU 性能优化从四个方面展开：模型间调度（D2D 数据直传消除任务下发时差）、训推切换（reshard + offload）、训练（复用 MindSpeed 优化 + old_log_prob 免计算）、推理（rollout 阶段算子/调度优化，已合入 vLLM-Ascend）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image2.png" width="72%"></p>
<p align="center"><sub>图：veRL 的四向性能优化总览——模型间调度 / 训推切换 / 训练 / 推理（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·verl 适配和优化实践总览）</sub></p>

## 训练后端：veRL + MindSpeed

当前 veRL 版本已**原生支持 MindSpeed 训练后端**，机制是 repatch：

> 通过内嵌于 MegatronWorker 初始化阶段的 repatch 机制，实现了 verl 配置参数到 MindSpeed 配置参数的转换和解析，以及 MindSpeed 训练 NPU 亲和实现在 Megatron-LM 中的替换。

也就是说，veRL 的 actor / reference 这类 MegatronWorker 在初始化时把 MindSpeed 的 NPU 亲和实现 patch 进 Megatron-LM，再把 veRL 的配置项翻译成 MindSpeed 配置。据此可在 veRL 启动脚本里直接打开 MindSpeed 的功能/性能特性（复用 [swap-optimizer](../techniques/swap_optimizer.md) 等内存/通信/计算优化），训练脚本节选：

```shell
+actor_rollout_ref.actor.megatron.override_transformer_config.use_flash_attn=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.moe_token_dispatcher_type='alltoall' \
+actor_rollout_ref.actor.megatron.override_transformer_config.moe_grouped_gemm=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.use_fused_rotary_pos_emb=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.use_fused_swiglu=True \
+actor_rollout_ref.actor.megatron.override_transformer_config.swap_optimizer=True
```

DeepSeek-R1 RL 实践中 actor 与 ref 的训练侧并行策略一致，均为 **256 die / TP4 EP8 PP8**（见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)）。

## 推理后端：veRL + vLLM-Ascend

为何选 vLLM-Ascend：它通过硬件插件化机制解耦框架与硬件依赖，用户无需修改核心代码即可在昇腾 NPU 部署模型，代码完全开源，且已支持 vLLM 的 **V1 模式**、针对 DeepSeek-R1 的 **TorchAir 图模式**做了优化——这对 rollout 优化很有必要。

为让 veRL 与 vLLM-Ascend 兼容，需改部分接口参数，修改集中在初始化 vLLMRollout 对象的 `vllm_rollout_spmd.py`：

| 主要操作 | 详细描述 |
| --- | --- |
| 手动使能 vLLM-Ascend 的 patch | patch 含 vLLM-Ascend 对 vLLM 的类、函数、部分变量类型的调整，当前版本需在 `import vllm` 前手动引入 patch。 |
| 初始化 DP 通信域 | 配置 `VLLM_DP_MASTER_PORT` 保证每个 DP group 有独立通信端口用于组内进程同步，并通过 `VLLM_DP_MASTER_IP` 指定 DP 组主节点 IP，适应动态集群环境。 |
| 关闭 sleep 模式 | 当前 NPU 上的 sleep 模式在多机上失效、无法释放显存；不显式关闭会导致 weight 与 kv_cache 被 vLLM 自定义内存池管理，后续无法通过 torch_npu 手动卸载。 |
| 配置 `max_num_batched_token` | 加载真实权重后默认值 8192 会在专家负载不均时让部分卡 OOM，需配 `max_num_batched_token=1024` + `enable_chunked_prefill=True`。 |

使能 vLLM-Ascend 优化特性需在 vLLM 初始化时传入 `additional_config`（原理见 [vllm-ascend](vllm_ascend.md)）：

```python
additional_config={
    "torchair_graph_config": {
        "enabled": VLLM_ENABLE_GRAPH_MODE,    #  使能图模式
        "use_cached_graph": False,
        "graph_batch_sizes_init": False,
        "graph_batch_sizes": [max_num_seqs],  #  配置图模式中每个DP rank的batch size
        "enable_multistream_mla": True,       #  图模式中，使能MLA多流，将MLA的vector操作放到另一个流中。
        "enable_multistream_moe": True,       #  图模式中，使能MoE多流，将共享专家计算放到另一个流中
        "enable_view_optimize": False,        #  图模式中，消除部分transpose操作
        "enable_kv_nz": True,                 #  图模式中，使能kvcache 的 NZ 排布
    },
    "ascend_scheduler_config": {
        "enabled": True,                      #  使用vllm ascend的scheduler
    },
    "refresh": True
},
```

并显式配 `enable_expert_parallel=True` 使能 vLLM 的 EP 并行。rollout 侧并行为 **256 die / DP64TP2EP128**（真实权重）或 **DP128TP2EP256**（随机权重峰值场景）。

## 全共卡部署与训推切换约束

三模型全共卡（ActorRolloutRef 共 worker 实例）下，每步要在训练态与推理态之间切换：训练更新后参数因训推并行策略不同需 **reshard**（重划分），又因共卡需把前一模型 **offload** 至 host、再 onload 后续模型。由于 vLLM 的 `wake_up` / `sleep` 在 NPU 多机实测仍有问题，参考 MindSpeed-RL，用 `onload_model_weight` + `init_cache_engine` 替代 `wake_up`、用 `offload_model_weight` + `free_cache_engine` 替代 `sleep`。reshard / offload 的零冗余 AlltoAllV 路由等机制详见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 与 [train-rollout-switch](../techniques/train_rollout_switch.md)。

## 技术路径取舍小结

| 决策 | 选择 | 理由 |
| --- | --- | --- |
| 部署形态 | rollout/ref/update 三模型全共卡 | 671B 三阶段都吃算力，共卡分时复用最简单高效 |
| 是否 PD 分离 | 否 | RL 训练中 Prefill 耗时占比很小，优化收益不高 |
| 训练引擎 | Megatron-LM + MindSpeed | NPU 上经 MindSpeed repatch 拿训练性能与亲和算子 |
| 推理引擎 | vLLM + vLLM-Ascend | 硬件插件化解耦、V1 模式 + TorchAir 图模式，rollout 优化必需 |
| RL 算法 | GRPO（on-policy） | on-policy 下 old_log_prob 可免算（开关 `recompute_old_log_prob=False`，`log_prob.detach()` 复用）；当前仅 GRPO on-policy，off-policy 需调 batch_size |

整套技术路径基于 Atlas A3 SuperPoD 超节点 128 卡集群验证：加载真实权重（deepscaler，1K 推 3K）系统吞吐 **123.16 TPS/卡**；随机初始化权重 + 强制专家均衡 + 全部优化（gsm8k，固定推 3K）峰值系统吞吐 **250.2 TPS/卡**。

## verl_npu 昇腾 patch 适配层

[mindspeed-rl](mindspeed_rl.md) 仓内的 `verl_npu/` 子包是 veRL 昇腾适配的工程化承载——一套**非侵入、import 即生效**的 patch 框架，把对 veRL 及其依赖链（transformers / mbridge / mindspeed / megatron-core …）的所有 NPU 改动从原仓代码里剥离出来、集中托管。核心是**不 fork veRL，而是在运行时把改动 patch 进 pip 装好的原版包**。

**注入点：`verl/__init__.py` import 触发全部 patch。** 插件安装（`setup.py`）探测 pip 装的 veRL 路径，向其 `__init__.py` 注入一段守卫块（`from verl.utils.device import is_npu_available` → `if is_npu_available:` → `import verl_npu` + 一行启用日志）；当 veRL 在 NPU 上 `import verl` 时即触发 `verl_npu/__init__.py` 的 `_initialize_npu_plugin()`，按序执行 `patch_summary()`（解析清单）→ `apply_npu_plugin()`（打 patch + 校验）。安装期 `setup.py` 还改两处依赖：注释掉 `verl/utils/kernel/linear_cross_entropy.py` 的 `from . import kernels` 导入，并经 `inject_vllm_plugin()` 给 vLLM 的 `fp8_utils.py`/`fused_moe.py` 补 typing 兼容（`list`→`List`）。改动收口在安装期注入 + 运行期 patch，可随上游版本平滑替换。

**patch 落地机制：依赖仓改动走系统 `patch` 打 unified diff，另对 tensordict 单点做函数级 monkey-patch。** `apply_repo_patches(repo, current_rev, repo_dir)` 先 `pip show <repo>`（`get_target_path`，优先取 editable 安装目录）定位目标包，再 `git rev-parse HEAD` 校验**目标仓 commit 与清单声明的 `current_rev` 是否一致**（`check_commit_id`），不一致就**跳过该仓 patch 并告警**（而不是盲目硬打导致 hunk 错位）。一致才遍历该 `dir` 下文件 `patch -p1 -N -i <file>`（`-N` 跳过已应用），返回码非 0 时——输出含 `Reversed (or previously applied)` 或 `Skipping patch.` 当作幂等成功告警、其余才 `raise`。打完 `after_patch_check()` 再把每个 patch 的 `+` 新增行回读真实包文件、确认确实落地。此外 `apply_npu_plugin()` 在打完 diff 后对 `tensordict.base.TensorDictBase._sync_all` 做一处函数级 monkey-patch（替换为 `_sync_all_patch`，对非 CUDA/MPS 的 NPU 设备补 `synchronize()`），修非阻塞 `.to()` 设备→CPU 搬运缺同步导致的精度问题。

**patch_summary：版本路由 + 可读概览（非「打哪些 patch」的事实源）。** `patch_summary.yaml` 按 `repo → versions[{rev, dir, files[]}]` 组织：每个 repo 钉一个 `current_rev`，`versions` 列出该 commit 对应的 `dir`（如 `d62da4950`）和文件级 `class_changes`/`module_changes` 概览。`patch_summary.py` 据此做三件事：(1) **版本路由**——同一 repo 在 `patch/<repo>/` 下并存多个 commit 目录（如 verl 有 `796871d7d`/`0c06358d6`/`d62da4950` 三套），只挑 `rev == current_rev` 的那套目录，实现「一套插件兼容依赖库多版本」；(2) **路径还原**——`find_path_in_patch()` 读 patch 的 `diff --git` 头还原被改文件包内路径；(3) **rank0 概览**——`print_patch_summary()` 仅主进程打印 `NPU Patch Summary`，作改动地图与安装自检。**注意**：真正打哪些 patch 由 `apply_repo_patches` 对该 `dir` 下**全部 `.patch` 文件 `os.listdir`** 决定，并不读 YAML 的 `files`——目录里可有未在 yaml 声明的 patch（如 verl 的 `agent_loop`/`retool`/`sglang_deepscaler_data`），YAML 只管路由与概览。

**与 MindSpeed 训练后端的衔接：patch 作用在「依赖链」而非只在 veRL。** 清单同时托管对 `mindspeed` 仓的 patch（`adaptor.py` 的 `dot_product_attention_forward_impl`、`grouped_linear.py` 的 `MindSpeedTEGroupedLinear.forward`）与 `megatron-core`（`DotProductAttention.__init__`、`MultiTokenPredictionBlock.forward`）、`mbridge`（FP8 反量化权重 IO、NPU 设备探测）、`transformers`（`current_rev` 下仅 NPU FlashAttention；RoPE/RMSNorm 融合 patch 属旧版本目录、不在当前版本路由命中集）。这与「训练后端」节的 repatch 是两层互补：MegatronWorker 初始化时的 repatch 负责把 veRL 配置翻译进 MindSpeed、并在运行期换 NPU 亲和实现；而 verl_npu 这层在**包加载期**就把 MindSpeed / Megatron 自身的少量 NPU 适配 diff 钉死进对应版本的源码（衔接见 [mindspeed](mindspeed.md)）。逐模型适配（如 DeepSeek-V3.2 DSA 的 `mindspeed/07056df535/dsa.patch`）也走同一清单机制承载。

MindSpeed 后端在 veRL 侧的开关全部经 `actor_rollout_ref.actor.megatron.override_transformer_config.*` 透传：TP/PP/EP/ETP/SP/CP、分布式优化器、swap-optimizer、重计算、MoE alltoall dispatcher、MLA，以及 FA/RMSNorm/SwiGLU/grouped-gemm/mc2 等融合算子（均为 Preview 状态）；`strategy=megatron` 是启用 MindSpeed 后端的前置开关。具体配置见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)。

## Evidence

- [verl](https://github.com/volcengine/verl) — veRL 上游仓 source 页（含 URL 与各 recipe pin ref）

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/deepseek_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md)（§1.1 框架对照表、§1.2 技术路径选择（全共卡 / 选型 vLLM-Ascend / 不做 PD 分离）、§1.3 verl 适配优化总览（训练引擎 MindSpeed + 推理引擎 vLLM-Ascend + 四向优化图）、§1.4 128 卡 A3 性能、§2.1 verl+MindSpeed repatch、§2.2 verl+vLLM-Ascend 接口修改表 + additional_config、§5.1 MindSpeed 优化脚本节选）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/deepseek/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/README.md)（DeepSeek-R1 RL recipe：veRL 角色、依赖框架版本 verl/vLLM/vLLM-Ascend/Megatron-LM/MindSpeed 拉取与 checkout、`train_deepseekv3_256die_{random_init,true_weight}.sh` 拉起、`from verl_patches import prelude_patch` patch 入口、verl_patches 目录结构）
- 依赖框架版本基线：veRL `github.com/volcengine/verl`、vLLM `github.com/vllm-project/vllm @ v0.9.1`、vLLM-Ascend `github.com/vllm-project/vllm-ascend @ v0.9.1rc2`、Megatron-LM `github.com/NVIDIA/Megatron-LM @ core_r0.8.0`、MindSpeed `gitcode.com/ascend/MindSpeed @ v2.0.0_core_r0.8.0`

- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — `verl_npu/` 昇腾 patch 适配层（commit pin `398fd9a5fa6358c50071db2d09919e414accea90`），按符号锚定：
  - 注入入口 [`verl_npu/__init__.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/verl_npu/__init__.py) `_initialize_npu_plugin()`（import 即 `patch_summary()` → `apply_npu_plugin()`）；自动注入到 `verl/__init__.py` 的逻辑见 [`verl_npu/setup.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/setup.py)（向 verl `__init__.py` 写 `if is_npu_available: import verl_npu`）
  - patch 落地 [`verl_npu/plugin.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/verl_npu/plugin.py) `apply_repo_patches`（commit 校验 `check_commit_id` → `patch -p1 -N`）、`after_patch_check`（回读 `+` 行）、`apply_npu_plugin`
  - 清单 [`verl_npu/verl_npu/patch_summary/patch_summary.yaml`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/verl_npu/patch_summary/patch_summary.yaml)（`repo → versions[{rev, dir, files}]`，含 verl/transformers/mbridge/mindspeed/megatron-core）+ 路由/概览 [`patch_summary.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/verl_npu/patch_summary/patch_summary.py) `patch_summary()`/`find_path_in_patch()`/`print_patch_summary()`
  - 版本定位 [`verl_npu/verl_npu/utils/pkg_version.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/verl_npu/utils/pkg_version.py) `get_target_path`（`pip show` 取 editable 路径）/`check_commit_id`（`git rev-parse HEAD`）
  - MindSpeed 后端开关透传清单 [`verl_npu/docs/mindspeed.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/docs/mindspeed.md)（`override_transformer_config.*` 特性/融合算子表，均 Preview）；安装与自检 [`verl_npu/README.MD`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/verl_npu/README.MD)

## Links

- [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)（承载实践：veRL + MindSpeed + vLLM-Ascend 在 128 卡 A3 上的 GRPO RL，全共卡 123→250 TPS/卡）
- [mindspeed](mindspeed.md)（训练后端：veRL 经 MegatronWorker repatch 使能 MindSpeed + Megatron-LM 拿 NPU 训练性能）
- [mindspeed-rl](mindspeed_rl.md)（承载 `verl_npu/` 昇腾 patch 适配层的母仓：非侵入 import 即生效、patch_summary 清单 + 多版本路由）
- [vllm-ascend](vllm_ascend.md)（rollout 推理后端：vLLM 昇腾插件，图模式 / 大 EP / MoE·MLA 多流 / KVCache NZ；veRL 经 additional_config 透传其开关）
- [grpo-dapo](../techniques/grpo_dapo.md)（本框架承载的 RL 算法：GRPO on-policy 下 old_log_prob 免计算、组内优势归一）
- [swap-optimizer](../techniques/swap_optimizer.md)（训练侧经 MindSpeed `swap_optimizer=True` 复用的内存优化）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — DeepSeek-R1 RL 训练优化实践（veRL + A3 集群）
- [train-rollout-switch](../techniques/train_rollout_switch.md)（veRL on-policy RL 的训推切换(reshard/offload/D2D)）
- [sam-speculative](../techniques/sam_speculative.md)（SAM 投机加速 veRL rollout）
- [rollout-rebalance](../techniques/rollout_rebalance.md)（veRL rollout 序列级均衡调度）
- [length-aware-resampler](../techniques/length_aware_resampler.md)（veRL LengthAwareEpochSampler 重采样）
- [qwen2.5-rl](../../guides/recipes/qwen2_5_rl.md)（Qwen2.5 入门基于 veRL）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（Qwen3 RL 基于 veRL）
- [scalebox](scalebox.md)（veRL 融合 ScaleBox 沙盒做 Code RL）
- [agent-rl-loop](../techniques/agent_rl_loop.md)（veRL asyncLLM+agent_loop 多轮工具调用）
- [qwen3-tool-agent-rl](../../guides/recipes/qwen3_tool_agent_rl.md)（Qwen3 tool agent RL(verl/retool)）
- [qwen2-code-rl-scalebox](../../guides/recipes/qwen2_code_rl_scalebox.md)（ScaleBox Code RL(verl)）
- [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（多轮工具调用 Code RL(verl)）
- [mindspeed-mm](mindspeed_mm.md)（MindSpeed-MM verl_plugin 生成式 RL 用到 verl）