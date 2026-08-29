---
type: Concept
title: 权重在线切分（Online Split Weight）
description: 权重在线切分指模型加载时由系统自动将对应权重分发到各个 Device，**无需预先离线处理**，从而避免额外磁盘存储开销、提升调试效率、降低磁盘占用。cann-recipes-infer 在 `module/Linear.py`、`module/fuse_moe_gmm.py` 提供了统一的在线切分 Linear / Embedding / MoE GMM 类，并在各模型的 `modeling_*.py` 中通过 `load_weights` 函数做 checkpoint 权重名 → 模型参数名的匹配与分发。 在线切分的核心机制：**每个相关模块在加载权重时获得当前 device 需要加载的权重切片位置**——根据 TP/EP 维度，从原始完整权重中 slice 出本卡分片，直接写入模块参数，跳过全局磁盘中转。
tags:
- task.optimization
- topic.model_architecture
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/common/online_split_weight_guide.md
  role: supporting
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 权重在线切分（Online Split Weight）

## Summary

权重在线切分指模型加载时由系统自动将对应权重分发到各个 Device，**无需预先离线处理**，从而避免额外磁盘存储开销、提升调试效率、降低磁盘占用。cann-recipes-infer 在 `module/Linear.py`、`module/fuse_moe_gmm.py` 提供了统一的在线切分 Linear / Embedding / MoE GMM 类，并在各模型的 `modeling_*.py` 中通过 `load_weights` 函数做 checkpoint 权重名 → 模型参数名的匹配与分发。

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

`module/Linear.py` 定义了四种切分策略下的 Linear 类与一个 Embedding 类：

| 类 | 切分轴 | 用途 |
|----|--------|------| | **ReplicatedLinear** | 不切 | 不涉及 TP 切分的 Linear 模块 |
| **ColumnParallelLinear** | 切 **N 轴**（列切） | TP 切分需要切权重 N 轴 |
| **MergedColumnParallelLinear** | 切 **N 轴** + merge | 多个权重对同一 `input_activations` 做矩阵乘、且切 N 轴；**当前 merge 顺序为先对权重 slice 再 concat**（如 DeepSeek 的 MLP up / gate 权重） |
| **RowParallelLinear** | 切 **K 轴**（行切） | TP 切分需要切权重 K 轴 |
| **VocabParallelEmbedding** | 切 **vocab size** | Embedding 表按 vocab 维度切分（HSTU Embedding TP 也基于此扩展） |

### FusedMoEGMM（MoE 在线切分）

`module/fuse_moe_gmm.py` 定义 `FusedMoEGMM` 类，**当前支持纯 TP 或纯 EP 切分**。

## 模型适配五步

### 步骤一：替换 Linear / Embedding 类

根据 TP 切分策略把模型脚本中的 `nn.Linear` 替换为上述四种之一，`nn.Embedding` 替换为 `VocabParallelEmbedding`。

### 步骤二：替换 MoeGMM 类

若模型含 MoE 模块，参考上节将 MoE 计算替换为 `FusedMoEGMM`。

### 步骤三：修改 modeling 文件

在模型类中增加：

```python
def load_weights(self, weights: Iterable[Tuple[str, torch.Tensor]]):
 ...
```

**函数职责**：遍历权重文件中的所有权重，将权重 name 层级与模型 param 层级进行匹配，匹配成功后调用模块的 `weight_loader`；若模块未定义 `weight_loader`，则调用 `default_weight_loader`。

**特殊处理**：部分权重加载时需要特殊处理或额外传参（例如 `MergedColumnParallelLinear` 需要知道当前是 up 还是 gate），可通过 **map 的方式** 在 `load_weights` 中匹配并对匹配到的模块做针对性处理。

### 步骤四：适配 `_process_weight_after_loading`

基类 `ModelRunner` 通过遍历模型子模块的方式调用子模块的 `process_weights_after_loading` 方法，**默认对所有 Linear 与 GroupedMatmul 的权重进行转置 + NZ 格式化**（即 `enable_weight_nz = True`，见 [weight-nz](weight_nz.md)）。

**需重写的场景**：

- 某些特殊 Linear 类权重不需要转置或不转 NZ → 重写 `_process_weight_after_loading`，修改对应子模块 `process_weights_after_loading` 的传参。
- 量化场景需要改变 Linear 类中 scale 或 smooth scale 的数据类型 → 给参数 `scales_dtype` 传一个 dict：`{"scale名称": "target数据类型"}`。

### 步骤五：YAML 开关

```yaml
model_config:
 enable_online_split_weight: True
```

## Applicable Scenarios

- **调试阶段**：避免离线切分带来的 "修改 TP 配置 → 重新离线切 → 拷贝到各节点" 循环；改配置直接重跑。
- **磁盘空间受限**：不同 `attn_tp_size` / `moe_tp_size` 组合不需要预存多份切分权重。
- **通用载入路径**：本仓大多数 LLM 模型的 `modeling_*.py` 都按此机制实现 `load_weights`。

## Constraints

- **FusedMoEGMM 当前仅支持纯 TP 或纯 EP**，TP+EP 混合切分需在模型侧自行扩展。
- **默认 Linear 权重转置 + NZ**：若模型有特殊 Linear 不参与转置/NZ，需要重写 `_process_weight_after_loading`，否则可能破坏计算语义。
- **MergedColumnParallelLinear 的 merge 语义固定为"先 slice 再 concat"**：如果模型里存在"先 concat 再 slice"的权重组织，需要额外适配。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/common/online_split_weight_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/common/online_split_weight_guide.md)（67 行完整指南）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`module/Linear.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/module/Linear.py)（4 种 ParallelLinear + VocabParallelEmbedding）、`module/fuse_moe_gmm.py`（FusedMoEGMM）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 各模型 `modeling_*.py` 中的 `load_weights` 与 `_process_weight_after_loading` 重写

## Links

- [cann-executor](../frameworks/cann_executor.md)
- [weight-nz](weight_nz.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [embedding-tp](../parallelism/embedding_tp.md)

## Notes

- **gap**：源 67 行文档只讲了 Linear / MoeGMM / VocabEmbedding 三类；Attention 的 head 切分（Q/K/V head 切）在 `docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md` 有独立描述，**属模型级适配**而非通用 `module/Linear.py` 能覆盖；本页未并入。
- **gap**：量化场景 `scales_dtype` dict 的具体 key 命名约定（哪些 scale 名会出现、与 [w8a8c8](../quantization/w8a8c8.md) 如何对接）源文档未展开。
