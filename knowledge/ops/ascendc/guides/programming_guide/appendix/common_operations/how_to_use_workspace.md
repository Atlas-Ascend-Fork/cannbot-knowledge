---
type: Guide
title: 如何使用workspace
description: workspace是设备侧Global Memory上的一块内存。workspace内存分为两部分：系统workspace和用户workspace。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/common_operations/how_to_use_workspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 如何使用workspace

workspace是设备侧Global Memory上的一块内存。workspace内存分为两部分：系统workspace和用户workspace。
-   系统workspace：Ascend C API需要预留的workspace内存
API在计算过程需要一些workspace内存作为缓存，因此算子需要为API预留workspace内存，预留内存大小通过GetLibApiWorkSpaceSize接口获取。
-   用户workspace：算子实现使用到的workspace内存
算子内部需要通过额外的device内存进行数据交换或者缓存的时候才需要分配，根据实际情况自行分配。使用场景如下：
-   需要使用Unified Buffer和L1 Buffer上的空间且空间不够用时，可以将数据暂存至workspace上。
-   调用SyncAll等API接口时，需要workspace作为入参。
-   其他需要使用Global Memory上内存空间的场景。
不同开发方式下，具体的使用方法如下：
-   工程化算子开发方式
在tiling函数中先通过GetWorkspaceSizes接口获取workspace大小的存放位置，再设置workspace的大小，框架侧会为其申请对应大小的设备侧Global Memory，在对应的算子kernel侧实现时可以使用这块workspace内存。在使用Matmul Kernel侧接口等需要系统workspace的高阶API时，设置的workspace空间大小为系统workspace和用户workspace之和。
在device侧kernel入口处的workspace为用户的workspace指针：
-   Kernel直调算子开发场景
需要使用workspace空间时，建议开启编译选项HAVE_WORKSPACE。host侧开发者仍需要自行申请workspace的空间，并传入。在使用Matmul Kernel侧接口等需要系统workspace的高阶API时，设置的workspace空间大小为系统workspace和用户workspace之和。系统workspace大小可以通过PlatformAscendCManager的GetLibApiWorkSpaceSize接口获取。开启HAVE_WORKSPACE后，开发者在kernel侧入参处获取的workspace为偏移了系统workspace后的用户workspace。

<!-- cannbot:related:start -->
## 相关

- [GetLibApiWorkSpaceSize](../../../../apis/utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)（`explains`）：workspace 指南给出 host 分配、地址下发和 kernel 使用流程，补全 GetLibApiWorkSpaceSize 只有返回字节数而没有生命周期的部分。
- [GetSysWorkSpacePtr](../../../../apis/simd_api/basic_api/resource_management/workspace/get_sys_work_space_ptr.md)（`explains`）：指南解释系统区、用户区的分配和 Host 预留流程，使 GetSysWorkSpacePtr 的来源、容量和使用者形成完整闭环。
- [GetUserWorkspace](../../../../apis/simd_api/basic_api/resource_management/workspace/get_user_workspace.md)（`explains`）：GetUserWorkspace 与《如何使用workspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [InitDetermineComputeWorkspace](../../../../apis/simd_api/basic_api/sync_control/inter_core_sync/init_determine_compute_workspace.md)（`explains`）：确定性核间同步需专用 GM workspace 并按参与核初始化。
- [SetLocalWorkspace](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_local_workspace.md)（`explains`）：Matmul local workspace 是具体消费接口。
- [SetSysWorkSpace](../../../../apis/simd_api/basic_api/resource_management/workspace/set_sys_work_space.md)（`explains`）：SetSysWorkSpace 与《如何使用workspace》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [UpdateKfcWorkspace](../../../../apis/simd_api/basic_api/cube_group_mgmt/kfc_workspace/update_kfc_workspace.md)（`explains`）：UpdateKfcWorkspace 与《如何使用workspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [Workspace](../../../../apis/simd_api/basic_api/resource_management/workspace/workspace.md)（`explains`）：指南解释系统 workspace 与用户 workspace 的分区、Host 申请和 Kernel 使用，给 Workspace 总览补充完整生命周期。
- [507035 host tiling workspace 缺 RESERVED](../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`related`）：507035 host tiling workspace 缺 RESERVED 与《如何使用workspace》的实质衔接是：REGISTER_NONE_TILING wrapper 会先预留系统 workspace，再把用户指针偏移 RESERVED_WORKSPACE；RegisterNoneTiling、Get/SetSysWorkspace、GetUserWorkspace 与指南构成同一地址契约。
- [TilingDebug](tiling_debug.md)（`related`）：workspace 大小/偏移通常由 tiling 下发，可用 tiling debug 核对。
- [如何使用Kernel侧临时空间](../../library_api/advanced_api/quick_reference/how_to_use_kernel_temp_space.md)（`related`）：Kernel 临时空间的 sharedTmpBuffer/框架预留属于片上计算暂存，workspace 指南处理跨 Kernel 或更大 GM 工作区；两者共同完成内存预算分层。
- [核函数内删除Workspace相关冗余操作](../../../operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`same_topic`）：核函数内删除Workspace相关冗余操作 与《如何使用workspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
<!-- cannbot:related:end -->
