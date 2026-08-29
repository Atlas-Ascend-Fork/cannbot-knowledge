---
type: API
title: Destroy
description: 释放TPipe资源，用于重复申请释放TPipe，创建TPipe对象后可调用Destroy手动释放资源。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Destroy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Destroy

头文件路径为："basic_api/kernel_tpipe.h"。

释放资源。

约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`related`）：“该接口内部未设置PIPE_ALL同步，需要开发者自行保证同步流水正确。”揭示无全流水同步版本的责任转移；“创建tpipe对象后，可调用Destroy手动释放资源。”给出常规手动释放入口，二者用于按同步保障选择释放方式。
- [Init](init.md)（`related`）：Tpipe对象复用时，要与Destroy接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。；约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。。Init 明确规定复用前先 Destroy，Destroy 则提供手工释放资源的对应动作，两者共同定义 TPipe 重复申请释放的生命周期。
- [TPipe](t_pipe_constructor.md)（`related`）：如果需要使用多个TPipe时，请先调用Destroy接口释放前一个TPipe；创建tpipe对象后，可调用Destroy手动释放资源。构造卡明确同一时刻只能有一个 TPipe，并把再次创建前的释放指向 Destroy；Destroy 卡给出对应资源回收操作，形成直接生命周期合同。
<!-- cannbot:related:end -->
