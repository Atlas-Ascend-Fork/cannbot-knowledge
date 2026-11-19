---
type: API
title: 旧Adam更新：out状态、BERT参数与废弃迁移
description: 保留低层状态写回协议、Scalar声明与非out入口报错，避免机械替换优化器。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_apply_adam.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bert_apply_adam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bert_apply_adam.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_bert_apply_adam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BertApplyAdamKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BertApplyAdamKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ApplyAdamKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ApplyAdamKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧Adam更新：out状态、BERT参数与废弃迁移

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## npu_apply_adam

参数beta1_power、beta2_power、lr、beta1、beta2、epsilon为Scalar，grad为Tensor；out=(var,m,v)携带参数和两个矩状态。use_locking/use_nesterov是可选bool，源码仅在有值时传底层属性，不据“可选”猜测所有模式有效。接口计划废弃，文档建议torch.optim.Adam。

两固定实现的非out入口直接报错；out入口检查/刷新var、m、v格式并更新它们，再返回三元组。它不是独立分配三份状态的纯函数，也不能把调用本身当成完整Optimizer的step、参数分组、梯度清理或检查点协议。迁移须核对幂次更新时点、epsilon位置、状态dtype及别名。

## npu_bert_apply_adam

该接口计划废弃，底层不维护，性能/精度不作保证。var为FP16/FP32，m/v/grad与其shape、dtype相同；另有max_grad_norm、global_grad_norm、weight_decay、step_size和adam_mode。发布原型写关键字var/m/v，但同页示例、主线修正原型及实际schema使用out=(var,m,v)。两版非out同样直接报错，不复制旧原型作为可运行示例。

step_size两固定schema为Scalar?，发布与主线英文页写Tensor，主线中文修正为Scalar；不能为此额外构造设备Tensor或把Scalar说明的shape(1,)当真实Tensor约束。公开adam_mode只列0/1；实现把0映射adam、非0映射mbart_adam，文档拼mbert_adam，不从内部宽松分支推荐其他整数模式。保留梯度范数、权重衰减和实际状态写回差异，不能直接宣称普通Adam等价。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_apply_adam.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bert_apply_adam.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bert_apply_adam.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_bert_apply_adam.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BertApplyAdamKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BertApplyAdamKernelNpu.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ApplyAdamKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ApplyAdamKernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
