---
type: Concept
title: torchtitan-npu 融合算子与组件替换入口
description: 以当前 override 与 ops 机制说明 RMSNorm、RoPE、MoE dispatch/SwiGLU、DSA/SMLA 和 mHC 的启用入口及配置、布局和反向边界。
tags:
- task.implementation
- topic.architecture
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/fused_ops.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/README.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/rms_norm.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/rope.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/common/token_dispatcher.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- agnostic
---

# torchtitan-npu 融合算子与组件替换入口

## 接入关系

当前融合算子通过 `override.imports` 显式替换可配置组件，由 `ops/` 或已有 CANN/torch_npu 接口执行设备计算。完整覆盖组件时替换 Module；只覆盖局部计算时重写对应方法并保留其余上游逻辑。旧 `get_model_converter_config("npu_gmm")` / `npu_permute` / `npu_rope` 注册列表不再是当前启用方式。

`torch.library.custom_op` 是需要进入 `torch.compile` 时使用的 schema、Fake 和 Autograd 兼容封装，不会代替配置级组件选择，也不表示所有后端与形状都已支持。

## 公共组件入口

以下条目均以 `torchtitan_npu.override.common.` 为前缀：

| 入口 | 被替换对象与作用 |
| --- | --- |
| `rms_norm.asc` | `RMSNorm.Config`，调用 `torch_npu.npu_rms_norm`。 |
| `rope.workaround` | 精确匹配 `ComplexRoPE.Config`，用预展开 cos/sin 与 PyTorch 小算子计算。 |
| `rope.asc_complex` | 精确匹配 ComplexRoPE，使用 interleave 模式的 `npu_rotary_mul`。 |
| `rope.asc_cossin` | 匹配 CosSinRoPE，使用 half 模式的 `npu_rotary_mul`。 |
| `rope.asc_partial` | 精确匹配 split-aware partial-RoPE 配置，调用 CANN 融合原地旋转。 |
| `token_dispatcher.asc` | 在 AllToAllTokenDispatcher 的部分 dispatch/combine 逻辑中组合 permute、reroute 和 unpermute。 |
| `token_dispatcher.asc_deepep` | 匹配 DeepEPTokenDispatcher，通过 `cann_ops_transformer.ElasticBuffer` 处理训练 dispatch/combine；当前要求 EP>1。 |
| `swiglu_group.asc` | 在 routed experts 中融合 gate/up 后的 SwiGLU 与可选路由分数乘法。 |
| `swiglu_group.asc_shared_experts` | 在 shared experts 的 FeedForward 中融合 SwiGLU。 |

同一节点不能同时选择两个 RoPE variant。来源说明 `AscComplexRoPE` / `AscCosSinRoPE` 的同一 batch 各行需共享位置布局，不能据融合接口存在推导任意逐文档位置都受支持。

### RMSNorm 与 RoPE 的当前实现

`AscRMSNorm.forward` 直接调用 `npu_rms_norm(x, weight, eps)[0]`。`elementwise_affine=False` 时使用非持久化单位 scale buffer；初始化 buffer 时会把它放到当前 NPU，避免 CPU offload 后输入在设备、scale 在 Host 的不一致。

RoPE variant 的缓存和旋转布局必须与目标组件匹配。`rope.asc_partial` 的 CANN 依赖在首次计算时惰性加载，不能因只导入模块成功就认为设备算子包齐全。

### MoE 重排与专家计算

`token_dispatcher.asc` 在 AllToAll dispatcher 中做局部布局变换：`npu_moe_token_permute` 直接调用 torch_npu，unpermute 和 re-routing 在 `ops/ascendc/` 中提供编译、Fake 与 Autograd 包装。路由选择、通信、rank-major/local-expert-major 布局和最终恢复必须按 dispatcher 契约配套，不能把两次不同布局的 permute 视为同一次计算。

SwiGLU override 只覆盖 FFN 的中间激活桥接，前后分组矩阵乘及 token dispatch 继续使用现有路径。routed 与 shared expert 是不同配置节点，因此可以分别选择实现；低精度转换也可能先安装兼容的专家配置，须核对最终类型而不是重复启用旧的 GMM converter 名称。

## 模型专属注意力与 mHC

| 模型入口前缀 | 关键选择与边界 |
| --- | --- |
| `torchtitan_npu.override.deepseek_v3_2.` | `sparse_attn.asc` 接入 DSA，并把嵌套 indexer loss 配置派生为 Ascend 实现。 |
| `torchtitan_npu.override.deepseek_v4.` | `sparse_attn.asc` 与 `lightning_indexer.asc` / `.pypto` 分别承担 attention 与 indexer；训练 indexer 需要匹配的 teacher/consumer 两侧。 |
| `torchtitan_npu.override.deepseek_v4_1.` | `sparse_attn.asc` 与 `lightning_indexer.asc` 必须同时请求，配置阶段检查配对。 |
| `torchtitan_npu.override.deepseek_v4.mhc.` | pre/post/head 按 AscendC、Triton、TileLang variant 选择，同一配置节点只能有一个 replacement。 |

TND metadata 由被替换的 attention backend 的 `Config.build_attention_metadata` 构建，每个 microbatch、每个几何一份，同几何层共享。当前没有独立 metadata override 入口；普通模型 metadata 与 vendor metadata 必须保持包装关系。CP 时需按 rank-local frames 重建后端记录，不能复用完整全局布局直接调用内核。

V4/V4.1 的 teacher 边在 attention 反向与 Lightning Indexer 反向之间传递；只接入一侧或把其他含义的梯度写入该边会破坏训练语义。具体字段与后端限制见[SLIG](../kernels/slig.md)、[SMLA](../kernels/smla.md)、[SFAG](../kernels/sfag.md)。

## 验证与失效边界

先核对 override 日志及最终配置类型，再逐级验证 kernel、组件与整网：schema/Fake/Autograd、前后向数值、输入和参数梯度、DTensor sharding、CP metadata 和 checkpoint。融合收益取决于调用占比、形状、通信与布局变换，不能把某次单算子加速直接作为整网收益。

当前训练实践文档保留的 DeepSeek-V3.2 来源测量见[预训练实践](../../guides/recipes/deepseek_v32_pretrain.md)，不把该测量概括为本页所有当前 variant 的收益。本仓未执行 NPU 训练或性能复测。

## 相关入口

- [框架与启动](torchtitan.md)
- [配置转换及 override 冲突](model_custom_converter.md)
- [5D 并行](../parallelism/torchtitan_5d_parallel.md)
- [mHC](../kernels/mhc_train.md)
- [TileLang RoPE](../kernels/tilelang_rope.md)
- [低精度训练](../quantization/hif8.md)
