---
type: API
title: GetHcclContext
description: 获取指定Index通信域的context（消息区）地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/GetHcclContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetHcclContext

获取指定Index通信域的context（消息区）地址。

函数原型：
template <uint32_t index>
__aicore__ inline __gm__ uint8_t* __gm__ GetHcclContext(void)

参数：
- index：模板参数，用来表示要设置的通信域ID，当前只支持2个通信域，index只能为0/1。
返回值：指定通信域的context（消息区）地址。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：Kernel 根据组配置取得 HCCL context；组名错误会在这一消费端暴露。
- [InitV2](../hccl_kernel/init_v2.md)（`related`）：InitV2 的 context 参数来自 GetHcclContext，包含 rankDim/rankID 等通信上下文。
- [SetGroupName](../hccl_tiling/set_group_name.md)（`related`）：SetGroupName 与《GetHcclContext》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [HCCL Context](hccl_context.md)（`same_topic`）：GetHcclContext 与《HCCL Context》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
- [HCCL Context简介](hccl_context_intro.md)（`same_topic`）：HCCL Context简介 与《GetHcclContext》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；GetHcclContext正文界定“获取指定Index通信域的context（消息区）地址”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`same_topic`）：GetHcclContext 与《HCCL使用说明》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
- [SetHcclContext](set_hccl_context.md)（`same_topic`）：GetHcclContext 与《SetHcclContext》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
<!-- cannbot:related:end -->
