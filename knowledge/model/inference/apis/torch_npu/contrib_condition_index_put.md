---
type: API
title: 条件替换包装：torch.where新结果与原地语义差别
description: 修正旧bbox文案，记录Bool条件、标量值和原生可能更快的边界。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_fast_condition_index_put.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_fast_condition_index_put.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_fast_condition_index_put.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/index_op.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/index_op.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# 条件替换包装：torch.where新结果与原地语义差别

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 实际调用

`npu_fast_condition_index_put(x,condition,value)`要求condition.dtype为bool，否则TypeError；value为int/float替代值，不是发布误写的bbox步长。两固定实现按0/1分别zeros_like/ones_like，否则zeros_like+value，再调用torch.where(condition,mask,x)，返回**新Tensor**，没有原地写入x。

因此替换`x[condition]=value`时必须处理返回值和原存储/别名，不是忽略返回便可等价。广播、dtype提升和多分配的实际行为还按输入验证，不能由功能简介补全所有index_put累加/高级索引合同。

发布样例`x1=copy.deepcopy(x)[condition]=value`不能正确建立期望对照，主线分为拷贝、索引赋值两句；同时修正返回“框转换deltas”的误植。源码明确原生index持续优化、部分场景原生更快，不据fast名称报告收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_fast_condition_index_put.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_fast_condition_index_put.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_fast_condition_index_put.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/index_op.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/index_op.py)（implementation）
