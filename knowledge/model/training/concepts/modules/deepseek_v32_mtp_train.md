---
type: Concept
title: DeepSeek-V3.2 MTP 训练（torchtitan-npu 可配置长度多 Token 预测）
description: DeepSeek-V3.2 MTP 训练（torchtitan-npu 可配置长度多 Token 预测，兼容 FSDP2/EP/TP）：MTPModule 继承 TransformerBlockV32，按 DeepSeek-V3 技术报告(arxiv2412.19437)加 MTP 结构。关键设计：标准 Transformer 层与 MTP 层统一进顶层 model.layers，现有 FSDP2/EP/TP 并行逻辑零额外适配即作用于 MTP。loss：每 MTPModule 独立 CE，total_loss=main_loss+mtp_loss_weight·mtp_loss（patches/torchtitan/loss.py）。配置 TrainingConfig.num_mtp_modules(0=关,=预测 token 数)/mtp_loss_weight(0.3)。区别 cann-infer MTP 投机解码（推理侧）。V4 续训用 num_mtp_modules=1。
tags:
- task.design
- topic.model_architecture
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/deepseek_v32_mtp.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DeepSeek-V3.2 MTP 训练（可配置长度多 Token 预测）

torchtitan-npu 在 DeepSeek-V3.2 上适配了**多 Token 预测（Multi Token Prediction, MTP）训练**特性：单次前向同时预测多个连续目标 Token，通过扩展预测长度 + 引入辅助损失加速收敛，并兼容 FSDP2 / EP / TP 等分布式训练。实现长度可配置（`num_mtp_modules` 控制预测的 token 个数），参考 [DeepSeek-V3 技术报告](https://arxiv.org/pdf/2412.19437)。

> ⚠️ 此处 MTP 是**训练特性（辅助损失加速收敛）**。与推理域的 [mtp-speculative-decoding](../../../inference/concepts/techniques/mtp_speculative_decoding.md)（MTP 作为推理投机解码，用 MTP 头草拟候选 token 再验证）**作用域不同**：训练侧增训练效率，推理侧降解码延迟，共享同源 MTP 头结构但目标各异。

## 核心设计：MTP 层并入顶层 `model.layers`

为最大化复用成熟的分布式训练实现，**标准 Transformer Layer 与 MTP Layer 被统一封装进单一顶层 `model.layers` 列表**，从而与原有 FSDP2 / EP / TP 并行逻辑**无缝兼容、零额外并行化工作**。模型主类为 `DeepSeekV32ModelNpu`（`models/deepseek_v32/model.py`，[blob](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/deepseek_v32/model.py)），其 `__init__` 按 `num_mtp_modules` 切分主干层与 MTP 层：

```python
n_total = len(config.layers)
n_main = n_total - config.num_mtp_modules
self.layers = ModuleDict()
for layer_id, layer_cfg in enumerate(config.layers):
    if layer_id < n_main:
        self.layers[str(layer_id)] = TransformerBlockV32(layer_cfg, layer_id, n_total)
    else:
        self.layers[str(layer_id)] = MTPModule(layer_cfg, layer_id, n_total)
```

### `MTPModule` 类

`MTPModule` **继承自 `TransformerBlockV32`**，在其基础上新增 MTP 模块所需结构与参数（`model.py` 中 `class MTPModule(TransformerBlockV32)`）：

- `enorm` / `hnorm`：分别对当前 token embedding 与上一层预测流做归一化（复用 `attention_norm` 的 config，同 normalized_shape/eps/param_init）；
- `eh_proj = _Linear(2 * dim, dim, bias=False)`：将拼接后的 `[input_offset, prev_embed]`（dim 维 × 2）投影回模型维度。

`MTPModule.forward(input_offset, prev_embed, freqs_cis, ...)` 先 `enorm`/`hnorm` 归一化，再 `torch.cat([input_offset, prev_embed], dim=-1)` → `eh_proj` → 走 `TransformerBlockV32` 的 attention/FFN，输出送下一 MTP 层与 `output` 头。这与底层 [mla](../../../inference/concepts/modules/mla.md) 注意力结构一脉相承（V3.2 主干仍为 MLA）。

### 前向中的 MTP 主循环

`DeepSeekV32ModelNpu.forward` 先用前 `n_main_layers` 层算主干输出，再对每个 MTP 层用偏移 token embedding 续算（`model.py`）：

```python
seq_len -= self.num_mtp_modules
...
for mtp_layer_id in range(self.num_mtp_modules):
    token_offset_id = mtp_layer_id + 1
    token_offset = tokens[:, token_offset_id : token_offset_id + seq_len]
    input_offset = self.tok_embeddings(token_offset)
    layer_id = mtp_layer_id + self.n_main_layers
    h, residual = self.layers[str(layer_id)](input_offset, prev_embed, ...)
    ...
    output_list[mtp_layer_id + 1] = output
return output_list  # [main_output, mtp_out_1, ...]
```

`num_mtp_modules <= 0` 时直接返回单一 `output`（MTP 关闭）；否则返回 `1 + num_mtp_modules` 个输出张量列表。

## 损失：主损失 + 加权 MTP 损失

新增了适配 MTP 的训练损失函数：**每个 MTPModule 独立计算自己的交叉熵损失**，总损失为主损失与 MTP 损失的加权和。实现见 `torchtitan_npu/patches/torchtitan/loss.py`（patch 替换上游 `build_cross_entropy_loss`，当 `training.num_mtp_modules > 0` 时返回 `multi_token_cross_entropy_loss`，否则回退上游 `cross_entropy_loss`）：

```python
def multi_token_cross_entropy_loss(preds, labels, num_mtp_modules, mtp_loss_weight):
    seq_len = preds[0].shape[1]          # seq_len 由主预测张量内部推导，非入参
    main_loss = cross_entropy_loss(preds[0], labels[:, :seq_len])
    mtp_loss = 0
    for ...:  # 逐 MTP 头按 label 偏移取目标
        loss = cross_entropy_loss(pred, labels[:, label_offset:end_idx])
        loss = loss / num_mtp_modules        # MTP 各头损失先平均
        mtp_loss = mtp_loss + loss
    return main_loss + mtp_loss * mtp_loss_weight
```

即 `total_loss = main_loss + mtp_loss_weight * mtp_loss`。

## 配置选项

`num_mtp_modules` 与 `mtp_loss_weight` 已作为 **NPU 扩展字段**定义在 `torchtitan_npu.config.configs.TrainingConfig`（`@dataclass`，[blob](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/config/configs.py)），并在各模型的 `config_registry.py` 中配置：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `num_mtp_modules` | int | `0`（不开 MTP） | MTP 预测的 token 个数 |
| `mtp_loss_weight` | float | `0.3` | MTP 训练损失权重，`total_loss = main_loss + mtp_loss_weight * mtp_loss` |

代码配置：

```python
from torchtitan_npu.config.configs import TrainingConfig

training = TrainingConfig(
    local_batch_size=4,
    seq_len=2048,
    num_mtp_modules=1,
    mtp_loss_weight=0.3,
)
```

CLI 覆盖：

```bash
bash scripts/run_train.sh \
  --training.num_mtp_modules 1 \
  --training.mtp_loss_weight 0.3
```

## 在训练实践中的应用

- **DeepSeek-V3.2 预训练** [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)：MTP 训练特性的承载模型，主干 MLA + V3.2 稀疏注意力。
- **DeepSeek-V4 续训** [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)：续训中启用 `num_mtp_modules=1`。`models/deepseek_v4/config_registry.py` 的各正式注册项——`..._43_layers_bf16` / `..._43_layers_mxfp8` / `..._43layers_4k_128die` / `..._pro_debug_16_layers` / `..._pro_debug_61_layers_4k_384die`（覆盖 BF16、mxfp8、4K、pro_debug 16/61 层）——均设 `num_mtp_modules=1`；唯一例外是 `deepseek_v4_smoketest` 冒烟测试桩设 `num_mtp_modules=0`（关闭 MTP），并非某个真实续训变体。

> 注：`config_registry` 当前默认以 `num_mtp_modules=0` 构建层列表，`DeepSeekV32ModelNpu.Config.update_from_config` 支持**配置期 0→N 的增长**——当已构建数为 `0` 且 trainer 请求 `N>0` 时，调用 `_extend_dsv32_layers_with_mtp` 并 `self.layers.extend(new_layers)` 追加 N 个 MTP 层、同步 `num_mtp_modules`。仅当已构建数为**非 0** 且 trainer 请求改成不同值时才抛 `ValueError`（请求值与已构建值相同则直接跳过，`<0` 单独校验报错）。

## Links

- 训练框架枢纽：[torchtitan](../frameworks/torchtitan.md)
- 推理域对照（投机解码）：[mtp-speculative-decoding](../../../inference/concepts/techniques/mtp_speculative_decoding.md)
- 主干注意力：[mla](../../../inference/concepts/modules/mla.md)
- 应用 recipe：[deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md) · [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)

## Evidence

- 特性文档：[`docs/feature_guides/deepseek_v32_mtp.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/deepseek_v32_mtp.md)（torchtitan-npu @8f128cd）
- 模型实现：`torchtitan_npu/models/deepseek_v32/model.py`（`DeepSeekV32ModelNpu` / `MTPModule` / `TransformerBlockV32`；`DeepSeekV32ModelNpu.forward` MTP 循环）
- 损失实现：`torchtitan_npu/patches/torchtitan/loss.py`（`multi_token_cross_entropy_loss` / `mtp_build_cross_entropy_loss`）
- 配置字段：`torchtitan_npu/config/configs.py`（`TrainingConfig.num_mtp_modules` / `.mtp_loss_weight`）；注册：`models/deepseek_v32/config_registry.py`、`models/deepseek_v4/config_registry.py`
- 源页：[torchtitan-npu](https://gitcode.com/cann/torchtitan-npu)
