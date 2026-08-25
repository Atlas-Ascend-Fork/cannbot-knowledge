---
type: API
title: Move
description: 将src中的元素复制到dst中，有mask时仅复制有效元素，无效元素填0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/Move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Move

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

将src中的元素复制到dst中的对应位置。如果有输入mask，则仅复制被mask选定的有效元素，无效元素填0。

如需将RegTensor复制到MaskReg。

参数：dst: 目的操作数，类型为MaskReg。；src: 源操作数，类型为MaskReg。；mask: 指示在复制过程中哪些bit有效，类型为MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Move](../reg_data_load/move.md)（`same_topic`）：Move 与《Move》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
<!-- cannbot:related:end -->
