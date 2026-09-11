---
type: API
title: GET_TILING_DATA_WITH_STRUCT
description: 使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# GET\_TILING\_DATA\_WITH\_STRUCT<a name="ZH-CN_TOPIC_0000001867523629"></a>

## 功能说明<a name="zh-cn_topic_0000001526206862_section212607105720"></a>

使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与[GET\_TILING\_DATA](get_tiling_data.md)的区别是：[GET\_TILING\_DATA](get_tiling_data.md)只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。

## 函数原型<a name="zh-cn_topic_0000001526206862_section1630753514297"></a>

```
GET_TILING_DATA_WITH_STRUCT(struct_name, tiling_data, tiling_arg)
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
<tbody><tr id="row472122142712"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p6721528274"><a name="p6721528274"></a><a name="p6721528274"></a>struct_name</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="p17721152142712"><a name="p17721152142712"></a><a name="p17721152142712"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p372120282711"><a name="p372120282711"></a><a name="p372120282711"></a>指定的结构体名称。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a>tiling_data</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a>输出</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a>返回指定Tiling结构体变量。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_row1239183183016"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_p223953193015"><a name="zh-cn_topic_0000001526206862_p223953193015"></a><a name="zh-cn_topic_0000001526206862_p223953193015"></a>tiling_arg</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_p7239938308"><a name="zh-cn_topic_0000001526206862_p7239938308"></a><a name="zh-cn_topic_0000001526206862_p7239938308"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_p72396320307"><a name="zh-cn_topic_0000001526206862_p72396320307"></a><a name="zh-cn_topic_0000001526206862_p72396320307"></a>此参数为算子入口函数处传入的tiling参数。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001526206862_section65498832"></a>

-   本函数需在算子核函数（Kernel）代码处使用，并且传入的tiling\_data参数不需要声明类型。
-   暂不支持核函数（Kernel）直调工程。

## 调用示例<a name="zh-cn_topic_0000001526206862_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    KernelAdd op;
    if (TILING_KEY_IS(1)) {
        GET_TILING_DATA_WITH_STRUCT(Add_Struct_Special, tilingData, tiling); // 使用算子指定注册的结构体
	op.Init(x, y, z, tilingData.totalLengthSpecial, tilingData.tileNumSpecial);
    } else {
        GET_TILING_DATA(tilingData, tiling);   // 使用算子默认注册的结构体
	op.Init(x, y, z, tilingData.totalLength, tilingData.tileNum);
    }
    if (TILING_KEY_IS(1)) {
        op.Process();
    } else if (TILING_KEY_IS(2)) {
        op.Process();
    } else if (TILING_KEY_IS(3)) {
        op.Process();
    }
}
```



<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。 构建 Ascend950 kernel 时报 C++ 解析错，出错行即 `GET_TILING_DATA_WITH_STRUCT(MaskedFillTilingData<RANK>, tilingData, tiling);`。 宏展开在模板类型的 `<>` 字符串化处产生解析错误，Runbook 还区分了分支绕过后节级注册丢失。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：**机制解释**（根因分析，属 interpretation）：`REGISTER_TILING_DEFAULT(T)` 把 struct `T` 注册为**整个算子的唯一 default tiling structure**。同一算子的多条 `if constexpr` 模板实例化分支在编译期都被实例化（即使运行时只走一条）；若两条分支用 `REGISTER_TILING_DEFAULT` 注册了**不同的** struct，opbuild 在收集 default 注册时看到两个候选 default，无法决定用哪一个，遂报 `Only one default tiling structure can be configured.`。既有 SmallKernel 多条分支全部注册**同一个** struct 故不冲突；SIMT 分支用 `REGISTER_TILING_FOR_TILINGKEY` 按 key 注册、不占 default 槽位。新增分支引入第二个不同 struct 却仍占 default 槽位，正是冲突来源——按 key 注册即可规避。；使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。Runbook 的多 key 结构体方案需要按具体类型读取，API 卡给出指定结构体而非只读 default 的消费方式。
- [TilingData 追加数据超额致 INVALID_TILING](../../../../runbooks/compilation/tilingdata_invalid_tiling.md)（`exemplifies`）：- **工程形态**：ops-registry-invoke 自定义算子仓，host Tiling 用 `GetRawTilingData()` / `GetTilingData<T>()` 写 TilingData，并在 struct 之后追加额外数据（如全精度标量向量）；kernel 用 `GET_TILING_DATA_WITH_STRUCT` + 手动偏移读取尾区。；使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。Runbook的 kernel 先用该宏解包注册 struct，再手动读取尾区；API 卡明确宏只负责指定结构体的 tiling 信息，支撑区分 struct 与额外数据容量。
- [aicore 禁止 const char* cast 到 __gm__ T*](../../../../runbooks/compilation/aicore_const_char_cast_gm_t.md)（`exemplifies`）：若只需读 TilingData struct 内字段，`GET_TILING_DATA_WITH_STRUCT` 已把 struct 从 GM `memcpy` 到栈局部变量，直接用 `tilingData->field` 即可，无需手算 GM 偏移；用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。。Runbook把宏产生的局部 TilingData 作为避免非法 GM 指针转换的首选修法，API 卡给出该宏的确切填充合同。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。 `GET_TILING_DATA_WITH_STRUCT` 宏未定义——直调编译路径没有自定义算子打包系统生成的宏。 API 的编译期宏合同解释直调为何缺定义，Runbook 给出显式 `__gm__` 逐字段拷贝替代。
- [FastGelu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“Host 的 `GetTilingData<EleBaseTilingDataV2>` 与 entry 的 `REGISTER_TILING_DEFAULT/GET_TILING_DATA_WITH_STRUCT` 使用同一声明。”闭合 FastGelu 的 POD producer/consumer；“该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。”解释 entry 按结构体名解析 Tiling 的合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 127 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 32 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/upsample_bicubic2d_aa_apt.cpp#L32)
- [All 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/all_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 28 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/fill/op_kernel/fill_apt.cpp#L28)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.cpp#L33)
- [BlockSparseAttentionGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 116 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc22/attn_infra/epilogue/block/block_epilogue_softmaxgrad.hpp#L116)
- [UpsampleBicubic2dAAGrad 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad_apt.cpp#L31)
- [BitwiseNot 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/bitwise_not_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 27 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/invert/op_kernel/invert_apt.cpp#L27)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu_apt.cpp#L31)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_kernel/flash_attention_score_apt.cpp#L50)
- [UpsampleNearest3d 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 32 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_nearest3d/op_kernel/upsample_nearest3d_apt.cpp#L32)
- [Ceil 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/ceil_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA_WITH_STRUCT(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/ceil/op_kernel/ceil_apt.cpp#L31)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
