---
type: API
title: QuantConv2d模块：静态图量化卷积与预留参数差异
description: 保存NCHW、FP16输出与范围，区分文档预留、实际拒绝和源码扩展签名。
tags:
- task.lookup
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/quant_conv2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/quant_conv2d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000001855947305.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_image_0000001809304238.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/zh-cn_formulaimage_0000001855947305.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/zh-cn_image_0000001809304238.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/en-us_formulaimage_0000001855947305.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/en-us_image_0000001809304238.png
  role: constraint
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# QuantConv2d模块：静态图量化卷积与预留参数差异

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 文档调用与形状

`QuantConv2d(in_channels,out_channels,kernel_size,output_dtype,stride=1,padding=0,dilation=1,groups=1,bias=True,offset=False,offset_x=0,round_mode='rint',device=None,dtype=None)`。A2/A3训练/推理及旧Atlas推理卡，只支持静态图模式在线推理，output_dtype只FP16，groups只1；kernel 1..255、stride1..63、padding0..255、dilation1..255，int或二维tuple。旧Atlas输出W=1不支持，不扩到950。

输入和weight为4D INT8/NCHW；scale一维out_channels的FP32或INT64/ND，bias可选同长度INT32/ND。图片公式为Conv2d+反量化的简写`output=(fmap*weight+bias)*scale`，不能把*当所有元素逐点相乘；输出H/W按卷积尺寸公式及stride/padding/dilation判断。三版padding图均展示2×2全2输入、padding1和offset_x1后外围补1成4×4，offset_x是补充值而非量化权重offset。

## 实际包装与文档的边界

offset文档预留但实际构造True直接ValueError；round_mode虽称预留，包装实际存储并传底层，不能说所有值都会忽略。device/dtype未用于分配，weight/bias/scale为requires_grad=False的empty，需先装载有效量化参数。FP32 scale在forward临时trans_quant_param；不证明转换只做一次或scale任意整数即合法。

两固定实现还增加input_dtype/weight_dtype参数，docstring列BF16/FP32/hifloat8输出等更宽说明；当前OpPlugin产品页仍只确认FP16及静态图，不据源码注释扩展完整产品能力。QuantConv2d在contrib.module导出、contrib顶层没有同名导入，不能随意缩短路径。

正文图片6个引用、3个不同内容均已查看；公式透明图只为阅读生成白底artifact预览，上游未改。未运行TorchAir编译、量化卷积或性能实验。

## 图片来源的适用范围

公式三版逐字节相同，中文补pad图与英文翻译图内容一致，均只解释这份模块文档中的卷积简写及offset_x补值，不提供额外dtype、产品或量化校准保证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-QuantConv2d.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/quant_conv2d.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/quant_conv2d.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/__init__.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/__init__.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000001855947305.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_image_0000001809304238.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/zh-cn_formulaimage_0000001855947305.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/zh-cn_image_0000001809304238.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/en-us_formulaimage_0000001855947305.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/en-us_image_0000001809304238.png)（constraint）
