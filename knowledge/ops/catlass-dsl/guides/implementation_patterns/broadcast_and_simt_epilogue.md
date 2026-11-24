---
type: Guide
title: "广播加载与 SIMT 收尾"
description: "用 DIST_BRC_B32 做行广播，用 simt 模式的 thread_block_dim 处理非对齐标量写；混合 pattern 先按 UB 空间反推 tile 面积，再调旋钮。"
tags: [task.implementation, topic.data_movement, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/81da64bca9da5c782f6589541b967456d4fdc4c7/python/tla_dsl/catlass/core_api.py
created_at: '2026-10-23T12:00:00Z'
updated_at: '2026-11-23T00:00:00Z'
platforms: ['950']
verified:
- {by: "process:catlass-python-kernel-run-audit", at: '2026-10-23T12:00:00Z'}
---
# 广播加载与 SIMT 收尾


## 接口与概念

两类"不舒服"的访问各有专用手段：

1. **把 [N] 的统计量广播到 [N, M] 的每一行**：不必手工 interleave 展开，可用广播加载。
2. **输出行宽不是 32B 的整数倍时，逐行向量/MTE 写会报对齐错误**：
   例如 `[M, K+1]` 的 fp32 输出，K=128 时行宽 `129 × 4 = 516B`，`516 mod 32 = 4`，
   逐行跨步访问会触发
   `The address for VEC to access UB is not aligned`（errcode 340）或
   `The MTE non-atomic instruction address is not aligned`（errcode 80）。
   做法：**逐行结果用 SIMT 标量逐元素写**；行宽本就 32B 对齐的连续输出
   （如 `[M]` 的 local_max）才用 `tla.copy` 连续写。
   **UB 内的暂存缓冲同理**：`[rows, K+1]` 的 stride（516B）同样不允许向量访问，
   应把暂存建为 `[rows, K]`（K=128 → 512B = 16×32B，对齐），payload 的第 0 列与
   第 1..K 列分开处理。

## 用法

```python
# 广播
brc = tla.tile_view(stat_ub, tla.make_shape(1), tla.make_coord(i)).load(
    params=tla.params.NormalLoadParams(load_dist=tla.params.LoadDist.DIST_BRC_B32)
)

# SIMT 收尾
with tla.vec.func(mode="simt", thread_block_dim=128):
    tid, _, _ = tla.arch.thread_idx()
    nthreads, _, _ = tla.arch.thread_block_dim()
    for r in tla.range(tid, ROWS, nthreads):
        gm_out[row0 + r, 0] = sum_ub[r]
```

## 约束

- SIMT 区域的栈预算有限（实测出现 `stack object size exceeded vf stack size`），
  区域内不要捕获大张量或做深调用；复杂逻辑放在区域外。
- UB 指针必须在 SIMT 区域**内**构造为 tensor，捕获外部裸指针会报错。
- 广播加载只适用于"同值铺满一行"的语义，逐元素不同仍需向量运算。
- SIMT region 要求被访问的 buffer 是**静态 shape**；对输出张量用
  `mark_layout_dynamic` 会报 `requires statically shaped buffers`。
- UB 标量访问的基址必须直接来自 `tla.allocate` 返回的指针；先对 arena 指针做加减
  再标量访问会报 `tla.vec.func cannot outline scalar access`。

## 空间预算（先算这笔账，再调旋钮）

SIMD 段与 SIMT 段处理的是**同一块** tile，UB 剩余空间就是 tile 面积的上限；tile 面积又决定
搬运、广播、barrier、写回这些每块固定开销能摊到多少元素。该段吞吐明显低于向量占比应有的
水平时，先核空间账，再调算子细节：

- 每多一份整 tile 的中间缓冲，tile 面积就被钉低一档；同一块缓冲在多段之间复用，
  等于把面积上限抬高一档。
- 优先做不改算法的那件事：tile 内**原地复用**（读出 → 改写 → 写回同一块）。SIMT region
  要求静态 shape，省空间只能靠缩 buffer，不能靠动态 shape。
- 判定看 elem/core/cycle 而不是只看向量占比，且分子分母必须同口径：
  - 整段口径：`elem/core/cycle = 该段元素数 ÷（该段耗时 × 实际参与的物理核数 × 核频）`，
    或改用各核有效周期之和归一化；mixed kernel 要把 AIC 与 AIV 分开统计。
  - 单 block 口径：`该 block 元素数 ÷（该 block 耗时 × 1 核 × 核频）`。
  - launch 的逻辑 block 数不能代替物理核数：多波调度下逻辑块会在同一物理核上排队，
    例如 100 个逻辑块在 10 个核上分 10 波执行，用 block 数当分母会把每核吞吐低估 10 倍；
    仅调整 grid/task 粒度也会改变该指标，从而把"tile 太小"判断错。
  - 向量占比接近 1 但该值明显偏低，说明单块 tile 太小、固定开销摊不开，此时放大 tile
    比继续调算子细节更有效。
- 放大后仍要 fresh profile 复核：吞吐随面积增长通常次线性，固定开销占比降下来后瓶颈会切到
  别的管道，此时再按该管道的判据决定下一步。

## 收益参考

同一形状下把 `[M, K+1]` 的写回从"向量方式"改成 SIMT 标量逐元素写后，
该段写回耗时从约 **225 秒**降到约 **1 毫秒**（原先向量方式直接触发 errcode 340/80）。

接口行为以固定提交的实现为准。[^api]

[^api]: <https://gitcode.com/cann/catlass/blob/81da64bca9da5c782f6589541b967456d4fdc4c7/python/tla_dsl/catlass/core_api.py> 固定提交的源码与文档中对应实现。

## 代码模式

见上文 `NormalLoadParams(load_dist=DIST_BRC_B32)` 与 `vec.func(mode="simt", thread_block_dim=...)` 片段。

## 失败表现

- SIMT 区域报 `stack object size ... exceeded vf stack size`；
- 捕获外部 UB 裸指针报 "Buffers must be captured as tensors"。

## 验证方法

小 shape 下与 host 侧逐元素对拍；把区域内的复杂逻辑移到区域外后再测。
