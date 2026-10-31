---
type: Concept
title: InferenceConfig（统一推理配置体系）
description: 说明当前六类推理配置、独立SpeculativeConfig，以及Decode attention DP与CP Prefill DP的不同公式和token预算，避免沿用旧runner字段。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.kv_cache
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/common/inference_config_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/server.py
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T12:31:15Z'
platforms:
- a2
- a3
- '950'
---

# InferenceConfig（统一推理配置体系）

## 当前配置入口

`InferenceConfig.from_dict(yaml_dict, global_rank, local_rank, disagg_config=None)` 把YAML转换为结构化配置，并计算运行时推导值。当前包含Data、Model、Speculative、Parallel、Scheduler和Disagg六个分组；PD分离配置由服务端构造后传入，不是普通模型YAML的字段组。

模型应以当前README、统一launcher和注册项选择入口。`executor/model_runner.py` 仍存在，不代表所有保留过旧runner的模型当前仍走该路径；旧的 `runner_settings/input_max_len` 不能直接作为当前dataclass字段。

## 数据与模型

`DataConfig` 包含dataset、dataset_path、input_truncated_len（默认256）、reuse_tokenizer以及temperature/top_p/top_k/seed。temperature默认0表示greedy；温度和top_k必须非负，top_p位于[0,1]。

`ModelConfig` 使用model_name/model_path/output_path/dtype、with_ckpt、exe_mode和custom_params等字段：

- dtype默认bfloat16，with_ckpt默认true；关闭加载用于dummy权重路径，不能当作模型质量验收。
- exe_mode为eager/ge_graph/npugraph_ex；静态kernel只允许npugraph_ex。enable_dynamic_graph默认true，只对npugraph_ex有意义，GE下被忽略并产生提示。
- enable_cache_compile、force_eplb、enable_profiler默认false，enable_weight_nz默认true；模型和平台仍可施加额外限制。
- platform_version支持A2、A3、950；YAML显式值优先，否则探测设备名，探测失败警告并回落A3。配置回落不能代替真实产品识别。

## 投机推理配置

当前使用独立 `speculative_config`：

| 字段 | 当前语义 |
| --- | --- |
| `num_speculative_tokens` | 非负，0关闭投机，正数为最大Draft宽度。 |
| `method` | 开启时必须选择后端；mtp为模型原生MTP，其他方法由后端注册解析。文档提供mtp/dspark示例，实际支持范围还需核对模型注册。 |
| `draft_model_path` | 空值复用主模型路径，否则使用独立Draft checkpoint。 |
| `confidence_threshold` | 开启时限定[0,1]；DSpark的0关闭confidence截断，正值改变每请求参与校验的有效Draft前缀，不改变Verify固定输入宽度。 |
| `draft_temperature` | None继承请求Target温度；非负值独立选择Proposal分布q，Target仍使用请求自己的p做拒绝采样。 |
| `markov_lmhead_tp_size` | 当前配置保留的Markov lmhead TP宽度，默认1并要求正整数；具体后端另行验证支持范围。 |

```yaml
speculative_config:
  num_speculative_tokens: 5
  method: dspark
  confidence_threshold: 0.0
  draft_temperature:
```

`model_config.next_n` 仍是兼容字段，但读取时提示废弃。没有新配置时，正数next_n映射为原生mtp；同时提供新配置且两者宽度不同则报错。归一化后的宽度回填到model_config供兼容代码使用。Draft宽度与Paged Attention的block_size不是同一参数，Verify通常需要K+1输入。

## 并行视图：Decode DP 与 CP Prefill DP 分开

rank由启动入口传入；YAML提供world_size与各TP、CP及offline_prefill_dp_group_size。推导值不接受YAML直接覆盖：

| 变量 | 当前公式 |
| --- | --- |
| `attn_dp_size` | `world_size // attn_tp_size` |
| `cp_prefill_dp_size` | `world_size // (attn_tp_size * cp_size)` |
| `embed_dp_size` | `world_size // embed_tp_size` |
| `moe_ep_size` | `world_size // moe_tp_size` |
| `batch_size_per_dp_rank` | `batch_size // attn_dp_size`，AFD有单独视图调整 |

不能继续把CP乘进通用attn_dp_size。CP Prefill时多个CP rank共同处理同一请求批次，使用cp_prefill_dp_size；Decode与普通attention DP仍使用attn_dp_size。

当前实现只接受cp_size=1，或cp_size=world_size；启用CP时还要求attn_tp_size=1。各TP维度须整除world_size，offline_prefill_dp_group_size为正数并整除world_size；owner group大于1时还校验batch_size_per_dp_rank能被owner group整除。模型配置进一步核对专家数与注意力头数的切分条件。

## 调度与预算

| 字段 | 默认与约束 |
| --- | --- |
| `batch_size` | 全局batch，需与attention DP分组匹配。 |
| `max_new_tokens` | 默认32。 |
| `max_prefill_tokens` | 默认0，构造时按实际Prefill批次推导token预算。 |
| `max_mm_encode_tokens` | 默认0；正值是全局MM Encode打包目标，不是严格单请求或显存上限。 |
| `cp_mini_batch` | 默认-1，不额外限制CP Prefill请求数；当前V4 CP要求为1。 |
| `mem_fraction_static` | 默认0.85，用于设备静态内存预算。 |
| `block_size` | 默认128，每KV block的token容量。 |
| `num_reserved_decode_tokens` | 默认64，PD Decode准入时为每条在途请求预留近期生成空间。 |

max_prefill_tokens=0时，非CP用 `input_truncated_len * batch_size_per_dp_rank`；CP改用 `input_truncated_len * (batch_size // cp_prefill_dp_size)`，并在cp_mini_batch为正时先裁剪该Prefill请求数。不能继续把旧的非CP公式无条件用于CP。

MM Encode目标按 `ceil_div(max_mm_encode_tokens, cp_prefill_dp_size)` 分给本地副本，FIFO整请求入批，队首请求可单独超出目标，因此还需按真实输入、KV和encoder内存验证峰值。

## PD分离、日志与验收

DisaggConfig由在线入口传入，区分NONE/PREFILL/DECODE，支持memfabric与mooncake；后者使用HIXL后端，具体设备端点与bootstrap约束见[在线PD](../frameworks/online_pd_inference.md)。

主入口通过setup_logging统一日志，`CANN_RECIPES_LOG_LEVEL` 默认INFO。先检查最终打印配置、设备探测与分组，再用少量请求核对采样、Prefill打包、Decode准入与cache容量；逐项开启投机和图模式，不把配置解析成功视为模型与拓扑已经验证。本仓未运行NPU推理。

## 相关入口

- [Executor](../frameworks/cann_executor.md)
- [KV管理](../frameworks/kv_cache_manager.md)
- [投机推理](mtp_speculative_decoding.md)
- [长序列CP](../parallelism/context_parallel.md)
- [图模式](npu_graph_mode.md)
- [MM统一拉起](../frameworks/mm_inference_launch.md)
