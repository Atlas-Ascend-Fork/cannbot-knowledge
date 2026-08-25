---
type: API
title: SatMode
description: SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT,
  SAT };&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；&bull;&nbsp;&nbsp;SAT：饱和模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/SatMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SatMode

SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT,

本接口属于 Reg 矢量计算辅助数据类型定义。

# SatMode | 参数名 | 描述 | | :-- | :-- | | SatMode | 用于设置Cast类型转换饱和与不饱和模式。 enum class SatMode { UNKNOWN = -1, NO_SAT, SAT }; • UNKNOWN：当转换类型不支持SatMode时，选择该模式； • NO_SAT：不饱和模式； • SAT：饱和模式。 |

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：SatMode 枚举定义 SAT/NO_SAT 语义，本卡进一步给出 dav-3510 Cast 实现硬编码 SAT 后 NaN/Inf 变为 65504 的实测边界。
- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《SatMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [Cast](../type_conversion/cast.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《SatMode》说明SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT, SAT };&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；&bull;&nbsp;&nbsp;SAT：饱和模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [RoundMode](round_mode.md)（`same_topic`）：RoundMode 与《SatMode》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
<!-- cannbot:related:end -->
