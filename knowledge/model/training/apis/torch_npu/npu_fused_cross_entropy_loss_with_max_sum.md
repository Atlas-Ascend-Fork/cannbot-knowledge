---
type: API
title: npu_fused_cross_entropy_loss_with_max_sum：消费全局统计
description: 说明 A2/A3 的全局统计前提、label_smoothing=0 与可选 FP32 softmax 输出。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_cross_entropy_loss_with_max_sum.py
  role: example
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# npu_fused_cross_entropy_loss_with_max_sum：消费全局统计

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口

```text
npu_fused_cross_entropy_loss_with_max_sum(logits_max, sum_exp_logits,
    predicted_logits, *, label_smoothing=0.0, input=None, weight=None,
    vocab_parallel_logits=None) -> (loss, softmax)
```

前三项须是通信处理后的全局量，均一维FP32、shape相同。loss=log(sum_exp_logits)-predicted_logits，softmax按exp(local_logits-global_max)/global_sum计算；必须确保分母与预测logit以同一全局最大值作参考点，不能直接相加未修正的局部exp和。

label_smoothing目前仅0，input/weight目前仅None。vocab_parallel_logits若给定，为二维FP16/BF16/FP32，首维匹配统计向量；返回FP32 softmax且同shape。未给时softmax槽为None，loss始终FP32、shape同统计向量。

产品页仅列A2/A3，本卡不因前后两个接口均列950而扩大本阶段范围。这个接口不替用户执行必要的跨rank统计合并。

- [局部MatMul统计](npu_fused_linear_online_max_sum.md)
- [显式反向接口](npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 可选返回、参数传递和静态测试边界

主线C++总是返回二槽；没有vocab_parallel_logits时第二槽为未定义Tensor，静态测试明确断言Python返回None，不是具有某个空shape的FP32概率矩阵。提供局部logits时才分配与它同shape的FP32 softmax。前三份统计和loss为同长度的一维FP32，局部logits的首维也需匹配。

Schema的label_smoothing允许None，C++把None转成0；这不扩大公开仅0的支持范围。input、weight虽被包装原样传递，公开仍仅允许None。包装层没有完成这些数学前提、形状及产品范围的全部检查，参数能够传到底层不等于用法有效。

该实现文件只分配输出并调用aclnnFusedCrossEntropyLossWithMaxSum，没有跨rank归约。测试用随机max、sum与predicted数据，只检查shape/dtype及可选槽，并未验证这些统计来自同一批logits，也没有数值损失、梯度或完整通信参考。

两份主线公开页均只列A2/A3。950在此阶段未确认，不能写成明确不支持，也不能用另两阶段的950PR/DT支持补齐整条链路。固定Meta与derivatives文件没有找到本接口的同名手写条目；这只是文件内的检索结果，不宣称所有图后端不可用或自动求导已经适配。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_cross_entropy_loss_with_max_sum.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedLinearCrossEntropyLossKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_fused_cross_entropy_loss_with_max_sum.py)（example）
