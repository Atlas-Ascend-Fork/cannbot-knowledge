---
type: API
title: Max
description: 双目矢量计算接口，对两个输入tensor按元素取最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Max

双目矢量计算接口，按元素取最大值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = max(src0_i, src1_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：该卡证明 count-based Max 的 src1 是完整 tensor，不会自动标量广播。
- [Min](min.md)（`related`）：Max 与 Min 共享双 tensor 比较契约但选择相反极值。
- [Maxs](maxs.md)（`same_topic`）：Maxs 将第二操作数改为标量，按 tensor/tensor 或 tensor/scalar 需求选用。
<!-- cannbot:related:end -->
