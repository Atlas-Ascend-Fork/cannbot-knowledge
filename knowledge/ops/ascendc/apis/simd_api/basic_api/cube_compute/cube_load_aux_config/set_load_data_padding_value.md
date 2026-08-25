---
type: API
title: SetLoadDataPaddingValue
description: 调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataPaddingValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetLoadDataPaddingValue

设置 LoadData（卷积数据搬运）接口的 Pad 填充值。当 LoadData 模板参数 isSetPadding 为 false 时须通过本接口设置；为 true 时本接口不生效。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：padValue 为填充值，模板类型 T 须与 LoadData 源操作数数据类型一致。支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Kirin X90/9030，不支持 Vector Core 和 Atlas 训练系列。
