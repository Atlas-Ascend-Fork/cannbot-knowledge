---
type: API
title: BitwiseNot接口
description: 提供BitwiseNot按位取反运算接口及其Tiling临时空间大小查询接口，包含BitwiseNot、GetBitwiseNotMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseNot_interface/BitwiseNot_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseNot接口

- **BitwiseNot**

- **GetBitwiseNotMaxMinTmpSize**

- **GetBitwiseNotTmpBufferFactorSize**

<!-- cannbot:related:start -->
## 相关

- [GetBitwiseNotMaxMinTmpSize](get_bitwise_not_max_min_tmp_size.md)（`related`）：BitwiseNot 的显式 sharedTmpBuffer 需由 MaxMin 查询得到合法范围。
- [GetBitwiseNotTmpBufferFactorSize](get_bitwise_not_tmp_buffer_factor_size.md)（`related`）：FactorSize 用 live-node/extraBuf 模型补充 BitwiseNot 固定 UB 下的 calCount 规划。
- [BitwiseNot](bitwise_not.md)（`same_topic`）：BitwiseNot 与《BitwiseNot接口》的实质衔接是：BitwiseNot kernel 与 MaxMin/factor 两种空间查询共同决定实际调用和 sharedTmpBuffer 分配。
<!-- cannbot:related:end -->
