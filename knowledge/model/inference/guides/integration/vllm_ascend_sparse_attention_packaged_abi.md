---
type: Guide
title: vLLM Ascend稀疏Attention封装：DSA缓存元组与DSL输出ABI
description: 核对DSA no_compile层、capability控制的压缩cache元组和实际metadata消费，以及QLI/QSLI/混合量化SparseMLA的schema、Fake形状、延迟导入与输出缓冲，避免将编译推形或ops包可导入当完整kernel支持。 另保留3164删除need_gather_q_kv的DSA custom op签名迁移。
aliases:
- AscendDeepseekSparseAttention
- dsa_forward
- vllm_ascend::quant_lightning_indexer
- vllm_ascend::quant_sparse_lightning_indexer
- vllm_ascend::mixed_quant_sparse_flash_mla
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/dsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/packaged_attention.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/dsa.py
  role: primary
created_at: '2026-11-03T06:33:14Z'
updated_at: '2026-11-03T06:53:21Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend稀疏Attention封装：DSA缓存元组与DSL输出ABI

固定Main ceac1a2，完整技术程序阅读DSA wrapper290行和packaged_attention648行。这里聚合框架调用/缓存/输出ABI；实际DSAAttention backend和外部ops DSL模块仍需独立来源与运行验证，没有执行导入、NPU、图或精度实验，保持draft/空平台。

## DSA从forward context消费缓存，而非签名参数

AscendDeepseekSparseAttention保存投影、norm、sink、indexer/compressor/SWA模块并建立内部DSAAttention；外部prefix注册到static_forward_context，重复名称明确拒绝。forward按hidden shape分配empty output，经vllm.dsa_forward以prefix找到no_compile_layers中的实际对象；positions、显式kv_cache和attn_metadata参数不在此forward直接传给算子，consumer从forward context取真实metadata。

dsa_forward为eager_break_during_capture边界。metadata缺失仍调用内部impl、传None cache/metadata，而不是本wrapper自动计算正确zero结果；need_gather_q_kv只有为真才显式传True。custom op声明mutates output，Fake直接返回None，不计算值或验证完整shape。

实际cache始终包含SWA。compress_ratio>1才取compressor state和压缩KV，压缩KV在virtual_engine存在且为list/tuple时选对应项；ratio4另取indexer compressor state及K/scale。DSV4_COMPRESSED_CACHE capability为真时还解包indexer_full_cache，最终元组7项，否则6项；后端参数顺序必须一致，不能把None槽删除后再压缩成短元组。

unfold_kvcache只递归展开长度1的list，不展开tuple或多个元素的list。只有压缩KV那一处有virtual_engine选择，不把它推广到每一份cache。ratio4假定indexer/compressor对象具所需属性，这个wrapper没有自动为未配置模块补默认缓存。新模型先核实际capability、ratio、virtual engine和每一槽shape/dtype/storage所有者，再验backend。

## 包装注册与外部DSL是不同层

packaged_attention在import时定义Torch schema和Fake/impl，真实调用_get_dsl_ops才按名字import外部ops模块并cache。QLI/QSLI模块名加_dsl及_metadata_dsl后缀，mixed_quant_sparse_flash_mla不加；Python包能导入不证明这些外部模块、编译包和设备实现可用。metadata注册CompositeExplicitAutograd，compute注册PrivateUse1，不以metadata函数成功作为NPU compute支持证据。

| 接口 | compute返回与Fake形状 |
| --- | --- |
| QLI | 四项：I32 sparse indices[T,Nk,topk]；可选BF16 values同形否则[0]；候选块I32[T,Nk,candidate_topk_blocks]与length[T,Nk]，不开候选均[0] |
| QSLI | 候选block indices/length为必需输入，compute只返回indices与可选BF16 values；Nk从candidate_block_indices.shape[1]取 |
| Mixed Quant SparseMLA | BF16 attn_out沿q.shape；可选FP32 LSE，TND时[Nkv,T,Nq/Nkv]，其它layout分支另组shape；不开则[0] |

QLI Fake的Nk在TND从k.shape[1]取，PA_BBND从k.shape[2]取；QLI/QSLI Fake只接受Q TND、K TND/PA_BBND。它们没有在此完整验证dtype、head整除、topk合法域、block table容量或quant_mode的数值意义。metadata Fake均给1024个INT32而非实际执行计划内容，不能据其容量推所有真实metadata占用固定1024。

Mixed metadata Fake只按ori_topk_length.device分配；真实compute在wrapper中先分配BF16 output与LSE，再将out/lse传外部DSL。return_softmax_lse=True直接读取ori_kv.shape[2]，即使schema允许ori_kv=None且外部可走仅压缩KV路线，这个包装分支也未见相应保护；不能据optional类型推该组合可用。num_heads可整除以及不同layout的LSE语义仍须按真实callee核对。

QLI/QSLI的compute把全部可选length、residual、block_table、offset、metadata、layout、mask/compress/candidate参数逐项传外部函数；没有按Fake替调用者生成缺失metadata。新后端接入要保留空Tensor与None差别、四返回/两返回差别，以及预分配输出是否被真正写入；shape推导不证明payload、padding或概率结果。

先在固定外部ops/CANN/TorchNPU组合中核真实入口与输出ABI，再验证无压缩/ratio4、SWA与indexer多cache、GQA head比例、candidate关闭/开启、仅压缩KV、LSE和图中buffer寿命。性能拆分metadata构造、外部导入/编译、indexer与Attention执行，不把Fake成功或少一次包装分配当端到端收益；本次未运行这些验证。


## 3164 版本变化：移除旧 gather 参数

固定3164增量完整diff相对ceac：AscendDeepseekSparseAttention构造器、实例属性、dsa_forward真实与Fake签名均删除need_gather_q_kv。forward改为torch.ops.vllm.dsa_forward(hidden_states, output, prefix)；profiling和普通执行都直接调用impl.forward，不再分支传True。依赖旧位置参数或关键字的模型/补丁必须与wrapper和custom op注册一起迁移，不能只修改一处调用使Fake与真实schema不一致。

此改动不删除ACL图的边界：attention及o_proj/HCCL仍在dsa_forward内，metadata=None时仍委托内部impl完成profiling。cache元组和DSL接口按各自来源继续核对；不能把删除一个布尔参数理解为所有CP路径都不需要gather，相关通信已由新版backend/模型协议承担。本节只读变更和六行上下文，没有重读目标全文、执行图捕获或NPU。
