---
type: Concept
title: HiF8（HiFloat8）8-bit 浮点格式与 V3 低精度预训练量化方案
description: HiF8/MXFP8 8-bit 低精度训练有两条实现路径。(1)MindSpeed+TE：--fp8-format/--fp8-recipe，FP8GlobalStateManager/TERowParallelLinear，950 950DT。(2)torchtitan-npu converter 路径：nn.Linear→MXLinear(quant_linear.py)、npu_grouped_mm→低精度 GMM(quant_gmm.py)，converter quantize.linear.mx/quantize.grouped_mm.mx，recipe_name∈{mxfp8,hif8}，MXFP8 用 torch_npu.npu_dynamic_mx_quant(block=32)+npu_quant_matmul、HiF8 用 npu_dynamic_quant+npu_grouped_matmul，filter_fqns 跳敏感层，npu_gmm 须先于 quantize.grouped_mm.mx，仅 Ascend950+。该 converter 路径不同于 torchtitan 上游的 TorchAO MXLinearConverter 路径。
tags:
- task.design
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md
  role: supporting
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: supporting
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/low_precision_training.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
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

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image1.png" width="62%"></p>
<p align="center"><sub>图：HiF8 Normal 编码模式——Dot 变长前缀编码阶码位宽，阶码原码 + 1-bit 隐含位（红字），E=[−3,3] 时 3-bit 尾数、随阶码幅值增大平滑收缩至 1-bit（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·第一章 Normal 编码模式）</sub></p>

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

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image3.png" width="55%"></p>
<p align="center"><sub>图：8-bit 浮点格式有效位-指数曲线——HiF8（红）在 E≈[−3,3] 区间达到 4-bit 有效位（含隐含位），两端平滑下降，呈锥形；E4M3（蓝）/E5M2（黑）则为固定平台（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·第一章 核心特性）</sub></p>

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image4.png" width="60%"></p>
<p align="center"><sub>图：HiF8 vs FP16 vs FP8-E4M3/E5M2 典型值与关键特征——HiF8 指数(+DML) 范围 [−22,15]，Max Positive NML 达 2^15，在 8-bit 位宽下逼近 FP16 动态范围（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·表 4）</sub></p>

## 量化方案：缩放与粒度

高精度（FP32/BF16）→ 8-bit 的核心是**缩放（Scaling）**：对数据块 X 乘缩放因子 Scale，使原值无溢出地映射进 8-bit 动态范围。其中 $F8_{\max}$ 为目标格式最大可表示值（如 FP8-E4M3 为 448），$A_{\max}$ 为块内元素绝对值最大值：

$$\mathrm{Scale} = \frac{A_{\max}}{F8_{\max}}, \qquad X_{\mathrm{scaled}} = X \cdot \mathrm{Scale} = X \cdot \frac{A_{\max}}{F8_{\max}}$$

8-bit 位宽下精度有限，业界用「细粒度量化」加大 Scale 密度抑制损失：激活按 **Per-Token**（适配 LLM 激活在 token 维度的动态范围与离群值），权重按 **Per-Channel / Per-Block**（典型 block `128×128`，适配通道/块的静态分布差异）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image5.png" width="62%"></p>
<p align="center"><sub>图：常见量化粒度——(a) Per-Tensor 全张量单 Scale、(b) Per-Token 每行一 Scale、(c) Per-Channel 每列一 Scale、(d) Per-Block 每块一 Scale；越细 Scale 越多（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 4）</sub></p>

但极致细粒度会引入大量 Scale，显著增加硬件控制逻辑复杂度——需频繁加载/存储/应用这些额外因子，带来内存带宽开销与计算延迟，**部分抵消 8-bit 计算本身的加速**。关键差异在此：**HiF8 动态范围更大，训练中往往可用粗粒度 Per-Tensor 量化；而 FP8、MXFP8 等格式往往需要 Per-Block 量化。**

> **MXFP8**（Micro-scaling FP8）是块级共享 Scale 的细粒度方案：把浮点向量按块切分，每块共享一个低位宽 Scale（MX Scaling），元素为 FP8 E4M3 或 E5M2。推理侧对应实现见跨域页 [mxfp8-a8w8](../../../inference/concepts/quantization/mxfp8_a8w8.md)（DiT Linear A8W8，`group_size=32`、E8M0 scale）。训练侧 MXFP8 走 Per-Block scaling，与 HiF8 的 Per-Tensor 形成直接对照。

## 训练方案：BF16 混合精度基线与缩放策略

**基线**是基于 BF16 的混合精度训练（AMP）：前向/反向中计算密集型算子（MatMul、Convolution）下采样到 BF16，数值敏感算子（Softmax/LayerNorm/Loss）保留 FP32，Optimizer 维护一份 FP32 主权重（Master Weights）避免 BF16 尾数不足导致更新停滞。BF16 与 FP32 同阶码位宽（8-bit），动态范围相同（约 $10^{\pm 38}$），仅牺牲尾数精度。8-bit 混合精度在此基础上把缩放技术叠加进来。

8-bit 训练有两类缩放策略：

- **Current Scaling**：每个训练步都遍历输入 X 求 $A_{\max}$ 再算 Scale，求 $A_{\max}$ 与下游计算（MatMul）**串行**，部分抵消 8-bit 性能收益。
- **Delayed Scaling**：用**历史统计值**估计当前步 $A_{\max}$，把遍历 X 求 $A_{\max}$ 的操作与后续运算**解耦**，以 interval = K iterations 为周期更新；其中 $N_{guard}$ 是防上溢的保护参数。能更充分发挥 8-bit 训练的性能优势。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image7.png" width="78%"></p>
<p align="center"><sub>图：Delayed Scaling——每 interval（K iterations）才 Compute Amax 并写入 Amax_history_buffer，按 (F8max, Āmax, N_guard) 更新 Scale；逐 iteration 仅用上一周期 Scale_{i−1} 做缩放/量化，求 Amax 与主计算解耦（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 6）</sub></p>

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

## 在 torchtitan-npu 的应用：converter 机制低精度路径

除 MindSpeed + TE 路径外，HiF8 与 MXFP8 这两种 8-bit 浮点格式在 [torchtitan](../frameworks/torchtitan.md) 上还有**另一套独立实现**：通过 torchtitan 的 converter 机制，在模型构建完成后对目标模块做无缝替换，把线性层与 MoE 专家层的 GEMM 降到 8-bit 执行。其 `recipe_name` 取值即决定走哪种格式：`recipe_name ∈ {"mxfp8", "hif8"}`。**硬件门槛与 MindSpeed 路径一致——仅支持 Ascend 950 及更高架构**，初始化时经 `torch_npu.npu.get_device_name()` 检测，不满足报错 `[MXFP8/Hif8] is only supported on Ascend950 or higher architecture.`（`Ascend950`/`Ascend910_95`；以代码 `quant_converter.py` 实际抛出串为准——大小写为 `Hif8` 且结尾带句点，源文档写作 `[MXFP8/HiF8] ...` 无句点，与代码不一致）。

> ⚠️ 区分上游 TorchAO 路径：[torchtitan](../frameworks/torchtitan.md) 页里的 MXFP8 小节描述的是 **TorchAO 上游 `quantize_` + `MXLinearConverter`** 路径；本小节是 **NPU 专用路径**——torchtitan-npu patch 掉上游 `MXFP8Converter`，把 GEMM 重写为 `torch_npu` 低精度算子（详见 [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)）。二者不矛盾，是同一格式在不同算子后端上的两条落地路线。

### 转换机制与代码落点

| 文件 | 作用 |
| - | - |
| `converters/quant_converter.py` | NPU 适配替换上游 `MXFP8Converter` 的初始化与转换逻辑、硬件检测 |
| `converters/kernels/quant_linear.py` | 低精度线性层 `MXLinear`（MXFP8/HiF8 前反向自定义算子） |
| `converters/kernels/quant_gmm.py` | 低精度分组矩阵乘（MoE GMM 的 MXFP8/HiF8 前反向算子） |
| `patches/quantization/quant_config.py` | 配置数据类 `MXLinearConfig` / `MoETrainingConfig` 及 recipe 枚举 |
| `patches/quantization/quantize.py` | `linear_quantize_` / `grouped_quantize_`，递归遍历模型模块并替换 |

两个转换器分别注册为 `quantize.linear.mx`（线性层）与 `quantize.grouped_mm.mx`（MoE GMM）。converter 在 `nn.Linear` → `MXLinear`、`npu_grouped_mm` → 低精度 GMM 之间做替换；`MXLinear.forward` 按 `recipe_name` 分派到 MXFP8 或 HiF8 自定义算子。

### MXFP8 模式（Per-Block，block=32）

- **线性层**：`torch_npu.npu_dynamic_mx_quant` 对激活与权重做 per-block 量化（block size=32，每 32 个元素共享 1 个 scale），再经 `torch_npu.npu_quant_matmul` 做低精度矩阵乘；Fprop / Dgrad / Wgrad 均以 FP8 执行，输出恢复原精度。
- **MoE GMM**：前向用 `torch_npu.npu_dynamic_mx_quant`（block=32）量化输入与权重后调 `torch_npu.npu_grouped_matmul`；反向权重梯度（Wgrad）改用 `torch_npu.npu_grouped_dynamic_mx_quant`（`blocksize=32`）做 per-block 量化。MXFP8 元素为 `float8_e4m3fn`、scale 为 `float8_e8m0fnu`。

### HiF8 模式（Per-Tensor / Per-Expert-Group）

- **线性层**：`torch_npu.npu_dynamic_quant(..., dst_type=torch_npu.hifloat8, quant_mode="pertensor")` 对激活与权重做 **per-tensor** 动态量化（整张量共享 1 个 scale），再调 `torch_npu.npu_quant_matmul`。这与下文 HiF8 训练推荐配置的 Per-Tensor 粒度一致——HiF8 的大动态范围使粗粒度量化即可保稳定。
- **MoE GMM**：分组大小 `g_size` 不在量化算子内现算，而是从 `gmm.py` 定义的模块级全局字典 `group_size_params`（含 `num_experts` / `expert_model_parallel_size` / `g_size`）读取——量化算子 `quant_gmm.py` 仅 `g_size = group_size_params["g_size"]` 消费它，该字典由 `npu_gmm` converter 侧据专家数与 EP 并行度填入。这正是 `npu_gmm` 必须前置于 `quantize.grouped_mm.mx` 的机制根源：前置 converter 写好 `group_size_params`，后置量化算子才取得到 `g_size`。随后 `reshape(g_size, -1)` 再用 `torch_npu.npu_dynamic_quant` 的默认 **per-token** 模式逐行量化（实际对应**每个专家分组共享一个 scale**，即 per-token-per-expert-group），再调 `torch_npu.npu_grouped_matmul`。

### 配置与关键约束

线性层配置（`quantize.linear.mx`）：`recipe_name`（str，默认 `"mxfp8"`，可选 `"hif8"`）、`filter_fqns`（list[str]，**子串包含**匹配，跳过不替换的层，如 `"output"`、`"router.gate"`）。MoE 配置（`quantize.grouped_mm.mx`）：`recipe_name` 同上；`fqns`（list[str]，默认空）按**子串包含**匹配待替换的 MoE 模块（`moe_module_filter_fn` 返回 `any(target_fqn in cur_fqn for target_fqn in self.moe_fqns)`，`self.moe_fqns = config.fqns`），留空则 `any(...)` 恒为 False、**不替换任何 MoE GMM**；要全量替换需显式传入覆盖所有专家层 FQN 的子串。

> ⚠️ 矛盾标记：源文档（`low_precision_training.md`）称 `fqns` 为「保留字段，暂不生效，目前对所有 MoE 专家层 GMM 全量替换」，但代码 `quant_converter.py` 的 `moe_module_filter_fn` 实际按 `fqns` 子串过滤，默认空列表使过滤恒 False，行为是「一个 MoE 模块都不替换」，与「全量替换」相反。此处以代码为准。

```python
model_converters = ModelConvertersContainer.Config(
    converters=[
        get_model_converter_config("npu_gmm"),  # 必须在 quantize.grouped_mm.mx 之前
        MXFP8Converter.Config(
            recipe_name="mxfp8",                 # 或 "hif8"
            filter_fqns=["output", "router.gate"],
        ),
    ],
)
```

> **CRITICAL 顺序约束**：MoE 低精度依赖 `npu_gmm` converter 提供的分组矩阵乘基础实现，因此 `converters` 列表中 `"npu_gmm"` **必须位于** `"quantize.grouped_mm.mx"`（即 `MXFP8Converter`）**之前**，否则 MoE 专家层替换失败。生效自检：启动日志应出现 `MX training active with recipe <mxfp8|hif8>` / `Swapped to MXLinear_NPU layers`（线性层）与 `Converted all MoE grouped MM layers to use dynamic <mxfp8|hif8> quantization with scaled grouped GEMMs` / `[MXFP8/Hif8 GMM] Replaced <N> NPU GMM methods/functions.`（MoE）。注意 MoE 转换日志以代码实际输出（`quant_converter.py` 末尾 `logger.info`）为准——源文档验证清单写作 `<recipe_name> MoE training enabled`，该串在代码与全仓中均不存在。

## 收益分析：HiF8 vs BF16 vs MXFP8

实验在 950DT-8P（单卡 486 TFLOPS）、裁剪版 DeepSeek-v3、MindSpeed / MindSpeed LLM、仅量化 **MM / GMM** 算子下进行。端到端单次迭代耗时对比（表 6）：

| 指标 | HiF8 | MXFP8 | BF16 | HiF8 vs MXFP8 | HiF8 vs BF16 |
| - | - | - | - | - | - |
| 单次迭代时间(s) | 2.80796152 | 3.12526599 | 3.63629095 | **1.113×** | **1.295×** |

即 HiF8 相对 BF16 加速 **29.5%**、相对 MXFP8 加速 **11.3%**（MXFP8 相对 BF16 仅 14.05%）。注意这是**仅 MM/GMM 量化**下的部分算子端到端收益，扩展到更多算子仍有提升空间。

### HiF8 相对 BF16 的收益来源

1. **位宽减半的访存收益**：BF16 16-bit → HiF8 8-bit 后，矩阵乘输入/输出/中间激活搬运量同步下降——降低片上内存带宽压力、提高片上 SRAM/Cache 复用率、减少跨存储层级搬运延迟（训练中部分算子受存储带宽限制）。
2. **8-bit 计算吞吐提升**：AI 加速硬件对 8-bit 计算路径有专门优化，MM/GMM 映射到 HiF8 路径后算力利用率提高。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image14.png" width="78%"></p>
<p align="center"><sub>图：HiF8 vs BF16 的 MM（左）与 GMM（右）算子逐 shape 加速比——平均加速比超过 1.8 倍（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 13）</sub></p>

### HiF8 相对 MXFP8 的收益来源

差异主要在**量化粒度与缩放元数据开销**。MXFP8 用 Per-Block 细粒度，需为每块维护额外 Scale 并频繁访问；HiF8 凭大动态范围用 Per-Tensor，三方面占优：

- **缩放元数据开销较低**：Scale 加载/存储次数减少、显存中细粒度 Scale 额外开销下降、数据访问更连续（无碎片化元数据的对齐/访问问题）。
- **控制逻辑更简单**：Per-Block 需处理块边界切换、局部反量化、跨块 Scale 对齐，增加控制复杂度并影响算子融合/流水化；Per-Tensor 数据流连续、控制简单。
- **更适合 Delayed Scaling**：HiF8 大动态范围 → 可用更新频率较低的 Delayed Scaling 而不明显影响稳定性，Amax 统计频率低、Scale 更新与同步操作少、对主计算流程干扰小；动态范围小的 FP8/MXFP8 往往需更频繁更新或更细粒度 scaling。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v3/image15.png" width="62%"></p>
<p align="center"><sub>图：DeepSeek-v3 裁剪网络 GMM 算子在 HiF8（上）与 MXFP8（下）下的 profiling 对比——HiF8 量化算子（标注「HiF8 量化算子」）耗时短于 MXFP8（标注「MXFP8 量化算子」）（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md">DeepSeek-V3 优化文档</a>·图 14）</sub></p>

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

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v3_pre_train_hifp8_mxfp8.md)（第一章 HiF8 数据格式：字段结构 / Normal·Denormal 编码 / 特殊值 / 核心特性；第二章 量化方案：缩放公式 + Per-Token/Channel/Block 粒度；第三章 训练方案：BF16 AMP 基线 + Current vs Delayed Scaling；第四章 MindSpeed TE 与表 5 格式×粒度组合；第六章 收益分析表 6 + HiF8 vs BF16 / vs MXFP8 收益来源；第七章 表 7 推荐配置）
- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/low_precision_training.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/low_precision_training.md)（torchtitan converter 机制实现 MXFP8/HiF8：converter 注册名 `quantize.linear.mx` / `quantize.grouped_mm.mx`、`MXLinear` 与低精度 GMM、`recipe_name`/`filter_fqns` 配置、`npu_gmm` 必须前置约束、Ascend 950+ 硬件门槛、验证清单）；低精度算子 [`converters/kernels/quant_linear.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/quant_linear.py) / [`converters/kernels/quant_gmm.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/quant_gmm.py) / [`patches/quantization/quant_config.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/patches/quantization/quant_config.py)（`recipe_name ∈ {"mxfp8","hif8"}`）

## Links

- [deepseek-v3-low-precision-pretrain](../../guides/recipes/deepseek_v3_low_precision_pretrain.md)（承载 HiF8 格式/量化方案的预训练实践：裁剪版 DeepSeek-v3 在 950DT-8P 上 HiF8 相对 BF16 29.5% 端到端加速）
- [mindspeed](../frameworks/mindspeed.md)（HiF8/MXFP8 验证所用训练框架：MindSpeed Core + MindSpeed LLM 的 TE 低精度路径、表 5 格式组合）
- [mxfp8-a8w8](../../../inference/concepts/quantization/mxfp8_a8w8.md)（跨域：推理侧 MXFP8 块级 micro-scaling 实现，训练侧 MXFP8 Per-Block 与之同源；HiF8 以 Per-Tensor 与其形成收益对照）
- [torchtitan-5d-parallel](../parallelism/torchtitan_5d_parallel.md)（同域：另一条 DeepSeek-V3.2 预训练优化主线，含 Float8 训练接入；HiF8 是 V3 低精度预训练的格式核心）
- [torchtitan](../frameworks/torchtitan.md)（HiF8/MXFP8 的**第二实现框架**：torchtitan-npu 经 converter 机制（`quantize.linear.mx` / `quantize.grouped_mm.mx`）把 GEMM 重写为 `torch_npu` 低精度算子，与上游 TorchAO `quantize_` + `MXLinearConverter` 路径并存；V3 低精度预训练验证走 MindSpeed+TE）
- [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)（承载 torchtitan-npu 低精度路径的 converter 注册/替换机制：`npu_gmm` 前置约束、`MXFP8Converter` patch 与 `linear_quantize_`/`grouped_quantize_` 递归替换）
- [qat-train](../techniques/qat_train.md)（训练态量化：QAT 学习适应量化误差，对照 HiF8 低精度训练格式）

<!-- cannbot:related:start -->
## 相关

- [DeepSeek-V3 裁剪模型 MXFP8/HiF8 低精度预训练（MindSpeed · Atlas 950 950DT · 8K）](../../guides/recipes/deepseek_v3_low_precision_pretrain.md)（`related`）：这一动态范围优势使 HiF8 能采用**粗粒度 Per-Tensor 量化 + 周期较长的 Delayed Scaling**，从而比需要 Per-Block 细粒度 scaling 的 MXFP8 省下大量缩放元数据访存与控制开销。；分别用 **HiF8** 与 **MXFP8（E4M3）** 两种低精度格式量化整网的 **MatMul（MM）/ Grouped MatMul（GMM）** 算子，与 BF16 混合精度做长稳精度对齐与性能对比。。概念卡解释 HiF8 的 Per-Tensor 与 Delayed Scaling 机制及相对 MXFP8 的开销差异，Recipe 将这两种格式用于 MM/GMM 并与 BF16 做稳定性和性能验证，形成量化原理到训练实验的实施链。
<!-- cannbot:related:end -->
