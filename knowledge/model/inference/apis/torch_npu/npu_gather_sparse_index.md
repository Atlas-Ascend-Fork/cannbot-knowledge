---
type: API
title: 稀疏索引取数（torch_npu.npu_gather_sparse_index）
description: torch_npu.npu_gather_sparse_index：按 index 从二维输入的第0维取数，输出保留索引外形及被选行的尾维。 说明高维index拼接输出shape、负索引禁用及输入大小和零值连续分布的性能前提。
tags:
- task.lookup
- topic.compute.indexing
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gather_sparse_index.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_gather_sparse_index.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gather_sparse_index.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
created_at: '2026-11-10T03:38:42Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_gather_sparse_index
---


# npu_gather_sparse_index：首轴索引与数据聚合条件

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口与形状

```text
npu_gather_sparse_index(input, index) -> Tensor
```

按首轴取input[index]，输出shape为index.shape+input.shape[1:]，dtype随input。例如input=(16,32)、index=(2,3)，输出(2,3,32)。名称中的sparse不表示输入必须是稀疏存储Tensor，也不是删除所有零值的压缩操作。

input支持FP16/BF16/FP32/FP64、INT8/16/32/64、UINT8、BOOL、COMPLEX64/128。index为INT32/64、rank≤7，只允许[0,input.shape[0]-1]，不支持负索引。index.rank+input.rank-1≤8；Meta对标量有形状分支，不据此扩展含首轴索引的参数契约。

## 性能选择

来源建议input占用字节数>150*1024、index元素数>960，且零值和非零值分别集中在连续区域。可把input!=0展平，统计相邻布尔值变化次数/(元素数-1)，比例越小表示聚合越强；此指标是选择输入场景的线索，不是固定收益门槛。

小Tensor或零值频繁交错可能无收益，需要与相同首轴gather结果对照。产品表确认A2/A3训练系列和950DT；本卡的平台标签不进一步证明PR或各产品所有子型号支持。


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 两版公开范围与生成路径

发布中文页限定input为二维，主线双语去掉该短语；两版共享输出形状函数有一般rank和标量分支，但不能仅据分配函数放宽发布公开二维约束。主线950只列DT，未列PR；发布只列A2/A3训练系列。

两版Schema生成路径均调用aclnnGatherV3，固定dim=0、batch_dims=0、mode=1；不是任意axis的gather。Meta与形状函数推导index.shape+input尾轴并限制总rank，却不检查每个索引的值或证明所有产品支持全部dtype/rank。

## 反向聚合与测试覆盖

两版自动求导声明将input.sym_sizes传给npu_gather_sparse_index_backward；实现先新建原input形状的全零梯度，再按首轴index_add累加重复索引。普通index分支在新建缓冲上调用私有原地helper，Tensor子类index分支用私有函数式helper；不表示修改原始input。此次没有沿私有helper扩大所有rank或dtype支持结论。

两版测试的前向input均二维，index维数只到6，并非公开上限7的完整覆盖；Embedding对照本身也使用NPU权重，不是独立CPU参考。部分dtype生成用randn包含整数/BOOL，不能把列出的dtype循环当成有效设备覆盖。反向仅有一维index及浮点类型案例。

性能阈值、零/非零连续聚合来自文档建议。测试的形状生成不保证严格超过所有阈值，也没有计时；公开小例子只展示结果，不据此宣称收益。主线的相邻零值标识变化比例分母为元素数减1，比例低并非任意稀疏度都会加速的保证。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 稀疏索引取数：torch_npu.npu_gather_sparse_index

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

按 index 从二维输入的第0维取数，输出保留索引外形及被选行的尾维。

### 文档签名

```text
torch_npu.npu_gather_sparse_index(input, index) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

该版 input 为二维；index 使用 int32/int64 且不支持负值。输出维数为 `index.dim + input.dim - 1`，索引范围按 input 第0维核对。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gather_sparse_index.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gather_sparse_index.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_gather_sparse_index.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gather_sparse_index.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
