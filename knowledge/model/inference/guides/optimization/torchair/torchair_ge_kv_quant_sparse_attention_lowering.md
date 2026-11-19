---
type: Guide
title: GE发布快照稀疏量化注意力：Pioneer映射
description: 对照发布Pioneer的GE独立HiF8 Bitcast与Eager成对包装，补齐Q减RoPE输出分配及Meta/空Value边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention_pioneer.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvQuantSparseFlashAttentionPioneerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T10:00:16Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE发布快照稀疏量化注意力：Pioneer映射

## 版本与证据范围

依据TorchAir发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的kv_quant_sparse_flash_attention_pioneer.py完整85行源码。主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c无同一路径，这只记录固定tree差异，不表示主线没有其他注册、分解或后端能力，也不将发布实现静默并入主线软件栈。

本卡包含准确Converter到自定义IR映射及新增OpPlugin Eager/Meta静态对照，整卡产品矩阵未知，保持draft与空平台；未执行上游、GE编译、NPU精度或性能实验。未阅读完整kernel，不能从属性名称推导完整稀疏格式、反量化公式或产品支持。

## 准确入口与HIFLOAT8解释

准确注册torch.ops.npu._npu_kv_quant_sparse_flash_attention_pioneer.default。函数在torch_npu存在非None的hifloat8属性时，仅当key_dtype/value_dtype分别等于该值且对应输入非None，才分别Bitcast key/value为GE HIFLOAT8；query不经过这个转换。

这是Bitcast重解释，不是统一数值Cast；其他key_dtype/value_dtype取值没有在此函数转换成其他目标类型，也没有本地完整验证dtype枚举或打包布局。不能把有int注解解释成所有低比特取值都生效。

## 自定义IR的输入与属性

函数调用torchair.ge.custom_op('KvQuantSparseFlashAttentionPioneer',...)，输入名如下：query/key/value、sparse_indices、key_dequant_scale/value_dequant_scale、block_table、actual_seq_lengths_query/actual_seq_lengths_kv、key_sink/value_sink。可选输入原样传递，没有在本层替换为默认数值或证明所有None组合可运行。

| 属性类别 | 本层构造 |
| --- | --- |
| 缩放与量化 | scale_value用attr.Float；key_quant_mode/value_quant_mode用attr.Int，二者为必需形参，没有本地完整枚举校验。 |
| 稀疏与布局 | sparse_block_size默认1、sparse_mode默认3，均attr.Int；layout_query/layout_kv默认BSND，均attr.Str。 |
| 窗口与注意力模式 | pre_tokens/next_tokens默认9223372036854775807，attention_mode默认0，均attr.Int。默认大窗口不等于已证明任意边界或动态窗口支持。 |
| 量化仓库与分块 | quant_scale_repo_mode默认1、tile_size默认128、rope_head_dim默认64，均attr.Int。不能仅凭这些值生成通用最优调参规则。 |

size、head、稀疏索引编码、block_table与有效长度之间的关系没有在此函数完整校验，sink含义也不能只按命名补造。本映射未按meta_outputs统一Cast输入或输出。

## 发布OpPlugin的输出与HiF8解释分支

本节另审阅OpPlugin发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的KvQuantSparseFlashAttentionPioneer包装、Schema及Meta。对应C++在主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`同路径不存在，仅说明精确tree差异，不作主线能力否定。发布来源组合是ascend_26_0_pt28，但没有整接口产品表和运行记录，仍保持draft与空平台。

### 输出D来自Query减RoPE段，不从Value直接复制

Eager显式要求query、key、sparse_indices非空。构造输出时只允许layout_query精确"BSND"或"TND"，前者要求Q四维、后者三维，并逐轴要求Q尺寸>0、尾维>rope_head_dim。结果分别为[B,Sq,Nq,QD-rope_head_dim]或[Tq,Nq,QD-rope_head_dim]，dtype和options来自query。

因此本入口的rope_head_dim会影响分配的输出尾长，不是只供后端忽略的属性；也不能像普通FIA那样直接从value尾维推导Dv。构造函数接收的rope_head_dim是uint64_t引用，而Schema为int，调用方应先核对非负且小于QD，不能依赖负数的隐式转换得到有意义的分配。

layout_kv在本构造函数虽作为参数接收，却没有被用于分配或校验，只在最后作为字符串传给ACLNN。Key/Value缓存shape、物理分页布局、各量化mode和scale对应关系仍需后端合同；没有本地检查不意味着任意KV布局可用。

### Eager用Key提示决定是否包装两份KV

Eager仅当key_dtype存在且映射为ACL_HIFLOAT8时，才同时创建key_wrapper和value_wrapper；此时各自应用key_dtype/value_dtype。否则两份KV都以原Tensor直接传入，**value_dtype单独指定HiF8不会在这一C++分支形成value wrapper**。本层没有两个独立的提示开关。

前面的GE Converter却分别检查key_dtype和value_dtype，独立对匹配的输入Bitcast。若只给value_dtype或两侧提示不对称，不能假定Eager和GE按同样逻辑解释KV；应明确固定双方载体、逻辑dtype及成对提示，再验两条后端结果。make_wrapper和Bitcast都不进行数值量化、尺度校准或字节重排。

两个Eager分支都调用aclnnKvQuantSparseFlashAttentionPioneer，使用EXEC_NPU_NO_FORMAT_CHECK_CMD，没有本函数的符号探测回退。参数和符号存在不是设备支持、shape或精度认证，更不能用单一成功输入外推所有quant_scale_repo_mode/tile_size组合。

### Meta比Eager多检查Value，少部分Q边界

发布Meta要求query、key、value及sparse_indices都非None且非空；C++前置检查没有同样的value.numel()>0。Meta同样限定BSND/TND的Q rank，并按QD-rope_head_dim分配meta输出，但没有C++逐轴>0、尾维严格大于RoPE的完整显式检查。零尾长或异常rope值应先统一验合法性，不能由一个后端能推导shape判断另一条路径也接受。

本节没有执行上游、图或设备实验。接入时保持准确下划线入口与单返回，先验证Q包含RoPE段的尾轴、KV物理表示、Key/Value提示及scale关系，再核对稀疏索引、分页有效区和窗口；对成对HiF8提示、单侧提示和空Value分别比较Eager/Meta/GE的真实行为，最后测完整KV量化、稀疏读取及注意力收益。任何静态分配/包装分支都不替代这些验收。

## 输出与优化核对

自定义调用只列outputs=['attention_out']，不返回本层另行构造的LSE或cache元组；输出名称与数量不认证动态shape、精度、别名或底层实现已可用。

优化前应在匹配发布软件栈核对准确FX重载、真实IR注册及kernel、输入量化格式和Bitcast、稀疏索引/窗口/分块属性、有效长度及返回shape/dtype，再测精度与性能。本文没有执行这些实验。

- [RoPE与KV缓存融合的独立合同](torchair_ge_rope_cache_lowering.md)
- [自定义算子Meta、函数化与后端交付](../../integration/torchair/custom_operator_graph_contract.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention_pioneer.py)（primary）

## 补充实现证据

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvQuantSparseFlashAttentionPioneerKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention_pioneer.py)（primary）
