---
type: Guide
title: Ascend-TLA · DeltaNet 线性注意力 NLP 预训练样例
description: 昇腾 NPU 上 DeltaNet（Delta Rule）线性注意力的训练侧入门样例：一个基于 DeltaNet 线性注意力、面向昇腾 NPU 的实践样例，配套 NLP 语言建模训练流程与 Quick Start Notebook，更完整工程见上游仓库 Ascend-TLA（https://gitcode.com/SMULL_Group/Ascend-TLA.git）。其定位与同域其它 recipe 不同：不是大规模分布式实践，而是一条「先读 Notebook、再跑 GPT-2 风格语言建模」的算子+训练上手梯子，配 demo_config.zip 演示配置即可在单机体验 DeltaNet 算子与 NLP 训练评测全流程。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/ascend_tla_deltanet/README.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a2
---

# Ascend-TLA · DeltaNet 线性注意力 NLP 预训练样例

## Summary

昇腾 NPU 上 **DeltaNet（Delta Rule）线性注意力**的训练侧入门样例：一个基于 DeltaNet 线性注意力、面向昇腾 NPU 的实践样例，配套 **NLP 语言建模**训练流程与 Quick Start Notebook，更完整工程见上游仓库 `Ascend-TLA`（`https://gitcode.com/SMULL_Group/Ascend-TLA.git`）。其定位与同域其它 recipe 不同：不是大规模分布式实践，而是一条「先读 Notebook、再跑 GPT-2 风格语言建模」的算子+训练上手梯子，配 `demo_config.zip` 演示配置即可在单机体验 DeltaNet 算子与 NLP 训练评测全流程。

底层 **Ascend-TLA** 在昇腾 NPU 上基于 **Triton** 实现高效注意力算子；本样例聚焦 **Delta Rule / DeltaNet** 路径及 **NLP** 侧训练与 Notebook，不包含通用 Linear Attention 算子目录（`linear_attn`）、视觉（CV）模型与相关文档。

DeltaNet 是 DeltaNet/线性注意力谱系在**训练侧**的代表实现；推理侧的同谱系模块见跨域页 [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)（Qwen3-Next 的 Gated DeltaNet）与 [qwen3-next](../../../inference/concepts/models/qwen3_next.md)，「与推理侧 Gated DeltaNet 的异同」节做对照。完整环境/命令以上游仓 `Ascend-TLA`（`https://gitcode.com/SMULL_Group/Ascend-TLA.git`）为准。

## DeltaNet 线性注意力机制要点

三条核心特性：

- **DeltaNet（Delta Rule）**：序列长度维度的并行化线性 Transformer 实现要点见下游论文与上游 `tla/ops/delta_rule`。
- **NLP 语言建模**：GPT-2 风格架构，可与 SlimPajama 等数据配合使用。
- **评测**：可与 `lm-eval` 等工具对接（详见上游与 Notebook 说明）。

DeltaNet 是一类**沿序列长度维度可并行化的线性 Transformer**（线性注意力），其算子实现位于上游 `internal/tla/nlp/tla-nlp-frame/tla/ops/delta_rule`，算子目录含 `delta_rule`、`common`、`utils` 等，**不包含** `linear_attn`。NPU 侧实现与训练入口见 `internal/tla/nlp/`。

## 相关模型与论文

NLP（DeltaNet）的参考条目：

| Year | Venue | Paper | Code |
| ---- | ----- | ----- | ---- |
| 2024 | NeurIPS | Parallelizing Linear Transformers with Delta Rule over Sequence Length（`https://arxiv.org/abs/2406.06484`） | flash-linear-attention / delta_net（`https://github.com/fla-org/flash-linear-attention/blob/3e61322b615df248e7579222d1a68260560f7c24/fla/layers/delta_net.py`） |

NPU 侧实现与训练入口见 `internal/tla/nlp/`。
- [gated-deltanet-train](../../concepts/modules/gated_deltanet_train.md)（GDN 训练模块：chunk 并行 / Flash / GDN 上下文并行的机制枢纽）

## 本样例支持的任务

- **NLP**
  - 语言建模（GPT、LLaMA 等量级可按上游配置裁剪）
  - 数据集示例：SlimPajama（见 Notebook 与 `preparation` 脚本）
  - 评测：`lm-eval` 等（见 `02_downstream_nlp.ipynb`）

本样例**不包含** CV 分类/检测等任务与通用 **Linear Attention（`linear_attn`）** 算子章节。

## 训练配置

| 维度 | 配置 |
| --- | --- |
| 注意力机制 | DeltaNet（Delta Rule）线性注意力，算子基于 Triton 在昇腾 NPU 实现 |
| 模型架构 | GPT-2 风格语言建模（GPT、LLaMA 等量级可按上游配置裁剪） |
| 阶段 / 任务 | pretrain / NLP 语言建模 |
| 数据集 | SlimPajama（示例，见 Notebook 与 `preparation` 脚本） |
| 评测 | `lm-eval` 等（见 `02_downstream_nlp.ipynb`） |
| 演示配置 | `demo_config.zip`（含 `config.json` / `tokenizer.json` / `vocab.json` / `merges.txt` 等） |

环境与依赖在样例根目录用 `requirements.txt`（按团队规范锁定版本）；完整环境搭建、CANN / PyTorch / Triton 等组合以上游仓 `Ascend-TLA`（`https://gitcode.com/SMULL_Group/Ascend-TLA.git`）说明为准。

## 样例目录结构

```text
ascend_tla_deltanet/
├── README.md
├── patches/                    # 框架补丁
└── internal/
    ├── quick_start/            # 概览、DeltaNet 算子、NLP 下游 Notebook
    └── tla/
        ├── utils.py
        ├── modules/
        ├── torch/              # 如 delta_net 相关参考实现
        └── nlp/
            └── tla-nlp-frame/  # 训练脚本、democonfig、DeltaNet attention 等
```

算子实现位于 `internal/tla/nlp/tla-nlp-frame/tla/ops/`（含 `delta_rule`、`common`、`utils` 等），**不包含** `linear_attn`。

## 演示配置 democonfig

为控制样例仓体积，`training/democonfig/` 在代码树中**仅保留占位**（`.gitkeep`），不含完整模型与分词器文件；训练与 Notebook 所需配置打包为 `demo_config.zip`（在 `demo-config-download` 分支的 downloads 目录），解压到 `training/democonfig/` 即可。解压后含 `config.json`、`tokenizer.json`、`vocab.json`、`merges.txt` 等，供 `train.sh` 与 Notebook 的 `model=`、`tokenizer=` 使用。

## 快速开始

NLP 语言建模训练脚本与 DeepSpeed 配置见 `internal/tla/nlp/tla-nlp-frame/training/`。**先按上一节解压 `democonfig`**，再启动训练；配置示例为 `internal/tla/nlp/tla-nlp-frame/training/democonfig/config.json`。

建议先阅读三个 Quick Start Notebook：

- `internal/quick_start/00_overview.ipynb`
- `internal/quick_start/01_operator_deltanet.ipynb` — DeltaNet 算子实践
- `internal/quick_start/02_downstream_nlp.ipynb` — NLP 数据、训练与评测流程

更详细的命令行与数据准备说明见 **Ascend-TLA 文档**（上游仓 `Ascend-TLA`，`https://gitcode.com/SMULL_Group/Ascend-TLA.git`）。

## 评测与验证

NLP（DeltaNet）下 CUDA 与 TLA（昇腾）两套实现在标准语言建模评测集上的对照：

| | PIQA (acc) | HellaSwag (acc_n) | WinoGrande (acc) | Arc_e (acc) | Arc_c (acc_n) |
| ---- | ---------- | ----------------- | ---------------- | ----------- | ------------- |
| CUDA | 63.8 | 32.2 | 52.9 | 46.1 | 20.4 |
| TLA | 64.3 | 32.7 | 50.4 | 45.0 | 18.9 |

昇腾 TLA DeltaNet 实现与 CUDA 参考实现在多项任务上精度对齐（互有高低，整体相当）。训练架构与配置见 `internal/tla/nlp/tla-nlp-frame/training/democonfig/`（需先下载并解压 `demo_config.zip`，见上文）。

**算子性能（torch_npu native vs Triton，Ascend 910B 1×，B=32 / H=8 / D=64）**：

| Seq Len | Stage | torch_npu (ms) | Triton (ms) | Speedup |
|:---:|:---|:---:|:---:|:---:|
| 512 | Forward / Backward / **Total** | 21.06 / 61.33 / **83.12** | 20.71 / 34.33 / **55.21** | 1.02x / 1.79x / **1.51x** |
| 1024 | Forward / Backward / **Total** | 32.41 / 106.44 / **139.70** | 40.88 / 67.64 / **108.69** | 0.79x / 1.57x / **1.29x** |
| 2048 | Forward / Backward / **Total** | 55.13 / 246.47 / **302.72** | 81.07 / 134.30 / **215.56** | 0.68x / 1.84x / **1.40x** |
| 4096 | Forward / Backward / **Total** | 109.47 / 744.56 / **855.82** | 161.68 / 267.61 / **429.58** | 0.68x / 2.78x / **1.99x** |

关键结论：Triton 融合算子的增益集中在**反向**（4096 时 2.78x），且随序列变长加速越显著（Total 1.51x→1.99x）；但**前向**在长序列反而比 torch_npu 慢（2048/4096 仅 0.68x）——所以"Triton 高效算子"的收益主要来自 Backward 与整体，而非 Forward。

算法与代码版权归上游 **Ascend-TLA** 项目及其许可证约束；使用本样例时请同时遵守上游仓库的 **License** 与引用要求。

## 与推理侧 Gated DeltaNet 的异同（跨域对照）

本样例的 DeltaNet 与推理侧 [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md) 同属 **DeltaNet / 线性注意力**谱系，均以 Delta Rule 递推状态更新为核心，沿序列做线性复杂度上下文聚合；二者参考的也是同一篇 Delta Rule 论文与 `fla-org/flash-linear-attention` 实现脉络。差异在于：

- **侧重不同**：本样例是**训练侧**入门样例（GPT-2 风格 NLP 语言建模，Triton 算子，DeepSpeed 训练，`lm-eval` 评测）；推理侧 [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md) 是 [qwen3-next](../../../inference/concepts/models/qwen3_next.md) / Qwen3.5-MoE 的 **Gated DeltaNet** 推理模块。
- **是否带门控**：本样例是**无门控的纯 Delta Rule**——`training/attentions/deltanet.py` 对 q/k 做 L2 单位范数后用 `beta`（clamp 1e-4~1-1e-4，写入强度）调 `chunk_delta_rule`，`torch/delta_net.py` 是分块 WY/T 矩阵递推的纯 Delta Rule 参考实现，全仓无 forget-gate / Conv1d / RMSNormGated（末端仅一个非 gated 的 RMSNorm）。推理侧 Gated DeltaNet 则显式叠加 forget gate、Causal Conv1d 与输出 RMSNorm+Gate（`conv_state` / `ssm_state` 状态缓存），并区分 Prefill ChunkGDN 与 Decode RecurrentGDN 两条融合路径——这一差异是确定的。
- **算子载体不同**：本样例算子基于 **Triton** 在 NPU 上实现（`tla/ops/delta_rule`）；推理侧 GDN 走 PyPTO ChunkGDN / AscendC RecurrentGDN / torch_npu 原生算子等多条 NPU 融合路径。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_pretrain/ascend_tla_deltanet/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/ascend_tla_deltanet/README.md)（概述 / 特性 / 相关模型与论文 / 环境与依赖 / 支持任务 / 目录结构 / democonfig 下载解压命令 / 快速开始 Notebook / 评测与验证 CUDA vs TLA 精度表 / 致谢与许可）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_pretrain/ascend_tla_deltanet/internal/quick_start/`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/ascend_tla_deltanet/internal/quick_start)（`00_overview.ipynb` / `01_operator_deltanet.ipynb` / `02_downstream_nlp.ipynb` 三个 Quick Start Notebook）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_pretrain/ascend_tla_deltanet/internal/tla/nlp/tla-nlp-frame/training/`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/ascend_tla_deltanet/internal/tla/nlp/tla-nlp-frame/training)（训练脚本 `train.sh` / DeepSpeed 配置 / `democonfig` 占位目录）；`tla/ops/delta_rule/README.md`（torch_npu native vs Triton 算子性能对照表）；`training/attentions/deltanet.py` + `torch/delta_net.py`（无门控纯 Delta Rule 实现）
- 上游 `Ascend-TLA` 仓（外部 URL `https://gitcode.com/SMULL_Group/Ascend-TLA.git`，完整环境搭建 CANN/PyTorch/Triton 组合、命令行与数据准备、License 以其为准）
- 论文：`Parallelizing Linear Transformers with Delta Rule over Sequence Length`（NeurIPS 2024，`https://arxiv.org/abs/2406.06484`）；参考实现 `fla-org/flash-linear-attention` delta_net

## Links

- [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)（跨域：推理侧 Gated DeltaNet 模块，DeltaNet/线性注意力同谱系；本页训练侧 vs 其推理侧门控结构异同见上文对照节）
- [qwen3-next](../../../inference/concepts/models/qwen3_next.md)（跨域：以 Gated DeltaNet 为线性注意力分支的混合注意力推理模型）
- [deepseek-v3-low-precision-pretrain](deepseek_v3_low_precision_pretrain.md)（同域并列：另一条 pretrain 阶段训练实践）
- [qwen2.5-rl](qwen2_5_rl.md)（同域并列：cann-train recipe 入门样例标杆，RL 阶段）
- [gdn-chunk-kernels](../../concepts/kernels/gdn_chunk_kernels.md)（同域：门控 DeltaNet chunk-parallel Triton 算子族，本样例 DeltaNet chunk 递推算子的 gated 形式对应）

<!-- cannbot:related:start -->
## 相关

- [Gated DeltaNet 训练（Chunk 并行 / Flash 递归 / GDN 上下文并行）](../../concepts/modules/gated_deltanet_train.md)（`related`）：样例卡将自身限定为“本样例聚焦 **Delta Rule / DeltaNet** 路径及 **NLP** 侧训练与 Notebook，不包含通用 Linear Attention 算子目录”；训练概念卡说明“GDN 的概念定义（in_proj → Causal Conv1d → 门控 → Delta Rule 递推 → 输出 RMSNorm+Gate）见推理侧”，为从无门控 DeltaNet 样例迁移到 Gated DeltaNet 训练时补上门控、递推与归一化差异。
<!-- cannbot:related:end -->
