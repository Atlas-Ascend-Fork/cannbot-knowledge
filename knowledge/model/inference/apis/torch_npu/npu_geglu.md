---
type: API
title: npu_geglu：双输出与待确认的平台契约
description: 记录主线 Schema、实现和旧文档签名差异；平台及发布支持尚未确认，保留草稿。
tags:
- task.lookup
- topic.compute.elementwise.activation
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeGluKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py
  role: constraint
created_at: '2026-11-09T02:09:29Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_geglu：双输出与待确认的平台契约

## 版本与证据状态

仅依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`。没有找到独立产品支持页，旧 docstring 只对 BF16 标注 A2，不能据此给整个接口指定通用平台。因此本卡为 draft，platforms 为空；不据此承诺发布版或设备可用。

## 已确认的接口事实

Schema 声明：`npu_geglu(Tensor self, int dim=-1, int approximate=1, bool activate_left=False) -> (Tensor, Tensor)`。旧 docstring 的签名遗漏 activate_left，调用应核对实际安装版本的 Schema。

C++ 实现沿 dim 将输出尺寸设为输入的一半，分配 result/result_gelu，调用 aclnnGeGluV3 并返回两个 Tensor；不是单 Tensor 接口。docstring 说明 approximate=0 对应 none、1 对应 tanh，输出 dtype 与输入一致。不能用整数除法的输出分配代码证明奇数轴长或标量输入合法，底层数值约束仍需核验。

## 使用前核验

先核对硬件、TorchNPU/OpPlugin/CANN 组合、真实 Schema、输入维度与偶数切分，再以相同 GELU 近似方式比较两个输出及 activate_left 的方向。源码测试的存在不等于本次实际执行；本次未运行上游代码或设备测试。

- [软件栈适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeGluKernelNpuOpApi.cpp)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py)（constraint）
