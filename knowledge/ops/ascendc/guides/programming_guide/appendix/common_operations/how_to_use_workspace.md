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
