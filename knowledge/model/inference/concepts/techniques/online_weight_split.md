---
type: Concept
title: 权重在线切分（Online Split Weight）
description: 权重在线切分指模型加载时由系统自动将对应权重分发到各个 Device，**无需预先离线处理**，从而避免额外磁盘存储开销、提升调试效率、降低磁盘占用。cann-recipes-infer 在 `module/linear.py`、`module/fuse_moe_gmm.py` 提供了统一的在线切分 Linear / Embedding / MoE GMM 类，并在各模型的 `modeling_*.py` 中通过 `load_weights` 函数做 checkpoint 权重名 → 模型参数名的匹配与分发。 在线切分的核心机制：**每个相关模块在加载权重时获得当前 device 需要加载的权重切片位置**——根据 TP/EP 维度，从原始完整权重中 slice 出本卡分片，直接写入模块参数，跳过全局磁盘中转。
tags:
- task.optimization
- topic.model_architecture
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/common/online_split_weight_guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: implementation
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- agnostic
---

# 权重在线切分（Online Split Weight）

## Summary

权重在线切分指模型加载时由系统自动将对应权重分发到各个 Device，**无需预先离线处理**，从而避免额外磁盘存储开销、提升调试效率、降低磁盘占用。cann-recipes-infer 在 `module/linear.py`、`module/fuse_moe_gmm.py` 提供了统一的在线切分 Linear / Embedding / MoE GMM 类，并在各模型的 `modeling_*.py` 中通过 `load_weights` 函数做 checkpoint 权重名 → 模型参数名的匹配与分发。

在线切分的核心机制：**每个相关模块在加载权重时获得当前 device 需要加载的权重切片位置**——根据 TP/EP 维度，从原始完整权重中 slice 出本卡分片，直接写入模块参数，跳过全局磁盘中转。

## Mechanism

### 矩阵乘与切分轴约定

$$
Y = XW + B
$$

- `X` = input_activations，shape `(M, K)`
- `W` = 权重，shape `(K, N)`
- `Y` = Linear 输出，shape `(M, N)`

切分轴使用 **M / K / N** 表示。

### 四种 Linear 类 + VocabEmbedding 类

`module/linear.py` 定义了四种切分策略下的 Linear 类与一个 Embedding 类：

| 类 | 切分轴 | 用途 |
|----|--------|------|
| **ReplicatedLinear** | 不切 | 不涉及 TP 切分的 Linear 模块 |
| **ColumnParallelLinear** | 切 **N 轴**（列切） | TP 切分需要切权重 N 轴 |
| **MergedColumnParallelLinear** | 切 **N 轴** + merge | 多个权重对同一 `input_activations` 做矩阵乘、且切 N 轴；**当前 merge 顺序为先对权重 slice 再 concat**（如 DeepSeek 的 MLP up / gate 权重） |
| **RowParallelLinear** | 切 **K 轴**（行切） | TP 切分需要切权重 K 轴 |
| **VocabParallelEmbedding** | 切 **vocab size** | Embedding 表按 vocab 维度切分（HSTU Embedding TP 也基于此扩展） |

### FusedMoEGMM（MoE 在线切分）

`module/fuse_moe_gmm.py` 定义 `FusedMoEGMM` 类，**当前支持纯 TP 或纯 EP 切分**。

## 当前模型适配

用切分Linear/Embedding/FusedMoEGMM替换原模块，在模型load_weights中映射checkpoint名、合并分支及专家ID，再调用对应weight_loader。MergedColumnParallelLinear是先slice再concat，权重组织不同时需显式适配。

ModelWorker.init加载配置与Tokenizer、验证参数并构建CommManager；可选模型update_model_cfg/check_model_config_before_loading在装载前执行。_load_weights完成实际权重迭代，_process_weights_after_loading委托模型方法，并可继续check_model_settings、offload_weights，最后model.to(device)。框架不替模型决定转置、NZ或scale类型。

旧指南仍含ModelRunner._process_weight_after_loading和enable_online_split_weight开关；当前统一InferenceConfig无此开关，不能照抄。在线切片也不等于所有模型都接受原始低精度权重：离线反量化或转换需求见各模型和量化路径指南。

## Applicable Scenarios

- **调试阶段**：避免离线切分带来的 "修改 TP 配置 → 重新离线切 → 拷贝到各节点" 循环；改配置直接重跑。
- **磁盘空间受限**：不同 `attn_tp_size` / `moe_tp_size` 组合不需要预存多份切分权重。
- **通用载入路径**：cann-recipes-infer 的大多数 LLM 模型的 `modeling_*.py` 都按此机制实现 `load_weights`。

## Constraints

- **FusedMoEGMM 当前仅支持纯 TP 或纯 EP**，TP+EP 混合切分需在模型侧自行扩展。
- **加载后处理按入口适配**：当前统一执行器在模型 `process_weights_after_loading()` 中决定哪些模块转置、转 NZ 以及如何处理 scale。跳过必要后处理或对不支持的权重执行转换都可能破坏语义。
- **MergedColumnParallelLinear 的 merge 语义固定为"先 slice 再 concat"**：如果模型里存在"先 concat 再 slice"的权重组织，需要额外适配。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [online_split_weight_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/common/online_split_weight_guide.md)（supporting）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）

## Links

- [cann-executor](../frameworks/cann_executor.md)
- [weight-nz](weight_nz.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [embedding-tp](../parallelism/embedding_tp.md)

## Notes

- **gap**：源 67 行文档只讲了 Linear / MoeGMM / VocabEmbedding 三类；Attention 的 head 切分（Q/K/V head 切）在 `docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md` 有独立描述，**属模型级适配**而非通用 `module/linear.py` 能覆盖；本页未并入。
- **gap**：量化场景 `scales_dtype` dict 的具体 key 命名约定（哪些 scale 名会出现、与 [w8a8c8](../quantization/w8a8c8.md) 如何对接）源文档未展开。
