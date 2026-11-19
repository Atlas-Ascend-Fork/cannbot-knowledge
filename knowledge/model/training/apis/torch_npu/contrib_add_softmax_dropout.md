---
type: API
title: add-softmax-dropout组合：融合门控与回退状态差异
description: 保存4D、尺寸和32整除门控，指出dim未消费及示例实际走回退路径。
tags:
- task.lookup
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-fuse_add_softmax_dropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-fuse_add_softmax_dropout.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-fuse_add_softmax_dropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/fuse_add_softmax_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/fuse_add_softmax_dropout.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# add-softmax-dropout组合：融合门控与回退状态差异

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 调用与门控

`fuse_add_softmax_dropout(training,dropout,attn_mask,attn_scores,attn_head_size,p=.5,dim=-1)`返回Tensor，逻辑为mask+scores/sqrt(head_size)，最后维softmax，再dropout。页面给的npu_fuse_add_softmax_dropout是局部Python参考函数名字，不能当另一个公共torch_npu融合算子。

两固定实现直接把scores解包为n,c,h,w，仅h在{128,256,384,512}且n*c被32整除才调用npu_dropout_with_add_softmax；这层没有校验w与h相同。融合路径training=False设drop_p=0，否则用p；回退路径调用传入dropout模块，未用该training/p参数，必须另外保持模块状态和概率一致。

## 参数与样例缺口

dim虽然出现在原型，两条路径均硬编码-1，不表示任意softmax轴已支持。发布样例将alpha=.125误传成head_size，p=axis=-1；主线更正head_size64、p=.1、dim=-1，仍用了不属于常规torch.nn的DropoutWithByteMask写法。页面scores h=30的例子实际走回退，不能证明融合Kernel成功或收益。

参考Python逻辑没有融合分支对training的单独处理，不能只按“等价”二字省略状态对照。底层byte-mask旧接口维护状态也需独立核对，未做数值或吞吐实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-fuse_add_softmax_dropout.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-fuse_add_softmax_dropout.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-fuse_add_softmax_dropout.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/fuse_add_softmax_dropout.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/fuse_add_softmax_dropout.py)（implementation）
