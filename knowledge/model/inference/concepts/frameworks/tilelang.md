---
type: Concept
title: TileLang
description: TileLang当前Ascend适配与分目录、V4 Developer机制和受具体kernel约束的JIT；更新V3.2 LI workspace/布局与安装入口。
tags:
- task.implementation
- topic.architecture
- topic.attention
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_tilelang_operator_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_tilelang_operator_guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/README.md
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v32/lightning_indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v4/sparse_flash_attention.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v4/act_quant.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:34:04Z'
platforms:
- agnostic
---

# TileLang

## Summary

TileLang 是 **TileAI 开源社区**推出的面向 GPU/NPU/CPU 的 **Tile 级算子编程语言**，采用类 Python 语法、基于 TVM 底层基础设施，**将调度空间（线程绑定、布局、张量化、流水线）与数据流解耦**，以一组可自定义注解和原语封装出来。用户专注于内核的数据流本身，其余优化交给编译器完成。

cann-recipes-infer 同步对接 CANN 软件栈，在 TileLang 上完成了 DSA 的 **Lightning Indexer** 与 **Sparse Flash Attention** 两个关键算子实现（`ops/tilelang/ds_v32/lightning_indexer.py`、`ops/tilelang/ds_v32/sparse_flash_attention.py`），作为与 [ascendc](ascendc.md)、[pypto](pypto.md) 并列的第三路算子开发通道。

## Architecture

### NPU 工作流

![TileLang NPU 工作流](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-workflow.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-workflow.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-workflow.png)（cann-recipes-infer @ 944d2d3）*

- **编译阶段**：
 1. 多级 Lowering：TileLang 算子根据 NPU 硬件特性多级降级，生成针对昇腾硬件优化的 TensorIR；
 2. **AscendC 代码生成**：基于 TensorIR，用 Ascend Codegen 模块生成对应 AscendC 代码；
 3. **动态库编译**：通过**毕昇编译器（bisheng）**将 AscendC 代码编成 `.so`。
- **运行阶段**：
 4. 通过 `torch_npu` 运行时把 `.so` 加载到 Python 环境；
 5. 封装为可调用的 Python 函数对象；
 6. 用户以普通 Python 函数方式调用，提供输入张量即可在昇腾 NPU 上执行并拿结果。

### 编译运行流程与 Ascend 适配层

![TileLang 编译运行流程图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-ascendc-workflow.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-ascendc-workflow.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-ascendc-workflow.png)（cann-recipes-infer @ 944d2d3）*

图中深绿色标出 Ascend NPU 适配层：TileLang API 原语、CodeGen（AscendC 映射）、JIT 适配器、PyTorch 集成。

### NPU 内存层次

![NPU 存储结构](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-npu-memory.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/tl-npu-memory.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/tl-npu-memory.png)（cann-recipes-infer @ 944d2d3）*

## Key Features

### 原语体系

| 原语类型 | 典型名称 | 功能 |
| ---- | ---- | ---- |
| 内核原语 | `T.kernel(block_num, is_npu=True)` | 对应 AscendC kernel 调用；A2 的 cv 核默认 1:2，`cid/vid` 指定 Cube/Vector 索引 |
| 内存分配 | `T.alloc_L1 / L0A / L0B / L0C / UB` | 按 shape + dtype 分配片上 buffer |
| 数据搬运 | `T.copy(src, dst)` | 以 `BufferLoad` / `BufferRegion` 指定子区域 |
| 计算 | `T.gemm`, `T.add`, `T.mul`, `T.reduce_max` | `T.reduce_max(dst, src, tmp, dim)`（目前只支持二维规约） |
| 同步 | `T.set_flag / wait_flag / set_cross_flag / wait_cross_flag / pipe_barrier` | 跨流水/跨核同步 |

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

JIT按调用参数生成编译专门化；动态shape、缓存与调度支持依赖具体kernel和编译器，不能由JIT名称推定任意动态输入或自动读取硬件利用率优化。JIT 适配步骤：CodeGen 生成源码 → 编到 `.so` → 基于 TileLang 的 Cython 适配器对接 NPU 接口 → 集成到 Python 环境。

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
- **DeepSeek-V3.2-Exp DSA**：cann-recipes-infer 提供了 TileLang 版的 LI 与 SFA —— 用较少代码量达到开箱可用；后续计划性能对齐 Triton 及更优（见 "下一步计划"）。

## Known Kernels

- [lightning-indexer](../kernels/lightning_indexer.md) — TileLang 版 LI（Cube/Vector 分解 + Top-K 归并排序；见 kernel 页 "TileLang 实现" 段）
- [sparse-flash-attention](../kernels/sparse_flash_attention.md) — TileLang 版 SFA（7 步 Block-Level 算法，`T.gemm_v0 / T.copy / T.set_cross_flag` 协同）

## Constraints

旧技术指南中的2025 Q4目标是当时计划，不能作为当前尚未支持的清单或已经交付的证明。当前ops/tilelang/README更新到TileLang-Ascend安装入口、CANN8.5/PyTorch2.8镜像与ds_v32/ds_v4分目录；测试入口为对应examples/test_sfa.py。能力、动态shape及整网接入仍需按实际编译器和算子验收。

V3.2 LI现在显式传入VECTOR/BLOCK尺寸并声明QK workspace，QK张量为[B,N2,S1,G,S2]；不能复制旧展平shape和硬编码UB地址。通用原语介绍不代表新版本后端ABI恒定。

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
- **Activation Quantization** `act_quant.py` — 列向最大值规约 → 算缩放因子（该固定实现始终使用 max_abs/127，签名 round_scale 尚未被函数体使用，不能据指南将其当作已实现的 2 的幂取整选项）→ int8 对称量化 `y=round(clamp(x/scale,-127,127)).to(fp16).to(int8)` → 写回 scale + 量化值。

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

**attn sink 归一化**：以固定实现为准，TopK 循环先完成 online softmax 的累计与重缩放，然后把每个 head 的 sink 指数项加入已有分母：

```python
T.tile.sub(attn_sink_ub, attn_sink_ub, scores_max[:, 0])
T.tile.exp(attn_sink_ub, attn_sink_ub)
T.tile.add(sum_exp[:, 0], sum_exp[:, 0], attn_sink_ub)
T.tile.broadcast(sum_exp_brd, sum_exp)
T.tile.div(acc_o_ub, acc_o_ub, sum_exp_brd)
```

分母为 `sum_j exp(score_j - scores_max) + exp(attn_sink - scores_max)`，不能只除以 sink 指数项。这里的 attn_sink 是可学习的 per-head 归一化项，代码没有保留前 s 个 token 的注意力权重或 KV 缓存的操作。指南步骤 7 的简化公式与固定实现不一致，本卡采用代码中的完整分母；不能将这一机制混同于前缀 token 缓存保留。算子级上下文见 [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)。

## Evidence

- [deepseek_v3.2_exp_tilelang_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（primary）
- [deepseek_v4_tilelang_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_tilelang_operator_guide.md)（supporting）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/README.md)（constraint）
- [lightning_indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v32/lightning_indexer.py)（implementation）
- [sparse_flash_attention.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v4/sparse_flash_attention.py)（implementation）
- [act_quant.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/tilelang/ds_v4/act_quant.py)（implementation）

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
