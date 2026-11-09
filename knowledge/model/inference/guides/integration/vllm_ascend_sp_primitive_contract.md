---
type: Guide
title: vLLM Ascend SP 原语接入：token轴、padding mask与PP边界
description: 接入SP算子时核对任意维token分片、二维归约、functional alias与fake形状，沿Kimi PP和草稿调用方验证gather裁剪及mask生命周期。
aliases:
- ascend_sp_shard_impl
- ascend_sp_padding_mask_impl
- ascend_sp_reduce_scatter_impl
- SP原语接入
tags:
- task.implementation
- topic.parallelism
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/common/ops/sequence_parallel.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_sequence_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_pp_sp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/dspark.py
  role: implementation
created_at: '2026-10-31T05:40:23Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T05:51:47Z'
---

# vLLM Ascend SP 原语接入：token轴、padding mask与PP边界

## 任务、版本与边界

将新模型的hidden、HC、残差或aux接入序列并行时，逐个标注完整token、TP分片和padding状态，先验证布局再判断通信收益。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的common/ops/sequence_parallel.py完整152行、专属算子UT完整100行和Kimi PP/SP CPU测试完整631行；Kimi模型只读MLP.forward及attn-res model.forward等列明范围，V4 MTP与V4.1草稿复用同SHA全文阅读证据。

本卡处理内部SP原语和调用方接线；全局开关、EP/DP门控及MoE布局见[SP MoE指南](../optimization/vllm_ascend_sequence_parallel_moe.md)，PP层分区和实际支持见[PP接入](vllm_ascend_pipeline_partitioning.md)。不把此处的token分片等同Ulysses/Ring注意力、recipes中的SP-TP-SP选型或所有FlashComm融合。没有整项硬件范围证据，保持draft/空平台。

## 四种操作分别接线

| 入口 | 此处行为 | 调用方仍需保证 |
| --- | --- | --- |
| sp_shard | 本地沿dim0补零到TP倍数，再取本rank连续块；不是集合通信或求和。 | 所有待对齐张量的token顺序、原始N和TP group一致。 |
| sp_padding_mask | 使mask与sp_shard的rank块同布局，新补行标True。 | mask作用范围、dtype/device及跨调用生命周期。 |
| sp_all_gather | 优先custom_all_gather，返回None时走通用TP all-gather(dim0)。 | 实际通信顺序/shape、按原N裁剪和DP有效行布局。 |
| sp_reduce_scatter | 公共入口断言二维，先补零行再优先custom_reduce_scatter，否则通用TP reduce-scatter(dim0)。 | 各rank输入是同一token顺序上的局部贡献，不能直接归约不同序列块。 |

_custom_collective在没有TP device_communicator或相应属性时返回None；存在则调用它，返回结果仍为None也会触发后备。异常没有在这里捕获，不能把“有fallback”理解为任意通信错误都会自动恢复。此处也没有检查custom返回值的shape/dtype或同步健康。

## 任意维分片与二维归约的区别

设原token数为N，P=TP，补行p=(-N)%P，每rank行数ceil(N/P)，起始rank×ceil(N/P)。_ascend_sp_shard_impl的F.pad参数按输入ndim构造，因此1D IDs、2D hidden和3D [N,hc_mult,H]或残差都补dim0；不能沿HC轴补齐。N=6、P=8时每rank一行，后两rank只有零PAD，mask应True，不能把这两行当有效token。

无padding时切片会clone，避免functional custom op返回输入view；有padding时切的是新分配的padded tensor。不要推广成所有输出stride/contiguous相同，或所有SP入口都保证相同alias行为。这里clone维护functional op的输入输出alias合同，与[跨流消费副本](../../runbooks/runtime/multistream_cross_stream_tensor_lifetime_clone.md)处理的通信流生命周期问题分别验收，不能据此一律增加或删除clone。reduce-scatter的对齐输入在通信前避免额外整张复制，但不由此保证具体communicator不复制或不别名。

_ascend_sp_reduce_scatter_impl按[pad,H]分配零并cat(dim0)，不是任意维padding实现；公共sp_reduce_scatter显式assert x.ndim==2。三维HC可直接shard或gather，并不意味着可直接交这个reduce-scatter；若要展平，应由模型定义可逆shape与归约语义并验证，不删除assert掩盖错轴。

## mask、fake实现与动态shape

mask为None时，sp_padding_mask从参考hidden_states的axis0分配N个False bool；参考也可以是positions。显式mask这里只断言首维等于N，不能认为已经检查一维、bool、相同device或正确token顺序。旧True行保留，新增padding为True；无补行的mask切片同样clone。

_ascend_sp_shard_fake保留其余维度、dtype/device，只把首维改ceil(N/P)；_ascend_sp_reduce_scatter_fake为[ceil(N/P),H]，mask fake为[ceil(N/P)]。它们生成形状用empty，不提供真实数值、alias或所有stride证明；N=0对应零行只是源码形状行为，所列UT没有完成真实空batch NPU通信验收。

ascend_sp_shard_impl与ascend_sp_reduce_scatter_impl注册了mutates_args=[]、PrivateUse1和fake；ascend_sp_padding_mask_impl的注册不同，带needs_fixed_stride_order，不能复制前两者的全部注册属性。注释解释custom op用于把modulo padding隐藏于Dynamo、避免shape烘焙风险，这是设计意图；已读CPU impl/fake测试没有验证torch.compile、动态bucket或图重放。图复用持久position尾段还可能属于[stale position越界](../../runbooks/runtime/graphmode_padding_stale_position_gatherv3_out_of_range.md)的另一签名，fake shape不能代替实际尾段初始化。

## gather裁剪与PP状态边界

sp_all_gather本身不保存N，不做unpad，也不识别每个DP rank的有效区。调用方在进入依赖真实positions/slot metadata的计算前按原始布局恢复，输出边界也需裁去PAD。总shape相同不代表有效token连续；DP交错有效区继续按SP MoE指南验证。

所读Kimi MLP在SP时先gather再让权重分片处理同一组tokens，之后reduce-scatter；attention片段在调用前gather并裁到positions长度。不能让不同rank各自的序列块直接进入同一权重归约，否则live/PAD混合。这里只闭合MLP.forward与模型forward，attention中段不是完整算子/通信实现证据。

Kimi attn-res模型的每个PP stage从完整序列hidden/residual/aux进入，随后分别shard，残差bank在shard后按本地token数分配。非末stage在边界gather并裁三类tensor，再由下一stage重新shard；末stage可把main和aux沿feature维拼后一次gather，裁N再按hidden_size拆分，不能当成沿层轴或token轴拼接。

这条forward在attn_res_block_size=None时委托Native，且0.32分支处理step签名差异；不能把本地attn-res路径的全部细节套到委托路径。PP transport/持久buffer、真实通信与全部Runner仍要单独闭合；SupportsPP、源码中出现gather或CPU测试通过的定义都不能替代完整执行证明。

## mask恢复由模型拥有

这些原语不替调用方管理forward_context。Kimi已读model.forward把context.is_padding换成分片mask，正常返回也未在本方法恢复；相关CPU测试为各stage创建新context，不能由测试通过定义推断任意复用安全。

[V4普通MTP](vllm_ascend_v4_mtp_adapter.md)正常路径保存并恢复原mask，但没有异常finally；[V4.1草稿](vllm_ascend_v41_dspark_adapter.md)正常路径也保留分片mask。接入新循环、PP或重放时记录谁创建/复用context、何时恢复，以及异常后下一次输入的完整N；不能给所有模型统一补一条“自动恢复”结论。

## 测试证据与实际验收

100行文件的七个CPU测试定义覆盖3D N6/TP8各rank、2D对齐切片与不别名、1D IDs、fake ceil、RS补零、mask True PAD及mask不别名。RS测试把_custom_collective替成identity，期望的是3×4补成4×4；它没有验证真实TP2输出2行、跨rank求和或NPU communicator。

631行Kimi文件通过AST抽取部分生产定义、替换基类/装饰器和全局，使用CPU attn_res参考及thread barrier模拟collectives。pipeline矩阵48组包含SP开关、raw/materialized、未对齐N3、TP16/N8和空层stage；这里的空stage不是全局N=0通信测试。32组aux合同测试和mapper/host计数测试另有各自边界，fixture gate不取代生产FlashComm门控。

本次没有执行这些测试、上游import、安装/build、图、服务或NPU。实际交付至少记录每个入口前后shape/stride/alias、N/p/rank、mask、通信分支、PP三类状态及有效行；先在相同输入上对齐无SP参考，再验证padding尾rank、TP1/多TP、重复/异常调用和图bucket。收益同时测通信、clone/pad临时内存与端到端耗时；错误时回到匹配版本的无SP/已有正确通信路径并保留诊断，不修改assert或吞异常。
