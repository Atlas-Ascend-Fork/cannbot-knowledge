---
type: API
title: Min
description: 双目矢量计算接口，对两个输入tensor按元素取最小值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Min

双目矢量计算接口，按元素取最小值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = min(src0_i, src1_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：该卡证明 Min 的双 tensor count 版本不会自动标量广播。
- [AscMin](../../../c_api/reg/arithmetic_compute/asc_min.md)（`related`）：AscMin 与《Min》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
- [Max](max.md)（`related`）：Max 与 Min 共享双 tensor 比较契约但选择相反极值。
- [AscMin](../../../c_api/vector_compute/asc_min.md)（`same_topic`）：AscMin 与《Min》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [Min](../../reg_vector_compute/basic_arithmetic/min.md)（`same_topic`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Min》说明双目矢量计算接口，对两个输入tensor按元素取最小值。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [Mins](mins.md)（`same_topic`）：Mins 与《Min》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [min（整数数学函数）](../../../../simt_api/math_functions/integer_math_functions/min.md)（`same_topic`）：min（整数数学函数） 与《Min》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
<!-- cannbot:related:end -->
