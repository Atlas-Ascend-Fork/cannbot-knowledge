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

- [HCCL Context简介](hccl_context_intro.md)（`related`）：“才可以调用GetHcclContext获取对应的context地址。”给出焦点端事实；“获取指定Index通信域的context（消息区）地址。”给出候选端事实。简介卡给出调用 GetHcclContext 前必须完成通信域配置的先决条件，接口卡定义按 Index 取得消息区地址的结果，构成明确的配置后取址链。
- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：获取指定Index通信域的context（消息区）地址。；配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。。HcclGroup 在原型侧声明通信域名称，GetHcclContext 在 Kernel 侧按索引取得该域的 context 地址，二者是通算融合通信域从注册到运行时访问的直接链。
- [SetHcclContext](set_hccl_context.md)（`related`）：设置通算融合算子每个通信域对应的context（消息区）地址。；获取指定Index通信域的context（消息区）地址。。Set 生产按 index 保存的消息区地址，Get 读取同一通信域地址，构成明确的写入/取回合同。
<!-- cannbot:related:end -->
