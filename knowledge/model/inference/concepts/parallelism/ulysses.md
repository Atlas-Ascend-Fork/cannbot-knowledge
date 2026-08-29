---
type: Concept
title: Ulysses Sequence Parallelism
description: Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。相比于 Ring Attention 依赖 P2P 循环传 KV，Ulysses 用集合通信 all-to-all 实现，简单高效，是 HunyuanVideo / HunyuanImage-3.0 / Wan2.2-I2V 长序列 DiT 推理的首选序列并行。 cann-recipes-infer 在 `module/unified_sp/` 提供统一 SP 框架，支持 Ulysses / Ring / Hybrid（Ulysses × Ring）三种模式，并通过 **Ulysses Anything Attention (UAA)** 支持任意头数的灵活配置。
tags:
- task.design
- topic.parallelism
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
- agnostic
---

# Ulysses Sequence Parallelism

## Summary

Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。相比于 Ring Attention 依赖 P2P 循环传 KV，Ulysses 用集合通信 all-to-all 实现，简单高效，是 HunyuanVideo / HunyuanImage-3.0 / Wan2.2-I2V 长序列 DiT 推理的首选序列并行。

cann-recipes-infer 在 `module/unified_sp/` 提供统一 SP 框架，支持 Ulysses / Ring / Hybrid（Ulysses × Ring）三种模式，并通过 **Ulysses Anything Attention (UAA)** 支持任意头数的灵活配置。

## Mechanism

![Ulysses 序列并行](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/figures/ulysses.png)
*来源：[`docs/models/hunyuan-video/figures/ulysses.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/figures/ulysses.png)（cann-recipes-infer @ 2f82d10）*

> 源（HunyuanVideo 优化文档）：假设 input 的 shape 为 B，S，N，D，分别代表（batch size，sequence，number of head，dimension），序列并行即将 input 沿着 S 维度进行切分，在多卡上实现更低的动态显存占用，和更高的 DiT 性能。
>
> 首先将 input 沿着 S 维度切分为 S/SP，其中 SP 为序列并行数量，输入模型，直到 attn 操作。考虑到多头自注意力计算时各个头是并行计算的，在 attention 以外的地方切分 latent 的序列长度，在 attn 操作时，需要一次 AllToAll 通讯，交换每张卡存储的数据，等价为将 input 的 shape 从（B，S/SP，N，D）reshape 为（B，S，N/SP，D）。即从切分序列长度改为切分 head num。在 attn 结束后，由于每张卡实际仅计算 1/SP 的 head 的结果，所以需要再一次 AllToAll 通讯获得完整的 attn 结果。

```mermaid
flowchart LR
 In["Input [B, S, N, D]"] --> Split["Sequence split<br/>[B, S/SP, N, D]"]
 Split --> Pre[pre-attention modules]
 Pre --> A2A1[AllToAll #1<br/>S/SP×N → S×N/SP]
 A2A1 --> Attn["FA per head shard<br/>[B, S, N/SP, D]"]
 Attn --> A2A2[AllToAll #2<br/>S×N/SP → S/SP×N]
 A2A2 --> Post[post-attention modules]
```

### Ulysses Anything Attention (UAA)

标准 Ulysses 要求 `num_heads % ulysses_degree == 0` 且视频尺寸满足 `H % 16 % ulysses_degree == 0` 或 `W % 16 % ulysses_degree == 0`，限制实际配置灵活性。UAA（`module/unified_sp/uaa.py`）通过动态 padding + per-rank 序列长度协商解除约束。

核心填充逻辑：

```python
# 来源：module/unified_sp/uaa.py _maybe_pad_qkv_head
def _maybe_pad_qkv_head(x: torch.Tensor, h: int, world_size: int) -> Tuple[torch.Tensor, int]:
 """Maybe pad the head dimension to be divisible by world_size."""
 h_pad = 0
 if h % world_size != 0:
 h_pad = world_size - (h % world_size)
 new_h_local = (h + h_pad) // world_size
 # 约束：填充头数必须小于每卡本地头数
 if h_pad >= new_h_local:
 raise ValueError(
 f"Padding head num {h_pad} should be less than new local head num {new_h_local}"
 )
 x = F.pad(x, (0, 0, 0, h_pad)).contiguous()
 return x, h_pad
```

仅最后一 rank 需要填充；填充头数必须小于每卡本地头数，否则退化为负优化。

动态序列长度分配（视频尺寸约束解除）：

```python
# 收集各 rank 的序列长度
output_split_sizes = _gather_size_by_comm(s_local, self.ulysses_pg)
# 使用实际的序列长度分配进行 all-to-all
x = fc.all_to_all_single(x, output_split_sizes, input_split_sizes, self.ulysses_pg)
```

示例：

| 配置 | 头数 | 并行度 | 填充数 | 每卡头数 |
|------|------|--------|--------|----------| | 标准 Ulysses | 24 | 8 | 0 | 3 |
| Ulysses Anything | 30 | 8 | 2 | 4 |
| Ulysses Anything | 40 | 8 | 0 | 5 |

## Applicable Scenarios

- 长序列 DiT 推理（HunyuanVideo 119k、HunyuanImage-3.0、Wan2.2-I2V）
- 需要跨卡均摊 sequence 方向动态显存的场景
- 可与 Ring Attention 组合（hybrid SP，2D mesh）
- 与 FP8 量化注意力配合：**FP8 量化 attention 当前仅支持 Ulysses SP，不支持 Ring**
- 与 [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md) 配合：块稀疏仅与单卡/Ulysses 协同（不支持 Ring）。块稀疏 × Ulysses 负载均衡为本页钉定版 @2f82d10 之后由提交 `dcabc6a`（"HunyuanVideo support Ulysses parallelism with block-wise sparse attention"）引入的 master 演进，@2f82d10 的 `module/blockwise_sparse/` 尚不含相关符号：`ulysses_degree > 1` 时对**实现该方法的 TopK 路径**（在 `sample_video.py` 经 `getattr(args, "ulysses_degree", 1) > 1 and hasattr(..., "apply_head_reorder_for_load_balance")` 守卫，SVG 路径因无该方法而跳过）调 `apply_head_reorder_for_load_balance` 重排 head 以均衡各 rank 的稀疏计算量，`parallel_sparse_attention` 为 SP 下执行入口（落点为 `module/blockwise_sparse/sparse_method.py` 与 `models/hunyuan-video/hyvideo/modules/attention.py`，非 `unified_sp/core.py`）

## Configuration

- HunyuanVideo：`ulysses5` / `ulysses8`，关键参数 `ulysses_degree`
- 头数能整除并行度 → 开启标准 Ulysses；头数不整除或视频尺寸不对齐 → 开启 `ulysses_anything=True`

```python
# 开启 UAA
attn = UnifiedSPAttention(
 ulysses_group=ulysses_group,
 ring_group=None,
 ulysses_anything=True,
)
```

## Constraints

- 依赖 all-to-all 全量通信带宽，SP 规模扩大通信开销呈超线性
- `num_heads` 需可整除 SP（标准模式）；UAA 的填充头数需 < 每卡本地头数
- attention 必须以 head 为独立计算单元（DiT / LLM 都满足）
- 视频尺寸 / 序列长度在标准 Ulysses 下需 16 对齐，UAA 解除此限制

## Known Deployments

- **HunyuanVideo**：`ulysses5`（搭配 VAE 并行 + 融合算子 + 虚拟内存 + UAA（性能表 UAA 列为 √）→ 4.65× 端到端）；`ulysses8`（最佳 7.73×–7.81×，叠加 UAA 仍有 7.81×）
- **HunyuanImage-3.0**：文档未明确给出 SP 规模，但序列并行基础建在同一套 `module/unified_sp/` 上
- **Wan2.2-I2V**：Ring Attention Overlap 形式使用，见 [ring-attention-overlap](../techniques/ring_attention_overlap.md)

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md) 序列并行 / Ulysses Anything Attention
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/unified_sp/core.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/unified_sp/core.py) `module/unified_sp/uaa.py`
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 块稀疏 × Ulysses 负载均衡（@2f82d10 之后引入）：[`module/blockwise_sparse/sparse_method.py`](https://gitcode.com/cann/cann-recipes-infer/blob/dcabc6a21962ab5cf21bfd51099c08c7c21de88e/module/blockwise_sparse/sparse_method.py) `apply_head_reorder_for_load_balance` / [`models/hunyuan-video/hyvideo/modules/attention.py`](https://gitcode.com/cann/cann-recipes-infer/blob/dcabc6a21962ab5cf21bfd51099c08c7c21de88e/models/hunyuan-video/hyvideo/modules/attention.py) `parallel_sparse_attention` / [`models/hunyuan-video/sample_video.py`](https://gitcode.com/cann/cann-recipes-infer/blob/dcabc6a21962ab5cf21bfd51099c08c7c21de88e/models/hunyuan-video/sample_video.py) `ulysses_degree > 1` + `hasattr` 守卫（提交 `dcabc6a`）

## Links

- [ring-attention](ring_attention.md)
- [cfg-parallel](cfg_parallel.md)
- [dit](../modules/dit.md)
- [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [hunyuan-image-3](../models/hunyuan_image_3.md)
- [wan2.2-i2v](../models/wan2_2_i2v.md)
- [vggt](../../../spatial/concepts/models/vggt.md)（跨域·空间智能：VGGT 长序列推理用 Ulysses 序列并行）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)（Cosmos 长序列 Ulysses 序列并行）
- [context-parallel-train](../../../training/concepts/parallelism/context_parallel_train.md)（跨域·训练：MindSpeed Ulysses CP，head 维 All2All，含 USP Hybrid 与变长非对齐变体）

<!-- cannbot:related:start -->
## 相关

- [FP8 Per-Block Dynamic Quant Attention](../quantization/fp8_attention.md)（`related`）：- **仅支持 Ulysses 序列并行，不支持 Ring Attention**（HunyuanVideo 源文档明示）；- 与 FP8 量化注意力配合：**FP8 量化 attention 当前仅支持 Ulysses SP，不支持 Ring**。两端给出同一部署硬边界，Ulysses 卡还提供 AllToAll 与 head 切分机制供并行接入。
- [HunyuanVideo](../models/hunyuan_video.md)（`related`）：“Ulysses 序列并行 ｜ 提高算力 ｜ 将超长序列高效地切分到多个 NPU 上并行处理，每张卡负责处理自己负责的序列长度”；“Ulysses 是面向**长序列多头注意力**的序列并行策略”。模型明确采用 Ulysses，候选卡给出 all-to-all 布局转换和整除边界。
- [Ring Attention Overlap](../techniques/ring_attention_overlap.md)（`related`）：Overlap 卡硬约束“FP8（perblock）量化 attention 仅支持 Ulysses 序列并行”；Ulysses 卡同样规定“**FP8 量化 attention 当前仅支持 Ulysses SP，不支持 Ring**”。当需要 FP8 attention 时，该关系提供从 Ring Overlap 切换 Ulysses 的选型边界。
- [Ulysses 按 head 切分的整除约束（序列可软填充、head 需 UAA 放开）](../../runbooks/runtime/ulysses_head_seq_divisibility_uaa.md)（`related`）：Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。；标准 Ulysses 用 head-to-seq 的 all-to-all，**同时**把序列维和 head 维在各 rank 间等分，故两维都要求能被 `ulysses_world_size` 整除。序列长不整除→无法均分；head 数不整除→all-to-all 头切分不成立。单卡走 all-to-all no-op 分支，无此约束。。概念卡说明 S 与 head 之间的 all-to-all 切分转换，运行手册由同一转换推导序列和 head 的整除故障及 UAA 修法，形成机制到部署排障的直接链路。
- [VGGT 昇腾 Atlas A2 推理适配与优化](../../../spatial/concepts/models/vggt.md)（`related`）：“**Ulysses（头维度切分）**：通过 all-to-all 把 `［B, shard_s, H, D］` 与 `［B, S, shard_hc, D］` 互换 —— 每 rank 持有完整序列、部分 attention 头。”；“Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。”。两端给出 VGGT 实例与通用 Ulysses 数据重排合同。
- [混合序列并行 (Ulysses + Ring) 下 joint / 文本 token 的 attention 精度](../../runbooks/precision/precision_hybrid_sp_joint_token_attention.md)（`related`）：焦点卡的故障链是“若在 Ulysses all_to_all（head→seq）与 Ring gather **之前**就把 joint K/V 拼进普通序列 K/V，joint token 会被后续 all_to_all 与 ring gather 当**普通序列 token 重分布**——joint attention 结果被破坏。”；Ulysses 卡给出“Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。”，可据此定位 joint K/V 应在换维之后按 head 对齐。
- [视频 DiT（I2V）单卡推理 OOM：降到标称之下的分辨率，或大规格转多卡序列并行](../../runbooks/performance/video_dit_single_card_oom_resolution.md)（`related`）：**大规格转多卡序列并行**：更大的 1280×720 不在单卡跑，改走多卡 ［ulysses］(../../concepts/parallelism/ulysses.md) 序列并行（如 ulysses degree 4）。；Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。runbook 给出 OOM 时的多卡分支，概念卡解释该分支如何沿序列均摊显存。
- [长序列视频 DiT 接 Ulysses 序列并行（pad_freqs 补齐 + world_size 拓扑校验两处易错）](../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)（`related`）：焦点卡写明“沿序列维 `dim=1` 用 `torch.chunk(x, sp_world_size, dim=1)［sp_rank］` 切片”，候选卡写明“一次 AllToAll 通讯，交换每张卡存储的数据”。规则卡给出 Wan2.2 的序列切片与复原实现，概念卡解释 Attention 处 S→head 的 AllToAll 机制，衔接实现与原理。
<!-- cannbot:related:end -->
