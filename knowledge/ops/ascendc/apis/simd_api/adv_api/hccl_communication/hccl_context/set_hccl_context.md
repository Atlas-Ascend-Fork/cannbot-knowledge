---
type: API
title: SetHcclContext
description: 设置通算融合算子每个通信域对应的context（消息区）地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/SetHcclContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetHcclContext

设置通算融合算子每个通信域对应的context（消息区）地址。

函数原型：
template <uint32_t index>
__aicore__ inline void SetHcclContext(__gm__ uint8_t* context)

参数：
- index：模板参数，用来表示要设置的通信域ID，当前只支持2个通信域，index只能为0/1。
- context：对应通信域的context（消息区）地址。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁 与《SetHcclContext》的实质衔接是：单 rank mock 未提供真实 HCCL 参与者，SyncAll 无法闭合；HCCL context/commit/wait 和核间同步共同支持判别。
- [SetGroupName](../hccl_tiling/set_group_name.md)（`related`）：SetGroupName 与《SetHcclContext》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [GetHcclContext](get_hccl_context.md)（`same_topic`）：GetHcclContext 与《SetHcclContext》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
- [HCCL Context](hccl_context.md)（`same_topic`）：SetHcclContext 与《HCCL Context》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
- [HCCL Context简介](hccl_context_intro.md)（`same_topic`）：HCCL Context简介 与《SetHcclContext》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；SetHcclContext正文界定“设置通算融合算子每个通信域对应的context（消息区）地址”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`same_topic`）：SetHcclContext 与《HCCL使用说明》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
- [InitV2](../hccl_kernel/init_v2.md)（`same_topic`）：SetHcclContext 与《InitV2》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
<!-- cannbot:related:end -->
