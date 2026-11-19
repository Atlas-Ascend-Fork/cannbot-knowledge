---
type: Guide
title: TorchNPU上下文并行的注册作用域与序列策略
description: TorchNPU上下文并行的注册作用域与序列策略的本地规则、适用条件及未核对外部边界。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/experimental/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/experimental/_context_parallel/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/experimental/_context_parallel/_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/experimental/_context_parallel/_npu_attention.py
  role: implementation
created_at: '2026-11-11T06:49:16Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU上下文并行的注册作用域与序列策略

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的experimental/_context_parallel本地实现及包入口。固定发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`在此路径的Git树没有条目，只记录路径差异，不据此宣称发布软件栈没有任何CP能力。没有导入执行上游、注册或通信，也没有设备、性能或编译实验。

## 公开包装与两层全局改动

experimental顶层只导出context_parallel并把其__module__设为该包；_context_parallel子包先导入NPU _attention触发副作用，再从Torch原生模块导出上下文、unshard、rotate及负载均衡相关对象。三个本地包装直接转发args/kwargs，functools.wraps仅拷贝指定名称、限定名、doc和annotations；原生上下文本体、分片和负载均衡算法没有在本组核对。

NPU _attention在导入时把原生模块_enable/_disable_cp_dtensor_dispatcher两个函数替换为NPU版本，没有在此保存/恢复这两个模块属性。后续disable恢复的是dispatcher handler、策略及隐式复制开关，不能解释为撤销全部导入注入。

## CP候选扩展不等于handler支持任意布局

策略入口接收一个OpSchema，将OpStrategy转换为首候选的output_spec，TupleStrategy沿children递归；先调用普通DTensor v3前/反向策略获取复制、batch和head候选，再追加序列候选。序列维取layout中S的索引，否则取T；二者皆无时只展开原候选。

只有pse、padding_mask、prefix、actual_seq_qlen、actual_seq_kvlen、sink全部严格为None且keep_prob不小于1，才加CP候选；handler中“空list/tuple视为未传”的检查与这里严格None不同。策略未在此检查BNSD四维、sparse_mode范围或任意mask是否合法，不能由存在序列候选就绕过实际handler限制。

CP前向把q/k/v、attention_out、softmax_max/sum沿seq_dim分片，softmax_out、seed/offset复制；mask沿原复制候选保留Replicate或None，不随KV旋转。反向把q/k/v/dy及存在的softmax_max/sum/attention_in沿seq_dim分片，dq/dk/dv沿seq_dim，grad_pse/grad_sink复制；其他槽沿复制模板。input_index按算子Schema返回数取值，再把输出和输入placement拼接交外部mesh展开。

基础batch/head规则见[DTensor融合Attention](torch_npu_dtensor_fused_attention_layout_dispatch.md)；CP增加序列布局，不意味着同时给任意TP/CP多维组合证明。

## 进程组选取与版本兼容入口

一维mesh直接get_group；多维mesh按指定q/k/v（反向另含dy）spec顺序寻找第一个Shard(seq_dim)，返回其mesh维进程组。找不到则调用无维度get_group，可能由外部报错；没有在本helper核对所有输入序列分片同一维或多个CP维是否冲突。

策略context获取先尝试_single_dim_strategy_context，ImportError才取_op_strategy_context，首个成功结果缓存；不是在本地按版本号字符串判定。注册两个NPU v3策略各用RuntimeSchemaInfo(1)，调用context.__enter__并保存在字典；字典非空则直接跳过。注销逐个__exit__再清字典，没有通用嵌套引用计数。

## enable/disable保存什么

enable以_cp_prev_handlers非空为重复启用保护，保存两个NPU v3 handler旧值（不存在时None），用合并字典覆盖这两个键，并保存全局_allow_implicit_replication后设True，让普通非标量Tensor能在unwrap时被隐式复制。之后注册NPU CP策略，再调用原生register_cp_sharding_rules。

disable把旧handler值恢复，原来不存在的键删除，清保存表；恢复隐式复制开关、退出NPU策略context，再调用原生unregister_cp_sharding_rules(clear_the_cache=False)。其它handler键保留。这个保存表是模块全局状态，不是线程局部对象，也不是每次嵌套enable都压栈；没有锁、异常事务回滚或部分注册失败后的完整恢复机制。不要把重复enable保护当成任意重入/并发上下文都独立安全。

源码注释提到编译友好派发，但支持页仍需独立核对；本组没有运行torch.compile或证明与PP、负载均衡组合已经成立。公开BNSD、causal和编译边界见[原生TP/CP限制](torch_npu_native_tensor_parallel_constraints.md)，计算与状态路径见[Ring Attention状态](torch_npu_context_parallel_ring_softmax_state.md)。
