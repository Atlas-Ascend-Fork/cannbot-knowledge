---
type: Concept
title: Wan2.2-I2V
description: Wan2.2-I2V 是阿里万相 2.2 的 Image-to-Video 生成模型，cann-recipes-infer 在 NPU 上提供融合算子适配、8 卡 VAE 并行、CFG 并行、Ring Attention Overlap、DiT-Cache（FBCache / TeaCache）等优化。代码入口为 `models/wan2.2-i2v/generate.py` + `run.sh`，DiT 结构位于 `models/wan2.2-i2v/wan/`。Cache 框架通过 `models/wan2.2-i2v/wan/cache/cache_config.json` 热切换。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- agnostic
---

# Wan2.2-I2V

## Summary

Wan2.2-I2V 是阿里万相 2.2 的 Image-to-Video 生成模型，cann-recipes-infer 在 NPU 上提供融合算子适配、8 卡 VAE 并行、CFG 并行、Ring Attention Overlap、DiT-Cache（FBCache / TeaCache）等优化。代码入口为 `models/wan2.2-i2v/generate.py` + `run.sh`，DiT 结构位于 `models/wan2.2-i2v/wan/`。Cache 框架通过 `models/wan2.2-i2v/wan/cache/cache_config.json` 热切换。

## Architecture And Serving Traits

- Image-to-Video DiT 模型：输入参考图像 + 文本 prompt，输出视频
- 主要源文件：
 - `models/wan2.2-i2v/generate.py` / `run.sh` / `set_env.sh`
 - `models/wan2.2-i2v/wan/modules/{attention.py, model.py}` — FA / RoPE / RMSNorm / LayerNorm 融合
 - `models/wan2.2-i2v/wan/image2video.py` — CFG 并行调度
 - `models/wan2.2-i2v/wan/vae_patch_parallel.py` — 8 卡 VAE 并行
 - `models/wan2.2-i2v/wan/cache/{cache_block.py, cache_config.json}` — 适配 dit_cache_step 的双流模块
 - `module/dit_cache_step/cache_step.py` — Step-level DiT Cache 实现
- CFG 串行特点 → TeaCache 使用官方 cond/uncond 分开管理版本

### 统一推理拉起

部署经统一拉起架构 [mm-inference-launch](../frameworks/mm_inference_launch.md)：`models/wan2.2-i2v/infer.sh` + YAML 场景切换（统一拉起 refactor，commit 06656b0，晚于上文融合算子内容钉定的 2f82d10）。config 变体（`config/`）：`14b_single`（单卡基线，`dit_cache.method` 注释切 NoCache/FBCache/TeaCache）、`14b_cfg2_ulysses4`（8 卡，CFG2 × Ulysses4 + VAE 并行 + DiT/T5 FSDP，多卡侧固定 NoCache）。

## Known Optimizations

### 融合算子适配

#### npu_fused_infer_attention_score

替代 FlashAttention。启动依赖：

```python
# 来源：generate.py L30 后
import torch_npu
torch_npu.npu.set_compile_mode(jit_compile=False)
torch.npu.config.allow_internal_format = False
from torch_npu.contrib import transfer_to_npu
```

在 `wan/modules/attention.py:L69` `npu_fused_attention` 中：

```python
attention_out, _ = torch_npu.npu_fused_infer_attention_score(
 q, k, v,
 actual_seq_lengths=actual_seq_lengths,
 actual_seq_lengths_kv=actual_seq_lengths_kv,
 num_heads=N,
 scale=float(softmax_scale),
 input_layout="BNSD",
 num_key_value_heads=num_key_value_heads,
 pre_tokens=65535,
 next_tokens=65535 if not causal else 0,
 sparse_mode=0,
 inner_precise=0,
)
attention_out = attention_out.transpose(1, 2).contiguous
return attention_out.to(out_dtype)
```

#### npu_rotary_mul

在 `wan/modules/model.py:L58` `rope_apply` 中：

```python
@torch.amp.autocast('cuda', enabled=False)
def rope_apply(x, grid_sizes, freqs_list):
 s, n, c = x.size(1), x.size(2), x.size(3)
 output = []
 for i, (f, h, w) in enumerate(grid_sizes.tolist):
 x_i = x[i, :s].reshape(1, s, n, c)
 if not x_i.is_contiguous:
 x_i = x_i.contiguous
 cos, sin = freqs_list[i]
 if cos.dim == 3:
 cos = cos.unsqueeze(0)
 sin = sin.unsqueeze(0)
 cos = cos.to(dtype=x_i.dtype, device=x_i.device)
 sin = sin.to(dtype=x_i.dtype, device=x_i.device)
 x_i = torch_npu.npu_rotary_mul(
 input=x_i, r1=cos, r2=sin, rotary_mode="interleave",
 )
 output.append(x_i)
```

#### npu_rms_norm

在 `wan/modules/model.py:L87` `WanRMSNorm.forward`：

```python
def forward(self, x):
 return torch_npu.npu_rms_norm(x, self.weight, epsilon=self.eps)[0]
```

#### npu_layer_norm_eval 与 LN+Modulate 融合

在 `wan/modules/model.py:L103` `WanLayerNorm.forward`：

```python
return torch_npu.npu_layer_norm_eval(
 x, normalized_shape=[self.dim], weight=self.weight, bias=self.bias, eps=self.eps,
)
```

进一步，每个 block 内有 4 个 LN，其中 3 个 LN 的 gemma/beta 固定为初始 1 和 0。本样例将这 3 个 LN 与后续 modulate 融合：按 `(x - mean) / var * 1 + 0) * (scale + 1) + shift` 推导，融入 `npu_layer_norm_eval` 的 `weight = 1.0 + scale`、`bias = shift`：

```python
# 来源：wan/modules/model.py:L119 FusedLayerNormModulate
def forward(self, x, weight, shift):
 weight = 1.0 + scale
 bias = shift
 return torch_npu.npu_layer_norm_eval(
 x, normalized_shape=[self.dim], weight=weight, bias=bias, eps=self.eps,
 )
```

> 注：源代码片段中使用了 `weight = 1.0 + scale`，但函数入参名为 `weight`（形参）而非 `scale`。ambiguity：源文档贴出的片段 `weight = 1.0 + scale` 中 `scale` 与形参 `weight` 的对应关系不明，此处原样保留。

### 8 卡 VAE 并行

> 源：通过空间并行的方式实现，将大尺寸图像在高度和宽度维度上切分成多个块，分配给不同的 NPU 进程并行处理。卷积与邻居交换边界；attention 全局收集所有 K,V；插值扩展边界、计算后再裁剪。

详见 [vae-patch-parallel](../parallelism/vae_patch_parallel.md)、[vae](../modules/vae.md)。实现脚本：`wan/vae_patch_parallel.py`。

### CFG 并行

`wan/image2video.py` 的实现已在 [cfg-parallel](../parallelism/cfg_parallel.md) Mechanism 节完整引用。去噪 step 循环在 L441，启用判据 `get_classifier_free_guidance_world_size() == 2`（L454）。

### Ring Attention Overlap

> 源：异步启动 AllGather 收集其他卡的 KV 数据，同时立即使用本地 KV 计算第一个 FA；待 AllGather 完成后把远程多个 chunks 合并为一个长序列一次性计算第二个 FA，最后用 LSE 合并两次 attention 输出。

详见 [ring-attention-overlap](../techniques/ring_attention_overlap.md)。

### DiT-Cache（Step-level）

集成 [FBCache](https://github.com/chengzeyi/ParaAttention)、[TeaCache](https://liewfeng.github.io/TeaCache/)。因 WAN2.2 CFG 串行特点，采用 [TeaCache4Wan2.1 cond/uncond 分别管理版](https://github.com/ali-vilab/TeaCache/tree/7c10efc4702c6b619f47805f7abe4a7a08085aa0/TeaCache4Wan2.1)。实现路径：`module/dit_cache_step/cache_step.py` + `wan/cache/cache_block.py`。

通过 `wan/cache/cache_config.json` + `run.sh` 的 `--cache_config` 参数热切换。默认 `NoCache`，将 `cache_forward` 改为 `FBCache` 或 `TeaCache` 启用：

```json
{
 "cache_forward": "NoCache",
 "comment": "choose from FBCache/TeaCache, otherwise use NoCache",
 "enable_separate_cfg": true,
 "FBCache": {
 "cache_name": "FBCache",
 "rel_l1_thresh": 0.05,
 "latent": "latent",
 "judge_input": "cache_latent"
 },
 "TeaCache": {
 "cache_name": "TeaCache",
 "rel_l1_thresh": 0.1,
 "coefficients": [733.226126, -401.131952, 67.5869174, -3.149879, 0.0961237896],
 "latent": "latent",
 "warmup": 2,
 "judge_input": "modulated_inp"
 },
 "NoCache": {"cache_name": "NoCache"}
}
```

参数：`rel_l1_thresh` 越大跳步越多、精度损失越大；`warmup` 用于在 step 开始/结束的剧变阶段强制计算；`enable_separate_cfg` 必须在 CFG 串行时开启。

目录结构：

```
cann-recipes-infer
 models/
 wan2.2-i2v/
 set_env.sh # 激活 module 环境
 wan/
 cache/
 cache_block.py # dit-cache 适配双流模块
 cache_config.json # 默认 cache 参数位置
 module/
 dit_cache_step/ # step-level 实现逻辑
```

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/wan2.2-i2v/{generate.py, run.sh, set_env.sh, wan/}`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/wan2.2-i2v/{generate.py, run.sh, set_env.sh, wan/})
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/dit_cache_step/cache_step.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/dit_cache_step/cache_step.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 统一推理拉起（`infer.sh` + `config/`，引入于 refactor commit 06656b0）：[`models/wan2.2-i2v/infer.sh`](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/infer.sh)、[`config/14b_cfg2_ulysses4.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml)

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [ring-attention](../parallelism/ring_attention.md)
- [cfg-parallel](../parallelism/cfg_parallel.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [dit-cache](../techniques/dit_cache.md)
- [ring-attention-overlap](../techniques/ring_attention_overlap.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-video](hunyuan_video.md)
- [hunyuan-image-3](hunyuan_image_3.md)

## Notes

- **性能数据范围**：源未给出 benchmark 端到端数据
- **文件名差异**：源 optimization.md 将该文件误写作 `iamge2video.py`，真实代码文件为 `image2video.py`
- **示例限制**：`FusedLayerNormModulate.forward` 中 `scale` 变量未在片段作用域定义，源代码片段可能有遗漏