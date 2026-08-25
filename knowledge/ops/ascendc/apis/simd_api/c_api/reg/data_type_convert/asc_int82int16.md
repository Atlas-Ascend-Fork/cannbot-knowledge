---
type: API
title: AscInt82int16
description: 将int8类型数据转换为int16类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int82int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscInt82int16

将int8类型数据转换为int16类型。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscInt82int16》说明将int8类型数据转换为int16类型。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [asc_int82int32 (废弃)](asc_int82int32_deprecated.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《AscInt82int16》说明将int8类型数据转换为int16类型。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
- [类型转换](data_type_convert.md)（`related`）：AscInt82int16 与《类型转换》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
- [AscInt162Uint8](asc_int162uint8.md)（`same_topic`）：AscInt82int16 与《AscInt162Uint8》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
- [AscUint82uint16](asc_uint82uint16.md)（`same_topic`）：AscInt82int16 与《AscUint82uint16》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
<!-- cannbot:related:end -->
