---
type: Concept
title: 训练入图：torch.compile + Inductor + AutoFuse（Bypass Triton → AutoFuse）
description: 训练入图（torchtitan-npu）：torch.compile+Inductor 缓解 host-bound，Bypass Triton(npu_bypass_triton_codegen 清空 lowerings/decompositions 使 Aten fallback 原实现)；full-compile 仅 V3/V3.2/V4，其余模型须开 bypass。inductor_npu_ext Codegen 后端经 AutoFuse 从 Inductor IR 生 AscendC kernel。CompileConfig(enable,components model+loss)。坑：NameError _world 用 TORCHINDUCTOR_FX_GRAPH_CACHE=0+AUTOGRAD_CACHE=0 修(禁 FxGraphCache→每次启动全量重编译预热,稳态不受影响)，结构变更后清 /root/.cache 与 /tmp。未来对接 Ascend C AutoFuse/DualPipeV/Async TP。
tags:
- task.optimization
- topic.graph_execution
- topic.model_adaptation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: supporting
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/torch_compile.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
---

# 训练入图：torch.compile + AutoFuse（Ascend C 自动融合，DeepSeek-V4）

## Summary

DeepSeek-V4-Flash 续训练（CPT）的训练入图链路为：`torch.compile` 捕获静态图 → Inductor 后端做算子融合 → **AutoFuse（基于 Ascend C 的 Codegen 后端，替代 Triton 后端）** 把 Inductor IR 自动生成 NPU 亲和的融合 Kernel；在训练中带来 **31.8% 整网开箱收益**（AIV 算子融合 + Host-Bound 缓解）。

这是 [torchtitan](../frameworks/torchtitan.md) 训练入图小节里 DeepSeek-V3.2 阶段「Bypass Triton（先绕过自动融合）→ Future 对接 AutoFuse」承诺在 V4 的**正式落地**：V3.2 上 NPU Inductor 自动生成的 Triton 算子编译/执行均差，故只能 `npu_bypass_triton_codegen` 清空 lowerings/decompositions 让算子 fallback 原始实现、仅吃 host-bound 缓解；到 V4，`inductor_npu_ext` + AutoFuse 成熟，`compile.enable=true` 直接走自动融合，且 `entry.py` 对 `deepseek_v4` **禁止**再带 `npu_bypass_triton_codegen`（见下）。与推理侧已落地的 [autofuse](../../../inference/concepts/frameworks/autofuse.md) 对照：两者共用同一 CANN AutoFuse 组件（继承 Inductor、Ascend C Codegen），差异在训练侧入图的是含反向/重计算的整层 TransformerBlock、且 V4-Flash 以 Eager 模式执行编译图。

> 软件架构自顶向下：**TorchTitan**（PyTorch Native 框架、FSDP 开箱）→ **TorchTitan-NPU**（插件化昇腾适配）→ **TorchInductor**（继承社区 torch.compile 图捕获与融合）→ **AutoFuse**（面向昇腾 NPU 的 Ascend C Codegen & Schedule 后端，在 Inductor 基础上注入架构感知融合/优化/展开策略）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse.png" width="58%"></p>
<p align="center"><sub>图：AutoFuse 继承 Inductor 整体流程、以目标为 Ascend C 的 Schedule & Codegen 后端替代 Triton，将计算图自动映射为高效 NPU 算子代码（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·torch.compile + AutoFuse）</sub></p>

## 为什么 V4 需要自动融合：小算子组合成主流

随着 MoE 与多模态架构普及，**动态、细粒度的小算子组合**已成主流设计模式。典型如 DeepSeek 提出的 **mHC**：它把 HC 过程分解为 HcRes、HcPre、HcPost 三部分，分别通过双随机矩阵与 Sigmoid 门控系数保障数学性质，但实现上依赖大量细碎的 PyTorch 操作。

> 这类灵活结构在模型设计中日益普遍，若延续传统手写融合算子的方式，开发效率已难以匹配模型迭代速度，算子自动化融合能力由此成为刚需。

`torch.compile` 为此提供基础能力：通过捕获 FX 计算图把模型逻辑转为算子图表示，交由 Inductor 后端做算子融合与代码生成，Inductor 用**垂直与水平融合**把多个细碎操作合并为单一高效内核实现跨算子全局优化；TorchTitan 对 `torch.compile` 原生深度支持，可直接复用 PyTorch 编译生态。但 NPU 与 GPU 在内存架构与计算范式上存在本质差异，直接沿用 GPU 优化策略（Triton）难以释放 NPU 潜力——这正是 AutoFuse 接入 Ascend C Codegen 后端的动因。

## 入图链路在 torchtitan-npu 的落点

### 使能开关：`compile.enable` + `inductor_npu_ext`

V4-Flash 配置 toml 的 `[compile]` 节即开关，`components=["model","loss"]` 表示编译完整模型（而非只编 loss）：

```toml
[model]
name = "deepseek_v4"
flavor = "285B_debug_43_layers"
converters = ["npu_rms_norm", "npu_permute", "npu_gmm", "npu_rope", "deepseek_v4_sfa", "npu_mhc_pre"]
[parallelism]
tensor_parallel_degree = 1          # 不开 TP（纯 FSDP+EP，故无 TP 通信入关键路径）
expert_parallel_degree = 64         # EP（按 die 数变化，文档主线 EP128/FSDP128）
[compile]
enable = true
components = ["model", "loss"]      # 编译完整模型而非仅 loss
# torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml
```

`entry.py` 在启动时校验入图前置条件——这是 V4 与 V3.2 路线分叉的关键证据：开了 `compile.enable` 时，`deepseek_v3/v4/v32` 走 AutoFuse 路径，**必须**能 `import inductor_npu_ext`，且 V4 **不允许**再带 bypass converter；其余模型反而**必须**带 `npu_bypass_triton_codegen`：

```python
if config.compile.enable:
    if config.model.name in ("deepseek_v3", "deepseek_v4", "deepseek_v32"):
        ...
        try:
            import inductor_npu_ext        # 注册基于 AutoFuse 的 Inductor NPU Codegen 后端
        except Exception as e:
            raise RuntimeError(
                f"compile.enable is True for {config.model.name} model but inductor_npu_ext is not available. ...")
        if "npu_bypass_triton_codegen" in config.model.converters:
            raise RuntimeError(                 # V4 已落地 AutoFuse，禁止再 bypass
                f"{config.model.name} model with compile.enable=True should not use npu_bypass_triton_codegen. ...")
    else:
        if "npu_bypass_triton_codegen" not in config.model.converters:
            raise RuntimeError(                 # 其他模型尚无 AutoFuse，强制 bypass Triton
                f"{config.model.name} model with compile.enable=True requires npu_bypass_triton_codegen. ...")
# torchtitan_npu/entry.py
```

`inductor_npu_ext` 是 `Ascend/torchair` 仓的实验后端，借 [AutoFuse](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/900beta1/graph/graphguide/autofuse_1_0001.html) 自动融合能力从 Inductor IR 生成 Ascend C 融合 Kernel；从源码安装（`pip3 install -e experimental/_inductor_npu_ext/python/`），启动前另需 `export TORCHINDUCTOR_SIZE_ASSERTS=0`（[`docs/feature_guides/torch_compile.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/torch_compile.md)）。AutoFuse 亮点：**PyTorch 前端增加一行代码即可使能**；性能依赖 NPU 亲和算子生成（模板规约 Schedule + 硬件建模动态求解 Tiling + Ascend LoopIR Codegen）；当前覆盖 152 个 LoopIR 表达中的 46 个，未来逐步补齐。

### 逐 TransformerBlock 编译（`apply_compile`）

`apply_compile` 对每个 `TransformerBlock` 加 `torch.compile`（利用层结构重复使编译高效），但 MoE 层不能整块编译——`FSDP(GroupedExperts)` 会触发 graph break，故对 MoE 子模块逐个 wrap，并把不可编译/已是融合算子的部分跳过：

```python
def apply_compile(model, compile_config, ep_enabled):
    torch._dynamo.config.capture_scalar_outputs = True   # 避免 token-choice MoE 动态 shape 断图
    for layer_id, transformer_block in model.layers.named_children():
        if transformer_block.moe_enabled:
            ...
            for attr_name, submod in block.named_children():
                if attr_name in {"hc_pre"}:              # hc_pre 跳过（TileLang/自定义算子）
                    continue
                if isinstance(submod, moe_module.MoE):
                    for attr_name, submod in moe.named_children():
                        if attr_name == "experts":       # 跳过 experts（GroupedExperts 分组专家 GEMM）：含 FSDP(GroupedExperts) hooks，整块编译会让 AC fallback eager
                            continue
                        setattr(moe, attr_name, torch.compile(submod, backend=compile_config.backend, fullgraph=True))
                elif isinstance(submod, Attention):
                    for attr_name, submod in attention.named_children():
                        if attr_name == "inner_attention":   # inner_attention 是 NPU 融合算子（SAS/LI），不编译
                            continue
                        setattr(attention, attr_name, torch.compile(submod, backend=compile_config.backend, fullgraph=True))
                else:
                    setattr(block, attr_name, torch.compile(submod, backend=compile_config.backend, fullgraph=True))
        else:                                            # 非 MoE 层可整块编译
            transformer_block = torch.compile(transformer_block, backend=compile_config.backend, fullgraph=True)
        model.layers.register_module(layer_id, transformer_block)
# torchtitan_npu/models/deepseek_v4/infra/parallelize.py — apply_compile
```

跳过项与 V3.2 思路一致：`inner_attention`（DSA 稀疏注意力**前向**，已是 SAS / LI Ascend C 融合算子，见 [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md) / [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)）、`hc_pre`、以及 MoE 的 `experts`（`GroupedExperts` 分组专家 GEMM）三者绕过逐层编译——`experts` 之所以被 `_compile_children_except(submod, {"experts"}, ...)` 单独剔除，是因为它含 `FSDP(GroupedExperts)` hooks，整块 compile 会让 activation checkpointing 把整图 fallback 回 eager。注意真正的 token 分发逻辑（router / `reorderer` 按索引 scatter `routed_input = x_flat[token_indices_experts_sorted]`）发生在 `MoE.forward` 里、且其 child（gate/router 等）反而是被编译的；`experts` 接收的已经是 reorder 后的 `routed_input`，是分组专家计算本身而非 dispatch/combine。剩下大量 Vector 小算子（mHC 门控、RMSNorm、router/gate、逐元素链）交给 AutoFuse 融合。被剔除的 grouped GEMM 随后由 `_patch_grouped_mm_compile` 单独 `torch.compile`，并在 EP 场景用 `torch._dynamo.mark_dynamic(x, 0)` 标注动态 token 数。

### Eager 模式执行编译图

纯 FSDP+EP（TP=1）下单算子计算量本身较大，做算子融合后 Kernel Launch 开销占比极低，不存在静态图的收益空间；故采用动态图 Eager 模式执行编译后的算子图，既拿到融合收益，又无需处理动态 Shape 约束，更简洁灵活。

## 通用入图配方

上节 V4-Flash 是 AutoFuse **全流程编译**的范例；同一链路（Dynamo 成图 → Inductor 图优化/Codegen → `inductor_npu_ext` 后端借 AutoFuse 从 Inductor IR 生成 AscendC 融合 Kernel）可抽成复用配方落到其他模型/分支，关键约束是**全图编译白名单**与一个高频报错的修复。

### 全图编译白名单与 bypass converter

> torchtitan-npu 当前支持 `DeepSeek-V3、DeepSeek-V3.2、DeepSeek-V4` 模型的全流程编译。其他模型的 Codegen 仍处于待调试状态。

启用 `torch.compile` 时，**白名单之外的模型必须**在模型 `config_registry.py` 的 `ModelConvertersContainer.Config.converters` 列表里包含 `npu_bypass_triton_codegen`——它跳过 Inductor Codegen，仅保留 Dynamo / AOTAutograd / Inductor 图优化等前置流程（converter 本身见 [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md) / [model-custom-converter](../frameworks/model_custom_converter.md)）：

```python
model_converters = ModelConvertersContainer.Config(
    converters=[
        get_model_converter_config("npu_rms_norm"),
        # ... 其他 converter ...
        get_model_converter_config("npu_bypass_triton_codegen"),  # 非白名单模型必带
    ],
)
# config_registry.py
```

> 这与 `entry.py` 的校验互补：白名单模型（v3/v32/v4）开 `compile.enable` 时**禁带** bypass 并强制 `import inductor_npu_ext`，其余模型**强制带** bypass（见上节）。

`inductor_npu_ext` 从源码安装（`Ascend/torchair` 仓 `checkout 3c9418c2`，`pip3 install -e experimental/_inductor_npu_ext/python/`）。使能 compile 两种方式：①模型 `config_registry.py` 配 `CompileConfig(enable=True, components=["model", "loss"])`（编译完整模型而非只编 loss）；②命令行 `bash scripts/run_train.sh --compile.enable`，并 `export TORCHINDUCTOR_SIZE_ASSERTS=0`。

### `NameError: name '_world' is not defined` 修复

编译时若抛 `NameError: name '_world' is not defined`，需在训练前关闭 Inductor 的 FxGraph / AOTAutograd 缓存：

```bash
export TORCHINDUCTOR_FX_GRAPH_CACHE=0
export TORCHINDUCTOR_AUTOGRAD_CACHE=0
```

关闭后 Inductor 不再走 `FxGraphCache.load_with_key` 路径即可规避；代价是**每次启动重走完整编译**、一次性 warmup 增加，**稳态步长不受影响**。配合上节的「改结构后清缓存」（`rm -rf /root/.cache /tmp/* /tmp/.[!.]*`）一起使用——切分支 / 改代码 / 更新算子实现后旧编译产物可能导致编译失败或运行异常。

## AutoFuse 收益分析

使能 AutoFuse 后 DeepSeek-V4-Flash 整网吞吐收益 **31.8%**，拆解为两块：**AIV 算子融合** + **Host-Bound 缓解带来的 Free Time 减少**。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-gain.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 整网 31.8% 收益拆解——AIV 算子融合净收益 + Host Bound 缓解减少 Free Time（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

### AIV 收益：各类算子融合

| 融合后算子名称 | 数量 Count | 融合后总耗时 (s) | 融合前总耗时 (s) | 净收益 (s) | 优化核心 |
| --- | --- | --- | --- | --- | --- |
| `autofused_mul_sum` 系列 | 10,232 | 1.6 | 7.1 | 5.5 | 带宽优化：消除 Mul 结果写回内存再读回，直接片上完成规约 |
| 基础逐元素融合 (Mul/Add/Div) | ~20万个 | 7.8 | 12.8 | 5 | 访存收敛：合并大量独立乘/加/除，显著减少内存总访问次数 |
| `autofused_add_div_expand_mul_pow` | 1,584 | 1 | 2.6 | 1.6 | 指令加速：将极高延迟的独立 Pow 算子指令化，以计算掩盖访存延迟 |
| `BroadcastTo` 隐式化（聚合项） | ~3.3万个 | 0.3 | 2.5 | 2.2 | 隐式广播：通过 Stride 逻辑变换实现广播，消除物理内存拷贝 |
| `autofused_npu_dtype_cast` 系列 | 14,832 | 1.8 | 2.5 | 0.7 | 调度简化：吸收数万次类型转换，降低 CPU 下发 NPU 频率 |

三大核心收益来源：

- **消除"访存墙"（Memory Bound）**：把 12 个独立算子的"读-算-写"循环重构为 2 个高集成度融合内核，中间张量驻留片上缓存（SRAM/L1），规避频繁读写 HBM 的巨大带宽开销。
- **掩盖高耗时指令（Operator Hiding）**：编译器对 Pow/RealDiv 等高周期算子做指令级重排，计算压力被掩盖在矢量流水线中，实现非线性数学公式链的"近乎零成本"合并。
- **精简内核启动开销（Launch Overhead）**：大幅减少 Host-to-Device 握手次数，清理 MatMul 等重量级算子之间的"计算碎屑"，确保 NPU 核心持续高负载产出。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-example.png" width="60%"></p>
<p align="center"><sub>图：典型片段——12 个独立"读-算-写"算子被 AutoFuse 重构为 2 个高集成度融合内核，中间张量片上驻留（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

### Host-Bound（调度瓶颈）缓解

> 核心优化路径：将原本离散间隔执行的小算子，优化为融合算子的连续执行，降低了硬件空泡，保障 NPU 计算流水线连续性，大幅提升硬件利用率。

两条路径：**调度优化**——静态化分析 + Codegen Wrapper → 预编译执行流（取代动态 Dispatcher），降低 Host 延迟；**算子级优化**——算子融合 → 减少 Launch 次数 → 缓解 Host 侧指令下发压力。这与 V3.2 阶段 Inductor「Codegen Wrapper + 静态化分析绕过 PyTorch Dispatcher」的 host-bound 缓解机制同源（见 [torchtitan](../frameworks/torchtitan.md)），区别在 V4 同时叠加了真正的算子融合。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-hostbound.png" width="58%"></p>
<p align="center"><sub>图：离散间隔的小算子被融合为连续执行，硬件空泡减少、NPU 流水线连续性提升（Host-Bound 缓解）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

## 在整体优化中的占比

AutoFuse 是 V4-Flash 续训三条优化主线（极简并行、自动融合、定制算子）之一。整体吞吐从初始 **397 → 1100 tokens/p/s**（A3 64 卡、BF16、4K 序列 + MTP1），其中**定制融合算子贡献约 90%、AutoFuse 贡献约 30% 吞吐提升**。展望中明确「进一步扩大 AutoFuse 自动融合的覆盖范围以压缩计算时延」——当前 Profiling 显示 Vector 类算子占整网耗时近 40%，仍是融合空间所在。

## 入图前置与运维约束

入图三项承重前置（具体安装/启动命令见源仓 README 与 `docs/feature_guides/torch_compile.md`）：

- **后端**：须从源码装好 `inductor_npu_ext`（`Ascend/torchair` 仓的实验 Inductor NPU Codegen 后端）才能走 AutoFuse 自动融合，否则 `entry.py` 校验直接报错（见前文）。
- **环境变量**：启动前 `export TORCHINDUCTOR_SIZE_ASSERTS=0`，否则 Inductor 的 size assert 会在动态 token 形状下误报。
- **改结构清缓存重 compile**：`torch.compile` 会缓存编译结果，模型结构变化（改代码/切分支/更新算子）后旧缓存可能导致编译失败，需 `rm -rf /root/.cache /tmp/* /tmp/.[!.]*`（[`docs/feature_guides/torch_compile.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/torch_compile.md)）。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（『torch.compile + AutoFuse』分层架构 / mHC 小算子组合刚需 / Inductor 垂直水平融合 / Ascend C Codegen 后端；『AutoFuse 收益分析』31.8% 拆解表、AIV 三大收益来源、Host-Bound 缓解；Highlights 31.8% + 46/152 LoopIR；『性能结果』397→1100 TPS、AutoFuse 贡献约 30%）
- [`torchtitan_npu/entry.py`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/entry.py) — `compile.enable` 校验：`deepseek_v3/v4/v32` 强制 `import inductor_npu_ext` 且禁带 `npu_bypass_triton_codegen`，其余模型强制带 bypass（V4 落地 AutoFuse 的分叉点）
- [`torchtitan_npu/models/deepseek_v4/infra/parallelize.py`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/infra/parallelize.py) — `apply_compile` 逐 TransformerBlock `torch.compile(backend=..., fullgraph=True)`，跳过 `inner_attention`/`hc_pre`/`experts`，`capture_scalar_outputs=True`，EP 下 `_run_experts_grouped_mm` 配 `mark_dynamic`
- [`torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml) — `[compile] enable=true components=["model","loss"]`、`tensor_parallel_degree=1`、`expert_parallel_degree=64`（V4-Flash 4K/128die 配置）
- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/torch_compile.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/torch_compile.md)（@8f128cd）：全图编译白名单 `DeepSeek-V3/V3.2/V4`、非白名单模型 `config_registry.py` 必带 `npu_bypass_triton_codegen`；`inductor_npu_ext` 源码安装（torchair `checkout 3c9418c2`）、AutoFuse 从 Inductor IR 生成 AscendC Kernel、`CompileConfig(enable=True, components=["model","loss"])` / `--compile.enable` / `TORCHINDUCTOR_SIZE_ASSERTS=0`；`NameError: name '_world' is not defined` 修复（`TORCHINDUCTOR_FX_GRAPH_CACHE=0` + `TORCHINDUCTOR_AUTOGRAD_CACHE=0`，关闭 `FxGraphCache.load_with_key`，warmup 增加、稳态不变）；清缓存 `rm -rf /root/.cache /tmp/*`
- [`torchtitan_npu/converters/features/bypass_triton_codegen.py`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/converters/features/bypass_triton_codegen.py) — V3.2 路线的 `compile_bypass_fusion`（`lowerings.clear()/decompositions.clear()`），`SUPPORTED_MODELS={"deepseek_v32","llama3"}`（对照：V4 不再走此路）

## Links

- [torchtitan](../frameworks/torchtitan.md)（训练入图的承载框架；其「Bypass Triton → Future AutoFuse」承诺在 V4 落地，ModelConverter / Inductor / apply_compile 机制同源）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（本入图技术的承载实践：V4-Flash 64 卡 1100 TPS 续训，AutoFuse 贡献约 30%）
- [slig](../kernels/slig.md)（DSA 训练**反向**算子 SLIG；与 AutoFuse 自动融合并列——「手写定制算子」（含 inner_attention 正向 SAS/LI 与反向 SLIG/SASG）vs「编译器自动融合」两条路线）
- [torchtitan-5d-parallel](../parallelism/torchtitan_5d_parallel.md)（V4 纯 FSDP+EP、TP=1 是 Eager 执行编译图的前提；并行装配中 compile 处于 AC 之后、FSDP 之前）
- [autofuse](../../../inference/concepts/frameworks/autofuse.md)（跨域：推理侧已落地的同一 CANN AutoFuse 组件——继承 Inductor、Schedule 模板规约 + ATT 自动 Tiling + Ascend C Codegen；训练侧应用与对照）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：A3 64 卡集群，纯 FSDP+EP + AutoFuse 达 1100 TPS 的硬件底座）