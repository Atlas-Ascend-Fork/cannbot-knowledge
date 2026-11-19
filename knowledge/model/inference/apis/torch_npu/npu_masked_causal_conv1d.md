---
type: API
title: npu_masked_causal_conv1d：950 三点因果卷积与输出掩码
description: 说明序列优先布局、固定窗口和 mask 仅置零输出，不把它当作输入状态重置。
tags:
- task.lookup
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_masked_causal_conv1d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_masked_causal_conv1d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_masked_causal_conv1d.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_masked_causal_conv1d_backward.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_causal_conv1d.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- '950'
---

# npu_masked_causal_conv1d：950 三点因果卷积与输出掩码

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口

```text
torch_npu.npu_masked_causal_conv1d(input, weight, *, mask=None) -> Tensor
```

input=(S,B,H)、weight=(W,H)，ND、同FP16/BF16，二者可非连续。W只支持3，序列起点补两个零，沿S做depthwise卷积；不等价于任意宽度、任意布局Conv1d。

mask若给定为连续BOOL、shape=(B,S)，True有效，False将对应输出整行置零；mask=None不掩码。文档公式是在卷积结果上施加mask，不能据此假定被mask输入不再参与后续位置的因果窗口，或自动重置跨序列状态。

输出同input shape/dtype。主线产品页仅列950PR/DT推理，列单算子和图模式；不推断其他产品或训练反向支持。


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；存在单独反向需求时先核对公开产品范围和梯度契约；当前推理路径还需比较多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 生成包装、Meta和反向入口

固定主线Schema用gen_opapi生成aclnnMaskedCausalConv1d包装，输出shape/dtype取自input；同文件还描述独立backward入口的grad_input与grad_weight。Meta前向仅empty_like(input)，后向仅按grad_output及weight分配，不能据此认定已经检查W=3、mask连续性、dtype和布局。

TorchAir主线Converter只把input、weight和mask传给MaskedCausalConv1d；生成GE声明FP16/BF16输入、可选BOOL mask和单个同类型输出，仍不是完整参数检查。发布快照没有该文档或对应转换器，主线950PR/DT声明不回推该发布组合。

derivatives.yaml确有从前向映射到独立backward的规则，但产品页只声明推理，不能把规则存在当成公开训练支持或设备梯度验收。前向3例和后向4例测试全部无条件skip，本文未执行。

前向参考用CPU FP32 depthwise卷积，序列头补W-1个零，卷积后按输出mask置零；后向参考先mask梯度，再求移位输入梯度和权重梯度。这些参考不把被mask的原始输入从未来窗口中删除。autograd用例在requires_grad Tensor上调用.npu后直接检查该结果的.grad，没有保留非叶节点梯度，不能凭该断言证明整条自动反向链已验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_masked_causal_conv1d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_masked_causal_conv1d.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_masked_causal_conv1d.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_masked_causal_conv1d_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_causal_conv1d.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
