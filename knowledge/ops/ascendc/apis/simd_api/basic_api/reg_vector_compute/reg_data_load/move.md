---
type: API
title: Move
description: 将srcReg中的有效元素逐个复制写入dstReg对应位置，无效位置保留dstReg原值，支持传入mask参数控制有效元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/Move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Move

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

对srcReg中的有效元素逐个复制写入dstReg中对应位置处，无效位置保留dstReg原值。

如需将RegTensor复制到MaskReg。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式当前不支持。 • MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。；U: 目的操作数的RegTensor类型，例如RegTensor\ ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。

约束：该接口的mode参数不支持ZEROING模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MaskMergeMode](../aux_data_types/mask_merge_mode.md)（`same_topic`）：Move 与《MaskMergeMode》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
- [MaskReg计算](../mask_reg_compute/mask_reg_compute.md)（`same_topic`）：Move 与《MaskReg计算》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
- [Move](../mask_reg_compute/move.md)（`same_topic`）：Move 与《Move》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
<!-- cannbot:related:end -->
