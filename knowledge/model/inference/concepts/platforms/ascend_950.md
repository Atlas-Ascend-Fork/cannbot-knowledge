---
type: Concept
title: Ascend 950 (950PR / 950DT)
description: Ascend 950（950PR/950DT）是 cann-recipes-infer 面向新代际昇腾的部署平台，DeepSeek-V4、HunyuanVideo
  和 Pangu-7B 等已有适配。相较 A3，其 V4 路径支持 FP8/MXFP4，并可用 Histograms 加速 LI 精确 Top-k；在 S_k=16384、k=512、uint32
  条件下理论约 7296 cycle，对比 A3 排序路径约 28375 cycle。SAS 在 950 使用含反量化的五阶段伪量化流水，Tiling 可取 256³
  基本块，weightNZ 则关闭。950PR 偏 Prefill、950DT 偏 Decode，但配置统一使用 platform_version="950"，代码未区分两者；950
  的 CV 核比和 L0 容量字节数仍缺直接证据。
tags:
- task.lookup
- topic.architecture
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-10-22T10:36:46Z'
platforms:
- '950'
---
# Ascend 950 (950PR / 950DT)

## Summary

Ascend 950（950PR / 950DT）是新代际昇腾推理芯片，与 [atlas-a3](atlas_a3.md) 在上游 README 中并列为两类目标部署平台。cann-recipes-infer 中已有多个模型适配 950 新代际（deepseek-v4 `platform_version` 取值仅 `A3`/`950`；「950」仅见于个别 commit 标签，与 950 关系源未明示）：[deepseek-v4](../models/deepseek_v4.md) 0day LLM 适配（A3 + 950PR/DT）、HunyuanVideo single_fp8（量化加速仅支持 950PR）、Pangu-7B（声明支持 Atlas A3 + 950PR/DT 系列）等；DeepSeek-V4 是其上的 0day LLM 适配之一，也是本页代际特性的主要证据来源。相对 A3，950 的核心代际增益体现在三点：**原生 FP8 / MXFP4 浮点算力**、**Histograms（直方图）指令加速 LI 精确 Top-k**、以及**更充裕的 L0A/L0B 片上 Buffer 容量**（容下 256³ 统一基本块，据 Tiling 约束推断）。

`950PR` 与 `950DT` 是部署侧的两类标识：`950PR` 偏 Prefill 部署、`950DT` 偏 Decode 部署。在 cann-recipes-infer 配置中二者共用同一枚举值——`platform_version: "950"`（与 `"A3"` 二选一），代码未将 PR / DT 进一步细分。

## Compute Specs

- 支持 **原生 FP8 与 MXFP4** 浮点计算：DeepSeek-V4 在 950 上启用原生 Hybrid FP8-MXFP4 量化（权重无损平滑迁移），并支持用 **MXFP8 替代原生 FP8** 的 Linear 模块，在 Prefill / Decode 高吞吐场景进一步提升算力利用率（见 [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)）。代码侧 FP8 走 `float8_e4m3fn`、MXFP4 走 `float4_e2m1fn_x2` dtype。
- **Histograms（直方图）指令**：950PR/DT 独有的向量指令，对若干 uint8 数字做直方图统计——一个 cycle 可将 64 个数字分入 0–127 或 128–255 桶。该指令用于加速 LI（[lightning-indexer](../kernels/lightning_indexer.md)）的**精确** Top-k 选择（保序变换 float→uint32 + 多级直方图分桶 + 向量化筛选）。`hist` 指令本体在外部仓（cann-recipes-infer 的 AscendC 源码不含该指令级实现，算法以 guide 为准）。
- CV（Cube : Vector）核数比：未在 V4 文档中给出（**源未明示**，待验证）；与之相对，A3 为分离架构、CV 比 **1:2**（每 1 Cube 核 + 2 Vector 核组成一个 AICore，见对照表）。

### 代际兼容软件栈

PyPTO 后端基于 **PTO 虚拟指令集（PTO ISA）**：一套算子代码可在 **A2 / A3 / 950D** 多代际芯片上运行，代际能力差异通过 pass IR 与后端 PTO 指令区分，guide 称其「兼容不降速」（除 MXFP8 量化等芯片本身能力不支持的情形外）。即同一份 V4 融合算子源码无需为 950 重写前端，详见 [pypto](../frameworks/pypto.md)。算子框架在 950 上的平台分支（直方图 API、FP8 模式、平台分模板 Tiling）由 [ascendc](../frameworks/ascendc.md) 落地。

## Memory Hierarchy

- 与 A3 相同的 Cube 片上 Buffer 层级：L1 / L0A / L0B / L0C，Vector 侧 UB。
- **L0A / L0B 容量约束更宽松（据 Tiling 约束推断，源未给字节容量对比）**：A3 上 L0A、L0B 各开 double buffer `2×32KB`，K/V 走 3-Buffer，矩阵块以混合基本块搬入；950PR/DT 可取统一基本块 `baseM = baseN = baseK = 256`（A3 同算子则用混合基本块，如 Compressor C128A `256/128/512`、C4A `128/256/512`）。据此 Tiling 约束推断 950 的 L0A/L0B 容量更充裕，但源未直接给出字节容量对比。
  > 待验证：源仅给出"考虑 L0A，L0B 容量限制，可取 baseM=baseN=baseK=256"（ascendc guide:221），未直接列出 950 的 L0A/L0B 字节容量，也未给与 A3 的字节容量对比；此处为依 Tiling 约束的推断，不臆造具体 KB 数与"容量大于 A3"的直接断言。
- HBM 高带宽内存；超长序列下仍可叠加 KVCache Offload / HiXL（基于 CANN-SHMEM）卸载 KV（这些为平台无关的通用技术，弱相关，见 Links 弱链一行）。

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
| V4 部署最小单元（源 README） | Flash 4 chips / Pro 32 chips | Flash 4 chips / Pro 16 chips |
| V4 典型部署 | 64 卡大 EP（高吞吐） | 8 卡 / 16 卡（极低单用户时延） |

> ⚠️ 矛盾标记（CV 核比）：A3 的 CV 1:2 来自 mHC guide；950 的 CV 核比在 V4 文档中**未给出**，不可由 A3 推得或臆造（如 1:1）。两平台不同代际，相关数值各按其源，不混用。

## Histograms Top-k 理论开销（前提限定）

LI Top-k 必须精确（非近似）。950PR/DT 用 Histograms 方案在 Sₖ=16384、k=512、uint32 输入下，理论开销 ≈ `Sₖ/256 × 111 + 192 = 7296` cycle；A3 `sort32`/`mrgsort` 方案在相同 Sₖ/k 下理论开销 ≈ `(1.36Sₖ + 3.32k + ⌈max(log₂k−5,0)/2 × Sₖ⌉)/2 ≈ 28375` cycle。两者均为**理论估算值**，限定该 Sₖ / k / 数据类型；不同序列长度与 K 下数值不同。算子级实现细节见 [lightning-indexer](../kernels/lightning_indexer.md) 与 [ascendc](../frameworks/ascendc.md)（直方图 API）。

## 模型部署入口

DeepSeek-V4 的并行与配置按[分平台部署 Guide](../../guides/models/deepseek_v4_deployment.md)核对，来源测量按[950 来源观测](../../optimizations/benchmark_observations/deepseek_v4_950_source_benchmark.md)读取；不从单一模型推导芯片的固定部署卡数或通用优势。

## Known Constraints

- 配置层面 `950PR` / `950DT` 不单独区分，均通过 `platform_version: "950"` 选择（统一推理配置体系见 [inference-config](../techniques/inference_config.md)，`is_ascend_950()` 据此判断平台分支）；PR / DT 的部署差异由卡数与 Prefill/Decode 角色体现，非独立平台枚举。
- 950 上 weightNZ 关闭，相应 Matmul 权重布局策略与 A3 不同。
- L0A/L0B 具体字节容量、CV 核比等底层规格在 V4 文档中未完整列出（标 gap，避免臆造）。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md)（950PR/DT 平台引入、部署卡数、量化策略、950DT Benchmark）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md)（Histograms 指令 Top-k 算法与理论开销 7296 vs 28375 cycle、L0A/L0B 容量约束→ baseM=baseN=baseK=256、SAS FP8 伪量化五阶段）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_mHC_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_mHC_guide.md)（A3 分离架构 CV 比 1:2，作代际对照基准）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/config/ci_950/deepseek_v4.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/config/ci_950/deepseek_v4.yaml) / [`config/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/config/README.md)（`platform_version: "950"`、`world_size: 16`、`next_n: 3`；枚举仅 `["A3", "950"]`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/README.md)（最小部署单元 950PR/DT Flash 4 / Pro 16 chips）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/infer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/infer.py)（实现：`enable_weight_nz = not platform_version == "950"`、`platform_version` 仅 `"A3"`/`"950"`、kernel 注册键拼接 `op_type_kernel_impl_platform`）；[`models/modules/attention_data.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modules/attention_data.py)（950 cmp_kv dtype = `float8_e4m3fn`）；MXFP4 dtype `float4_e2m1fn_x2`（`modeling_deepseek.py`）
- 溯源（@2c45117）：`13b8e6a` dsv4 add platform guide（!396）；`377f20f` DeepSeek-V4-Flash 模型与文档；`c62b731` deepseek-v4 ge_graph（!412）；`5ba7598` 950 combine quant、`fac85e8` 950 inplace_partial_rotary_mul 混合精度（commit message 标 950；950 与 950 关系源未明示，本页不并称同代际）。

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
