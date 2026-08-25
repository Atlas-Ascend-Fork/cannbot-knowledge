---
type: API
title: HCCL通信类
description: 汇总Ascend C SIMD高阶API中的HCCL集合通信接口，包含Kernel侧、Tiling侧及HCCL Context管理接口。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_communication.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# HCCL通信类

汇总Ascend C SIMD高阶API中的HCCL集合通信接口，包含Kernel侧、Tiling侧及HCCL Context管理接口。

本接口组包含 HCCL Kernel侧接口, HCCL Tiling侧接口, HCCL Context。

本接口属于 HCCL 集合通信接口，用于多卡间的通信操作。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：HCCL通信类 与《单 rank mock HCCL 致 AIC+AIV SyncAll 死锁》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL Context](hccl_context/hccl_context.md)（`related`）：HCCL通信类 与《HCCL Context》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL Context简介](hccl_context/hccl_context_intro.md)（`related`）：HCCL Context简介 与《HCCL通信类》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Kernel侧接口](hccl_kernel/hccl_kernel.md)（`related`）：HCCL通信类 与《HCCL Kernel侧接口》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL Tiling使用说明](hccl_tiling/hccl_tiling_usage.md)（`related`）：HCCL通信类 与《HCCL Tiling使用说明》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL Tiling侧接口](hccl_tiling/hccl_tiling.md)（`related`）：HCCL通信类 与《HCCL Tiling侧接口》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL使用说明](hccl_kernel/hccl_usage.md)（`related`）：HCCL通信类 与《HCCL使用说明》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HcclTilingData](hccl_tiling/tiling_data_struct.md)（`related`）：HCCL通信类 与《HcclTilingData》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
<!-- cannbot:related:end -->
