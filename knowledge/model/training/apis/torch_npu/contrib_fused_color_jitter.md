---
type: API
title: FusedColorJitter旧接口：Host实现与参数错位边界
description: 保留ColorJitter迁移、随机区间和Host路径，指出当前固定包装不能作为可靠设备增强配方。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-FusedColorJitter.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/fusedcolorjitter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/fusedcolorjitter.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# FusedColorJitter旧接口：Host实现与参数错位边界

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 发布合同与替代

仅发布页收录，计划废弃、建议torchvision.transforms.ColorJitter。实际构造brightness=0,contrast=0,saturation=0,hue=0；页面的FusedColorJitter(torch.nn.Module)不是完整签名。前三项非负标量或(min,max)，因子从[max(0,1-v),1+v]或给定区间取；hue标量[0,.5]或区间-.5<=min<=max<=.5。

## 固定实现的缺口

两固定实现实际走PIL/NumPy、Python random、矩阵乘加、clip并按原dtype输出；没有NPU Tensor Kernel路径，调用模块.npu()不能把它变成设备数据增强。输入按HWC三通道，4通道去最后通道，1通道扩三通道；PIL路线返回RGB图像。

构造调用`_FusedColorJitterApply(brightness,contrast,saturation,hue)`，该helper位置参数顺序却为hue,saturation,contrast,brightness，存在参数对应错位。检查后的区间值保存在模块属性，但helper收到原值，后续又对它做标量运算，不能将tuple可通过构造检查当完整执行支持。

docstring约20%加速是无当前硬件/输入及测量记录的旧描述，不作为已验证收益。此卡记录迁移与失效边界，不建议以该包装继续构建优化方案，外部ColorJitter完整版本合同未自动摄取。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-FusedColorJitter.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/fusedcolorjitter.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/fusedcolorjitter.py)（implementation）
