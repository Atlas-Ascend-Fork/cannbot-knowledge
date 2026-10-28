---
type: Guide
title: "在 SIMD 中复现 bf16 的 ties-to-even 舍入"
description: "SIMD 的 f32→bf16 转换默认 round-half-away-from-zero，与 GEMM 的 round-half-to-even 不一致，需位运算仿真。"
tags: [task.implementation, topic.precision, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/catlass/core_api.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/vector_ops/bitcast_op.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/vector_ops/shift_op.py
- resource: https://gitcode.com/cann/catlass/blob/30a45e447824888ba97e089962064334c1d21163/python/tla_dsl/examples/end_to_end/vector_ops/bitwise_ops.py
created_at: '2026-10-26T00:00:00Z'
updated_at: '2026-10-27T00:00:00Z'
platforms: ['950']
---
# 在 SIMD 中复现 bf16 的 ties-to-even 舍入

## 接口与概念

矩阵乘法路径（ND2NZ / MMAD）对 bf16 采用 round-half-to-even，而 SIMD 的
`to(tla.BFloat16)` 默认是 round-half-away-from-zero。两者在 halfway 值上差 1 ULP，
当代码需要与 GEMM 的数值语义逐位对齐时（例如放大后再做在线统计），必须显式仿真。

## 用法

把 f32 按位解释为 i32，做一次"加偏置 + 奇偶校正"再掩码：

```python
with tla.vec.func(mode="simd"):
    bits    = x.bitcast(tla.Int32)                              # f32 位模式，零开销
    one     = tla.full(1, tla.Int32)
    bias    = tla.full(0x7FFF, tla.Int32)
    mask16  = tla.full(-65536, tla.Int32)
    parity  = tla.bitwise_and(tla.shift_right(bits, 16), one)    # 保留位的最低位
    rounded = tla.bitwise_and(
        tla.add(tla.add(bits, bias), parity), mask16)
```

`bitcast` 只改元素类型、不产生指令；`shift_right`/`bitwise_and` 的第二个操作数必须是
同宽向量，所以常量用 `tla.full(..., tla.Int32)` 铺满，而不是 Python 标量。

等价于 `(x + 0x7FFF + ((x >> 16) & 1)) & ~0xFFFF`。
应在按温度缩放**之前**做，保证后续统计基于与 GEMM 一致的数值。

## 代码模式

见上文片段；偏置 `0x7FFF` 与掩码 `-65536` 均通过 `tla.full(..., tla.Int32)` 生成同宽向量，
全程按 32 位整数处理。

## 约束

- 只适用于 f32→bf16；f16 的偏置与掩码位数不同。
- 依赖小端与 IEEE754 位序，不允许在打包/解包路径重复做。
- 会增加一段全 tile 的 SIMD 位运算，需评估对流水的影响。

## 失败表现

- 与 GEMM 结果存在 1 ULP 级差异，边界用例超差而主体通过。
- 若在缩放后补做，误差会被放大，看起来像"随机"偏差。

## 验证方法

构造 halfway 输入（如 `1 + 2^-9`），与 numpy 的 `round-half-to-even` 结果逐位比对；
再用同一 shape 与 GEMM 输出做 bitwise 比较。

接口行为以固定提交的实现为准。[^api]

[^api]: 固定提交的源码与文档中对应实现。
