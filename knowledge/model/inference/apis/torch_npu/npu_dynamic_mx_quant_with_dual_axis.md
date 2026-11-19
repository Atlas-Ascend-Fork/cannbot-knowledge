---
type: API
title: npu_dynamic_mx_quant_with_dual_axis：两套量化结果与算法矩阵
description: 区分两轴独立32元素分组与32×32共享块，说明四输出、FP4打包和参数组合。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant_with_dual_axis.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicMxQuantWithDualAxisKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant_with_dual_axis.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicMxQuantWithDualAxisKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant_with_dual_axis.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant_with_dual_axis.py
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

# npu_dynamic_mx_quant_with_dual_axis：两套量化结果与算法矩阵

## 固定版本与范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的950产品页、同提交Schema、Meta及包装实现。仅描述明确分支，不回推其他产品或发布基线；未执行上游代码、图编译或真机实验。

## 接口与两轴语义

```text
npu_dynamic_mx_quant_with_dual_axis(input, *, round_mode='rint',
    dst_type=296, scale_alg=0, dst_type_max=0.0)
    -> (y1, mxscale1, y2, mxscale2)
```

在-1轴和-2轴各自每32元素求尺度，输出两份不同量化结果；它不是npu_dynamic_block_mx_quant用一个32×32尺度广播成两份。输入rank2..7、FP16/BF16 ND，可非连续，-2轴之前合轴处理。

FP8结果同input形状；FP4要求末轴偶数，两份y都以UINT8打包、末轴减半，即使y2按倒数第二轴量化也仍沿物理末轴打包。两份尺度均UINT8承载E8M0、rank+1、尾轴2，对(B,M,N)形状为(B,M,ceil(ceil(N/32)/2),2)和(B,ceil(ceil(M/32)/2),N,2)，scale2需两行交织。输出不支持非连续布局。

## 组合矩阵

FP8 E4M3FN/E5M2仅rint，可scale_alg=0（共享指数）或1（块尺度上取整），dst_type_max仅默认0。FP4 E1M2只算法0；FP4 E2M1可0或2，算法2才可dst_type_max=0或[6,12]，支持rint/floor/round。不是所有dtype都支持三个算法，参数值也不能从另一个MX接口复制。

文档列默认确定性、训练/推理及单算子/图模式；同提交Meta以符号整数运算推导双尺度形状，但这不是任意动态输入均可成图的运行证明。

包装层还探测aclnnDynamicMxQuantWithDualAxisV2，有V2才传dst_type_max；旧接口会对有值的该参数告警并忽略，不能把配置被接受当作已影响尺度。此处理与grouped_dynamic_mx_quant旧分支直接拒绝的规则不同。

- [32×32共享尺度的不同接口](npu_dynamic_block_mx_quant.md)


## 验证

先检查逻辑dtype与容器、分组边界、尺度布局及后端接口版本，再对照同算法量化/反量化结果，覆盖尾块和空组。性能比较分开记录编译、内存和稳态开销；静态Meta和包装分配不是设备结果。

## 950DT与双后端版本边界

主线中英文产品页明确仅Ascend950DT，未确认PR；默认确定性是来源声明，未由本次实测。图示例使用backend="npugraph_ex"、dynamic=False及fullgraph=True，不能把它直接当GE Converter的运行记录。

固定发布schema/包装/Converter只有四个输入属性，没有dst_type_max；发布Meta仅接受scale_alg=0。主线新增Optional幅度、Meta接受0/1/2，并用符号整数向上取整推导两个尺度维；这与发布的int(math.ceil(...))分开保留，不能把全部新算法回推旧图路径。

两个固定TorchAir Converter都有GE四输出和FP4重打包，主线才下传dst_type_max。两个y的物理打包都缩尾轴，按-2轴量化不意味着沿-2轴把输出物理长度减半。公开的合轴、两行交织和配对pad仍是消费者布局契约，转换器存在或Meta推导成功不保证所有组合已验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant_with_dual_axis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicMxQuantWithDualAxisKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant_with_dual_axis.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicMxQuantWithDualAxisKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant_with_dual_axis.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant_with_dual_axis.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
