---
type: API
title: SGL归一化后BF16激活乘FP32门值接口
description: 保留 gate_multiply 的独立sigmoid、精确dtype边界、910C融合阈值和非连续退回表达式路径。
tags:
- task.implementation
- topic.precision
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/gate_multiply.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/gate_multiply.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/elementwise/gate_multiply.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/utils/registry.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T04:38:09Z'
platforms:
- a2
- a3
aliases:
- gate_multiply
---

# SGL归一化后BF16激活乘FP32门值接口

## 调用入口

```python
from sgl_kernel_npu.operators.elementwise import gate_multiply

def gate_multiply(y, gate, *, impl="auto"):
    ...
```

## 精确语义

输入y为NPU BF16、gate为同NPU同shape FP32，均不要求梯度。计算 `(y.float()*gate).to(y.dtype)`，返回同shape的新BF16输出，不改输入。gate必须已由调用方计算sigmoid；这里不融合归一化、不近似sigmoid，也不替换swish-gated LayerNorm。

公共层在启动前检查dtype、设备、shape及无梯度要求，不符ValueError。auto与triton同入口，选择失败不切其他实现。

## 融合门槛和范围

固定实现仅按连续性和元素数选择：连续且元素数>=16,777,216时尝试融合 Triton kernel，较小或非连续输入使用同一 PyTorch 表达式；没有 arch35 判断。API 文档称 arch35 保持表达式，但注册支持集省略表示全部已知代际，故 arch35 连续大输入也会尝试融合，能否成功执行未验证；需要确定采用表达式时应显式选 torch_native。融合阈值在A3/910C测得，不是所有NPU通用收益阈值。上游arch35融合路径标未验证，本卡平台范围限定arch22，不据其参考运算能运行声称950融合收益。

运行元素数不参与kernel specialization；图捕获前仍需对目标shape/kernel预热。显式torch_native是独立表达式参考。验证要求有限值逐位相同，NaN位置另比，并检查已完成的BF16归一化舍入被保留；不能把输入提升提前到归一化之前。

## 固定来源与验证状态

- [elementwise/gate_multiply.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/gate_multiply.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
