---
type: API
title: TILING_KEY_IS
description: 在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_IS.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
---

# TILING\_KEY\_IS<a name="ZH-CN_TOPIC_0000001586995454"></a>

## 功能说明<a name="zh-cn_topic_0000001610027821_section212607105720"></a>

在核函数（Kernel）中判断本次执行时的tiling\_key是否等于host侧运行时设置的某个key，从而标识tiling\_key==key的一条kernel分支。

## 函数原型<a name="zh-cn_topic_0000001610027821_section1630753514297"></a>

```
TILING_KEY_IS(key)
```

## 参数说明<a name="zh-cn_topic_0000001610027821_section129451113125413"></a>

<a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p10223674448"><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p10223674448"></a><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p645511218169"><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p645511218169"></a><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p1922337124411"><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p1922337124411"></a><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p2340183613156"><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p2340183613156"></a><a name="zh-cn_topic_0000001610027821_zh-cn_topic_0000001389783361_p2340183613156"></a>key</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001610027821_p18857658124919"><a name="zh-cn_topic_0000001610027821_p18857658124919"></a><a name="zh-cn_topic_0000001610027821_p18857658124919"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001610027821_p53562135013"><a name="zh-cn_topic_0000001610027821_p53562135013"></a><a name="zh-cn_topic_0000001610027821_p53562135013"></a>key表示某个核函数（Kernel）的分支，必须是非负整数。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001610027821_section65498832"></a>

-   TILING\_KEY\_IS运用于if和else if分支，不支持else分支，即用TILING\_KEY\_IS函数来表征N个分支，必须用N个TILING\_KEY\_IS\(key\)来分别表示。
-   暂不支持核函数（Kernel）直调工程。

## 调用示例<a name="zh-cn_topic_0000001610027821_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *workspace, __gm__ uint8_t *tiling)
{
    GET_TILING_DATA(tilingData, tiling);
    if (workspace == nullptr) {
        return;
    }
    KernelAdd op;
    op.Init(x, y, z, tilingData.numBlocks, tilingData.totalLength, tilingData.tileNum);
    // 当TilingKey为1时，执行Process1；为2时，执行Process2；为3时，执行Process3
    if (TILING_KEY_IS(1)) {
        op.Process1();
    } else if (TILING_KEY_IS(2)) {
        op.Process2();
    } else if (TILING_KEY_IS(3)) {
        op.Process3();
    }
    // 其他代码逻辑
    ...
    // 此处示例当TilingKey为3时，会执行ProcessOther
    if (TILING_KEY_IS(3)) {
        op.ProcessOther();
    }
}
```

配套的host侧tiling函数示例（伪代码）：

```
ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    // 其他代码逻辑
    ...
    if (context->GetInputShape(0) > 10) {
        context->SetTilingKey(1);
    } else if (some condition) {
        context->SetTilingKey(2);
    } else if (some condition) {
        context->SetTilingKey(3);
    }
}
```



<!-- cannbot:related:start -->
## 相关

- [IcpuSetTilingKey](../debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`related`）：指定本次CPU调测使用的tilingKey；判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；连接调测 key 设置与 Kernel 分支消费。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`same_topic`）：判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；注册与 TilingKey 相匹配的 TilingData 结构体。REGISTER_TILING_FOR_TILINGKEY 先把 key 条件映射到 TilingData，TILING_KEY_IS 再在 kernel 中选择相同 key 的执行分支；两者共同保证数据结构和代码分支匹配。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 166 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/resize_bilinear_v2_apt.cpp#L50)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 25 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.cpp#L25)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 32 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.cpp#L32)
- [NsaCompressAttentionInfer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/nsa_compress_attention_infer.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 35 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_compress_attention_infer/op_kernel/nsa_compress_attention_infer.cpp#L35)
- [ThreeInterpolateBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/three_interpolate_backward.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 354 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/three_interpolate_backward/op_kernel/three_interpolate_backward.cpp#L354)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 27 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/circular_pad_grad.cpp#L27)
- [FatreluMul A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fatrelu_mul.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 30 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/fatrelu_mul/op_kernel/fatrelu_mul.cpp#L30)
- [NsaSelectedAttention A2 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/nsa_selected_attention.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 66 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_selected_attention/op_kernel/nsa_selected_attention.cpp#L66)
- [NMS 950 Direct Invoke 算子知识](../../../../operators/direct/cv/image/nms_950.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 38 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/nms_with_mask/op_kernel/nms_with_mask_apt.cpp#L38)
- [CircularPad3d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_3d.md)（`related`）：算子声明的固定版本源码包含对 `TILING_KEY_IS(...)` 的直接调用（第 25 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.cpp#L25)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
