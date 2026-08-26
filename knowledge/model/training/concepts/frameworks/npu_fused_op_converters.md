---
type: Concept
title: NPU 基础融合算子 ModelConverter 家族（torchtitan-npu）
description: torchtitan-npu 基础融合算子 ModelConverter 家族（get_model_converter_config）：npu_gmm（npu_grouped_matmul 合并全专家同一 Linear，须配 npu_permute）/npu_permute（npu_moe_token_permute/unpermute MoE 重排）/npu_rms_norm（npu_rms_norm）/npu_rope（npu_rotary_mul），均绑 torch_npu 原生算子（非新 AscendC kernel）。benchmark：单 step −5.16%、RMSNorm −71.2%(138.7→39.9μs)、Permute −84.2%(803.9→127.3μs)、GMM −22.6%(3.1→2.4ms)。DSA/SMLA/mHC converter 见各专页。
tags:
- task.implementation
- topic.architecture
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# NPU 基础融合算子 ModelConverter 家族

## Summary

torchtitan-npu 在 `torchtitan_npu/converters/kernels/` 下定义了一组 torchtitan `ModelConverter`：模型训练任务启动时，它们根据用户配置，自动把模型中的原始模块替换为基于 **torch_npu 融合算子** 的亲和实现，从而让模型在 NPU 平台上高效运行。

基础融合算子家族 `npu_gmm` / `npu_permute` / `npu_rms_norm` / `npu_rope` 把模型里的标准模块**绑定到现成的 `torch_npu` 算子**（而非新写 AscendC kernel）。模型特有的稀疏注意力 / MHC converter 各有页面：[slig](../kernels/slig.md) 的 DSA、[smla](../kernels/smla.md) 的 SMLA、[mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md) 的 mHC。

## 配置

所有 NPU converter 通过 `ModelConvertersContainer.Config` 的 `converters` 列表启用，每个 converter 名先经 `get_model_converter_config()` 转成 Config 对象：

```python
from torchtitan.protocols.model_converter import ModelConvertersContainer
from torchtitan_npu.converters import get_model_converter_config

model_converters = ModelConvertersContainer.Config(
    converters=[
        get_model_converter_config("npu_dsa"),
        get_model_converter_config("npu_rms_norm"),
        get_model_converter_config("npu_permute"),
        get_model_converter_config("npu_gmm"),
    ],
)
```

每个 converter 模块用 `@register_model_converter("<name>")` 装饰一个 `ModelCustomConfig` 子类（内含 `model_converter` 类），`converters/__init__.py` 的 `_auto_search_conveter()` 在 import 时自动扫描 `kernels/` 与 `features/` 下所有模块完成注册；converter 的 `convert()` 遍历 `model.named_modules()`，对匹配类型的模块调 `replace_module_with_name(...)` 原地替换。注册/装配机制详见 [model-custom-converter](model_custom_converter.md)，整体框架见 [torchtitan](torchtitan.md)。

## npu_gmm（Grouped MatMul）

MoE 模块中每个专家执行结构相同的 FFN（如 Swiglu：输入经升维 `w1` → 激活 → 降维 `w2`）。`npu_gmm` 引入分组矩阵乘 **`npu_grouped_matmul`** 算子：接收 [npu_permute](#npu_permute) 输出的重排后 token 及对应专家索引，在一次调用中并行计算所有专家的同一线性层（如所有专家的 `w1`），把同类矩阵运算合并为一次算子调用以提升计算效率。

> ⚠️ 使用 `npu_gmm` 时**必须同时开启 `npu_permute` 配合使用**——GMM 依赖 permute 产出的重排 token + 索引。

- **converter 类**：`NpuGroupedExpertConverter`，匹配并替换 `GroupedExperts` 模块（`@register_model_converter("npu_gmm")`）；`GMMModelConfig` 还挂了 `state_dict_updater = GMMStateDictUpdater`（HF 权重的 `w13` 融合/拆分映射）。

## npu_permute

MoE 前向中，为利用 [npu_gmm](#npu_gmmgrouped-matmul) 提升效率，token 需按 MoE Router 为每个 token 分配的专家以特定顺序**重排**（输出重排后 token 及其专家索引）；专家计算完成后再**恢复**回原始 token 顺序。`npu_permute` 把"重排/恢复"替换为基于 **`npu_moe_token_permute` / `npu_moe_token_unpermute`** 算子的实现：

```python
indices = selected_experts_indices.view(-1, top_k)           # router 分配 [T, K]
routed_input, sorted_indices = torch_npu.npu_moe_token_permute(x, indices)
...
unpermuted = torch_npu.npu_moe_token_unpermute(routed_output, sorted_indices, None)
```

该 converter 除替换 MoE 模块前向外，还通过 `parallelize_plan_updater = NpuParallelizePlanUpdater` 把并行计划里的标准 `ExpertParallel` **替换为 `NpuExpertParallel`**——后者承接 EP 维度的 token dispatch / combine。

- **两段语义不同的 permute**：(1) **router 后聚合**——`_npu_moe_forward` 用 `selected_experts_indices`（top-k 专家槽 `[T, K]`）做第一组 token/expert 重排；(2) **EP all-to-all 后的 local reroute**——`NpuExpertParallel._token_dispatch` 在 all-to-all 之后把 token 从 rank-major 布局重排为 local-expert-major，其 `indices` 由 `num_tokens_per_expert_group` 经 `arange(num_local_experts).repeat(ep_degree).repeat_interleave(...)` 构造，再调 `npu_moe_token_permute`。两者输入语义与布局目标不同，属并列的两步而非同一步。
- **converter 类**：`NpuPermuteConverter`（`@register_model_converter("npu_permute")`，同时匹配 `MoE` 与 DeepSeek-V4 `MoE`）；恢复路径上 EP combine 走 `NPUMoeTokenUnpermute.apply`（autograd.Function），其 `forward` 实际调 **`torch_npu._npu_moe_token_unpermute_with_routing_map(...)`**，上面片段里裸的 `npu_moe_token_unpermute` 是 MoE 前向直接恢复时用的等价路径（示意）。

## npu_rms_norm

RMSNorm 通过每个样本平方均值的平方根稳定深层网络训练。`npu_rms_norm` 把模型中的 `RMSNorm` 替换为基于 **`npu_rms_norm`** 融合算子的实现——`NPURMSNorm.forward` 直接调算子并取第 0 个返回值：

```python
resolved_eps = self.eps if self.eps is not None else torch.finfo(x.dtype).eps
return torch_npu.npu_rms_norm(x, self.weight, resolved_eps)[0]
```

`eps` 经 `_get_eps()` 从 `eps`/`variance_epsilon`/`epsilon` 三个属性名归一化；缺失时回退到输入 dtype 的机器 epsilon（对齐 `nn.RMSNorm` 默认行为）。

- **converter 类**：`NpuRMSNormConverter`，匹配并替换 `torchtitan.models.common.rmsnorm.RMSNorm`（`@register_model_converter("npu_rms_norm")`）

## npu_rope

RoPE 把与 token 位置相关的旋转矩阵应用到 Attention 的 Query / Key 上，使相对位置信息自然进入 Q·K 乘积。实现上通常预生成各位置旋转角度，Attention 时即时旋转 Q/K。`npu_rope` 把该旋转变换替换为基于 **`npu_rotary_mul`** 融合算子的实现：

```python
xq_out = torch_npu.npu_rotary_mul(xq_f, cos, sin)
xk_out = torch_npu.npu_rotary_mul(xk_f, cos, sin)
# interleave 变体：npu_rotary_mul(x_f, cos, sin, rotary_mode="interleave")
```

> 注：`converters/__init__.py` 的 `_auto_search_conveter()` **优先 import `rope` 模块**——其 module-level patch 把 NPU-safe 的 `_reshape_for_broadcast_complex` 装到 `common.rope` 上，须先于其它（如 `npu_smla` 经 `deepseek_v32.model` 快照该符号的）kernel 落地。

- **converter 类**：`NpuRoPEConverter`（`@register_model_converter("npu_rope")`）

## Benchmark（融合算子收益）

DeepSeek-V3.2 训练实测，启用上述基础融合算子相对原生实现的算子级 / 单 step 收益（亦见 [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)）：

| 范围 | 收益 | 耗时（前→后） |
|------|------|----------------|
| 完整模型单 step 计算 | **−5.16%** | — |
| RMSNorm（`npu_rms_norm`） | **−71.2%** | 138.7 → 39.9 μs |
| Permute（`npu_permute`） | **−84.2%** | 803.9 → 127.3 μs |
| GMM（`npu_gmm`） | **−22.6%** | 3.1 → 2.4 ms |

> 单算子收益（Permute/RMSNorm 各降 70–84%）远高于整模型单 step 的 −5.16%，因为这些算子只占整 step 的小部分；GMM 绝对耗时最大（ms 级），其 −22.6% 是单 step 收益的主要来源。

## 关联融合 converter

| Converter 名 | 面向 | 详见页面 |
|--------------|------|----------|
| `npu_dsa` | DeepSeek-V3.2 DSA（Lightning Indexer + Sparse Flash Attention） | [slig](../kernels/slig.md) |
| `npu_smla` | DeepSeek-V4 Sparse Flash MLA | [smla](../kernels/smla.md) |
| `npu_mhc_pre` / `npu_mhc_post` | DeepSeek-V4 MHC pre/post processing | [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md) |

## Evidence

- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/npu_fused_ops.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md)（融合算子适配总文档，converter 配置说明，不含收益指标）
- 实现源（@8f128cd）：[`converters/kernels/gmm.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/gmm.py)（`npu_gmm`）、[`converters/kernels/permute.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/permute.py)（`npu_permute`）、[`converters/kernels/rms_norm.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/rms_norm.py)（`npu_rms_norm`）、[`converters/kernels/rope.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/rope.py)（`npu_rope`）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（Benchmark 收益指标出处）

## Links

- [torchtitan](torchtitan.md) — torchtitan-npu 框架总览（converter 家族、Inductor、Bypass Triton）
- [model-custom-converter](model_custom_converter.md) — ModelConverter 注册 / 装配 / state-dict 更新机制
- [slig](../kernels/slig.md) — `npu_dsa` 的 Lightning Indexer / Sparse Flash Attention 融合算子
- [smla](../kernels/smla.md) — `npu_smla` Sparse Flash MLA converter
- [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md) — mHC HcPre / HcPost 融合算子
- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（基于本框架的 DeepSeek-V3.2 32K 预训练实践，Benchmark 数据所在 recipe）
- [qwen3-sft-torchtitan](../../guides/recipes/qwen3_sft_torchtitan.md)（SFT 配置用 npu_rms_norm/rope/permute/gmm converter）
- [tilelang-rope](../kernels/tilelang_rope.md)（npu_rope 绑定算子的底层 TileLang 训练实现）
- [tilelang-moe-token-permute](../kernels/tilelang_moe_token_permute.md)（npu_permute 绑定的 npu_moe_token_permute/unpermute 的底层 TileLang 实现）
- [tilelang-rmsnorm-swiglu](../kernels/tilelang_rmsnorm_swiglu.md)（npu_rms_norm 绑定算子的底层 TileLang 实现）
- [megatron-bridge](megatron_bridge.md)（MindSpeed-Bridge 权重桥接的邻近概念）
