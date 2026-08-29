---
type: API
title: GetUserTag
description: 获取指定Tensor块的Tag信息，用户可以根据Tag信息对Tensor进行不同操作。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetUserTag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetUserTag

获取指定Tensor块的Tag信息，用户可以根据Tag信息对Tensor进行不同操作。

获取指定Tensor块的Tag信息，用户可以根据Tag信息对Tensor进行不同操作。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：指定Tensor块的Tag信息。TTagType定义如下：

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [SetUserTag](set_user_tag.md)（`related`）：焦点卡负责“获取指定Tensor块的Tag信息”，候选卡明确“后续可通过GetUserTag获取指定Tensor的Tag信息”；SetUserTag 写入、GetUserTag 读取构成同一 Tensor 元信息的成对访问合同。
<!-- cannbot:related:end -->
