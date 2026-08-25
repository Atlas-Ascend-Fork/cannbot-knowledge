---
type: Guide
title: 核函数内删除Workspace相关冗余操作
description: 【描述】在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。减少这些冗余判断后，编译器可以在不使用该参数的情况下进一步优化未用到的workspace变量。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数内删除Workspace相关冗余操作

【优先级】中
【描述】在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。减少这些冗余判断后，编译器可以在不使用该参数的情况下进一步优化未用到的workspace变量。
【反例】
fast_gelu函数的参数workspace等价于用户workspace，且不为空，仍然对workspace进行判空，并且设置SetSysWorkspace和GetUserWorkspace来获取用户Workspace。
【正例】
fast_gelu函数中删除对workspace参数进行空指针判断，也无需设置SetSysWorkspace和通过GetUserWorkspace来获取Workspace。

<!-- cannbot:related:start -->
## 相关

- [GetSysWorkSpacePtr](../../../../apis/simd_api/basic_api/resource_management/workspace/get_sys_work_space_ptr.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《GetSysWorkSpacePtr》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [GetUserWorkspace](../../../../apis/simd_api/basic_api/resource_management/workspace/get_user_workspace.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《GetUserWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [InitDetermineComputeWorkspace](../../../../apis/simd_api/basic_api/sync_control/inter_core_sync/init_determine_compute_workspace.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《InitDetermineComputeWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [SetLocalWorkspace](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_local_workspace.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《SetLocalWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [SetSysWorkSpace](../../../../apis/simd_api/basic_api/resource_management/workspace/set_sys_work_space.md)（`explains`）：SetSysWorkSpace 与《核函数内删除Workspace相关冗余操作》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [SetWorkspace](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_workspace.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《SetWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [Workspace](../../../../apis/simd_api/basic_api/resource_management/workspace/workspace.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《Workspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [507035 host tiling workspace 缺 RESERVED](../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`related`）：核函数内删除Workspace相关冗余操作 与《507035 host tiling workspace 缺 RESERVED》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [Matmul workspace 预偏移 totalN 回读 banned](../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`related`）：核函数内删除Workspace相关冗余操作 与《Matmul workspace 预偏移 totalN 回读 banned》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [SIMD算子优化概述](../memory_access/avoid_ub_bank_conflict/overview.md)（`related`）：核函数内删除Workspace相关冗余操作 与《SIMD算子优化概述》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [优化建议总览表（SIMD算子优化）](../optimization_summary.md)（`related`）：核函数内删除Workspace相关冗余操作 与《优化建议总览表（SIMD算子优化）》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [避免TPipe在对象内创建和初始化](avoid_tpipe_init_in_object.md)（`related`）：移除冗余 workspace 与避免重复 TPipe 初始化都减少固定控制/分配开销，可在同一 overhead profile 验证。
- [限制TilingData结构大小](limit_tiling_data_size.md)（`related`）：精简 tiling data 与去冗余 workspace 都降低固定搬运/初始化开销。
- [如何使用workspace](../../../programming_guide/appendix/common_operations/how_to_use_workspace.md)（`same_topic`）：核函数内删除Workspace相关冗余操作 与《如何使用workspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [设置合适的核数和算子Kernel类型](core_count_kernel_type.md)（`same_topic`）：设置合适的核数和算子Kernel类型 与《核函数内删除Workspace相关冗余操作》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
<!-- cannbot:related:end -->
