---
type: API
title: ModulatedDeformConv：pack输入、FP32与索引寿命
description: 说明DCNv2别名、默认bias更正和偏移初始化，保留迁卡及反向保存条件缺口。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-DCNv2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-ModulatedDeformConv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-ModulatedDeformConv.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-ModulatedDeformConv.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/deform_conv.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/deform_conv.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# ModulatedDeformConv：pack输入、FP32与索引寿命

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与输入

`ModulatedDeformConv(in_channels,out_channels,kernel_size,stride=1,padding=0,dilation=1,groups=1,deformable_groups=1,bias=True,pack=True)`。DCNv2实际为同类别名；发布DCNv2页建议ModulationDeformConv的拼写与真实ModulatedDeformConv不同，不能据拼写创建不存在的替代调用。主线未收录DCNv2独立页不等于源码别名已移除。

两固定真实bias默认True，发布参数表/源码注释曾写False，主线API页已更正。kernel/stride/padding/dilation文档写int或tuple，但底层包装部分重新组成列表，不据文档宽类型推定任意tuple组合都验证过。

pack=True内部Conv产生offset与mask，mask经sigmoid；conv_offset权重和偏置初始化0。pack=False实际forward输入为(x,offset,mask)三元组，而非只有一个Tensor。该零初始化是偏移预测层，不把整个可变形卷积weight也置零。

## FP32、迁移与梯度

文档仅支持FP32。Function对input/offset/mask显式float，weight未统一强转，因此不能通过传入FP16模型来规避限制。偏移索引按NPU次序重排，反向再还原；bias=False仍存普通零Tensor，首次forward将索引及bias随x迁移，然后用布尔标记跳过后续迁移，不提供模型反复换卡的自动修正保证。

保存反向Tensor的判断含weight/mask/offset/input.requires_grad，未包括仅bias需要梯度的情况，不能承诺该冻结组合正确反向。底层forward/backward分别调用npu_deformable_conv2d及bk，不把静态入口存在当任意高阶、图模式或数值验证。未运行模型。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-DCNv2.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-ModulatedDeformConv.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-ModulatedDeformConv.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-ModulatedDeformConv.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/deform_conv.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/deform_conv.py)（implementation）
