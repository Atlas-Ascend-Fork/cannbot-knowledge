---
type: API
title: IcpuRunKf
description: CPU调测总入口，完成CPU侧的算子程序调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/ICPU_RUN_KF.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# IcpuRunKf

CPU 调测总入口，完成 CPU 侧的算子程序调用。通过 ICPU_RUN_KF 宏调用核函数，支持 blockDim、 blockDimI 和 tiling 参数。仅 CPU 调测使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：ICPU_RUN_KF 是 CPU 调测的核函数调用总入口，把指南中的 CPU 域编译结果真正执行起来。
- [CPU孪生调试](cpu_twin_debug.md)（`related`）：IcpuRunKf 是 CPU 孪生调试的实际核函数执行入口，消费内存、tiling key 与 kernel mode 配置。
- [GmAlloc](gm_alloc.md)（`related`）：GmAlloc 与《IcpuRunKf》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [IcpuSetTilingKey](icpu_set_tiling_key.md)（`related`）：IcpuRunKf 运行 Kernel 前由 ICPU_SET_TILING_KEY 注入当前 tiling key，才能在 CPU 孪生环境走与设备一致的模板分支。
<!-- cannbot:related:end -->
