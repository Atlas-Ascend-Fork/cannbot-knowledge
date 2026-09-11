---
type: API
title: AllocTensor
description: 从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/AllocTensor.md
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
- include/basic_api/kernel_tpipe.h
---

# AllocTensor<a name="ZH-CN_TOPIC_0000001811034064"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。

## 函数原型<a name="section620mcpsimp"></a>

-   non-inplace接口：构造新的Tensor作为内存管理的对象

    ```cpp
    template <typename T>
    __aicore__ inline LocalTensor<T> AllocTensor()
    ```

-   inplace接口：直接使用传入的Tensor作为内存管理的对象，可以减少Tensor反复创建的开销，具体使用指导可参考[Tensor原地操作](../../../../../guides/programming_guide/appendix/common_operations/tensor_inplace_performance.md)。

    ```cpp
    template <typename T>
    __aicore__ inline void AllocTensor(LocalTensor<T>& tensor)
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table1550165916920"></a>
<table><thead align="left"><tr id="row115015591391"><th class="cellrowborder" valign="top" width="12.139999999999999%" id="mcps1.2.3.1.1"><p id="p12501159099"><a name="p12501159099"></a><a name="p12501159099"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="87.86%" id="mcps1.2.3.1.2"><p id="p85019592918"><a name="p85019592918"></a><a name="p85019592918"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row1550117591914"><td class="cellrowborder" valign="top" width="12.139999999999999%" headers="mcps1.2.3.1.1 "><p id="p185019592913"><a name="p185019592913"></a><a name="p185019592913"></a>T</p>
</td>
<td class="cellrowborder" valign="top" width="87.86%" headers="mcps1.2.3.1.2 "><p id="p12101541625"><a name="p12101541625"></a><a name="p12101541625"></a><span>Tensor的数据类型，支持的类型请见<a href="../../data_structures/local_tensor/index.md">LocalTensor</a>相关描述。</span></p>
</td>
</tr>
</tbody>
</table>

**表2**  参数说明

<a name="table181221135162517"></a>
<table><thead align="left"><tr id="row151221135112520"><th class="cellrowborder" valign="top" width="12.471247124712471%" id="mcps1.2.4.1.1"><p id="p1353754532512"><a name="p1353754532512"></a><a name="p1353754532512"></a>参数名称</p>
</th>
<th class="cellrowborder" valign="top" width="12.591259125912593%" id="mcps1.2.4.1.2"><p id="p1253774516259"><a name="p1253774516259"></a><a name="p1253774516259"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="74.93749374937492%" id="mcps1.2.4.1.3"><p id="p1653710452259"><a name="p1653710452259"></a><a name="p1653710452259"></a>含义</p>
</th>
</tr>
</thead>
<tbody><tr id="row12122235102511"><td class="cellrowborder" valign="top" width="12.471247124712471%" headers="mcps1.2.4.1.1 "><p id="p1537164502512"><a name="p1537164502512"></a><a name="p1537164502512"></a>tensor</p>
</td>
<td class="cellrowborder" valign="top" width="12.591259125912593%" headers="mcps1.2.4.1.2 "><p id="p1653714592515"><a name="p1653714592515"></a><a name="p1653714592515"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="74.93749374937492%" headers="mcps1.2.4.1.3 "><p id="p165371945142512"><a name="p165371945142512"></a><a name="p165371945142512"></a>inplace接口需要传入<a href="../../data_structures/local_tensor/index.md">LocalTensor</a>作为内存管理的对象。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

-   non-inplace接口分配的Tensor内容可能包含随机值。
-   non-inplace接口，需要将TQueBind的depth模板参数设置为非零值；inplace接口，需要将TQueBind的depth模板参数设置为0。

## 返回值说明<a name="section640mcpsimp"></a>

non-inplace接口返回值为LocalTensor对象，inplace接口没有返回值。

## 调用示例<a name="section642mcpsimp"></a>

-   non-inplace接口

    ```cpp
    AscendC::TPipe pipe;
    AscendC::TQueBind<AscendC::TPosition::VECOUT, AscendC::TPosition::GM, 2> que;
    int num = 4;
    int len = 1024;
    pipe.InitBuffer(que, num, len); // InitBuffer分配内存块数为4，每块大小为1024Bytes
    AscendC::LocalTensor<half> tensor1 = que.AllocTensor<half>(); // AllocTensor分配Tensor长度为1024Bytes
    ```

-   inplace接口

    ```cpp
    AscendC::TPipe pipe;
    AscendC::TQueBind<AscendC::TPosition::VECOUT, AscendC::TPosition::GM, 0> que;
    int num = 2;
    int len = 1024;
    pipe.InitBuffer(que, num, len); // InitBuffer分配内存块数为2，每块大小为1024Bytes
    AscendC::LocalTensor<half> tensor1;
    que.AllocTensor<half>(tensor1); // AllocTensor分配Tensor长度为1024Bytes
    ```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 71 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 62 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_all_copy.h#L62)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 267 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_all_align.h#L267)
- [InplaceSigmoid A2 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/inplace_sigmoid.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 80 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/experimental/activation/sigmoid_v2/op_kernel/sigmoid.h#L80)
- [FusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 743 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/fused_causal_conv1d_cut_bsh.h#L743)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 63 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_all_copy.h#L63)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.h#L57)
- [Sigmoid A2 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/sigmoid.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 80 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/experimental/activation/sigmoid_v2/op_kernel/sigmoid.h#L80)
- [InplaceFusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/inplace_fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 743 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/fused_causal_conv1d_cut_bsh.h#L743)
- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 77 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/arch35/upsample_bicubic2d_aa_data_copy.h#L77)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `AllocTensor(...)` 的直接调用（第 164 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/arch32/circular_pad_grad.h#L164)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
