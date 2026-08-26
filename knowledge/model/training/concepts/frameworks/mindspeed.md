---
type: Concept
title: MindSpeed（昇腾大模型训练加速框架 + 低精度训练）
description: MindSpeed（MindSpeed Core）是面向华为昇腾设备的大模型加速库，把大模型训练/推理任务高效迁移到昇腾平台并提供昇腾专有优化能力。DeepSeek-V3 的 HiF8 / MXFP8 低精度预训练实践（裁剪版 DeepSeek-v3，8 卡 Atlas A5 950DT，8K 序列）正是基于 MindSpeed + MindSpeed-LLM + Megatron-LM(core_v0.12.1) 这条栈跑通的——区别于 torchtitan（PyTorch 原生、DTensor / DeepSeek-V3.2 DSA 那条 recipe），MindSpeed 走的是 Megatron 风格 的训练栈，低精度由其内置的 Transformer Engine（TE）兼容模块承载。本页讲清这条栈的层次关系、TE 低精度训练流程（Fprop/Dgrad/Wgrad MatMul 量化、Delayed/Tensorwise/Blockwise/MX 四类 scaling、HiF8/MXFP8 支持矩阵）、以及 swap-optimizer 这一「自适应 Swap」特性的来源；安装/拉起命令忠实裁剪自 recipe README。 补充：MindSpeed 特性接入机制——features_manager + monkey-patch 注入(MindSpeedFeature 自描述特性、MindSpeedPatchesManager 两阶段打补丁、optimization_level 0/1/2 分级、ms-core⇄ms-llm 两层补丁框架)。
tags:
- task.implementation
- topic.architecture
- topic.reinforcement_learning
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
- a5
---

# MindSpeed（昇腾大模型训练加速框架 + 低精度训练）

## Summary

MindSpeed（**MindSpeed Core**）是面向华为昇腾设备的大模型加速库，把大模型训练/推理任务高效迁移到昇腾平台并提供昇腾专有优化能力。DeepSeek-V3 的 **HiF8 / MXFP8 低精度预训练实践**（裁剪版 DeepSeek-v3，8 卡 Atlas A5 950DT，8K 序列）正是基于 **MindSpeed + MindSpeed-LLM + Megatron-LM(core_v0.12.1)** 这条栈跑通的——区别于 [torchtitan](torchtitan.md)（PyTorch 原生、DTensor / DeepSeek-V3.2 DSA 那条 recipe），MindSpeed 走的是 **Megatron 风格** 的训练栈，低精度由其内置的 **Transformer Engine（TE）兼容模块**承载——对 Fprop/Dgrad/Wgrad MatMul 做量化，支持 Delayed / Tensorwise / Blockwise / MX 四类 scaling 与 HiF8 / MXFP8。[swap-optimizer](../techniques/swap_optimizer.md) 的「自适应 Swap」即源自 MindSpeed Core 的内存优化模块。

## 框架层次：MindSpeed Core / LLM / MM / RL

MindSpeed Core 是**亲和加速底座**，向上派生面向不同场景的套件，向下落到 PyTorch / MindSpore → CANN → 昇腾硬件。DeepSeek-V3 低精度 LLM 场景用的是 **MindSpeed LLM 套件**：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image8.png" width="72%"></p>
<p align="center"><sub>图：MindSpeed 框架分层——上层 LLM/MM/RL 套件，中间 MindSpeed Core 亲和加速模块（并行/内存/通信/计算优化），下接 PyTorch/MindSpore → CANN → 昇腾硬件（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·MindSpeed 低精度训练框架）</sub></p>

- **MindSpeed Core 亲和加速模块**：四类优化——**并行优化**（多维混合并行、自动并行搜索、高效流水排布）、**内存优化**（内存压缩算法、**自适应 Swap**、Gelu 重计算优化）、**通信优化**（通信隐藏、流量冲突管理、通算融合）、**计算优化**（高性能融合算子、昇腾亲和优化、脚本等价改写）。
- **MindSpeed LLM 套件**：100+ LLM 模型（稠密 Qwen/LLaMA、稀疏 DeepSeek 等）+ LLM 核心组件（数据预处理、全流程、偏好对齐）。DeepSeek-V3 低精度 recipe 即跑在此套件上。
- **MindSpeed MM / RL 套件**：分别覆盖 30+ 多模态模型与 LLM/MM/Agent 全场景 RL（RL 算法、Ray 流水调度、分离/共卡）。

> **内存优化**这一格里的「自适应 Swap」，正是 [swap-optimizer](../techniques/swap_optimizer.md) 的来源——torchtitan-npu 的 `SwapOptimizer` 实现派生自 MindSpeed `mindspeed/core/optimizer/swap_optimizer/swap_optimizer.py`（见该页 Evidence 的版权声明）。

## 与 Megatron-LM / MindSpeed-LLM 的关系

DeepSeek-V3 低精度 recipe 的训练栈由三层拼装（recipe README「源码准备」）：

- **Megatron-LM**：NVIDIA 上游分布式训练框架，提供 GPT/MoE 模型与 mcore（megatron core）训练循环骨架。本 recipe 锁定 **`core_v0.12.1`** 分支，并把其 `megatron` 目录**拷贝进 MindSpeed-LLM** 复用。
- **MindSpeed Core**：昇腾亲和加速库，以补丁/适配方式接管 Megatron 的并行、内存、通信、算子路径，让 Megatron 训练脚本无改动迁移到 NPU。
- **MindSpeed-LLM**：面向 LLM 场景的上层套件，承载 DeepSeek-V3 的模型定义、数据转换（`data_convert_deepseek3_pretrain.sh`）、权重转换（HF→mcore，`ckpt_convert_deepseek3_hf2mcore.sh`）与训练入口脚本。

组装时把 Megatron `core_v0.12.1` 的 `megatron` 目录拷进 MindSpeed-LLM 复用，三层各 `pip install -e`。DeepSeek-V3 低精度 recipe 用 2 层裁剪模型（1 moe + 1 dense），A5 超节点训练需注入 HCCL 拓扑文件，MXFP8 / HiF8 各有一个量化训练脚本。硬件为 [hif8](../quantization/hif8.md) 实验所用的 **Atlas A5 950DT-8P**（单卡 486 TFLOPS）。

## MindSpeed 特性接入机制（features_manager + patch_utils）

**MindSpeed 不 fork Megatron，而是在 `import megatron` 前后做运行时 monkey-patch**，把昇腾亲和实现替换进 Megatron 的函数/类——上节「以补丁/适配方式接管 Megatron」即指此机制。每个优化点被建模成一个 `MindSpeedFeature`，由 `MindSpeedFeaturesManager` 按开关与 `optimization_level` 决定启用，再由 `MindSpeedPatchesManager` 统一落补丁。

### MindSpeedFeature：一个特性的四件事

`mindspeed/features_manager/feature.py` 的 `MindSpeedFeature` 基类把「一个特性」抽象成自描述对象，构造时 `__init__(feature_name, optimization_level=2)`：`feature_name` 经 `lower().strip().replace('-', '_')` 归一为参数名（如 `swap-optimizer` → `swap_optimizer`），`default_patches = (optimization_level == 0)`。子类按需重写以下钩子，覆盖一个特性的全生命周期：

- **`register_args(parser)`**：注册该特性的 CLI 开关与参数（如 `SwapOptimizerFeature` 注册 `--swap-optimizer` / `--swap-optimizer-times`）。开关名与 `feature_name` 对齐，于是 `getattr(args, self.feature_name)` 即「该特性是否被命令行打开」。
- **`is_need_apply(args)`（基类已实现，是启用判据）**：`(self.optimization_level <= args.optimization_level and getattr(args, feature_name, None)) or self.default_patches`。即——要么「全局优化档位 ≥ 本特性档位 且 用户显式打开了开关」，要么本特性是 level-0 基座补丁（`default_patches`，无条件应用）。
- **`pre_validate_args` / `validate_args` / `post_validate_args`**：三段式参数校验。`pre_validate_args` 在 Megatron 自身 `validate_args` **之前**跑，用于临时改写参数绕过 Megatron 的校验（如临时把 `context_parallel_size` 置 1）；`post_validate_args` 在之后还原。基类另给 `incompatible_check(global_args, check_args)` / `dependency_check(...)` 两个工具做互斥/依赖断言（如 swap-optimizer 与 `reuse_fp32_param` 互斥）。
- **`pre_register_patches` / `register_patches(patch_manager, args)`**：声明该特性要打的补丁。`pre_register_patches` 在 `import megatron` 之前应用（用于必须早于 megatron 加载的替换），`register_patches` 在之后。补丁动作落到传入的 `patch_manager`，本身只「登记」不立即生效。

> 一个特性 = 参数注册（register_args）+ 启用判据（is_need_apply / optimization_level）+ 参数校验改写（*validate_args）+ 打补丁（register_patches）。后续每个 MindSpeed 并行/显存/通信/融合算子特性都按这套模板写一个 `*Feature` 类，互不耦合。

### MindSpeedPatchesManager：给 Megatron 函数打补丁

`mindspeed/patch_utils.py` 的 `MindSpeedPatchesManager` 是补丁注册表（`patches_info: Dict[str, Patch]`），**两阶段**生效：

1. **`register_patch(orig_func_name, new_func=None, force_patch=False, create_dummy=False)`** 只登记不生效。`orig_func_name` 是点路径全名（如 `'megatron.core.optimizer.distrib_optimizer.DistributedOptimizer'`）。三条关键语义：① `new_func` 名字以 `wrapper`/`decorator` 结尾 → 作为**装饰器叠加**（可重复叠多层，多个特性能各自包一层）；否则作为**整体替换**，`force_patch=False` 时同一目标不可二次替换（避免特性冲突）。② `create_dummy=True` 时若目标模块/函数不存在，造一个 dummy module 占位，保证 `import` 不炸（用于可选依赖如 TE 缺失场景）。③ `new_func=None` 配 dummy 表示「调用即报错」的占位。
2. **`apply_patches()`** 才真正生效：遍历每个 `Patch`，解析目标点路径定位原模块/原函数，叠完所有 wrapper 后用 `setattr` 把最终函数写回原模块**以及 `sys.modules` 中所有已引用该函数的模块**——这一步是 monkey-patch 的本体，保证已经 `from x import f` 拿到旧引用的模块也被刷新。`remove_patches()` 反向把原函数 restore 回去（RL repatch 依赖它）。

### features_manager：按档位编排全部特性

`mindspeed/features_manager/features_manager.py` 的 `MindSpeedFeaturesManager` 持有全局 `FEATURES_LIST`，把上面两者串成流水线：`register_features_args(parser)` 让每个特性注册参数 → `pre_validate_features_args` / `validate_features_args` / `post_validate_features_args` 三段校验 → **`apply_features_pre_patches(args)` / `apply_features_patches(args)`** 遍历 `FEATURES_LIST`，pre 与正式两阶段各自遍历 `FEATURES_LIST` 对 `is_need_apply(args)` 为真的特性调 `(pre_)register_patches` 登记后**各调一次 `MindSpeedPatchesManager.apply_patches()`** 落地（共两轮）：pre 轮（`apply_features_pre_patches`）让 `pre_register_patches` 的补丁在 `import megatron` 之前生效，正式轮（`apply_features_patches`）在之后。`FEATURES_LIST` 由 `__init__.py:create_features_list()` 按域（megatron_basic / context_parallel / fusions / moe / pipeline / optimizer / memory / …）分组装配；`--optimization-level`（`arguments.py`，`choices=[0,1,2]` 默认 2）是总闸：**0=适配 NPU 的最小补丁集，1=亲和优化（融合算子等），2=高级加速算法**，逐档累加启用更激进的特性（level-0 基座特性如 `MegatronBasicFeature(optimization_level=0)` 永远生效）。

### 入口与两层补丁框架（ms-core ⇄ ms-llm）

入口 `mindspeed/megatron_adaptor.py` 在 import 期即执行 `patch_features()`：取 `mindspeed_args` → `apply_features_pre_patches` → `apply_features_patches`；并通过 `arguments.py` 的 `parse_args_wrapper` / `validate_args_wrapper` 把特性的 `register_args` / 三段校验**织入 Megatron 自己的 `parse_args` / `validate_args`**。于是用户脚本只要 `import mindspeed.megatron_adaptor`，无需改 Megatron 源码，NPU 亲和实现就已注入。

**ms-core 与 ms-llm 是同机制的两层**：[mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM) 的 `mindspeed_llm/features_manager/__init__.py` 复用 ms-core 的 `MindSpeedFeature` / `MindSpeedFeaturesManager` / `MindSpeedPatchesManager` 基础设施，但**重新装配自己的 `FEATURES_LIST`**——既直接复用一批 ms-core 的 `*Feature`（如 `UnalignedLinearFeature` / `GroupedMatmulFeature` / `SwapOptimizerFeature` / `ReuseFP32Param`），又新增 LLM 专属特性（`TrainingDefaultFeature` / `MLAFeature` / `MoERouter` / `DPOFeature` / `LoraFeature` / `FinetuneFeature` / `CheckpointFeature` 等）。其入口 `mindspeed_llm/tasks/megatron_adaptor_v2.py` 的 `FeatureAdaptor.execute()` 先 `MindSpeedFeaturesManager.remove_patches()` 清掉 ms-core 默认补丁，再用 ms-llm 的参数与特性列表重打——即**上层套件用「同一打补丁机制 + 自己的特性集」覆盖底座**。这也是 [megatron-bridge](megatron_bridge.md) 等外部框架经此机制接入、以及 [mindspeed-rl](mindspeed_rl.md) / [mindspeed-mm](mindspeed_mm.md) 各自定制特性集的统一底座。

> RL 场景的「全共卡分时复用」正是建立在 `remove_patches` + 重打之上：`megatron_adaptor.repatch(args)`（及 ms-llm `megatron_adaptor_v2.py` 的**模块级 `repatch(config)` 函数**，非 `FeatureAdaptor` 类方法）先卸载现有补丁、改写参数、再 `apply_*_patches` 重打，让同一组卡在「训练态」与其它态间切换 MindSpeed 的特性集（见 §在 RL 训练中的角色）。

## TE 兼容模块与低精度训练流程

MindSpeed 的低精度训练能力由内置的 **Transformer Engine（TE）兼容模块**承载。TE 原是面向 Transformer、支持 Hopper GPU FP8 的加速库；MindSpeed 的 TE 模块在**接口与能力上与官方 TE 兼容**，让第三方框架无缝迁移、在昇腾 NPU 上跑高效 LLM 训练/推理。

MindSpeed 低精度训练流程的核心在于，将前向传播（Fprop）、激活反向传播（Dgrad）和权重反向传播（Wgrad）过程中的通用矩阵乘法运算量化为 FP8 / HiF8 精度执行。整体训练流程仍基于 BF16 / FP16 的 AMP 混合精度模式，但在特定计算算子中，尤其是 Linear 层中的矩阵乘法运算（涵盖 Fprop、Dgrad 和 Wgrad），采用 FP8 / HiF8 精度路径执行。

也就是说：**只把 Linear 层的三段 MatMul（Fprop/Dgrad/Wgrad）下沉到 FP8/HiF8 路径**，Softmax / LayerNorm / Loss 等数值敏感算子仍走高精度（与 BF16 AMP 一致），Optimizer 维护 FP32/BF16 Master Weights 保证更新精度——这与 [hif8](../quantization/hif8.md) 实验「仅量化 MM / GMM」一致。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image9.png" width="78%"></p>
<p align="center"><sub>图：TE 量化代码模块——模型 Linear 层（TERowParallelLinear/TEColumnParallelLinear）/ 量化粒度 recipe / Tensor 类三大块，FP8GlobalStateManager 单例维护全局 FP8 状态（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·MindSpeed 低精度训练框架）</sub></p>

模块职责：TERowParallelLinear 和 TEColumnParallelLinear 对应 Linear 层实现，其核心是将 Fprop、Dgrad 和 Wgrad 中的 MatMul 运算替换为 FP8 / HiF8 低精度路径。FP8GlobalStateManager 是一个单例对象，用于维护全局 FP8 状态以及各 TE Module 的运行信息。各 Recipe 类负责执行不同的量化策略，并通过对应的 Tensor 类管理 Scale 与数据张量。

即三层分工：`TE*ParallelLinear`（行/列并行 Linear，对接 Megatron 的 TP）承载 MatMul 量化路径 → **Recipe 类**实现不同 scaling 策略 → **Tensor 类**管理每张量的 Scale 与低精度数据，`FP8GlobalStateManager` 单例统揽全局 FP8 运行状态。

## 四类 Scaling 策略与 HiF8/MXFP8 支持矩阵

高精度（FP32/BF16）→ 低精度（FP8）量化的核心是缩放，文档列出 TE 模块支持的四类策略：

- **Delayed Scaling**：用**历史 Amax** 算 Scale，再量化 Tensor——把求 Amax 与下游 MatMul 解耦，最能发挥 8-bit 性能（见下图）。
- **Tensorwise Scaling**：在线计算 Amax 实时缩放（即 Current Scaling 的 per-tensor 形态），与下游计算串行。
- **Blockwise Scaling**：对 Tensor 分块、逐块算 Amax 并 scaling。
- **MX Scaling**：块级共享 Scale + 低位宽元素组合成 MX 块，动态量化（[hif8](../quantization/hif8.md) 中 MXFP8 走此路）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image7.png" width="78%"></p>
<p align="center"><sub>图：Delayed Scaling——以 interval=K iterations 为周期更新 Amax_history_buffer，用上一周期的 Scale_{i-1} 量化当前 iteration 的输入 X，N_guard 为防上溢保护参数（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 低精度优化文档</a>·缩放方案）</sub></p>

HiF8 因动态范围大（[-22,15] 共 38 个指数，接近 FP16），**可走 Per-Tensor + Delayed Scaling 长周期（interval=10 steps）**仍稳定；FP8/MXFP8 动态范围小，往往要细粒度 Per-Block。当前支持的格式 × 算子组合：

| 数据格式 | 量化粒度 | MatMul | Grouped MatMul | TP-MC2 | MatMul Add | Grouped MatMul Add |
| - | - | - | - | - | - | - |
| FP8 | Delayed | ✅ | Tensorwise 路径 | ❌ | ❌ | ❌ |
| FP8 | Tensorwise | ✅ | ✅ | ❌ | ❌ | ❌ |
| FP8 | Blockwise | ✅ | BF16 回退 | ❌ | ❌ | ❌ |
| FP8 | MXFP8 | ✅ | ✅ | ✅ | ✅ | ✅ |
| HiF8 | Delayed | ✅ | Tensorwise 路径 | ❌ | ❌ | ❌ |
| HiF8 | Tensorwise | ✅ | ✅ | ❌ | ❌ | ❌ |

> 注：「Tensorwise 路径」= 该算子在此组合下采用 Tensorwise 量化执行；「BF16 回退」= 回退至 BF16 精度路径；「TP-MC2」= 通信与计算融合算子（仅 MXFP8 一行打通 TP-MC2 / MatMul Add / GMM Add 全列）。

可见 **MXFP8 是唯一打通 TP-MC2 + MatMul Add + Grouped MatMul Add 全列的组合**；HiF8 当前只覆盖 MatMul/GMM（Delayed 的 GMM 走 Tensorwise 路径），与「仅量化 MM/GMM 主干算子」的实验范围吻合。

## 在 DeepSeek-V3 低精度实践中的角色

MindSpeed 在 [deepseek-v3-low-precision-pretrain](../../guides/recipes/deepseek_v3_low_precision_pretrain.md) 里既是训练栈也是低精度引擎：HiF8 实验取 **Per-Tensor + Delayed Scaling（interval=10 steps）**、仅量化 MM/GMM，相对 BF16 端到端提速 **29.5%**；MXFP8(E4M3) 取 Per-Block 细粒度，相对 BF16 提速 **14.05%**；两者损失曲线与 Gradient Norm 均与 BF16 基本对齐。Master Weights 保持 FP32/BF16。这一整套「TE Linear MatMul 量化 + Delayed Scaling」即由本框架的 TE 兼容模块落地。

## 在 RL 训练中的角色

除低精度预训练外，MindSpeed 也是 RL 后训练的**训练后端**：[verl](verl.md) 经 `MegatronWorker` repatch 用 MindSpeed / MindSpeed-LLM 承载 actor / reference 的**训练态**计算（与 rollout 推理后端 [vllm-ascend](vllm_ascend.md) 在同一组卡上**全共卡分时复用**）；其 **MindSpeed-RL** 提供的 `onload` / `init_cache` 等接口承载 RL [train-rollout-switch](../techniques/train_rollout_switch.md) 的 offload（训练后权重保留、`init_cache` 后置降峰值）。[deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 即复用 MindSpeed 的内存/通信/计算优化（actor/ref TP4EP8PP8）。这与 RL 套件（§框架层次）的 LLM/MM/Agent 全场景 RL 能力一脉相承。

## Evidence

- [mindspeed](https://gitcode.com/ascend/MindSpeed) — 上游代码仓。特性接入机制（ms-core，pin `1432cb09`）：
  - [`mindspeed/features_manager/feature.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/feature.py) — `MindSpeedFeature` 基类：`__init__(feature_name, optimization_level)` / `is_need_apply` / `register_args` / `pre_validate_args`·`validate_args`·`post_validate_args` / `pre_register_patches`·`register_patches` / `incompatible_check`·`dependency_check`
  - [`mindspeed/features_manager/features_manager.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/features_manager.py) — `MindSpeedFeaturesManager`：`FEATURES_LIST` / `apply_features_pre_patches`·`apply_features_patches`（按 `is_need_apply` 过滤）/ `register_features_args` / 三段 `*_validate_features_args` / `remove_patches`
  - [`mindspeed/features_manager/__init__.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/__init__.py) — `create_features_list()` 按域装配（megatron_basic / context_parallel / fusions / moe / pipeline / optimizer / memory …）
  - [`mindspeed/patch_utils.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/patch_utils.py) — `MindSpeedPatchesManager.register_patch`（`wrapper`/`decorator` 后缀叠加 vs 整体替换、`force_patch`、`create_dummy`）/ `apply_patches`（`setattr` 落补丁到原模块 + `sys.modules`）/ `remove_patches`；`Patch` 类
  - [`mindspeed/megatron_adaptor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/megatron_adaptor.py) — 入口 `patch_features()`（pre/正式两阶段应用）+ `repatch(args)`（remove→改参→重打，RL 共卡分时复用依赖）
  - [`mindspeed/arguments.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/arguments.py) — `--optimization-level`（`choices=[0,1,2]` 默认 2：0 最小 NPU 适配 / 1 亲和优化 / 2 高级加速）；`parse_args_wrapper`·`validate_args_wrapper` 把特性参数与校验织入 Megatron
- [mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM) — 上层套件，同机制第二层（pin `183e02c2`）：
  - [`mindspeed_llm/features_manager/__init__.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/features_manager/__init__.py) — 复用 ms-core `*Feature` + 新增 LLM 专属特性（`TrainingDefaultFeature` / `MLAFeature` / `MoERouter` / `DPOFeature` / `LoraFeature` / `FinetuneFeature` / `CheckpointFeature`），`create_features_list()` 重装 `FEATURES_LIST`
  - [`mindspeed_llm/tasks/megatron_adaptor_v2.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/megatron_adaptor_v2.py) — `FeatureAdaptor.execute()`：`remove_patches()` 清 ms-core 默认补丁 → 用 ms-llm 参数与特性集重打；`repatch(config)` 同理

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md)（第四章「低精度训练框架」4.1 MindSpeed：框架分层图、TE 兼容模块、Fprop/Dgrad/Wgrad MatMul 量化流程、四类 scaling、支持矩阵表 5；第三章 3.2 缩放方案 Delayed Scaling）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_pretrain/DeepSeekV3/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/DeepSeekV3/README.md)（MindSpeed + MindSpeed-LLM + Megatron-LM(core_v0.12.1) 安装组装、数据/权重转换脚本、`run_pretrain_dsk3_A5_8P_{hif8,mxfp8}.sh` 拉起命令、PyTorch 2.7.1 + torch_npu 环境）
- 上游仓：MindSpeed `gitcode.com/Ascend/MindSpeed @ 1432cb09`、MindSpeed-LLM `gitcode.com/Ascend/MindSpeed-LLM @ 183e02c2`、Megatron-LM `github.com/NVIDIA/Megatron-LM @ core_v0.12.1`

## Links

- [deepseek-v3-low-precision-pretrain](../../guides/recipes/deepseek_v3_low_precision_pretrain.md)（承载实践：MindSpeed 栈上的 HiF8/MXFP8 8 卡 A5 预训练，提速 29.5%/14.05%）
- [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)（承载实践：DeepSeek-R1 RL 训练侧经 MindSpeed repatch 复用其内存/通信/计算优化，actor/ref TP4EP8PP8）
- [hif8](../quantization/hif8.md)（本框架 TE 模块落地的 8-bit 格式：Per-Tensor + Delayed Scaling）
- [swap-optimizer](../techniques/swap_optimizer.md)（MindSpeed「自适应 Swap」内存优化的来源；torchtitan-npu `SwapOptimizer` 派生自此）
- [torchtitan](torchtitan.md)（平行训练框架对照：PyTorch 原生 DTensor 栈 vs MindSpeed 的 Megatron 栈；TorchTitan 低精度走 TorchAO MXFP8，MindSpeed 走 TE）
- [mxfp8-a8w8](../../../inference/concepts/quantization/mxfp8_a8w8.md)（跨域：推理侧 MXFP8 块级量化对照，本框架训练侧 MXFP8 是唯一打通 TP-MC2 全列的组合）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（Qwen3 235B RL 训练后端(HDP)）
- [qwen3-sft](../../guides/recipes/qwen3_sft.md)（Qwen3-1.7B SFT 用 MindSpeed-LLM + Megatron mcore）
- [virtual-optimizer](../techniques/virtual_optimizer.md)（torchtitan-npu Virtual Optimizer 派生自 MindSpeed VirtualOptimizer）
- [megatron-bridge](megatron_bridge.md)（外部框架经 MindSpeed 特性接入机制 monkey-patch 接入 Megatron 训练）
- [mindspeed-rl](mindspeed_rl.md)（RL 套件：复用同一 features_manager/patch_utils 底座 + 自己的特性集；`remove_patches`+repatch 支撑共卡分时复用）
- [mindspeed-mm](mindspeed_mm.md)（多模态套件：同机制第二层，装配 MM 专属特性集）
- [tensor-parallel-2d](../parallelism/tensor_parallel_2d.md)（承载特性：TP-2D 实现于 `mindspeed/core/tensor_parallel/tp_2d/`，经 features_manager 的 `TP2dFeature` 注册启用）
- [context-parallel-train](../parallelism/context_parallel_train.md)（承载的训练侧上下文并行家族：Ulysses / Ring / Hybrid / Unaligned CP，由 `--context-parallel-algo` 分派）
- [dualpipev](../parallelism/dualpipev.md)（承载的 V 形双向流水调度：一卡同载前反向 batch 互相掩盖 EP 通信）
- [pipeline-parallel-advanced](../parallelism/pipeline_parallel_advanced.md)（承载的高级流水并行能力集：VPP / Ripipe / 多参数 / Unaligned PP / 变长序列 / PP Layout）
- [hetero-parallel](../parallelism/hetero_parallel.md)（MindSpeed-MM 多模态异构并行：分组并行 + 动态 DP-CP）
- [fsdp](../parallelism/fsdp.md)（自研 custom-fsdp / torch-FSDP2 适配 / ND 引擎，FSDP2 概念主页）
- [recomputation](../techniques/recomputation.md)（承载的内存特性：激活函数/Norm/按 PP rank 重计算经 features_manager 注册、patch megatron 的 `MLP.forward`/`TransformerLayer.forward`/`_checkpointed_forward`）
- [chunk-loss](../techniques/chunk_loss.md)（承载的内存特性：分块 LM-Head + 损失，MindSpeed-LLM `ChunkLossFeature` 注册 `--loss-compute-mode chunk` / MindSpeed-MM 经 `loss_cfg` 启用，压末端 logits 激活峰值）
- [swap-attention](../techniques/swap_attention.md)（承载的内存特性：激活换出 Host + SmartSwap + 自适应内存，经 features_manager 注册）
- [optimizer-memory](../techniques/optimizer_memory.md)（承载的优化器显存特性：reuse-fp32-param / 低精度优化器 / LayerZeRO）
- [mm-activation-memory](../techniques/mm_activation_memory.md)（MindSpeed-MM 激活显存：Chunk-MBS + 异步激活 offload）
- [muon-optimizer](../techniques/muon_optimizer.md)（承载的 Megatron 栈 Muon 优化器实现）
- [moe-load-balance](../techniques/moe_load_balance.md)（承载的 MoE 负载均衡特性：features_manager/moe 下 `balanced_moe` 复制热专家 / `experts_placement` 物理迁移 / `moe_fix_router` 路由覆盖三套）
- [mc2](../techniques/mc2.md)（承载的通算融合特性：`MC2Feature` / `MoEAlltoAllMC2Feature` 注册 `--use-ascend-mc2` / `--moe-alltoall-mc2`，patch Column/RowParallelLinear 与 MoELayer 用昇腾融合算子掩盖 TP/EP 通信）
- [coc](../techniques/coc.md)（承载的 TP 通信掩盖：CoC 计算通信重叠）
- [moe-comm-overlap](../techniques/moe_comm_overlap.md)（承载的 MoE 通信掩盖：dispatch 异步 + 层内 overlap + 跨 microbatch 前反向掩盖）
- [moe-training-optim](../techniques/moe_training_optim.md)（承载的 MoE 训练优化：TP-Extend-EP / Zero-Memory / GMM / Shared-Experts）
- [ttp-high-availability](../techniques/ttp_high_availability.md)（承载的 verl RL 高可用容错：故障检测 + 副本 dump 恢复）
- [auto-settings](../techniques/auto_settings.md)（承载的自动调参：profiling 搜索并行/重计算/内存配置）
- [peft-lora](../techniques/peft_lora.md)（承载的 PEFT 微调：MindSpeed-LLM LoRA/CC-LoRA/QLoRA/LU-LoRA/LoRA-MoE）
- [data-packing-varlen](../techniques/data_packing_varlen.md)（承载的训练数据效率：EOD Reset + 变长 FA + 多样本 Packing）
- [qat-train](../techniques/qat_train.md)（承载的量化感知训练：qat_quant_engine 伪量化）
- [mla](../../../inference/concepts/modules/mla.md)（跨域：MLA 概念主页，含 MindSpeed 训练侧 MLA 小节——LinearNoTP 下投影 / --enable-mla-absorb / MLAFeature 注册）
