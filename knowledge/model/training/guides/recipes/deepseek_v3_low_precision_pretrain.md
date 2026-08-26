---
type: Guide
title: DeepSeek-V3 裁剪模型 MXFP8/HiF8 低精度预训练（MindSpeed · Atlas A5 950DT · 8K）
description: cann-recipes-train 在 Atlas A5 950DT 上跑通的 8-bit 混合精度预训练：基于 mindspeed 框架（MindSpeed Core + MindSpeed-LLM 组件，底座对接 NVIDIA Megatron-LM core_v0.12.1），用一个 DeepSeek-V3 裁剪模型（2 层：1 dense + 1 MoE，hidden 7168、256 专家、MLA），在 8 卡 A5（950DT，单卡 486 TFLOPS）、序列长 8K、GBS=64 下，分别用 HiF8 与 MXFP8（E4M3） 两种低精度格式量化整网的 MatMul（MM）/ Grouped MatMul（GMM） 算子，与 BF16 混合精度做长稳精度对齐与性能对比。HiF8/MXFP8 损失与梯度范数都基本对齐 BF16，HiF8 端到端提速 29.5%、MXFP8 提速 14.05%、HiF8 相对 MXFP8 再快 11.3%。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- '950'
- a5
---

# DeepSeek-V3 裁剪模型 MXFP8/HiF8 低精度预训练（MindSpeed · Atlas A5 950DT · 8K）

## Summary

cann-recipes-train 在 **Atlas A5 950DT** 上跑通的 **8-bit 混合精度预训练**：基于 [mindspeed](../../concepts/frameworks/mindspeed.md) 框架（MindSpeed Core + **MindSpeed-LLM** 组件，底座对接 NVIDIA **Megatron-LM core_v0.12.1**），用一个 DeepSeek-V3 **裁剪模型**（2 层：1 dense + 1 MoE，hidden 7168、256 专家、MLA），在 **8 卡 A5（950DT，单卡 486 TFLOPS）**、序列长 8K、GBS=64 下，分别用 **HiF8** 与 **MXFP8（E4M3）** 两种低精度格式量化整网的 **MatMul（MM）/ Grouped MatMul（GMM）** 算子，与 BF16 混合精度做长稳精度对齐与性能对比。HiF8/MXFP8 损失与梯度范数都基本对齐 BF16，HiF8 端到端提速 **29.5%**、MXFP8 提速 **14.05%**、HiF8 相对 MXFP8 再快 **11.3%**。

低精度格式本身（HiF8 编码模式、Denormal、Per-tensor vs Per-block、Current/Delayed Scaling 等量化原理）的完整推导见 [hif8](../../concepts/quantization/hif8.md)，落到**真实拉起脚本与 recipe 配置**上即下文。它与 [deepseek-v32-pretrain](deepseek_v32_pretrain.md)（TorchTitan 671B 全量 / DSA 路线）并列——MindSpeed + 裁剪模型 + 低精度是另一条预训练路线。

## 训练配置（模型 × 阶段 × 框架 × 并行 × 精度 × 平台）

| 维度 | 取值 | 来源 |
|------|------|------|
| 模型 | DeepSeek-V3 **裁剪**（`NUM_LAYERS=2`：`--first-k-dense-replace 1` ⇒ 1 dense + 1 MoE） | run_pretrain 脚本 |
| 阶段 | 预训练（pretrain，enwiki 语料，`--train-iters 1000`） | run_pretrain 脚本 |
| 框架 | MindSpeed + MindSpeed-LLM（`--transformer-impl transformer_engine`），Megatron-LM core_v0.12.1 | README |
| 并行 | TP1 · PP1 · **EP8** · CP1（`ulysses_cp_algo`）· `--expert-tensor-parallel-size 1` · `--sequence-parallel` | run_pretrain 脚本 |
| 精度 | BF16 AMP 主路（`--bf16`），MM/GMM 走 HiF8 或 MXFP8 低精度路径 | 文档第五章 |
| 平台 | Atlas A5 **950DT**，单卡 486 TFLOPS | README / 文档 5.1 |
| 卡数 | 8 卡（`NPUS_PER_NODE=8`，单节点） | run_pretrain 脚本 |
| 序列/批 | `SEQ_LEN=8192`、`MBS=1`、`GBS=64` | run_pretrain 脚本 |

> HiF8 实验在 950DT 平台上进行，基于裁剪版 DeepSeek-v3 模型开展混合精度预训练验证。当前实验仅对整网中的 **MatMul（MM）和 Grouped MatMul（GMM）** 算子进行量化，其余对数值敏感的算子仍保留在较高精度路径中执行，以保证训练稳定性。

模型结构参数（MLA + MoE，`--*` 入参）：MLA `--q-lora-rank 1536 --kv-lora-rank 512 --qk-head-dim 128 --qk-pos-emb-head-dim 64 --v-head-dim 128`（`--multi-latent-attention`）；MoE `--num-experts 256 --moe-router-topk 8 --moe-shared-expert-intermediate-size 2048 --moe-router-score-function sigmoid --moe-router-num-groups 8 --moe-router-group-topk 4`（`--moe-grouped-gemm` 启用 GMM）；RoPE 走 YARN（`--rope-scaling-type yarn --rope-scaling-factor 40 --rope-scaling-original-max-position-embeddings 4096`）。

## MindSpeed 低精度框架与 TE 量化路径

低精度验证基于 MindSpeed + MindSpeed-LLM。MindSpeed Core 是面向昇腾的大模型加速库，MindSpeed-LLM 是其上的 LLM 场景组件；二者关系见下图。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image8.png" width="55%"></p>
<p align="center"><sub>图：MindSpeed Core 加速库与上层 MindSpeed-LLM 组件框架（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·MindSpeed 低精度训练框架）</sub></p>

低精度的入口是 MindSpeed 的 **Transformer Engine（TE）** 模块——接口/能力与官方 TE 兼容，在昇腾 NPU 上把 Linear 层矩阵乘改走 8-bit 路径：

> MindSpeed 低精度训练流程的核心在于，将前向传播（Fprop）、激活反向传播（Dgrad）和权重反向传播（Wgrad）过程中的通用矩阵乘法运算量化为 FP8 / HiF8 精度执行。整体训练流程仍基于 BF16 / FP16 的 AMP 混合精度模式，但在特定计算算子中，尤其是 Linear 层中的矩阵乘法运算（涵盖 Fprop、Dgrad 和 Wgrad），采用 FP8 / HiF8 精度路径执行。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image9.png" width="60%"></p>
<p align="center"><sub>图：TE 量化代码模块——TERowParallelLinear/TEColumnParallelLinear 把 Fprop/Dgrad/Wgrad 的 MatMul 替换为低精度路径，FP8GlobalStateManager 单例维护全局 FP8 状态，各 Recipe 类执行不同量化策略（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·Transformer Engine 量化代码模块实现）</sub></p>

MindSpeed 当前支持的低精度数据格式与算子组合（文档表 5 摘要，承重行）——HiF8 走 Delayed/Tensorwise，MXFP8 是 FP8 的细粒度 block 路径，且唯一覆盖到 TP-MC2（通信计算融合）与 MatMul Add：

| 数据格式 | 量化粒度 | MatMul | Grouped MatMul | TP-MC2 | MatMul Add |
|----------|----------|--------|----------------|--------|------------|
| FP8 | MXFP8 | ✅ | ✅ | ✅ | ✅ |
| HiF8 | Delayed | ✅ | Tensorwise 路径 | ❌ | ❌ |
| HiF8 | Tensorwise | ✅ | ✅ | ❌ | ❌ |

两种缩放策略的差异是性能分水岭——HiF8 因动态范围大可走低频 **Delayed Scaling**，把求 Amax 与下游 MatMul 解耦；FP8/MXFP8 动态范围小，往往得每步在线求 Amax（**Current Scaling**），与 MatMul 串行，抵消部分收益：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image6.png" width="48%"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image7.png" width="48%"></p>
<p align="center"><sub>图：左 Current Scaling（每 iteration 求 Amax，与下游计算串行）；右 Delayed Scaling（interval=K iterations 用历史统计估计 Amax，N_guard 防上溢）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·3.2 缩放方案）</sub></p>

## 真实拉起脚本（HiF8 / MXFP8 唯一差异在 FP8 块）

两个脚本 `run_pretrain_dsk3_A5_8P_{hif8,mxfp8}.sh` **除 `FP8="..."` 块外完全一致**。HiF8 走 Per-tensor Delayed Scaling（`interval=10`），MXFP8 走 block 级 mxfp8 recipe：

```bash
# run_pretrain_dsk3_A5_8P_hif8.sh — HiF8 块
FP8="
--fp8-format hif8
--fp8-recipe delayed
--fp8-interval 10
--transformer-impl transformer_engine
--te-gmm-mode performance
"

# run_pretrain_dsk3_A5_8P_mxfp8.sh — MXFP8 块（无 --fp8-interval，recipe=mxfp8）
FP8="
--fp8-format e4m3
--fp8-recipe mxfp8
--transformer-impl transformer_engine
--te-gmm-mode performance
"
```

共用的并行 / 性能环境变量（两脚本头部完全一致）：

```bash
# run_pretrain_dsk3_A5_8P_hif8.sh / _mxfp8.sh — 头部 export + 并行度
export CUDA_DEVICE_MAX_CONNECTIONS=1
export CPU_AFFINITY_CONF=1
export TASK_QUEUE_ENABLE=2
export PYTORCH_NPU_ALLOC_CONF="expandable_segments:True"
export HCCL_CONNECT_TIMEOUT=300
export STREAMS_PER_DEVICE=32          # A5 超节点多流
NPUS_PER_NODE=8; NNODES=1
TP=1; PP=1; EP=8; CP=1; CP_TYPE='ulysses_cp_algo'
NUM_LAYERS=2; SEQ_LEN=8192; MBS=1; GBS=64
```

GMM 由 `--moe-grouped-gemm` 打开（MoE 专家分支用 Grouped MatMul），故低精度量化覆盖到的「MM/GMM」两类主干算子在本配置里都真实存在；`--use-flash-attn`、`--use-fused-rmsnorm`、`--use-fused-swiglu` 等融合算子与 `--attention-softmax-in-fp32` 保留高精度路径。最终命令把 `$FP8 $GPT_ARGS $MLA_ARGS $ROPE_ARGS $MOE_ARGS` 拼进 `pretrain_gpt.py`：

```bash
# 两脚本共用的拉起命令（仅 --profile-save-path / tee 日志名按 hif8/mxfp8 区分）
python -m torch.distributed.launch $DISTRIBUTED_ARGS pretrain_gpt.py \
  $PROFILE_ARGS $FP8 $GPT_ARGS $DATA_ARGS $OUTPUT_ARGS \
  $MLA_ARGS $ROPE_ARGS $MOE_ARGS --distributed-backend nccl | tee <log>
```

执行前需先 `source` CANN/ATB 环境并设超节点拓扑（README「pretrain 执行」节）：

```bash
# llm_pretrain/DeepSeekV3/README.md — pretrain 执行
export GLOO_SOCKET_IFNAME=eth0
export HCCL_HOST_SOCKET_PORT_RANGE=auto
source /usr/local/Ascend/cann/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export HCCL_TOPO_FILE_PATH=/etc/superpod_1d_noroce.json   # A5 超节点 1D 拓扑
export HCCL_CONNECT_TIMEOUT=200; export HCCL_EXEC_TIMEOUT=200
bash ./run_pretrain_dsk3_A5_8P_mxfp8.sh   # 或 _hif8.sh
```

## 环境与权重 hf2mcore 转换

框架版本对接（承重）：源码侧装 MindSpeed（`master`，`pip install -e .`）、MindSpeed-LLM（`master`），底座 Megatron-LM 取 `core_v0.12.1` 并把其 `megatron` 目录 `cp` 进 MindSpeed-LLM（mcore 底座以源码 cp 方式合入，而非 pip 包）。具体 PyTorch/torch_npu whl 版本与 CANN/ATB 安装步骤见 Evidence 的 README「构建环境」节。

数据集用 enwiki parquet，经 `data_convert_deepseek3_pretrain.sh` 转为 `enwiki_text_document`（`DATA_PATH` 指向它，`--split 100,0,0` 全训练集）。

权重侧用 **hf2mcore** 把 HuggingFace 权重转为 Megatron-core（mcore）格式：

```bash
# README「模型权重准备」— 从魔搭下 DeepSeek-V3 基础文件（裁剪模型可不下权重，仍需此步取配置）
modelscope download --model deepseek-ai/DeepSeek-V3 --local_dir /data/models/DeepSeek-V3
# 参考 MindSpeed-LLM examples/mcore/deepseek3/ckpt_convert_deepseek3_hf2mcore.sh
# 修改原始权重路径、保存路径与对应切分/裁剪策略后：
bash examples/mcore/deepseek3/ckpt_convert_deepseek3_hf2mcore.sh   # 转为 mcore 权重
```

> 从魔搭社区下载模型的基础文件，存放至样例的 `./assets/hf/DeepSeek-V3` 目录下（不加载权重实验也需要执行这步操作）……当前是裁剪模型可以不下载权重。

脚本用 `--no-load-optim --no-load-rng`、`TOKENIZER_PATH` 指向 HF 权重目录取 tokenizer/config（`--tokenizer-type PretrainedFromHF`）。

## Benchmark（HiF8/MXFP8 vs BF16）

同一平台、模型、量化覆盖范围（仅 MM/GMM）下三种精度对比，BF16 单步端到端 **3.63629095 s**：

| 指标 | HiF8 | MXFP8（E4M3） | BF16 | HiF8 vs MXFP8 | HiF8 vs BF16 |
|------|------|--------------|------|---------------|--------------|
| 单次迭代时间 (s) | 2.80796152 | 3.12526599 | 3.63629095 | **1.113×** | **1.295×** |
| 量化粒度 | Per-tensor | Per-block | — | — | — |
| 缩放策略 | Delayed（interval=10） | block 级 scaling | — | — | — |

即 HiF8 相对 BF16 提速 **29.5%**、MXFP8 相对 BF16 提速 **14.05%**、HiF8 相对 MXFP8 再快 **11.3%**。两种格式的损失曲线与 Gradient Norm 都基本对齐 BF16：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image12.png" width="48%"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image13.png" width="48%"></p>
<p align="center"><sub>图：950DT 裁剪 DeepSeek-V3 长稳精度对比——左 BF16 vs HiF8、右 BF16 vs MXFP8（各含训练损失/损失相对差值/Gradient Norm/Gradient Norm 相对差值四联图），损失与梯度范数基本对齐（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·5.1/5.2 混合精度训练实验）</sub></p>

收益拆解：① **位宽减半的访存收益**（16→8 bit，缓解片上带宽压力、提缓存复用、降搬运延迟）；② **8-bit 计算吞吐**——MM/GMM 映射到低精度路径，HiF8 相对 BF16 的 MM 与 GMM 算子平均加速比 **超过 1.8 倍**：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image14.png" width="62%"></p>
<p align="center"><sub>图：HiF8 vs BF16 的 MM 算子（左）与 GMM 算子（右）对比，平均加速比 >1.8×（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·6.1.2 8-bit 计算吞吐提升）</sub></p>

HiF8 相对 MXFP8 的额外收益来自**量化粒度与缩放元数据开销**：MXFP8 走 Per-block，每块要维护并频繁访问 scale；HiF8 动态范围大，可走 Per-tensor，scale 数量与访存少、控制逻辑简单、更适合 Delayed Scaling。GMM 算子两方案的 profiling 对比：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image15.png" width="60%"></p>
<p align="center"><sub>图：DeepSeek-V3 裁剪网络中 GMM 算子在 HiF8 与 MXFP8 下的 profiling 对比，HiF8 Per-tensor 路径元数据/控制开销更低（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·6.2 HiF8 相对 MXFP8 的收益来源）</sub></p>

> 当前实验仅对整网中的 MM 和 GMM 算子进行了量化，因此目前测得的收益属于部分算子量化条件下的端到端收益。若后续将 HiF8 扩展到更多适合低比特量化的算子（如 FlashAttention 及集合通信算子），整体收益仍有进一步提升空间。

## 推荐配置（HiF8）

文档第七章给出的 HiF8 训练推荐配置（与本脚本一致）：量化粒度 **Per-tensor**、缩放策略 **Delayed Scaling**、更新周期 **interval=10 steps 或更高**、覆盖算子 **MM/GMM**、Master Weights 维持 **FP32/BF16**。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md)（第四章 MindSpeed/TE 量化框架 + 表 5 格式/算子组合、3.2 Current/Delayed Scaling、第五章 HiF8/MXFP8 实验、第六章收益分析（MM/GMM >1.8× + GMM profiling）、第七章推荐配置）
- [`llm_pretrain/DeepSeekV3/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/DeepSeekV3/README.md) — 概述（A5 8 卡 8K MXFP8/HiF8）、构建环境（MindSpeed/MindSpeed-LLM master + Megatron-LM core_v0.12.1）、数据集 enwiki、权重 hf2mcore 转换、pretrain 执行（HCCL 超节点拓扑 + bash run 脚本）
- [`llm_pretrain/DeepSeekV3/run_pretrain_dsk3_A5_8P_hif8.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/DeepSeekV3/run_pretrain_dsk3_A5_8P_hif8.sh) — HiF8 `FP8` 块（`--fp8-format hif8 --fp8-recipe delayed --fp8-interval 10`）、TP1/PP1/EP8/CP1、MLA/MoE/RoPE 入参、`pretrain_gpt.py` 拉起
- [`llm_pretrain/DeepSeekV3/run_pretrain_dsk3_A5_8P_mxfp8.sh`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/DeepSeekV3/run_pretrain_dsk3_A5_8P_mxfp8.sh) — MXFP8 `FP8` 块（`--fp8-format e4m3 --fp8-recipe mxfp8`，无 `--fp8-interval`），其余与 hif8 脚本完全一致

## Links

- [mindspeed](../../concepts/frameworks/mindspeed.md)（本 recipe 的承载框架：MindSpeed Core + MindSpeed-LLM + TE 量化模块）
- [hif8](../../concepts/quantization/hif8.md)（HiF8 数据格式与量化原理：Dot 域/Denormal/Per-tensor/Delayed Scaling 的完整推导）
- [deepseek-v32-pretrain](deepseek_v32_pretrain.md)（同域并列预训练路线：TorchTitan 671B 全量 + DSA，对照 MindSpeed 裁剪 + 低精度）
- [mxfp8-a8w8](../../../inference/concepts/quantization/mxfp8_a8w8.md)（跨域：推理侧 MXFP8（DiT Linear）A8W8，Per-group/E8M0 scale，与此处训练 MXFP8 Per-block 路径对照）
- [ascend-950](../../../inference/concepts/platforms/ascend_950.md)（跨域：950PR/950DT 代际特性，本配置训练用 950DT 单卡 486 TFLOPS）
- [deltanet-pretrain](deltanet_pretrain.md)（同域并列预训练：DeltaNet 线性注意力 NLP 样例）
