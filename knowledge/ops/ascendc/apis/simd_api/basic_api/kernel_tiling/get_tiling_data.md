---
type: API
title: GET_TILING_DATA
description: 用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA

获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — stub kernel tiling 数据未初始化](../../../../runbooks/compilation/aclnn_507035_stub_tilingfunc_must_init_tiling_buffer.md)（`exemplifies`）：stub TilingFunc 必须调用 `context->GetTilingData<TilingDataT>()` 取得指针并写入至少一个字段（如 `totalLength`），再 `SetBlockDim`/workspace；kernel 侧保持接口桩不变。修复后 11/11 冒烟通过。；获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。。运行手册用 Host GetTilingData 初始化字段来消除 stub 的 507035，API 卡说明 Kernel 宏如何读取注册结构体，二者把故障修复连接到 Host 生产、Device 消费同一 TilingData 缓冲的合同。
- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。；`GET_TILING_DATA(var_name, tiling_arg)` → 展开为 `HistogramTilingData var_name; InitTilingData<HistogramTilingData>(tiling_arg, &var_name);`（首参为变量名，非类型名）。。运行手册用真实宏展开说明接口首参为何必须是变量名，并给出编译失败探针。
- [TilingData 须 host 与 kernel 各定义一份](../../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：AscendC 算子的 TilingData struct 需要同时被两个编译器看到：；获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。runbook 的 host 完整类型报错发生在生产侧，GET_TILING_DATA 页明确 Kernel 消费同一注册结构体，能核对两端 ABI。
- [限制TilingData结构大小](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：“调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。”。Guide 解释为何要减小 GET_TILING_DATA 从 GM 到栈的搬运量，API 卡界定该宏的实际取数行为。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“Host `SaveToBuffer` 与 Device `GET_TILING_DATA` 使用同一注册结构，字段顺序不得改变。”给出 DequantBias 的 POD ABI 闭环；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。”说明 Device 宏在该闭环中的消费职责。
- [HardswishBackwardV2 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/hardswish_backward_v2_950.md)（`related`）：“GET_TILING_DATA(tilingData, tiling);”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。”。950 operator entry 实际调用该宏把 Host 生成的 HardSwishGradV2TilingData 解析到 Device，API 定义其宏展开合同。
- [TilingData结构定义](../../../utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`related`）：“- SaveToBuffer接口：完成TilingData的序列化和保存。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。”。Host 序列化的 TilingData 经 kernel 入参传递后由 GET_TILING_DATA 反序列化到同一注册结构。
<!-- cannbot:related:end -->
