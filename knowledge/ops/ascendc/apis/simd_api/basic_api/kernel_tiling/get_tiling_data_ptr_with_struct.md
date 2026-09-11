---
type: API
title: GET_TILING_DATA_PTR_WITH_STRUCT
description: 在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_PTR_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# GET\_TILING\_DATA\_PTR\_WITH\_STRUCT<a name="ZH-CN_TOPIC_0000002448078405"></a>

## 功能说明<a name="zh-cn_topic_0000001526206862_section212607105720"></a>

在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用\_\_tiling\_data\_ptr\_\_修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。

## 函数原型<a name="zh-cn_topic_0000001526206862_section1630753514297"></a>

```
GET_TILING_DATA_PTR_WITH_STRUCT(tiling_struct, dst_ptr, tiling_ptr)
```

## 参数说明<a name="zh-cn_topic_0000001526206862_section129451113125413"></a>

<a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row472122142712"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p6721528274"><a name="p6721528274"></a><a name="p6721528274"></a>tiling_struct</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="p17721152142712"><a name="p17721152142712"></a><a name="p17721152142712"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p372120282711"><a name="p372120282711"></a><a name="p372120282711"></a>指定的结构体名称。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a>dst_ptr</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a>输出</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a>返回指定的Tiling结构体指针。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_row1239183183016"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_p223953193015"><a name="zh-cn_topic_0000001526206862_p223953193015"></a><a name="zh-cn_topic_0000001526206862_p223953193015"></a>tiling_ptr</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_p7239938308"><a name="zh-cn_topic_0000001526206862_p7239938308"></a><a name="zh-cn_topic_0000001526206862_p7239938308"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_p72396320307"><a name="zh-cn_topic_0000001526206862_p72396320307"></a><a name="zh-cn_topic_0000001526206862_p72396320307"></a>算子入口函数处传入的Tiling参数。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001526206862_section65498832"></a>

-   该宏需在算子核函数（Kernel）代码处使用，并且传入的dst\_ptr参数无需声明类型。
-   动态Shape场景下，获取到的dst\_ptr是指向Global Memory变量的指针；静态Shape场景下，获取到的dst\_ptr是指向局部变量的指针，需确保在合理的作用域范围内使用。
-   暂不支持核函数（Kernel）直调工程。

## 调用示例<a name="zh-cn_topic_0000001526206862_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    KernelAdd op;

    GET_TILING_DATA_PTR_WITH_STRUCT(AddCustomTilingData, tilingDataPtr, tiling);

    op.Init(x, y, z, tilingDataPtr->totalLength, tilingDataPtr->tileNum);
    op.Process();
    
}
```

以下是错误调用的示例：

```
__aicore__ __tiling_data_ptr__ AddCustomTilingData* foo(__gm__ uint8_t *tiling)
{
    GET_TILING_DATA_PTR_WITH_STRUCT(AddCustomTilingData, tilingDataPtr, tiling);
    return tilingDataPtr;
}

extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    KernelAdd op;

    auto tilingDataPtr = foo(tiling);  // 错误，foo函数已经执行完成，非法访问生命周期已经结束的局部变量

    op.Init(x, y, z, tilingDataPtr->totalLength, tilingDataPtr->tileNum);
    op.Process();
}
```



<!-- cannbot:related:start -->
## 相关

- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：约束：该宏需在算子Kernel代码处使用，并且传入的dst_ptr参数无需声明类型。；动态Shape场景下，获取到的dst_ptr是指向Global Memory变量的指针；静态Shape场景下，获取到的dst_ptr是指向局部变量的指针，需确保在合理的作用域范围内使用。；暂不支持Kernel直调工程。；- **原始观测**：本 trace 中 `grep` 命中宏只在 host 侧 tiling 生成路径，ASC 编译器对直调 `.asc` 不注入该宏；改为逐字段拷贝后编译通过（仅余 `__gm__` cast 在 host 侧被忽略的无害 warning）。；焦点声明 PTR_WITH_STRUCT 的直调限制，目标卡给出同族宏在直调工程中缺失及逐字段读取的实测绕行。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 15 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ReplicationPad2d 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/replication_pad_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 131 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_simt.h#L131)
- [MishBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/mish_backward.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 25 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/mish_grad/op_kernel/mish_grad_apt.cpp#L25)
- [ReplicationPad3d 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/replication_pad_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 131 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_simt.h#L131)
- [Gelu 950 Direct Invoke 算子知识](../../../../operators/direct/nn/activation/gelu_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 29 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_v2/op_kernel/gelu_v2_apt.cpp#L29)
- [Slice 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/slice_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 150 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/strided_slice/op_kernel/arch35/strided_slice_simt.h#L150)
- [Gather 950 Direct Invoke 算子知识](../../../../operators/direct/nn/index/gather_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 71 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_elements/op_kernel/arch35/gather_elements.h#L71)
- [SliceV2 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/slice_v2_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 150 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/strided_slice/op_kernel/arch35/strided_slice_simt.h#L150)
- [StridedSlice 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/strided_slice_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 150 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/strided_slice/op_kernel/arch35/strided_slice_simt.h#L150)
- [InplaceLog10 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_log10_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 28 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/log/op_kernel/log_apt.cpp#L28)
- [InplaceLog2 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_log2_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_PTR_WITH_STRUCT(...)` 的直接调用（第 28 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/log/op_kernel/log_apt.cpp#L28)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
