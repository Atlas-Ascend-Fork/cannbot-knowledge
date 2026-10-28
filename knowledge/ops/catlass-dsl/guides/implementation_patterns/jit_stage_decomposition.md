---
type: Guide
title: "用 @tla.jit 把 kernel 拆成可独立验证的 stage"
description: "把缩放/统计更新/收集/写回拆成 @tla.jit 函数，主 kernel 变短且每个 stage 可单独编译验证。"
tags: [task.implementation, topic.programming_model, topic.compilation]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/core_api.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/flash_attention_infer/stage_softmax.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/flash_attention_infer/stage_rescale.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/jit_callable/jit_callable_epilogue.py
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-10-27T00:00:00Z'
platforms: ['950']
---
# 用 @tla.jit 把 kernel 拆成可独立验证的 stage

## 接口与概念

把长 kernel 按职责拆成若干 `@tla.jit` 函数（如 `_stage_scale_rowmax`、
`_stage_max_update`、`_stage_exp_acc`、`_stage_gather`、`_stage_store_outputs`），
主 kernel 只保留数据流与同步骨架。这样每个 stage 都能单独编译、单独对拍，
也便于复用。

## 用法

```python
@tla.jit
def _stage_max_update(rowmax_ub, lastmax_ub, decay_ub):
    with tla.vec.func(mode="simd"):
        preg = tla.create_mask(pattern=tla.mask.ALL, dtype=tla.Float32)
        rm, lm = rowmax_ub.load(), lastmax_ub.load()
        nm = tla.max(rm, lm, mask=preg)
        lastmax_ub.store(nm, mask=preg)
        decay_ub.store(tla.exp(tla.sub(lm, nm, mask=preg), mask=preg))
```

主 kernel 内按顺序调用这些 stage，同步与 flag 仍集中在主 kernel 里。

## 代码模式

见上文；stage 只接收张量/标量形参，不读模块级状态。

## 约束

- stage 只读取形式参数与 `tla` API，不得捕获模块级 tile/shape/常数或闭包变量，
  否则主 kernel 的自由名字检查会失败。
- 同步原语（flag/barrier）建议留在主 kernel，stage 内只做纯向量/标量计算，降低耦合。
- stage 的 buffer 必须由调用方传入，避免每个 stage 各自 allocate 造成 UB 浪费。

## 失败表现

- stage 捕获外部变量：kernel 自包含检查失败（自由名字非空）。
- stage 内自行 allocate：UB 叠加超限，或同一缓冲被重复分配。
- 同步被拆进 stage：调用顺序变化时 flag 失衡，表现为死锁。

## 验证方法

先只编译不运行，确认前端通过；再逐个 stage 用小张量单独驱动，与 host 对拍。
这也是"骨架先行"里分阶段验证的落点。

[^api]: 固定提交的 jit 与 vec.func 实现。
