---
type: API
title: Tiling数据结构注册
description: Tiling数据结构注册接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/Tiling_data_structure_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Tiling数据结构注册

提供 TilingData 结构体的定义与注册能力。TilingData 结构定义通过 BEGIN_TILING_DATA_DEF、TILING_DATA_FIELD_DEF、TILING_DATA_FIELD_DEF_ARR、TILING_DATA_FIELD_DEF_STRUCT 和 END_TILING_DATA_DEF 等宏定义字段，继承 TilingDef 后自动生成 set_/get_ 接口用于 Host 侧读写字段值。
TilingData 结构注册通过 REGISTER_TILING_DATA_CLASS 宏将 TilingData 类与算子绑定，支持注册默认结构体、中间结构体（虚拟算子名为 struct_name#Op）和按 tiling_key 定制的结构体（op_type 命名为 ${op_type}_${tiling_key}）。
约束：字段仅支持 int8_t~uint64_t、float 等通用数据类型；结构体成员需满足字节对齐；tiling 结构体名需全局唯一，不同算子注册同名不同结构体会产生未定义行为。需包含头文件 register/tilingdata_base.h。

<!-- cannbot:related:start -->
## 相关

- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《Tiling数据结构注册》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《Tiling数据结构注册》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [TILING_DATA_DEF 迁移 rebase 字段失配判别](../../../runbooks/compilation/tiling_data_def_rebase.md)（`exemplifies`）：Tiling数据结构注册 与《TILING_DATA_DEF 迁移 rebase 字段失配判别》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [TilingData 追加数据超额致 INVALID_TILING](../../../runbooks/compilation/tilingdata_invalid_tiling.md)（`exemplifies`）：Tiling数据结构注册 与《TilingData 追加数据超额致 INVALID_TILING》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [限制TilingData结构大小](../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：Tiling数据结构注册 与《限制TilingData结构大小》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [REGISTER_TILING_DEFAULT](../../simd_api/basic_api/kernel_tiling/register_tiling_default.md)（`related`）：Tiling数据结构注册 与《REGISTER_TILING_DEFAULT》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [TilingData结构定义](tiling_data_struct_definition.md)（`same_topic`）：Tiling数据结构注册 与《TilingData结构定义》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [TilingData结构注册](tiling_data_struct_register.md)（`same_topic`）：Tiling数据结构注册 与《TilingData结构注册》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
<!-- cannbot:related:end -->
