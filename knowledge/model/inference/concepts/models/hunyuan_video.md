---
type: Concept
title: HunyuanVideo
description: HunyuanVideo 是腾讯发布的开源 DiT 文生视频模型；cann-recipes-infer 在 Atlas A2/A3 上实现了 NPU 适配与完整的推理性能优化方案。其 5s 720p（129 帧）生成任务里 **Attention 占 DiT 端到端 81%、DiT 占端到端 95%**，所以优化围绕长序列 Attention（FIA 融合算子、Ulysses / Ring SP、Ulysses Anything Attention、FP8 量化 FA、TopK / SVG 块稀疏）、DiT 多步缓存（FBCache / TeaCache / TaylorSeer）以及 VAE 侧（空间并行、mask 缓存、虚拟内存取消 offload）展开。叠加最优组合（ulysses8 + 融合算子 + VAE 并行 + VAE 优化 + 虚拟内存 + UAA）可在 Atlas A3 达到 **e2e 7.81×**（3768.91 s → 482.65 s）；量化叠加（MXFP8 A8W8 + FP8 Attn + ulysses8 + VAE 并行）在 950PR 上 **e2e 1.38×**。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
- '950'
---

# HunyuanVideo

## Summary

HunyuanVideo 是腾讯发布的开源 DiT 文生视频模型；cann-recipes-infer 在 Atlas A2/A3 上实现了 NPU 适配与完整的推理性能优化方案。其 5s 720p（129 帧）生成任务里 **Attention 占 DiT 端到端 81%、DiT 占端到端 95%**，所以优化围绕长序列 Attention（FIA 融合算子、Ulysses / Ring SP、Ulysses Anything Attention、FP8 量化 FA、TopK / SVG 块稀疏）、DiT 多步缓存（FBCache / TeaCache / TaylorSeer）以及 VAE 侧（空间并行、mask 缓存、虚拟内存取消 offload）展开。叠加最优组合（ulysses8 + 融合算子 + VAE 并行 + VAE 优化 + 虚拟内存 + UAA）可在 Atlas A3 达到 **e2e 7.81×**（3768.91 s → 482.65 s）；量化叠加（MXFP8 A8W8 + FP8 Attn + ulysses8 + VAE 并行）在 950PR 上 **e2e 1.38×**。

## Architecture And Serving Traits

- **Backbone**：DiT（3D full attention），5s 720p ≈ 119k tokens 序列长度
- **双流/单流 Block**：Attention 按 `cu_seqlens` 拆分图像部分与文本部分分别计算 FA 再拼接（见下文 FIA 代码）
- **Text Encoder**：LLM + CLIP（源文档未展开）
- **目录结构**：
 - `models/hunyuan-video/sample_video.py` — 推理入口
 - `models/hunyuan-video/hyvideo/modules/{attention.py, norm_layers.py, posemb_layers.py, mxfp8_a8w8.py}` — 融合算子与量化
 - `models/hunyuan-video/hyvideo/sparse/sparse_config.yaml` — 块稀疏配置
 - `models/hunyuan-video/scripts/` — 运行脚本
 - `module/unified_sp/{core.py, uaa.py}` — Ulysses / Ring / UAA
 - `module/dit_cache/cache_method.py` — DiT cache
 - `module/blockwise_sparse/{sparse_method.py, offline_profiling/}` — 块稀疏
 - `module/fa_quant/fa_quant.py` — FP8 量化 attention
 - `module/vae_patch_parallel.py` — VAE patch 并行

### 统一推理拉起

部署经统一拉起架构 [mm-inference-launch](../frameworks/mm_inference_launch.md)：`models/hunyuan-video/infer.sh` + YAML 场景切换（`mm_function.sh` 因 `model_name` 含 `hunyuan-video` 选用 `--cache-config` 连字符参数名）。config 变体（`config/`）：`single`·`sp8`（基线，`dit_cache.method` 注释切 NoCache/FBCache/TeaCache/TaylorSeer）、`single_fp8`（FP8 FA + MXFP8 matmul，950PR）、`single_sparse`·`sp8_sparse`（块稀疏 Attention，默认 SVG 可切 TopK；`sp8_sparse` 为 Ulysses8）。

## 优化总览（源表）

| 优化方案 | 优化角度 | 方案介绍 |
| ------- | -------- | -------- |
| NPU 开箱，FA 融合算子适配 | 融合算子 | 使用 CANN 内部的 FIA 融合算子替代 transformer 中 attention 计算，算子内部通过 tiling 策略减少运行时的动态内存，并且加速 attention 计算。| | NPU RMS Norm 融合算子适配 | 融合算子 | 使用 CANN 内部的 RMSNorm 融合算子替代小算子实现。| | NPU ROPE 融合算子适配 | 融合算子 | 使用 CANN 内部的 `npu_rotary_mul` 融合算子替代小算子实现。| | Ulysses 序列并行 | 提高算力 | 将超长序列高效地切分到多个 NPU 上并行处理，每张卡负责处理自己负责的序列长度。Attention 以外切 S，Attention 处切 N。| | Ring Attention 序列并行 | 提高算力 | 与 Ulysses 类似，但 attention 计算时仍按 S 切分，通过 P2P 循环传递 KV 块。| | FBCache | 减少计算量 | 用第一个 DiT Block 的输出判断能否复用残差。| | TeaCache | 减少计算量 | 用第一个 img modulate 输出判断能否复用残差。| | Ulysses Anything Attention | 功能泛化 | 扩展 Ulysses 支持任意头数配置，动态填充 + 对齐。| | VAE 并行 | 提高算力 | 每张卡仅处理分配给自身的序列；为卡补充相邻卡部分序列解决卷积感受野。| | VAE 优化 | 减少计算量 | mask 缓存，减少重复构造。| | 取消 VAE offload | 减少搬运 | 开启虚拟内存，取消 CPU-offload。| | FP8 量化注意力 | 降低显存带宽 | per-block 动态量化 Q/K/V 为 FP8。| | MXFP8 矩阵量化 (A8W8) | 降低显存带宽 | DiT Linear 层 MXFP8，权重显存减半。| | 块稀疏 Attention | 减少计算量 | TopK / SVG 两种 predictor，基于 blitz_sparse_attention 算子。|

## Known Optimizations

### 融合算子

#### FIA 融合算子（`hyvideo/modules/attention.py:L119`）

qkv 按序列长度拆分，图像部分与文本部分分别计算 FA 再拼接：

```python
elif mode == "flash":
 scale = 1.0 / math.sqrt(d)
 if cu_seqlens_q is None:
 x = torch_npu.npu_fused_infer_attention_score(
 q, k, v,
 num_heads=n,
 input_layout="BNSD",
 scale=scale,
 )[0]
 else:
 attn1 = torch_npu.npu_fused_infer_attention_score(
 q[:, :, :cu_seqlens_q[1], :],
 k[:, :, :cu_seqlens_kv[1], :],
 v[:, :, :cu_seqlens_kv[1], :],
 num_heads=n, input_layout="BNSD", scale=scale,
 )[0]
 attn2 = torch_npu.npu_fused_infer_attention_score(
 q[:, :, cu_seqlens_q[1]:, :],
 k[:, :, cu_seqlens_kv[1]:, :],
 v[:, :, cu_seqlens_kv[1]:, :],
 num_heads=n, input_layout="BNSD", scale=scale,
 )[0]
 x = torch.cat([attn1, attn2], dim=2)
```

#### RMSNorm 融合算子（`hyvideo/modules/norm_layers.py:L55`）

小算子实现 `x * rsqrt(mean(x^2) + eps)` 替换为：

```python
def forward(self, x):
 return torch_npu.npu_rms_norm(x, self.weight, epsilon=self.eps)[0]
```

#### Rotary 融合算子（`hyvideo/modules/posemb_layers.py:L163`）

```python
xq_out = torch_npu.npu_rotary_mul(xq, cos, sin, rotary_mode="interleave")
xk_out = torch_npu.npu_rotary_mul(xk, cos, sin, rotary_mode="interleave")
```

### 序列并行

> 源：input shape `B, S, N, D`，序列并行沿 S 切分；attention 以外切 S，attention 处切 N（Ulysses）或继续切 S（Ring）。

- **Ulysses SP**：详见 [ulysses](../parallelism/ulysses.md)
- **Ring Attention SP**：详见 [ring-attention](../parallelism/ring_attention.md)
- **Ulysses Anything Attention (UAA)**：任意头数支持，详见 [ulysses](../parallelism/ulysses.md)

### FP8 量化注意力

- Q 使用 `group_size=128`，K/V 使用 `group_size=256`
- 详见 [fp8-attention](../quantization/fp8_attention.md)
- **仅支持 Ulysses SP，不支持 Ring Attention**

### MXFP8 矩阵量化 (A8W8)

- per-token 激活 + per-group（32）权重，E4M3FN + E8M0 scale
- 仅量化 `double_blocks` / `single_blocks` 中的 2D Linear，跳过 modulation 层与 1D 权重
- 详见 [mxfp8-a8w8](../quantization/mxfp8_a8w8.md)

### DiT Cache（FBCache / TeaCache / TaylorSeer）

- 详见 [dit-cache](../techniques/dit_cache.md)
- Cache + SP 场景需 all_reduce 同步 `l1_loss`

### VAE 并行 / 优化 / 取消 offload

- VAE 并行：沿序列切 latent，每卡补充邻居序列避免卷积拼接缝
- mask 缓存：减少重复构造 mask 的计算开销
- 虚拟内存 + 取消 VAE offload：利用 `torch_npu` 虚拟内存扩展可用空间，避免反复 Host↔Device 搬运
- 详见 [vae-patch-parallel](../parallelism/vae_patch_parallel.md)、[vae](../modules/vae.md)

### 块稀疏 Attention（TopK / SVG）

- 基于 [blitz_sparse_attention](https://gitcode.com/cann/ops-transformer/blob/ca41b0b5eb9dbf6eb94a58aa20fe379681c1d751/experimental/attention/blitz_sparse_attention/README.md) 算子
- 详见 [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- 配置入口：`models/hunyuan-video/hyvideo/sparse/sparse_config.yaml`；使能：`python sample_video.py --sparse_method TopK/SVG`
- 模型专用 predictor 适配器：`HunyuanVideoTopKAdapter` / `HunyuanVideoSVGAdapter`（继承 `TopKPredictor` / `SVGPredictor`，承载双流/单流 DiT block 的稀疏接入，`sparse_block.py` 的 `sparse_double_block_forward` / `sparse_single_block_forward`）

#### 块稀疏 × 序列并行协同

块稀疏当前只与单卡或 Ulysses 序列并行协同，**不与 Ring Attention 组合**。`sample_video.py` 在 `sparse_method != "no_sparse"` 时检测 `ring_degree > 1` 直接抛 `ValueError("Sparse attention does not support ring_degree > 1 in the current runtime.")`（"current runtime" 限制）。

与 Ulysses 组合（`ulysses_degree > 1`）时，各 head 的稀疏 mask 不同、实际计算量不均，`sample_video.py` 经 `hasattr` 守卫**仅对实现了该方法的 TopK 路径**（`TopKPredictor` / `HunyuanVideoTopKAdapter`）调 `apply_head_reorder_for_load_balance(ulysses_degree)` 对 head 做负载均衡重排（按 head 计算量贪心装箱到各 Ulysses rank，详见 `sparse_method.py`）；**SVG 路径未实现该方法，hasattr 守卫下跳过、不重排**。两路径均用 `parallel_sparse_attention`（`hyvideo/modules/attention.py:275`）作为 SP 下的执行入口。`config/sp8_sparse.yaml` 即 Ulysses8 + 块稀疏参考配置（默认 SVG，即走不重排路径）。

源文档 `Ulysses + TopK/SVG 联合优化` 性能（异构稀疏 vs 稠密 attention，DiT 耗时 s）：单卡 3587→2160；四卡 904→576（负载均衡 564）；八卡 464→335（负载均衡 321）。八卡相较稠密整体 ~1.39×–1.45×；四卡 head 已较均衡（负载均衡仅 ~12 s 增益），八卡并行度提升后 head 不均更突出（负载均衡 ~4.2%）。

## Benchmark

### 性能优化（Atlas A3，baseline 仅做 NPU 开箱 FIA 替换）

| 并行 | 融合算子 | ditcache | vae 并行 | vae 优化 | 虚拟内存<br/>取消 VAE offload | UAA | dit(s) | vae(s) | e2e | dit speedup | vae speedup | e2e speedup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1, **baseline** | x | x | x | x | x | x | 3634.48 | 133.15 | 3768.91 | 1.00 | 1.00 | 1.00 |
| | √ | x | x | √ | √ | x | 3568.36 | 39.66 | 3612.30 | 1.02 | 3.36 | 1.04 |
| | √ | FBCache | x | √ | x | x | 1693.89 | 83.03 | 1778.28 | 2.15 | 1.60 | 2.12 |
| | √ | TeaCache | x | √ | x | x | 1737.92 | 88.56 | 1830.75 | 2.09 | 1.50 | 2.06 |
| | √ | TaylorSeer | x | √ | x | x | 1405.68 | 92.85 | 1500.17 | 2.59 | 1.43 | **2.51** |
| ulysses5 | √ | x | √ | √ | √ | √ | 769.33 | 40.61 | 811.38 | 4.72 | 3.28 | 4.65 |
| ulysses8 | √ | x | √ | x | √ | x | 467.67 | 22.78 | 495.94 | 7.77 | 5.85 | 7.60 |
| | √ | x | √ | √ | √ | x | 465.43 | 12.40 | 487.68 | 7.81 | 10.74 | 7.73 |
| | √ | x | √ | √ | √ | √ | 477.12 | 13.10 | 482.65 | 7.62 | 10.16 | **7.81** |
| | √ | x | √ | √ | √ | 730, 1300 | 511.12 | 13.06 | 525.75 | 7.11 | 10.20 | 7.17 |

> Cache 配置：FBCache L1 阈值 0.05；TeaCache L1 阈值 0.15；TaylorSeer 算 1 跳 3，三阶泰勒。三种方法都能保持良好的推理精度（与 `cache_config.json` 配置一致）。

### 量化性能（950PR）

| 并行 | 融合算子 | matmul 量化 | fa 量化 | vae 并行 | dit(s) | vae(s) | e2e | dit speedup | vae speedup | e2e speedup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1, **baseline** | √ | x | x | x | 2548.49 | 31.76 | 2580.87 | 1.00 | 1.00 | 1.00 |
| | √ | √ | x | x | 2392.24 | 31.71 | 2424.52 | 1.07 | 1.00 | 1.06 |
| | √ | x | √ | x | 1606.29 | 31.70 | 1638.55 | 1.59 | 1.00 | 1.58 |
| | √ | √ | √ | x | 1539.24 | 31.43 | 1571.24 | 1.66 | 1.01 | 1.64 |
| ulysses8, **baseline** | √ | x | x | √ | 246.29 | 10.27 | 256.92 | 1.00 | 1.00 | 1.00 |
| | √ | √ | x | √ | 231.55 | 10.33 | 244.47 | 1.06 | 0.99 | 1.05 |
| | √ | x | √ | √ | 181.85 | 10.50 | 193.96 | 1.35 | 0.98 | 1.32 |
| | √ | √ | √ | √ | 170.04 | 10.17 | 185.54 | 1.45 | 1.01 | **1.38** |

### 块稀疏 Attention 性能（TopK vs SVG，单卡）

源文档「不同块稀疏 Attention 算法的性能数据」（`block_size_Q=128` / `block_size_K=512`；TopK 走离线 profiling 的 CAC 阈值 0.66、`sparse_time_step` 10-49；SVG `sparsity=0.8`、`sparse_time_step` 14-49）：

| Method | Sparsity | DiT Time (s) | E2E Time (s) | DiT Speedup | E2E Speedup |
| ------ | -------- | -----------: | -----------: | ----------: | ----------: |
| Baseline | – | 3459.52 | 3577.19 | 1.00× | 1.00× |
| TopK | 76% | **1839.48** | **1963.52** | **1.88×** | **1.82×** |
| SVG | 80% | 2036.18 | 2167.55 | 1.70× | 1.65× |

> TopK 在更低稀疏度（76%）下 DiT 加速反而高于 SVG（80%）：1.88× vs 1.70×；E2E 1.82× vs 1.65×。

### Ring Attention + TopK/SVG 性能（四卡）

> **Ring 路径块稀疏机制**（与 Ulysses 路径不同）：Ulysses 路径在 attention 前后复用 all-to-all，通信后每卡持有**完整序列 + 部分 head**，故可在完整序列语义上构造 `sabi/pattern` 并做 head 级负载均衡。**Ring 路径保留本卡 query 分片，并聚合全局 key/value**——Ring + TopK 用**本地 query 和全局 key/value** 构造 TopK `sabi`，并对首帧 query 用完整 key/value 做 dense attention 回填。**Ring + TopK + overlap** 进一步把 key/value 分成本地分片和其他分片：异步 `all_gather(k/v)` 的同时先算本地分片的稀疏 attention，通信完成后再算其他分片，并通过 **LSE 合并**两段输出。Ring + SVG 用本地 query 采样并同步 spatial/temporal MSE 中间量统一各卡 pattern，再按本地 query 全局时空坐标构造 `sabi`；当前 SVG overlap 配置复用普通 Ring + SVG 路径。配置：`config/sp8_sparse.yaml` 将 `ulysses-degree` 改 1、`ring-degree` 改 8 即走 Ring；`config/sp8_sparse_overlap.yaml` 为 Ring + TopK + overlap。

四卡 Ring Attention 下 DiT 推理耗时（s）：

| 方案 | `720*1280*209`, CAC `0.9` | `720*1280*209`, CAC `0.66` | `720*1280*129`, CAC `0.9` | `720*1280*129`, CAC `0.66` |
| ---- | ------------------------: | -------------------------: | ------------------------: | -------------------------: |
| Ring Attention | 2250 | 2250 | 949 | 949 |
| Ring + TopK | 1877 | 1385 | 812 | 554 |
| Ring + TopK + overlap | 1742 | 1327 | 822 | 584 |

**overlap-payoff 分析**（源结论）：

1. `720*1280*209` 场景：Ring + TopK 把耗时从 `2250s` 降到 `1385s`（CAC 0.66）；启用 overlap 进一步降到 `1327s`，相较稠密 Ring Attention 加速约 `1.70x`。
2. `720*1280*129` 场景：Ring + TopK 在 CAC `0.66` 时把耗时从 `949s` 降到 `554s`，相较稠密 Ring Attention 加速约 `1.71x`。
3. **overlap 收益与序列长度和 CAC 配置相关**：`720*1280*209`（长序列）收益更明显（1385→1327）；`720*1280*129`（短序列）下，通信与计算重叠的收益不足以抵消额外分段计算开销（CAC 0.9 时 812→822、CAC 0.66 时 554→584，overlap 反而略慢）。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md)（582 行完整优化实践）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/hunyuan-video/{README.md, sample_video.py, hyvideo/, scripts/}`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-video/{README.md, sample_video.py, hyvideo/, scripts/})
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/{unified_sp/, dit_cache/, blockwise_sparse/, fa_quant/, vae_patch_parallel.py}`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/{unified_sp/, dit_cache/, blockwise_sparse/, fa_quant/, vae_patch_parallel.py})
- 块稀疏 × SP 协同（@2c45117，MR!353 / MR!369）：[`models/hunyuan-video/sample_video.py#L116-L126`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/sample_video.py)（ring_degree ValueError + apply_head_reorder_for_load_balance 调用）、[`hyvideo/modules/attention.py#L275`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/hyvideo/modules/attention.py)（`parallel_sparse_attention`）、[`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md) `Ulysses + TopK/SVG 联合优化` 章节
- 块稀疏 Attention 性能表（TopK 76% / SVG 80%）：[cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md#不同块稀疏-attention算法的性能数据`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md)
- Ring + TopK / Ring + TopK + overlap 性能表与 Ring 路径块稀疏机制：[cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md#ring-attention--topksvg-性能数据`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md) `TopK/SVG + 序列并行联合优化` 章节

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [ulysses](../parallelism/ulysses.md)
- [ring-attention](../parallelism/ring_attention.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [dit-cache](../techniques/dit_cache.md)
- [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- [ring-attention-overlap](../techniques/ring_attention_overlap.md)
- [fp8-attention](../quantization/fp8_attention.md)
- [mxfp8-a8w8](../quantization/mxfp8_a8w8.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [hunyuan-image-3](hunyuan_image_3.md)
- [wan2.2-i2v](wan2_2_i2v.md)
- [sana-video](sana_video.md)

## Notes

- **unverified**：块稀疏 Attention 的端到端 speedup 与画质对比未在 benchmark 表中给出
- **gap**：源文档未给出 baseline 所用具体分辨率/帧数与 A3 硬件规格（只提"Atlas A3"），假定与正文描述 5s 720p 129 帧一致
- **gap**：与 HunyuanImage-3.0 的 MoE DoubleRouting 不同，HunyuanVideo 文档未涉及 MoE；HunyuanVideo DiT 纯 dense

<!-- cannbot:related:start -->
## 相关

- [Blockwise Sparse Attention (TopK / SVG)](../modules/blockwise_sparse_attention.md)（`related`）：“块稀疏 Attention ｜ 减少计算量 ｜ TopK / SVG 两种 predictor，基于 blitz_sparse_attention 算子”；“**Blockwise Sparse Attention** 是一种 Attention 组件变体：按 `［block_Q, block_K］` 粒度估计块的重要程度，只计算 TopK 重要块、跳过其余块”。模型卡的具体优化由候选卡定义算法机制和离线配置要求。
- [DiT Cache (FBCache / TeaCache / TaylorSeer)](../techniques/dit_cache.md)（`related`）：“DiT 多步缓存（FBCache / TeaCache / TaylorSeer）”；“DiT-Cache 是扩散生成模型推理加速的 Step-level 缓存框架”。模型采用候选卡定义的三种 step 级复用/预测机制，后者提供阈值与验证边界。
- [DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug](../../optimizations/experience/rules/dit_step_cache_fbcache_teacache.md)（`related`）：“config 变体（`config/`）：`single`·`sp8`（基线，`dit_cache.method` 注释切 NoCache/FBCache/TeaCache/TaylorSeer）”；“用 **step-level 残差缓存**跳过整段 DiT block 前向可得约 **2x** DiT 加速”。候选卡直接解释该配置的键控、阈值和 TeaCache 属性名故障。
- [FP8 Per-Block Dynamic Quant Attention](../quantization/fp8_attention.md)（`related`）：“FP8 量化注意力 ｜ 降低显存带宽 ｜ per-block 动态量化 Q/K/V 为 FP8”；“HunyuanVideo 在 DiT Attention 上引入的 FP8 量化方案：对 Q/K/V 做 **per-block 动态量化**”。两卡共同描述模型的 FP8 Attention 生产配置与算子消费合同。
- [MM Inference Launch（多模态生成模型统一推理拉起架构）](../frameworks/mm_inference_launch.md)（`related`）：“部署经统一拉起架构 ［mm-inference-launch］(../frameworks/mm_inference_launch.md)：`models/hunyuan-video/infer.sh` + YAML 场景切换”；“MM Inference Launch 是 cann-recipes-infer 中 4 个多模态生成模型（Wan2.2-I2V / HunyuanVideo / SANA-Video / HunyuanImage-3.0）的统一推理拉起架构”。前者把 HunyuanVideo 的入口和配置交给后者，形成直接部署合同。
- [MXFP8 A8W8 (DiT Linear)](../quantization/mxfp8_a8w8.md)（`related`）：“MXFP8 矩阵量化 (A8W8) ｜ 降低显存带宽 ｜ DiT Linear 层 MXFP8，权重显存减半”；“HunyuanVideo 针对 DiT 中 Linear 层（MLP / 投影层）的 Micro-scaling FP8 矩阵量化方案”。前者是模型配置，后者给出权重/激活分组和算子调用边界。
- [Ring Attention Overlap](../techniques/ring_attention_overlap.md)（`related`）：“**Ring + TopK + overlap** 进一步把 key/value 分成本地分片和其他分片：异步 `all_gather(k/v)` 的同时先算本地分片的稀疏 attention”；“多卡 Ring Attention 的 P2P / AllGather 通信通常与 FA 计算串行，利用率低”。前者是模型落地，后者定义异步通信、本地 FA 与 LSE 合并机制。
- [Ring Attention Sequence Parallelism](../parallelism/ring_attention.md)（`related`）：“Ring Attention 序列并行 ｜ 提高算力 ｜ 与 Ulysses 类似，但 attention 计算时仍按 S 切分，通过 P2P 循环传递 KV 块”；“Ring Attention 是另一种长序列 SP 方案：与 Ulysses 不同，**attention 内部也保持序列切分**”。模型卡给出 Ring 选项，候选卡补足实际 AllGather/LSE 路线与适用边界。
- [Ulysses Sequence Parallelism](../parallelism/ulysses.md)（`related`）：“Ulysses 序列并行 ｜ 提高算力 ｜ 将超长序列高效地切分到多个 NPU 上并行处理，每张卡负责处理自己负责的序列长度”；“Ulysses 是面向**长序列多头注意力**的序列并行策略”。模型明确采用 Ulysses，候选卡给出 all-to-all 布局转换和整除边界。
- [VAE Patch Parallel](../parallelism/vae_patch_parallel.md)（`related`）：“VAE 并行 ｜ 提高算力 ｜ 每张卡仅处理分配给自身的序列；为卡补充相邻卡部分序列解决卷积感受野”；“**HunyuanVideo 是另一份实现**：用 `models/hunyuan-video/hyvideo/vae/vae_parallel.py` 的沿单一序列维 1D overlap-chunk decode”。模型卡的 VAE 并行由候选卡精确限定为 HunyuanVideo 专用一维重叠切分。
- [块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）](../../guides/experience/interventions/blockwise_sparse_attention_ulysses_integration.md)（`related`）：“`single_sparse`·`sp8_sparse`（块稀疏 Attention，默认 SVG 可切 TopK；`sp8_sparse` 为 Ulysses8）”；“长序列视频 ［DiT］(../../../concepts/modules/dit.md) 想同时吃到两种降本：［块稀疏 Attention］(../../../concepts/modules/blockwise_sparse_attention.md)（TopK/SVG 丢弃低注意力块）减计算量，［Ulysses］(../../../concepts/parallelism/ulysses.md) 序列并行摊显存/时延”。候选卡就是该配置组合的布局重排与负载均衡实施指南。
- [多卡 Ring/序列并行注意力用异步 all-gather + 本地 FA + LSE 合并掩盖 KV 通信](../../guides/experience/interventions/ring_attention_comm_compute_overlap_lse_merge.md)（`related`）：“通信完成后再算其他分片，并通过 **LSE 合并**两段输出”；“用 all-gather 一次性收全环 KV，配合异步启动 + 本地先算 + LSE 合并，把通信掩盖在第一段本地注意力里”。模型卡的实际两段计算由指南给出可执行步骤和 LSE 前置。
- [大分辨率 VAE encode/decode 多卡空间并行（按算子选通信 + 边界 halo/overlap 补偿）](../../guides/experience/interventions/vae_multicard_spatial_parallel.md)（`related`）：“每张卡仅处理分配给自身的序列；为卡补充相邻卡部分序列解决卷积感受野”；“VAE decode 沿 latent 宽度维在各 rank 间切分：因卷积感受野，非首片向左借 `overlap_size`、各片向右借到边界”。候选指南把模型总览中的 VAE 并行扩成可执行切分、去 pad 和 all_gather 流程。
- [视频 DiT 块稀疏 Attention 使能 — must-keep 首帧/文本 + TopK/SVG 选型（TopK 需离线 profiling）](../../optimizations/experience/rules/video_dit_blockwise_sparse_attention.md)（`related`）：“模型专用 predictor 适配器：`HunyuanVideoTopKAdapter` / `HunyuanVideoSVGAdapter`”；“长序列视频 ［dit］(../../../concepts/modules/dit.md)（本经验覆盖 ［hunyuan-video］(../../../concepts/models/hunyuan_video.md)）”。候选卡直接给出模型专用 must-keep、TopK profiling 与 SVG 选型步骤。
- [视频 DiT 量化降显存 / 带宽：per-block FP8 注意力（主要收益，Ulysses-only）+ MXFP8 matmul（跳过 adaLN）](../../guides/experience/interventions/video_dit_fp8_mxfp8_quantization.md)（`related`）：“`single_fp8`（FP8 FA + MXFP8 matmul，950PR）”；“两者都需 ［ascend-950］(../../../concepts/platforms/ascend_950.md)（Atlas 950）级 FP8 硬件”。模型配置的双量化组合由候选指南给出量化范围、硬件门控与 Ulysses-only 限制。
<!-- cannbot:related:end -->
