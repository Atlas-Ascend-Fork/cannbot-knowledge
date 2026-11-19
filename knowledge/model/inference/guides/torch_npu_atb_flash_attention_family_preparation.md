---
type: Guide
title: ATB FlashAttention族：掩码、长度与内核模式
description: 聚合普通、V2、V3与unpad入口，连接固定SelfAttention参数、掩码装填、格式准备和Operation缓存，保留文档及版本差异。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtbV2.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionAtbV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtbV3.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionUnpadAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionUnpadAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionUnpadAtbV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
created_at: '2026-11-11T03:31:17Z'
updated_at: '2026-11-11T03:31:17Z'
platforms: []
---

# ATB FlashAttention族：掩码、长度与内核模式

## 固定入口与参数类型

本卡对照OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的`atb::_npu_flash_attention`、`atb::_npu_flash_attention_v2.out`与`atb::_npu_flash_attention_unpad`。主线另有`atb::_npu_flash_attention_v3`和`atb::_npu_flash_attention_unpad_v2`。这些准确名称通过TORCH_LIBRARY_FRAGMENT(atb)及PrivateUse1注册，使用SelfAttentionParam与SelfAttentionOperation。

整卡平台和执行库配套未知，保持draft与空平台。固定仓内参数头文件与FA V2 docstring的局部产品条件按下文保留。输入整理、13种bridge类型转换、Setup和工作区等公共阶段见[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。本次仅静态审阅，未执行上游或设备。

## 五条入口的实际准备

| 入口 | kernel/mask与长度 | VariantPack输入和格式请求 | 返回 |
| --- | --- | --- | --- |
| 旧flash_attention | kernel默认0，mask=NORM(1)，isTriuMask=0；seq_len为Tensor | Q/K/V、mask、seq_len，Q/K/V和长度显式format_trans=True，mask默认False | caller out，Schema返回() |
| flash_attention_v2.out | kernel_type、mask_type先转枚举；seq_len为SymInt[]并以asIntArrayRefUnchecked后at::tensor(...,kInt)构造 | 所有Input使用默认False；按下文mask分支形成5或6个槽 | 返回同一out引用 |
| 主线flash_attention_v3 | kernel默认0，mask_type缺值取NORM_COMPRESS；只接受该枚举3，isTriuMask=1 | 与旧普通入口相同的五槽及格式标志 | caller out，Schema返回() |
| 旧flash_attention_unpad | kernel默认0，mask=UNDEFINED(0)，isTriuMask=0；长度为Tensor | Q/K/V、seq_len四槽均显式format_trans=True | caller out，Schema返回() |
| 主线flash_attention_unpad_v2 | kernel_type缺值取0，局部只接受DEFAULT(0)或EXP_M8V2(2)；mask=0、isTriuMask=0 | 与旧unpad相同四槽和格式标志 | caller out，Schema返回() |

五条入口都以query建立OptionalDeviceGuard，Q/K/V和out由调用方提供。Output直接转换描述符；准备阶段的格式转换和可能的缓冲成本与Attention计算分别核对。V2仅指定INT32构造dtype的长度materialize没有另设query.device，也未在该处补完整符号和值域检查。None可选输入与undefined Tensor都保持空描述槽，已定义对象才进入常规Input准备。

## dense V2按掩码决定槽位

V2对ALIBI(2)、ALIBI_COMPRESS(4)、ALIBI_COMPRESS_SQRT(5)、ALIBI_COMPRESS_LEFT_ALIGN(6)设isTriuMask=1，对NORM(1)设0。其它值沿参数结构默认isTriuMask=0。

压缩ALIBI三项4/5/6将Q/K/V、mask、seq_len_tensor、slopes依次装为六槽；普通ALIBI(2)和NORM(1)仅装前五槽。其它mask值在这个函数的两条装填分支都没有命中，之后仍取得Operation并走RunAtbCmd。特别是docstring列出的UNDEFINED=0基础场景，在本地消费者没有对应装填分支，需要按准确安装入口和配套ATB核验。

V3的压缩倒三角mask不是将V2的所有枚举开放一遍，其局部TORCH_CHECK只接受NORM_COMPRESS。PagedAttentionParam的同名NORM_COMPRESS为主线值5，SelfAttentionParam为3，两种类型的编号应按准确参数结构读取。

## 固定字段与头文件声明

本族五个包装器均令headNum=num_heads、kvHeadNum=num_kv_heads、qkScale=scale_value，并固定下列字段，kernelType、maskType和isTriuMask按前表分别设置。

| 字段 | 局部固定值 |
| --- | --- |
| calcType | PA_ENCODER(3) |
| kvcacheCfg / scaleType | K_CACHE_V_CACHE(0) / SCALE_TYPE_TOR(0) |
| clampType / clampMin / clampMax | CLAMP_TYPE_UNDEFINED / 0 / 0 |
| quantType / outDataType | TYPE_QUANT_UNDEFINED(0) / ACL_DT_UNDEFINED |
| qScale / batchRunStatusEnable | 1 / False |
| inputLayout / mlaVHeadSize | TYPE_BSND(0) / 0 |
| cacheType / windowSize | CACHE_TYPE_NORM(0) / 0 |

头文件的head/kvHead为int32_t、qkScale为float，包装入口用int64/double，需核对转换后的属性。kvHeadNum=0时，头文件规定K/V头数量沿Q头数；非零时采用kvHeadNum。qScale在PA_ENCODER下按docstring不生效，本族仍保留固定赋值。

SelfAttentionParam的CalcType声明UNDEFINED/ENCODER/DECODER/PA_ENCODER/PREFIX_ENCODER为0..4。KernelType默认0的注释以FP16输入/BMM/输出解释，高精度1以FP16输入、FP32 BMM、FP16输出解释；主线新增EXP_M8V2=2，注释为FP16、exp:m8v2、softmax:default，发布声明只有前两项。dense V2仅做kernel enum cast，unpad V2则明确限制0/2，不能从类型声明替每条包装器补同一局部检查。

MaskType两版均声明0..8，依次为UNDEFINED、NORM、ALIBI、NORM_COMPRESS、ALIBI_COMPRESS、ALIBI_COMPRESS_SQRT、ALIBI_COMPRESS_LEFT_ALIGN、SLIDING_WINDOW_NORM、SLIDING_WINDOW_COMPRESS。头文件对LEFT_ALIGN注释仅支持A2推理产品；V2 docstring另给出A2/A3条件，两份范围一起保留并按配套核验。

头文件的QuantType将UNDEFINED和UNQUANT均设0，将DEQUANT_FUSION=1标为预留且当前不可取，OFFLINE/ONLINE=2/3注明仅A2推理产品。其量化段要求PA_ENCODER、INT8 Q/K/V、K/V headsize等长且在(0,256]并32对齐，输出仅FP16/BF16、布局仅BSND；本族固定未量化0。SCALE_TYPE_LOGN还要求quantType=0。

clampType声明可选MIN_MAX，需指定上下界；本族固定关闭。头文件说明SWA通过windowSize>0与SLIDING_WINDOW的mask开启，使用CACHE_TYPE_SWA可限制Cache长度减少显存，本族固定windowSize=0和NORM Cache。mlaVHeadSize声明范围[0,576]，大于0对应合并KV时V head_size，本族固定0。

头文件的KvCacheCfg段标注不支持calcType为PA_ENCODER，而本族固定PA_ENCODER和默认K_CACHE_V_CACHE。该字段的实际生效范围应按具体ATB消费者解释，包装层没有在这里因默认组合而拒绝，也不据字段名字认证Cache写回行为。

## Operation缓存使用八项SelfAttention属性

SelfAttentionParam使用对应模板实例的thread_local OpParamCache。捕获状态非零时CreateOperation；普通路径计算hash并在op_map查找或保存。HashOpParam<SelfAttentionParam>只序列化kvHeadNum、headNum、qkScale、calcType、kernelType、maskType、quantType、isTriuMask这八项，computeHash先重置缓冲偏移再调用该特化。

Q/K/V内容、seq_len和slopes由本次VariantPack交给执行准备。参数缓存命中后仍按公共路径做Setup和工作区处理。完整hash函数、外部ATB状态及跨线程/跨设备生命周期继续按各自证据核验。

## FA V2文档的输入与产品条件

两版所选docstring相同。它列Q/K/V与out为FP16/BF16，通常形状为[num_tokens,num_heads,head_size]；A2/A3的PA_ENCODER段也列二维输入，Q/K/V的维数应相同。num_heads需大于0；GQA要求head_num>kv_head_num且整除。输出的实际KV head维和head_size_v按文档具体场景核对。

普通mask列[max_seq_len,max_seq_len]、[batch,max_seq_len,max_seq_len]，ALIBI列[batch,head_num,max_seq_len,max_seq_len]。压缩ALIBI仅在PA_ENCODER/PREFIX_ENCODER说明生效，headSize≤128；A2/A3的压缩mask列[head_num,seq_len,128]或[256,256]，压缩倒三角为[128,128]，LEFT_ALIGN为[256,256]。该产品段的FP16压缩ALIBI要求高精度。slopes被说明为Device Tensor、ND、shape=[batch]，采用时按实际ATB接口核对该局部描述。

另一个“Atlas推理系列产品”段列batch在(0,2000]、mask用真实max_seq_len、q_seqLen=kv_seqLen；相应NZ/分块mask布局和nTokens对齐条件单独适用。头大小一般段与特定产品段分别列(0,576]及head/v_head相等、(0,256]且16对齐等条件。A2/A3的nTokens按各batch长度求和；该另列产品的PA_ENCODER则在总和后对齐16，其余条件按单batch先对齐再求和。docstring还建议headSize取64倍数以改善性能，这是一项来源建议，本次没有测得收益。

这些通用说明包含ENCODER/DECODER、KV-bypass和其它参数场景，本卡包装器固定PA_ENCODER与前表属性。采用时按当前入口筛选适用条件，保留文档、头文件与本地分支的差异。docstring中的示例也未在本次运行。

## 版本与验收

旧普通、dense V2和旧unpad的两版完整CPP token分别一致，主线V3与unpad V2的准确源码路径在发布快照缺失。固定头文件的SelfAttention结构差异仅上述新增EXP_M8V2，PagedAttention结构另新增MASK_FREE/NORM_COMPRESS，其余所选声明/注释对照已记录。均不把局部差异扩大成全部外部安装包能力。

按准确atb target、kernel/mask、seq_len表示、格式标志、输出别名和实际参数检查生成图与执行，分别量化长度构造、输入准备、Operation创建、Setup、工作区和Attention耗时。数值、捕获、设备支持和性能仍需实际验收，本次没有新增verified或设备结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtbV2.cpp)（primary）：1–108。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionAtbV2.cpp)（implementation）：1–108。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtb.cpp)（implementation）：1–75。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionAtb.cpp)（implementation）：1–73。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionAtbV3.cpp)（implementation）：1–83。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionUnpadAtb.cpp)（implementation）：1–72。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionUnpadAtb.cpp)（implementation）：1–72。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionUnpadAtbV2.cpp)（implementation）：1–76。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（implementation）：36–44、348–373、522–668。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（implementation）：39–47、349–372、522–667。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（implementation）：314–402。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（implementation）：314–402。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：112–127、142–148。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：116–133、149–156。
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：26–114。
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：26–124。
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：559–568。
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：508–517。
