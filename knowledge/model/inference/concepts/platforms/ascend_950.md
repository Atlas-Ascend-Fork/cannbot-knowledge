---
type: Concept
title: Ascend 950 (950PR / 950DT)
description: 950 的平台选择与 V4 的 FP8/HiF8/MXFP4、直方图 TopK、当前低时延 TP 和量化边界；区分技术报告与实际整网支持。
tags:
- task.lookup
- topic.architecture
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_ascendc_operator_guide.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-10-29T15:20:09Z'
platforms:
- '950'
---

# Ascend 950 (950PR / 950DT)

## Summary

Ascend 950（950PR / 950DT）是新代际昇腾推理芯片，与 [atlas-a3](atlas_a3.md) 在上游 README 中并列为两类目标部署平台。cann-recipes-infer 中已有多个模型适配 950 新代际：[deepseek-v4](../models/deepseek_v4.md) 0day LLM 适配（A3 + 950PR/DT）、HunyuanVideo single_fp8（量化加速仅支持 950PR）、Pangu-7B（声明支持 Atlas A3 + 950PR/DT 系列）等；DeepSeek-V4 是其上的 0day LLM 适配之一，也是本页代际特性的主要证据来源。相对 A3，950 的核心代际增益体现在三点：**原生 FP8 / MXFP4 浮点算力**、**Histograms（直方图）指令加速 LI 精确 Top-k**、以及**更充裕的 L0A/L0B 片上 Buffer 容量**（容下 256³ 统一基本块，据 Tiling 约束推断）。

`950PR` 与 `950DT` 是部署侧的两类标识：`950PR` 偏 Prefill 部署、`950DT` 偏 Decode 部署。在 cann-recipes-infer 配置中二者共用同一枚举值——`platform_version: "950"`，代码未将 PR / DT 进一步细分。

## Compute Specs

- 支持 **原生 FP8 与 MXFP4** 浮点计算：DeepSeek-V4 在 950 上启用原生 Hybrid FP8-MXFP4 量化（权重无损平滑迁移），并支持用 **MXFP8 替代原生 FP8** 的 Linear 模块，在 Prefill / Decode 高吞吐场景进一步提升算力利用率（见 [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)）。代码侧 FP8 走 `float8_e4m3fn`、MXFP4 走 `float4_e2m1fn_x2` dtype。
- **Histograms（直方图）指令**：950PR/DT 独有的向量指令，对若干 uint8 数字做直方图统计——一个 cycle 可将 64 个数字分入 0–127 或 128–255 桶。该指令用于加速 LI（[lightning-indexer](../kernels/lightning_indexer.md)）的**精确** Top-k 选择（保序变换 float→uint32 + 多级直方图分桶 + 向量化筛选）。`hist` 指令本体在外部仓（cann-recipes-infer 的 AscendC 源码不含该指令级实现，算法以 guide 为准）。
- CV（Cube : Vector）核数比：未在 V4 文档中给出（**源未明示**，待验证）；与之相对，A3 为分离架构、CV 比 **1:2**（每 1 Cube 核 + 2 Vector 核组成一个 AICore，见对照表）。

### 代际兼容软件栈

PyPTO 后端基于 **PTO 虚拟指令集（PTO ISA）**：一套算子代码可在 **A2 / A3 / 950D** 多代际芯片上运行，代际能力差异通过 pass IR 与后端 PTO 指令区分，guide 称其「兼容不降速」（除 MXFP8 量化等芯片本身能力不支持的情形外）。这是框架跨代际设计，不能当作该版本 V4 整网已接入 950 PyPTO 的证据：当前 V4 的 update_op_kernel_dict 在 enable_pypto 且平台非 a3 时拒绝运行，后续选择的是 _pypto_a3 实现。950 的 V4 部署须使用对应已接入算子路径，详见 [pypto](../frameworks/pypto.md)。算子框架在 950 上的平台分支（直方图 API、FP8 模式、平台分模板 Tiling）由 [ascendc](../frameworks/ascendc.md) 落地。

## Memory Hierarchy

- 与 A3 相同的 Cube 片上 Buffer 层级：L1 / L0A / L0B / L0C，Vector 侧 UB。
- **L0A / L0B 容量约束更宽松（据 Tiling 约束推断，源未给字节容量对比）**：A3 上 L0A、L0B 各开 double buffer `2×32KB`，K/V 走 3-Buffer，矩阵块以混合基本块搬入；950PR/DT 可取统一基本块 `baseM = baseN = baseK = 256`（A3 同算子则用混合基本块，如 Compressor C128A `256/128/512`、C4A `128/256/512`）。据此 Tiling 约束推断 950 的 L0A/L0B 容量更充裕，但源未直接给出字节容量对比。
  > 待验证：源仅给出"考虑 L0A，L0B 容量限制，可取 baseM=baseN=baseK=256"（ascendc guide:221），未直接列出 950 的 L0A/L0B 字节容量，也未给与 A3 的字节容量对比；此处为依 Tiling 约束的推断，不臆造具体 KB 数与"容量大于 A3"的直接断言。
- HBM 高带宽内存；KV Offload 和在线 PD 传输仍需核对各模型支持条件，不由平台编号推断其可用性。

## 与 Atlas A3 的代际架构对照

| 维度 | Atlas A3 | Ascend 950 (950PR/DT) |
| ---- | ---- | ---- |
| CV（Cube:Vector）核比 | 分离架构 **1:2**（源 mHC guide 明示） | 源未明示（待验证） |
| LI 精确 Top-k 指令 | `sort32` + `mrgsort`（理论 ≈ **28375** cycle @ Sₖ=16384,k=512） | **Histograms**（`hist`，理论 ≈ **7296** cycle，同 Sₖ/k 前提） |
| LI 量化路径 | 按该 A3 实现的 INT8/半精度路径核对 | **FP8 全量化版本**，FP8 Q/K 参与矩阵乘 |
| SAS 量化路径 | 半精度四阶段 C1/V1/C2/V2 | **伪量化版本**，V0 对 KV 反量化后进入五阶段流水 |
| Compressor 量化路径 | 按各自接口核对 | 单独核对实现，不由 LI/SAS 的模式推导 |
| 原生浮点格式 | BF16/FP16/INT8；走 sort32/mrgsort + 伪量化路径（未见原生 FP8/MXFP4 算力，按代码/文档推断） | **原生 FP8 + MXFP4**（MXFP8 可替代原生 FP8） |
| weightNZ 分形（[weight-nz](../techniques/weight_nz.md)） | 启用 | **关闭**（代码 `enable_weight_nz = not (platform_version == "950")`） |
| V4 部署最小单元（源 README，绑定量化条件） | Flash 4 chips（INT8 W8A8）/ Pro 32 chips（Hybrid INT8-INT4） | Flash 4 chips / Pro 16 chips（均为 Hybrid MXFP8-MXFP4） |
| V4 典型部署 | 64 卡大 EP（高吞吐） | 8 卡 / 16 卡（极低单用户时延） |

> ⚠️ 矛盾标记（CV 核比）：A3 的 CV 1:2 来自 mHC guide；950 的 CV 核比在 V4 文档中**未给出**，不可由 A3 推得或臆造（如 1:1）。两平台不同代际，相关数值各按其源，不混用。

## Histograms Top-k 理论开销（前提限定）

LI Top-k 必须精确（非近似）。950PR/DT 用 Histograms 方案在 Sₖ=16384、k=512、uint32 输入下，理论开销 ≈ `Sₖ/256 × 111 + 192 = 7296` cycle；A3 `sort32`/`mrgsort` 方案在相同 Sₖ/k 下理论开销 ≈ `(1.36Sₖ + 3.32k + ⌈max(log₂k−5,0)/2 × Sₖ⌉)/2 ≈ 28375` cycle。两者均为**理论估算值**，限定该 Sₖ / k / 数据类型；不同序列长度与 K 下数值不同。算子级实现细节见 [lightning-indexer](../kernels/lightning_indexer.md) 与 [ascendc](../frameworks/ascendc.md)（直方图 API）。

## 模型部署入口

DeepSeek-V4 的并行与配置按[分平台部署 Guide](../../guides/models/deepseek_v4_deployment.md)核对，来源测量按[950 来源观测](../../optimizations/benchmark_observations/deepseek_v4_950_source_benchmark.md)读取；不从单一模型推导芯片的固定部署卡数或通用优势。

## 最新 V4 功能范围

当前 V4 已增加 HiF8-MXFP8-MXFP4、A4W4 和低时延全 TP；Flash DSpark 在950也有配置。V4 低时延 TP 的所有相关 TP 等于 world 且 CP1；A4W4 加载前校验950。详见[量化矩阵](../quantization/hybrid_mxfp8_mxfp4.md)与[部署流程](../../guides/models/deepseek_v4_deployment.md)，这些是具体模型的实现条件，不扩展为所有950模型的共性。

## Known Constraints

- 配置层面 `950PR` / `950DT` 不单独区分，均通过 `platform_version: "950"` 选择（统一推理配置体系见 [inference-config](../techniques/inference_config.md)，`is_ascend_950()` 据此判断平台分支）；PR / DT 的部署差异由卡数与 Prefill/Decode 角色体现，非独立平台枚举。
- V4 的 950 路径 weightNZ 关闭，相应 Matmul 权重布局策略与 A3 不同。
- L0A/L0B 具体字节容量、CV 核比等底层规格在 V4 文档中未完整列出（标 gap，避免臆造）。

## Evidence

- [deepseek_v4_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md)（primary）
- [deepseek_v4_ascendc_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_ascendc_operator_guide.md)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py)（implementation）

## Links

- [atlas-a3](atlas_a3.md)（代际对照：A3 = CV1:2 / sort32-mrgsort / 无原生 FP8 / weightNZ 启用 vs 950 = Histograms / 原生 FP8-MXFP4 / weightNZ 关闭）
- [deepseek-v4](../models/deepseek_v4.md)（本页代际特性主要证据来源的 0day LLM 适配模型，A3 + 950PR/DT 双平台）
- [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)（950 原生 FP8 / MXFP4 浮点混合量化）
- [lightning-indexer](../kernels/lightning_indexer.md)（950 Histograms 精确 Top-k）
- [ascendc](../frameworks/ascendc.md)（950 直方图 API / FP8 模式 / 平台分模板 Tiling）
- [pypto](../frameworks/pypto.md)（PTO-ISA 一套算子代码跨 A2/A3/950D「兼容不降速」）
- [aicpu-scheduler](../techniques/aicpu_scheduler.md)（SAS / LI 值依赖分核下沉 AICPU）
- [weight-nz](../techniques/weight_nz.md)（950 上关闭，A3 启用）
- [inference-config](../techniques/inference_config.md)（`platform_version: "950"` 配置项 / `is_ascend_950()` 平台分支）
- 亦相关（弱链，纯文字提及不强求反链）：parallelism/context-parallel（950PR 长序列 Prefill CP）、technique/cann-shmem、technique/hixl、technique/kvcache-offload（超长序列 KV 卸载）
- [deepseek-v3-low-precision-pretrain](../../../training/guides/recipes/deepseek_v3_low_precision_pretrain.md)（跨域·训练：950DT(950) 上 V3 低精度预训练）
