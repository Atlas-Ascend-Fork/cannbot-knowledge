---
type: API
title: npu_add_rms_norm_v2：覆盖残差输入，仅返回 rstd
description: 说明 950 的双输入 mutation、RMSNorm 与残差写回位置，避免按旧版三输出接口接入。
tags:
- task.lookup
- topic.compute.normalization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T06:17:11Z'
updated_at: '2026-11-09T21:26:11Z'
platforms:
- '950'
---

# npu_add_rms_norm_v2：覆盖残差输入，仅返回 rstd

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口与原地语义

```text
torch_npu.npu_add_rms_norm_v2(x1, x2, gamma, epsilon=1e-6) -> Tensor
```

先得到z=x1+x2，再计算RMSNorm(z)。归一化结果覆盖x1，残差z覆盖x2；返回值是FP32的rstd中间量，不能当作y，也不能按旧npu_add_rms_norm解包三个输出。Schema分别标注Tensor(a!)与Tensor(b!)，图接入必须保留两个写回。

x1/x2/gamma为ND，FP16/BF16/FP32，不支持空Tensor；x1为1..8维，x2同shape，gamma匹配归一化尾维。Eager中三者dtype一致。rstd与x1同rank，被归一化维为1，例如(2,3,4,8)配gamma=(4,8)，rstd=(2,3,1,1)。epsilon默认1e-6。

产品表仅列950，支持单算子和TorchAir图模式；不能用普通AddRMSNorm的A2/A3范围扩大此v2接口。保留调用前独立输入参考，并检查x1、x2和rstd三个观察对象。

- [发布版非原地三输出接口](npu_add_rms_norm.md)


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练还需验证反向及保存的中间值。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## 两个固定实现的原地与functional分支

主线双语的产品范围为950PR及950DT，不扩到A2/A3；发布没有此公开页面。两固定实现都有npu_add_rms_norm_v2：以RMS helper分配一份FP32统计量，aclnnInplaceAddRmsNorm接收两个可写输入并仅返回该统计量。functional辅助先clone两个输入，再返回(rstd,x1_clone,x2_clone)，这是图变换需要的无原地表达，不改变公开原地接口的单返回合同。

公开页将统计量用标准差等文字描述有歧义；本卡按RMSNorm流程将其记作rstd，数值含义仍须与真实包对照，不能从变量名或分配逻辑作运行验证。源码存在于发布快照也不证明发布已公布950支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_v2.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
