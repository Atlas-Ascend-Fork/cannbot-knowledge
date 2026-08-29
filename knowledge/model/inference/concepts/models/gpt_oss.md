---
type: Concept
title: GPT-OSS
description: GPT-OSS 是 OpenAI 开源的 MoE 架构大语言模型家族，包含 **GPT-OSS-20B** 与 **GPT-OSS-120B** 两个规格。cann-recipes-infer 基于 HuggingFace Transformers 官方 `modeling_gpt_oss.py`，在 **Atlas A2 系列产品**上实现了单机单 batch 推理样例：GPT-OSS-20B 单 device 部署，GPT-OSS-120B 8 卡 TP 部署。 优化手段为经典"大 MoE 模型 NPU 推理"组合拳：Attention TP + MoE TP（`gate_up_proj` 合并）+ 固定 KV Cache + 融合算子（RMSNorm / AddRMSNorm / `fused_infer_attention_score_v2` / MoE routing 四件套 / GroupedMatmul）+ 集合通信 AIV 展开。**本样例仅支持 eager 单算子模式 + batch_size=1**，暂未引入图模式 / MTP / EP / W8A8 等更激进的优化。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/gpt-oss/gpt_oss_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
---

# GPT-OSS

## Summary

GPT-OSS 是 OpenAI 开源的 MoE 架构大语言模型家族，包含 **GPT-OSS-20B** 与 **GPT-OSS-120B** 两个规格。cann-recipes-infer 基于 HuggingFace Transformers 官方 `modeling_gpt_oss.py`，在 **Atlas A2 系列产品**上实现了单机单 batch 推理样例：GPT-OSS-20B 单 device 部署，GPT-OSS-120B 8 卡 TP 部署。

优化手段为经典"大 MoE 模型 NPU 推理"组合拳：Attention TP + MoE TP（`gate_up_proj` 合并）+ 固定 KV Cache + 融合算子（RMSNorm / AddRMSNorm / `fused_infer_attention_score_v2` / MoE routing 四件套 / GroupedMatmul）+ 集合通信 AIV 展开。**本样例仅支持 eager 单算子模式 + batch_size=1**，暂未引入图模式 / MTP / EP / W8A8 等更激进的优化。

### Highlights

- **Atlas A2 目标平台**（与仓内多数走 Atlas A3 的模型不同）
- **权重仅支持 bf16**：原始 mxfp4 权重需离线转换为 bf16 后才能喂入本样例
- **parallel_config 三项同值约束**：`attn_tp_size == moe_tp_size == lmhead_tp_size`
- **可学习 attention sink**：每头一个 `self.sinks` 标量经 FIA `learnable_sink` 入参生效，按 rank 切分；GPT-OSS 标志性注意力设计
- **专家走 clamped-GLU**（`limit=7.0` / `alpha=1.702` / `(up+1)*glu`），两个 GMM 均带 bias，非裸 SwiGLU
- **`scatter_update` 管 KV Cache 更新**，`npu_fused_infer_attention_score_v2` 统一 prefill/decode
- **`npu_moe_gating_top_k_softmax` + `npu_moe_init_routing` + `npu_moe_compute_expert_tokens` + `npu_moe_finalize_routing` + `npu_grouped_matmul`** 完整 MoE 融合算子链

## Architecture And Serving Traits

```mermaid
flowchart TD
 In[Hidden] --> RN1[RMSNorm]
 RN1 --> MQKV[qkv_proj<br/>合并 Q/K/V 一次 matmul]
 MQKV --> Split[Split → Q/K/V]
 Split --> FA[npu_fused_infer_attention_score_v2]
 FA --> OP[o_proj 行切]
 OP --> Add1[+ residual]
 Add1 --> RN2[AddRMSNorm]
 RN2 --> Router[router<br/>npu_moe_gating_top_k_softmax]
 Router --> Routing[npu_moe_init_routing<br/>+ compute_expert_tokens]
 Routing --> GMM[npu_grouped_matmul<br/>gate_up_proj+bias → clamped-GLU<br/>limit=7.0,alpha=1.702,(up+1)*glu → down_proj+bias]
 GMM --> Fin[npu_moe_finalize_routing]
 Fin --> Add2[+ residual]
 Add2 --> Out[Hidden']
```

- **Softmax Attention + GQA + 可学习 attention sink**：QKV 头数通过 HuggingFace `configuration_gpt_oss.py` 配置决定，支持 MQA/GQA（`num_key_value_heads <= num_heads`）。每个 attention 头额外持有一个可学习 sink 标量 `self.sinks = nn.Parameter(empty(num_attention_heads_per_rank))`，作为 `learnable_sink` 入参传给 `npu_fused_infer_attention_score_v2`，相当于在 softmax 分母里挂一个常驻的"无 token"通道；该参数按 rank 切分（`load_weights` 里 `"sinks" in name` 分支按 `head_start / heads_per_rank` narrow）。attention sink 是 GPT-OSS 的标志性设计，并非裸 softmax attention。
- **MoE**：routed experts，无 shared expert。逻辑上是 gate / up / down 三矩阵，但物理实现已将 gate 与 up 合并为单个 `gate_up_proj`（带 bias），与 `down_proj`（带 bias）共两个 GMM；激活为带 clamp 的 GLU 变体而非裸 SwiGLU，详见下文。
- **支持滑窗注意力**：`config.layer_types[layer_idx] == "sliding_attention"` 的层走 `sliding_window`，对应 FIA 的 `sparse_mode=4`；非滑窗层 `sparse_mode=3`。属仓内带 attention-sink + 滑窗的非裸 MoE LLM 结构。

### 支持的部署规格

| 配置文件 | 模型 | world_size | attn_tp / moe_tp / lmhead_tp | exe_mode | dataset |
| ---- | ---- | ---- | ---- | ---- | ---- |
| `gpt_oss_20b.yaml` | GPT-OSS-20B | 1 | 1 / 1 / 1 | eager | default |
| `gpt_oss_120b_8tp.yaml` | GPT-OSS-120B | 8 | 8 / 8 / 8 | eager | LongBench |

> `parallel_config` 要求 `attn_tp_size`、`moe_tp_size`、`lmhead_tp_size` **三者相同**（见 config YAML 注释）。仅提供 TP 切分，不提供 EP 路径。

### 约束

- **batch_size = 1**：`infer.sh` 与 executor 层面当前仅支持单 batch。
- **eager 单算子模式**：`exe_mode` 枚举只有 `eager`，未支持图模式 / cache_compile。
- **权重格式**：原始 mxfp4 权重**不能直接用**，需参考 [openai/gpt-oss weights.py](https://github.com/openai/gpt-oss/blob/7b583341fe16729127f6d5b94a7b09ccae97e1a1/gpt_oss/torch/weights.py) 自行离线转换为 bf16。
- **在线切分**：YAML 默认 `enable_online_split_weight: True`，加载时在线切到各卡，不需离线切分。

## Known Optimizations

优化要点见下文。

### Attention Tensor Parallel (TP) 优化

对 Attention 的张量切分策略可以分为**对 QKV 头的切分**和**对线性层的切分**。

在对 QKV 头切分时，attention 的多头计算机制可以方便进行张量切分，每个头先独立计算，再将结果 concat 起来。假设模型的 attention 层需要对 `num_heads` 个 query 按照切分数量 `tp_size` 进行切分，要求 `num_heads` 必须能被 `tp_size` 整除，每张卡放置 query 头个数为 `num_heads_per_rank = num_heads // tp_size`；key 和 value 头数相等，且可能小于等于 query 头个数（在 MQA 和 GQA 的场景下会小于）。为了确保每张卡至少放置一个 key 和 value 头，每张卡放置的 key 或 value 头数计算方法为 `num_key_value_heads_per_rank = max(num_key_value_heads // tp_size, 1)`。QKV 头在卡上排布情况如下图所示。

![GPT-OSS Attention QKV 头切分](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/gpt-oss/figures/attention_tp.png)
*来源：[`docs/models/gpt-oss/figures/attention_tp.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/gpt-oss/figures/attention_tp.png)（cann-recipes-infer @ 2f82d10）*

针对 `q_proj`、`k_proj` 和 `v_proj` 三个线性层，可以进一步**合并为一个线性层 `qkv_proj`**，即在推理中将三个矩阵乘替换为一个矩阵乘，可以最大化使用 NPU 的计算能力提升性能。随后将结果切分得到 Q、K、V，并进行 attention 计算，最后通过 `o_proj` 层输出。

### MoE Tensor Parallel 优化

假设模型的 MoE 层的切分数量为 `tp_size`，专家个数为 `expert_num`。对 MoE 层进行张量切分时：

- 对 `gate_proj` 与 `up_proj` 进行**列切分**
- 对 `down_proj` 进行**行切分**
- 对 `gate_proj` 和 `up_proj` 可以采取**合并 matmul** 的优化方式，得到 `gate_up_proj`，实现计算性能优化

> **专家激活是带 clamp 的 GLU 变体，非裸 SwiGLU**：`GptOssExperts` 中 `gate_up_proj` 合并输出按 `[..., ::2]` / `[..., 1::2]` 拆出 `gate`、`up` 后，先 `gate.clamp(max=7.0)`、`up.clamp(-7.0, 7.0)`（`self.limit = 7.0`），再 `glu = gate * sigmoid(gate * 1.702)`（`self.alpha = 1.702`），最终送入第二个 GMM 的张量是 `(up + 1) * glu`。两个 `npu_grouped_matmul`（`gate_up_proj`、`down_proj`）均带 bias（`gate_up_proj_bias` / `down_proj_bias`）。这些 clamp 上下界、`alpha` 缩放与 `+1` 偏移会直接影响数值正确性，权重转换/对齐时不可按普通 SwiGLU 处理。

### 固定 KV Cache 大小

- 首先申请一块**固定大小**的 KV Cache tensor，以优化源码动态申请内存的性能损失。KV Cache 的大小为 `(batch * seq_len * num_key_value_heads_per_rank * head_dim)`，其中 `seq_len` 至少为输入和输出的最大总和，以保证在推理过程中 KV Cache 的更新不会越界。
  > `gpt_oss_optimization.md` 称该实现位于 `GptOssForCausalLM.init_cache`，但 modeling 里 `GptOssForCausalLM` 仅有 `__init__` / `forward` / `load_weights`，并无 `init_cache` 方法。实际由 executor runner 的 `init_kvcache` 流程在 device 上预分配：模型侧 `GptOssAttention` 仅占位 `self.k_cache = self.v_cache = torch.Tensor([])  # will be set in runner's init_kvcache`，由 `model_worker._init_kvcache` 完成分配（`init_cache` 只是框架对 `hasattr(self.model, "init_cache")` 的可选回调，本模型未实现）。
- 在计算完 Q、K、V 后，可以通过 [`scatter_update`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-scatter_update.md) 算子对指定位置上的 KV Cache 进行更新。

### 使能融合算子

#### RMSNorm 融合与 AddRMSNorm 融合

替换 `GptOssRMSNorm` 的 `forward` 函数，使用融合算子接口 [`torch_npu.npu_rms_norm`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_rms_norm.md) 和 `torch_npu.npu_add_rms_norm`，将多个算子的计算替换成融合 kernel，提升性能。

#### GMM 使能与 Routing 优化

在 GPT-OSS 的 MoE 专家模块中，通过使能融合算子，进一步提升性能，可以参考 `GptOssMLP` 类中的实现。

- **快速选择专家**：使用 [`torch_npu.npu_moe_gating_top_k_softmax`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_gating_top_k_softmax.md) 融合算子，代替原来"先 topk 再 softmax"的多算子操作，更快速地计算出 token 和专家的分数。
- **高效排序和 token 路由**：
 - [`torch_npu.npu_moe_init_routing`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_init_routing.md) —— 获取专家的排序；
 - [`torch_npu.npu_moe_compute_expert_tokens`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_compute_expert_tokens.md) —— 获取每个专家需要计算的 token 数；
 - [`torch_npu.npu_moe_finalize_routing`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_finalize_routing.md) —— 将专家计算完成后的 token 重新排布并加权求和，获得最终输出。
- **高性能专家计算**：[`torch_npu.npu_grouped_matmul`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_grouped_matmul.md) 融合算子，实现多个专家的矩阵乘计算，提高计算和搬运效率。

### Flash Attention 融合算子优化

通过使能 [`torch_npu.npu_fused_infer_attention_score_v2`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_fused_infer_attention_score_v2.md) 推理场景下支持图模式的 FlashAttention 算子，既可以支持**全量计算场景（prefill）**，也可支持**增量计算场景（decode）**。

> 与 `npu_fused_infer_attention_score`（v1）的差异详见 [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)。

### 集合通信使能 AIV 展开

利用 Device 的 Vector Core 计算单元来加速 AllReduce 操作，可通过环境变量 [`HCCL_OP_EXPANSION_MODE`](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/83RC1alpha002/maintenref/envvar/envref_07_0096.html) 使能 AIV，配置如下：

```shell
export HCCL_OP_EXPANSION_MODE=AIV
```

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/gpt-oss/gpt_oss_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/gpt-oss/gpt_oss_optimization.md)（Attention TP / MoE TP / 固定 KV Cache / 融合算子 / FA / AIV 六大章节）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/README.md)（Atlas A2 环境准备、权重转换约束、单 batch 限制、在线切分默认开启）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/config/gpt_oss_{20b,120b_8tp}.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/config/gpt_oss_{20b,120b_8tp}.yaml)（两份部署模板）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/gpt_oss/models/modeling_gpt_oss.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/gpt_oss/models/modeling_gpt_oss.py)（`GptOssAttention.sinks` 可学习 sink + `learnable_sink` 入参 / `GptOssExperts` clamped-GLU 带 bias / `GptOssAttention` k_cache 占位待 runner 分配 / `GptOssMLP` 参考实现）

## Links

- [atlas-a3](../platforms/atlas_a3.md) — 本样例目标为 Atlas A2，但 cann-recipes-infer 主体面向 A3
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [ascendc](../frameworks/ascendc.md)

<!-- cannbot:related:start -->
## 相关

- [npu_fused_infer_attention_score (v1 / v2)](../kernels/fused_infer_attention_score.md)（`related`）：“**Softmax Attention + GQA + 可学习 attention sink**：QKV 头数通过 HuggingFace `configuration_gpt_oss.py` 配置决定，支持 MQA/GQA（`num_key_value_heads <= num_heads`）。每个 attention 头额外持有一个可学习 sink 标量 `self.sinks = nn.Parameter(empty(num_attention_heads_per_rank))`，作为 `learnable_sink` 入参传给 `npu_fused_infer_attention_score_v2`，相当于在 softmax 分母里挂一个常驻的"无 token"通道；该参数按 rank 切分（`load_weights` 里 `"sinks" in name` 分支按 `head_start / heads_per_rank` narrow）。attention sink 是 GPT-OSS 的标志性设计，并非裸 softmax attention。”与“昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算：`softmax(QKᵀ/√d)·V`，支持 Paged KVCache、Block-Table、分离的 NoPE/RoPE Query/Key 输入、以及 Query / Key / Value 三端的动态 Int8 反量化（dequant_scale_*）。在 DeepSeek-R1 decode 路径中作为 ［mla-prolog］(mla_prolog.md) 之后的主 FA 算子。”提供双方正文证据。GPT-OSS 模型卡给出实际 `npu_fused_infer_attention_score_v2` 调用及 `learnable_sink` 特有入参，FIA 卡补齐该调用所属融合注意力算子的主体计算与缓存能力，能直接支撑该模型注意力路径的实现核对。
<!-- cannbot:related:end -->
