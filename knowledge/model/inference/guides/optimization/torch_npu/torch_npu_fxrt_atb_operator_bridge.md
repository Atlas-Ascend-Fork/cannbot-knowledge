---
type: Guide
title: FXRT ATB算子桥接：变体包、操作缓存与310 SoC分派
description: 记录FXRT经atb::infer接口桥接Ascend Transformer Boost算子的机制：仅连续Tensor的atb::Tensor转换、按流复用的ATB
  Context、FIFO容量控制的操作与workspace缓存、paged_attention/reshape_and_cache参数映射，以及Ascend310系列linear的ATB动态加载分派。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_adapter.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_base.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_base.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_add.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_add.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_linear.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_linear.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_paged_attention.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_paged_attention.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_reshape_and_cache.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_reshape_and_cache.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_operator_factory.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_operator_factory.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/composite/unify_linear.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/composite/unify_linear.h
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT ATB算子桥接：变体包、操作缓存与310 SoC分派

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT ATB（Ascend Transformer Boost）算子桥接层与unify_linear分派。静态阅读，未链接atb库或运行；ATB自身kernel能力、产品矩阵与数值边界不在本卡，整卡draft、platforms为空。

## atb::Tensor转换的硬边界

`GetAtbTensor`把FXRT IR Tensor转成atb::Tensor：dtype按静态映射表转aclDataType（QInt8/QUInt4x2映射到ACL_DT_UNDEFINED，遇未知类型异常）；format按MemoryFormat映射aclFormat，但**基础布局统一归一为ACL_FORMAT_ND**，避免ATB kernel依赖具体4D/5D枚举；dataSize按Numel×itemsize计算；CPU张量填hostData、NPU填deviceData。**非连续Tensor直接异常**——“ATB现在只支持连续Tensor”是桥接层的硬边界，非连续输入必须先物化。`ParamSetter`按声明的输入/输出下标构建variant pack；`Update`只刷新地址（重放时复用pack结构），输出按单Tensor或Tuple展开。

## 每流一个ATB Context

`AtbContextManager`按aclrtStream缓存`atb::Context`：首次为该流CreateContext并SetExecuteStream，进程退出时统一Destroy。同一stream复用同一context；**不同stream各自建context**，没有跨流共享或池化。Setup/Execute都经`GetAtbContext(stream)`取当前流的context。

## 操作与workspace的FIFO缓存

`AtbBase::GetOrCreateEntry`以`AtbHash(inputs, output, op_name)`为键缓存已创建的`atb::Operation`与workspace大小：hash变化才重建param_setter的variant pack；`CreateOperation`按param（如LinearParam/PagedAttentionParam）建op。容量来自`GetAtbCacheCapacity()`，超容量按FIFO淘汰并DestroyOperation；**FIFO队列与map不一致时跳过陈旧hash，map与队列同时异常时兜底清空全部缓存防无限增长**。workspace大小在首次`op->Setup(variant_pack, ws, context)`后缓存（`workspace_cached`），后续同hash直接返回；Setup取`CollectiveManager::local_rank_id()`对应的Ascend DeviceContext当前stream。Execute把variant pack按值传入`op_->Execute`。因此ATB路径的重放成本模型是：命中时仅做地址Update+Execute，miss时重建param与Operation；与aclnn执行器缓存（键只含元数据）不同，这里的hash由inputs/output/op名共同决定，具体构成以AtbHash实现为准。

## 各算子的参数映射

`atb_linear`：LinearParam固定transposeA=false、transposeB=true（权重按已转置传入）、enAccum=false，hasBias由第三个输入是否为None决定；variant pack按有/无bias选择3或2输入。`atb_paged_attention`：按10输入合同（query/key_cache/value_cache/num_kv_heads/num_heads/scale_value/block_table/context_lens/out/workspace）填充PagedAttentionParam——headNum/kvHeadNum来自标量、qkScale取scale_value、maskType=UNDEFINED、batchRunStatusEnable=false、quantType/compressType/calcType未定义、scaleType=TOR、**inputLayout固定TYPE_BSND**、mlaVHeadSize=0；真实输出经inputs[kOutIdx]传入（与PagedAttentionAtb.cpp签名一致），variant pack只绑query/key/value/block_table/context_lens五输入。`atb_reshape_and_cache`：按key/value cache的format是否都为FRACTAL_NZ选择K_CACHE_V_CACHE_NZ或K_CACHE_V_CACHE，**输出就是key_cache/value_cache本身**（原地更新KV cache），slot_indices为第5输入。`atb_add`：ElewiseParam ELEWISE_ADD，两输入直传。

## unify_linear：Ascend310走ATB，其余走aclnn

`UnifyLinear`构造时读`GetAscendSocVersion()`：SocName以Ascend310/ASCEND310开头则`use_atb_linear_=true`，尝试dlopen `libops_ascend_atb.so`并经`CreateAtbLinear`符号（extern "C"工厂，见atb_operator_factory.cpp）创建ATB linear；**加载或符号失败静默回退AclnnLinear**（只打日志）。非310系列直接AclnnLinear。CalcWorkspace/Launch纯转发内部算子。因此“linear在FXRT里用什么实现”是SoC相关的：310上默认尝试ATB、失败回退；其他SoC固定aclnn复合路径（见[量化/MoE/融合特例算子](torch_npu_fxrt_quant_moe_fused_specialized_ops.md)）。不能从x86仿真或910B的行为推导310行为，反之亦然。

## 边界与验证方式

本卡未运行任何ATB路径：BSND布局适配、NZ KV cache分支、310分派都应按实际SoC与atb库版本复核（日志确认走ATB还是回退）。paged_attention的mask/量化/压缩参数当前固定为未定义，新增能力不会自动出现。验证时分别用连续/非连续输入（非连续应报错）、不同stream（各自context）、多次同hash调用（workspace缓存命中）与hash变化输入（pack重建）对照首末次耗时与数值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_adapter.cpp)（primary）：全文件219行。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_base.cpp)（implementation）：全文件98行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_base.h)（implementation）：定向范围1–86。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_paged_attention.cpp)（implementation）：全文件109行。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_reshape_and_cache.cpp)（implementation）：全文件83行。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_linear.cpp)（implementation）：全文件48行。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/composite/unify_linear.cpp)（implementation）：全文件74行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/atb/atb_operator_factory.cpp)（implementation）：全文件9行。
