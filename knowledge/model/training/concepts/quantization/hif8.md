---
type: Concept
title: HiF8（HiFloat8）8-bit 浮点格式与 V3 低精度预训练量化方案
description: HiF8 编码、缩放和来源报告的低精度训练收益；当前 TorchAO-NPU all_hif8、V4 LI HiFloat8 与 FSDP 预量化边界。
tags:
- task.design
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/low_precision_training.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/adaptor/torchao/recipes.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/te/pytorch/fp8/scale_data.py
  role: implementation
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- '950'
---

# HiF8（HiFloat8）8-bit 浮点格式与 V3 低精度预训练量化方案

## Summary

HiF8（HiFloat8）是华为自研的 8-bit 浮点数据格式，也是**裁剪版 DeepSeek-v3 在昇腾 950DT 上低精度预训练**的低精度核心。区别于固定阶码位宽的传统 FP8（E4M3/E5M2），HiF8 引入额外的 **点位（Dot）** 字段，使阶码与尾数位宽**随数值大小动态分配**，在 8-bit 位宽下同时取得「契合数据分布的锥形精度 + 接近 FP16 的大动态范围」。这一动态范围优势使 HiF8 能采用**粗粒度 Per-Tensor 量化 + 周期较长的 Delayed Scaling**，从而比需要 Per-Block 细粒度 scaling 的 MXFP8 省下大量缩放元数据访存与控制开销。在仅量化 MM / GMM 算子的实验中，HiF8 相对 BF16 取得 **29.5%** 端到端加速、相对 MXFP8 取得 **11.3%** 加速，且 Loss 与 Gradient Norm 与 BF16 基本对齐。它是 [deepseek-v3-low-precision-pretrain](../../guides/recipes/deepseek_v3_low_precision_pretrain.md) 实践所用的低精度格式与量化方案。

## HiF8 数据格式

HiF8 由**符号（S）/ 点位（D）/ 阶码（E）/ 尾数（M）** 四个字段组成。关键创新是 **Dot 字段**采用前缀编码（变长 2~4 bit），其编码值 D∈{0,1,2,3,4} 既指示阶码域宽度，又指示是否进入 Denormal 编码模式（DML）。表 1 给出字段结构：

| 字段 | 宽度（bit） | 说明 |
| - | - | - |
| 符号（S） | 1 | 1 表示负，0 表示正；HiF8 不区分 +0/−0 |
| 点位（D） | 2~4 | 前缀编码（`11`→4, `10`→3, `01`→2, `001`→1, `0001`→0, `0000`→DML），指示阶码域宽度及 Denormal 模式 |
| 阶码（E） | D 位 | **符号-幅度（Sign-Magnitude）** 编码，幅值最高位为隐含 1，不占存储 |
| 尾数（M） | 1~3 | 省略前导 1 的小数部分，无符号整数编码 |

### Normal 编码模式

Normal（规格化）模式数值为 $X = (-1)^S \cdot 2^E \cdot 1.M$。为使不同位宽阶码域对应的指数范围**互不重叠、实现无冗余编码**，阶码采用 Sign-Magnitude 且幅值最高位固定为隐含 1：Dot=0 时阶码不占位宽、E=0；Dot=1 时 E 只能取 ±1；Dot=2 时 E 取 ±[2,3]，依此类推。Dot 域指示的五种位宽阶码共编码 [−15, 15] 共 31 个指数且彼此不重复。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image1.png" width="62%"></p>
<p align="center"><sub>图：HiF8 Normal 编码模式——Dot 变长前缀编码阶码位宽，阶码原码 + 1-bit 隐含位（红字），E=[−3,3] 时 3-bit 尾数、随阶码幅值增大平滑收缩至 1-bit（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·第一章 Normal 编码模式）</sub></p>

「大位宽 Dot 域匹配小位宽（小幅值）阶码域」的设计让尾数精度**平滑渐变而非断层跳变**——这正是 HiF8 优于其借鉴对象 Posit 格式的关键。

### Denormal 编码模式与特殊值

为进一步扩大动态范围，HiF8 用了不同于 IEEE 754 的 Denormal 方案：当 Dot 域指示 DML 时不再保留独立阶码域，将原 3-bit 尾数空间（可编码 0~7 共 8 个离散值）**复用为极小值的指数扩展**。Denormal 在 Normal 的 [−15, 15] 之外额外开辟 [−22, −16] 共 7 个指数（编码 0 对应 −23，表示特殊值 Zero/NaN）。最终 HiF8 覆盖 [−22, 15] 共 **38 个指数**，已非常接近 FP16 的 [−24, 15]（40 个）；且 [−15,−8] 区间本身 1-bit 尾数、新增 [−22,−16] 区间 0-bit 尾数，精度连续过渡。

特殊值定义如下（表 3）：

| 条件 | 输出 | HiF8（二进制） | HiF8（十六进制） |
| - | - | - | - |
| S=0, D=DML, M=3'b0 | **Zero** | `00000000` | `0x00` |
| S=1, D=DML, M=3'b0 | **NaN** | `10000000` | `0x80` |
| D=4, Es=4'b0111, M=1 | **±Inf** | `X1101111` | `0x6F`/`0xEF` |

### 核心特性

- **契合数据分布的锥形精度（Tapered Precision）**：神经网络参数/激活通常呈类高斯分布，HiF8 把更高精度集中在高频出现的小幅值区间（Dot 大→阶码小→尾数 3-bit），而 FP8 E4M3/E5M2 阶码位宽固定难以兼顾范围与精度。
- **无冗余编码**：阶码原码 + 隐含 1-bit 高位，不同位宽阶码表达范围互不重叠。
- **大动态范围**：经 Denormal 把综合指数范围扩到 [−22, 15]，接近 FP16。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image3.png" width="55%"></p>
<p align="center"><sub>图：8-bit 浮点格式有效位-指数曲线——HiF8（红）在 E≈[−3,3] 区间达到 4-bit 有效位（含隐含位），两端平滑下降，呈锥形；E4M3（蓝）/E5M2（黑）则为固定平台（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·第一章 核心特性）</sub></p>

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image4.png" width="60%"></p>
<p align="center"><sub>图：HiF8 vs FP16 vs FP8-E4M3/E5M2 典型值与关键特征——HiF8 指数(+DML) 范围 [−22,15]，Max Positive NML 达 2^15，在 8-bit 位宽下逼近 FP16 动态范围（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·表 4）</sub></p>

## 量化方案：缩放与粒度

高精度（FP32/BF16）→ 8-bit 的核心是**缩放（Scaling）**：对数据块 X 除以反量化尺度 Scale（等价于乘其倒数），使原值无溢出地映射进 8-bit 动态范围。其中 $F8_{\max}$ 为目标格式最大可表示值（如 FP8-E4M3 为 448），$A_{\max}$ 为块内元素绝对值最大值：

$$\mathrm{Scale} = \frac{A_{\max}}{F8_{\max}}, \qquad X_{\mathrm{scaled}} = X / \mathrm{Scale} = X \cdot \frac{F8_{\max}}{A_{\max}}$$

上式假定 Amax>0；零张量由量化实现作零值保护。固定优化文档把 Amax/F8max 与量化乘数混用，此处纠正；MindSpeed scale_data.py 也说明为适配算子存储的是原乘数倒数，反量化时乘该尺度。

8-bit 位宽下精度有限，业界用「细粒度量化」加大 Scale 密度抑制损失：激活按 **Per-Token**（适配 LLM 激活在 token 维度的动态范围与离群值），权重按 **Per-Channel / Per-Block**（典型 block `128×128`，适配通道/块的静态分布差异）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image5.png" width="62%"></p>
<p align="center"><sub>图：常见量化粒度——(a) Per-Tensor 全张量单 Scale、(b) Per-Token 每行一 Scale、(c) Per-Channel 每列一 Scale、(d) Per-Block 每块一 Scale；越细 Scale 越多（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 4）</sub></p>

但极致细粒度会引入大量 Scale，显著增加硬件控制逻辑复杂度——需频繁加载/存储/应用这些额外因子，带来内存带宽开销与计算延迟，**部分抵消 8-bit 计算本身的加速**。关键差异在此：**HiF8 动态范围更大，训练中往往可用粗粒度 Per-Tensor 量化；而 FP8、MXFP8 等格式往往需要 Per-Block 量化。**

> **MXFP8**（Micro-scaling FP8）是块级共享 Scale 的细粒度方案：把浮点向量按块切分，每块共享一个低位宽 Scale（MX Scaling），元素为 FP8 E4M3 或 E5M2。推理侧对应实现见跨域页 [mxfp8-a8w8](../../../inference/concepts/quantization/mxfp8_a8w8.md)（DiT Linear A8W8，`group_size=32`、E8M0 scale）。训练侧 MXFP8 走 Per-Block scaling，与 HiF8 的 Per-Tensor 形成直接对照。

## 训练方案：BF16 混合精度基线与缩放策略

**基线**是基于 BF16 的混合精度训练（AMP）：前向/反向中计算密集型算子（MatMul、Convolution）下采样到 BF16，数值敏感算子（Softmax/LayerNorm/Loss）保留 FP32，Optimizer 维护一份 FP32 主权重（Master Weights）避免 BF16 尾数不足导致更新停滞。BF16 与 FP32 同阶码位宽（8-bit），动态范围相同（约 $10^{\pm 38}$），仅牺牲尾数精度。8-bit 混合精度在此基础上把缩放技术叠加进来。

8-bit 训练有两类缩放策略：

- **Current Scaling**：每个训练步都遍历输入 X 求 $A_{\max}$ 再算 Scale，求 $A_{\max}$ 与下游计算（MatMul）**串行**，部分抵消 8-bit 性能收益。
- **Delayed Scaling**：用**历史统计值**估计当前步 $A_{\max}$，把遍历 X 求 $A_{\max}$ 的操作与后续运算**解耦**，以 interval = K iterations 为周期更新；其中 $N_{guard}$ 是防上溢的保护参数。能更充分发挥 8-bit 训练的性能优势。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image7.png" width="78%"></p>
<p align="center"><sub>图：Delayed Scaling——每 interval（K iterations）才 Compute Amax 并写入 Amax_history_buffer，按 (F8max, Āmax, N_guard) 更新 Scale；逐 iteration 仅用上一周期 Scale_{i−1} 做缩放/量化，求 Amax 与主计算解耦（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 6）</sub></p>

> 常用于 8-bit 混合精度训练的 FP8-E4M3 因其动态范围较小，往往需要采用细颗粒度的 **Current Scaling**，而 HiF8 得益于其在精度和动态范围间所取得的平衡，能够采用 **Delayed Scaling**，并以较长的周期（interval）估计 **Amax** 值，同时仍保持训练稳定性。

## MindSpeed 低精度训练框架落点

HiF8 / MXFP8 验证基于 [mindspeed](../frameworks/mindspeed.md)（MindSpeed Core + MindSpeed LLM）开展，其 Transformer Engine（TE）模块与官方 TE 接口/能力兼容。低精度流程的核心是把 Linear 层中前向（Fprop）、激活反向（Dgrad）、权重反向（Wgrad）的通用矩阵乘量化为 FP8 / HiF8 执行，整体仍是 BF16/FP16 AMP 框架：

- `TERowParallelLinear` / `TEColumnParallelLinear` 把 Fprop / Dgrad / Wgrad 中的 MatMul 替换为低精度路径；
- `FP8GlobalStateManager` 单例维护全局 FP8 状态；各 Recipe 类执行不同量化策略，通过对应 Tensor 类管理 Scale 与数据张量。

MindSpeed 支持的格式 × 粒度组合（表 5 摘要）：

| 数据格式 | 量化粒度 | MatMul | Grouped MatMul | TP-MC2 |
| - | - | - | - | - |
| FP8 | Delayed | ✅ | Tensorwise 路径 | ❌ |
| FP8 | Tensorwise | ✅ | ✅ | ❌ |
| FP8 | Blockwise | ✅ | BF16 回退 | ❌ |
| FP8 | MXFP8 | ✅ | ✅ | ✅ |
| HiF8 | Delayed | ✅ | Tensorwise 路径 | ❌ |
| HiF8 | Tensorwise | ✅ | ✅ | ❌ |

（TP-MC2 = 通信计算融合算子；「BF16 回退」表示该组合下回退 BF16 路径。）

## 当前 TorchTitan-NPU 量化接入

当前低精度使用 TorchAO-NPU ParamSwap 与配置树转换；旧 quantize.linear.mx/quantize.grouped_mm.mx converter、全局 GMM 函数替换和 g_size 字典入口已移除，不能继续照旧列表设置 npu_gmm 前置。

低精度总开关为 --extension.quantization.enable-quantized-training，recipe 选择 all_hif8、all_mxfp8、mix、all_block_fp8。当前实现明确注册 all_hif8；指南前部只列三个 recipe 的表并非完整枚举，应结合配置和实现核对。模块按模型路径匹配，在模块构建时应用 quantize_，保留原模型的行为与配置，不再全局替换所有 GMM 调用。

V4 的 --extension.quantization.li-quantization hif8 是另一个独立选项：对 LI Q/K 使用 HiFloat8 per-tensor 动态量化、FP32 scale、CANN quant_mode=4。其前向量化不改变 BF16 SLIKG 反向 dtype；teacher 经 topk_scores 传递，并按 microbatch 完整 query token 数归一。V4.1 LI 当前只支持 mxfp4，不能套用 hif8。

当前训练面向 A5/950，并需配套 TorchAO-NPU 与算子依赖。日志 Applied TorchAO-NPU recipe=... 只能确认配置应用，仍需前反向、收敛与性能验证。Recipes 最新 README 中保留的旧 ParamSwap HiF8 脚本依赖已归档分支，不能混入当前 TorchTitan 提交作为可直接运行的配方。

## FSDP 预量化的适用边界

enable-fsdp-prequantize 仅对 Block FP8 scope 有效；与 all_hif8/all_mxfp8 同开会因无预量化 scope 抛 ValueError。mix/all_block_fp8 可在 all-gather 前量化本地 shard，减少参数 payload；梯度 reduce-scatter 的 reduce_dtype 不随之改变。

未设置白名单使用 recipe 默认范围，显式空表报错。命中 scope 但没有实际 FSDP shard等结构性情况可回退普通通信；量化维不满足对齐则报错，不能指望静默回退。该通信优化和 HiF8 格式本身是不同能力。

## 收益分析：HiF8 vs BF16 vs MXFP8

实验在 950DT-8P（单卡 486 TFLOPS）、裁剪版 DeepSeek-v3、MindSpeed / MindSpeed LLM、仅量化 **MM / GMM** 算子下进行。端到端单次迭代耗时对比（表 6）：

| 指标 | HiF8 | MXFP8 | BF16 | HiF8 vs MXFP8 | HiF8 vs BF16 |
| - | - | - | - | - | - |
| 单次迭代时间(s) | 2.80796152 | 3.12526599 | 3.63629095 | **1.113×** | **1.295×** |

即 HiF8 相对 BF16 加速 **29.5%**、相对 MXFP8 加速 **11.3%**（MXFP8 相对 BF16 吞吐提升约 16.35%，对应耗时下降约 14.05%，来源文字的 14.05% 使用耗时下降口径）。注意这是**仅 MM/GMM 量化**下的部分算子端到端收益，扩展到更多算子仍有提升空间。

### HiF8 相对 BF16 的收益来源

1. **位宽减半的访存收益**：BF16 16-bit → HiF8 8-bit 后，矩阵乘输入/输出/中间激活搬运量同步下降——降低片上内存带宽压力、提高片上 SRAM/Cache 复用率、减少跨存储层级搬运延迟（训练中部分算子受存储带宽限制）。
2. **8-bit 计算吞吐提升**：AI 加速硬件对 8-bit 计算路径有专门优化，MM/GMM 映射到 HiF8 路径后算力利用率提高。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image14.png" width="78%"></p>
<p align="center"><sub>图：HiF8 vs BF16 的 MM（左）与 GMM（右）算子逐 shape 加速比——平均加速比超过 1.8 倍（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 13）</sub></p>

### HiF8 相对 MXFP8 的收益来源

差异主要在**量化粒度与缩放元数据开销**。MXFP8 用 Per-Block 细粒度，需为每块维护额外 Scale 并频繁访问；HiF8 凭大动态范围用 Per-Tensor，三方面占优：

- **缩放元数据开销较低**：Scale 加载/存储次数减少、显存中细粒度 Scale 额外开销下降、数据访问更连续（无碎片化元数据的对齐/访问问题）。
- **控制逻辑更简单**：Per-Block 需处理块边界切换、局部反量化、跨块 Scale 对齐，增加控制复杂度并影响算子融合/流水化；Per-Tensor 数据流连续、控制简单。
- **更适合 Delayed Scaling**：HiF8 大动态范围 → 可用更新频率较低的 Delayed Scaling 而不明显影响稳定性，Amax 统计频率低、Scale 更新与同步操作少、对主计算流程干扰小；动态范围小的 FP8/MXFP8 往往需更频繁更新或更细粒度 scaling。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v3/image15.png" width="62%"></p>
<p align="center"><sub>图：DeepSeek-v3 裁剪网络 GMM 算子在 HiF8（上）与 MXFP8（下）下的 profiling 对比——HiF8 量化算子（标注「HiF8 量化算子」）耗时短于 MXFP8（标注「MXFP8 量化算子」）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 14）</sub></p>

## HiF8 训练推荐配置

兼顾精度与吞吐的推荐配置（表 7）：

| 配置维度 | 推荐方案 | 核心动机 |
| - | - | - |
| 量化粒度 | **Per-Tensor** | 最大化 HiF8 格式优势，消除 Per-Block 的访存与控制负担 |
| 缩放策略 | **Delayed Scaling** | 减少 Per-Block 量化的元数据开销与控制复杂度 |
| 更新周期 | **Interval = 10 steps**（或更高） | 利用 HiF8 动态范围优势，降低 Scale 更新频率 |
| 覆盖算子 | **MM / GMM** | 优先覆盖计算密集型主干算子 |
| Master Weights | **FP32 / BF16** | 保证参数更新阶段数值精度 |

实施原则：(1) 大多数 LLM 训练场景 Per-Tensor 已满足精度需求；(2) Delayed Scaling 周期设 10 steps 或更高以减少 Amax 统计/同步开销；(3) 从数值能力、训练稳定性、系统开销三方面综合评估。后续优化方向包括把 HiF8 扩展到 FlashAttention(FA) 及集合通信算子、优化 Amax 统计与 Scale 更新机制、软硬件协同优化低比特数据路径。

## Evidence

- [deepseek-v3_pre_train_hif8_mxfp8.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v3_pre_train_hif8_mxfp8.md)（primary）
- [low_precision_training.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/low_precision_training.md)（supporting）
- [recipes.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/adaptor/torchao/recipes.py)（implementation）
- [scale_data.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/te/pytorch/fp8/scale_data.py)（implementation）

## Links

- [低精度预训练实践](../../guides/recipes/deepseek_v3_low_precision_pretrain.md)
- [当前训练框架](../frameworks/torchtitan.md)
- [训练量化](../techniques/qat_train.md)
