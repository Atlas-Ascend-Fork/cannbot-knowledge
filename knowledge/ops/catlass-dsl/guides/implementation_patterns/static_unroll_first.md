---
type: Guide
title: "静态展开优先，动态循环只用于真正运行时边界"
description: "编译期常量用 Constexpr 形参 + Python range 展开；动态 trip count 循环里避免复杂 vec.func。"
tags: [task.implementation, topic.compilation, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/core_api.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/basic_mmad_streamk/basic_mmad_streamk.py
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-10-27T00:00:00Z'
platforms: ['950']
---
# 静态展开优先，动态循环只用于真正运行时边界

## 接口与概念

前端对动态控制流有明确限制：动态 `if` 内首次定义变量会被拒；动态循环的归纳变量在循环
结束后再次被读取会被拒；动态 trip count 循环体内的复杂 `vec.func` 在某些后端会下标/编译
失败。很多"编译不过"并不是 API 错，而是**把编译期常量写成了运行时值**。

## 用法

- tile 尺寸、段数、步长等编译期量，全部作为 `tla.Constexpr` 形参传入 `tla.compile`，
  在 kernel 里用 Python `range(...)` 展开，前端会静态展开。
- 只有真正依赖 tensor shape/运行时的循环才用 `tla.range(...)`。
- 动态 `if` 分支里需要的变量，用三元表达式在分支外先定义。
- 同一层多个动态循环不要复用同名归纳变量。

```python
## 编译期：静态展开
for c in range(N_CHUNKS):
    ...

## 运行时：动态循环
for v in tla.range(c0, num_v, c1):
    ...
```

## 约束

- 静态展开会增加编译时间与 IR 规模，段数很大时改用 `tla.range` 并简化循环体内的 vec 操作。
- 动态循环体内尽量只做单一 vec 操作，复杂逻辑拆到循环外的 stage 函数。

接口行为以固定提交的实现为准。[^api]

[^api]: 固定提交的源码与文档中对应实现。

## 代码模式

```python
@tla.kernel
def k(..., n_chunks: tla.Constexpr[int]):
    for c in range(n_chunks):        # 编译期展开
        ...
    for v in tla.range(0, num_v, 1): # 运行时循环
        ...
```

## 失败表现

- "动态 if 中首次定义变量被拒"；
- "归纳变量在循环后被再次读取"；
- "Unsupported scalar instruction in AIV loop"。

## 验证方法

先用 `dump_mlir`/编译校验前端是否通过，再上板跑最小 shape；
若动态循环报错，把循环体拆成单一 vec 操作或改成编译期展开。
