---
type: Guide
title: GE逐点数学与激活：精度、反向和参数边界
description: 审阅42组逐点及激活转换，区分GELU近似参数、反向保存值、辅助buffer、输出别名和erfinv版本差异。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/acos.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/acos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/acosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/acosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/asin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/asin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/asinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/asinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/atan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/atan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/atanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/atanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cos.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cosh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sinh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tan.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/erf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/erf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/erfinv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/erfinv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/relu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/relu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/silu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/silu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mish.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mish.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/elu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/elu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/elu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/elu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/prelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/prelu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/glu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/glu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/glu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/glu_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_forward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_forward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lerp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lerp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:15:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE逐点数学与激活：精度、反向和参数边界

## 版本与证据边界

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的42组逐点数学/激活及反向Converter。逐个审阅主线全部非空源码、发布完整AST差异及注释变化：39组AST相同，3组差异中relu和threshold_backward仅说明文本不同，erfinv.out有实质控制流差异。

这里只形成静态构图合同；没有覆盖整卡的产品矩阵，保持draft、空平台，未执行上游、GE编译、smoke、NPU数值或性能测试。declare_supported的dtype、shape和参数仅为声明/候选测试，不能当作运行通过；未在本层显式Cast也不直接证明最终GE/kernel结果错误或正确。

## 一元数学与显式类型转换

| 准确default入口 | 此快照的构图行为 |
| --- | --- |
| acos、acosh、atan、atanh | 分别直接Acos/Acosh/Atan/Atanh，没有在Converter内统一按Meta处理输入。 |
| asin、asinh | 仅meta_outputs存在时先按其dtype处理输入，再Asin/Asinh；不能把这条分支传播给其他反三角函数。 |
| cos、cosh、sin、sinh、tan、tanh | 直接调用同名GE节点；不在本层读取运行值或认证输入定义域、复数及非有限值。 |
| erf、erfinv | 分别直接Erf/Erfinv；erfinv.out的版本和输出对象限制见后文。 |
| relu、sigmoid、silu、mish | 分别Relu、Sigmoid、Swish、Mish；silu的映射名字是Swish，不据此认定任意beta配置或融合模式被透传。 |

这些Tensor.default实现不能推出同名Python标量int/float/complex/Scalar overload也实现。直接拒绝清单逐项保留，避免只凭一个有实现的文件认定整个算子包接入。精度转换辅助的固定行为见[GE算术转换](torchair_ge_arithmetic_lowering.md)。

## GELU近似模式未完整转交

torch.ops.aten.gelu.default签名中的approximate默认字符串是大写开头的"None"，而Schema说明写小写"none"；函数体无论收到什么approximate，都直接Gelu(self)，没有选择tanh近似或传递该参数。不能因参数绑定成功就声称不同近似算法均保持语义。

torch.ops.aten.gelu_backward.default在approximate不等于"None"时仅warning_once，并不拒绝或改换实现；随后把grad_output再作为unused第三输入传GeluGrad(grad_output,self,unused)。这里的unused不是已计算前向输出，也不是用第三输入认证前向缓存格式。需要核对实际生成的GE节点及对应近似精度，不能把警告当成安全回退或模式已经生效。

## 属性、输入/结果标志与前反向分别核对

| 家族 | 固定Converter的参数边界 |
| --- | --- |
| elu与elu_backward | 前向把alpha、scale、input_scale交Elu属性；Union[Number,Tensor]注解不构成任意动态图Tensor属性合法的证明。反向明确拒绝三个系数中任一为GE Tensor；is_result=True且alpha<0时拒绝，否则EluGradV2(grad_output,self_or_result,...)保留is_result。 |
| leaky_relu与leaky_relu_backward | 两者拒绝Tensor negative_slope，前向交LeakyRelu属性；反向交LeakyReluGrad(grad_output,self,negative_slope=...)，没有使用self_is_result。不能从同一Schema形参存在推导以结果替代原输入时仍正确，特别需核对负斜率和保存Tensor的含义。 |
| hardsigmoid与hardswish | 前向分别HardSigmoid/HardSwish，反向分别HardSigmoidGrad(grad_output,self)、HardSwishGrad(grad_output,self)；不能照搬使用前向output的sigmoid/tanh反向模板。 |
| hardtanh | min_val>=max_val时Fill输入Shape，max_val转输入原dtype；其他分支将self和两界限按Meta输出dtype处理再ClipByValueV2。两条分支的类型选择不同，Python比较也不能当作任意动态图Tensor上下界的运行判断。 |
| hardtanh_backward | 显式拒绝Tensor上下界，然后调用HardtanhGrad(self,grad_output,min_val=...,max_val=...)；输入次序与前述HardSwishGrad相反。 |
| threshold与threshold_backward | 前向直接ThresholdV2(self,threshold=...,value=...)。反向先将self和grad_output按Meta dtype处理，拒绝Tensor threshold；threshold==0.0时用ReluGrad，否则ThresholdGradV2D。源码建议零阈值高性能，只是IR选择线索，尚无本任务性能测量。 |

## 门控、参数梯度与辅助buffer

prelu.default与_prelu_kernel.default都调用PRelu(self,weight)；_prelu_kernel_backward.default直接返回PReluGrad(grad_output,self,weight)的两个输出，没有在Converter额外构造权重梯度归约。权重shape、通道广播、两输出规格和归约合同须核对实际GE算子，不能从返回tuple推导所有训练配置已验证。源declare_supported把多个输入放在一个列表内，也只是候选声明，不是实际测试记录。

glu.default明确拒绝rank<1，其余GLU(self,dim=dim)；glu_backward.default用GLUGrad(grad_output,self,dim=dim)。前向没有在这里逐项检查axis范围和相应长度偶数，不能因缺少Python检查就覆盖[ATen文档能力表](torchair_aten_constraint_review.md)里的限制。

sigmoid_backward.default、tanh_backward.default分别调用SigmoidGrad(output,grad_output)、TanhGrad(output,grad_output)，原Schema的参数顺序在这里被调换。它们使用前向输出而不是任意原输入，不能对全部激活反向统一替换保存值。

log_sigmoid_forward.default返回(LogSigmoid(self),Identity(self))，第二个buffer是输入的Identity；log_sigmoid_backward.default却直接LogSigmoidGrad(grad_output,self)，没有使用传入buffer。这是此GE实现内部的配对安排，不是所有Eager/设备实现通用的缓存格式，也不证明buffer可以跨后端混用或永久复用。

lerp.Scalar调用Lerp(self,end,weight)，准确lerp.Tensor仍直接NotImplementedError。不能由Scalar函数的Union注解推导Tensor权重overload已经实现，也不能默认该层为self/end/weight增加公共dtype或任意广播适配。

## 有输出重载不等于完成写回

主线erfinv.out创建Erfinv结果后返回；发布版同处却写raise out，抛出构图结果而非返回。记录这一源码差异，不把它当作已执行的设备故障或修复验收。

mish.out将局部out改为新Mish结果；log_sigmoid_forward.output重新创建output和Identity buffer；log_sigmoid_backward.grad_input重新赋新LogSigmoidGrad结果。它们均没有读取调用方传入的输出对象，不能仅按“没有NotImplementedError”认定写回、对象身份、别名与存储合同已完整满足。外围函数化或输出绑定是否负责写回仍需另核，不能由当前返回语句代替。

其余无条件异常壳见下表，保留RuntimeError与NotImplementedError区别。消息中的旧PyTorch版本文字只作为源码诊断，不宣称换较新版本后这些壳自动变为实现。

## 优化与验收

从准确FX overload确认参数是否真实使用，再检查保存的是输入还是前向结果、反向GE操作数顺序、Cast位置以及辅助输出。重点覆盖GELU approximate、负斜率、hard阈值边界、GLU轴和偶数长度、PReLU权重梯度、log-sigmoid buffer与out别名。源码单节点、零阈值快捷分支及接口名字不构成实际融合或性能收益证据，需在目标固定版本分别测数值与稳态性能。

方法入口见[Converter开发](torchair_converter_implementation.md)，归约精度另见[GE归约与排序](torchair_ge_reduction_lowering.md)。

## 全部准确overload及直接拒绝边界

有构图分支仍受前文参数、dtype、版本和输出别名限制；erfinv.out特指主线返回分支，发布版会raise结果。直接拒绝列只描述实际选中此Converter后的异常，不把同名高层函数或其他后端一概判为不支持。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| acos | `torch.ops.aten.acos.default` | NotImplementedError：`torch.ops.aten.acos.out`、`torch.ops.aten.acos.int`、`torch.ops.aten.acos.float`、`torch.ops.aten.acos.complex`、`torch.ops.aten.acos.Scalar` |
| acosh | `torch.ops.aten.acosh.default` | NotImplementedError：`torch.ops.aten.acosh.out`、`torch.ops.aten.acosh.int`、`torch.ops.aten.acosh.float`、`torch.ops.aten.acosh.complex`、`torch.ops.aten.acosh.Scalar` |
| asin | `torch.ops.aten.asin.default` | NotImplementedError：`torch.ops.aten.asin.out`、`torch.ops.aten.asin.int`、`torch.ops.aten.asin.float`、`torch.ops.aten.asin.complex`、`torch.ops.aten.asin.Scalar` |
| asinh | `torch.ops.aten.asinh.default` | NotImplementedError：`torch.ops.aten.asinh.out`、`torch.ops.aten.asinh.int`、`torch.ops.aten.asinh.float`、`torch.ops.aten.asinh.complex`、`torch.ops.aten.asinh.Scalar` |
| atan | `torch.ops.aten.atan.default` | NotImplementedError：`torch.ops.aten.atan.out`、`torch.ops.aten.atan.int`、`torch.ops.aten.atan.float`、`torch.ops.aten.atan.complex`、`torch.ops.aten.atan.Scalar` |
| atanh | `torch.ops.aten.atanh.default` | NotImplementedError：`torch.ops.aten.atanh.out`、`torch.ops.aten.atanh.int`、`torch.ops.aten.atanh.float`、`torch.ops.aten.atanh.complex`、`torch.ops.aten.atanh.Scalar` |
| cos | `torch.ops.aten.cos.default` | NotImplementedError：`torch.ops.aten.cos.out`、`torch.ops.aten.cos.int`、`torch.ops.aten.cos.float`、`torch.ops.aten.cos.complex`、`torch.ops.aten.cos.Scalar` |
| cosh | `torch.ops.aten.cosh.default` | NotImplementedError：`torch.ops.aten.cosh.out`、`torch.ops.aten.cosh.int`、`torch.ops.aten.cosh.float`、`torch.ops.aten.cosh.complex`、`torch.ops.aten.cosh.Scalar` |
| sin | `torch.ops.aten.sin.default` | NotImplementedError：`torch.ops.aten.sin.out`、`torch.ops.aten.sin.int`、`torch.ops.aten.sin.float`、`torch.ops.aten.sin.complex`、`torch.ops.aten.sin.Scalar` |
| sinh | `torch.ops.aten.sinh.default` | NotImplementedError：`torch.ops.aten.sinh.out`、`torch.ops.aten.sinh.int`、`torch.ops.aten.sinh.float`、`torch.ops.aten.sinh.complex`、`torch.ops.aten.sinh.Scalar` |
| tan | `torch.ops.aten.tan.default` | NotImplementedError：`torch.ops.aten.tan.out`、`torch.ops.aten.tan.int`、`torch.ops.aten.tan.float`、`torch.ops.aten.tan.complex`、`torch.ops.aten.tan.Scalar` |
| tanh | `torch.ops.aten.tanh.default` | RuntimeError：`torch.ops.aten.tanh.out`、`torch.ops.aten.tanh.int`、`torch.ops.aten.tanh.float`、`torch.ops.aten.tanh.complex`、`torch.ops.aten.tanh.Scalar` |
| erf | `torch.ops.aten.erf.default` | RuntimeError：`torch.ops.aten.erf.out`、`torch.ops.aten.erf.int`、`torch.ops.aten.erf.float`、`torch.ops.aten.erf.Scalar` |
| erfinv | `torch.ops.aten.erfinv.default`、`torch.ops.aten.erfinv.out` | 无无条件拒绝壳；不等同完整运行支持 |
| relu | `torch.ops.aten.relu.default` | NotImplementedError：`torch.ops.aten.relu.out` |
| sigmoid | `torch.ops.aten.sigmoid.default` | RuntimeError：`torch.ops.aten.sigmoid.out` |
| sigmoid_backward | `torch.ops.aten.sigmoid_backward.default` | NotImplementedError：`torch.ops.aten.sigmoid_backward.grad_input` |
| tanh_backward | `torch.ops.aten.tanh_backward.default` | RuntimeError：`torch.ops.aten.tanh_backward.grad_input` |
| gelu | `torch.ops.aten.gelu.default` | RuntimeError：`torch.ops.aten.gelu.out` |
| gelu_backward | `torch.ops.aten.gelu_backward.default` | RuntimeError：`torch.ops.aten.gelu_backward.grad_input` |
| silu | `torch.ops.aten.silu.default` | NotImplementedError：`torch.ops.aten.silu.out` |
| mish | `torch.ops.aten.mish.default`、`torch.ops.aten.mish.out` | 无无条件拒绝壳；不等同完整运行支持 |
| elu | `torch.ops.aten.elu.default` | RuntimeError：`torch.ops.aten.elu.out` |
| elu_backward | `torch.ops.aten.elu_backward.default` | RuntimeError：`torch.ops.aten.elu_backward.grad_input` |
| leaky_relu | `torch.ops.aten.leaky_relu.default` | RuntimeError：`torch.ops.aten.leaky_relu.out` |
| leaky_relu_backward | `torch.ops.aten.leaky_relu_backward.default` | NotImplementedError：`torch.ops.aten.leaky_relu_backward.grad_input` |
| hardsigmoid | `torch.ops.aten.hardsigmoid.default` | RuntimeError：`torch.ops.aten.hardsigmoid.out` |
| hardsigmoid_backward | `torch.ops.aten.hardsigmoid_backward.default` | RuntimeError：`torch.ops.aten.hardsigmoid_backward.grad_input` |
| hardswish | `torch.ops.aten.hardswish.default` | RuntimeError：`torch.ops.aten.hardswish.out` |
| hardswish_backward | `torch.ops.aten.hardswish_backward.default` | RuntimeError：`torch.ops.aten.hardswish_backward.out` |
| hardtanh | `torch.ops.aten.hardtanh.default` | RuntimeError：`torch.ops.aten.hardtanh.out` |
| hardtanh_backward | `torch.ops.aten.hardtanh_backward.default` | NotImplementedError：`torch.ops.aten.hardtanh_backward.grad_input` |
| threshold | `torch.ops.aten.threshold.default` | NotImplementedError：`torch.ops.aten.threshold.out` |
| threshold_backward | `torch.ops.aten.threshold_backward.default` | RuntimeError：`torch.ops.aten.threshold_backward.grad_input` |
| prelu | `torch.ops.aten.prelu.default` | 无无条件拒绝壳；不等同完整运行支持 |
| _prelu_kernel | `torch.ops.aten._prelu_kernel.default` | 无无条件拒绝壳；不等同完整运行支持 |
| _prelu_kernel_backward | `torch.ops.aten._prelu_kernel_backward.default` | 无无条件拒绝壳；不等同完整运行支持 |
| glu | `torch.ops.aten.glu.default` | RuntimeError：`torch.ops.aten.glu.out` |
| glu_backward | `torch.ops.aten.glu_backward.default` | RuntimeError：`torch.ops.aten.glu_backward.grad_input` |
| log_sigmoid_forward | `torch.ops.aten.log_sigmoid_forward.default`、`torch.ops.aten.log_sigmoid_forward.output` | 无无条件拒绝壳；不等同完整运行支持 |
| log_sigmoid_backward | `torch.ops.aten.log_sigmoid_backward.default`、`torch.ops.aten.log_sigmoid_backward.grad_input` | 无无条件拒绝壳；不等同完整运行支持 |
| lerp | `torch.ops.aten.lerp.Scalar` | NotImplementedError：`torch.ops.aten.lerp.Tensor`、`torch.ops.aten.lerp.Scalar_out`、`torch.ops.aten.lerp.Tensor_out` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/acos.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/acos.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/acosh.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/acosh.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/asin.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/asin.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/asinh.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/asinh.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/atan.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/atan.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/atanh.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/atanh.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cos.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cos.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cosh.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cosh.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sin.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sin.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sinh.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sinh.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tan.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tan.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/erf.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/erf.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/erfinv.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/erfinv.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/relu.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/relu.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid_backward.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sigmoid_backward.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh_backward.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tanh_backward.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu_backward.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gelu_backward.py)（implementation）
- [固定来源 41](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/silu.py)（implementation）
- [固定来源 42](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/silu.py)（implementation）
- [固定来源 43](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mish.py)（implementation）
- [固定来源 44](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mish.py)（implementation）
- [固定来源 45](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/elu.py)（implementation）
- [固定来源 46](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/elu.py)（implementation）
- [固定来源 47](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/elu_backward.py)（implementation）
- [固定来源 48](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/elu_backward.py)（implementation）
- [固定来源 49](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu.py)（implementation）
- [固定来源 50](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu.py)（implementation）
- [固定来源 51](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu_backward.py)（implementation）
- [固定来源 52](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/leaky_relu_backward.py)（implementation）
- [固定来源 53](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid.py)（implementation）
- [固定来源 54](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid.py)（implementation）
- [固定来源 55](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid_backward.py)（implementation）
- [固定来源 56](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardsigmoid_backward.py)（implementation）
- [固定来源 57](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish.py)（implementation）
- [固定来源 58](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish.py)（implementation）
- [固定来源 59](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish_backward.py)（implementation）
- [固定来源 60](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardswish_backward.py)（implementation）
- [固定来源 61](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh.py)（implementation）
- [固定来源 62](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh.py)（implementation）
- [固定来源 63](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh_backward.py)（implementation）
- [固定来源 64](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/hardtanh_backward.py)（implementation）
- [固定来源 65](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold.py)（implementation）
- [固定来源 66](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold.py)（implementation）
- [固定来源 67](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold_backward.py)（implementation）
- [固定来源 68](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/threshold_backward.py)（implementation）
- [固定来源 69](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/prelu.py)（implementation）
- [固定来源 70](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/prelu.py)（implementation）
- [固定来源 71](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel.py)（implementation）
- [固定来源 72](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel.py)（implementation）
- [固定来源 73](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel_backward.py)（implementation）
- [固定来源 74](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_prelu_kernel_backward.py)（implementation）
- [固定来源 75](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/glu.py)（implementation）
- [固定来源 76](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/glu.py)（implementation）
- [固定来源 77](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/glu_backward.py)（implementation）
- [固定来源 78](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/glu_backward.py)（implementation）
- [固定来源 79](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_forward.py)（implementation）
- [固定来源 80](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_forward.py)（implementation）
- [固定来源 81](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_backward.py)（implementation）
- [固定来源 82](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log_sigmoid_backward.py)（implementation）
- [固定来源 83](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lerp.py)（implementation）
- [固定来源 84](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lerp.py)（implementation）
- [固定来源 85](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 86](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 87](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 88](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
