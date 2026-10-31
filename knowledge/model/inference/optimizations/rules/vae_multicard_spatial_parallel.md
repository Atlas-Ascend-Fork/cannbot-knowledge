---
type: Optimization
title: 大分辨率 VAE encode/decode 多卡空间并行（按算子选通信 + 边界 halo/overlap 补偿）
description: 大分辨率 VAE encode/decode 多卡空间并行（按算子选通信 + 边界 halo/overlap 补偿）。图/视频生成 pipeline 里，VAE 在大分辨率（如 1280×720、720p 视频）encode/decode 时是空间大张量算子密集段，单卡慢/占显存，而 DiT 主干已在多卡序列并行。此时可把 VAE 沿空间维切到多卡并行，与 DiT 的序列并行互补。核心难点是 VAE 含卷积，感受野受限——朴素按空间切块会在块边界产生拼接缝/失真，必须补边界上下文。
tags:
- task.debugging
- topic.diffusion
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/218
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/49
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/266
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:32:47Z'
platforms:
- a2
---

# 大分辨率 VAE encode/decode 多卡空间并行（按算子选通信 + 边界 halo/overlap 补偿）

## 适用场景

图/视频生成 pipeline 里，[VAE](../../concepts/modules/vae.md) 在大分辨率（如 1280×720、720p 视频）encode/decode 时是**空间大张量算子密集段**，单卡慢/占显存，而 DiT 主干已在多卡序列并行。此时可把 VAE 沿空间维切到多卡并行，与 DiT 的序列并行互补。核心难点是 **VAE 含卷积，感受野受限——朴素按空间切块会在块边界产生拼接缝/失真**，必须补边界上下文。

## 做什么

把输入沿空间维切成块分到各卡，各卡只算本块，**按算子类型选通信原语补边界**，末端 all_gather 按原空间位置重拼。canonical 机制见 [vae-patch-parallel](../../concepts/parallelism/vae_patch_parallel.md)。两条参考实现落地了两种切法：

### 二维 patch 并行（H×W 切、按算子谱选通信）

- **进程网格**：沿高(H)、宽(W)切成 `h_split × w_split == world_size` 块（断言必须相等），`row_rank = rank // w_split`、`col_rank = rank % w_split`，建行/列通信组。
- **算子级通信策略**（monkeypatch `F.conv2d/conv3d/interpolate/scaled_dot_product_attention`，对 VAE 前向零改动）：
  1. **stride=1 的卷积路径**：先按邻居交换边界行/列（`exchange_rows/exchange_columns` 用 `dist.P2POp(isend/irecv)` + `batch_isend_irecv` 的异步 P2P halo）拿 halo 上下文，块边缘无邻居处补零 pad，再本地卷积。
     stride≠1 的二维下采样卷积是另一分支：先 dispatch 重组完整空间输入，再按输出通道切权重计算，随后 all_to_all 重分块，不能套用 P2P halo。
  2. **注意力**：`all_gather` 收全局 K/V，保跨块注意力完整。
  3. **插值/上采样**：扩展边界 → 插值 → 裁剪回本块，避免边界插值失真。
- **收集复原**：两阶段 `all_gather`（先 all_gather 各块 shape，再 all_gather 展平数据），按 `rank→(row,col)` 映射重拼成完整输出。

### 一维宽度切 + overlap 补偿（decode）

VAE decode 沿 latent 宽度维在各 rank 间切分：因卷积感受野，非首片向左借 `overlap_size`、各片向右借到边界，各 rank `_decode` 后**按空间上采样率 `up_rate` 放大再去掉 pad**，`all_gather` 拼回。`overlap_size` 由 tile 参数（`tile_latent_min_size`/`tile_overlap_factor`）推导。

## 何时不适用 / 边界

- 二维切法 `h_split × w_split` 必须等于 world_size；一维切法只切最后一维（宽），依赖分布式已 init（`dist.is_initialized()` 为假时抛 RuntimeError；不是按 world_size==1 拒绝）。
- **不同算子走不同通信原语**（stride=1 conv 的 P2P halo / stride≠1 下采样的 dispatch+all_to_all / attn 的 all_gather K/V / interp 扩边裁剪），不能一刀切用同一原语；换 VAE 结构（新增/替换算子类型）须为新算子相应补配通信，否则跨块结果错。
- overlap 补偿依赖 `up_rate` 与 tile 参数的假设，规格不符可能仍有边缘误差。
- rollback：不传并行开关（`--vae_parallel` / `--use-vae-parallel`），走原生 `self.vae.decode`。

## 参考实现

- HunyuanImage-3.0：共享模块 `module/vae_patch_parallel.py`（`Parallel_VAE_SP` 类），`set_vae_patch_parallel(...)` 接入、`VAE_patch_parallel` 上下文管理器 monkeypatch 相关算子，退出还原。二维 H×W 切。
- [Wan2.2-I2V](../../concepts/models/wan2_2_i2v.md)（Atlas A2）：`Parallel_VAE_SP` 同结构，以 `--vae_parallel` 暴露，实现移植自 MindIE/Wan2.2。
- [HunyuanVideo](../../concepts/models/hunyuan_video.md)：`hyvideo/vae/vae_parallel.py` 的 `decode`（一维宽度切 + overlap），`--use-vae-parallel` 开关，多卡脚本在 `--ulysses-degree=8` 基础上追加。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/218)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/49)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/266)（evidence）
