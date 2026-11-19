---
type: Guide
title: TorchNPU DTensor融合Attention布局、mask与本地派发
description: 记录四个融合Attention分片策略、mask广播、统计和头数改写，保留反向kwargs维度差异。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_attention.py
  role: implementation
created_at: '2026-11-11T06:32:18Z'
updated_at: '2026-11-11T06:32:18Z'
platforms: []
---

# TorchNPU DTensor融合Attention布局、mask与本地派发

## 固定实现范围

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_attention.py；两版完整AST相同，仅三处行尾空白不同。本文蒸馏四个Attention策略、反向kwargs布局推导及公共handler，不用注册成功推导产品、dtype、任意布局或数值已经验证。没有导入运行上游、通信、设备或性能实验。

## 额外分片候选有统一入口限制

npu_fusion_attention、其grad、v3及grad_v3总先加入全部复制候选。只有pse、padding_mask、prefix、actual_seq_qlen、actual_seq_kvlen、sink全部为None且keep_prob不小于1时才继续添加分片候选；源码检查是keep_prob < 1.0即返回，不是完整的概率取值校验。传入这些可选参数仍可能保留复制候选，不能把“没有分片候选”写成算子不支持。

额外候选由input_layout是否包含字符B或N决定，模块没有完整布局白名单、head整除、GQA比例或任意mask合法性校验。B和N两条规则分别加入，是否在多维mesh组合由外部register_sharding处理；这里没有S序列维的上下文并行候选。

| 候选 | q/k/v、attention输出及反向dq/dk/dv/dy | softmax_max/sum | atten_mask |
|---|---|---|---|
| B维 | Shard(input_layout.index('B')) | Shard(0)，按注释的BNS8统计布局 | 4维且shape[0]!=1时Shard(0)，其余复制 |
| N维 | Shard(input_layout.index('N')) | Shard(1) | 4维且shape[1]!=1时Shard(1)，其余复制 |

缺省mask对应None；保留的softmax_out或softmax_in按复制处理，存在时attention_in随q的B/N维分片。统计张量没有因为q的布局变化就改用q维度索引，不能把q、mask、统计全部套同一个Shard(dim)。

## 普通版与v3输出不是同一种标量合同

普通前向策略的四个Tensor输出后接三个None槽，源码注释对应整数类附加返回；v3为六个Tensor输出，seed/offset也声明Replicate。v3反向存在时把seed/offset输入设复制；普通反向的seed/offset/numels只是非张量槽。

普通grad的grad_pse在pse为None时输出placement为None，否则复制；v3 grad无条件把grad_pse设复制。四个分片分支的sink均不允许实际输入，但grad_sink仍声明Replicate，注释称其暂不支持。保留这些策略的静态输出差异，不据占位spec推导可选梯度一定有实际有效数据。

## 反向kwargs重新推导与一个需单独验收的维度差异

_infer_npu_fusion_attention_grad_kwargs_spec按首个输出dq的placements推导kwargs。非DTensorSpec值直接保留；复制输出对应复制kwargs。B/N分片下，softmax_max/sum分别映射Shard(0)/Shard(1)，attention_in沿q的B/N维，其他张量kwargs默认复制；遇到不在复制/B/N之列的placement报ValueError。新spec沿用原kwargs的mesh与tensor_meta。

mask分支在4维且对应B/N大小不为1时，实际追加的是dp_shard/tp_shard，即q的input_layout索引；这与前面候选策略固定给mask的Shard(0)/Shard(1)不总相同。例如SBH的B索引为1、BSND的N索引为2，不能据策略表认定这个kwargs推导会自动规范为mask的0/1维。本文记录局部实现差异，未执行运行路径证明它必然触发错误或被其他逻辑消除；应覆盖这些布局、mask广播和重分布目标逐项验收。

## handler在本地调用前修改什么

handler根据op的schema_info.needs_pytree决定是否展平位置参数以取得首个DTensor的device_mesh。内部input_fn遍历顶层args与kwargs.values，把普通Tensor用DTensor.from_local(mesh, [Replicate()], run_check=False)包装，再按原kwargs键顺序恢复字典。该转换不是任意嵌套容器的递归DTensor化，[Replicate()]也没有在此显式展开为多维mesh长度；要求首个展开参数已有device_mesh，不能宣称全普通Tensor调用也会自动找到mesh。

随后unwrap_to_op_info、传播分片，参与mesh的rank先重分布位置参数。前向使用local_kwargs，反向另外调用公共kwargs重分布helper。input_layout包含N时，不论是否实际选中N分片，都把head_num改为本地query在N维的size；普通/v3前向改第3位置参数，两个反向改第4位置参数。带N的布局通过本地shape得到头数，不是简单按world_size除全局head_num；不含N的布局不做这一改写。

四个入口分别调用torch_npu对应的普通/v3前反向函数；传入不匹配入口会报NotImplementedError，异常信息只提普通前反向，不能由这条信息否定实际v3分支。这里没有自动为不支持的组合换其他Attention算法。

## 非参与rank与全局注册副作用

mesh.get_coordinate为None时不运行本地算子；对每个输出spec构建占位：有tensor_meta的零维返回该dtype的零标量Tensor，其余返回该dtype的空Tensor；缺tensor_meta报RuntimeError，None spec用整数0。没有显式NPU设备参数，不能把这些占位当作正常全局结果或用来证实数值一致。最终统一由dispatcher.wrap处理。

模块末尾把四个自定义handler与旧_handlers合成新字典，同名四个键由本组覆盖，其他键保留；导入即发生赋值，模块没有本地撤销入口。优化验收需固定包版本和实际handler，记录策略、q/mask/statistics kwargs布局、head_num、本地shape与实际重分布通信，并比较前向和梯度；具体算子约束见[npu_fusion_attention](../apis/torch_npu/npu_fusion_attention.md)，公共布局辅助见[DTensor重分布与注册](torch_npu_dtensor_redistribution_and_registration.md)。
