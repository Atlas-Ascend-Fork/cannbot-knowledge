---
type: API
title: SetLoadDataBoundary
description: 设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataBoundary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# SetLoadDataBoundary

设置 LoadData（卷积数据搬运）接口的 L1 Buffer（A1/B1）边界值。源操作数在 L1 Buffer 上的地址超出边界时，从起始地址开始读取（环绕）。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：boundaryValue 为边界值。LoadData v1 指令单位 32B，v2 指令单位 1B。boundaryValue=0 表示无边界，可使用整个 L1 Buffer。配合 LoadData 使用时最小值 1024，设置 1~1023 为未定义行为。LoadData 的 L1 Buffer 初始地址须在边界内。

支持 a2/a3/Atlas 推理 AI Core，不支持 950/Atlas 200I/500 A2/Atlas 训练系列。
