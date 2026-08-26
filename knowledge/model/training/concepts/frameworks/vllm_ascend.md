---
type: Concept
title: vLLM-Ascend（veRL RL 的 rollout 推理后端）
description: vLLM-Ascend 是开源高吞吐推理引擎 vLLM 的昇腾 NPU 适配插件：通过硬件插件化机制解耦框架与硬件依赖，用户无需修改核心代码即可在昇腾 NPU 上部署模型。在 DeepSeek-R1 671B 的 RL 训练实践中，它充当 verl 框架的 rollout（on-policy 采样生成）推理后端——即「推理生成完整问答数据（rollout/generate）→ 参考模型计算参考概率分布（ref）→ 训练模型计算 loss 并反向更新（update）」这条 RL 流水的第一阶段。原文给出选型理由： > vLLM Ascend 通过硬件插件化机制解耦了框架与硬件依赖，用户无需修改核心代码即可在昇腾 NPU 上部署模型，代码完全开源，且持续进行新特性适配。目前 vLLM Ascend 已经支持 vLLM 的 V1 模式，并针对 DeepSeekR1 的 TorchAir 图模式进行了优化，这对于 rollout 部分的优化很有必要。 本实践与训练引擎 mindspeed（经 Megatron-LM）配合，在 Atlas A3 SuperPoD 超节点 128 卡上达成系统吞吐 123.16 TPS/卡 补充：MindSpeed-RL rollout vllm_adapter(megatron_weight_loaders 在线灌权重 + QKV/MoE reshape、acl graph、prefix cache、chunked prefill 在 RL rollout 的应用)。
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
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# vLLM-Ascend（veRL RL 的 rollout 推理后端）

## Summary

[vLLM-Ascend](https://github.com/vllm-project/vllm-ascend) 是开源高吞吐推理引擎 [vLLM](https://github.com/vllm-project/vllm) 的**昇腾 NPU 适配插件**：通过硬件插件化机制解耦框架与硬件依赖，用户无需修改核心代码即可在昇腾 NPU 上部署模型。在 DeepSeek-R1 671B 的 RL 训练实践中，它充当 [verl](verl.md) 框架的 **rollout（on-policy 采样生成）推理后端**——即「推理生成完整问答数据（rollout/generate）→ 参考模型计算参考概率分布（ref）→ 训练模型计算 loss 并反向更新（update）」这条 RL 流水的第一阶段。选它作 rollout 后端的关键能力是：代码完全开源并持续适配新特性、已支持 vLLM 的 V1 模式、并针对 DeepSeek-R1 的 TorchAir 图模式做了优化（图模式优化直接决定 rollout 这一耗时主导阶段的吞吐）。

本实践与训练引擎 [mindspeed](mindspeed.md)（经 Megatron-LM）配合，在 Atlas A3 SuperPoD 超节点 128 卡上达成系统吞吐 123.16 TPS/卡（真实权重）/ 250.2 TPS/卡（随机权重）。这是与推理域 [sglang](../../../inference/concepts/frameworks/sglang.md) **同为 LLM 推理服务框架**、但被嵌入训练循环作 rollout 引擎的训练侧用法（vLLM rollout 与 SGLang 同属 veRL 的可选推理后端）。

## rollout 在 RL 训推流程中的角色

DeepSeek-R1 每一步 RL 训练分三个计算密集阶段，三个模型 **全共卡部署、分时复用计算资源**：

| 阶段 | 模型 | 引擎 | 本实践部署（真实权重，256die） |
|------|------|------|---------------------------------|
| rollout / generate（采样生成问答数据） | actor（推理态） | **vLLM + vLLM-Ascend** | 2 个 DP 实例，DP64TP2EP128 |
| ref（参考模型算参考概率分布） | reference | Megatron + MindSpeed | TP4EP8PP8 |
| update（训练模型算 loss + 反向更新） | actor（训练态） | Megatron + MindSpeed | TP4EP8PP8 |

rollout 是数据生成阶段，长序列场景下其耗时可占总体 80% 以上，1K 推 3K 场景也接近一半，因此是 RL 优化的重中之重。本实践 rollout 未采用推理常用的 **PD 分离部署**——因整个 RL 训练中推理 Prefill 部分耗时占比很小、优化收益不高，故走 P/D 共卡。训练与推理并行策略不同（rollout 的 DP/EP 大、ref/update 的 TP/EP/PP），故每步 update 后需经 reshard 把训练权重重新划分给推理侧（见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 的训推切换优化）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image2.png" width="55%"></p>
<p align="center"><sub>图：本实践对 veRL 的四方面性能优化（模型间调度 / 训推切换 / 训练 / 推理），rollout 优化集中在「推理」一支（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·verl 适配和优化实践总览）</sub></p>

## verl + vLLM-Ascend 适配

为使 veRL 与 vLLM-Ascend 兼容，本实践基于 vLLM 社区 vLLM-Ascend 对 DeepSeek-R1 模型结构的昇腾亲和适配，修改主要集中在用于初始化 `vLLMRollout` 对象的 `vllm_rollout_spmd.py` 文件。四项主要操作：

| 主要操作 | 详细描述 |
|----------|----------|
| **手动使能 vLLM-Ascend 的 patch** | patch 包含 vLLM-Ascend 对 vLLM 的一些类、函数、以及部分变量类型的调整，当前版本需要在 import vllm **前**手动引入 patch。 |
| **初始化 DP 通信域** | 配置 `VLLM_DP_MASTER_PORT` 保证每个 DP group 都有独立的通信端口用于组内进程同步，同时通过 `VLLM_DP_MASTER_IP` 指定 DP 组主节点 IP，适应动态集群环境。 |
| **关闭 sleep 模式** | 当前 NPU 上的 sleep 模式在多机上存在失效问题，无法释放显存；不显式关闭会导致 weight 与 kv_cache 被 vLLM 自定义的内存池管理，后续无法通过 torch_npu 手动卸载。 |
| **配置 `max_num_batched_token`** | 加载真实权重后，默认值 8192 会导致专家负载不均时部分卡 OOM，因此需配置 `max_num_batched_token=1024`、`enable_chunked_prefill=True`。 |

> sleep/wake_up 失效是 RL 全共卡部署的关键约束：因 NPU 多机 sleep/wake_up 不可用，offload/onload 改由 `onload_model_weight`+`init_cache_engine`（替代 wake_up）与 `offload_model_weight`+`free_cache_engine`（替代 sleep）手动实现，参考 MindSpeed-RL（见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 的 offload 优化）。

### 使能 vLLM-Ascend 优化特性

使能优化特性需在 vLLM 初始化时传入以下 `additional_config`：

```python
additional_config={
    "torchair_graph_config": {
        "enabled": VLLM_ENABLE_GRAPH_MODE,    #  使能图模式
        "use_cached_graph": False,
        "graph_batch_sizes_init": False,
        "graph_batch_sizes": [max_num_seqs],  #  配置图模式中每个 DP rank 的 batch size
        "enable_multistream_mla": True,       #  图模式中，使能 MLA 多流，将 MLA 的 vector 操作放到另一个流中
        "enable_multistream_moe": True,       #  图模式中，使能 MoE 多流，将共享专家计算放到另一个流中
        "enable_view_optimize": False,        #  图模式中，消除部分 transpose 操作
        "enable_kv_nz": True,                 #  图模式中，使能 kvcache 的 NZ 排布
    },
    "ascend_scheduler_config": {
        "enabled": True,                      #  使用 vllm ascend 的 scheduler
    },
    "refresh": True
},
```

- 启用 vLLM-Ascend 的优化特性，包含使能图模式（[torchair](../../../inference/concepts/frameworks/torchair.md) 整图下沉，消除 Decode 算子下发开销）、使能 MLA/MoE 多流（[moe-multi-stream](../../../inference/concepts/techniques/moe_multi_stream.md)）、使能 kv_cache 的 NZ 格式。
- 显式配置 `enable_expert_parallel=True`，使能 vLLM 的 EP 并行。

> `enable_view_optimize=False` 是显式关闭——EP256 单卡 1 专家时该开关会因专家权重 shape 含值为 1 的维度触发额外 Reshape，破坏 `GroupedMatmulTransFusionPass` 融合而保留冗余 Transpose 算子（单层 MoE Transpose 耗时高达 175us）；`enable_kv_nz` 与 `enable_multistream_*` 等优化项实现原理见 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 的推理优化主线。

## rollout 推理性能优化历程

数据生成推理阶段是 RL 优化的核心。本实践在 vLLM-Ascend 上做了多轮推理优化，**优化代码已全部合入 vLLM-Ascend 社区仓**，DeepSeek-R1 随机权重 1K 推 3K 场景的单卡推理吞吐从 162 token/p/s 提升到 618 token/p/s：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image22.png" width="62%"></p>
<p align="center"><sub>图：RL 推理吞吐优化历程（单卡 BS=64）：Base 162 → TorchAir+AIV+vLLM-V1 419 → 大 EP Transpose/Cumsum 消除 456 → MoE/MLA 多流+fix router 487 → 零冗余 TP 转 EP 通信 519 → DP 间 EoS 检测调度优化 618 token/p/s（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·性能优化：推理）</sub></p>

贡献较大的几项特性（各自的完整原理见所链推理域专页）：

- **TorchAir 整图下沉**：在 vLLM 中使能 [torchair](../../../inference/concepts/frameworks/torchair.md) 图模式，消除 rollout Decode 阶段的算子下发开销（Eager 模式下 NPU 大量时间空闲、CPU 调度成主因）；双层 Dense+MoE 网络图模式耗时优化 9.5ms，671B 全参整网 Decode 吞吐翻倍。
- **MoE/MLA 多流**：基于 TorchAir 多流能力把共享专家计算与路由专家通信、MLA 的无依赖 Cube/Vector 计算重排到并行流，单步 Decode TPOT 优化 6ms、整网推理吞吐提升 7%（[moe-multi-stream](../../../inference/concepts/techniques/moe_multi_stream.md)）。
- **零冗余 TP 转 EP 通信**：Decode 阶段把 MLA 层 AllReduce 替换为 ReduceScatter、MoE 层末尾 AllGather 移至 MLA 层，消除 MoE 部分 AllGather+Split 冗余，TPOT 优化 2ms 以上、Decode 吞吐 +3%。
- **KVCache 支持 NZ**：以 `enable_kv_nz` 控制，KvRmsNormRopeCache 算子 `cache_mode="PA_NZ"` 按 NPU 私有 NZ 格式存 KVCache，消除 FA 算子内部格式转换，3K 序列时 Decode TPOT 收益超 1ms。
- **大 EP 冗余算子消除**：关闭 `enable_view_optimize` 消除冗余 Transpose、配 `npu_grouped_matmul` 的 `group_list_type=1` 消除 Cumsum，整网 9ms Decode 收益、3K 长度下 rollout 总耗时优化超 28s。

### RL 推理调度 bound 优化

纯模型优化后，Prefill+Decode 纯模型计算在 rollout 整体耗时占比已不足 60%，其余 40% 集中在 Decode 前后处理、vLLM V1 Engine 调度、训推切换前权重内存卸载等调度操作上。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image44.png" width="72%"></p>
<p align="center"><sub>图：rollout 373s 耗时拆解——vLLM Sche 31s / Prefill 2s / Decode Forward Model 223s / Decode pre/post process 94s / RL Sche 20s，纯模型计算占比已不足 60%（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·RL 推理调度 bound 优化）</sub></p>

关键调度瓶颈在 vLLM 调度前的全卡 DP 域间 EOS 检测同步与 Decode 前的 P/D 检测同步——均通过 CPU 的 AllReduce 获取 `has_unfinished_requests`，单次平均 10ms，Decode 3000 次后各叠加耗时高达 30s。优化把 `has_unfinished_requests` 与 `_get_forward_metadata_across_dp` 中的 AllReduce 通信后端由 **Gloo（CPU-TCP）改为 HCCL（NPU-HCCS）**：单通信耗时由 14ms 降到 3ms 以内，128 卡整网推理吞吐由 519 优化到 618 tps、推理耗时 385s→322s（提升约 20%）。

## MindSpeed-RL rollout vllm_adapter

[mindspeed-rl](mindspeed_rl.md) 是 veRL 之外的另一个昇腾 RL 后训练框架，它不复用 veRL 的 `vLLMRollout`，而是在 `mindspeed_rl/models/rollout/` 下自带一层 **vLLM-Ascend adapter**，用 `VLLMInferEngine`（继承 `BaseInferEngine`）直接驱动 vLLM-Ascend 做 GRPO/DAPO/PPO 的 rollout 采样。其与 veRL 用法的本质差异：veRL 走单控制器+SPMD worker，MindSpeed-RL 走 `external_launcher` + Megatron 权重在线注入；但二者面对的昇腾约束（sleep 失效、megatron→vllm 权重格式转换、图模式）是同一套，机制可对照。

### Megatron 权重在线加载进 vLLM（不落盘）

`VLLMInferEngine.__init__` 以 `load_format='megatron'` 初始化 vLLM 时把 `LLM(load_format='dummy')` —— vLLM 只建空壳模型、不读 checkpoint；真实权重由训练侧每步 reshard 后通过 `sync_model_weights(params)` 在线灌入，**全程不落盘**。核心是 `megatron_weight_loaders.py`：

- `update_megatron_weight_loader()` 把 vLLM 的 `ColumnParallelLinear / RowParallelLinear / ReplicatedLinear / QKVParallelLinear / MergedColumnParallelLinear / VocabParallelEmbedding / ParallelLMHead / FusedMoE` 八类层的 `weight_loader` 全部替换成 `parallel_weight_loader`（直接 `param.data = loaded_weight.data` 共享显存、不 copy），前提是训练侧已按推理并行策略切好、shape 严格对齐。
- 按模型架构分发 loader（`MODEL_MEGATRON_WEIGHT_LOADER_REGISTRY`）：Llama / Qwen2/3 / Qwen3-MoE / DeepSeekV2/V3 / Qwen2.5-VL 各一套。Megatron 的融合 `qkv` 权重要按 `infer_tensor_parallel_size` 拆回 q/k/v 再 cat（`qkv_split_weight`/`qkv_split_bias`，按 `num_key_value_heads` 分组处理 GQA repeats）。
- MoE 专家权重按推理 EP 重排：`mlp.experts.w13_weight` / `w2_weight` 依 `infer_expert_parallel_size` 与 `infer_local_num_experts` reshape，EPLB 开启（`infer_local_num_experts != -1`）时还要 `transpose(2,1)`。
- DeepSeek MLA：`qkv` 依 `q_lora_rank` 走 `fused_qkv_a_proj` 或拆成 `q_proj`+`kv_a_proj_with_mqa`；灌权后 `_process_mla()` 清掉旧 `w_kc/w_vc/W_UV/W_UK_T` 缓存并重跑 `process_weights_after_loading`，否则 MLA 吸收权重是上一轮的脏值。

### sleep/wake_up 失效 → 手动 offload/onload

与 veRL 实践同一约束（NPU 多机 sleep 模式无法释放显存），MindSpeed-RL 同样**不依赖 vLLM 的 sleep/wake_up**，而是手动管理「权重 + KVCache」两份显存：

- `__init__` 末尾为每个参数建一份 CPU 影子 `cpu_model[name] = empty_like(..., device="cpu")`，初始化后立刻 `free_cache_engine()` + `offload_model_weights()`，把显存让给训练态。
- `offload_model_weights()`：`params.data = cpu_model[name]` 把权重指针切到 CPU，并清空 MLA 的 `w_kc/w_vc/W_UV/W_UK_T`（这些是 loading 后算出的派生权重，不清会驻留显存）。
- `init_cache_engine()` / `free_cache_engine()` 是 wake_up/sleep 的替身：V1 下分别走 `model_executor.initialize_from_config(kv_cache_configs)`+`reset_prefix_cache()` 与把各层 `kv_cache` 置空 tensor、`untyped_storage().resize_(0)` 真正回收。每次 `generate_sequences` 开头 `init_cache_engine()`、结尾 `free_cache_engine()`，使 KVCache 只在 rollout 窗口内占显存。

### acl graph / TorchAir 图模式

`enforce_eager=False` + `torchair_graph=True` 时，`VLLMInferEngine` 向 vLLM 传 `additional_config.torchair_graph_config`（`enabled / use_cached_graph=False / graph_batch_sizes_init=False / graph_batch_sizes=[max_num_seqs]`），用 [torchair](../../../inference/concepts/frameworks/torchair.md) 整图下沉消除 Decode 算子下发开销；`graph_batch_sizes` 固定成 `max_num_seqs` 以便图按定长 batch 编译。约束：DeepSeek-V3 开 `torchair_graph` 必须关 `enforce_eager`；图模式（`enforce_eager=False`）下 `TASK_QUEUE_ENABLE` 应设 1、否则设 2（task_queue 算子下发队列，控制排队/批处理以提吞吐，对 MoE 专家不均也有动态均衡作用）。多模态分支（`is_multimodal()`）会强制 `graph_batch_sizes=[]`、`ascend_scheduler_config={}`，即 VLM rollout 不走 ascend scheduler 与定长图。

### prefix cache 与 chunked prefill 在 rollout 的边界

- **prefix cache**：`enable_prefix_caching` 透传给 `LLM(...)`，缓存已处理请求 Prefill 阶段的 KV 中间结果，新请求命中相同前缀时直接复用、跳过重复 Prefill；只在 Prefill 生效、不影响输出，适合 RL 里同 system prompt / 同few-shot 前缀的批量 rollout。
- **chunked prefill**：把长 prompt 切块跨多个 forward step 调度、与 decode 拼 batch 拉平每步算量，降 P90 TTFT/TPOT 并缓解单 batch 过大 OOM（veRL 实践即靠 `enable_chunked_prefill=True`+`max_num_batched_token=1024` 防专家不均 OOM）。边界：**不能与 prefix cache(APC) / KVCache 量化同开**；vLLM V1 scheduler 默认开 chunked prefill，但开 `ascend_scheduler_config.enabled=True`（`VLLMInferEngine` 默认 `ascend_scheduler_config_enabled=True`）后 chunked prefill **默认关闭**（非硬互斥，是默认值切换），rollout 默认走昇腾自研 scheduler。

### engine_core / 多模态 patch

adapter 在 import vllm 后立刻打两类 patch（`from vllm_ascend.patch import platform, worker` 之后再引 `vllm_adapter.engine_core`）：

- `engine_core.py` monkey-patch `EngineCore._initialize_kv_caches` 与 `NPUModelRunner.initialize_kv_cache`：前者因「共享的中心化控制器」要求所有 worker 的 `kv_cache_config` 一致（断言各 worker `num_blocks` 相同），取 `kv_cache_configs[0]` 统一建调度器；后者加 `if not self.attn_groups` 守卫，**防止 RL 反复 init/free cache engine 时多次重建 attn_backends**，并按 sparse / DeepSeek-MLA / 常规分流建 KVCache。
- `vllm_adapter/patch/` 仅在 `is_multimodal()` 时生效，给 VLM rollout 打三个昇腾亲和 patch：`rotary_embedding_patch` 把 `MRotaryEmbedding.forward` 换成 `torch_npu.npu_mrope` 融合算子（一次下发完成 multimodal RoPE，省去 vLLM 原生多算子拼装）、`qwen2_5_vl_visionmlp_patch` 替换 ViT MLP、`qwen2_5_vl_reuse_vit_patch` 复用 ViT image embedding 避免重复视觉编码。

> 训推权重在不同并行策略间的重切分（TP 成倍增减、PP→DP、EP 成倍增大）由框架的 Resharding/ShardingManager 完成，`VLLMInferEngine.sync_model_weights` 只是 reshard 后的最后一跳「灌入 vLLM」，切换编排细节见 [train-rollout-switch](../techniques/train_rollout_switch.md)。

## 环境与版本

依赖版本基线：vLLM `v0.9.1` + vLLM-Ascend `v0.9.1rc2`；CANN `8.2.RC1` + torch_npu `7.1.0` + PyTorch `2.5.1`；recipe 附 `0001-FIX-KVcache-NZ.patch`（KVCache NZ 优化），框架本体自行拉取。真实权重 123.16 TPS/卡 是在「复用 MindSpeed 训练优化 + TorchAir 整图下沉 + MoE/MLA 多流 + KVCache 支持 NZ」四项特性同开下达成，对应代码已合入 verl PR #3427 与 vLLM-Ascend v0.9.1rc2。

## Evidence

- [vllm-ascend](https://github.com/vllm-project/vllm-ascend) — vLLM-Ascend 上游仓 source 页（含 URL 与各 recipe pin ref）

- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — MindSpeed-RL rollout vLLM-Ascend adapter（blob base `https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/`）：
  - [`mindspeed_rl/models/rollout/vllm_engine.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/rollout/vllm_engine.py) — `VLLMInferEngine`（`LLM(load_format='dummy', distributed_executor_backend='external_launcher', additional_config=...)`、`sync_model_weights`/`_process_mla`、`offload_model_weights`/`init_cache_engine`/`free_cache_engine`（替 wake_up/sleep）、`generate_sequences`）
  - [`.../vllm_adapter/megatron_weight_loaders.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/rollout/vllm_adapter/megatron_weight_loaders.py) — `update_megatron_weight_loader`/`parallel_weight_loader`、`MODEL_MEGATRON_WEIGHT_LOADER_REGISTRY`、`deepseek/qwen/llama_*_weight_loader`、`qkv_split_weight`、MoE `w13/w2` 按 EP reshape
  - [`.../vllm_adapter/engine_core.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/rollout/vllm_adapter/engine_core.py) — patch `EngineCore._initialize_kv_caches`（共享中心控制器、统一 `kv_cache_configs[0]`）与 `NPUModelRunner.initialize_kv_cache`（`if not self.attn_groups` 防重复建 attn_backend）
  - [`.../vllm_adapter/patch/rotary_embedding_patch.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/rollout/vllm_adapter/patch/rotary_embedding_patch.py) — `replace_qwenvl_mrope` → `torch_npu.npu_mrope`（VLM rollout 多模态 patch，`patch/__init__.py` 仅 `is_multimodal()` 时生效）
  - [`docs/zh/features/{acl_graph,vLLM_prefix_cache,chunked_prefill,task_queue,resharding}.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/features/acl_graph.md) — 图模式/前缀缓存/chunked prefill/task_queue/在线重切分特性说明

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/deepseek_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md)（§1.2.2 为何选择 vLLM Ascend、§1.3 引擎适配、§1.4 性能表、§2.2 verl+vLLM-Ascend 适配（四项操作表 + additional_config）、§6 性能优化：推理（TorchAir/多流/零冗余 TP 转 EP/NZ/大 EP 冗余算子/调度 bound）、§4.2 offload）
- [`llm_rl/deepseek/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/README.md) — 选型框架表（verl/vLLM/vLLM-Ascend/Megatron-LM/MindSpeed）、依赖版本（vLLM v0.9.1 / vLLM-Ascend v0.9.1rc2 / CANN 8.2.RC1 / torch_npu 7.1.0）、vllm-ascend 镜像与 patch 拉取命令、128 卡 120 TPS/卡 benchmark
- `llm_rl/deepseek/vllm_ascend_patches/0001-FIX-KVcache-NZ.patch` — KVCache NZ 优化 patch（README 手动环境章节 git apply）
- `verl/workers/rollout/vllm_rollout/vllm_rollout_spmd.py`（veRL 上游，本仓以 patch 修改）— `vLLMRollout` 初始化的接口参数适配点（doc §2.2 所述修改集中处）

## Links

- [verl](verl.md)（承载 RL 框架：vLLM-Ascend 是其 rollout 推理后端，veRL 单控制器调度 rollout/ref/update 三阶段）
- [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)（DeepSeek-R1 RL 训练实践承载页：训推切换 reshard/offload、模型间调度 D2D、推理优化细节）
- [mindspeed](mindspeed.md)（同实践的训练引擎，经 Megatron 承担 ref/update，与 vLLM-Ascend 共卡分时复用）
- [mindspeed-rl](mindspeed_rl.md)（veRL 之外的昇腾 RL 后训练框架：自带 `VLLMInferEngine` rollout adapter，megatron 权重在线灌入 vLLM、手动 offload/onload）
- [train-rollout-switch](../techniques/train_rollout_switch.md)（训推切换：Resharding/ShardingManager 重切分后由 `sync_model_weights` 灌入 vLLM 的最后一跳）
- [sglang](../../../inference/concepts/frameworks/sglang.md)（跨域对照：同为 LLM 推理服务框架，veRL 推理后端的另一可选项）
- [torchair](../../../inference/concepts/frameworks/torchair.md)（跨域：rollout Decode 图模式整图下沉，由 `torchair_graph_config` 使能）
- [moe-multi-stream](../../../inference/concepts/techniques/moe_multi_stream.md)（跨域：MoE/MLA 多流通算并行，rollout Decode 提速来源）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：Atlas A3 SuperPoD 超节点 128 卡部署平台，HCCS 高带宽支撑调度 bound 优化）
- [sam-speculative](../techniques/sam_speculative.md)（SAM 投机在 vLLM-Ascend rollout 后端落地）
- [rollout-rebalance](../techniques/rollout_rebalance.md)（rollout 均衡调度作用于生成阶段）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（Qwen3 RL 的 rollout 后端）
- [scalebox](scalebox.md)（Code RL rollout）
- [eplb](../techniques/eplb.md)（EPLB 在 vLLM-Ascend(VLLM_ENABLE_EPLB)）
- [qwen2-code-rl-scalebox](../../guides/recipes/qwen2_code_rl_scalebox.md)（Code RL rollout 后端）
- [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（EAGLE3/Suffix 投机在 vLLM-Ascend rollout）
