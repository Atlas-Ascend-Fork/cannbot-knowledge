---
type: Runbook
title: CP chunked-prefill 空 KV 分片返回 None 破 LSE 合并——须返零输出 + -inf LSE 占位（在线-softmax 中性元）
description: 昇腾 context parallel（CP）chunked-prefill 注意力中，当某分片对某 chunk 无 KV cache（total_toks == 0）时，计算 prefill-context 的函数（vllm-ascend attention_cp.py 的 _compute_prefill_context）原返回 (None, None)，被下游跨分片/跨 chunk 的在线-softmax LSE 合并逻辑当张量使用而抛 TypeError。根因是在线-softmax 合并要求每分片提供同形状/同 dtype 的 (output, lse) 两路输入、靠 lse 表达权重，而 None 破坏了「每分片都在场」的合并契约。修法：空分片提前返回与非空 FIA 路径同形状/同 dtype 的占位张量——output 全 0（形状 (T, num_heads, head_size)、query.dtype）、lse 全 -torch.inf（形状 (T, num_heads, 1)、固定 float32）。-inf 的 LSE 是 log-sum-exp 在线-softmax 合并的中性元（exp(-inf)=0、权重 0），等价于该空分片不参与合并，下游无需为空分片写特判分支。非空路径走 npu_fused_infer_attention_score（FIA，TND 布局，softmax_lse_flag=True，actual_seq_lengths_kv/actual_seq_lengths）。触发用例：tensor_parallel_size=2、prefill_context_parallel_size=2、W8A8、cp_kv_cache_interleave_size=128，混合长度 prompt + chunk_size=50 构造空分片边界，回归用例 test_models_chunked_prefill_with_empty_kvcache。抓手系于 CP 分片 + NPU FIA chunked-prefill 的 LSE 合并契约，可迁移到任何昇腾上 CP/ring-attention 式跨分片 chunked-prefill + LSE 合并实现；与 decode 侧「只 mask lse 不 mask
  out」陷阱互补。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5844
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# CP chunked-prefill 空 KV 分片返回 None 破 LSE 合并——须返零输出 + -inf LSE 占位（在线-softmax 中性元）

## 信号（现象）

在昇腾上做 [context parallel](../../concepts/parallelism/context_parallel.md) 的 chunked prefill（长序列分块预填充），跨分片/跨 chunk 归并注意力时抛 `TypeError`——负责算 prefill-context 的函数在「本分片对本 chunk 无 KV」的边界情形返回了 `(None, None)`，下游把它当张量喂进 LSE 合并（`torch.where` 掩码 / log-sum-exp 归并）即崩。

命中前提：

- prefill 路径把 KV cache 按 CP 维切分到多卡后，逐 chunk 用 [FIA](../../concepts/kernels/fused_infer_attention_score.md)（TND 布局、`softmax_lse_flag=True`）算出本分片本 chunk 的 `(output, lse)`，再跨分片/跨 chunk 做在线-softmax 合并。
- 存在「本分片对某 chunk 持有 0 份 KV token」（`total_toks == 0`）的位置——CP 切分 + chunked prefill 下这是正常边界，不是配置错误。
- 计算 prefill-context 的函数把 `(output, lse)` 初始化为 `None, None`，只在 `total_toks > 0` 时才调 FIA 填充；空分片直接把这对 `None` 返回给下游合并逻辑。

若 prefill 每卡都持有全量 KV（不存在空分片）、或注意力不做跨分片 LSE 合并，则不属本信号。

## 触发条件

- 用例落在 CP + chunked prefill：测试配置为 `tensor_parallel_size=2`、`prefill_context_parallel_size=2`、`decode_context_parallel_size=1`、`enable_expert_parallel=True`、`block_size=128`、`cp_kv_cache_interleave_size=128`、`long_prefill_token_threshold=50`、W8A8（`quantization="ascend"`），模型如 `Qwen3-30B-A3B-W8A8` / `DeepSeek-V2-Lite-W8A8`。
- 触发点：某设备上某 chunk 的 `total_toks == 0`。函数按早期实现返回 `(None, None)`；下游合并按 tensor 使用该返回值（参与跨分片/跨 chunk 的 LSE 合并与 `torch.where` 掩码），拿到 `None` 即 `TypeError`。
- 复现构造：混合长度 prompt（如 128 / 1 / 130 / 51 / 129）+ `chunk_size=50` + `kv_cache_interleave_size=128`，即可造出「某分片某 chunk 无 KV」的空分片边界。

## 根因

在线-softmax 跨分片合并要求每个分片都提供**同形状/同 dtype** 的 `(output, lse)` 两路输入，靠 lse 的相对大小决定各分片权重。空分片被当成「没有贡献就不返回张量」而给了 `None`，破坏了这个契约——合并算子期望的是一个「权重为 0 的中性分片」，而不是缺席的 `None`。这是把「空分片 == 无返回」的直觉，错误套到「合并算法要求每分片都在场、用 lse 表达其权重」的实现上。

## 修法

空分片提前返回**与非空路径同形状/同 dtype**的占位张量：`output` 全 0，`lse` 全 `-inf`：

```python
if total_toks == 0:
    return (torch.full((query.size(0), num_heads, self.head_size),
                       fill_value=0,
                       dtype=query.dtype,
                       device=query.device),
            torch.full((query.size(0), num_heads, 1),
                       fill_value=-torch.inf,
                       dtype=torch.float32,
                       device=query.device))
```

要点：

- **`-inf` 的 LSE 是在线-softmax（log-sum-exp）合并的中性元**：合并按 `exp(lse)` 定权重，`exp(-inf)=0`，故该分片权重为 0，对最终注意力零贡献。返回「零输出 + `-inf` LSE」在数学上等价于「本分片不参与合并」，而下游无需为空分片再写特判分支。
- 形状/dtype 必须与真实分片对齐：`output` 形状 `(T, num_heads, head_size)` 用 `query.dtype`（跟随激活精度）；`lse` 形状 `(T, num_heads, 1)` 固定 `float32`（LSE 通道恒为 fp32，即便激活是 bf16/低比特）。
- 非空路径不变：`torch.ops.npu.npu_fused_infer_attention_score(... input_layout="TND", softmax_lse_flag=True, actual_seq_lengths_kv=..., actual_seq_lengths=...)` 得 `(output, lse)`，随后仍用 `batch_chunk_seq_mask` 把无效位置的 lse `torch.where(lse_mask, -torch.inf, lse)` 置 `-inf`——空分片占位与这条既有掩码语义同源，`-inf` LSE 在两处都表示「权重 0」。

correctness 验证由构造空分片边界的回归用例覆盖，断言消除 `TypeError`（用例构造见 Evidence）。本修复为 bugfix，无性能数字。

## 可迁移边界

- 抓手系于昇腾特有形态：CP 分片 + NPU FIA（`npu_fused_infer_attention_score`，TND 布局，`softmax_lse_flag`）chunked-prefill 的 LSE 合并契约，不是各硬件同名框架的纯逻辑 bug。
- 在此抓手内可迁移：**任何在昇腾上实现 CP / ring-attention 式跨分片 chunked-prefill + 在线-softmax LSE 合并的实现**，空分片都必须返回「零输出 + `-inf` LSE」占位张量、而非 `None`——与具体模型无关（改动落在模型无关的 CP attention 后端）。
- 与同域另一陷阱互补：本页是 **prefill** 侧「空分片返 None 破合并（须返占位张量）」；[CP/DCP 解码合并只 mask lse 不 mask out](../precision/cp_dcp_online_softmax_merge_mask_out_not_only_lse.md) 是 **decode** 侧「空位置的 out 未屏蔽污染归并（须对 out 也置 0）」。两者同属「CP 跨分片在线-softmax 合并对空分片的处理」这一族，但信号与修法各异。

## 参考实现及其约束

- vllm-ascend 昇腾 attention 后端 `vllm_ascend/attention/context_parallel/attention_cp.py`，函数 `_compute_prefill_context`。
- 约束（属该参考实现、非技术本身）：占位形状为 `(query.size(0), num_heads, head_size)`（output）与 `(query.size(0), num_heads, 1)`（lse），是该函数当下的 TND 出参形态；`head_size` 取 `self.head_size`；`fill_value` 分别为 `0` 与 `-torch.inf`。源未给 before→after 精度/性能数字（bugfix）。
- 断言只落到「须返回占位张量以参与合并」这一层，下游合并算法的内部归约不在本页覆盖范围。

## Evidence

- 空分片返回值、`-inf` LSE、TND-FIA 非空路径见 `vllm_ascend/attention/context_parallel/attention_cp.py` 的 `_compute_prefill_context`（`vllm-ascend@b1ce6f65fbf1911b92696c9706f33ad7851b0dba`，base `releases/v0.13.0`）。
- `-inf` LSE 作在线-softmax 合并中性元，与同函数既有 `torch.where(lse_mask, -torch.inf, prefix_chunk_lse)` 掩码语义同源。
- 回归用例 `test_models_chunked_prefill_with_empty_kvcache`（128/1/130/51/129 混合长度 prompt + `chunk_size=50` + `kv_cache_interleave_size=128` 构造空分片边界）断言消除 `TypeError`。
- 溯源下探：[vllm-ascend-pr-5844-0-13-0-cherry-pick-bugfix-cp-replace-none-with-zeros-inf-tensor-to-avoid](https://github.com/vllm-project/vllm-ascend/pull/5844)（sha `b1ce6f65fbf1911b92696c9706f33ad7851b0dba`）。