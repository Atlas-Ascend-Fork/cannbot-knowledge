---
type: API
title: GET_TILING_DATA_WITH_STRUCT
description: 使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA_WITH_STRUCT

使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。

用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体。

本接口组包含 GET_TILING_DATA, GET_TILING_DATA。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。 构建 Ascend950 kernel 时报 C++ 解析错，出错行即 `GET_TILING_DATA_WITH_STRUCT(MaskedFillTilingData<RANK>, tilingData, tiling);`。 宏展开在模板类型的 `<>` 字符串化处产生解析错误，Runbook 还区分了分支绕过后节级注册丢失。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：**机制解释**（根因分析，属 interpretation）：`REGISTER_TILING_DEFAULT(T)` 把 struct `T` 注册为**整个算子的唯一 default tiling structure**。同一算子的多条 `if constexpr` 模板实例化分支在编译期都被实例化（即使运行时只走一条）；若两条分支用 `REGISTER_TILING_DEFAULT` 注册了**不同的** struct，opbuild 在收集 default 注册时看到两个候选 default，无法决定用哪一个，遂报 `Only one default tiling structure can be configured.`。既有 SmallKernel 多条分支全部注册**同一个** struct 故不冲突；SIMT 分支用 `REGISTER_TILING_FOR_TILINGKEY` 按 key 注册、不占 default 槽位。新增分支引入第二个不同 struct 却仍占 default 槽位，正是冲突来源——按 key 注册即可规避。；使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。Runbook 的多 key 结构体方案需要按具体类型读取，API 卡给出指定结构体而非只读 default 的消费方式。
- [TilingData 追加数据超额致 INVALID_TILING](../../../../runbooks/compilation/tilingdata_invalid_tiling.md)（`exemplifies`）：- **工程形态**：ops-registry-invoke 自定义算子仓，host Tiling 用 `GetRawTilingData()` / `GetTilingData<T>()` 写 TilingData，并在 struct 之后追加额外数据（如全精度标量向量）；kernel 用 `GET_TILING_DATA_WITH_STRUCT` + 手动偏移读取尾区。；使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。。Runbook的 kernel 先用该宏解包注册 struct，再手动读取尾区；API 卡明确宏只负责指定结构体的 tiling 信息，支撑区分 struct 与额外数据容量。
- [aicore 禁止 const char* cast 到 __gm__ T*](../../../../runbooks/compilation/aicore_const_char_cast_gm_t.md)（`exemplifies`）：若只需读 TilingData struct 内字段，`GET_TILING_DATA_WITH_STRUCT` 已把 struct 从 GM `memcpy` 到栈局部变量，直接用 `tilingData->field` 即可，无需手算 GM 偏移；用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。。Runbook把宏产生的局部 TilingData 作为避免非法 GM 指针转换的首选修法，API 卡给出该宏的确切填充合同。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。 `GET_TILING_DATA_WITH_STRUCT` 宏未定义——直调编译路径没有自定义算子打包系统生成的宏。 API 的编译期宏合同解释直调为何缺定义，Runbook 给出显式 `__gm__` 逐字段拷贝替代。
- [FastGelu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“Host 的 `GetTilingData<EleBaseTilingDataV2>` 与 entry 的 `REGISTER_TILING_DEFAULT/GET_TILING_DATA_WITH_STRUCT` 使用同一声明。”闭合 FastGelu 的 POD producer/consumer；“该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。”解释 entry 按结构体名解析 Tiling 的合同。
<!-- cannbot:related:end -->
