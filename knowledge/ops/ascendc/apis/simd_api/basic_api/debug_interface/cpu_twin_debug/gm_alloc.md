---
type: API
title: GmAlloc
description: CPU侧运行验证时创建共享内存，在/tmp目录下创建共享文件并返回映射指针。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/GmAlloc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GmAlloc

CPU 侧运行验证时创建共享内存，在 /tmp 目录下创建共享文件并返回映射指针。参数 bufferSize 为申请的内存大小（字节）。仅 CPU 调测使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：GmAlloc 与《CPU域孪生调试（功能调试）》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [IcpuRunKf](icpu_run_kf.md)（`related`）：GmAlloc 与《IcpuRunKf》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [CPU孪生调试](cpu_twin_debug.md)（`same_topic`）：GmAlloc 与《CPU孪生调试》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [GmFree](gm_free.md)（`same_topic`）：GmAlloc 与《GmFree》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
<!-- cannbot:related:end -->
