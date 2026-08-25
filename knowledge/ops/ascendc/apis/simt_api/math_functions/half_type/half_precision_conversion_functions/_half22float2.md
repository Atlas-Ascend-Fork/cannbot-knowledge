---
type: API
title: __half22float2
description: 将half2的两个分量分别转换为float，填充到float2后返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half22float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half22float2

功能：将half2的两个分量分别转换为float，填充到float2后返回。

函数原型：float2 __half22float2(const half2 x)

参数：x（输入）源操作数。

返回值：将half2的两个分量分别转换为float，并填充到float2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。


支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rd](_float22half2_rd.md)（`related`）：__float22half2_rd 与《__half22float2》的实质衔接是：float2→half2 RD 与饱和、其他舍入、反向 half2→float2 和双 float 拼装入口共享双 lane 窄化契约。
- [__float22half2_rn_sat](_float22half2_rn_sat.md)（`related`）：__float22half2_rn_sat 与《__half22float2》的实质衔接是：float2→half2 RN 饱和接口与非饱和/其他舍入、双 float 拼装和反向 half2→float2 共享双 lane 窄化契约。
- [__float22half2_rz](_float22half2_rz.md)（`related`）：__half22float2 将 half2 两 lane 宽化回 float2，是本 float2→half2 窄化结果的直接逆向消费路径。
- [__float22half2_rz_sat](_float22half2_rz_sat.md)（`related`）：__half22float2 是 packed half2 到 float2 的反向扩精度接口，可连接 focal 生成的 half2 与后续 fp32 计算。
- [AscHalf2Float](../../../../simd_api/c_api/reg/data_type_convert/asc_half2float.md)（`same_topic`）：AscHalf2Float说明将half类型数据转换为float类型，无舍入模式。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
- [__e5m2x22float2](../../fp8_type/fp8_conversion_functions/_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《__half22float2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [__float22half2_ro](_float22half2_ro.md)（`same_topic`）：__float22half2_ro 与《__half22float2》的实质衔接是：__float22half2_ro 与 RO-sat、RD/RN/RNA/RU/RZ 变体共享 float2→half2 双 lane 窄化，只改变舍入或饱和；scalar RO 和反向 half2→float2 明确向量封装及转换方向。
- [__half2float](_half2float.md)（`same_topic`）：__half2float 与《__half22float2》的衔接是：C Reg、C Vector 和 half2 转换入口都执行 half 到 float 的数值扩展，仅批宽与执行单元不同。
<!-- cannbot:related:end -->
