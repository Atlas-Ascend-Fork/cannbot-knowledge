---
type: API
title: npu_deformable_conv2d：采样中间量、dtype和产品路径
description: 保留四元素步长/膨胀、offset通道数及950单算子模式，不当普通conv等价替换。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_deformable_conv2d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_deformable_conv2d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_deformable_conv2d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DeformableConv2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DeformableConv2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DeformableConv2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeformableConv2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeformableConv2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# npu_deformable_conv2d：采样中间量、dtype和产品路径

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## 采样和输出

接口接input、weight、offset、可空但必传的bias、kernel_size、stride、padding，默认dilation=[1,1,1,1]、groups=1、deformable_groups=1、modulated=True。发布原型把bias=None放在必传参数之前，不能复制为合法Python声明；两版schema bias均Tensor?且无默认值。

input为(N,Cin,H,W)，weight为(Cout,Cin/groups,Kh,Kw)。沿常规卷积采样坐标加offset后，四邻点双线性插值，再做带bias的卷积；不是只给普通Conv改stride。输出H=floor((H+padTop+padBottom-((Kh-1)*dilationH+1))/strideH)+1，W对应左右边界。

offset为(N,deformable_groups*Kh*Kw*(3或2),Hout,Wout)，modulated=True含mask用3，否则2。返回(conv_output,deformable_offset)：前者(N,Cout,Hout,Wout)，后者实际是采样特征(N,Cin,Hout*Kh,Wout*Kw)，不是把传入offset原样返回。该中间量会影响训练内存，不能按普通输出尺寸估算全部开销。

## 参数限制

input/weight/offset为4D、bias为1D Cout，格式NCHW/ND且匹配；不支持空Tensor，支持非连续。H*W中文允许到2147483647，英文写必须小于，边界值不据此承诺。kernel_size两个正整数、Kh*Kw<=2048、Kh*Kw*Cin/groups<=65535；stride/dilation各4个正整数，N/C两项必须1。padding按上、下、左、右四项，不是F.pad的尾轴顺序。groups>0整除Cin/Cout，deformable_groups>0整除Cin。

## 版本dtype与实现

A2/A3及旧Atlas路径将所有Tensor转FP32，输出FP32；ACL Op实际在采样前后显式NCHW/NHWC转置并修改临时描述，之后卷积用kernel_size作stride、零padding。不能因逻辑格式相同就声称没有转换或中间分配。

主线文档只允许单算子模式；950PR/DT另保留FP16/FP32/BF16同输入输出dtype且只modulated=True。OpAPI检查符号可用并仅ACLNN-only走该路线，其他回退ACL Op；注册存在不能回推发布硬件支持。主线新反向OpAPI分配input/weight/offset各自shape及Cout bias梯度，保留各自options，按同样条件选择或回退。没有本卡运行、性能或高阶梯度保证，本卡元数据保守按A2/A3消费。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_deformable_conv2d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_deformable_conv2d.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_deformable_conv2d.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DeformableConv2dKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DeformableConv2dKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DeformableConv2dKernelNpuOpApi.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeformableConv2dKernelNpuOpApi.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeformableConv2dBackwardKernelNpuOpApi.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
