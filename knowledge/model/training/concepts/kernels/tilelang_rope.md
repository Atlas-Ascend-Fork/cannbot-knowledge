---
type: Concept
title: TileLang RoPE（旋转位置编码，TileLang-Ascend 训练算子）
description: TileLang-Ascend RoPE 训练融合算子（DeepSeek-V3.2，前向+反向，训推通用）：interleave/half 两种旋转模式（interleave rotate([x0,x1,x2,x3])=[-x1,x0,-x3,x2]；half=[-x2,-x3,x0,x1]），前向 out=x*cos+rotate(x)*sin、反向 dx=cos*dy+swap(sin_masked*dy)；Partial RoPE 仅末 rope_dim 维；纯 Vector 算子（按操作类型推断）+ fp32 计算（前向为逐元素 FMA，非归约累加）；block_M 默认 64(fp16/bf16)/32(fp32)；6 步 TileLang 流程（block load→cast fp32→sin/cos load→gather+mask 元素重排→RoPE 计算→writeback）。是 npu_rope converter 绑定算子的 TileLang 实现。
tags:
- task.implementation
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
---

# TileLang RoPE（旋转位置编码，TileLang-Ascend 训练算子）

## Summary

RoPE（Rotary Position Embedding，旋转位置编码）是大模型中的位置编码算子：与绝对位置编码不同，它通过**旋转向量**把位置信息融入注意力，更好地捕捉**相对位置**关系。DeepSeek-V3.2 中的 RoPE 算子由 [tilelang](../../../inference/concepts/frameworks/tilelang.md) 实现，是 TileLang-Ascend「8 个训练算子」之一。该算子同时实现**前向与反向**传播，「支持前向和反向传播计算，适用于模型训练和推理场景」，因此**训练与推理通用**。TileLang 编程模型 / CodeGen / JIT 基础见 [tilelang](../../../inference/concepts/frameworks/tilelang.md)。

算子有两个核心特性：**Partial RoPE**（仅对张量最后 `rope_dim` 维做旋转，前 `dim_start` 维保持不变，匹配 MLA 的「nope + rope」分量切分）与**双旋转模式**（interleave / half，决定元素重排映射）。FP16/BF16 输入统一提升到 FP32 计算以保数值稳定，算完再 cast 回原 dtype。

在 TorchTitan-npu 训练栈里，模型侧的旋转变换由 [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md) 的 `npu_rope` converter 绑定（替换 3 个上游 rope 函数，均以 `torch_npu.npu_rotary_mul` 为后端算子——`cos_sin` 路径用默认 half 模式，`complex` / `single-complex` 路径传 `rotary_mode="interleave"`）；TileLang-Ascend RoPE 是与之等价语义的另一条算子实现路径，可作为 op 替换候选。

## 算法流程详解

### 输入输出张量（典型维度）

| 张量 | 形状 | 含义 |
|------|------|------|
| `x` | `[M, hidden_size]` 或 `[B, S, N, D]` | 输入张量 |
| `sin` | `[sc_rows, rope_dim]` | 旋转正弦角度向量 |
| `cos` | `[sc_rows, rope_dim]` | 旋转余弦角度向量 |
| `mask` | `[row_per_vec, rope_dim]` | 旋转索引掩码向量（编码元素重排映射） |
| `output` | 与输入同形状 | 旋转位置编码输出 |

### 计算流程（6 步）

```mermaid
flowchart TD
    A["1. 数据加载与预处理<br/>按 block_M 分块载入 UB；Partial RoPE 仅取最后 rope_dim 维"] --> B["2. 数据类型转换<br/>fp16/bf16 → fp32（T.tile.cast）保精度"]
    B --> C["3. sin/cos 加载<br/>row_sin_cos = (row_x // head_num) % sc_rows<br/>按索引载入 sin/cos 至 UB"]
    C --> D["4. 旋转操作（元素重排）<br/>T.tile.gather + mask 实现 rotate()<br/>interleave 或 half 模式"]
    D --> E["5. RoPE 计算<br/>fwd: out = x*cos + rotate(x)*sin<br/>bwd: dx = cos*dy + swap(sin_masked*dy)"]
    E --> F["6. 结果写回<br/>fp32 → 原 dtype；partial 仅更新最后 rope_dim 维"]
```

**① 数据加载与预处理**
- **分块加载**：按 `block_M` 大小将输入分块载入 UB buffer，`block_M` 默认为 **64**（float16/bfloat16）或 **32**（float32）。
- **Partial RoPE 支持**：当 `rope_dim < hidden_size` 时，仅对输入最后 `rope_dim` 维应用旋转，前 `dim_start` 维保持不变。

**② 数据类型转换**
- **精度提升**：对 float16/bfloat16 输入，用 `T.tile.cast` 转换为 **float32** 计算，确保数值精度与稳定性。

**③ sin/cos 加载**
- **位置索引计算**：按 `head_num` 与行位置算 sin/cos 索引，公式 `row_sin_cos = (row_x // head_num) % sc_rows`。
- **旋转角度加载**：按算得的索引把对应 sin/cos 载入 UB buffer。

**④ 旋转操作（元素重排）**
- 用 `T.tile.gather` 配合 `mask` 实现旋转中的元素重排——`mask` 向量编码了旋转所需的索引映射关系。
- 两种旋转模式的重排映射（以 4 元素为例）：

  | 模式 | `rotate([x0, x1, x2, x3])` | 重排语义 |
  |------|----------------------------|----------|
  | **interleave** | `[-x1, x0, -x3, x2]` | 相邻元素对交换旋转 |
  | **half** | `[-x2, -x3, x0, x1]` | 前后半部分交换旋转 |

**⑤ RoPE 计算（前向 / 反向）**
- **前向传播**：
  ```
  out = x * cos + rotate(x) * sin
  ```
- **反向传播**：
  ```
  dx = cos * dy + swap(sin_masked * dy)
  ```
  其中 `dy` 是上游梯度，`sin_masked` 为按 mask 作用后的 sin（据 RoPE 旋转的正交性，`swap(·)` 即对应前向 `rotate` 的逆重排，反向把梯度沿旋转方向回传；此为数学推断，源仅给出反向公式本身）。

**⑥ 结果写回**
- **类型转换**：结果由 float32 cast 回原始 dtype（float16/bfloat16）。
- **结果保存**：按块写回全局内存；若为 partial RoPE，则仅更新最后 `rope_dim` 维。

### Cube/Vector 核划分与精度

RoPE 全程为逐元素的乘加与重排（gather / cast / mul / add），无矩阵乘，据此应为 **Vector-only** 算子（源文档 RoPE 章节未显式标注 Cube/Vector 核划分，此为据计算特征的推断）；`T.tile.cast` / `T.tile.gather` 等原语映射到 AscendC 的 Vector 指令。关键精度处理是 **fp32 计算**：fp16/bf16 进 UB 后统一升 fp32 做 `x*cos + rotate(x)*sin`，避免低精度乘加的舍入误差，算完再降回原 dtype 写出。RoPE 前向是逐元素 FMA 而非归约累加，「FP32 累加」术语另指 MoE Gather-Reduce 与 RMSNorm 平方和。TileLang 的核间/核内同步、UB 内存分配由原语/编译器处理（见 framework 页）。

## op 绑定与替换路径

模型侧旋转变换在 TorchTitan-npu 由 `npu_rope` converter（`NpuRoPEConverter`，`@register_model_converter("npu_rope")`）绑定，其 `_ROPE_REPLACEMENTS` 替换 3 个上游 `common.rope` 函数（`apply_rotary_emb_cos_sin` / `apply_rotary_emb_complex` / `apply_rotary_emb_single_complex`），均以 `torch_npu.npu_rotary_mul` 为后端算子，按上游函数语义选择旋转模式：

```python
# cos_sin 路径：默认 half 模式（不传 rotary_mode）
xq_out = torch_npu.npu_rotary_mul(xq_f, cos, sin)
xk_out = torch_npu.npu_rotary_mul(xk_f, cos, sin)
# complex / single-complex 路径：传 rotary_mode="interleave"
y = torch_npu.npu_rotary_mul(x_f, cos, sin, rotary_mode="interleave")
```

TileLang-Ascend RoPE 与该 converter 语义等价（同样支持 interleave / half、partial、前向+反向），是「TileLang 算子替换」框架下可挂载的另一实现路径——算子替换接入方式见 torchtitan-npu `tilelang_ops` feature guide。converter 绑定细节（含 `rope` 模块须优先 import 的 patch 顺序）见 [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（『训练算子实现』→『1、Rotary Position Embedding』：概述 / 6 步算法流程 / `row_sin_cos` 索引公式 / interleave·half 重排 / 前向 `out=x*cos+rotate(x)*sin` 与反向 `dx=cos*dy+swap(sin_masked*dy)` / partial RoPE / fp32 计算）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseekv32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/f1c9603d914cff495c00b04e91b91f264dbb736d/docs/llm_pretrain/deepseekv32_pre_train_optimization.md)（guide 指向的 DeepSeek-V3.2 预训练优化文档，提供 RoPE 所在训练上下文）
- [`torchtitan-npu` · `docs/feature_guides/tilelang_ops.md`](https://gitcode.com/cann/torchtitan-npu/blob/dbfd45a557197064fa749708108415f2b48a0d13/docs/feature_guides/tilelang_ops.md)（guide 指向的 TileLang 算子替换 feature guide）

## Links

- [tilelang](../../../inference/concepts/frameworks/tilelang.md)（TileLang-Ascend 编程模型 / CodeGen / JIT；本算子的实现框架与 8 训练算子归属）
- [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)（`npu_rope` converter 绑定本旋转变换，默认走 `npu_rotary_mul`，可替换为本 TileLang 实现）
- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（所属预训练实践，RoPE 用于其 MLA/注意力路径）
- [tilelang-moe-token-permute](tilelang_moe_token_permute.md)（同批 TileLang-Ascend 训练算子）
- [tilelang-rmsnorm-swiglu](tilelang_rmsnorm_swiglu.md)（同批 TileLang-Ascend 训练算子）
- [mla-prolog](../../../inference/concepts/kernels/mla_prolog.md)（跨域：MLA 推理路径中 RoPE 应用于 q_pe/k_pe 分量，与本算子 partial RoPE 切分对应）
