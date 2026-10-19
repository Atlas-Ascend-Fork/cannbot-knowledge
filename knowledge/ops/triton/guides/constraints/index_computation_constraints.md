---
type: Guide
title: index_computation 类算子设计约束
description: index_computation 类算子的适用范围、类别专属设计约束与常见陷阱；跨类别通用条款见 global_constraints.md。
tags: [task.design, topic.implementation.atomic, topic.compute.indexing, topic.data_movement.layout_transform, topic.tiling, topic.alignment]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Indexing_Ops/gather.md
  role: primary
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-10-14T00:00:00Z'
platforms: [a2, a3]
---

# index_computation 类算子设计约束

> 跨类别通用约束见 [global_constraints.md](global_constraints.md)（`GC-1`~`GC-15`），
> 本卡只列本类别特有条款。

## 索引计算类算子优化经验

本文档合并索引计算类算子的优化经验。按以下结构组织：
- **§1 通用经验**：跨算子重复的工程约束（已提取，各算子章节不再重复）
- **§2 Layer 2: 类别级通用算法骨架**
- **§3 Layer 3: 类别级公共关键代码**
- **§4 常见陷阱**（按算子分小节）
本类单算子：**Index/Gather** / **IndexPut/Scatter** / **EmbeddingDenseBackward** / **Sort/TopK**，其专属 Layer 1 约束见下方「算子级实现手册」。

---

## 本类别的算子级实现手册

> 本卡只列类别级共性约束。以下单算子手册含该算子专属的 Layer 1 设计约束、
> 算法骨架与性能基准，**命中对应算子时必须一并加载**。

- [`operators/index_computation__embeddingdensebackward.md`](../operator_playbooks/index_computation__embeddingdensebackward.md) — EmbeddingDenseBackward 算子（index-accumulate）
- [`operators/index_computation__index_gather.md`](../operator_playbooks/index_computation__index_gather.md) — Index / Gather 算子（index-read）
- [`operators/index_computation__indexput_scatter.md`](../operator_playbooks/index_computation__indexput_scatter.md) — IndexPut / Scatter 算子（index-write）
- [`operators/index_computation__sort_topk.md`](../operator_playbooks/index_computation__sort_topk.md) — Sort / TopK 算子（index-sort）

## §0 适用范围与算子分类

| 算子 | 类别 | 计算特征 | 优化哲学 |
|------|------|---------|---------|
| Index / Gather | `index-read` | 根据索引从输入中收集元素，核心计算量低于访存/重排 | 维度特化 + UB 预载 + `tl.gather`；非 last-dim 评估转置 |
| IndexPut / Scatter | `index-write` | 根据索引向输出写入或原子累加，存在写冲突风险 | 并行轴与连续访问对齐 + 向量 `tl.atomic_add` + 冲突处理 |
| EmbeddingDenseBackward | `index-accumulate` | 按索引将梯度累加到 embedding 权重，尾维度宽且重复索引多 | 三阶段 kernel + 连续维向量 atomic + fp32 中间累加 |
| Sort / TopK | `index-sort` | 基于比较重排并返回索引 | 排序网络/分桶 + 向量比较原语 + 注意索引 dtype 对齐 |

> ⚠️ **关键区分**：本类别的核心优化哲学是 **按维度特化分派 + 向量化读写/原子**。Gather/Index 读取类走 **UB 预载 + `tl.gather`**，Scatter/IndexPut/EmbeddingDenseBackward 写入累加类走 **连续维向量 `tl.atomic_add`**，Sort/TopK 排序选择类走 **排序网络/分桶**。生成时**禁止混用**其他类别经验（如不要在 Scatter 里套用 Gather 的 UB preload 技巧）。

---

## §1 通用经验（跨算子，首次生成必须遵守）

以下约束是索引计算类算子**共有**且**未在其他 template 文件覆盖**的工程约束。其他文件已提取的通用约束（如 GC-1）此处不再重复，各算子章节引用时标注。

### G1 并行轴选择：与连续访问对齐，而非与最大 numel 对齐

- **必须**按算子语义选择并行轴，使内层访问沿 trailing/E/D 连续维度。
- **Gather/读取类**：优先沿 `outer`（输出张量的外层维度）和 `index_len` 并行；每个 program 负责一条或多条 `(o, k)`，沿 `trailing` 连续读取/写入。
- **Scatter/写入类**：
  - 若 `trailing`/`E` 较短且索引重复可控：按 `outer * index_len` 并行，每个 program 写入一段连续输出位置（输出位置并行）。
  - 若 `trailing`/`E` 很宽（如 `E ≥ 128`）：按 `index`/`N` 分块并行，每个 program 对连续 `E` 维做**向量 atomic_add**。
- 当 `index_len` 很小但 `outer * trailing` 很大时，启用 **tile-based** 扩展，用 2D grid 占满 vector cores。
- **Why:** 索引算子核心计算量低于访存/重排，并行轴若不与连续访问对齐，会引入离散全局访问和原子竞争，性能通常跌至 0.1x 以下。

### G2 向量化读写与 Coalesced Memory Access

- **必须**对 `trailing`/`E`/`D` 连续维度，使用 `tl.arange(0, BLOCK)` + mask 进行向量 `tl.load`/`tl.store`。
- **必须**对索引张量本身也按 `BLOCK_M` 向量加载：`tl.load(index_ptr + offs, mask=mask).to(tl.int32)`。
- **Gather 中**，若索引沿连续维度排列，优先一次加载一段索引并配合硬件 gather；否则确保 indirect load 的目标地址尽可能连续。
- **Why:** 标量加载索引或标量 atomic 会破坏 SIMD，原子操作数量与元素数量相同，典型加速比从 0.3x~0.6x 跌至 0.05x~0.15x。

### G3 维度特化与 `tl.constexpr` 分发

- **必须**在 `ndim ≤ 4` 时，在 **host 侧**按 `dim=0/1/2/3` 启动独立 kernel 实例，将 `DIM`/`NDIM` 作为 `tl.constexpr` 传入。
- **禁止**在 kernel 内用运行时 `for j in range(NDIM)` 解码坐标，或在 kernel 内保留运行时 `if dim == X` 分支。
- **Why:** 运行时坐标解码会引入大量标量除法/取模、非合并访存，且无法使用 UB gather，典型加速比仅 0.05x~0.2x。
- **How to apply:** 见 Index/Gather 算子级手册 §2.1 L1.1、IndexPut/Scatter 算子级手册 §3.1 L1.3、EmbeddingDenseBackward 算子级手册 §4.1 L1.2。

### G4 索引/偏移数据类型

- **必须**将索引值尽快转换为 `tl.int32`：`.to(tl.int32)`。
- **必须**在计算最终全局地址时，对可能溢出的扁平偏移使用 `tl.int64`（如 `base + batch_offset * stride`）。
- **禁止**在标量上做 `.to(tl.int64)` 或在 int64 上做 `%`；需要取模时改用 `idx - (idx // M) * M`。
- **Why:** int64 标量会触发地址计算降级；NPU 上 int32 索引更高效，但扁平偏移可能溢出需用 int64。

### G5 原子操作粒度

- **必须**在连续输出段 `E ≥ 64/128` 时使用向量 `tl.atomic_add(ptr + arange, vals, mask=...)`。
- **禁止**把 `tl.atomic_add` 放在 `for j in range(BLOCK_E)` 标量循环里，或用 `tl.get_element(..., [j])` 拆成标量后再 atomic_add。
- **Why:** 向量 atomic 一次覆盖多个连续元素，原子数下降 1~2 个数量级；拆成标量会破坏 SIMD 并爆炸原子数。
- **How to apply:** 见 IndexPut/Scatter 算子级手册 §3.1 L1.2、EmbeddingDenseBackward 算子级手册 §4.1 L1.1。

### G6 精度保持

- **必须**在 fp16/bf16 累加场景，分配 `torch.float32` 中间 buffer 进行 `atomic_add`，最后 cast 回原始 dtype。
- **必须**在涉及 `scale_grad_by_freq` 等加权累加时，先用独立 O(N) 频数 kernel 统计，主 kernel 查表缩放，禁止二次扫描。
- **Why:** fp16/bf16 `atomic_add` 直接累加会导致精度下降；频数统计与主累加分拆避免热循环内分支。
- **How to apply:** 见 EmbeddingDenseBackward 算子级手册 §4.1 L1.3。

### G7 Host 侧与拷贝

- **必须**避免 `x.contiguous()`、`permute().reshape()` 等隐式拷贝；如必须转置，估算收益 `gather_gain > 2 × transpose_cost` 才执行。
- **必须**将所有传入 Triton kernel 的可选张量实例化为合法 dummy tensor，禁止传 `None`。
- **必须**将排除位置（如 `padding_idx`）清零、边界修正等作为**独立轻量 kernel**，不在热 scatter 循环内分支。
- **Why:** 隐式拷贝可能抵消 gather 收益；`None` 指针会导致 JIT 签名错误；热循环内分支破坏向量化。

### G8 GPU-source 迁移到 Ascend NPU 的 memory/index 改造检查清单

当参考代码来自 GPU/CUDA Triton 实现时，必须在生成 Ascend NPU 版本前完成以下迁移检查。这些项是**强制前置条件**，不应在 Phase 3/Phase 4 中才被修复。

| 检查项 | 迁移规则 | 反例（必须避免） |
|--------|----------|------------------|
| 设备与启动配置 | `cuda` → `npu`；移除 `num_warps`、`num_stages`、`cache_modifier`、`evict_last` 等 GPU-only 启动选项。 | `triton.Config({}, num_warps=4, num_stages=2)`、`tl.load(..., cache_modifier='.cg')` |
| `tl.load`/`tl.store` 参数 | 禁用 GPU-only 参数；明确指定 `care_padding=False` 当且仅当访问不越界，避免默认 padding 带来额外拷贝。 | 保留 `boundary_check`、`padding_option` 等 CUDA 参数 |
| 索引数据类型 | 索引张量进入 Vector 路径前统一转为 `tl.int32`；全局扁平偏移按需使用 `tl.int64`。禁用 `fp64`、`uint` 类型。 | 用 `int64` 索引做数组下标、在 kernel 内保留 `torch.int64` |
| 累加数据类型 | fp16/bf16 scatter/accumulate 必须分配 `torch.float32` 中间 buffer，最后 cast 回原始 dtype。 | 直接用 `tl.atomic_add` 累加 fp16/bf16 输出 |
| Block Pointer / 转置 | **禁止**通过交换 stride 实现 transpose；使用 `order=(...)` 或显式 host 侧 `permute().contiguous()`。 | `x_ptr + col * stride[1] + row * stride[0]` 假装二维连续 |
| Memory 布局决策 | 转置收益必须大于 2× 拷贝成本：`gather_gain ≈ saved_strided_loads × memory_latency`，`transpose_cost ≈ 2 × tensor.numel() × elem_bytes / copy_bw`。 | 无条件 `.contiguous()` 或 `.movedim(...).contiguous()` |
| Atomic 操作迁移 | 连续输出段优先向量 `tl.atomic_add(ptr + tl.arange(0, BLOCK_E), vals, mask=...)`；标量 atomic 仅作为不连续/冲突密集 fallback。 | `for e in range(BLOCK_E): tl.atomic_add(...)` |
| UB 容量与 tiling | UB preload 尺寸 `ROW_SIZE` 必须小于 UB 容量上限（fp32 约 32768 元素）；过大时分块为 `BLOCK_*` + `BLOCK_*_SUB`。 | 一次性预载整行但 `dim_size > UB_LIMIT` 导致 spilling |

> **判定口诀**：GPU 代码迁移后，若 kernel 内仍出现 `num_warps`、`cache_modifier`、int64 索引下标、stride 欺骗 transpose、或标量 atomic 内层循环，则迁移未完成。

### G9 语义正确性

- **必须**在 `accumulate=False` 且存在重复索引时，实现 **last-write-wins**（单 block 串行或两阶段）。
- **必须**覆盖边界检查：`index < 0`、`index >= dim_size`、`padding_idx` 等情况；越界读返回 0，越界写加 mask。
- **必须**将排除位置（padding_idx 等）通过独立后置 kernel 清零，不在热循环内判断。
- **Why:** 缺少写冲突处理会导致结果不稳定；越界访问触发 ACL 错误；热循环内判断破坏性能。

### G10 Autotune 与调试

- **必须**在累加/原地修改算子 autotune 时，每次重新 clone/初始化输出 buffer，或关闭 autotune。
- **必须**以目标维度（如 `K`、`E`、`D`）作为 autotune key，避免无关维度导致 config 错配。
- **出现 ACL 507035 时**优先检查是否未使用 UB/gather 或运行时 dim 分支。
- **Why:** 原地修改算子在 autotune 时重复累加同一 buffer，会导致结果错误且性能失真。

### G11 Grid 与并行规模

- **必须**根据实际 tile 数量计算 grid，配合 kernel 内 `for b in tl.range(pid, total, num_programs)` 做 strided 遍历。
- **必须**保证 1D grid 硬上限 **65535**；超出时使用 2D grid 或增大 BLOCK。
- **必须**让 BLOCK 大小取 `next_pow2_geq(dim)` 且不超过实际维度；避免 `BLOCK=256` 等固定大 block 在单 program 中循环过多而超时。
- **Why:** `grid = (min(num_cores, total_blocks),)` 后直接退出会浪费并行度；1D grid 超限导致启动失败；BLOCK 过大触发 Vector Core timeout（507034）。

---

## §2 Layer 2: 类别级通用算法骨架（跨算子抽象，首次生成就要写对）

索引计算类算子按**读/写/排序**三分，共享「**并行轴对齐连续维 + 向量化读写/原子 + 维度 constexpr 特化**」的类别级模板。子类分道：
**读类**（Index/Gather：UB 预载 + `tl.gather`）、**写累加类**（IndexPut/Scatter/EmbeddingDenseBackward：连续维向量 `atomic_add` + fp32 中间缓冲）、**排序选择类**（Sort/TopK/LightningIndexer：排序网络 + 选位结构）。
逐算子 L2 变体见各算子 `operator_playbooks`（Index/Gather、IndexPut/Scatter、EmbeddingDenseBackward、Sort/TopK）。

### L2.1 并行轴选择（G1：与连续访问对齐，非与最大 numel）
- **读类**：沿 `outer`（输出外层）+ `index_len` 并行，每 program 沿 `trailing` 连续读写。
- **写累加类**：`trailing/E` 短 → 按 `outer*index_len` 并行（输出位置并行）；`E ≥ 128` 宽 → 按 `index/N` 分块并行，每 program 对连续 E 维向量 atomic。
- `index_len` 很小而 `outer*trailing` 很大时，用 2D grid 占满 vector cores。

### L2.2 kernel 骨架：向量 index load + 连续维 SIMD
```python
offs = tl.arange(0, BLOCK_M); mask = offs < index_len
idx  = tl.load(index_ptr + offs, mask=mask, other=0).to(tl.int32)   # 索引向量化 load（G2/G4）
# 读类：沿非 last-dim 时评估转置；last-dim 用 UB 预载 ROW_SIZE(<UB) 后 tl.gather
# 写累加类：连续 E 维向量 atomic
tl.atomic_add(out_ptr + base + tl.arange(0, BLOCK_E), vals, mask=e_mask)
```

### L2.3 维度特化分发（G3：dim 作 constexpr）
- `ndim ≤ 4` 时 host 侧按 `dim=0/1/2/3` 启动独立 kernel，`DIM/NDIM` 传 `tl.constexpr`。
- **禁止** kernel 内运行时 `for j in range(NDIM)` 解码坐标或 `if dim == X` 分支（引入标量除/取模、非合并访存）。

### L2.4 顺序结构（NMS 类顺序算法同理：勿全 kernel 化）
- 需要跨 program 相关状态、有 host 依赖的 index-ordered 算子，保留 host 侧主循环 + device-side 计数，勿强塞单 kernel。

---

## §3 Layer 3: 类别级公共关键代码 / 技巧（可参考但不可复制结构）

### L3.1 向量 atomic 替代标量循环（G5，写累加类核心）
```python
# E ≥ 64/128 连续输出段：向量 atomic（原子数降 1-2 数量级）
tl.atomic_add(out_ptr + base + tl.arange(0, BLOCK_E), vals, mask=e_mask)
# 禁止在 for j in range(BLOCK_E) 内逐元素 scalr atomic 或 get_element + atomic_add
```
### L3.2 fp32 中间缓冲保精度（G6）
```python
acc = torch.zeros(..., dtype=torch.float32, device=x.device)  # fp16/bf16 累加用 fp32
... tl.atomic_add(acc_ptr + ..., vals) ...                     # 最后 cast 回原始 dtype
```
- `scale_grad_by_freq` 等加权：独立 O(N) 频数 kernel 统计 → 主 kernel 查表缩放，禁二次扫描。

### L3.3 索引扁平偏移用 int64、取模用减法（G4）
```python
base = batch_offset * StrideB.to(tl.int64) + row*Stride + idx.to(tl.int32)  # 扁平偏移防溢出
mod = x - (x // M) * M                                     # 禁 int64 上 %
```
### L3.4 边界/冲突处理为独立轻量 kernel（G9/G7）
- `accumulate=False` + 重复索引 → last-write-wins（单 block 串行或两阶段）；越界读返 0、越界写加 mask。
- `padding_idx` 排除位置用**独立后置 kernel** 清零，禁热循环内分支；可选 dummy tensor 替 `None` 指针。
### L3.5 GPU 迁移检查口诀（G8）
- kernel 内仍现 `num_warps`/`cache_modifier`、int64 下标、stride 欺骗 transpose、标量 atomic 内层循环 → **迁移未完成**。

---

## §4 常见陷阱与避免方法

### §4.1 Index / Gather 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| Kernel 内运行时判断 `dim` | `if dim == 0:` 运行时变量 | Host 侧 `DIM=0` 作为 `tl.constexpr` 启动（Index/Gather 算子级手册 §2.1 L1.1） |
| Gather 用输入 shape 做循环边界 | `M = x.shape[:dim].prod()` | `M = index.shape[:dim].prod()`（Index/Gather 算子级手册 §2.1 L1.3） |
| 直接间接 gather 当作默认路径 | 所有 gather 都用 `x_ptr + idx_vals * stride` | 优先 UB preload + `tl.gather`，direct-indirect 仅 fallback（Index/Gather 算子级手册 §2.1 L1.2） |
| UB 预载尺寸超过容量 | 预载整行 `tl.load(x_ptr + row * dim_size + arange(0, dim_size))` 且 `dim_size > UB_LIMIT` | 先校验 `ROW_SIZE ≤ UB_LIMIT`，过大则分 `BLOCK_*` + `BLOCK_*_SUB`（Index/Gather 算子级手册 §2.1 L1.4） |
| 无条件 host 侧转置 | 未估算收益就 `.contiguous()` | 仅在 `gather_gain > 2 × transpose_cost` 时转置（Index/Gather 算子级手册 §2.1 L1.5） |

### §4.2 IndexPut / Scatter 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 标量 atomic 内层循环 | 所有 scatter 都用标量 | 连续宽维度用向量 atomic（IndexPut/Scatter 算子级手册 §3.1 L1.1） |
| 运行时 ND 坐标解码 | `for j in range(NDIM)` 从 global buffer 读 shape/stride | `ndim ≤ 4` 编译期维度特化（IndexPut/Scatter 算子级手册 §3.1 L1.3） |
| `accumulate=False` 重复索引结果不稳定 | 多个 source 写入同一 target，顺序随机 | 实现 last-write-wins（IndexPut/Scatter 算子级手册 §3.1 L1.4） |
| 在热 scatter 循环内判断 padding | `if idx != padding_idx:` 每个元素 | 后置独立 zero kernel（IndexPut/Scatter 算子级手册 §3.1 L1.5） |
| 忽略索引越界 | 直接 `tl.load(x_ptr + idx * stride)` | 加 mask 与 `other=0`，必要时过滤（IndexPut/Scatter 算子级手册 §3.1 L1.5） |

### §4.3 EmbeddingDenseBackward 陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 单 kernel 双重循环 | 对 `N` 和 `E` 做双重标量循环 | 拆分为 freq / scatter-add / padding-zero 三个 kernel（EmbeddingDenseBackward 算子级手册 §4.1 L1.1） |
| 向量 load 后拆标量 atomic | 用 `tl.get_element(..., [j])` 拆后再 `tl.atomic_add` | 直接构造向量地址并调用向量 `tl.atomic_add`（EmbeddingDenseBackward 算子级手册 §4.1 L1.2） |
| fp16/bf16 直接累加 | `tl.atomic_add` 累加 fp16/bf16 输出 | 分配 fp32 workspace，最后 cast 回原始 dtype（EmbeddingDenseBackward 算子级手册 §4.1 L1.3） |
| `padding_idx` 在热循环内清零 | 每个元素判断 `idx != padding_idx` | 独立 `padding_zero_kernel`（EmbeddingDenseBackward 算子级手册 §4.1 L1.5） |

### §4.4 通用跨算子陷阱

| 陷阱 | 原因 | 避免方法 |
|------|------|---------|
| 向 `tl.atomic_add` 传 `None` | `freq_ptr=None` | 传合法 dummy tensor（§1 G7） |
| Autotune 复用累加 buffer | 同一 buffer 被多 config 累加 | 每次重新初始化或禁用 autotune（§1 G10） |
| GPU 源代码保留 cuda-only 启动参数 | 保留 `num_warps`/`num_stages`/`cache_modifier` | 完全移除；Ascend 只保留 `BLOCK_*`（§1 G8） |
| GPU 源通过 stride 交换实现 transpose | `ptr + col * stride[1] + row * stride[0]` | 使用 `order=(...)` 或显式 host 侧 `permute().contiguous()`（§1 G8） |
| `int64` 索引未降级为 `int32` | 用 `int64` 做下标或保留 `torch.int64` 进 kernel | Vector 路径前 `.to(tl.int32)`；扁平偏移按需用 `int64`（§1 G4） |
| 1D grid 超过 65535 | `grid = (total_blocks,)` | 使用 2D grid 或增大 BLOCK（§1 G11） |
