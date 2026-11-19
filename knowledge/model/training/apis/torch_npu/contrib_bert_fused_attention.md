---
type: API
title: BERT融合注意力旧包装：NZ约束、首次检查与LayerNorm返回
description: 区分两个Function的参数、输出和梯度，保留一次校验缺口及keep_prob默认身份。
tags:
- task.lookup
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-npu_fused_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention_with_layernorm.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/fused_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/fused_attention.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# BERT融合注意力旧包装：NZ约束、首次检查与LayerNorm返回

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 两个入口

`npu_fused_attention(hidden_states,attention_mask,query_kernel,key_kernel,value_kernel,query_bias,key_bias,value_bias,scale=1,keep_prob=0)`返回context。发布另有with_layernorm变体，在偏置后增加gamma/beta，**实际返回(context,norm)二元组**，不是页面单一Tensor；该变体计划废弃，推荐npu_fusion_attention与nn.LayerNorm组合，替换需另核对数据路线和返回。

主线普通页补充hidden_states二维、行数32倍数、宽768或1024；mask为(B,1,S,S)，权重二维且第0维768/1024，前五Tensor格式FRACTAL_NZ(29)，三个bias为ND(2)。两固定源码已有这些检查，内部head_dim固定64，序列长从hidden行数/batch推算；不支持任意隐藏维或注意力布局。

keep_prob描述1−drop_rate、默认0，与常见“无dropout”设1不同；不静默更正默认或把两个概率名互换。scale默认1，不能照抄其他注意力的缩放约定而忽略本包装。

## 首次检查与反向

_check_compatibility_once由两个入口共享；装饰器在检查前就置called=True，第一次失败或后续换形状/格式也不会再次做该Python校验。校验通过/不再报错都不是所有后续调用合法的证据。

普通路线在no_grad中做QKV线性/重排，并由自定义backward调用score_grad、qkv_grad建立输入与投影梯度；attention_mask不返回梯度。withLN还保存归一化结果/统计、gamma/beta并消费grad_norm，不能丢弃第二输出后就承诺与任意LayerNorm排列等价。源码没有完整错误恢复或任意高阶梯度保证，未运行反向或数值试验。

- [当前融合注意力接口的独立合同](npu_fusion_attention.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-npu_fused_attention.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-npu_fused_attention_with_layernorm.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/fused_attention.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/fused_attention.py)（implementation）
