---
type: API
title: Rintf
description: 获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rintf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Rintf

功能：获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。

函数原型：float rintf(float x)

参数：x（输入）源操作数。

返回值：与输入浮点数最接近的整数值。特殊值：0→0；0→0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](../../../../runbooks/precision/bf16_cast_cast_rint.md)（`exemplifies`）：bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别说明AscendC Level-2 Cast 的 RoundMode 语义按方向区分：扩精度（half/bfloat16→float，位数增加无舍入）一律 CAST_NONE；缩精度（float→half/bfloat16，位数减少须舍入）才用 CAST_RINT。把 "bf16 不支持 CAST_NONE" 这条缩精度约束误用到 bf16→fp32 扩精度方向、对 bf16 扩精度取 CAST_RINT，不产生精度漂移而直接产生符号翻转/量级错误的垃圾输出。判别=同实现下 fp16 全过、bf16 全错且为 garbage（非小 diff），唯一变量是 widenMode。
- [AscRint](../../../simd_api/c_api/reg/data_type_convert/asc_rint.md)（`related`）：SIMT rintf 为单线程 float 提供相同 ties-to-even 舍入，可按 SIMD Reg 与 SIMT 标量执行模型选型。
- [Hrint](../bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《Rintf》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Rint接口](../../../simd_api/adv_api/math_compute/rint_interface/rint_interface.md)（`related`）：Rint接口说明按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。
- [Llrintf](llrintf.md)（`same_topic`）：Llrintf 与《Rintf》的实质衔接是：Llrintf 按当前 rounding mode 返回 long long；Lrintf、Rintf/Nearbyintf 和 AscRint分别对照返回宽度、异常行为和 Tensor 入口。
- [Nearbyintf](nearbyintf.md)（`same_topic`）：nearbyintf 与 rintf 都按 ties-to-even 返回最接近的浮点整数值；两卡给出的输入、返回类型和舍入规则相同。
<!-- cannbot:related:end -->
