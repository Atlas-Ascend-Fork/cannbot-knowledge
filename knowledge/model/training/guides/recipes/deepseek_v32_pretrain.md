---
type: Guide
title: DeepSeek-V3.2 当前训练配置与 32K 优化案例
description: 当前 deepseek_v3_2 debug 配置与 DSA/分片/编译边界，保留来源报告的 671B 32K A3 性能案例并撤下失效全量 TOML 命令。
tags:
- task.implementation
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/torch_compile.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- a3
---

# DeepSeek-V3.2 当前训练配置与 32K 优化案例

## 当前入口

当前模块为 torchtitan_npu.models.deepseek_v3_2，配置函数 deepseek_v3_2_debugmodel；旧 deepseek_v32/train_configs 目录与完整 671B 32K TOML 已移除。当前入口用于先验证模型/DSA 路径，不能把它当作原 64 卡全量训练配置。

```bash
MODULE=torchtitan_npu.models.deepseek_v3_2 \
CONFIG=deepseek_v3_2_debugmodel \
bash scripts/run_train.sh --training.steps 5 \
  --hf-assets-path /path/to/tokenizer
```

启动前按当前安装文档准备 NPU 栈、数据和融合算子，按实际资源覆盖并行与 batch。当前全量 32K 配置需独立重建、核验容量和并行度，本页不再提供旧 TOML/bypass 的启动命令。

## 当前实现的关键约束

当前融合 DSA 以 backend-owned TND metadata 连接 SFA 与 LI/SLIG。SLIG 前向返回零标量，反向计算 Indexer 梯度并按有效 token 数缩放与记录，不能沿用旧显式前向 KL-loss 的控制方式。CP 采用对应模型的 sharding/metadata 契约，不能将旧 infra/parallelize.py 的 monkey-patch 当作当前 API。

FSDP/EP/TP 的分片由 ShardingConfig 与当前并行 helper 装配。内存预算须同时计入非专家参数、梯度、优化器状态、激活与通信 buffer；来源案例的 PP2/TP4/EP64 是实验选型，不能由模型规模推导为当前唯一配置。

torch.compile 当前使用 torch_npu 内置 AscendC，按 Block 编译；旧 npu_bypass_triton_codegen 已移除。model/loss 的启用、custom op 契约和 AC 副作用见 [训练 AutoFuse](../../concepts/techniques/autofuse_train.md)。

## 来源报告的 32K 实验边界

当前 Recipes 文档保留了 671B、61层、32K、A3 64卡的优化案例：FSDP 二次分片减少非专家冗余，主机卸载动量降低峰值，DSA 训练融合核减少离散访存，编译降低 host 下发。下列数字与图片均为该来源报告，本次未重跑；不可归因于上面的 debug 配置或任意当前参数组合。

## Benchmark

**精度（收敛性）**：lm loss 由 step1 的 12.25 稳步降至 step37 的 8.37，grad norm 由 28.24 回落至 16.03，indexer loss 全程平稳递减——大规模分布式场景下精度正常。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/707014b7-bbcf-4d3b-8f36-ca968d1a42d4.png" width="62%"></p>
<p align="center"><sub>图：lm loss step1 12.25→step37 8.37、grad norm 28.24→16.03 稳健收敛（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Benchmark / 精度）</sub></p>

对 DeepSeek-V3.2 新增的 Lightning Indexer 也同步训练——整个预训练过程中 indexer loss 稳步下降、全程平稳递减，与 lm loss / grad norm 收敛曲线一致，佐证大规模分布式场景下精度正常。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/7073deeb-3896-4632-a6e9-f9871147ff65.png" width="50%"></p>
<p align="center"><sub>图：Lightning Indexer 训练 indexer loss 全程平稳递减（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·Benchmark/精度）</sub></p>

**性能**：A3 64 卡 671B 全量预训练 **148 TPS/卡**。DSA 融合算子在裁剪模型上的内存 / 性能对比（训练长度4K）：8层=1 dense+7 MoE，4层=1 dense+3 MoE，**每个 MoE 层均仅8个专家**，不能外推为保留完整专家数、只减层时的结果：

| 裁剪模型 | 实现方式 | 内存 | 性能 |
|---------|---------|------|------|
| 8 层 | 原始小算子 | 58.32G | 155 TPS |
| 8 层 | 矩阵吸收 + DSA 融合算子 | 50.54G | 400 TPS |
| 4 层 | 原始小算子 | 54.58G | 402 TPS |
| 4 层 | 矩阵吸收 + DSA 融合算子 | 38.71G | 568 TPS |

完整模型进一步开启基础融合算子（RMSNorm 138.7→39.9μs / −71.2%，Permute 803.9→127.3μs / −84.2%，GMM 3.1→2.4ms / −22.6%），单 step 计算时间减少 **5.16%**；开启 inductor compile 后单层耗时减少 **5.1%**，MLAProlog host 下发 11.0ms→5.7ms（V3.2 计算集中于 SFA / LI，host 侧下发优化对整网增益有限）。


## Evidence

- [config_registry.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/config_registry.py)（primary）
- [torch_compile.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/torch_compile.md)（supporting）
- [deepseek-v32_pre_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（supporting）

## Links

- [当前 DSA 反向](../../concepts/kernels/slig.md)
- [SFA 反向](../../concepts/kernels/sfag.md)
- [5D 分片](../../concepts/parallelism/torchtitan_5d_parallel.md)
- [上下文并行](../../concepts/parallelism/context_parallel_train.md)
- [FSDP](../../concepts/parallelism/fsdp.md)
- [训练 AutoFuse](../../concepts/techniques/autofuse_train.md)
