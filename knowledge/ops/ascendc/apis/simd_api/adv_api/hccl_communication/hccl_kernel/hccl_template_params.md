---
type: API
title: HCCL模板参数
description: 创建HCCL对象时需要传入模板参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/HCCL_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL模板参数

创建HCCL对象时需要传入模板参数。

函数原型：template <HcclServerType serverType = HcclServerType::HCCL_SERVER_TYPE_AICPU, const auto& config = DEFAULT_CFG>

参数：
- serverType：支持的服务端类型。HcclServerType枚举类型，取值如下。/HCCL_SERVER_TYPE_AICPU：AI CPU服务端。/HCCL_SERVER_TYPE_CCU：CCU服务端。/HCCL_SERVER_TYPE_END：预留参数，不支持使用。
- config：用于指定向服务端下发任务的核。HcclServerConfig类型，定义如下代码所示，含义如下。 type：向服务端下发任务的核的类型。CoreType类型，可取值为：DEFAULT：表示不指定AIC核或者AIV核。/ON_AIV：表示指定为AIV核。/ON_AIC：表示指定为AIC核。 blockId：向服务端下发任务的核的ID。 默认值DEFAULT_CFG = {CoreType::DEFAULT, 0}。
支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
