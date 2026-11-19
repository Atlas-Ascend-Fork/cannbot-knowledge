---
type: API
title: 按轴索引散点更新：保留原数据（torch_npu.scatter_update）
description: torch_npu.scatter_update：按轴索引散点更新：保留原数据。将tensor updates中的值按指定的轴axis和索引indices更新tensor data中的值，并将结果保存到输出tensor，data本身的数据不变。 区分按轴更新与ScatterND索引深度，记录公开shape限制、原地别名及GE复制和版本差异。
tags:
- task.lookup
- topic.compilation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-scatter_update.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-scatter_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScatterUpdateKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterUpdateKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/scatter_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/scatter_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-scatter_update_.md
  role: constraint
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.scatter_update
---


# scatter_update与原地变体：轴更新、复制和索引范围

## 固定版本与接口

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文，以及各自包装、Meta、schema；TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013与独立主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c分别审阅，不把两个main当已配套发行。

```text
torch_npu.scatter_update(data, indices, updates, axis) -> Tensor
torch_npu.scatter_update_(data, indices, updates, axis) -> Tensor
```

按axis和indices把updates数据段覆盖到data；不是重复位置相加，也不是ScatterND的多坐标尾维协议。无下划线的C++两版先clone，原地版返回同一self；ACL Scatter和ACLNN InplaceScatterUpdate都固定update方式。GE功能版同样TensorMove再Scatter，直接原地版有dont_prune_me副作用标记；旧警告注释不覆盖实际复制。

## 参数与版本边界

data/updates为ND、rank2..8、非空、允许非连续，二者rank一致；“维度一致”不等于每根轴长度相等，来源示例会缩小更新轴。indices为INT32/INT64、一维或二维且非空。主线进一步约束二维indices第二轴必须2，updates首轴等于indices首轴且≤data首轴，除首轴和axis轴外其余长度相同。

axis必填，主线公开范围(-rank,rank)且不能0，不能借直接GE Converter的旧默认axis=0省略它。主线中文还明确只允许非负索引，框架不检查越界；重复目标位置结果不保证。约束段提到0维indices却与参数段仅一/二维矛盾，本卡不扩出0维支持。

发布A2及A3训练列INT8/INT32、FP16/BF16/FP32；旧Atlas训练不含BF16。主线新增950PR及950DT，并额外列UINT8；A3总览写系列但具体dtype段仍写训练，不自行扩大其推理细表。BOOL、INT64数据值和FP8并不因相邻ScatterND支持而自动加入本接口。

主线约束总体列单算子和图模式，功能版图示例又注明仅950PR/DT，原地示例未作同样限定；这些文字分别保留，不把示例一概提升为完整后端/产品矩阵。两个固定Converter存在也不等于每个产品图组合已运行。

## 使用与核验

按实际目标数据段检查不重叠、合法边界、未更新区域和原data是否保持；共享view及图复用还需检查原地写回。功能版要计入整Tensor复制成本。本文没有运行上游、设备、图编译或性能实验。

- [ScatterND功能版](npu_scatter_nd_update.md)
- [ScatterND原地版](npu_scatter_nd_update_.md)
- [量化后写回](npu_quant_scatter.md)
- [模型中按阶段选择KV写入方式](../../optimizations/rules/paged_kv_cache_write_scatter_update_vs_scatter_nd.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### 按轴索引散点更新：保留原数据：torch_npu.scatter_update

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将tensor updates中的值按指定的轴axis和索引indices更新tensor data中的值，并将结果保存到输出tensor，data本身的数据不变。

### 文档签名

```text
torch_npu.scatter_update(data, indices, updates, axis) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-scatter_update.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-scatter_update.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterUpdateKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterUpdateKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScatterUpdateKernelNpu.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterUpdateKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/scatter_update.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/scatter_update.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update_.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-scatter_update_.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-scatter_update_.md)（constraint）
