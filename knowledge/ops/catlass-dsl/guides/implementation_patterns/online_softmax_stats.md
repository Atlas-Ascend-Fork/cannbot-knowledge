---
type: Guide
title: "在线 softmax 的统计量递推"
description: "逐块更新 running max 与 running sum，并正确处理 rescale、尾块掩码与缩放顺序。"
tags: [task.implementation, topic.compute.reduction, topic.precision, topic.attention]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/core_api.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/flash_attention_infer/stage_rescale.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/flash_attention_infer/stage_softmax.py
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-10-28T00:00:00Z'
platforms: ['950']
---
# 在线 softmax 的统计量递推

## 接口与概念

按列分块计算时，softmax 不能等所有块到齐再算，需要在线维护每行的 running max
`M` 与 running sum `S`。每来一块：

```text
tile_max = max(块内元素)
new_max  = max(old_max, tile_max)
tile_sum = sum(exp(x - new_max))
new_sum  = tile_sum + old_sum * exp(old_max - new_max)
```

最后输出归一化结果时只用 `old_sum` 与最终的 max。

## 用法

单遍写法（每块先求块 max，再求块 sum）：

```python
mx = low
for c in range(BN // 64):
    xb = tile_view(x, shape(1, 64), coord(rr, c)).load()
    mx = tla.max(mx, tla.where(active(c), tla.mul(xb, inv_t), low))
tile_max = mx.reduce(tla.ReductionOp.MAX, mask=full)      # 归约成单 lane fragment
new_max  = tla.max(old_max, tla.full(tile_max, tla.Float32))  # 广播回 64 lane

sv = zero
for c in range(BN // 64):
    sb = tile_view(x, shape(1, 64), coord(rr, c)).load()
    ev = tla.exp(tla.sub(tla.mul(sb, inv_t), new_max))
    sv = tla.add(sv, tla.where(active(c), ev, zero))
tile_sum = sv.reduce(tla.ReductionOp.ADD, mask=full)      # 关键：逐 lane 累加后必须归约
new_sum  = tla.add(
    tla.full(tile_sum, tla.Float32),
    tla.mul(old_sum, tla.exp(tla.sub(old_max, new_max))),
)
```

`sv` 是逐 lane 累加的向量，`reduce` 之后才是当前块的行和；漏掉 `reduce` 时
`new_sum` 仍是 64 lane 向量，后续按标量使用会得到错误结果。`active(c)` 是第 `c`
个 64 分片的有效 lane 掩码，`full` 是全 lane 掩码。

两遍写法（先全块求 max，再全块求 exp 和）语义相同，寄存器压力更低。

## 代码模式

统计量的存放方式见 `ub_stats_packing`；广播读取用 `DIST_BRC_B32`。

## 约束

- **缩放（乘以 1/T）必须在求 max 之前**，否则 max 与 sum 不同基准。
- 越界 lane 必须掩成 `-inf`（求 max）或 `0`（求和），不能留脏数据。
- 初始 `old_max = -inf`、`old_sum = 0`；首次 `exp(old_max - new_max)` 会得到 0，语义正确。
- `reduce` 返回的是**单 lane fragment**，与 64 lane 向量运算前必须 `tla.full(...)` 广播；
  直接把它当满宽向量参与 `tla.max`/`tla.add` 会报 lane 数不匹配。
- 若原始 tile 是 bf16 输出，缩放前的舍入必须与 GEMM 一致（见 `bf16_ties_to_even`）。

## 失败表现

- 忘记 rescale `old_sum`：sum 偏大，log-prob 偏小且随块数增长。
- 未掩尾块：max 被脏数据抬高，sum 出现 NaN 或 inf。
- 缩放放在 max 之后：max 与 sum 基准不一致，结果系统性偏移。

## 验证方法

与 host 侧 fp32 全量 softmax 对拍，重点看块边界（第 1、2、最后一块）；
用极端输入（全相同值、含 ±inf）验证掩码。

[^api]: 固定提交的归约与向量运算实现。
