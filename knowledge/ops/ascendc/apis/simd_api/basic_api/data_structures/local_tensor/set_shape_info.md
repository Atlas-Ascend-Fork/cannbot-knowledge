---
type: API
title: SetShapeInfo
description: 设置LocalTensor的Shape信息。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetShapeInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_tensor.h
---

# SetShapeInfo<a name="ZH-CN_TOPIC_0000002330767566"></a>

## 功能说明<a name="section618mcpsimp"></a>

设置LocalTensor的Shape信息。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetShapeInfo(const ShapeInfo& shapeInfo)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

<a name="zh-cn_topic_0235751031_table33761356"></a>
<table><thead align="left"><tr id="zh-cn_topic_0235751031_row27598891"><th class="cellrowborder" valign="top" width="13.94%" id="mcps1.2.4.1.1"><p id="zh-cn_topic_0235751031_p20917673"><a name="zh-cn_topic_0235751031_p20917673"></a><a name="zh-cn_topic_0235751031_p20917673"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.98%" id="mcps1.2.4.1.2"><p id="zh-cn_topic_0235751031_p16609919"><a name="zh-cn_topic_0235751031_p16609919"></a><a name="zh-cn_topic_0235751031_p16609919"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="73.08%" id="mcps1.2.4.1.3"><p id="zh-cn_topic_0235751031_p59995477"><a name="zh-cn_topic_0235751031_p59995477"></a><a name="zh-cn_topic_0235751031_p59995477"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p284425844311"><a name="p284425844311"></a><a name="p284425844311"></a>shapeInfo</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p554174121211"><a name="p554174121211"></a><a name="p554174121211"></a>Shape信息，<a href="../../aux_data_structures/shape_info.md">ShapeInfo</a>结构体类型。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section17531157161314"></a>

```cpp
// 示例设置Tensor的ShapeInfo信息
AscendC::LocalTensor<float> maxUb = softmaxMaxBuf.template Get<float>();
uint32_t shapeArray[] = {16, 1024};
maxUb.SetShapeInfo(AscendC::ShapeInfo(2, shapeArray, AscendC::DataFormat::ND));
```


<!-- cannbot:related:start -->
## 相关

- [ReduceShapeInfoOptimizeStack](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/reduce_shapeinfo_optimize_stack.md)（`explains`）：【描述】GlobalTensor和LocalTensor中通过ShapeInfo类型的成员变量来保存shape信息，SetShapeInfo/GetShapeInfo可以设置或者获取ShapeInfo，在算子实现内部用于shape信息保存和传递。默认情况下支持的最大维度为8。在不使用上述ShapeInfo功能的情况下，不需要这些信息，可以通过K_MAX_SHAPE_DIM宏将其设置为0。经实测减小K_MAX_SHAPE_DIM值，可缩减栈空间，减少scalar指令和cache miss几率，提升算子性能。；设置LocalTensor的Shape信息。；指南解释 LocalTensor 的 SetShapeInfo 所保存信息会占用栈空间，并给出未使用该能力时缩减 K_MAX_SHAPE_DIM 的优化条件，从而补充 API 使用成本与停用边界。
- [GetShapeInfo](get_shape_info.md)（`related`）：获取LocalTensor的Shape信息。注意：Shape信息没有默认值，只有通过SetShapeInfo设置过Shape信息后，才可以调用该接口获取正确的Shape信息。；设置LocalTensor的Shape信息。。GetShapeInfo 的正确性前置条件就是先由 SetShapeInfo 写入属性，两接口构成 LocalTensor shape 元数据的写后读合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [BlockSparseAttentionGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `SetShapeInfo(...)` 的直接调用（第 454 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc35/vec_op.h#L454)
- [NsaCompress A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_compress.md)（`related`）：算子声明的固定版本源码包含对 `SetShapeInfo(...)` 的直接调用（第 108 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/common/include/op_kernel/util.h#L108)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
