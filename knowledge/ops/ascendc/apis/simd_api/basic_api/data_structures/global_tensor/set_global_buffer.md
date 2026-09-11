---
type: API
title: SetGlobalBuffer
description: 传入全局数据地址，初始化GlobalTensor。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetGlobalBuffer.md
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

# SetGlobalBuffer<a name="ZH-CN_TOPIC_0000002132243132"></a>

## 功能说明<a name="section618mcpsimp"></a>

传入全局数据地址，初始化GlobalTensor。

## 函数原型<a name="section620mcpsimp"></a>

-   传入全局数据的指针，并设置存储大小（通过元素个数表达）。

    ```cpp
    __aicore__ inline void SetGlobalBuffer(__gm__ PrimType* buffer, uint64_t bufferSize)
    ```

-   仅传入全局数据的指针，此时通过[GetSize](get_size.md)获取到的元素个数为0。

    ```cpp
    __aicore__ inline void SetGlobalBuffer(__gm__ PrimType* buffer)
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
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p284425844311"><a name="p284425844311"></a><a name="p284425844311"></a>buffer</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p126017529210"><a name="p126017529210"></a><a name="p126017529210"></a>Host侧传入的全局数据指针。PrimType类型。</p>
<p id="p18421731162810"><a name="p18421731162810"></a><a name="p18421731162810"></a><span id="ph169021373405"><a name="ph169021373405"></a><a name="ph169021373405"></a>PrimType定义如下：</span></p>
<a name="screen449513476423"></a><a name="screen449513476423"></a><pre class="screen" codetype="Cpp" id="screen449513476423">// PrimT用于从T中提取基础数据类型：T传入基础数据类型，直接返回数据类型；T传入为TensorTrait类型时萃取TensorTrait中的LiteType基础数据类型
using PrimType = PrimT&lt;T&gt;;</pre>
</td>
</tr>
<tr id="row184841037192110"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p4484123719216"><a name="p4484123719216"></a><a name="p4484123719216"></a>bufferSize</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p18484133715217"><a name="p18484133715217"></a><a name="p18484133715217"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="zh-cn_topic_0000001491300625_p114145113516"><a name="zh-cn_topic_0000001491300625_p114145113516"></a><a name="zh-cn_topic_0000001491300625_p114145113516"></a>GlobalTensor所包含的类型为PrimType的数据个数，需自行保证不会超出实际数据的长度。如指向的外部存储有连续256个int32_t，则其bufferSize为256。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

无。

## 约束说明<a name="section633mcpsimp"></a>

无。

## 调用示例<a name="section17531157161314"></a>

```cpp
uint64_t dataSize = 256; //设置input_global的大小为256

AscendC::GlobalTensor<int32_t> inputGlobal; // 类型为int32_t
inputGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t *>(src_gm), dataSize); // 设置源操作数在Global Memory上的起始地址为src_gm，所占外部存储的大小为256个int32_t

AscendC::LocalTensor<int32_t> inputLocal = inQueueX.AllocTensor<int32_t>();    
AscendC::DataCopy(inputLocal, inputGlobal, dataSize); // 将Global Memory上的inputGlobal拷贝到Local Memory的inputLocal上
```


<!-- cannbot:related:start -->
## 相关

- [DataCopy 不自动按 tile 推进须显式元素 offset](../../../../../runbooks/precision/datacopy_setglobalbuffer_no_auto_advance_tileoffset.md)（`exemplifies`）：“传入 GM 全局数据地址和大小，初始化 GlobalTensor。”给出焦点端事实；“GlobalTensor::SetGlobalBuffer(ptr, len)”给出候选端事实。API 卡说明 SetGlobalBuffer 只绑定 GM 地址与大小，runbook 用该调用复现多次 DataCopy 不会自动推进位置的故障，并给出显式 tileOffset 的修复边界。
- [GlobalTensor构造函数](global_tensor_constructor.md)（`related`）：GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。；传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。。构造函数只产生空对象并明确指定后接 SetGlobalBuffer，目标接口负责绑定 GM 地址和元素数，二者组成 GlobalTensor 从空对象到可访问全局内存视图的初始化顺序。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 469 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 49 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/arch35/col2im_simt.h#L49)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 89 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_all_align.h#L89)
- [Celu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 81 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_kernel/arch35/celu_v2.h#L81)
- [AttentionUpdate A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 60 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/decode_update.h#L60)
- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 138 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L138)
- [ChunkCat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_common.h#L88)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L93)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 293 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/block_sparse_attention_kernel_regular_arch22.h#L293)
- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 146 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_nc.h#L146)
- [ChunkCat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子声明的固定版本源码包含对 `SetGlobalBuffer(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_common.h#L88)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
