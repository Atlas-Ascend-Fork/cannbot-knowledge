---
type: API
title: LogicalXor接口
description: 按元素进行逻辑异或操作，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalXor_interface/LogicalXor_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# LogicalXor接口

-   **LogicalXor**

-   **GetLogicalXorMaxMinTmpSize**

-   **GetLogicalXorTmpBufferFactorSize**

<!-- cannbot:related:start -->
## 相关

- [GetLogicalXorMaxMinTmpSize](get_logical_xor_max_min_tmp_size.md)（`related`）：Host 侧 max/min 查询决定 LogicalXor Kernel 可用的临时空间。
- [GetLogicalXorTmpBufferFactorSize](get_logical_xor_tmp_buffer_factor_size.md)（`related`）：factor 查询提供另一种 LogicalXor workspace 计算方式，可按 tiling 形态选择。
- [LogicalXor](logical_xor.md)（`same_topic`）：《LogicalXor》说明按元素进行逻辑异或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。；《LogicalXor接口》说明按元素进行逻辑异或操作，并提供临时空间大小获取接口。。二者在LogicalXor执行接口必须与两个workspace查询在Host Tiling和Kernel调用间成套使用上存在可执行的直接衔接。
<!-- cannbot:related:end -->
