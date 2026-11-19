---
type: Guide
title: GE自定义激活：近似模式、门控与输入别名
description: 核对NPU Gelu与门控融合的近似参数、前反向实参和FastGelu输入别名警告，区分ATen映射与自定义入口。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/faset_gelu.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/faset_gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_clipped_swiglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_clipped_swiglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fast_gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fast_gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_geglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_geglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_softmax_with_rel_pos_bias.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_softmax_with_rel_pos_bias.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
created_at: '2026-11-10T09:30:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE自定义激活：近似模式、门控与输入别名

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。所选主线完整非空源码、发布完整AST/注释差异已审阅；这批成对Converter的差异为说明字符串、导入顺序、等价异常字符串写法，计算映射不变。QuantMax的同路径仅主线存在，缺路径不推导发布软件缺能力。

本卡限定静态构图合同，整卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、真机精度/别名/通信或性能实验。Support只是候选，警告和注释不是本次复现。IR参数与真实kernel、调度及外围函数化需分别核对。

## NPU Gelu与ATen映射的近似模式不同

npu_gelu.default与npu_gelu_backward.default都要求approximate为none或tanh，否则ValueError；分别传GeluV2(self,approximate)和GeluGradV2(grad_output,self,approximate)。它们与[ATen激活映射](torchair_ge_activation_lowering.md)里忽略/警告近似参数的路径不同，不能只按数学名称共享实现结论。二者没有本地统一Meta Cast，后向Schema注释缺grad_output也不改变真实函数实参顺序。

faset_gelu.py文件名虽拼写特殊，实际注册torch.ops.npu.npu_fast_gelu.default与torch.ops.npu.fast_gelu.default，均直接FastGelu(x)；npu_fast_gelu_backward.default直接FastGeluGrad(grad,self)。来源警告称底层原地实现可能影响输入，而这两条前向没有自行TensorMove；不能把out-of-place公开名称或无报错当输入不变保证。该警告未在本次复现，需按真实图和后续mutation验证。

## 门控融合的属性不等于完整输入域

| 入口 | 节点与属性 |
| --- | --- |
| npu_swiglu.default | SwiGlu(self,dim)，dim默认-1。 |
| npu_swiglu_backward.default | SwiGluGrad(y_grad,x,dim)，没有在本层另行拆分和求和。 |
| npu_geglu.default | GeGluV2(self,dim=-1,approximate=1,activate_left=False)，Schema列两返回，GE结果原序返回。 |
| npu_clipped_swiglu.default | ClippedSwiglu(x,group_index=...,dim=-1,alpha=1.702,limit=7.0,bias=1.0,interleaved=True)，参数原样透传。 |

这些映射没有本地完整检查dim合法性、分裂维度长度、group_index取值、近似枚举或所有混合dtype，也没有证明融合后的累加精度与成本。不要因为直接一个GE节点就认证一次设备启动或收益。

## 相对位置偏置Softmax

npu_masked_softmax_with_rel_pos_bias.default直接MaskedSoftmaxWithRelPosBias(x,atten_mask,relative_pos_bias,scale_value,inner_precision_mode)，默认scale=1.0、precision_mode=0。可选mask原样透传；源码的典型FP16 shape声明不是任意mask广播、相对位置布局、NaN或精度模式支持矩阵。

优化前确认FX准确命名空间与重载、approximate、门控参数、输入后续别名和最终图；分别验证数值、梯度及输入是否被改写后再测性能。本文没有执行这些实验。

## 准确映射清单

仅列所选文件实际注册，有构图分支不证明全部参数或产品可用；未声明的其他重载不作能力否定。

| 文件主题 | 准确入口 |
| --- | --- |
| faset_gelu | `torch.ops.npu.npu_fast_gelu.default`、`torch.ops.npu.fast_gelu.default` |
| npu_clipped_swiglu | `torch.ops.npu.npu_clipped_swiglu.default` |
| npu_fast_gelu_backward | `torch.ops.npu.npu_fast_gelu_backward.default` |
| npu_geglu | `torch.ops.npu.npu_geglu.default` |
| npu_gelu | `torch.ops.npu.npu_gelu.default` |
| npu_gelu_backward | `torch.ops.npu.npu_gelu_backward.default` |
| npu_masked_softmax_with_rel_pos_bias | `torch.ops.npu.npu_masked_softmax_with_rel_pos_bias.default` |
| npu_swiglu | `torch.ops.npu.npu_swiglu.default` |
| npu_swiglu_backward | `torch.ops.npu.npu_swiglu_backward.default` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/faset_gelu.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/faset_gelu.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_clipped_swiglu.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_clipped_swiglu.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fast_gelu_backward.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fast_gelu_backward.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_geglu.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_geglu.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_backward.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gelu_backward.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_softmax_with_rel_pos_bias.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_masked_softmax_with_rel_pos_bias.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_backward.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_backward.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
