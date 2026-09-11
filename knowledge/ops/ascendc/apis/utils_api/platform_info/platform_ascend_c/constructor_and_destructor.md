---
type: API
title: 构造及析构函数（PlatformAscendC）
description: 在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# 构造及析构函数<a name="ZH-CN_TOPIC_0000002078498898"></a>

## 功能说明<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section36583473819"></a>

在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。

## 函数原型<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
PlatformAscendC() = delete
~PlatformAscendC() = default
explicit PlatformAscendC(fe::PlatFormInfos *platformInfo): platformInfo_(platformInfo) {}
```

## 参数说明<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section189014013619"></a>

<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p10223674448"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p10223674448"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p645511218169"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p645511218169"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p1922337124411"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p1922337124411"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p17770136956"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p17770136956"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p17770136956"></a>platformlnfo</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p167701536957"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p167701536957"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p167701536957"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p4611154016587"><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p4611154016587"></a><a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_p4611154016587"></a>platformInfo结构体，通过GetPlatformInfo接口可以获取。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section25791320141317"></a>

无

## 约束说明<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001674924029_zh-cn_topic_0000001442758437_section320753512363"></a>

```
ge::graphStatus TilingXXX(gert::TilingContext* context) {
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    uint64_t ub_size, l1_size;
    ascendcPlatform.GetCoreMemSize(platform_ascendc::CoreMemType::UB, ub_size);
    ascendcPlatform.GetCoreMemSize(platform_ascendc::CoreMemType::L1, l1_size);
    auto aicNum = ascendcPlatform.GetCoreNumAic();
    auto aivNum = ascendcPlatform.GetCoreNumAiv();
    // ... 按照aivNum切分
    context->SetSimdNumBlocks(ascendcPlatform.CalcTschNumBlocks(aivNum, aicNum, aivNum));
    return ret;
}
```



<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：诊断后的处置方向：GetShapeInfo 不再硬依赖 CompileInfo，null 时回退到 `ctx_->GetPlatformInfo()` + `PlatformAscendC` 直读 `coreNum`/`ubSize`；UT 直接编译 tiling.cpp 时需为 PlatformAscendC 追加 `platform` 链接库。；在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。。Runbook 给出 CompileInfo 为空时改由 PlatformAscendC 读取 coreNum/ubSize 的修复，API 卡定义该类的硬件信息能力。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 560 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 187 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_host/arch35/col2im_tiling_arch35.cpp#L187)
- [Cat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 1514 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_host/arch35/concat_tiling_arch35.cpp#L1514)
- [Celu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 39 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_host/arch35/celu_v2_tiling_arch35.cpp#L39)
- [AttentionUpdate A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/attention_update.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 131 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_host/decode_update_tiling.cpp#L131)
- [Rasterizer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 125 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_host/rasterizer_tiling.cpp#L125)
- [ChunkCat A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/chunk_cat.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 51 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_host/chunk_cat_tiling.cpp#L51)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 58 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_host/clipped_swiglu_tiling.cpp#L58)
- [AttentionUpdate 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 65 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_host/attention_update_tiling.cpp#L65)
- [Resize 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 884 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_host/arch35/resize_bilinear_v2_tiling_arch35.cpp#L884)
- [ChunkCat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子声明的固定版本源码包含对 `PlatformAscendC(...)` 的直接调用（第 51 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_host/chunk_cat_tiling.cpp#L51)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
