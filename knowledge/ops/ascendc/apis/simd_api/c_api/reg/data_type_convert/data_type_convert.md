---
type: API
title: 类型转换
description: 寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/data_type_convert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 类型转换

寄存器侧类型转换接口覆盖bfloat16/half/float/int8/int16/int32/int64/uint8/uint16/uint32等数据类型间的相互转换，命名遵循asc_<src>2<dst>规范。
舍入接口含asc_ceil/floor/round/trunc/rint，提供不同的取整模式，舍入模式与饱和模式的配置说明见专文档。
多个e1m2/e2m1/e4m3/e5m2/hif8/int4x2相关转换接口已废弃，建议使用asc_half2hif8/hif82half等替代接口。

<!-- cannbot:related:start -->
## 相关

- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《类型转换》说明寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [AscInt82int16](asc_int82int16.md)（`related`）：AscInt82int16 与《类型转换》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
- [AscTrunc](asc_trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《类型转换》说明寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [asc_bfloat162e1m2x2 (废弃)](asc_bfloat162e1m2x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《类型转换》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_float2e5m2 (废弃)](asc_float2e5m2_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《类型转换》具体提供“寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
<!-- cannbot:related:end -->
