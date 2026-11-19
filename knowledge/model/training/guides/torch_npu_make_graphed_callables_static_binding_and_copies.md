---
type: Guide
title: Graph callable的静态绑定：预热、复制与输出别名
description: 解释样例/参数静态绑定、warmup及replay复制与输出别名，不将autograd实现当产品支持。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/graphs.py
  role: implementation
created_at: '2026-11-12T02:31:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Graph callable的静态绑定：预热、复制与输出别名

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`及发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的make_graphed_callables完整本地函数。它含autograd包装和反向捕获代码，但docstring中的“training drop-in”不升级[公开原生图支持页](../../inference/guides/optimization/torch_npu/torch_npu_native_graph_support_scope.md)的推理限定；本卡只解释实际绑定、准备和调用行为，未执行捕获或设备。

## 捕获前检查和静态输入面

| 条件/准备 | 实际行为 |
| --- | --- |
| NPU autocast开启且cache开启 | 立即拒绝；不是自动替用户关闭cache。 |
| nn.Module已有forward/pre-forward/backward hooks | 拒绝；同时拒绝requires_grad的buffer。检查当前传入模块的这些hook字典，不是递归证明所有外部hook都安全。 |
| sample_args | 先pytree展平，再要求每个叶子是Tensor；不是只允许一个扁平tuple，也没有在这里先统一核对callables/sample_args长度。 |
| 静态输入面 | 用户样例叶子tuple，加上捕获时c.parameters()生成的tuple；参数对象被闭包保留。 |
| 图/pool | 每个callable建立forward/backward NPUGraph；所有callable使用给定pool或同一个新pool token。 |

函数没有在这里复制出一组全新的用户样例Tensor作为独立静态输入；后续copy_目标就是静态输入面中的样例对象。Module参数也不是每次调用重新枚举，捕获后替换Parameter、改变buffer或顺序不能仅凭Python属性仍可访问就判为生效。普通函数闭包内的Tensor也没有在这里自动归类成可更新用户输入。

## 预热和捕获不是只读模型分析

预热前后各NPU synchronize，在新流上按num_warmup_iters重复调用func；有requires_grad输出时执行autograd.grad，grad_outputs用empty_like申请，allow_unused由参数决定。默认迭代数3是源码默认值，docstring提到DDP需11只是该文档说明，不代表本地已经按模块类型自动改成11。没有本地事务回滚或统一保存/恢复全部参数、buffer、输入值和随机状态。

随后正序捕获全部forward，按逆序捕获需要梯度输出的backward，共享pool。返回值先pytree展平并保存结构；代码随后直接访问各输出的requires_grad等属性，没有在此为任意非Tensor输出补齐通用协议。无梯度输出时可不建立实际backward捕获，但仍有相应对象/列表准备。

## replay只对用户输入检查地址，不全面验证形状和参数

| 包装阶段 | 本地行为 |
| --- | --- |
| Graphed.forward | 仅遍历len_user_args，若静态输入与新输入data_ptr不同才copy_；之后forward graph replay。 |
| forward输出 | 对保存的static_outputs逐个detach后返回，再按保存spec还原结构；detach不是独立Storage clone。 |
| Graphed.backward | 先检查梯度项数量；有静态梯度目标且地址不同才copy_，随后backward replay，返回保存的静态梯度detach或None。 |
| 高阶梯度 | 使用once_differentiable；没有提供双重反向的本地支持协议。 |

地址相同不代表内容不变；地址不同时copy_也没有在这层先构造完整的shape/stride/dtype/设备/别名Guard。实际Tensor复制或后端仍可能检查/拒绝，不能把“有copy分支”当成任意动态形状适配。backward对非None静态梯度槽直接读取对应grad.data_ptr，没有为任意None组合统一补零。输出和梯度返回的是保存对象的detach视图，长期保留其值时不能自动获得独立副本。

对于Module，函数原地替换func.forward：training标志等于捕获时值才走graphed，否则调用原forward。切换eval/training可能因此改走原路径，不是重新捕获一张适配图；普通函数没有这条Module状态分支。单callable返回一个对象，tuple输入返回tuple；共享pool的调用顺序、输入所有权和输出寿命应按实际模型组织。

两版完整主体及注释相同，主线额外记录autocast/hook错误诊断与结束日志，另有排版差异。没有据保留的CUDA措辞推导NPU产品支持或默认训练正确性；与[Tree的输入staging](../../inference/guides/optimization/torchair/torchair_inductor_ascendc_graph_tree.md)是不同入口，不能把Tree的重录、输出迁移或参数保护自动套用到这里。

## 固定实现来源

- [graphs.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py)（primary）：948–1257。
- [graphs.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/graphs.py)（implementation）：540–835。
