---
type: API
title: Duplicate
description: 将标量或源寄存器最低位元素广播到目的寄存器，支持Scalar和Tensor两种模式，可配合mask使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_padding/Duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Duplicate

支持Scalar和Tensor两种模式
-   Scalar模式：将scalarValue广播到寄存器，并保存在dstReg中（如果有mask，则保存在dstReg中被mask筛选的位置）。
-   Tensor模式：将srcReg的最低位元素广播到寄存器，并保存在dstReg中被mask筛选的位置。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_duplicate_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: scalar的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。；pos: 默认为LOWEST，表示将srcReg中的最低位广播至dstReg（暂不支持其他取值）。；S: 目的操作数的RegTensor类型， 例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；srcReg(输入): 源操作数。 类型为RegTensor。

支持数据类型：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：“安装头文件的真实声明表明，寄存器到寄存器重载的模板形参依次是 `T, HighLowPart pos, MaskMergeMode mode`。”给出实际编译修复，而“参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: scalar的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。；pos: 默认为LOWEST，表示将srcReg中的最低位广播至dstReg（暂不支持其他取值）。；S: 目的操作数的RegTensor类型， 例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；srcReg(输入): 源操作数。 类型为RegTensor。”定义 Duplicate 的 pos/mode 契约；runbook 直接示范模板顺序错误及正确实例化。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：焦点卡验证“去掉 RegTensor→Duplicate 直连，并改为 `StoreAlign` 到 32B UB 标量槽、`GetValue(0)` 读回 C++ 标量、再调用标量 `Duplicate` 后，两个末轴 fp32 探针同时恢复。”，候选 API 明确“Scalar模式：将scalarValue广播到寄存器，并保存在dstReg中（如果有mask，则保存在dstReg中被mask筛选的位置）。”；修复正是强制选用这一 Scalar 广播合同。
<!-- cannbot:related:end -->
