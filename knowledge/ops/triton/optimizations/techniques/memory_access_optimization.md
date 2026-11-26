---
type: Optimization
title: 内存访问优化
description: Triton Ascend 内存访问优化：连续访问、Block Pointer、对齐、Cache 复用与软件流水线策略。
tags: [task.optimization, topic.data_movement.memory_access, topic.data_movement, topic.alignment, topic.implementation.pipeline]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Memory_Pointer_Ops/tl.load.md
  role: primary
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-09-08T09:05:00Z'
platforms: [a2, a3, '950']
---
# 内存访问优化

HBM→UB 带宽优化策略，覆盖对齐、连续访问、block_ptr、cache 复用和软件流水线。

## OPT-triton-mem-001: 连续内存访问优先

避免 stride 跳跃访问导致 cache miss 率 >50%：
- ✅ 一维连续 `ptr + pid*BLOCK + tl.arange(0, BLOCK)`
- ❌ 多维 stride 偏移产生离散地址

## OPT-triton-mem-002: 2D Block Pointer

使用 `tl.make_block_ptr` 替代手动指针计算：
```python
a_block_ptr = tl.make_block_ptr(
    base=a_ptr, shape=(M, K), strides=(stride_am, stride_ak),
    offsets=(pid_m*BLOCK_M, 0), block_shape=(BLOCK_M, BLOCK_K), order=(1, 0))
```
编译器可生成更优的地址计算指令。

## OPT-triton-mem-003: 512B 行宽对齐

matmul 的 BLOCK_N × dtype_bytes 必须是 512 的整数倍。fp16: BLOCK_N≥256。

## OPT-triton-mem-004: 转置 Load 优化

行优先 load + `tl.trans` 寄存器转置，消除转置访存开销。

## 实测：转置操作数的两种呈现（bf16，A5）

被 dot 消费的转置操作数有两种做法：物化一份转置副本，或用 `tl.make_block_ptr` 以 `strides=(1,N)` 直接呈现转置视图。

| 方案 | 平均 ms | TFLOPS |
|---|---|---|
| 物化 `B^T`（同规模 `[N,K]`，单次 copy 0.556 ms） | 10.10 | 136.0 |
| `make_block_ptr` 转置视图（`strides=(1,N)`，`order=(0,1)`） | 8.72 | 157.6 |

- 视图方案省掉一次 copy 与一份同规模 `[N,K]` bf16 缓冲，端到端 **−13.7%**，relerr 不变（4.0e-3）；省下的时间大于 copy 本身，因为 copy 还要整块写回再读。
- **不是无条件更优**：同一视图在 `one program per tile` 的大 grid 下反而更慢（12.01 vs 物化 9.81 ms），与 grid 形态强相关，落地要连同 grid 一起对比。
- 适用前提：转置轴两维都是规则 stride（`strides=(1,N)` 这种可表达的形式）；数据相关 gather 不适用。

## OPT-triton-mem-006: 索引保持 affine 形式

对行/列索引做 `tl.where`（如尾块掩码把越界行映射到 0）会让地址生成退化为逐元素计算，DMA 效率明显下降。
做法：把 M 维 padding 到 tile 的整数倍、用 `m0 + rows` 的仿射基址推进，再对越界通道用 mask 处理数据而不是
改写索引；仅在确实无法 padding 时才用 `tl.where` 生成索引。
本案例（Ascend950PR、28 核、bf16 GEMM）把 `mrs = tl.where(rmask, rm, 0)` 改成 `mrs = rm` 后，dense/gh 两个
phase 的 cube 吞吐明显回升；具体数值随 shape 与 tile 变化，不作为通用阈值。

## OPT-triton-mem-005: 跨阶段寄存器复用

barrier 前后重复加载同一数据 → 寄存器复用消除重复 load。

