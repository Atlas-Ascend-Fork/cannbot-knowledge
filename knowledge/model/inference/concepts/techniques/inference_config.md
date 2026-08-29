---
type: Concept
title: InferenceConfig（统一推理配置体系）
description: InferenceConfig 是 CANN Executor 新推理链路的 dataclass 配置入口，聚合 Data、Model、Parallel、Scheduler、Disagg 五类配置并自动校验。关键推导为 attn_dp_size=world_size/(attn_tp_size×cp_size)、batch_size_per_dp_rank=batch_size/attn_dp_size；max_prefill_tokens 为 0 时由 input_truncated_len×batch_size_per_dp_rank 生成。DisaggConfig 由服务端构造，支持 NONE/PREFILL/DECODE 及 memfabric、mooncake 后端。该体系仅适用于 executor/offline/infer.py；legacy model_runner.py 仍使用 runner_settings、input_max_len 和 kvp_size，旧模型 YAML 不能按新字段解释。文档曾漏掉 cp_size，以代码公式为准。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.kv_cache
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/common/inference_config_guide.md
  role: supporting
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# InferenceConfig（统一推理配置体系）

## Summary

`InferenceConfig` 是 [cann-executor](../frameworks/cann_executor.md) 的统一配置入口类，以结构化 `dataclass` 取代早期的 `runner_settings` 字典，提供类型检查、嵌套子配置与自动验证。绝大多数字段由 YAML 加载（`InferenceConfig.from_dict(yaml_dict, global_rank, local_rank)`），少数为**推导值**（不接受 YAML）或由启动入口构造。代码入口 `executor/core/config/inference_config.py`。

聚合五个子配置：

| 子配置 | 来源 | 职责 |
|--------|------|------|
| `DataConfig` | YAML | 数据集 + 输入序列长度上限 |
| `ModelConfig` | YAML | 模型路径、执行模式、MTP、量化外特性开关 |
| `ParallelConfig` | YAML + 环境变量 + 推导 | TP/DP/EP/CP 并行规模与 rank 信息 |
| `SchedulerConfig` | YAML + 推导 | batch 规模、token 预算、Paged Attention block 粒度 |
| `DisaggConfig` | 启动入口构造（**YAML 不含**） | PD 分离运行时（见 [online-pd-inference](../frameworks/online_pd_inference.md)） |

## 字段语义（按子配置）

### DataConfig

| 字段 | 默认 | 说明 |
|------|------|------|
| `dataset` | `"default"` | 数据集名称 |
| `dataset_path` | `""` | 数据集路径；非 `default` 数据集必填 |
| `input_truncated_len` | `256` | 最大输入序列长度，超长 prompt 被截断 |

### ModelConfig

| 字段 | 默认 | 说明 |
|------|------|------|
| `model_name` / `model_path` / `output_path` | `"model"` / `""` / `""` | 模型标识与权重 / 输出目录 |
| `dtype` | `"bfloat16"` | 计算数据类型 |
| `with_ckpt` | `True` | False 时用 `DummyModelLoader` 随机初始化 |
| `next_n` | `0` | MTP 模块数量，>0 自动启用 [mtp-speculative-decoding](mtp_speculative_decoding.md) |
| `platform_version` | `A3` | 平台枚举（`A3` / `950`），参与通信组物理签名 |
| `exe_mode` | `"eager"` | `eager` / `ge_graph` / `npugraph_ex`，见 [npu-graph-mode](npu_graph_mode.md) |
| `enable_static_kernel` | `False` | 仅 `npugraph_ex` 可启用（`_validate` 强制校验） |
| `enable_cache_compile` | `False` | 缓存编译 |
| `force_eplb` | `False` | MoE 强制专家负载均衡 |
| `enable_profiler` | `False` | 性能分析桩 |
| `enable_weight_nz` | `True` | [weight-nz](weight_nz.md) 权重 NZ 格式 |
| `custom_params` | `{}` | 模型特有特性字典 |

### ParallelConfig

YAML 直配的 TP 维度 + 推导出的 DP/EP 维度，rank 信息从环境变量注入：

| 字段 | 来源 | 说明 |
|------|------|------|
| `world_size` | YAML | 总进程数 |
| `global_rank` / `local_rank` | 环境变量（**不支持 YAML**） | 由启动脚本注入 |
| `attn_tp_size` / `embed_tp_size` / `moe_tp_size` / `lmhead_tp_size` / `dense_tp_size` / `o_proj_tp_size` | YAML | 各层 TP 并行数（默认 1） |
| `cp_size` | YAML | context 并行度，见 [context-parallel](../parallelism/context_parallel.md) |
| `attn_dp_size` | **推导** | `world_size // (attn_tp_size * cp_size)` |
| `embed_dp_size` | **推导** | `world_size // embed_tp_size` |
| `moe_ep_size` | **推导** | `world_size // moe_tp_size`，见 [expert-parallel](../parallelism/expert_parallel.md) |

> ⚠️ 矛盾标记（doc≠code，以代码实现为准）：字段说明文档 §2.3（见 Evidence `inference_config_guide.md`）将 `attn_dp_size` 推导式写为 `world_size // attn_tp_size`；而 `inference_config.py:210-213` 实际为 `world_size // (attn_tp_size * cp_size)`（即把 attention 通信组按 TP×CP 计成一组后再分 DP）。以代码实现为准；`cp_size == 1` 时两式等价。

`_validate` 要求 `world_size` 能被各 `*_tp_size`、`cp_size` 及 `attn_tp_size*cp_size` 整除；`validate_model_config` 进一步校验 `num_experts % moe_ep_size == 0`、`num_attention_heads % attn_tp_size == 0`。

### SchedulerConfig

| 字段 | 默认 | 说明 |
|------|------|------|
| `batch_size` | `1` | 全局总 batch size |
| `max_new_tokens` | `32` | 单请求最大生成 token 数 |
| `max_prefill_tokens` | `0` | 单次 prefill batch 的 packed prompt token 预算；为 0 时框架按 `input_truncated_len * batch_size_per_dp_rank` 推导 |
| `mem_fraction_static` | `0.85` | 推理阶段静态占用的设备内存比例，影响 [kv-cache-manager](../frameworks/kv_cache_manager.md) 在线 block 预算 |
| `block_size` | `128` | 单个 Paged Attention KV block 容纳的 token 数 |
| `num_reserved_decode_tokens` | `64` | 仅 PD decode 端：每在途请求保留的 KV token 数，由 `DecodePreallocQueue.pop_preallocated` 用于准入控制 |
| `batch_size_per_dp_rank` | **推导** | `batch_size // attn_dp_size` |

`max_prefill_tokens` 的 0→推导发生在 `InferenceConfig.from_dict`（先算出 `batch_size_per_dp_rank` 再据 `input_truncated_len` 推导），不在 `SchedulerConfig` 内部。

### DisaggConfig

PD 分离运行时配置，由 `executor/online/server.py` 启动时按 CLI 参数构造，**YAML 不含此节**；离线模式取默认值。

| 字段 | 默认 | 说明 |
|------|------|------|
| `disaggregation_mode` | `"NONE"` | `NONE`（离线）/ `PREFILL` / `DECODE` |
| `engine_backend` | `"memfabric"` | `Literal["memfabric","mooncake"]`；选择 KVTransferManager 构造的 TransferEngine 子类，mooncake 走 HIXL 后端，为 opt-in |
| `bootstrap_host` / `bootstrap_port` | `"0.0.0.0"` / `18800` | Bootstrap server 地址 |
| `store_url` / `is_store_creator_node` | `""` / `False` | memfabric 专用 config store（mooncake 后端忽略） |
| `local_ip` | `""` | 本 rank 对外通告的联系地址 |

字段级语义详见 [online-pd-inference](../frameworks/online_pd_inference.md)。

## 配置体系并存说明

上述字段（`input_truncated_len`、移除 `kvp_size` / `packed_sequence`、`max_prefill_tokens` 等）**仅适用于新 `InferenceConfig` 体系**（`executor/offline/infer.py` + `OfflineInference`，即 [cann-executor](../frameworks/cann_executor.md)「部署模式分类」中的新执行器路径）。

**仓库当前并存两套配置体系**：

- **新体系**：`InferenceConfig` dataclass（上述字段语义所属）。供 deepseek_r1 / qwen3_moe / qwen3_5 / gpt_oss / gemma4 等无自带 `infer.py` 的模型使用。
- **legacy 体系**：`executor/model_runner.py:ModelRunner` + `runner_settings` dict，仍用字段 `input_max_len`（默认 `1024`，`data_config` 下）与 `kvp_size`。仍被 **deepseek-v3.2-exp / kimi-k2-thinking / longcat-flash** 在用（各自 `models/<name>/infer.py` + `runner_*.py:*Runner(ModelRunner)`）。

因此那些 legacy 模型页 YAML 表里出现的 `input_max_len` 字段是正确的（legacy 路径如实使用），**不应"修正"为 `input_truncated_len`**。「演进注记」仅相对新体系的早期版本而言。

## 演进注记（配置字段当前快照的来路）

以下为新 `InferenceConfig` 体系当前字段相对其早期版本的演进，便于阅读旧 YAML / 旧文档时对齐，不影响上表的现状语义；legacy `ModelRunner` 路径不在此演进范围内：

- `input_max_len` → `input_truncated_len`：语义相同（输入截断长度），但从 `SchedulerConfig` 迁入 `DataConfig`，默认值由 `1024` 改为 `256`。
- 移除 `packed_sequence`：prefill 现统一走 packed sequence 布局（`Batch.input_ids` 始终为一维 `[TotalTokens]`，框架接口契约的唯一输入布局），不再提供该开关。
- 移除 `ParallelConfig.kvp_size`（仅指**新 `ParallelConfig`**）：2026-05 从 refactored `ParallelConfig` 移除 `kvp_size` 开关，并删除 longcat 的 kvp YAML 配置（`longcat_flash_densetp8_ep{16,32}_kvp8_gegraph_w8a8.yaml`）与文档/图（commit/MR 溯源见 Evidence）。
  > ⚠️ 矛盾标记（2026-05，跨页）：legacy `executor/model_runner.py` 路径与 longcat `modeling_longcat_flash.py` 代码**仍引用 `kvp_size`**（`runner_settings.get("parallel_config").get("kvp_size", 1)`）。[kvp](../parallelism/kvp.md) 页的 KVP 配置示例对应回退前状态——两页就 `kvp_size` 是否仍可用存在表述张力（KVP 部署已于 2026-05 回退，详见 [kvp](../parallelism/kvp.md) 与 [longcat-flash](../models/longcat_flash.md)）；现状为 refactored `ParallelConfig` 已移除该 YAML 开关。
- 新增 `max_prefill_tokens` / `mem_fraction_static` / `block_size`（SchedulerConfig）、`num_reserved_decode_tokens`（PD decode 准入）。
- 新增统一日志：环境变量 `CANN_RECIPES_LOG_LEVEL`（默认 `INFO`），由 `executor/utils/logging_config.py::setup_logging()` 在主入口统一配置，库代码用 `logging.getLogger(__name__)`、禁用 `logging.basicConfig`。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/core/config/inference_config.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/core/config/inference_config.py)（五子配置 dataclass 定义、`from_dict` 推导逻辑、`_validate`；`attn_dp_size` 含 `cp_size`、`input_truncated_len∈DataConfig` 默认 256、`engine_backend` Literal 默认 memfabric、`num_reserved_decode_tokens=64`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/common/inference_config_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/common/inference_config_guide.md)（字段说明文档；其 `attn_dp_size` 推导式与代码实现存在偏差，按矛盾协议取代码实现）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/common/new_model_checklist.md §1`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/common/new_model_checklist.md)（新模型 YAML 必填字段：model_name/model_path/exe_mode、input_truncated_len、batch_size/max_new_tokens/max_prefill_tokens、world_size + 各 tp_size）
- 演进溯源：commit `b085e02`（!501 revert kvp）、`0296d00`（!388）、`f0b0fde`（!386）page-attention/packed sequence；config-guide 字段更新随 refactor !458 / docs !446。

## Links

- [cann-executor](../frameworks/cann_executor.md)
- [online-pd-inference](../frameworks/online_pd_inference.md)
- [kv-cache-manager](../frameworks/kv_cache_manager.md)
- [qwen-dense](../models/qwen_dense.md)（`input_truncated_len: 4096` + `parallel_config` 部署样例）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（`custom_params.moe_ep_decode_mode` + `attn_tp_size=1`/`embed_tp_size=8`/`lmhead_tp_size=8`/`dense_tp_size=1` 部署样例）
- [hy3-preview](../models/hy3_preview.md)（`custom_params.enable_superkernel`/`enable_multi_streams`/`enable_online_split_weight` + `attn_tp_size=dense_tp_size=embed_tp_size=lmhead_tp_size=4`/`moe_tp_size=1` 部署样例）
- [npu-graph-mode](npu_graph_mode.md)
- [mtp-speculative-decoding](mtp_speculative_decoding.md)
- [weight-nz](weight_nz.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [context-parallel](../parallelism/context_parallel.md)
- [kvp](../parallelism/kvp.md)
- [ascend-950](../platforms/ascend_950.md)（`platform_version: "950"` 平台枚举 / `is_ascend_950()` 分支）
- [hixl](hixl.md)（PD KV 传输 HIXL 后端：`engine_backend="mooncake"` 走 HIXL 路径）

## Notes

- **ambiguity**：`platform_version` 取值 `A3` / `950`；`950`（[ascend-950](../platforms/ascend_950.md)）相关行为在配置文档中未展开，仅出现在通信组物理签名与 `is_ascend_950()` 判断中（如 weightNZ 关闭等代际差异见平台页）。
- **gap**：`enable_cache_compile`（缓存编译）的具体落盘 / 命中机制不在配置文档范围。

## 已知冲突

- [kvp](../parallelism/kvp.md)

<!-- cannbot:related:start -->
## 相关

- [CANN Executor（cann-recipes-infer 自研 executor）](../frameworks/cann_executor.md)（`related`）：`InferenceConfig` 是 ［cann-executor］(../frameworks/cann_executor.md) 的统一配置入口类，以结构化 `dataclass` 取代早期的 `runner_settings` 字典，提供类型检查、嵌套子配置与自动验证。；**统一配置入口 `InferenceConfig`**：`dataclass` 结构化替代 `runner_settings` 字典，YAML 驱动，聚合 `DataConfig` / `ModelConfig` / `ParallelConfig` / `SchedulerConfig` 四子配置，PD 分离另由启动入口注入 `DisaggConfig`。字段语义详见 ［inference-config］(../techniques/inference_config.md)。前者提供字段与推导合同，后者明确其在新执行器中的装配位置，可直接完成配置到执行框架的定位。
<!-- cannbot:related:end -->
