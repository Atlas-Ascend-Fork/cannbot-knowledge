---
type: API
title: CPU孪生调试
description: CPU 孪生调试接口集，包含 GmAlloc、ICPU_RUN_KF、ICPU_SET_TILING_KEY、SetKernelMode 等。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/cpu_twin_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CPU孪生调试

CPU 孪生调试接口集合，用于在 CPU 侧模拟核函数执行以验证逻辑正确性。GmAlloc/GmFree 管理 GM 内存，ICPU_RUN_KF 触发核函数运行，ICPU_SET_TILING_KEY 设置 tiling key，SetKernelMode 设置核运行模式。该方式不依赖真实硬件，适合早期逻辑调试与快速迭代。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：指南说明 CPU 孪生方法与限制，接口集给出 GmAlloc、ICPU_RUN_KF、tilingKey 和 KernelMode 等实际控制入口。
- [IcpuRunKf](icpu_run_kf.md)（`related`）：IcpuRunKf 是 CPU 孪生调试的实际核函数执行入口，消费内存、tiling key 与 kernel mode 配置。
- [GmAlloc](gm_alloc.md)（`same_topic`）：GmAlloc 与《CPU孪生调试》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [IcpuSetTilingKey](icpu_set_tiling_key.md)（`same_topic`）：IcpuSetTilingKey 与《CPU孪生调试》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [SetKernelMode](set_kernel_mode.md)（`same_topic`）：SetKernelMode 与《CPU孪生调试》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
<!-- cannbot:related:end -->
