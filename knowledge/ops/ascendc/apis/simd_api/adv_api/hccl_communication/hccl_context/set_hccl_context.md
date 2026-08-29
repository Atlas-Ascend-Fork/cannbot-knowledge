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

- [GetHcclContext](get_hccl_context.md)（`related`）：设置通算融合算子每个通信域对应的context（消息区）地址。；获取指定Index通信域的context（消息区）地址。。Set 生产按 index 保存的消息区地址，Get 读取同一通信域地址，构成明确的写入/取回合同。
<!-- cannbot:related:end -->
