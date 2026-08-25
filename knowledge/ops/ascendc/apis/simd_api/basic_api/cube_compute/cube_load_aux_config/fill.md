---
type: API
title: Fill
description: 将L1 Buffer/L0A Buffer/L0B Buffer上的LocalTensor初始化为指定数值，通过InitConstValueParams配置迭代次数、数据块个数和填充值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/Fill.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Fill

将 L1 Buffer/L0A Buffer/L0B Buffer 上的 LocalTensor 初始化为指定数值。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：dst 为 LocalTensor（L1/L0A/L0B）；initConstValueParams 为 InitConstValueParams，字段含 repeatTimes[0,32767]迭代次数、blockNum[0,32767]每次迭代数据块个数、dstGap[0,32767]相邻迭代间隔、initValue 初始化值。L1 Buffer 每块 32B，L0A/L0B Buffer 每块 512B，dstGap 单位与块大小一致。repeatTimes 或 blockNum 为 0 时为 NOP。

模板参数 T 为 dst 数据类型，U 为初始化值类型，须与 T 一致。支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Atlas 训练/Kirin X90/9030，不支持 Vector Core。
