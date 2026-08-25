---
type: API
title: HCCL Context
description: 提供HCCL通信上下文管理接口，包含HCCL Context简介、SetHcclContext、GetHcclContext等方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/HCCL-Context.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# HCCL Context

提供HCCL通信上下文管理接口，包含HCCL Context简介、SetHcclContext、GetHcclContext等方法。

设置通算融合算子每个通信域对应的context（消息区）地址。

本接口组包含 SetHcclContext，辅助接口包括 GetHcclContext。

本接口属于 HCCL 集合通信接口，用于多卡间的通信操作。

约束：当前最多只支持2个通信域。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁 与《HCCL Context》的实质衔接是：单 rank mock 未提供真实 HCCL 参与者，SyncAll 无法闭合；HCCL context/commit/wait 和核间同步共同支持判别。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HCCL Context》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [GetHcclContext](get_hccl_context.md)（`same_topic`）：GetHcclContext 与《HCCL Context》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
- [HCCL Context简介](hccl_context_intro.md)（`same_topic`）：HCCL Context简介 与《HCCL Context》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [SetHcclContext](set_hccl_context.md)（`same_topic`）：SetHcclContext 与《HCCL Context》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
<!-- cannbot:related:end -->
