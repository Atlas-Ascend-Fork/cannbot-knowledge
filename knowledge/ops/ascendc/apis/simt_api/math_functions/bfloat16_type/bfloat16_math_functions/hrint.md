---
type: API
title: Hrint
description: 获取与输入bfloat16_t数据最接近的整数，若存在两个同样接近的整数则取偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hrint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hrint

获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。
函数原型：bfloat16_t hrint(bfloat16_t x)
返回值：与输入浮点数最接近的整数值。特别场景说明如下：本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [GetRintMaxMinTmpSize](../../../../simd_api/adv_api/math_compute/rint_interface/get_rint_max_min_tmp_size.md)（`related`）：Hrint 与《GetRintMaxMinTmpSize》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [GetRintTmpBufferFactorSize](../../../../simd_api/adv_api/math_compute/rint_interface/get_rint_tmp_buffer_factor_size.md)（`related`）：Hrint 与《GetRintTmpBufferFactorSize》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Hceil](hceil.md)（`related`）：Hrint 提供最近偶数取整，与 Hceil 的定向向上取整形成舍入模式对照。
- [Hrint](../../half_type/half_math_functions/hrint.md)（`related`）：Hrint 与《Hrint》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Htrunc](htrunc.md)（`related`）：hrint 取最近偶数，与 htrunc 的向零语义构成另一舍入选择。
- [Llrintf](../../float_math_functions/llrintf.md)（`related`）：Hrint 与《Llrintf》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Lrintf](../../float_math_functions/lrintf.md)（`related`）：Hrint 与《Lrintf》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Rintf](../../float_math_functions/rintf.md)（`related`）：Hrint 与《Rintf》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Rint接口](../../../../simd_api/adv_api/math_compute/rint_interface/rint_interface.md)（`related`）：Hrint 与《Rint接口》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [half类型数学库函数](../../half_type/half_math_functions/half_math_functions.md)（`related`）：Hrint 与《half类型数学库函数》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Hfloor](hfloor.md)（`same_topic`）：Hfloor 与《Hrint》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
- [bfloat16类型数学库函数](bfloat16_math_functions.md)（`same_topic`）：Hrint 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
<!-- cannbot:related:end -->
