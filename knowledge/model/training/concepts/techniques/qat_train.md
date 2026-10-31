---
type: Concept
title: QAT 量化感知训练（Quantization-Aware Training）
description: QAT 量化感知训练在 MindSpeed 中由 qat-quant-engine 特性实现：前向对权重做伪量化（fake-quant，量化→反量化）注入部署侧量化误差，反向用直通估计（STE，伪量化算子 backward 返回恒等梯度）让梯度落到原始高精度（BF16/FP32 master）权重上；权重高精度存储更新、矩阵乘仍跑 16-bit，训练收敛出对低比特鲁棒、可部署的低比特权重。开关 --qat-scheme 四取值按「位宽×作用域」展开：w4a16-mxfp4 / w8a16-mxfp8（全部线性层+MoE 专家层）与对应 -moe-only（仅专家层），实际进入 QAT 分支时激活保留 16-bit；低精度 GMM 优先路径可跳过专家 QAT，即纯权重量化 W4A16/W8A16。两个伪量化核按 MX 块量化（块大小 32、每块一个 2 的幂 shared exponent 夹到 E8M0 范围±127）：W4A16 元素 MXFP4/E2M1（max_norm=6），W8A16 元素 MXFP8/E4M3（max=448，先 pad 到 32 整数倍再 narrow）。整网线性层通过 patch megatron LinearWithGradAccumulationAndAsyncCommunication 前反向注入（需先开 gradient-accumulation-fusion/async-allreduce/sequence-parallel 之一），MoE 走 GMM experts 路径。与 PTQ 区别在把量化误差提前进优化目标用训练换部署精度；与低精度训练区别在 QAT 只模拟部署量化不真正降低比特计算/存储，而低精度优化器压动量省显存、TE/HiF8 把 GEMM 真降低比特求吞吐。
tags:
- task.optimization
- topic.precision
- topic.model_adaptation
status: stable
sources:
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/qat_quant.md
  role: supporting
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- agnostic
---

# QAT 量化感知训练（Quantization-Aware Training）

## Summary

QAT 让模型在训练阶段就「见到」部署时的量化误差：前向把权重按低比特格式做一次**量化再反量化**（fake-quant，伪量化），用反量化后的近似值参与矩阵乘；权重本身仍以高精度（BF16/FP32 master）存储与更新，反向用**梯度直通估计**（STE，Straight-Through Estimator）让梯度绕过不可导的取整算子、直接落到原始高精度权重上。于是训练在高精度下进行，但损失曲线已经把量化噪声计入优化目标，训练收敛出的权重对低比特量化**鲁棒**，可直接导出为可部署的低比特权重。MindSpeed 的 `qat-quant-engine` 特性把这套机制做成开关 `--qat-scheme`，支持权重 4-bit（MXFP4/E2M1）与 8-bit（MXFP8/E4M3）两种格式、整网线性层与「仅 MoE 专家层」两种作用域，实际进入 QAT 分支时激活保留 16-bit（即 W4A16 / W8A16，纯权重量化）。它与训练后量化（PTQ）、与真把计算降到低比特的低精度训练（[hif8](../quantization/hif8.md) 的 TE 路径、[optimizer-memory](optimizer_memory.md) 的低精度优化器）目标不同，是 [mindspeed](../frameworks/mindspeed.md) 量化工具箱里面向「部署精度」的一档。

## 伪量化与直通估计：QAT 的两个支点

低比特量化的取整/截断是阶梯函数，处处导数为 0 或不存在，无法直接反向。QAT 用一对配合的机制绕开这点：

- **伪量化（fake-quant）**：前向对权重 `W` 先量化到目标低比特格式 `Q(W)`，再立刻反量化回高精度 `W' = dequant(Q(W))`，用 `W'` 替代 `W` 参与本层矩阵乘。`W'` 与 `W` 数值接近、但已携带量化引入的扰动，等价于**把部署时的量化误差提前注入前向**。注意矩阵乘仍在 16-bit（`input.dtype`）下执行——伪量化只制造误差、不调用真正的低比特 GEMM，所以训练本身不因此提速。
- **直通估计（STE）**：伪量化算子的反向被定义为**恒等映射**，即 `∂L/∂W = ∂L/∂W'`，梯度像量化节点不存在一样穿过去，直接更新原始高精度权重。MindSpeed 的 `W4A16FakeQuantization.backward` / `W8A16FakeQuantization.backward` 都返回 `(output_grad, None, None)`，正是 STE 的实现。

结果是：权重以高精度存储更新、优化器照常工作，唯独前向多了一道「量化—反量化」让模型在训练中逐步适应低比特表示。

```mermaid
flowchart LR
  W["高精度权重 W (BF16/FP32 master)"] -->|fake-quant: 量化→反量化| Wq["W' = dequant(quant(W))<br/>携带量化误差"]
  Wq -->|matmul (16-bit)| Y["层输出"]
  Y --> L["loss"]
  L -.->|反向: STE 恒等穿过<br/>∂L/∂W = ∂L/∂W'| W
```

## 量化格式与作用域：--qat-scheme

`QATQuantEngineFeature`（`optimization_level=2`）注册唯一开关 `--qat-scheme`，默认 `None`（不启用），四个取值沿「位宽 × 作用域」两维展开：

| `--qat-scheme` | 权重格式 | 作用域 |
| --- | --- | --- |
| `w4a16-mxfp4` | MXFP4（E2M1 + 块缩放） | 全部线性层 + MoE 专家层 |
| `w4a16-mxfp4-moe-only` | MXFP4 | 仅 MoE 专家层 |
| `w8a16-mxfp8` | MXFP8（E4M3 + 块缩放） | 全部线性层 + MoE 专家层 |
| `w8a16-mxfp8-moe-only` | MXFP8 | 仅 MoE 专家层 |

命名里 `W4`/`W8` 指权重量化到 4/8 bit，`A16` 指激活保留 16-bit——**QAT 伪量化分支不量化激活/输入张量**，只有权重过伪量化，属纯权重量化（weight-only）。两种作用域由两处接入点分担：整网线性层走 `LinearWithGradAccumulationAndAsyncCommunication` 的前反向替换（只对 `w4a16-mxfp4` / `w8a16-mxfp8` 两个非 moe-only 方案生效），MoE 专家层走 GMM 实现内的判断（对 `*-moe-only` 与全量方案都生效）。这是目标作用域；非空 token 的专家路径若 get_gmm_quant_func() 返回低精度 GMM 实现，会优先调用 gmm_apply、跳过 w1/w2 的 QAT 伪量化。只有实际进入 QAT 分支时，激活不被伪量化、GEMM 仍走 16-bit，不能把这项保证套到低精度 GMM 优先分支。

## 块级 micro-scaling 的伪量化核

两个量化格式都按 **MX（micro-scaling）块量化**组织：把权重最后一维切成长度 32 的块，每块共享一个 2 的幂缩放（shared exponent），块内元素再按低比特浮点格式逐个量化。伪量化算子接口 `fakequant_func(weight, [1, 32], False)` 里 `[1, 32]` 名义上是 1×32 的缩放块形状、`False` 是 `transpose` 标志，但**两个参数当前都不被核消费**——块大小 32 由核内 `unflatten(-1, (-1, 32))` 硬编码，量化轴固定为最后一维。

**MXFP4（`w4a16_fake_quant`，元素 E2M1）**：直接 unflatten 最后一维为 32 元素块，没有补齐逻辑，故该维度必须能被 32 整除；专家层应检查展平后实际最后一维，而非原始权重任意一维。`ebits=2, mbits=3`，可表示最大值 `max_norm = 6.0`（E2M1 的最大模）。流程是——块内取绝对值最大 `amax` → 共享指数 `shared_exp = floor(log2(amax)) - emax`，并夹到 E8M0 缩放范围 `[-127, 127]`（越界置 NaN / 下夹）→ 块元素除以 `2^shared_exp` 落入 E2M1 可表示区间 → 逐元素取私有指数 `floor(log2|x|)`（下限夹到 0）、尾数四舍五入到 1 bit（`floor(|x|·2 + 0.5)/2` 这一步）、再夹到 `[-6, 6]` → 乘回 `2^shared_exp` 反量化、还原回原形状。

**MXFP8（`w8a16_fake_quant`，元素 E4M3）**：先把最后一维 **pad 到 32 的整数倍**（量化后再 `narrow` 裁回原长），按块取 `amax` → 共享指数 `shared_exp = ceil(log2(amax) - log2(448))`（448 = E4M3 最大有限值）、同样夹到 `[-127, 127]` → 块元素除以 `2^shared_exp` 并夹到 `[-448, 448]` → 逐元素走 `_e4m3fn_fake_quantize`（私有指数下限 −6、量化步长 `2^(private_exp-3)` 对应 3-bit 尾数、夹到 `[0, 448]`、NaN 透传）→ 乘回 `2^shared_exp` 反量化、裁掉 padding。

两个核的产物都是**与输入同 dtype 的反量化高精度张量**，回放进矩阵乘——量化误差被精确注入，但下游计算仍是普通 16-bit matmul。

## 接入点：替换 Megatron 线性层前反向

整网线性层的注入由 `register_patches` 完成：当 `--qat-scheme` 取 `w4a16-mxfp4` 或 `w8a16-mxfp8` 时，把 `megatron.core.tensor_parallel.layers.LinearWithGradAccumulationAndAsyncCommunication` 的 `forward` / `backward` 替换成 QAT 版本。替换前有一道**前置依赖检查**：必须至少开启 `--gradient-accumulation-fusion`、`--async-tensor-model-parallel-allreduce`、`--sequence-parallel` 三者之一（即走「优化版」线性层路径），否则只 `warnings.warn` 提示、不打 patch——因为被替换的就是这条优化版线性算子。

QAT 版前向 `_linear_with_grad_accumulation_and_async_qat_forward` 的关键改动只有一行——在矩阵乘之前对权重做伪量化、并把伪量化后的 `quant_weight` 存进 `ctx`：

```python
quant_weight = fakequant_func(weight, [1, 32], False)
ctx.save_for_backward(input, quant_weight)
...
output = torch.matmul(total_input, quant_weight.t())   # 仍是 16-bit matmul
# mindspeed/core/qat/layers.py · _linear_with_grad_accumulation_and_async_qat_forward
```

其余的序列并行 all-gather、bias 叠加照旧。QAT 版反向沿用原生的 dgrad / wgrad 逻辑，只是 dgrad 用伪量化后的权重算 `grad_input = grad_output.matmul(quant_weight)`、wgrad 仍把 `total_input × grad_output` 累加进 `main_grad`（兼容 `gradient_accumulation_fusion` 与 `sequence_parallel` 的 reduce-scatter / all-reduce 调度）。伪量化节点本身的反向是 STE 恒等，所以梯度最终落在原始高精度权重上。

MoE 专家层的注入在 GMM 路径里：专家前向按 `qat_scheme` 选 `W4A16FakeQuantization` / `W8A16FakeQuantization`，把 `w1` / `w2` 先展平成二维（`w1` 走 `view(-1, hidden_size)`、`w2` 走 `view(num_local_experts·hidden_size, -1)`，使各自的待量化轴落到最后一维）→ `fakequant_func(·, [1, 32], False)` → `reshape` 回专家权重形状，再喂给 `gg.ops.gmm` 分组矩阵乘；空 token 分支则退回普通 `torch.matmul`（此时 `w1`/`w2` 均按 `view(-1, hidden_size)` 展平后伪量化）。这条路径对全量方案与 moe-only 方案都生效，非空 token 路径仅在 get_gmm_quant_func() 返回空时执行上述 QAT，非空实现优先走 gmm_apply 而跳过该处理。

## 与 PTQ 的区别

PTQ（训练后量化）在模型训练完成后、不再更新权重的前提下直接把权重/激活折算到低比特，靠校准集统计 scale，零额外训练成本，但量化误差未进入过优化目标，低比特下精度损失可能较大。QAT 把量化误差提前搬进训练前向，让优化器在高精度空间里**主动把权重推向「量化后仍准」的解**，代价是要付一段（微调或继续训练）训练算力。两者定位互补：能接受 PTQ 精度时优先 PTQ（便宜），精度不达标再上 QAT 用训练换部署精度。MindSpeed QAT 文档把目标精度损失定位为「控制在可接受范围」。

## 与低精度训练的关系

QAT 与「低精度训练」同属低精度家族，但意图相反，容易混淆：

- **低精度优化器**（[optimizer-memory](optimizer_memory.md)）把**优化器状态**（动量 FP8/HiF8/MXFP8、梯度 FP16）压到低比特只为**省显存**，更新时反量化回 FP32 计算，低精度仅用于存储——不改变前向的数值表示，也不产出低比特权重。
- **TE / HiF8 低精度训练**（[hif8](../quantization/hif8.md)）把 Linear 的 Fprop/Dgrad/Wgrad **GEMM 真正降到 FP8/HiF8 执行**，低比特数据流进硬件低比特矩阵乘单元，目标是**训练吞吐**；它要的是「训练更快」，量化是真实计算。
- **QAT** 反过来：训练阶段权重仍以高精度存储更新、GEMM 仍跑 16-bit，伪量化只**模拟**部署时的量化、不带来训练加速；它要的是「部署更省」——产出对 W4/W8 量化鲁棒的权重。

因此 QAT 的「低精度」发生在被模拟的部署侧，而低精度训练的「低精度」发生在真实的训练计算/存储侧。三者目标不同；组合时须核对真实分支与覆盖，低精度 GMM 可能优先并跳过专家 QAT，不能由开关同开推导伪量化仍生效。可分别评估相容的组合（如 QAT 出鲁棒权重 + 低精度优化器省训练显存），共享 [mindspeed](../frameworks/mindspeed.md) 的同一套 feature manager 与 patch 机制。

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md)（primary）
- [qat_quant.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/docs/zh/features/qat_quant.md)（supporting）

## Links

- [hif8](../quantization/hif8.md)（同框架低精度路径，但 HiF8/MXFP8 经 TE 把 GEMM 真正降到低比特求吞吐，与 QAT 的「伪量化只模拟部署误差、计算仍 16-bit」对照）
- [optimizer-memory](optimizer_memory.md)（低精度优化器把动量/梯度量化到 FP8/HiF8/MXFP8 只为省显存、算时反量化；与 QAT 同属低精度家族但意图不同，可对照「存储低精度」与「模拟部署量化」）
- [mindspeed](../frameworks/mindspeed.md)（`qat-quant-engine` 特性所属框架，feature manager 注册 `--qat-scheme` 并 patch 线性层前反向与 MoE GMM）
