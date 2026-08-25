---
type: API
title: Sqrt
description: 根据mask对源操作数srcReg逐元素做平方根运算，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Sqrt

该接口根据mask，对源操作数srcReg逐元素做平方根运算，将结果写入目的操作数dstReg。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: 可配置为MaskMergeMode枚举类型的枚举或SqrtSpecificMode的结构体指针。 • MaskMergeMode，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。 • SqrtSpecificMode，定义如下： enum class SqrtAlgo { INTRINSIC = 0, FAST_INVERSE, PRECISION_1ULP_FTZ_TRUE, PRECISION_0ULP_FTZ_FALSE, PRECISION_1ULP_FTZ_FALSE, }; struct SqrtSpecificMode { MaskMergeMode mrgMode = MaskMergeMode::ZEROING, bool precisionMode = false; SqrtAlgo algo = SqrtAlgo::INTRINSIC; }; • mrgMode：选择MERGING模式或ZEROING模式。 • precisionMode：用于配置精度模式。当precisionMode为true时，使能更高精度的Sqrt计算，使用快速求逆算法得出结果。该算法目前只针对float数据类型生效。 • algo：用于配置Subnormal模式，具体参考关键特性说明。 • SqrtAlgo::INTRINSIC、SqrtAlgo::PRECISION_1ULP_FTZ_TRUE，使用单指令计算得出结果，最大精度误差为1ulp。 • SqrtAlgo::FAST_INVERSE、SqrtAlgo::PRECISION_0ULP_FTZ_FALSE，使用快速求逆算法得出结果。目前，该算法仅支持float数据类型，并在该模式下支持Subnormal数据计算。 • SqrtAlgo::PRECISION_1ULP_FTZ_FALSE，最大精度误差为1ulp。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：half、float。

约束：- 输入为负数时结果为nan。
- 输入为-0时结果为-0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：该 runbook 记录 device 侧 sqrtf 被 Bisheng 拒绝时改用向量 Sqrt，直接展示接口路线替换。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：Rsqrt 快速近似精度不足时以 Sqrt 后取倒数替代，说明 Sqrt 精度模式在验证链中的作用。
- [Sqrt](../../memory_vector_compute/basic_arithmetic/sqrt.md)（`related`）：Memory 矢量 Sqrt 与 Reg Sqrt 实现相同逐元素数学操作，但前者以 LocalTensor/count 工作，适用于不同执行路径选型。
- [sqrt（数学函数）](../../../../utils_api/cpp_stdlib/math_functions/sqrt.md)（`related`）：Sqrt说明根据mask对源操作数srcReg逐元素做平方根运算，将结果写入目的操作数dstReg。
- [AscSqrt](../../../c_api/reg/arithmetic_compute/asc_sqrt.md)（`same_topic`）：AscSqrt 与《Sqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
<!-- cannbot:related:end -->
