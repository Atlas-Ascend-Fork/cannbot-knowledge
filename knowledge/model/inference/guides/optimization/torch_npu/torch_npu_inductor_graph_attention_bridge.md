---
type: Guide
title: TorchNPU Inductor Attention图桥的Meta、scale与Autograd边界
description: 区分图桥七Tensor返回、位置与关键字scale分支、Meta布局及Autograd参数槽差异。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/pattern_match/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/pattern_match/npu_fusion_attention_graph.py
  role: implementation
created_at: '2026-11-11T06:58:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Inductor Attention图桥的Meta、scale与Autograd边界

## 固定实现与启用范围

依据PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的pattern_match包入口及npu_fusion_attention_graph.py。固定发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b的这些路径没有Git条目，只说明路径差异，不否定发布其它Attention能力。未导入Library注册、执行包装、编译、autograd或设备实验，保留draft和未知平台。

加载模块时在npu_graph命名空间定义npu_fa及npu_fa_backward两条Schema，并为PrivateUse1和Meta注册实现；末尾把公开Python函数挂到torch_npu.npu_fusion_attention_graph。pattern_match/__init__导入并导出它，但本组没有闭合完整后端初始化调用者，不能说导入torch_npu必启这条桥。它调用的是普通npu_fusion_attention前反向，不是v3六Tensor输出或CP Ring Attention。

## 七Tensor包装与scale位置差异

运行前向仅当len(args)>8时把第8位置scale改为倒数，再调用普通FA；传scale关键字不走该分支。except捕获IndexError，不会捕获倒数的ZeroDivisionError。普通FA返回的三个整数seed/offset/numels被torch.tensor([value], requires_grad=False)包装成Tensor，没有显式device；softmax_max/sum/out被设requires_grad=False。

运行反向若kwargs含scale_value，则无条件取倒数，再透传给普通FA grad；它没有在本地把Tensor形式的seed/offset/numels显式转成Python整数。NpuGraphAttentionFunction前向使用scale关键字，而反向使用scale_value关键字，二者本地倒数分支不同，不能自行写成所有调用形式scale合同完全相同。这里记录静态差异，未证明某个真实匹配或训练必然报错。

## Meta不能认证任意布局与可选梯度

前向Meta先按query的0/2维取B/S1，head_num取N，另取key第2维；仅对BSH和SBH分支重定B/S索引。attention输出为与query同shape/dtype的contiguous Meta，max/sum是[B,head_num,S1,8] FP32，softmax_out空，RNG三项为值0、形状[1]的Meta Tensor；没有完整布局白名单、q/k/v兼容、head整除或任意stride证明。

反向Meta给dq/dk/dv与各输入同shape的contiguous Meta，dpse为空Tensor但返回时按`if pse`选择它或None，不能改写成`pse is not None`的健壮存在性检查；sink缺省时仍给标量Meta，否则empty_like(sink)。Schema将五个返回都声明Tensor，不由局部占位推导所有可选输入都已有一致运行返回。

## Autograd保存、返回与参数槽数

Function前向保存q/k/v、pse、padding_mask、atten_mask、三个softmax结果、attention及三项RNG，把head_num/layout/scale/keep_prob、窗口、序列及稀疏控制写ctx；返回全部七项。backward只消费grad_result0作为dy，其余六个梯度形参未使用，再取保存结果调用图桥反向。

本地forward除ctx有19个输入，公开包装apply也传19个，而backward的返回tuple实际有26个槽：dq/dk/dv和grad_pse之外均为None，取得的grad_sink没有映射回输入。该包装也没有暴露Schema中的softmax_layout/sink参数。不能把保存状态或Meta注册当作完整autograd参数数目与梯度支持已经验收的证明；应对照真实调用、RNG类型/device、scale及gradcheck逐项验证，本文未执行这些验证。

Pass加载与设备限定predicate见[编译资源与注册](torch_npu_inductor_compile_resources_and_passes.md)，普通DTensor FA派发见[布局合同](../../../../training/guides/torch_npu_dtensor_fused_attention_layout_dispatch.md)；这些路线有各自入口和返回结构，不相互继承运行保证。
