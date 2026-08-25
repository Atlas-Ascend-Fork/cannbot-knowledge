---
type: API
title: AscFloat2Int64
description: 将float类型数据转化为int64_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。
  由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_float2int64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscFloat2Int64

将float类型数据转化为int64_t类型，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、int64_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../../../../../runbooks/compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`exemplifies`）：runbook 记录 dav-3510 f322s64 不接受 CAST_NONE 的实际编译断言，并给出精确整数输入用 CAST_TRUNC 的已验证构建修复。
- [AscInt642Float](asc_int642float.md)（`related`）：AscInt642Float 与《AscFloat2Int64》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：AscFloat2Int64 的结果由 RINT/ROUND/FLOOR/CEIL/TRUNC 和饱和模式共同决定；模式说明是解释溢出与小数取整行为的必要契约。
- [AscFloat2int64](../../vector_compute/asc_float2int64.md)（`same_topic`）：两者都完成 float→int64 并支持舍入选择；Reg 版本增加显式 RegTensor、mask、饱和和高低 lane 控制，可用于迁移计算路径。
<!-- cannbot:related:end -->
