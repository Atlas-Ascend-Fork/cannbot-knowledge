---
type: Concept
title: HunyuanImage-3.0
description: HunyuanImage-3.0 是腾讯混元发布的 MoE + DiT 文生图模型，cann-recipes-infer 提供 Atlas A2/A3 上的 TP 推理方案，并在其上叠加 **Attention TP、MoE TP、MoE EP（DoubleRouting）、MoE 多流、VAE 并行、CFG 并行、通算融合（AllGatherMM / MMReduceScatter）** 以及若干冗余 cast 消除。关键优化与相应源图并存，结构化拓扑用 mermaid 重绘。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
---

# HunyuanImage-3.0

## Summary

HunyuanImage-3.0 是腾讯混元发布的 MoE + DiT 文生图模型，cann-recipes-infer 提供 Atlas A2/A3 上的 TP 推理方案，并在其上叠加 **Attention TP、MoE TP、MoE EP（DoubleRouting）、MoE 多流、VAE 并行、CFG 并行、通算融合（AllGatherMM / MMReduceScatter）** 以及若干冗余 cast 消除。关键优化与相应源图并存，结构化拓扑用 mermaid 重绘。

## Architecture And Serving Traits

- **Backbone**：DiT 骨干 + MoE FFN，文本 encoder 为 Hunyuan 系 LLM
- **并行维度**：Attention 切头 + 线性行切 → Attention TP；MoE gate/up 列切 + down 行切；可切换 EP + DoubleRouting；CFG Parallel 在此基础上叠加
- **代码路径**：
 - `models/hunyuan-image-3.0/run_image_gen.py` — 生成入口
 - `models/hunyuan-image-3.0/model_adaptor.py` + `adaptor_patches/` — monkey patch 注入
 - `models/hunyuan-image-3.0/utils/` — 工具
 - `module/vae_patch_parallel.py` — VAE 并行（共享）

### 统一推理拉起

部署经统一拉起架构 [mm-inference-launch](../frameworks/mm_inference_launch.md)：`models/hunyuan-image-3.0/infer.sh` + YAML 场景切换，`entry_script` 为 `run_image_gen.py`，启动器默认 `torchrun`。config 变体（`config/`）：`ep8_cfg`（`world_size=16`，Attention TP8 + MoE EP8（`moe-ep: true`）+ CFG 并行 + VAE 并行）。

> 注：本段 `infer.sh` + `config/ep8_cfg.yaml` 统一拉起结构在正文主钉 @2f82d10 尚不存在（彼时启动脚本为 `demo.sh`，无 `config/`），系更晚的 **@2c45117** 引入；`ep8_cfg.yaml@2c45117` 字段：`world_size: 16`、`moe-ep: true`、`entry_script: run_image_gen.py`、`env_vars.CFG_PARALLEL=1` / `USE_VAE_PARALLEL=1`。

## Known Optimizations

### 切分策略

#### Attention TP

> 源：对 Attention 的张量切分策略可以分为对 QKV 头的切分和对线性层的切分。在对 QKV 头切分时，attention 的多头计算机制可以方便进行张量切分，每个头先独立计算，再将结果 concat 起来。

要求 `num_heads % attn_tp_size == 0`，每卡头数
`num_heads_per_rank = num_heads // attn_tp_size`；GQA/MQA 场景 K/V 头更少，需保证每卡至少 1 个 K/V 头：
`num_key_value_heads_per_rank = max(num_key_value_heads // attn_tp_size, 1)`。`o_proj` 按行切分。

![Attention TP 头切分](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/attention_tp.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/attention_tp.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/attention_tp.png)（cann-recipes-infer @ 2f82d10）*

**计算分解**：将 Q/K/V 的线性层合并为一次 Matmul（`merged_qkv_proj`）→ 拆分 Q/K/V → Q、V 归一化 + RoPE → `Fused_infer_attention_score` → `o_proj`。

![Attention 计算分解](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/attention_calcu.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/attention_calcu.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/attention_calcu.png)（cann-recipes-infer @ 2f82d10）*

#### MoE TP

> 源：假设模型的 MoE 层的切分数量为 `moe_tp_size`，专家个数为 expert_num。对 MoE 层进行张量切分。具体做法是对 `gate_proj` 与 `up_proj` 进行列切分，对 `down_proj` 进行行切分。同时对 `gate_proj` 与 `up_proj` 线性层采用合并计算的优化方式，得到 `w13_weight`。

每个专家层 `x = down(SiLU(gate(x)) * up(x))`；将切分后 `gate_proj` 与 `up_proj` concat 后使能 [`torch_npu.npu_swiglu`](https://www.hiascend.com/document/detail/zh/Pytorch/730/apiref/torchnpuCustomsapi/docs/context/overview.md) 融合算子（沿最后一维 chunk 为两块，计算 `SiLU(x[0]) * x[1]`）。

![MoE 计算分解](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/moe_opt.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/moe_opt.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/moe_opt.png)（cann-recipes-infer @ 2f82d10）*

#### MoE EP + DoubleRouting

当 TP 切分下 routing / finalizing 开销占比不随 RANK 数下降时，改用 EP 切 S 轴，routing + finalizing 计算量变为 `1/ep_size`。MoE 走 DoubleRouting（[double-routing](../techniques/double_routing.md) 的 HunyuanImage-3.0 场景），具体 8 步：

1. GatingTopK 后使用 InitRouting 确定当前 RANK 的 token 分给哪些专家
2. all_to_all 发送 `tokens_per_expert` 至对应 RANK
3. all_to_all 发送 tokens 至对应 RANK
4. LocalRerouting：每个 RANK 内按专家序重排
5. GroupedMatMul：专家计算
6. LocalFinalizeRerouting：排序回第二次 all_to_all 后的排布
7. all_to_all 把计算完的 token 发送回原本 TP 域内对应 RANK
8. FinalizeRerouting：对专家计算结果在 TP 域内累加

![MoE Double Routing（HunyuanImage-3.0 场景）](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/moe_double_routing.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/moe_double_routing.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/moe_double_routing.png)（cann-recipes-infer @ 2f82d10）*

为降低通信量，配合此方案：**q_proj 前 AllGather hidden_states + o_proj 后 ReduceScatter attn_output**，这样可为通算融合创造机会：AllGather × qkv_proj、o_proj × ReduceScatter（见下文）。

### 并行优化

#### MoE 多流并行

MoE 模块中，路由专家采用 TP 部署；共享专家的计算与路由专家完成 MoE 计算后的通信可通过多流并行掩盖，使用 `all_reduce` 异步机制。

![MoE MLP 多流排布](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/figures/moe_mlp_parallel.png)
*来源：[`docs/models/hunyuan-image-3.0/figures/moe_mlp_parallel.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/figures/moe_mlp_parallel.png)（cann-recipes-infer @ 2f82d10）*

参见 [moe-multi-stream](../techniques/moe_multi_stream.md)。

#### VAE 并行（空间并行）

把大尺寸图像在 H、W 维度切成 patch 分配到多 NPU 进程并行处理。卷积边界交换 / 注意力全局 gather / 插值扩展-裁剪。详见 [vae-patch-parallel](../parallelism/vae_patch_parallel.md) 与 [vae](../modules/vae.md)。

#### CFG 并行

`cond` / `uncond` 两样本拆到两卡并行，all_gather 后合并。示例：TP2 + CFGP：

> 以 TP2+CFGP 为例，排布情况如下图所示。

详见 [cfg-parallel](../parallelism/cfg_parallel.md)。

### 使能融合算子

#### 通算融合（AllGatherMM / MMReduceScatter）

EP 方案中，`qkv_proj` 前对 `hidden_states` 做 AllGather、`o_proj` 后做 ReduceScatter。串行会造成性能浪费，使用通算融合算子：

- **AllGatherMM** — [`torch_npu.npu_all_gather_base_mm`](https://www.hiascend.com/document/detail/zh/Pytorch/730/apiref/torchnpuCustomsapi/docs/context/torch_npu-npu_all_gather_base_mm.md)：仅支持 2D 输入、第 0 轴切分。调用前 `hidden_states` layout 由 `[b s h]` 转为 `[(s b) h]`，调用后再转回。**s 轴必须在最内侧**，否则精度异常。
- **MMReduceScatter** — [`torch_npu.npu_mm_reduce_scatter_base`](https://www.hiascend.com/document/detail/zh/Pytorch/730/apiref/torchnpuCustomsapi/docs/context/torch_npu-npu_mm_reduce_scatter_base.md)：同样 2D 输入第 0 轴切分；`[b n s d]` → `[(s b) (n d)]` → 反转。**s 轴必须在最内侧**。该 MMReduceScatter 融合算子在 A2（Ascend910B）暂未使能：`o_proj` 后经 `torch.npu.get_device_name()` 检测到 `Ascend910B` 时走设备分支，回退普通 `dist.reduce_scatter`（matmul 与通信不融合）；非 A2 才用 `npu_mm_reduce_scatter_base` 融合。AllGatherMM 侧无此分支（A2 仍直接调用融合算子）。

#### GroupedMatMul + Routing 优化

对 MoE，CANN 提供 `GroupedMatmul` 算子同时计算多个专家，避免 for 循环单独计算。具体实现在 `HunyuanMoE` 类的 `npu_grouped_matmul` 模式：

- [`torch_npu.npu_moe_init_routing`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_init_routing.md) — MoE routing 计算，获取专家排序
- [`torch_npu.npu_moe_compute_expert_tokens`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_compute_expert_tokens.md) — 每个专家需要计算的 token 数
- [`torch_npu.npu_moe_finalize_routing`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_finalize_routing.md) — 专家计算完成后的 token 重新排布 + 加权求和
- [`torch_npu.npu_grouped_matmul`](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/torch_npu-npu_grouped_matmul.md) — 多个专家的矩阵乘

#### RmsNorm 算子优化

使能 [`torch_npu.npu_rms_norm`](https://www.hiascend.com/document/detail/zh/Pytorch/60RC2/apiref/apilist/ptaoplist_000140.html) 算子加速。

### 消除冗余计算

#### 消除旋转位置编码冗余 cast 算子

在 `HunyuanImage3ForCausalMM` 类中将 cos, sin 提前转成 bfloat16，消除 `apply_rotary_pos_emb` 中 cos/sin 从 float32 自动 cast 到 bfloat16 的冗余：

```python
cos = real_batched_index_select(cos, dim=1, idx=position_ids).to(torch.bfloat16)
sin = real_batched_index_select(sin, dim=1, idx=position_ids).to(torch.bfloat16)

if self.use_rotary_pos_emb:
 cos, sin = custom_pos_emb
 query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
```

#### 消除 gate 计算冗余 cast 算子

屏蔽外层 `torch.autocast` 以保持 gate 的 float32 精度：

```python
with torch.npu.amp.autocast(enabled=False):
 if self.wg.weight.dtype == torch.float32:
 hidden_states = hidden_states.float
 logits = self.wg(hidden_states)
```

#### 消除 FA 中 scale 的冗余计算

每次调用 FA 时默认在 CPU 计算 `scale=1/math.sqrt(d)`，导致下发中断。由于 `d` 在 config 里固定，将 `scale` 计算提前到 `HunyuanImage3Model.__init__` 存为成员变量，`flash_attn_func_npu` 复用。

#### 消除 timestep_index 的冗余计算

`gen_timestep_scatter_index[0, 0].item` 是强同步，造成 device 等待。将 `timestep_index` 的初始化提前至 `HunyuanImage3Text2ImagePipeline.__call__` 开头，并透传至 `casual_len` 的计算处，避免反复 Host2Device。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/hunyuan-image-3.0/{run_image_gen.py, model_adaptor.py, adaptor_patches/, utils/}`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-image-3.0/{run_image_gen.py, model_adaptor.py, adaptor_patches/, utils/})
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/vae_patch_parallel.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/vae_patch_parallel.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 统一推理拉起结构（@2c45117，@2f82d10 尚为 `demo.sh`）：[`models/hunyuan-image-3.0/infer.sh`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/infer.sh) + [`config/ep8_cfg.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/ep8_cfg.yaml)（`world_size: 16` / `moe-ep: true` / `entry_script: run_image_gen.py` / `CFG_PARALLEL=1` / `USE_VAE_PARALLEL=1`）+ [`config/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/README.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — MMReduceScatter A2 设备分支（@2c45117，commit 59a7906 MR!405）：[`adaptor_patches/hunyuan.py#L580-L607`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)（`torch.npu.get_device_name()` / `"Ascend910B"` 设备分支：A2 走 `dist.reduce_scatter`、非 A2 走 `npu_mm_reduce_scatter_base`）+ [`docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)（MMReduceScatter 句尾「(A2平台下暂未使能该融合算子)」）

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [cfg-parallel](../parallelism/cfg_parallel.md)
- [vae-patch-parallel](../parallelism/vae_patch_parallel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [hunyuan-video](hunyuan_video.md)

## Notes

- **gap**：源文档未给出 benchmark 数字、未列出 `attn_tp_size` / `moe_tp_size` / `ep_size` 推荐值
- **gap**：文档提到 `HunyuanMoE` 类与 `HunyuanImage3ForCausalMM` 类，但未解释 `HunyuanImage-3.0` 的文本 tower 细节（是否为独立 LLM）

<!-- cannbot:related:start -->
## 相关

- [CFG Parallel](../parallelism/cfg_parallel.md)（`related`）：Classifier-Free Guidance (CFG) 在 DiT 每个采样 step 内需要做两次前向：一次条件（cond，带 prompt）、一次无条件（uncond，空 prompt），再按 `noise_pred = noise_pred_uncond + w·(noise_pred_cond - noise_pred_uncond)` 融合。CFG Parallel 把这两个样本分别放到两张卡上同时跑，每卡只做一次模型推理，最后通过 all_gather 互相拿对方的结果，端到端相当于把 DiT 每步耗时减半。HunyuanImage-3.0、Wan2.2-I2V 均采用该并行。；`cond` / `uncond` 两样本拆到两卡并行，all_gather 后合并。示例：TP2 + CFGP：。并行概念说明两次前向的拆卡机制，模型卡确认 HunyuanImage-3.0 的 cond/uncond 拆分与合并。
<!-- cannbot:related:end -->
