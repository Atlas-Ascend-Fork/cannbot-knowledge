---
type: Concept
title: FP8 Per-Block Dynamic Quant Attention
description: 解释 per-block FP8 与 MXFP8 注意力量化的分组、scale、layout和并行边界；性能统一引用平台观测，不承诺无损。
tags:
- task.design
- topic.precision
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-22T10:36:46Z'
platforms:
- '950'
---
# FP8 Per-Block Dynamic Quant Attention

## Summary

HunyuanVideo 在 DiT Attention 上引入的 FP8 量化方案：对 Q/K/V 做 **per-block 动态量化**（Q 用 `group_size=128`、K/V 用 `group_size=256`，FP8 E4M3 格式），再调用 `torch_npu.npu_fused_infer_attention_score_v2` 在算子内部完成反量化 + 注意力计算，输出 BF16。显著降低注意力的显存带宽，适合带宽受限场景。结果见[HunyuanVideo 950来源观测](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)，不作为量化后的质量保证。

## Mechanism

### Per-block 动态量化

- **Q**：`group_size=128`，更小块 → 更高精度（Q 直接影响 softmax 分数）
- **K/V**：`group_size=256`，更大块 → 压缩率更高，容忍量化噪声
- **格式**：FP8 E4M3FN（4 位指数 + 3 位尾数），平衡动态范围与精度
- **quant_mode=7**：算子内部 per-block dynamic 反量化 → QK^T → Softmax → ×V → BF16

量化核心：

```python
# 来源：docs/models/hunyuan-video/hunyuan_video_optimization.md「FP8 量化注意力」节（精简版；.py 原文形参为 x）
def npu_group_quant(input, group_size, dst_type=torch.float8_e4m3fn, output_bnsd=True):
 b, s, n, d = input.shape
 input = input.contiguous().view(b * s, n * d)
 input_quant, input_scale = torch_npu.npu_dynamic_block_quant(
 input,
 row_block_size=group_size,
 col_block_size=d,
 dst_type=dst_type,
 )
 input_quant = input_quant.contiguous().view(b, s, n, d)
 input_scale = input_scale.contiguous().view(b, -1, n, 1)
 return input_quant.transpose(1, 2), input_scale.transpose(1, 2)
```

FP8 融合 attention：

```python
# 来源：docs/models/hunyuan-video/hunyuan_video_optimization.md「FP8 量化注意力」节（精简版；.py 原文含 num_key_value_heads=n、softmax_scale 形参）
def npu_fp8_attn(q, k, v, dst_type=torch.float8_e4m3fn):
 q_quant, q_scale = npu_group_quant(q, 128, dst_type, output_bnsd=True)
 k_quant, k_scale = npu_group_quant(k, 256, dst_type, output_bnsd=True)
 v_quant, v_scale = npu_group_quant(v, 256, dst_type, output_bnsd=True)

 attn_out = torch_npu.npu_fused_infer_attention_score_v2(
 q_quant, k_quant, v_quant,
 num_query_heads=n,
 input_layout="BNSD",
 softmax_scale=1.0 / math.sqrt(d),
 query_quant_mode=7,
 key_quant_mode=7,
 value_quant_mode=7,
 dequant_scale_query=q_scale,
 dequant_scale_key=k_scale,
 dequant_scale_value=v_scale,
 )[0]
 return attn_out.transpose(1, 2).to(torch.bfloat16)
```

### 第二机制：MXFP8 量化注意力（动态 MX 量化，区别于上面的 per-block FP8）

> HunyuanVideo 源文档「MXFP8 量化注意力」节给出了与上面 per-block FP8 不同的**第二种量化注意力机制**：用 **MXFP8（Micro-scaling FP8）动态量化** 把 Q/K/V 量化为 MXFP8 格式（`torch_npu.npu_dynamic_mx_quant`），缩放因子用 **E8M0**（纯指数，仅 1 字节），同样降低注意力的显存带宽，适用于显存/带宽受限场景。

**与 per-block FP8 的核心区别**：

| 维度 | per-block FP8（上文） | MXFP8 量化注意力（本节） |
| ---- | -------------------- | ------------------------ |
| 量化算子 | `npu_dynamic_block_quant`（按 `row_block_size`×`col_block_size` 块量化） | `npu_dynamic_mx_quant`（per-token / per-channel group MX 量化） |
| 量化函数 | `npu_group_quant` → `npu_fp8_attn` | `npu_mxfp8_quant` → `npu_mxfp8_attn` |
| scale 格式 | block scale（FP8 E4M3 量化值） | **E8M0**（纯指数，1 字节，`torch_npu.float8_e8m0fnu`） |
| 数值格式 | IEEE FP8 E4M3FN（`torch.float8_e4m3fn`） | IEEE FP8 E4M3FN（`torch.float8_e4m3fn`） |
| quant_mode | Q/K/V 全部 `=7`（per-block dynamic） | Q/K **`=6`**（per-channel group，沿 hidden dim 分组）、V **`=8`**（per-token group，沿 seq_len 分组） |
| input_layout | `BNSD` | `TND` |
| 分组方向 | Q `group_size=128`、K/V `group_size=256`（行块） | Q/K 沿 hidden dim 分组（`axis=-1`）、V 沿 seq_len 分组（`axis=0`） |
| 启用开关 | `UnifiedSPAttention(..., fa_perblock_fp8=True)` | `UnifiedSPAttention(..., fa_mxfp8=True)` |

**量化原理**（源文档「量化原理」）：

1. **per-token / per-channel group MX 量化**：对 Q/K/V 分别做动态 MX 量化，每个块组独立计算缩放因子，缩放因子采用 E8M0 格式（纯指数表示），仅占 1 字节。
2. **差异化量化模式**：
   - **Query/Key**：沿 hidden dim 方向分组，即 FIA_v2 算子入参 `quant_mode=6`。
   - **Value**：沿 seq_len 方向分组，即 FIA_v2 算子入参 `quant_mode=8`。
3. **FP8 E4M3 格式**：采用 IEEE FP8 E4M3 格式（4 位指数，3 位尾数），在动态范围和精度之间取得良好平衡。

MX 动态量化核心（`module/fa_quant/fa_quant.py`）：

```python
def npu_mxfp8_quant(x, dst_type=torch.float8_e4m3fn, output_layout="TND", axis=-1):
    """Perform MXFP8 dynamic quantization for NPU fused attention."""
    b, s, n, d = x.shape

    if output_layout == "TND":
        x_tnd = x.contiguous().view(b * s, n, d)
        x_quant, x_scale = torch_npu.npu_dynamic_mx_quant(
            x_tnd, dst_type=dst_type, axis=axis
        )

    return x_quant, x_scale
```

融合注意力计算（`npu_mxfp8_attn`）：

```python
def npu_mxfp8_attn(q, k, v, dst_type=torch.float8_e4m3fn, softmax_scale=None):
    """Perform MXFP8 quantized attention computation on NPU."""
    b, s, n, d = q.shape
    kv_s = k.shape[1]
    out_dtype = q.dtype

    if softmax_scale is None:
        softmax_scale = 1.0 / math.sqrt(d)

    q_quant, q_scale = npu_mxfp8_quant(q, dst_type=dst_type, output_layout="TND")
    k_quant, k_scale = npu_mxfp8_quant(k, dst_type=dst_type, output_layout="TND")
    v_quant, v_scale = npu_mxfp8_quant(v, dst_type=dst_type, output_layout="TND", axis=0)

    attn_out = torch_npu.npu_fused_infer_attention_score_v2(
        q_quant, k_quant, v_quant,
        actual_seq_qlen=_actual_seq_lens(b, s, q.device),
        actual_seq_kvlen=_actual_seq_lens(b, kv_s, k.device),
        dequant_scale_query=q_scale,
        dequant_scale_key=k_scale,
        dequant_scale_value=v_scale,
        num_query_heads=n,
        num_key_value_heads=k.shape[2],
        softmax_scale=softmax_scale,
        input_layout="TND",
        sparse_mode=0,       # non-sparse
        query_quant_mode=6,  # per-channel group quant
        key_quant_mode=6,    # per-channel group quant
        value_quant_mode=8,  # per-token group quant
        query_dtype=torch.float8_e4m3fn,
        key_dtype=torch.float8_e4m3fn,
        value_dtype=torch.float8_e4m3fn,
        dequant_scale_query_dtype=torch_npu.float8_e8m0fnu,
        dequant_scale_key_dtype=torch_npu.float8_e8m0fnu,
        dequant_scale_value_dtype=torch_npu.float8_e8m0fnu,
        out_dtype=out_dtype
    )[0]

    return attn_out.contiguous().view(b, s, n, d)
```

**算子内部流程**（`npu_fused_infer_attention_score_v2`，源「量化模式说明」）：用 E8M0 缩放因子对量化值反量化 → Q×Kᵀ → Softmax → Attn×V → 返回原始精度格式输出。`npu_dynamic_mx_quant` 负责动态 MX 量化。

**使用方式**：

```python
from module.fa_quant import npu_mxfp8_attn

# 独立使用
output = npu_mxfp8_attn(q, k, v, dst_type=torch.float8_e4m3fn)

# 结合序列并行
attn = UnifiedSPAttention(
    ulysses_group=ulysses_group,
    ring_group=None,
    fa_mxfp8=True,  # 启用 MXFP8 量化注意力
)
```

**限制**（源「限制说明」）：

- MXFP8 量化注意力当前**仅支持 Ulysses 序列并行，不支持 Ring Attention**（与 per-block FP8 相同限制）。
- 建议在精度敏感场景做对比测试，选择合适的量化参数。

## Accuracy Impact

- Per-block 相比 per-tensor 量化精度更高（块内独立 scale）
- 源文档定性结论：精度与 group_size 相关，较小 group_size 精度更高但 scale 数量更多；建议精度敏感场景对比测试选参数
- unverified：源未给出画质指标（PSNR / CLIP score 等）

## Applicable Scenarios

- 显存受限或带宽受限的长序列 DiT（HunyuanVideo 5s 720p）
- 与 Ulysses SP 配合：

 ```python
 attn = UnifiedSPAttention(
 ulysses_group=ulysses_group,
 ring_group=None,
 fa_perblock_fp8=True,
 )
 ```

## Constraints

- **仅支持 Ulysses 序列并行，不支持 Ring Attention**（HunyuanVideo 源文档明示）
- 依赖 `torch_npu.npu_fused_infer_attention_score_v2` 的 `query/key/value_quant_mode=7` 与 `npu_dynamic_block_quant` 算子
- Group size 选择需权衡精度与 scale 元数据开销

## Known Results

单卡与Ulysses8各组来源数据统一见[HunyuanVideo 950来源观测](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)；量化实现的选择与质量验收见[950案例](../../optimizations/cases/hunyuan_video_950_fp8_quantization.md)。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md) FP8 量化注意力
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/fa_quant/fa_quant.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/fa_quant/fa_quant.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md#mxfp8-量化注意力`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md)（第二机制：MXFP8 量化注意力，`npu_mxfp8_attn` / `npu_dynamic_mx_quant`，quant_mode 6/8）

## Links

- [mxfp8-a8w8](mxfp8_a8w8.md)
- [dit](../modules/dit.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [ulysses](../parallelism/ulysses.md)
