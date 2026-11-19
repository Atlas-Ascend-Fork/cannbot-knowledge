---
type: Guide
title: GE损失函数：归约索引、权重与梯度类型
description: 核对MSE与NLL前反向的类型提升、归约枚举、INT32目标和缺失权重分支，区分文档约束与静态构图边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_forward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_forward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T09:13:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE损失函数：归约索引、权重与梯度类型

## 固定版本与证据边界

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线完整非空源码、发布完整AST/注释差异均已阅读；本卡平台矩阵未知，保持draft与空平台，未执行上游、GE编译、NPU精度/反向或性能实验。Support只是候选声明，静态构图不替代kernel、ABI和高层函数验证。

## MSE的归约和精度顺序

mse_loss.default把self/target一并提升为meta_outputs.dtype，再按['none','mean','sum'][reduction]选择字符串，传MseLoss。mse_loss_backward.default同样提升self/target，但grad_output原样传MseLossGrad；不是三项输入统一提升。

两处归约辅助函数都直接Python列表下标，没有独立的0..2校验，负索引/越界行为不能按报错外推为完整合法性检查。文档[ATen清单](../../inference/guides/optimization/torchair/torchair_aten_constraint_review.md)另要求MSE input/target同dtype并列前反向精度；本地存在Cast不抹去文档边界，也不认证任意广播和混合类型已可运行。

## NLL前向与反向类型处理不同

nll_loss_forward.default只将self转meta_outputs[0].dtype；target为INT64时警告并转INT32，其他target保持原类型，weight含None原样传给NLLLoss。返回output/total_weight原序，没有单独按第二个Meta Cast。

nll_loss_backward.default的weight=None分支，以GatherV2(Shape(self),1,0)取轴1大小再Fill 1.0；没有为rank1输入单独改取轴0的分支，不能从高层NLL支持1D就推导本缺weight路径已完整覆盖。随后self、grad_output、weight、total_weight统一提升为meta_outputs.dtype，target则**无论原类型都转INT32**，再NLLLossGrad。前向的仅INT64转换和反向的全target转换不能混用。

reduction同样直接列表下标；ignore_index虽然注解可为Tensor，原样作为GE属性传入，没有在此函数建立运行期Tensor ignore_index的计算节点。大INT64 target转INT32是否无损、weight/total_weight的精度与形状都要按真实输入核对，不能从参数透传认证所有值域。

## 优化与验证

检查真实FX准确重载、reduction值、input/target rank与shape、weight是否None、类别轴、ignore_index和total_weight来源，再核对前反向Cast顺序及最终归约图；数值与梯度确认后才评估收益。本组两快照四对AST相同，没有本次运行结果。所有out/grad_input入口的直接拒绝见表。

- [Converter类型与Meta职责](../../inference/guides/optimization/torchair/torchair_converter_implementation.md)
- [文档层NLL形状与精度约束](../../inference/guides/optimization/torchair/torchair_aten_constraint_review.md)

## 准确入口与拒绝重载

可构图入口仍受正文条件限制；拒绝仅指准确映射，不扩高层函数或其他后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| mse_loss | `torch.ops.aten.mse_loss.default` | `torch.ops.aten.mse_loss.out` (RuntimeError) |
| mse_loss_backward | `torch.ops.aten.mse_loss_backward.default` | `torch.ops.aten.mse_loss_backward.grad_input` (RuntimeError) |
| nll_loss_forward | `torch.ops.aten.nll_loss_forward.default` | `torch.ops.aten.nll_loss_forward.output` (RuntimeError) |
| nll_loss_backward | `torch.ops.aten.nll_loss_backward.default` | `torch.ops.aten.nll_loss_backward.grad_input` (RuntimeError) |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss_backward.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss_backward.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_forward.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_forward.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_backward.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nll_loss_backward.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
