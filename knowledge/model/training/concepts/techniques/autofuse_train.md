---
type: Concept
title: 训练入图：torch.compile + Inductor + AutoFuse（Bypass Triton → AutoFuse）
description: 当前训练 AutoFuse：两级后端、torch_npu 内置 AscendC、逐 Block 编译、AC 副作用、缓存隔离与来源报告的 A3 收益边界。
tags:
- task.optimization
- topic.graph_execution
- topic.model_adaptation
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/torch_compile.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- a3
---

# 训练 AutoFuse 与 AscendC 编译

## Summary

标准 TorchTitan 路径通过 TorchDynamo、AOTAutograd、Inductor 捕获和编译训练图，再用 `torch_npu` 内置 AscendC Codegen 接入 CANN AutoFuse。普通 ATen 图由编译器融合，完整组件可用 override 替换；GraphTrainer 的整步图捕获是独立路径。

## 启用与配置

```bash
TORCHINDUCTOR_NPU_BACKEND=ascendc bash scripts/run_train.sh \
  --compile.enable --compile.components model loss --compile.backend inductor \
  <训练参数>
```

`compile.enable` 默认 False，`components` 默认 model/loss，`backend` 默认 inductor，Async TP 默认关闭。只设置 backend 不会开启编译；通用启动器只透传参数。Flash 示例会默认开启 model 编译，loss 需明确选择。

两级后端必须同时正确：`compile.backend=inductor` 选择 Dynamo backend，`TORCHINDUCTOR_NPU_BACKEND=ascendc` 选择其 NPU Codegen，环境变量须在 `import torch` 前设置。当前单机和多机 launcher 都以未设置时默认 ascendc 的方式导出该变量；所有节点仍须保证环境一致。compile 指南中“多机不补默认值”的描述与当前脚本不一致，此处按实际脚本说明。

配套后端位于 `torch_npu/_inductor/ascendc`；当前无需独立安装旧 `inductor_npu_ext`，也不使用旧 bypass 白名单。软件版本需按当前安装文档与 requirements 配套。

## 图边界与正确性

- 标准路径逐 TransformerBlock 使用 `fullgraph=True`，并非编译整个 Trainer。Block 内 Dynamo 无法捕获的行为会报错；已捕获图内的 Inductor fallback/extern kernel 则仍可能存在。训练跑通不能证明所有区域均已融合。
- 通常先做 override、TP/EP、Activation Checkpointing，再逐 Block compile，最后 FSDP。model 与 loss 分别选择；Async TP 还要求启用 compile、包含 model 和有效 TP mesh。
- AC 下启用 `skip_fwd_side_effects_in_bwd_under_checkpoint`，正确性不能依赖反向重算时重新执行 Python mutation。状态与缓存需同时审计 eager、AC 和 compiled forward。
- `capture_scalar_outputs` 不等于任意动态 shape 都支持。packed layout、stride、数据相关控制流、路由 token 数仍受 guard 与后端约束。
- 训练 custom op 需要准确 schema、Fake/Meta、Autograd、mutation 与 alias 契约；`torch.fx.wrap` 不会自动提供这些能力。可用 `aot_eager` 先检查捕获与反向，但它不能证明整块 AscendC AutoFuse 生效。

## 初始化、缓存与观测

包初始化按 patches、config、extensions、ops 顺序安装适配。当前 compile 适配位于 extensions；不要照旧 entry.py 校验器安装过期后端或关闭 bypass。

第一次执行含捕获和编译，性能比较须在编译预热后采样。默认融合核缓存为 `/tmp/.npu_kernels_<user>`，可用 `TORCHINDUCTOR_NPU_EXT_CACHE_DIR` 隔离；目录必须支持文件锁。改变软件、SoC、图或关键 shape 后，隔离或定向失效缓存。

`FORCE_DISABLE_CACHES`、layout check、同步 launch、debug/autotune 等调试选项会改变执行行为，不能直接作为正式性能配置。PGO 的初始 profiling 阶段也应与外部 profiling 分开。

## AutoFuse 收益分析

Recipes 文档报告的 DeepSeek-V4-Flash A3 64 卡、BF16、4K、MTP1 优化案例中，AutoFuse 整网吞吐收益 **31.8%**，拆解为两块：**AIV 算子融合** + **Host-Bound 缓解带来的 Free Time 减少**。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-gain.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 整网 31.8% 收益拆解——AIV 算子融合净收益 + Host Bound 缓解减少 Free Time（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

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

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-example.png" width="60%"></p>
<p align="center"><sub>图：典型片段——12 个独立"读-算-写"算子被 AutoFuse 重构为 2 个高集成度融合内核，中间张量片上驻留（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

### Host-Bound（调度瓶颈）缓解

> 核心优化路径：将原本离散间隔执行的小算子，优化为融合算子的连续执行，降低了硬件空泡，保障 NPU 计算流水线连续性，大幅提升硬件利用率。

两条路径：**调度优化**——静态化分析 + Codegen Wrapper → 预编译执行流（取代动态 Dispatcher），降低 Host 延迟；**算子级优化**——算子融合 → 减少 Launch 次数 → 缓解 Host 侧指令下发压力。这与 V3.2 阶段 Inductor「Codegen Wrapper + 静态化分析绕过 PyTorch Dispatcher」的 host-bound 缓解机制同源（见 [torchtitan](../frameworks/torchtitan.md)），区别在 V4 同时叠加了真正的算子融合。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-hostbound.png" width="58%"></p>
<p align="center"><sub>图：离散间隔的小算子被融合为连续执行，硬件空泡减少、NPU 流水线连续性提升（Host-Bound 缓解）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

## 在整体优化中的占比

AutoFuse 是 V4-Flash 续训三条优化主线（极简并行、自动融合、定制算子）之一。整体吞吐从初始 **397 → 1100 tokens/p/s**（A3 64 卡、BF16、4K 序列 + MTP1），其中**定制融合算子贡献约 90%、AutoFuse 贡献约 30% 吞吐提升**。展望中明确「进一步扩大 AutoFuse 自动融合的覆盖范围以压缩计算时延」——当前 Profiling 显示 Vector 类算子占整网耗时近 40%，仍是融合空间所在。


上述数据是来源报告的特定实验结果，并非当前配置的重新实测。定制算子与 AutoFuse 的百分比来自不同优化阶段，不能相加推导总收益。

## Evidence

- [torch_compile.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/torch_compile.md)（primary）
- [deepseek-v4_torchtitan_npu_autofuse.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（supporting）

## Links

- [训练框架](../frameworks/torchtitan.md)
- [融合算子替换](../frameworks/npu_fused_op_converters.md)
- [训练性能观测](training_debug_observability.md)
