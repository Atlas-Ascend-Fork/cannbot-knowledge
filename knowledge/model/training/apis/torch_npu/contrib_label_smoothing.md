---
type: API
title: LabelSmoothingCrossEntropy：类别数、标签与FP32归约
description: 保存平滑范围及真实one-hot维度，区分类别默认值和预测列数必须一致的前提。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-LabelSmoothingCrossEntropy.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-LabelSmoothingCrossEntropy.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-LabelSmoothingCrossEntropy.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/crossentropy.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/crossentropy.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# LabelSmoothingCrossEntropy：类别数、标签与FP32归约

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造和计算

`LabelSmoothingCrossEntropy(num_classes=1000,smooth_factor=0.)`的页面smooth范围[0,1]，.1为建议而非必选。文档num_classes写float，实际用于off_value=smooth/(num_classes−1)；类别应按实际离散类别数配置，不能据标注接受任意小数。num_classes=1会在构造分母为0，包装没有完整合法域校验。

on_value=1−smooth，target先转INT32，one-hot的depth却取pred.size(1)，不是构造num_classes；两者需一致，否则非目标类权重不能按预期归一化。随后npu_softmax_cross_entropy_with_logits，并沿dim0求FP32 mean；源码误植的NMS(k,5)/(k,1)返回描述不适用。

## 调用边界

页面例只对[2,10]预测和两个标签做一次backward，没有标签越界、空批次、多维预测、分布式归约或数值对照。target.int转换不替代标签合法性检查；不能把一个返回标量当作所有reduction/ignore_index/类别权重选项均与原生交叉熵相同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-LabelSmoothingCrossEntropy.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-LabelSmoothingCrossEntropy.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-LabelSmoothingCrossEntropy.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/crossentropy.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/crossentropy.py)（implementation）
