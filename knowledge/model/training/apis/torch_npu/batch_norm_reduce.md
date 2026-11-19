---
type: API
title: batch_norm_reduce：通道和、平方和与保留eps
description: 明确BatchNorm归约的双FP32输出、NCHW通道轴及未参与计算的必填eps，限定A2/A3。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-batch_norm_reduce.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-batch_norm_reduce.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNormReduceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNormReduceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormReduceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormReduceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T21:26:11Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# batch_norm_reduce：通道和、平方和与保留eps

## 固定版本与接口

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文接口页，产品仅A2/A3；发布dedc316708372c9a8bfde4527abd2a94b74840f5没有该公开页面，虽有同名实现和声明，不能据此补出发布产品/模式承诺。两个独立主线不视为配套发行。

```text
torch_npu.batch_norm_reduce(input, eps) -> (sum, square_sum)
```

input按公开页为4D NCHW、FP16/BF16/FP32；对每个通道跨N/H/W求元素和与平方和，两个输出都是一维(C,) FP32。它没有返回均值、方差、归一化数据或完成running statistics更新；后续若求统计量，还需样本数、正确归约域和相应数值约定。

eps是必填float，文档建议1e-5，但为保留参数，不参与sum/square_sum计算；两固定实现均未将它传给底层，不能通过调eps改变这两个结果。all_version声明是框架注册范围，不是950或任意rank的产品保证。

## 两条包装路径

ACL路径要求rank>1，通道取size(1)，将非FP32输入转FP32后交BNTrainingReduce；输出分配为FP32。OpAPI路径先检查aclnnBatchNormReduce兼容性，NHWC/NDHWC内部格式取末轴，否则取size(1)，同样转FP32并分配通道输出。内部NHWC/高rank分支不扩大公开NCHW四维合同，也不能只看内存连续性就改变逻辑通道轴。

## 核验

分别比对沿N/H/W的和及平方和，检查输出dtype/shape，区分浮点累加误差与归约域错误。批归约和分布式聚合是不同步骤。本卡仅静态审阅，未执行上游、设备、反向、编译或性能测试，未新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-batch_norm_reduce.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-batch_norm_reduce.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNormReduceKernelNpu.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNormReduceKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormReduceKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormReduceKernelNpuOpApi.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
