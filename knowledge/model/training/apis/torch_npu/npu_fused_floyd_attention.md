---
type: API
title: npu_fused_floyd_attention：五维双路径注意力与反向统计
description: 说明 Floyd 注意力的五个输入、max/sum/out 返回顺序、形状倍数和反向非确定性。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_floyd_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_floyd_attention.py
  role: example
created_at: '2026-11-09T07:57:02Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# npu_fused_floyd_attention：五维双路径注意力与反向统计

## 版本与范围

本卡依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`；发布子模块 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的对应页另作版本约束。主线候选与ascend_26_0_pt28组合分别管理，不能只因接口同名推断可混用。 产品页列A2/A3；面向训练，支持PyTorch≥2.6。页面未给出完整图后端支持矩阵，不从Meta注册推断所有编译后端均可用。

## 接口与输出

```text
torch_npu.npu_fused_floyd_attention(query_ik, key_ij, value_ij, key_jk, value_jk, *, atten_mask=None, scale_value=1.) -> (softmax_max, softmax_sum, attention_out)
```

先将两条QK关系的分数相加并缩放、施加mask后做Softmax，再用相同权重聚合两条V路径并相加。额外序列轴参与批处理，不能用普通四维FA直接替换而不核对轴语义。

|输入/输出|形状|类型与含义|
|--|--|--|
|query_ik|B,H,N,M,D|FP16/BF16 ND|
|key_ij、value_ij|B,H,N,K,D|与query同dtype|
|key_jk、value_jk|B,H,K,M,D|与query同dtype|
|atten_mask|B,1,N,1,K|可选BOOL/UINT8；1排除、0参与|
|softmax_max、softmax_sum|B,H,N,M,8|FP32，供反向使用的统计量|
|attention_out|与query一致|最终结果，第三个返回值|

value_jk参数行单独列FP32，但同页综合约束要求五个输入dtype一致，其他四项只列FP16/BF16；本卡采用共同支持的FP16/BF16，不把该单行扩展为混合输入支持。

## 形状与反向契约

B∈[1,2048]、H∈[1,256]；N∈[16,1M]且16整除，M/K∈[128,1M]且128整除，D仅32/64/128。两组K/V各自shape相同，query与key_ij的B/N/D相同。

Schema生成的两个统计量尾轴固定8，与Meta一致；autograd声明前两个输出不可微、只有attention_out可微，并保存输入、attention_out与max/sum供五个输入梯度计算。反向不支持确定性，不能以开启全局确定性开关替代该接口的保证。显式backward返回五个梯度，不包括mask或scale梯度。


## 验证边界

按实际软件栈验证目标shape、dtype、mask语义和输出，再比较稳态性能。本卡只做固定文档与实现的静态审阅，未执行上游代码或NPU数值/性能测试。

- [软件栈版本与来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 生成调用与Meta的验证限度

两固定OpPlugin版本的Schema都为PyTorch v2.6起生成aclnnFusedFloydAttention调用；反向生成aclnnFusedFloydAttentionGrad。前向分配两个FP32的[B,H,N,M,8]统计量和与query同形同dtype的最终输出，反向按query、key_ij、value_ij、key_jk、value_jk依次分配五个梯度。导出的backward参数把attention_out放在统计量前，实际生成ACLNN调用却把softmax_max、softmax_sum、attention_out排在一起，调用时应使用公开参数顺序，不手工照底层调用位置拼参。

两版derivatives均只有第三个返回值可微，反向读取同一次前向的query/K/V、attention_out与max/sum；不能把Softmax后的概率当softmax_sum，或用另一个shape/scale/mask调用的统计量代替。Meta只创建这些形状的空张量，没有完整验证K/V形状、产品dtype组合、mask内容和各轴范围；Meta可构图不证明设备入口支持。固定TorchAir的Python快照内未找到该专用转换器，不以这一静态搜索宣称所有编译路径都明确不支持。

## 显式einsum参考与测试缺口

设query轴为b,h,i,k,c，邻接key/value为b,h,i,j,c，另一条key/value为b,h,j,k,c。两项QK都归约c，得到b,h,i,k,j，再沿j做Softmax；两项PV再归约j得到b,h,i,k,c。不能把额外i轴合并进一个普通序列轴后直接套四维FlashAttention，或先对两条QK各做Softmax再相加。mask[B,1,N,1,K]在head与M轴广播，1表示排除。

同名主线/发布测试各155行、两个方法都由unittest.skip跳过，原因注释为CI版本不支持，只标Ascend910B。测试覆盖意图是BF16、B/H=1、N16、M/K256、D64、正scale=1/sqrt(D)，分别检查前向统计量与autograd五梯度、显式backward五梯度；发布与主线的完整29行差异只有空白。它们不构成A3、FP16、全部边界、性能或真实反向验证。

两个方法都先创建随机mask，再覆盖为全零mask，因此没有有效检查被屏蔽的位置、全屏蔽行或UINT8掩码。参考实现先把BOOL mask乘-4e9加到QK，再对整体乘scale；文档公式写mask加在已缩放分数上，实际公开mask又是BOOL/UINT8。两者在正scale且非极端输入时可能都达到排除效果，但不能据此推导任意加性mask、零/负scale或全屏蔽行语义。测试里的truncated_normal把越界样本置0而非重采样，也不据名字当成一般截断正态分布。

稳态复核应保留前向原始统计量，分别比较五个梯度，并增加真实非零mask、合法非对称N/M/K、FP16及目标产品用例；统计量尾轴8是接口输出布局，不能把它当8个注意力头。反向非确定性的文档限制仍保留。本卡只完成固定源码静态审阅，没有执行上游或登记verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_floyd_attention.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_floyd_attention.py)（example）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_floyd_attention.py)（example）
