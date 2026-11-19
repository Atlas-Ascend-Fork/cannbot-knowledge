---
type: API
title: NpuDropPath：样本路径随机深度与预生成队列
description: 保存默认None缺口、首次透传和训练状态，区分随机深度与逐元素Dropout。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuDropPath.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuDropPath.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-NpuDropPath.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/drop_path.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/drop_path.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# NpuDropPath：样本路径随机深度与预生成队列

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与前向

文档`NpuDropPath(drop_prob=None)`，实际构造直接计算keep_prob=1-drop_prob，因此省略参数的None不构成可用默认，需显式有效概率。p=0或eval透传；未验证p=1，实际活跃路径会除keep_prob=0，不生成合法端点配方。源码另注明不支持动态shape，不能因独立页面没写就扩大。

活跃路径的随机Tensor形状为(batch,1,...,1)，按每样本残差主路径丢弃，计算x/keep_prob*floor(random+keep_prob)，与逐元素Dropout不同。类级任务键(shape,device,dtype,ndim)不含概率，不提供不同模型/概率队列隔离保证；缺随机数时请求后仍直接返回输入。

## 预生成及验收

enable_droppath_ensemble(model)注册两个pre-hook，先使当前流等待专用流，再在专用流生成后续随机Tensor；未注册或队列空不能据调用成功认定已做随机深度。示例drop_prob=0只测恒等/反向路径，不验证非零概率分布、随机独立或性能。需要显式处理重复Hook、共享状态、输入生命周期和恢复，本卡没有进行随机实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuDropPath.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuDropPath.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-NpuDropPath.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/drop_path.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/drop_path.py)（implementation）
