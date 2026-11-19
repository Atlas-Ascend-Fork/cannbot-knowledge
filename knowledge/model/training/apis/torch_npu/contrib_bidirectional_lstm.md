---
type: API
title: contrib BiLSTM：双单向拼接与旧接口迁移
description: 保留废弃计划、序列维翻转和实际Tensor返回，不把旧docstring视为完整原生LSTM合同。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-BiLSTM.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-BiLSTM.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-BiLSTM.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/bidirectional_lstm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/bidirectional_lstm.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# contrib BiLSTM：双单向拼接与旧接口迁移

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与实际前向

`BiLSTM(input_size,hidden_size)`为双向序列模块，输入例为(seq_len,batch,input_size)。两固定实现创建独立fw_rnn/bw_rnn的单向nn.LSTM；反向输入在第0维flip，结果再flip后在第2维cat，返回(seq_len,batch,2*hidden_size)的Tensor。

forward实际只接inputs，未接(h_0,c_0)，也不返回(h_n,c_n)；docstring复制原生LSTM的初始状态、PackedSequence和输出元组不能作为这个包装已支持的证明。PackedSequence还须经过flip的实际能力核对，不能按那段注释直接承诺。

## 迁移边界

页面两版本均计划废弃并链接外部小算子组合，构造也发FutureWarning。小算子外链不在本固定三仓范围，未自动摄取或执行。实现旧注释称当时NPU不支持bidirectional=True，是历史动机，不能泛化为当前所有原生LSTM都禁止双向。

替换需核对两个方向的权重、偏置、序列与batch维、初始状态和返回格式；不能仅因输出最后一维相同就把检查点直接换类。本卡未加载任何状态文件。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-BiLSTM.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-BiLSTM.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-BiLSTM.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/bidirectional_lstm.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/bidirectional_lstm.py)（implementation）
