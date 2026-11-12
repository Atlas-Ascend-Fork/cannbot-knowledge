---
type: API
title: SGL sigmoid 门控的逐元素与逐行广播接口
description: 区分 fused_sigmoid_mul 与 broadcast 变体的形状、混合精度、连续化和新输出约定。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/fused_sigmoid_mul.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/fused_sigmoid_mul_broadcast.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-08T11:03:33Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_sigmoid_mul
- fused_sigmoid_mul_broadcast
---

# SGL sigmoid 门控的逐元素与逐行广播接口

## 调用入口

```python
from sgl_kernel_npu.operators.activation import fused_sigmoid_mul

def fused_sigmoid_mul(x, gate, *, impl="auto"):
    ...

from sgl_kernel_npu.operators.activation import fused_sigmoid_mul_broadcast

def fused_sigmoid_mul_broadcast(x, gate, *, impl="auto"):
    ...
```

## 语义与选择

两接口都计算 `x * sigmoid(gate)`，先将两个操作数提升到 FP32，最后转回 `x.dtype`。逐元素接口要求形状完全相同；broadcast 接口把每行一个 logit 广播到该行全部通道。它们不会替调用方计算其他门控函数。

| 接口 | 输入 | 输出及差别 |
| --- | --- | --- |
| `fused_sigmoid_mul` | `x` 为任意 shape，含标量和空张量；`gate.shape == x.shape` | 同 shape、同 dtype；允许两个输入的浮点 dtype 不同。 |
| `fused_sigmoid_mul_broadcast` | `x: [N,D]`，`gate: [N]` 或 `[N,1]`；`N,D > 0` | `[N,D]`；gate 的 dtype 与 x 相同。 |

输入为同一 NPU 上的 strided FP16、BF16 或 FP32 Tensor，可传非连续视图。Triton 会连续化输入并返回连续输出；参考实现的输出布局由 PyTorch 决定。两接口均不改输入，分配新输出。

## 分发、边界与验证

`impl` 可选 auto、triton、torch_native；auto 对应 Triton，执行失败不触发回退。形状不兼容会报 ValueError，dtype、设备和布局不是每次都显式检查，调用方须满足约定。当前 NPU 应与输入设备一致。

对同一有限输入显式调用 torch_native 做容差比较；gate 全零时应得到 x/2。分别检查标量/空输入和逐行两种 gate 形状，不把 broadcast 接口误当任意 PyTorch 广播。

## 固定来源与验证状态

- [activation/fused_sigmoid_mul.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/fused_sigmoid_mul.md)
- [activation/fused_sigmoid_mul_broadcast.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/fused_sigmoid_mul_broadcast.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
