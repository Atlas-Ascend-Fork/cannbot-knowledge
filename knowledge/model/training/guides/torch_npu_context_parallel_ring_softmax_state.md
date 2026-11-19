---
type: Guide
title: TorchNPU上下文并行的Ring Attention与Softmax状态
description: TorchNPU上下文并行的Ring Attention与Softmax状态的本地规则、适用条件及未核对外部边界。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/experimental/_context_parallel/_npu_attention.py
  role: implementation
created_at: '2026-11-11T06:49:16Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU上下文并行的Ring Attention与Softmax状态

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的experimental/_context_parallel本地实现及包入口。固定发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`在此路径的Git树没有条目，只记录路径差异，不据此宣称发布软件栈没有任何CP能力。没有导入执行上游、注册或通信，也没有设备、性能或编译实验。

## BNSD与causal语义是handler的实际入口

两个v3 handler先unwrap和propagate，output_sharding为None或needs_redistribute即报RuntimeError；这里不自动修复不匹配输入布局，也没有普通handler那样的非参与mesh rank空结果分支。布局字符串可upper后比较BNSD，并要求q/k/v均四维，但后续头数修正等仍使用原input_layout，不能由校验可忽略大小写推出所有下游路径都会统一规范化。

拒绝实际存在的pse、padding_mask、prefix、actual_seq_qlen、actual_seq_kvlen、sink，空list/tuple视未传；softmax_layout只接受None或空字符串。sparse_mode仅0/1/2/3，非空atten_mask仅在1/2/3可通过。1/2/3在ring调用中都变为is_causal=True，原mask不逐块传入：每一步重新构造query序列长度S的S×S uint8上三角mask并用sparse_mode=1。不能据“输入mask通过causal入口”推广到任意自定义mask、不同稀疏模式差异或任意q/k长度组合。

前向按位置索引取参数并将带N布局的head_num改为本地q的N维大小；反向从local_kwargs取统计、输出、RNG和配置。私有Schema归一化和默认参数由外部派发提供，不在这里补成支持所有位置/关键字混合形式。

## 逐步算子与最终attention输出的来源

前向closure为每步调用npu_fusion_attention_v3，返回六项中的attention及softmax统计、seed/offset；scale缺省1/sqrt(D)，keep_prob=1-dropout_p。head_num、input_layout、pre/next_tockens、inner_precise、gen_mask_parallel、sync、softmax_layout按透传字典或默认值传递，unsupported参数显式None。

closure给原生_templated_ring_attention的每步结果使用当前步LSE：取[B,N,S,8]统计的slot0，用float max+log(float sum+1e-10)，不是累计合并后的LSE。最终attention输出来自原生模板result[0]；本地维护的merged_attn只供op合并统计路径使用，不作为最终输出替代原生合并器。

根据npu_ring_attention_update是否callable，在closure创建时选op或Python统计合并；这不是op失败后自动重试Python。op路径把BNSD attention经permute/contiguous/view转SBH，FP32统计交ring_update，再按头数转回BNSD；H不能被head_num整除时报错。涉及连续化和布局转换，是否值得不能只凭op名字判断。

Python路径按新max重标定两组sum，指数和sum计算用FP32；convert_to_f32决定输入统计先转FP32及最终累积类型。第一次保存统计；后续统计S维不同则按当前S_half更新累计张量尾半段，其余保留。这依赖原生causal半块协议，局部实现没有认证任意不同长度chunk。

## 统计与单组RNG通过autograd流转

每一步把merged_max/sum的clone及seed/offset追加到本卡调用的step_caches；不是模块级前反向缓存，但仍有每步clone和列表持有成本。最终六元组取最后一项合并统计及最后一步seed/offset，另给空softmax_out；若没有步骤则生成[B,N,S,8]零统计与零int64 RNG占位。这个回退不证明无步骤attention有有效数值。

反向从autograd kwargs读取最终merged_max/sum、attention_in和seed/offset，统计/输出为DTensor时取_local_tensor；重建LSE后交原生ring backward。每一步closure在query被切成尾半段时对应切统计，并调用npu_fusion_attention_grad_v3，返回dq/dk/dv；grad_pse/grad_sink用空Tensor占位。它使用保存的同一组seed/offset，不消费模板传入的philox参数来逐步重新构造RNG；源码注释类比single philox不构成独立随机性验证。

策略当前keep_prob<1时不增加CP候选，尽管closure具备dropout参数；不能由存在RNG代码宣称CP dropout已支持。反向缺统计/attention/RNG时没有完整可选输入防御，应按真实autograd合同验收。计算模板、通信旋转、负载均衡实现属于外部，本组未运行数值、梯度或分布式测试；注册恢复与输入布局见[CP作用域](torch_npu_context_parallel_dispatcher_scope.md)。
