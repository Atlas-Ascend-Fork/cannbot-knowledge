---
type: Concept
title: VGGT 昇腾 Atlas A2 推理适配与优化
description: VGGT（Visual Geometry Grounded Transformer，CVPR 2025）是一个前馈式 3D 视觉基础模型：给定一组无序图像，单次前向即可联合预测相机位姿、点云、深度图等几何属性。本页记录 cann-recipes-spatial-intelligence 在 Atlas A2（Atlas 800I A2 推理产品）上对 VGGT 的推理适配、性能优化与三任务精度评测。模型本体来自上游开源仓 facebookresearch/vggt（外部未克隆未核验，本页只引本仓内重写/覆盖的优化文件）。 补充：三任务精度评测指标语义（AUC@30=位姿误差≤30°累积准确率、Acc=预测→真值点云最近邻均距、Comp=真值→预测最近邻均距、Overall=(Acc+Comp)/2）。
tags:
- task.design
- topic.three_dimensional_reconstruction
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/vggt/vggt_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# VGGT 昇腾 Atlas A2 推理适配与优化

VGGT（Visual Geometry Grounded Transformer，CVPR 2025）是一个前馈式 3D 视觉基础模型：给定一组无序图像，单次前向即可联合预测**相机位姿、点云、深度图**等几何属性。cann-recipes-spatial-intelligence 在 **Atlas A2**（Atlas 800I A2 推理产品）上对 VGGT 做推理适配、性能优化与三任务精度评测。模型本体来自上游开源仓 [facebookresearch/vggt](https://github.com/facebookresearch/vggt)，优化围绕本仓内重写/覆盖的优化文件展开。

> 优化成果：在 `examples/kitchen` 25 张图片输入下，整网推理耗时降至 **1.12 秒**（8 卡 Ulysses=8 序列并行下另有 ~6.47x 提升）。

## 模型结构

VGGT 由 **Aggregator + 多任务头** 组成：

- **Aggregator**（[`vggt/models/aggregator.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/models/aggregator.py)）：交替堆叠 **Frame Attention（帧内）** 与 **Global Attention（跨帧）**，即代码中的 `aa_order=["frame", "global"]`，对应 `frame_blocks` / `global_blocks` 两组 Block，分别走 `_process_frame_attention` / `_process_global_attention`。Frame 处理单帧内的短序列、Global 在所有帧 token 上做长序列注意力 —— 这一双层架构是后续 FIA 算子分流优化的依据。
- **任务头**：相机位姿头（[`heads/camera_head.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/heads/camera_head.py)）、DPT 深度/点云头（[`heads/dpt_head.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/heads/dpt_head.py)）、track 头（[`heads/track_head.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/heads/track_head.py)）。

依赖：CANN 8.5.0、torch 2.7.1 / torch_npu 2.7.1.post2、Python 3.11。单卡 `python demo_infer.py --ckpt ckpt/model.pt`；多卡 `infer_test.sh`（torchrun + 序列并行）。

## 性能优化

各优化点的逐项累计耗时（8 卡 Atlas 800I A2，25 张图片，源自 [vggt_optimization.md](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/vggt/vggt_optimization.md)）：

| 累计使能 | 推理耗时 (ms) |
|:---|:---:|
| Cos/Sin 算子优化 | 1324.83 |
| + 旋转编码优化 | 1239.55 |
| + DPT 头计算优化 | 1211.26 |
| + npu_add_layer_norm 融合 | 1208.17 |
| + 权重转 BF16 | 1128.18 |
| + 卷积核私有格式提前转换 | 1121.09 |

### Cos/Sin 算子输入优化
原网络 `make_sincos_pos_embed` 中 `omega` 用 `torch.double`，导致 Cos/Sin 算子下发到 AI CPU 执行、性能差。优化将 `omega` 数据类型改为 `torch.bfloat16`，使算子留在 AI Core。见 [`heads/utils.py:make_sincos_pos_embed`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/heads/utils.py)（`omega = torch.arange(embed_dim // 2, dtype=torch.bfloat16, ...)`）。

### 旋转编码（RoPE）优化
见 [`vggt/layers/rope.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/layers/rope.py)，两处优化：
1. **融合算子 `npu_rotary_mul`**：原实现用 `(tokens * cos) + (rotate(tokens) * sin)` 多个小算子，Host 下发多。替换为 `torch_npu.npu_rotary_mul(tokens, cos, sin, rotary_mode='half')`，减少下发。
2. **冗余计算消除**：每次 attention 都重算 cos/sin 是冗余的。优化在 `RotaryPositionEmbedding2D` 建立**两级缓存**：`frequency_cache`（以 `(dim, seq_len, device, dtype)` 为 key 缓存基频 cos/sin 分量）与 `cos_sin_cache`（以 `(height, width, batch_size, seq_len)` 为 key 缓存 vertical/horizontal 的 cos/sin），相同尺寸图片复用、避免每次 attention 重算。

### DPT 头位置编码计算优化
DPT 头每次前向都重算位置编码（`create_uv_grid` → `position_grid_to_embed`），而结果只取决于输入图片尺寸和 token 长度。优化在 [`heads/dpt_head.py:_apply_pos_embed`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/heads/dpt_head.py) 中以 `(W, H, x.shape)` 为 key 建 `pos_embed_cache` 缓存位置编码结果，避免冗余计算。

### Add + LayerNorm 融合算子
将「残差加 + LayerNorm」小算子替换为融合大算子。重写 `nn.LayerNorm.forward`：无 residual 时用 `torch_npu.npu_layer_norm_eval`；有 residual 时用 `torch_npu.npu_add_layer_norm(..., additional_output=True)`，一次返回归一化输出与新 residual。

### npu_fused_infer_attention_score（FIA）适配
NPU FIA 是 torch_npu 提供的、适配增量/全量推理的 FlashAttention 融合算子，相比 SDPA 在昇腾上推理性能更好。VGGT 按 **Frame-Global 双层架构分流**：
- **Frame Attention**（帧内短序列）：保持 PyTorch `F.scaled_dot_product_attention`。
- **Global Attention**（跨帧长序列）：切换到 `torch_npu.npu_fused_infer_attention_score`，`input_layout="BNSD"`、`pre_tokens=next_tokens=65535`、`inner_precise=0`。

代码见 [`vggt/layers/attention.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/layers/attention.py)：`Attention` 模块以 `is_global_attention` 标志区分，`_compute_attention_with_fia` 内对 global 路径调用 FIA；仅在训练态 `dropout_p>0` 时回落 SDPA（FIA 不支持 dropout），GQA 经 `num_key_value_heads` 入参由 FIA 直接处理。跨域共享算子见 cann-infer 的 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。

### 二维卷积核私有格式（NZ / Fractal_Z）提前转换
NPU 上做二维卷积需先用 Transdata 把卷积核转为 `Fractal_Z` 格式，推理时引入转换开销。优化在加载权重后、推理前用 [`vggt/utils/cast_weight.py:cast_model_weight`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/utils/cast_weight.py) 递归遍历模块，对 `torch.nn.Conv2d`（`groups==1`）权重调 `torch_npu.npu_format_cast(weight, 4)` 提前转格式，消除运行期转换。此「权重私有格式预转换」思路与 cann-infer 的 [weight-nz](../../../inference/concepts/techniques/weight_nz.md) 同源（infer 域针对 Linear 权重的 NZ/FRACTAL_NZ）。

## 精度（BF16 / INT8 权重）

- **BF16 权重**：加载后将网络权重转 bfloat16，取得 **6.62%** 性能收益；相机位姿任务精度（AUC@30）从 fp32 的 0.919 降至 0.911，损失 <0.5%。
- **INT8 权重（W8A8）**：当前仅对 VGGT 中 **K=4096 的 Linear 层**做 8bit 量化 —— 权重静态 per-channel、激活在线动态 per-token。模型大小 fp32 4.9GB → bf16 2.46GB → int8 2.16GB。相机位姿精度相比 bf16 从 0.911 降至 0.907，损失 <0.5%。默认关闭，`--buildW8A8` 离线建量化模型、`--enableW8A8` 使能推理。实现见 [`quant/vggt_linear.py:LinearW8A8`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/quant/vggt_linear.py)：权重侧 `torch_npu.npu_dynamic_quant`，前向 `npu_dynamic_quant`（激活 per-token）+ `npu_quant_matmul`。量化方案与 cann-infer 的 [w8a8c8](../../../inference/concepts/quantization/w8a8c8.md)（W8A8 per-channel 权重 + per-token 激活）同族。

## 序列并行推理（Ulysses + Ring）

VGGT 原生仅单卡。本仓为 **Global Attention** 引入序列并行（`--enable_sp`，约束 `ulysses_degree × ring_degree = nproc_per_node`，且 `num_attention_heads` 须被 `ulysses_degree` 整除），实现见 [`vggt/sp/unified_sp_attention.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/models/vggt/vggt/sp/unified_sp_attention.py)：

- **Ulysses（头维度切分）**：通过 all-to-all 把 `[B, shard_s, H, D]` 与 `[B, S, shard_hc, D]` 互换 —— 每 rank 持有完整序列、部分 attention 头。跨域同概念见 [ulysses](../../../inference/concepts/parallelism/ulysses.md)。
- **Ring（序列维度切分）**：`use_ring_overlap` 边通信边计算 —— 异步 allgather K/V 的同时算 local attention，等通信完成再算 cross attention，最后**用 NPU FIA 返回的 LSE（log-sum-exp）做分块结果数值稳定合并**。跨域同概念见 [ring-attention](../../../inference/concepts/parallelism/ring_attention.md)。

整网精度（AUC@30）随并行度基本稳定；性能提升如下：

| 并行度 | 推理提升 | AUC@30 |
|:---:|:---:|:---:|
| 单卡 | 1.0x | 91.10 |
| Ulysses=2 / 4 / 8 | 1.75x / 3.43x / 6.47x | 91.12 / 91.10 / 90.86 |
| Ring=2 / 4 / 8 | 1.82x / 3.48x / 6.42x | 91.12 / 91.09 / 90.88 |

## 三任务精度评测

评测脚本与基线见 [vggt_accurancy_evaluation.md](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/vggt/vggt_accurancy_evaluation.md)。论文未开源全部评测脚本，本仓评测基于论文描述 + 社区代码复现。

**指标语义**（读懂下表数字的前提）：
- **AUC@30**（相机位姿，越大越好）：相机位姿误差 $\leq$ 30° 的累积准确率，即 0~30° 误差范围内模型正确估计相机位姿的累积准确率（源定义为「累积准确率」；AUC 字面为 Area Under Curve，此处不额外引申）。
- **Acc（Accuracy）**（点云重建/深度估计，越小越好）：预测点云中所有点到真值点云上最近邻的平均距离。
- **Comp（Completeness）**（越小越好）：真值点云中所有点到预测点云上最近邻的平均距离。
- **Overall（Average Overall）**：`(Acc + Comp) / 2`，三项数值越低重建精度越高。
- 深度估计任务先把多视角深度图融合成重建点云，再比较与真值点云的距离，故**复用上述 Acc/Comp/Overall 三指标**。

- **相机位姿估计**（Co3D，AUC@30，越大越好）：论文 88.2 / GPU 90.5 / **NPU 91.1**。脚本 `eval/pose_evaluation/eval_co3d.py`。
- **点云三维重建**（ETH3D，Acc/Comp/Overall，越小越好）：NPU 0.491 / 0.422 / 0.456，与 GPU（0.498 / 0.429 / 0.464）基本一致。脚本 `eval/point_map_estimation/eval_eth3d.py`。
- **深度估计**（DTU，Acc/Comp/Overall）：NPU 1.4669 / 0.5475 / 1.0072，与 GPU 接近。流程：`eval_dtu.py` 生成深度图 → `align_depth.py` 数值分布对齐 → `_open3d_fusion.py` 多视角融合点云 → `measure.py` 算点云距离。
  - **`unverified` / gap**：深度估计与论文（0.389/0.374/0.382）存在明显差异，本仓在 [vggt_accurancy_evaluation.md](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/vggt/vggt_accurancy_evaluation.md) 标注为**已知问题**（评测脚本基于社区复现、与论文实验设置有细微区别），非昇腾适配引入。

## Evidence

- 指标语义（AUC@30 / Acc / Comp / Overall 定义）出处：[vggt_accurancy_evaluation.md#精度测量结果](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/vggt/vggt_accurancy_evaluation.md)（「相机位姿估计 / 点云三维重建 / 深度估计」三小节的指标说明段）。

## Links

- 源仓：[cann-recipes-spatial-intelligence](https://gitcode.com/cann/cann-recipes-spatial-intelligence/tree/92747ee512faebff6068704f893d19d622f7282a)
- 平台：[atlas-a2](../platforms/atlas_a2.md)
- cann-infer 跨域共享概念：[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)、[weight-nz](../../../inference/concepts/techniques/weight_nz.md)、[w8a8c8](../../../inference/concepts/quantization/w8a8c8.md)、[ulysses](../../../inference/concepts/parallelism/ulysses.md)、[ring-attention](../../../inference/concepts/parallelism/ring_attention.md)

<!-- cannbot:related:start -->
## 相关

- [Ring Attention Sequence Parallelism](../../../inference/concepts/parallelism/ring_attention.md)（`related`）：“**Ring（序列维度切分）**：`use_ring_overlap` 边通信边计算 —— 异步 allgather K/V 的同时算 local attention，等通信完成再算 cross attention，最后**用 NPU FIA 返回的 LSE（log-sum-exp）做分块结果数值稳定合并**。”；“概念上（见下方 HunyuanVideo 文档引用）以 P2P 环形逐跳传递 KV；但本仓 `module/unified_sp/core.py` 的实际实现是用一次 `all_gather_into_tensor` 把其他所有 rank 的 1/SP KV 一次性收齐，再对「本地 FA」与「其他 rank 合并 FA」共 2 路输出做 LSE（Log-Sum-Exp）合并（非逐跳 P2P、非 SP-1 串行轮）。”。目标卡补齐焦点 overlap 路径的通信与 LSE 合并机制。
- [Ulysses Sequence Parallelism](../../../inference/concepts/parallelism/ulysses.md)（`related`）：“**Ulysses（头维度切分）**：通过 all-to-all 把 `［B, shard_s, H, D］` 与 `［B, S, shard_hc, D］` 互换 —— 每 rank 持有完整序列、部分 attention 头。”；“Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。”。两端给出 VGGT 实例与通用 Ulysses 数据重排合同。
- [npu_fused_infer_attention_score (v1 / v2)](../../../inference/concepts/kernels/fused_infer_attention_score.md)（`related`）：“**Global Attention**（跨帧长序列）：切换到 `torch_npu.npu_fused_infer_attention_score`，`input_layout="BNSD"`、`pre_tokens=next_tokens=65535`、`inner_precise=0`。”；“昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算：`softmax(QKᵀ/√d)·V`，支持 Paged KVCache、Block-Table、分离的 NoPE/RoPE Query/Key 输入、以及 Query / Key / Value 三端的动态 Int8 反量化（dequant_scale_*）。”。FIA 卡补齐 VGGT Global Attention 的算子语义与参数边界。
<!-- cannbot:related:end -->
