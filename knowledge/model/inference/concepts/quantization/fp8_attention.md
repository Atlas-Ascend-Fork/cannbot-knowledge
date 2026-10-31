---
type: Concept
title: MXFP8 量化注意力（HunyuanVideo）
description: 说明当前HunyuanVideo的TND动态MXFP8注意力：Q/K沿hidden维采用mode6，V沿序列轴采用mode8，限定纯Ulysses、950及CANN9.1+并保留错误定位边界。
tags:
- task.design
- topic.precision
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fa_quant/fa_quant.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/unified_sp/core.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/inference.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T12:28:04Z'
platforms:
- '950'
---

# MXFP8 量化注意力（HunyuanVideo）

## 当前机制

当前 `module/fa_quant` 只导出 `npu_mxfp8_quant` 与 `npu_mxfp8_attn`。HunyuanVideo 的量化注意力使用动态 MXFP8，不再使用旧 `npu_group_quant`、固定Q块128/KV块256或 `fa_perblock_fp8` 配置。

Q/K/V 的输入是 `[B,S,N,D]`；量化前合并B与S为TND。量化值为E4M3FN，scale为E8M0。分组方向与FIA v2模式必须配套：

| 张量 | npu_dynamic_mx_quant 的轴 | FIA v2 quant_mode |
| --- | --- | --- |
| Q | `axis=-1`，沿hidden dim | `6` |
| K | `axis=-1`，沿hidden dim | `6` |
| V | `axis=0`，沿展平后的序列轴 | `8` |

随后调用 `npu_fused_infer_attention_score_v2`，传入三组量化值与scale、TND布局、query/key各自累计序列长度，`sparse_mode=0`，输出dtype取原始Q的dtype。默认softmax scale为 `1/sqrt(D)`，输出恢复为BSND。

## 布局与调用边界

```python
from module.fa_quant import npu_mxfp8_attn

out = npu_mxfp8_attn(q, k, v, softmax_scale=None)
```

当前量化函数直接使用 `.view(B*S,N,D)`，输入必须具备可view的布局；非连续输入需先核对stride与必要的连续化开销。封装只支持TND，其他 `output_layout` 明确报错。

这条封装没有通用mask或causal入参，使用非稀疏FIA模式；不能从外层attention签名推导任意因果、稀疏或mask语义都被量化路径保留。

## 序列并行

`UnifiedSPAttention(..., fa_mxfp8=True)` 选择当前量化函数。`ring_world_size>1` 时构造直接抛错，因此仅允许单卡或纯Ulysses，不能与Ring组合。

当前core按有效序列与padding分段时，两段都进入 `_forward_core`，使用同一已选attention函数；旧版“只有有效联合段量化、padding自动走普通FIA”的描述不适用于当前实现。

## 平台、错误与质量验证

HunyuanVideo入口把这组量化限定到950类设备，拒绝Ascend910B/Ascend910_93。FIA量化调用要求CANN 9.1.0及以上。

注意 `npu_mxfp8_attn` 会把FIA调用中的所有 `RuntimeError` 包装为CANN版本提示；看到该提示时仍需读取异常cause，核对真实版本、算子包、dtype、shape与layout。输入view或前置MX量化发生的错误不经过这段包装，不能把所有失败都归因于版本。

单独对照BF16与MXFP8的误差、视频质量、峰值内存和端到端时间；来源没有给出统一画质保证。配置与对照方法见[950接入案例](../../optimizations/cases/hunyuan_video_950_fp8_quantization.md)，Linear量化见[MXFP8 A8W8](mxfp8_a8w8.md)，来源性能数据见[950观测](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)。本仓未执行设备复测。
