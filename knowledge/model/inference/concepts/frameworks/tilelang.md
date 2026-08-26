---
type: Concept
title: TileLang
description: 'TileLang 是基于 TVM、面向 GPU/NPU/CPU 的 Tile 级算子语言，以类 Python 语法分离数据流与线程绑定、布局、张量化和流水调度。CANN 对接路径经多级 Lowering 生成 Ascend 代码、毕昇编译为 .so，再由 torch_npu 加载；已用于 DSA 的 Lightning Indexer、Sparse Flash Attention。DeepSeek-V4 Developer 模式提供 AscendC 与 PTO-AS 两个后端，通过自动 CV/核内同步、32B 对齐的生命周期内存复用及 CV 指令拆分，将样例代码量降至传统后端约 20%。当前 V4 样例覆盖 Sparse Flash Attention、mHC Sinkhorn、Int8 GEMM 和激活量化；T.Pipelined 是文档能力，但在该批样例中未发现调用。'
tags:
- task.implementation
- topic.architecture
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md
  role: primary
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# TileLang

## Summary

TileLang 是 **TileAI 开源社区**推出的面向 GPU/NPU/CPU 的 **Tile 级算子编程语言**，采用类 Python 语法、基于 TVM 底层基础设施，**将调度空间（线程绑定、布局、张量化、流水线）与数据流解耦**，以一组可自定义注解和原语封装出来。用户专注于内核的数据流本身，其余优化交给编译器完成。

cann-recipes-infer 同步对接 CANN 软件栈，在 TileLang 上完成了 DSA 的 **Lightning Indexer** 与 **Sparse Flash Attention** 两个关键算子实现（`ops/tilelang/lightning_indexer.py`、`ops/tilelang/sparse_flash_attention.py`），作为与 [ascendc](ascendc.md)、[pypto](pypto.md) 并列的第三路算子开发通道。

## Architecture

### NPU 工作流

![TileLang NPU 工作流](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/tl-workflow.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-workflow.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/tl-workflow.png)（cann-recipes-infer @ 2f82d10）*

- **编译阶段**：
 1. 多级 Lowering：TileLang 算子根据 NPU 硬件特性多级降级，生成针对昇腾硬件优化的 TensorIR；
 2. **AscendC 代码生成**：基于 TensorIR，用 Ascend Codegen 模块生成对应 AscendC 代码；
 3. **动态库编译**：通过**毕昇编译器（bisheng）**将 AscendC 代码编成 `.so`。
- **运行阶段**：
 4. 通过 `torch_npu` 运行时把 `.so` 加载到 Python 环境；
 5. 封装为可调用的 Python 函数对象；
 6. 用户以普通 Python 函数方式调用，提供输入张量即可在昇腾 NPU 上执行并拿结果。

### 编译运行流程（含本次适配修改点）

![TileLang 编译运行流程图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/tl-ascendc-workflow.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-ascendc-workflow.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/tl-ascendc-workflow.png)（cann-recipes-infer @ 2f82d10）*

深绿色为本次对接 Ascend NPU 要修改的部分：TileLang API 原语、CodeGen（AscendC 映射）、JIT 适配器、PyTorch 集成。

### NPU 内存层次

![NPU 存储结构](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/tl-npu-memory.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-npu-memory.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/tl-npu-memory.png)（cann-recipes-infer @ 2f82d10）*

## Key Features

### 原语体系

| 原语类型 | 典型名称 | 功能 | | ---- | ---- | ---- | | 内核原语 | `T.kernel(block_num, is_npu=True)` | 对应 AscendC kernel 调用；A2 的 cv 核默认 1:2，`cid/vid` 指定 Cube/Vector 索引 | | 内存分配 | `T.alloc_L1 / L0A / L0B / L0C / UB` | 按 shape + dtype 分配片上 buffer | | 数据搬运 | `T.copy(src, dst)` | 以 `BufferLoad` / `BufferRegion` 指定子区域 | | 计算 | `T.gemm`, `T.add`, `T.mul`, `T.reduce_max` | `T.reduce_max(dst, src, tmp, dim)`（目前只支持二维规约） | | 同步 | `T.set_flag / wait_flag / set_cross_flag / wait_cross_flag / pipe_barrier` | 跨流水/跨核同步 |

每个原语底层映射到一条或多条 AscendC 指令，屏蔽底层硬件差异。

### CodeGen & 指令映射

CodeGen 将 TileLang 高层语法自动转化为标准 AscendC 代码。示例 —— `copy_gm_to_l1` 的指令模板封装：

```cpp
template <typename T, uint32_t srcM, uint32_t srcN, uint32_t dstM, uint32_t dstN>
void copy_gm_to_l1(LocalTensor<T> dstTensor, GlobalTensor<T> srcTensor) {
 AscendC::DataCopy(dstTensor, srcTensor, {1, dstM, dstN, 0, srcN, dstM, 1, 0});
}
```

前端 Python `div` 原语到后端模板的映射：

```python
def div(dst: Buffer, src0: Buffer, src1: Union[Buffer, BufferLoad]):
 return binary_op(dst, src0, src1, "Div")
```

最后调用 bisheng 编译器编译得 `.so`。

### JIT 即时编译

JIT 会在运行中实时解析输入参数（维度、数据类型），同步向 CodeGen 传递，确保 NPU 算子支持动态输入；并结合 NPU 当前硬件状态优化指令分配（AI Core 利用率、内存占用）。JIT 适配步骤：CodeGen 生成源码 → 编到 `.so` → 基于 TileLang 的 Cython 适配器对接 NPU 接口 → 集成到 Python 环境。

### 扩展机制

**简单 API** 可以直接调 Ascend C API 封装。例如 `T.exp`：

```python
def unary_op(dst: Buffer, src0: Buffer, op: str):
 size_0 = math.prod(src0.shape); size_2 = math.prod(dst.shape)
 assert size_0 == size_2
 return T.call_extern("handle", f"AscendC::{op}",
 dst.access_ptr("w"), src0.access_ptr("r"), size_0)

def exp(dst: Buffer, src0: Buffer):
 return unary_op(dst, src0, "Exp")
```

**复杂 API**（如 `T.gemm_v0`）需要用 AscendC 封装 + Codegen 一起改：Python 层做参数合法化、shape 校验、指针提取，后端 `common.h` 实现 `gemm_v0`（copy L1→L0A/L0B + `mma` + `PipeBarrier<PIPE_ALL>`），CodeGen 层把 `gemm_v0(...)` 翻译成对后端模板的调用。完整示例见 `docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md` "复杂 API 封装"段。

## Usage Scenarios

- **跨平台算子复用**：TileLang 的 DSL 理论上在 GPU/NPU/CPU 间可移植，对比 Triton 可保留更多硬件亲和的底层控制。
- **社区开源算子快速落地**：对接 CANN 栈后，社区贡献的算子可直接在昇腾平台使用。
- **DeepSeek-V3.2-Exp DSA**：本仓同步提供了 TileLang 版的 LI 与 SFA —— 用较少代码量达到开箱可用；后续计划性能对齐 Triton 及更优（见 "下一步计划"）。

## Known Kernels

- [lightning-indexer](../kernels/lightning_indexer.md) — TileLang 版 LI（Cube/Vector 分解 + Top-K 归并排序；见 kernel 页 "TileLang 实现" 段）
- [sparse-flash-attention](../kernels/sparse_flash_attention.md) — TileLang 版 SFA（7 步 Block-Level 算法，`T.gemm_v0 / T.copy / T.set_cross_flag` 协同）

## Constraints

源文档"下一步计划"明示当前局限：

- **API 完备性**：尚未支持全部 NPU 通用算子（目标 2025 Q4 支持所有 NPU 通用算子）。
- **泛化性**：动态 Shape 支持 + 接入整网仍在迭代（2025 Q4）；原语中添加更多可配置参数。
- **性能**：SFA/LI 典型 Shape 性能目标是优于 Triton（2025 Q4 达成）。

## DeepSeek-V4 框架级增强（Developer 模式）

> 上文（NPU 工作流、原语体系、CodeGen、JIT、扩展、SFA/LI）以 V3.2-Exp 视角描述 TileLang-Ascend；本节补 DeepSeek-V4 0day 适配带来的 **Developer 模式**新特性。V4 实现位于 `ops/tilelang/ds_v4/`。

### Expert vs Developer 双模式 + 双对接层

TileLang-Ascend 提供两种后端编程路径，编译时自动适配不同层级 / 硬件场景：

- **AscendC 路径**（稳定）：经多级 Lowering → Ascend CodeGen → 毕昇编译 `.so`（即上文 V3.2-Exp 工作流）。
- **PTO-AS 路径**（跨代际高性能）：对接 [pypto](pypto.md) 的 PTO ISA（见该页 「PTO-ISA：跨代际芯片兼容」），获得 A2/A3/950D 跨代际兼容与毕昇 PTO VF 融合能力。

Expert 模式保留底层精细控制；**Developer 模式**把核间/核内同步、内存规划、CV 算力分配等复杂操作交由原语/编译器自动完成，开发者无需深入硬件底层。结合 Developer 模式，**在保持相近性能的前提下代码量可降至原后端实现的约 20%**（guide「Tilelang 算子优势」段）。

> 溯源：「Expert / Developer 双模式 + AscendC 基础指令 / PTO-AS 双对接层」的提法出自 `docs/models/deepseek-v4/deepseek_v4_inference_guide.md:22`（代码核对）；`deepseek_v4_tilelang_operator_guide.md` 通篇只讲 Developer 模式、无 "Expert" 字样。

### Developer 模式四大自动化 + 两个并行语法糖

各特性由 `pass_configs` 中的 `tilelang.PassConfigKey.*` 开关使能（代码核对：`ops/tilelang/ds_v4/sparse_flash_attention.py:18-21` 等四 PassConfigKey 全部存在）：

| 特性 | PassConfigKey | 做什么 |
|------|---------------|--------|
| **自动 CV 流水同步** | `TL_ASCEND_AUTO_CV_SYNC`（核间）/ `TL_ASCEND_AUTO_SYNC`（核内） | 针对 Cube/Vector 异步执行，自动化分析（for 循环展开两份分析嵌套依赖 → Buffer 访问分析定位流水线 → RAW/WAW/WAR 依赖决策 → 同流水线 PipeBarrier、跨流水线 EventPair(SetFlag/WaitFlag)）精准生成同步指令 |
| **自动内存规划复用** | `TL_ASCEND_MEMORY_PLANNING` | 缓冲区生命周期分析（GEN/KILL 标记活跃区间）+ **线性扫描分配算法**（按活跃区间起始排序、维护活跃队列与空闲块池、优先复用空闲块、32 字节对齐），生成 buffer→Offset 映射表（address_map），替代人工 Offset 计算、降峰值占用 |
| **自动拆分 CV 指令** | `TL_ASCEND_AUTO_CV_COMBINE` | 开发者按算法逻辑自然编写、Pass 自动识别哪些操作属 Cube / Vector，编译期构建 CV 依赖图、插同步、流水重排 + 双缓冲，免手工拆分（如 Flash Attention 中 Softmax(V)/MatMul(C) 复用同步逻辑） |
| **T.Parallel**（数据并行语法糖） | — | 用逐元素编程语法表达 tile 内元素向量化计算，IR 层以「并行循环」描述数据并行，不暴露底层指令（代码核对：act_quant.py:74,77、int8_gemm.py:96 等 `T.Parallel`） |
| **T.Pipelined**（流水并行语法糖） | — | 编译时静态分析 + 代码转换，实现计算与内存重叠执行（guide 描述的 V4 框架特性；ds_v4 四算子样例代码未见调用，`grep Pipelined ops/tilelang/` 未命中） |

### V4 四个算子样例

`ops/tilelang/ds_v4/` 提供四个 V4 0day 算子用例（文件名代码核对存在）：

- **Sparse Flash Attention（SFA）** `sparse_flash_attention.py` — 8 步块级流程（查询块加载 → 稀疏 KV 索引构掩码块 → 注意力分数 → Online Softmax → 上下文向量 → 累加重缩放 → **attn sink 锚点** → 写回），接入 C4A/C128A 压缩稀疏架构 + 可学习 Attention Sink；C:V 核 1:2、`[head//2, block=64]` 细粒度核内切分。算子级细节见 [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)（V4-Flash Shared-KV SFA 由 TileLang 实现）。
- **mHC（Manifold-Constrained Hyper-Connections）** `hc_split_sinkhorn.py` — 6 步（多流缩放 → pre 预变换 → post 后变换 → 指数归一化 → Sinkhorn-Knopp 行列归一化 → 写回），覆盖 [TileKernels](https://github.com/deepseek-ai/TileKernels) 中的 mhc 算子。结构语义见 [mhc](../modules/mhc.md)。
- **Int8 GEMM** `int8_gemm.py` — int8 输入矩阵乘（int32 中间）→ cast fp32 → 反量化缩放（`T.Parallel` 数据并行）→ cast 目标 dtype → 写回。
- **Activation Quantization** `act_quant.py` — 列向最大值规约 → 算缩放因子（可选取整 2 的幂）→ int8 对称量化 `y=round(clamp(x/scale,-127,127)).to(fp16).to(int8)` → 写回 scale + 量化值。

#### Int8 GEMM 双缩放反量化细节（int8_gemm.py）

承重补充上文一行流程（源 guide §3「Int8 General Matrix Multiplication」）。Int8_gemm 是带量化激活输入的 MatMul：int8 矩阵乘结果反量化为 fp32、经缩放因子缩放后再量化到目标 dtype。它是 **W8A8 反量化 GEMM**（激活与权重各带一组 scale），区别于普通 matmul —— 见 [w8a8c8](../quantization/w8a8c8.md)。

I/O 典型维度（guide §3 维度表）：

| 张量 | 维度 | 含义 |
|------|------|------|
| `a_int8` | `[M, K]` | int8 激活值 |
| `a_scales` | `[M, 1]` | 激活值缩放因子（**per-row / per-token scale**） |
| `b_int8` | `[N, K]` | int8 权重 |
| `b_scales` | `[N, 1]` | 权重缩放因子（**per-col / per-channel scale**） |
| `output` | `[M, N]` | 量化 gemm 输出 |

**cast / 反量化链**：`gemm_v0` 在 Cube 核上算 int8 matmul，中间结果存 int32（`C_tile = A_tile @ B_tile.T  Shape -> [64, 64]`，经 GM workspace 写入 `c_ub`）→ `T.tile.cast(c_scale, c_ub)` int32→fp32 → 反量化缩放 → `T.tile.cast(c_out, c_scale)` fp32→fp16（目标 dtype 以 fp16 为例）→ 写回。

**双缩放反量化核心**（`T.Parallel` 数据并行，guide §3「反量化缩放」）：每个输出元素 `c_scale[i,j]` 先乘激活行 scale 再乘权重列 scale（行 scale × 列 scale）：

```python
for (i, j) in T.Parallel(block_M_2, block_N):
    c_scale[i, j] *= scale_a_ub[i]
    c_scale[i, j] *= scale_b_ub[j]
```

#### Sparse Flash Attention（V4）维度与 attn sink 细节（sparse_flash_attention.py）

承重补充上文一行流程（源 guide §1「Sparse Flash Attention」算法流程详解）。

I/O 典型维度（guide §1 维度表）：

| 张量 | 维度 | 含义 |
|------|------|------|
| `query` | `[b, m, h, d]` | 查询向量集合 |
| `key/value` | `[b, n, d]` | 键值向量集合 |
| `topk_idxs` | `[b, m, k]` | topk 索引向量 |
| `attn_sink` | `[h]` | attn sink 注意力锚点向量（**per-head**） |
| `output` | `[b, m, h, d]` | 注意力输出 |

**核间/核内切分**：batch×m 作核间并行（以 `batch*m` 为逻辑核 core_id 在 AiCores 均匀分配），C:V 核 1:2；核内以 `[head//2, block=64]` 细粒度切分，主块 `dim=512`（`Shape -> [32, 512]`）、核内切分块 `block=64`（`Shape -> [32, 64]`）。

**稀疏索引 idxs_ub 构建规则**（guide §1 步骤 2，`t` 为块循环序号）：

```python
for i in T.serial(block):
    idxs_ub[i] = topk_idxs[by, bx, t * block + i] if t * block + i < topk else -1
```

即块内位置在 topk 范围内取对应 `topk_idxs` 值，否则置 `-1`（标记非参与位）；再据 `idxs_ub` 筛选参与计算的 key（`kv_ub`）并构建注意力分数掩码矩阵 `acc_s_ub`。

**attn sink 锚点重缩放**（guide §1 步骤 7「注意力锚点计算」，`T.Parallel` 二维场景）：对累加结果 `acc_o_ub` 按锚点重缩放，除以 `exp(attn_sink − scores_max)`：

```python
for (i, j) in T.Parallel(v_block, d):
    acc_o_ub[i, j] /= T.exp(attn_sink_ub[i] - scores_max[i])
```

> **attn sink（可学习注意力锚点）是 V4 SFA 相对 V3.2-Exp 的新增机制**（源 guide §1 概述：「新版的 SFA 算子还引入了可学习注意力锚点（Attention sink）机制，通过调整每个查询头的注意力分数，保护模型输出序列的稳定性」），保留前 s 个 token 的注意力权重与 KV 缓存，使输出保留全局上下文、避免仅依赖近期 token。算子级细节见 [sparse-flash-attention](../kernels/sparse_flash_attention.md)。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（整文 —— 简介、工作流、NPU 适配、API、CodeGen、JIT、扩展、SFA/LI 实现、下一步计划）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md)（V4 TileLang-Ascend Developer 模式 + 四算子用例，MR afa4019/272df2f；通篇仅讲 Developer 模式、无 "Expert"）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md` §1 Sparse Flash Attention](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md)（SFA 维度表、idxs_ub 构建、attn sink 锚点重缩放 / C4A·C128A 压缩稀疏 + 可学习 Attention Sink）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md` §3 Int8 GEMM](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/deepseek-v4/deepseek_v4_tilelang_operator_guide.md)（Int8 GEMM I/O 维度表、双缩放反量化 `c_scale *= scale_a_ub[i]; *= scale_b_ub[j]`、int8→int32→fp32→fp16 cast 链）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_inference_guide.md:22`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md)（"Expert / Developer 双模式 + AscendC 基础指令 / PTO AS 双对接层" 提法溯源）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/tilelang/ds_v4/{sparse_flash_attention.py, hc_split_sinkhorn.py, int8_gemm.py, act_quant.py}`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/ops/tilelang/ds_v4)（V4 四算子 + PassConfigKey 符号 grep 核对）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/tilelang/{lightning_indexer.py, sparse_flash_attention.py}`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/tilelang/{lightning_indexer.py, sparse_flash_attention.py}) + `ops/tilelang/docs/` + `ops/tilelang/examples/`
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/tilelang/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/tilelang/README.md)

## Links

- [ascendc](ascendc.md)
- [pypto](pypto.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)（V4-Flash SAS sparse_attn_kernel 由 TileLang 实现）
- [deepseek-v4](../models/deepseek_v4.md)（V4 0day 适配 TileLang Developer 模式 + 四算子样例）
- [mhc](../modules/mhc.md)（V4 mHC 算子 hc_split_sinkhorn.py 由 TileLang 实现，覆盖 TileKernels mhc）
- [cann-shmem](../techniques/cann_shmem.md)（Tilelang-shmem 框架接入 SHMEM：`T.shmem_ub_put_nbi_new` 把 UB 数据非阻塞传送对端 win 区）
- [shmem-dispatch-combine](../techniques/shmem_dispatch_combine.md)（Tilelang-shmem 写 MoE dispatch&combine kernel 的实现样例之一）
- [tilelang-rope](../../../training/concepts/kernels/tilelang_rope.md)（跨域·训练：TileLang RoPE 训练算子）
- [tilelang-moe-token-permute](../../../training/concepts/kernels/tilelang_moe_token_permute.md)（跨域·训练：TileLang MoE Token Permute 算子族）
- [tilelang-rmsnorm-swiglu](../../../training/concepts/kernels/tilelang_rmsnorm_swiglu.md)（跨域·训练：TileLang RMSNorm/SwiGLU 训练算子）
- [triton-on-ascend](../../../training/concepts/frameworks/triton_on_ascend.md)（训练侧另一条昇腾 kernel DSL 通道：Triton DSL 经 triton_npu 后端落昇腾）
