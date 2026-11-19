---
type: Guide
title: 发布快照NN清单：模块、functional与初始化差异
description: 保留Module及functional独立兼容状态、激活dtype短名单和未验证卷积/SDPA等条目。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
created_at: '2026-11-09T17:27:10Z'
updated_at: '2026-11-09T17:27:10Z'
platforms: []
---

# 发布快照NN清单：模块、functional与初始化差异

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## Module能力不覆盖子模块或functional

Module管理、state_dict、to/half/bfloat16/train/eval和常见容器多数列Y，无独立限制；不能由Module.bfloat16列Y推出每个子算子支持BF16训练。Conv1d/2d/3d、转置/惰性卷积及对应functional卷积都留空；主要Max/AvgPool、RNN/LSTM/GRU、MultiheadAttention、Transformer和functional.scaled_dot_product_attention也有留空条目。这表示这份清单尚未验证，不替代自定义attention API或其他版本明确支持度。

| 分组 | 独立接口限制 |
| --- | --- |
| nn.ReLU/Tanh/Threshold与functional.threshold/threshold_/relu/relu_/tanh | FP16、FP32、INT64 |
| nn.Hardsigmoid/Hardswish/LeakyReLU/Softplus/MultiLabelSoftMarginLoss；functional.hardsigmoid/hardswish/leaky_relu/leaky_relu_/softplus | FP16、FP32 |
| 其他明确列四类型的Norm、Linear、Embedding、损失/激活/重排等 | 仅保存该行的FP16、FP32、INT64、BOOL泛化声明，未提供每个参数/输出的dtype契约 |

nn.GroupNorm留空，functional.group_norm有Y；nn.CrossEntropyLoss/BCELoss留空而functional.cross_entropy/binary_cross_entropy有Y；nn.BCEWithLogitsLoss有Y而对应functional.binary_cross_entropy_with_logits留空。Dropout/functional.dropout留空与nn.Dropout2d有Y也分开；不能由数学等价、类的forward入口或相邻函数调换支持结论。

## 梯度、剪枝与输入组织

clip_grad_value_列Y及四类型限制，clip_grad_norm_留空。prune的多数策略和管理方法有Y，但BasePruningMethod.compute_mask、RandomUnstructured.remove等具体方法留空；参数化列表与right_inverse的Y不覆盖register_parametrization/cached等留空入口。PackedSequence类、to/is_pinned列Y，而batch_sizes/data/sorted_indices与pack/pad入口多留空，不能把可持有对象等同任意打包执行流程。

初始化表的calculate_gain、uniform_/normal_/constant_/ones_/zeros_/eye_/dirac_/xavier_*/kaiming_*/orthogonal_/sparse_列Y，trunc_normal_留空。未列精度/随机/设备约束不表示任意dtype与图捕获组合已验证；模型优化验收仍区分前向、梯度、多步loss与性能。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.nn | 214 | 144 | 65 |
| torch.nn.functional | 47 | 66 | 47 |
| torch.nn.init | 14 | 1 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
