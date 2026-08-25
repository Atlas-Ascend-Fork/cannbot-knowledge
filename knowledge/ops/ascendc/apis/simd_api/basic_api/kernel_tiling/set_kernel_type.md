---
type: API
title: 设置Kernel类型
description: 用于用户自定义设置kernel类型，控制算子执行时只启动该类型的核，避免启动不需要工作的核，缩短核启动开销。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/set_Kernel_type.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 设置Kernel类型

用于用户自定义设置kernel类型，控制算子执行时只启动该类型的核，避免启动不需要工作的核，缩短核启动开销。

本接口组包含 Tiling模板编程，辅助接口包括 GetCoreNumAic, GetCoreNumVector。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [直调 kernel-type 裸赋值标记无效](../../../../runbooks/compilation/kernel_type.md)（`exemplifies`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《直调 kernel-type 裸赋值标记无效》补充：AscendC 直调 kernel 用文件作用域裸赋值 __enable_feature_for_compile_default = KERNEL_TYPE_*; 标记 CUBE+VEC mix 类型时编译失败；该写法只被 extract_host_stub.py 的正则匹配为文本标记，不是合法 C++ 语句，属 banned 路线。
- [设置合适的核数和算子Kernel类型](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md)（`explains`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《设置合适的核数和算子Kernel类型》补充：在算子执行过程中，可能会因为以下几个原因产生额外的启动开销或者头开销：
- [GetCoreNumAic](../../../utils_api/platform_info/platform_ascend_c/get_core_num_aic.md)（`related`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《GetCoreNumAic》补充：获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。
- [GetCoreNumVector](../../../utils_api/platform_info/platform_ascend_c/get_core_num_vector.md)（`related`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《GetCoreNumVector》补充：用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
- [SetKernelMode](../debug_interface/cpu_twin_debug/set_kernel_mode.md)（`same_topic`）：SetKernelMode 与《设置Kernel类型》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
<!-- cannbot:related:end -->
