---
type: API
title: npu_layer_norm_eval：可空仿射参数与推理迁移
description: 保留LayerNorm数学范围和实际克隆/脱离梯度行为，避免当通用训练替代。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_layer_norm_eval.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormEvalKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormEvalKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- a2
- a3
---

# npu_layer_norm_eval：可空仿射参数与推理迁移

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本次未导入上游、加载模型、执行设备、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在已读来源内，不作已核验结论。


## 参数和替代

npu_layer_norm_eval(input,normalized_shape,weight=None,bias=None,eps=1e-5)计划废弃，建议F.layer_norm。沿normalized_shape所指后缀做层归一化，区别于不减均值的RMSNorm；weight/bias可空，不把示例torch.Tensor未初始化内容出现NaN当正常数值基准。

两固定实现逐字节相同：非空weight/bias先clone并detach，None构造ones/zeros，再按normalized_shape乘积匹配和重设临时参数shape。此局部检查不是完整验证输入每个后缀维度，也不能用“eval”名称推断与训练LayerNorm完全相同的梯度/参数别名协议。

迁移时使用已知初始化值，核对归一化轴、eps、可空参数和输出；若参与训练需另核对参数梯度，不能把这个旧推理入口作为省显存的通用训练优化。未运行设备或性能实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_layer_norm_eval.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormEvalKernelNpu.cpp)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormEvalKernelNpu.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
