---
type: Guide
title: "单个 cross flag 的双向互斥用法"
description: "用一个 cross flag 在 CUBE 与 VECTOR 之间交替传递所有权，代替 ready/free 两个单向 flag。"
tags: [task.implementation, topic.implementation.synchronization, topic.programming_model]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/core_api.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/cross_flag_two_way/cross_flag_two_way.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/params.py
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-10-27T00:00:00Z'
platforms: ['950']
---
# 单个 cross flag 的双向互斥用法

## 接口与概念

缓冲在两核之间来回传递时，常见写法是一对单向 flag（ready / free）。另一种更省资源
的写法是**只用一个 cross flag，让所有权在两侧交替**：

    VECTOR 初始化 -> set
    FIX    等待 VECTOR 交接 -> 使用 -> set 交回
    VECTOR 等待 FIX 交接 -> 使用 -> set 交回

每次 set 都是一次"交棒"，wait 是"接棒"，因此不需要为两个方向各建一个 flag。

## 用法

```python
exchange = tla.cross_flag("exchange")
with tla.vector():
    tla.cross_core_set_flag(exchange, tla.arch.VECTOR)      # 开场放行

with tla.cube():
    tla.cross_core_wait_flag(exchange, tla.arch.FIX)        # 生产侧接棒
    tla.copy(ub_dst, l0c, tla.params.CopyL0C2DstParams(
        unit_flag=3, l0c2ub_mode=tla.params.L0C2UBMode.SPLIT_M))
    tla.cross_core_set_flag(exchange, tla.arch.FIX)         # 交棒

with tla.vector():
    tla.cross_core_wait_flag(exchange, tla.arch.VECTOR)     # 消费侧接棒
    # 消费 ub_dst ...
    tla.cross_core_set_flag(exchange, tla.arch.VECTOR)      # 用完交回
```

## 代码模式

见上文：开场由消费侧 set 一次，之后 set/wait 严格交替，任何一侧都不得连续两次 set。

## 约束

- set 与 wait 必须严格配对交替：多一次 set 会让对侧永不阻塞，少一次会死锁。
- `cross_core_set_flag`/`cross_core_wait_flag` 必须位于 `with tla.cube():` 或
  `with tla.vector():` 内（前端 `_require_enclosing_cube_or_vector` 会校验）；
  FIX 侧的等待、搬运、交棒进 `cube()`，VECTOR 侧的等待、消费、归还进 `vector()`。
- 两个执行引擎都必须各有一次 wait 与一次 set。
- 与按 aiv_id 定向的 flag 区别：本用法适用于"两个引擎独占同一缓冲"；若多个 AIV
  需要各自独立信号，仍应使用定向 flag。

## 失败表现

- 多 set / 少 wait：对侧提前读到未写完的数据，数值错乱但不报错。
- 少 set：对侧永久阻塞，表现为挂死或超时。

## 验证方法

把 set/wait 序列画成两列（FIX / VECTOR）逐行核对，确保每行只有一个动作且交替；
最小 shape 连跑两轮，确认第二轮不挂。

[^api]: 固定提交的 cross_flag 实现与方向语义。
