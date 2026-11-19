---
type: Guide
title: 原生EmbeddingBag：辅助缓冲与CPU反向搬运
description: 核对EmbeddingBag四输出的SoC分支、ACL空输入与索引转换，以及per-sample weights反向的整表CPU复制请求。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingBagNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingBagNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingBagKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingBagKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingBagPerSampleWeightsBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingBagPerSampleWeightsBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingBagPerSampleWeightsBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingBagPerSampleWeightsBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T14:15:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生EmbeddingBag：辅助缓冲与CPU反向搬运

## 固定范围与四输出

核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的ACL/OpAPI EmbeddingBag前向及per-sample weights反向。四对所选C++去注释、空白并拼接续行后token分别相同；不据此推定整个runtime或底层kernel相同。平台配套未知，保持draft、空平台；没有执行上游或设备实验。

[公开Embedding限制](torch_npu_native_embedding_linear_constraints.md)和[GE EmbeddingBag转换](../../inference/guides/optimization/torchair/torchair_ge_embedding_bag_lowering.md)已有文档和构图边界。本卡关注Eager的`(output, offset2bag, bag_size, max_indices)`实际准备以及准确的`_embedding_bag_per_sample_weights_backward`，不把它扩大成所有Embedding反向。

Schema中`_embedding_bag`与`_embedding_bag_forward_only`均有四输出、mode默认0、sparse默认False，且声明ACL和OpAPI候选。两种前向在所查各自后端重复同样的缓冲逻辑，`forward_only`名字不表示本层不申请后三项。OpAPI先经兼容宏检查aclnnEmbeddingBag及GetWorkspaceSize的缓存地址；缺符号且ACLNN-only时报错，否则返回相应ACL表达式。这是调用路由，不是设备能力证明。

## OpAPI辅助输出依赖准确SoC比较

令`O=offsets.size(0)`，`B=O-(include_last_offset?1:0)`，`D=weight.size(1)`。OpAPI局部检查三输入rank>0和weight为2D，输出申请(B,D)；并未在此完整检查indices/offsets为一维、offset单调/范围或任意输入设备一致性。下表的一维长度描述以一维offsets为条件，不把较高rank未拒绝当成已支持。

| 槽位 | 局部申请分支 |
| --- | --- |
| output | 按weight参照申请(B,D)。 |
| offset2bag | 先按indices参照申请`indices.size(0)`元素；mode=0、padding_idx<0且SoC<=Ascend950时，随后替换为长度0。 |
| bag_size | SoC>=Ascend950按offsets原形状；更早枚举在include_last_offset=True时申请O-1，否则按offsets原形状。 |
| max_indices | mode为0或1且SoC>=Ascend950时申请长度0；更早枚举按offsets原形状或O-1。mode不为0/1则按offsets参照申请(B,D)。 |

以上`>=`和`<=`在Ascend950枚举值处同时命中各自条件，不能笼统写成“新芯片都空辅助输出”。mode的else分支没有在此先校验合法枚举，不能认证所有其他mode都可用。SoC枚举比较也不等于已核对产品支持矩阵。

准备后三项后，只要原indices或offsets任一为Long，就将三项都`.to(Long)`；否则只要任一为Int，就都`.to(Int)`。Long优先，也没有在这里把原始indices/offsets统一转INT32。dtype变化时可能涉及新缓冲；同dtype的`.to`不意味着每次复制。offset2bag的零长替换发生在这些转换之后、ACLNN调用之前，不能只看最终空槽就推定此前没有准备工作。

## ACL前向还有不同的转换与空输入路线

ACL先把Long indices和Long offsets分别`_npu_dtype_cast`为INT32，没有在本层先验证其值域可无损收窄。辅助缓冲依据转换后的索引/offsets准备；通常在OpCommand之后，只要任一原输入是Long，就把三辅助结果恢复Long。

ACL形状helper在一维indices时用(B,D)，其他rank用`(indices.size(0),D)`；OpAPI始终按offsets计B。该局部分歧不能作为任意rank输入在两个后端都合法的证据。ACL mode映射为0→sum、1→mean、其余→max；合法mode和非法枚举不能混为同一合同。

在前置检查和分配已成功、进入helper且indices或offsets的numel为0时，ACL要求mode=0，再把output重新绑定为`apply_tensor(weight)`并fill_(0)，三项辅助输出改为空后立即返回。这里按weight原形状申请，不能用通常(B,D)估算这条分支；早退还绕过后面的Long恢复。不能据此声称每种空输入都必然到达该分支，前置O-1等准备仍可能限制可达性。

非空ACL路线调用EmbeddingBag OpCommand；sum且padding_idx==-1时在调用后将offset2bag替换为空。这个条件不同于OpAPI的padding_idx<0与SoC<=950，替换时机也不同。实际分配峰值、格式整理与代价需要量测，不能从最终返回尺寸认证两路内存行为等价。

## per-sample weights反向在两路都显式走CPU

`_embedding_bag_per_sample_weights_backward`的ACL和OpAPI实现都依次对grad、**整个传入weight Tensor**、indices、offsets、offset2bag调用`.to("cpu")`，在这些CPU对象上调用ATen同名反向，再无条件调用`at::native::sparse_to_dense(result)`，最后将结果`.to(indices.device())`。此处没有ACLNN调用，也没有一个以是否缺ACLNN符号为条件的回退分支。

这是per-sample weights的梯度入口，不能称为普通Embedding整表权重梯度或所有EmbeddingBag反向的统一路线。`sparse_to_dense`调用存在也不等于ATen结果每次本来都是稀疏Tensor。对于NPU上的大词表，整份weight的CPU转换请求是重要的内存/传输审阅点；已经在CPU的输入可能无需搬运。本卡未执行CPU dispatcher或量测同步、吞吐、Host峰值，也没有认证所有dtype/模式的CPU算子可用性。

## 模型优化验收入口

先确认是否真的请求per-sample weights梯度，再保存词表大小、weight dtype、indices/offsets形状与宽度、include_last_offset、mode、padding_idx及准确SoC/后端。分别核四输出的shape/dtype和空输入路径，不能只比较output。普通Embedding稠密梯度另见[整表分配指南](torch_npu_embedding_dense_gradient_allocation.md)；sparse参数透传不替代上层自动求导稀疏分派证据。

确认数值、可达性与梯度种类后，再比较辅助分配、输入收窄/输出恢复和显式CPU路径的代价。不能通过删掉辅助输出、改变mode/padding或绕过CPU调用来假定得到等价加速。本卡仅静态审阅，无性能数字、运行复现或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingBagNpuOpApi.cpp)（primary）：20–223。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingBagNpuOpApi.cpp)（implementation）：20–169。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingBagKernelNpu.cpp)（implementation）：19–260。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingBagKernelNpu.cpp)（implementation）：19–210。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingBagPerSampleWeightsBackwardKernelNpuOpApi.cpp)（implementation）：15–35。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingBagPerSampleWeightsBackwardKernelNpuOpApi.cpp)（implementation）：15–32。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingBagPerSampleWeightsBackwardKernelNpu.cpp)（implementation）：18–38。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingBagPerSampleWeightsBackwardKernelNpu.cpp)（implementation）：18–35。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：180–190。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：180–190。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110。
