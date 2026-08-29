---
type: API
title: PipeBarrier
description: 完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# PipeBarrier

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

如下图1所示，完成同一流水线内的同步控制，用于在同一流水线内部约束执行顺序。其作用是，保证前序指令中所有数据的读写工作全部完成，后序指令才能执行。

参数：pipe: 模板参数，表示阻塞的流水类别。 支持的流水参考硬件流水类型，其中不支持PIPE_S。 如果不关注流水类别，希望阻塞所有流水，可以传入PIPE_ALL。

约束：- Scalar流水之间的同步由硬件自动保证，PipeBarrier接口不支持PIPE_S单流水的同步。

- PipeBarrier()会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅阻塞单条流水线即可解决问题，应避免随意调用PipeBarrier()。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
