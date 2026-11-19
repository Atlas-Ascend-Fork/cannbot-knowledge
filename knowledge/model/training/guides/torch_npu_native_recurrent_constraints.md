---
type: Guide
title: 原生RNN的NPU限制：变长、投影与编译路径
description: 区分LSTM、GRU及Cell的公开范围，记录LSTMCell黑名单文字与DynamicRNNV2实现不一致及950未核对项。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/appendixes/example_of_adding_a_binary_blocklist.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmCellKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/appendixes/example_of_adding_a_binary_blocklist.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_gru.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_lstm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T10:01:21Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生RNN的NPU限制：变长、投影与编译路径

## 固定来源与入口区别

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生API支持页，范围为其明列的A2/A3训练系列与950DT，不扩展950PR或发布组合。同提交PyTorch2.7.1、2.9至2.14的相关完整条目已逐版本对照；页面链接中的版本号、HTML标识及排版差异不当成能力增减。文档中的“已验证”是上游清单口径，本卡只读审阅，未运行设备或性能实验。

RNN/GRU/LSTM模块与Cell不是同一条支持路线，不能把某个Cell成功运行推导为整层变长序列、投影或dropout已支持。

| 入口 | 明确限制 |
| --- | --- |
| torch.nn.LSTM | input仅FP32，不支持proj_size、不支持dropout，input不支持二维 |
| torch.nn.GRU | 不支持dropout、不支持变长序列输入 |
| torch.nn.GRUCell | input仅FP16/FP32 |
| torch.nn.RNN、RNNCell | 三类产品列支持，条目未给额外dtype/参数限制，不据此补造全规格 |
| torch.nn.LSTMCell | 仅A2/A3产品段；jit_compile=False与黑名单提示见下文，不从其他Cell推导950支持 |

清单写“不支持dropout参数”时，不将其扩展为自行在计算链中删除dropout便保持模型语义；同样，padding/手工逐步Cell循环也不是GRU变长训练的自动等价替代。需要保留真实长度、状态、输出和梯度的参考定义。

## LSTMCell黑名单的来源冲突

七个中文版本页均把LSTMCell放在910b/A3条件段，并称jit_compile=False时需把DynamicGRUV2加入NPU_FUZZY_COMPILE_BLACKLIST。附录只展示通过torch.npu.set_option传入一个或逗号分隔多个名称的写法，不证明列入任何名字都能修复当前失败。

静态对照OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`：aclops/LstmCellKernelNpu.cpp的LSTMCell经npu_lstm_cell构造DynamicRNNV2，属性cell_type=LSTM，反向为DynamicRNNV2Grad；并非文档提到的DynamicGRUV2。因此不能把该文字作为已确认的LSTMCell黑名单修复配方，也不自行改成另一个名字后宣称已验证。需从实际包、失败算子及CANN版本确认具体路径。

## 新主线ACLNN路径不覆盖公开产品缺项

同一OpPlugin主线的opapi LSTMCell先检测aclnnThnnFusedLstmCell兼容性；缺失时回ACL Op。ACLNN-only路径用两次matmul生成gate，再调_thnn_fused_lstm_cell；其余仍回旧路径。融合入口接受同dtype的float/half/bfloat16，代码注释称BF16从950起，最终由底层按SoC判定。

这些分支只证明固定实现有该路径，不足以将TorchNPU公开清单未列的950 LSTMCell认定为已确认支持，也不把两个主线当已配套发行版。公开nn.LSTM与npu_lstm_cell/_thnn内部算子是不同接口，内部工作区、gate和反向张量不能直接替换公共Cell的(h,c)返回。

## 验证边界

按实际选中实现检查输入rank、dtype、状态、序列长度、层数、训练/推理与梯度；先定位编译/调度路径，再判断黑名单是否相关。缺少说明不代表所有组合已验证，源码路径存在也不等于数值或性能结果。本卡未修改JIT/黑名单配置、编译或执行上游。

## 七版本的packed序列辅助入口

同一固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的七份torch.nn页对pack_padded_sequence、pad_packed_sequence、unpad_sequence均列A2/A3训练系列及950DT支持，但未在这些条目给出另一份完整dtype、CPU长度或布局细表。pad_sequence则明确sequences仅FP16/FP32；不能因辅助函数可用就认为GRU的变长输入限制已经解除，也不把“支持packed辅助对象”当成LSTM/GRU全部参数与反向已验证。

这些工具的长度与批次接线需按具体模块/实际包核对，不把FIA的TND累计长度规则移植到RNN工具。本文仍没有执行packed序列或设备实验。

## RNNBase与PackedSequence对象条目

七版本页对RNNBase及flatten_parameters、pack_sequence和unpack_sequence列三类产品。PackedSequence主条目input列FP32/INT64，to子条目self同样列这两类，count/index子条目列self FP32。batch_sizes/data/is_cuda/is_pinned/sorted_indices/unsorted_indices仅列产品，未给全部数据字段的设备和dtype合同。

对象中数据、长度、索引和属性返回值是不同角色，不能将self条目的FP32解释成count/index返回浮点数，也不将一个字段的产品支持提升为所有字段必须在NPU。辅助工具支持仍不解除前述GRU变长输入及LSTM参数限制。本文没有构造或移动PackedSequence。

## 英文LSTMCell的明确950DT标记

英文七版本对LSTMCell明确950DT不支持，中文只列A2/A3。这使“中文未收录”和“英文明确不支持”成为不同证据，不再仅按中文缺项描述950；OpPlugin内部ACLNN分支存在仍不能覆盖公开产品表或解决DynamicGRUV2文字与DynamicRNNV2实现差异。

## 双语黑名单附录的示例粒度

中英文附录均以torch.npu.set_option传入NPU_FUZZY_COMPILE_BLACKLIST，单名字例为DynamicGRUV2，多个名字例为逗号分隔的DynamicGRUV2,DynamicRNN，名称要求按真实场景替换。该页只展示配置写法，不给通用算子选择、捕获或性能合同，也不消除前述LSTMCell公开提示与DynamicRNNV2实现的冲突；本卡未设置黑名单或运行样例。

## 旧低层RNN的输出协议

[旧GRU/LSTM API](../apis/torch_npu/legacy_gru_and_lstm.md)返回六/八份结果并携带训练中间量，不是nn.GRU/LSTM的高层返回结构。旧页中bool的“默认”与两个固定注册的必传形参分开；LSTM单层及不支持packed、双向、batch_first等限制不能由参数名字抵消。迁移须重建门/权重顺序和反向消费。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/appendixes/example_of_adding_a_binary_blocklist.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmCellKernelNpu.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/appendixes/example_of_adding_a_binary_blocklist.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_gru.md)（primary）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_lstm.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
