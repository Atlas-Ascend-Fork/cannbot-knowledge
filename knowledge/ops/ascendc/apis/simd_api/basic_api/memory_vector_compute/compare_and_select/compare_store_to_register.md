---
type: API
title: CompareStoreToRegister
description: 逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compare_store_to_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CompareStoreToRegister

逐元素比较两个 tensor，将比较结果存储到寄存器中。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”明确 GetCmpMask 的数据来源；“逐元素比较两个 tensor，将比较结果存储到寄存器中。”明确 CompareStoreToRegister 的生产行为，二者形成同一 CmpMask 寄存器的写入与读取链。
<!-- cannbot:related:end -->
