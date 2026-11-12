---
type: Guide
title: SGLang Batch Invariant：外部算子包安装与懒加载依赖
description: 区分sgl-kernel-npu中的Python封装、外部CANN算子.run包与batch_invariant_ops扩展，说明arch22/arch35接口支持与目标平台安装边界。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-08T11:02:02Z'
platforms:
- a2
- a3
- '950'
aliases:
- batch_invariant_ops
- Batch Invariant
---

# SGLang Batch Invariant：外部算子包安装与懒加载依赖

## 两层外部依赖必须同时到位

`sgl_kernel_npu.operators.batch_invariant` 是外部 Batch Invariant 库的 Python 适配层，随包含该模块的新 wheel 发布，不内置对应外部 kernel。调用需要：一是提供 `aclnn*BatchInvariant` 的 CANN `.run` 算子包，二是注册 `torch.ops.batch_invariant_ops.*` 的 torch extension。只安装 sgl-kernel-npu 或只安装其中一项都不构成完整环境。

固定安装文档列出 910B、A3、Ascend 950 的 x86_64/aarch64 算子包；各接口文档另列 arch22/arch35 的 `batch_invariant_ops` 支持表。平台标签仅表示这些来源声明的对应范围，具体设备与 CPU 架构仍须匹配包，不能凭 2201 泛称选择任意产品。

## 安装顺序与库发现

1. 在目标设备环境安装匹配 `.run` 包，先查看该包 `--help`，再按其参数安装。
2. 加载实际 CANN 环境，并把 `opp/vendors/batch_invariant/op_api/lib` 加入运行 shell 的动态库路径。示例中的 CANN 9.1.0 目录需按实际环境调整，不能仅由路径证明版本兼容。
3. 解压外部 torch extension，在目标 Python 和 CPU 架构上编译/安装。来源要求 `torch_npu`、ninja、C++17 编译器及 Python 开发头文件，不能跨架构复制 wheel。
4. 用 `import batch_invariant_ops` 与 `torch.ops.batch_invariant_ops.npu_mm_batch_invariant` 检查扩展注册，再调用 sgl 封装验证实际 ACLNN kernel。

## 懒加载与 auto 的真实含义

封装第一次调用才导入 `batch_invariant_ops` 并缓存 `torch.ops` 对象；因此导入 `sgl_kernel_npu.operators.batch_invariant` 成功不能证明依赖已安装。`impl="auto"` 与 `impl="batch_invariant_ops"` 注册到同一个函数，缺依赖时不会自动回退其他 DSL 或普通 PyTorch 实现。

API 对输入多为直接转发，真正参数与算子可用性仍由外部实现检查；安装了错误芯片包可能到调用时才报 ACLNN 查找失败。

## 数值验收边界

批不变性是同一行/请求单独计算与作为更大 batch 一部分时的逐位一致性，不是要求不同算法/不同架构/任意 PyTorch 基线彼此逐位一致。先按[归约](../../../apis/sgl_kernel_npu/batch_invariants/sgl_batch_invariant_reductions.md)、[矩阵乘](../../../apis/sgl_kernel_npu/batch_invariants/sgl_batch_invariant_matmul.md)、[FIA](../../../apis/sgl_kernel_npu/batch_invariants/sgl_batch_invariant_attention.md)对应接口构造测试，并分别验证普通计算与图捕获所需符号。

本次未下载外部二进制或源码包，未执行安装、编译、数值、图捕获或性能测试；外部 kernel 实现不在当前 Git 快照内。

## Evidence

- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（primary）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/__init__.py)（implementation）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py)（implementation）
