---
type: API
title: npu_dynamic_dual_level_mx_quant：512与32两级尺度
description: 说明FP4 E2M1的两级缩放、两种尺度存储及暂不支持的smooth_scale。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_dual_level_mx_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicDualLevelMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_dual_level_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicDualLevelMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_dual_level_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_dual_level_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:34:54Z'
updated_at: '2026-11-09T21:57:27Z'
platforms:
- '950'
---

# npu_dynamic_dual_level_mx_quant：512与32两级尺度

## 固定版本与范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的950产品页、同提交Schema、Meta及包装实现。仅描述明确分支，不回推其他产品或发布基线；未执行上游代码、图编译或真机实验。

## 接口

```text
npu_dynamic_dual_level_mx_quant(input, *, smooth_scale=None,
    round_mode='rint') -> (y, level0_scale, level1_scale)
```

输入rank1..7、FP16/BF16 ND，末轴为正偶数，不支持空、可非连续。只在末轴量化，其他轴合并处理；先每512元素生成FP32一级尺度，再对临时值每32元素生成E8M0二级尺度，最终输出FP4 E2M1。不能把它当作只有一份E8M0尺度的普通MX量化。

y实际UINT8、末轴减半，level0_scale为FP32、尾维ceil(N/512)，level1_scale为UINT8承载E8M0，末两维(ceil(ceil(N/32)/2),2)，组数偶数pad补0，其他前置维一致。解码和下游算子必须同时消费两级scale，不能只传二级。

smooth_scale当前未支持，保持None；round_mode允许rint/round/floor。产品页列训练/推理和单算子/图模式，不据签名添加其他目标dtype或任意块大小。


## 验证

先检查逻辑dtype与容器、分组边界、尺度布局及后端接口版本，再对照同算法量化/反量化结果，覆盖尾块和空组。性能比较分开记录编译、内存和稳态开销；静态Meta和包装分配不是设备结果。

## 两级计算与固定图路径

主线中英文仅950PR及950DT，训练/推理及单算子/图模式。先按尾轴每512值计算一级FP32尺度，并把归一化临时量cast回输入dtype，再按每32值计算二级共享指数尺度（E2M1的emax=2），最后转为FP4；两级顺序和中间舍入不能省掉后当同一量化参考。

两个固定包装都把块大小固定为512/32，smooth_scale虽被透传到ACLNN，公开页仍明确暂不支持，不能把“能传Tensor”作为启用平滑的依据。固定发布快照已有schema、Meta、包装及Converter而没有同名公开页，不补出发布产品支持。

两版TorchAir均接GE DynamicDualLevelMxQuant，一级scale描述FP32、二级E8M0，FP4经Reshape/Bitcast打包为UINT8。两版Meta以int(math.ceil(...))形成尺度维，静态一致不证明任意符号输入编译成功。公式未完整定义全零块、溢出及全部边界数值，本卡未据其生成未经核验的可执行参考。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_dual_level_mx_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicDualLevelMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_dual_level_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicDualLevelMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_dual_level_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_dual_level_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
