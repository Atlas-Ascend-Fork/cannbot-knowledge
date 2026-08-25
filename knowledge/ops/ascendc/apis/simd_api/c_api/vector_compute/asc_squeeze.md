---
type: API
title: AscSqueeze
description: 通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscSqueeze

通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中。
函数原型：void asc_squeeze(__ubuf__ uint16_t* dst, __ubuf__ uint16_t* src0, __ubuf__ uint16_t* src1, uint8_t repeat, uint8_t dst_block_stride, uint8_t src0_block_stride, uint8_t src1_block_stride, uint8_t dst_repeat_stride, uint8_t src0_repeat_stride, uint8_t src1_repeat_stride)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscGetSqueezeStatus](../sys_var/asc_get_squeeze_status.md)（`same_topic`）：AscGetSqueezeStatus说明读取squeeze操作后保存的有效数据长度值。
- [AscSqueeze](../reg/compare_and_select/asc_squeeze.md)（`same_topic`）：AscSqueeze说明将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscSqueezeAndStoreunalign](../reg/reg_store/asc_squeeze_and_storeunalign.md)（`same_topic`）：AscSqueezeAndStoreunalign说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。
- [AscSqueezeAndStoreunalignFinalize](../reg/reg_store/asc_squeeze_and_storeunalign_finalize.md)（`same_topic`）：AscSqueezeAndStoreunalignFinalize说明配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
- [AscSqueezeAndStoreunalignInit](../reg/system_variables_access/asc_squeeze_and_storeunalign_init.md)（`same_topic`）：AscSqueezeAndStoreunalignInit说明对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [AscSqueezeV2](../reg/compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：AscSqueezeV2说明已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，搭配asc_storeunalign_postupdate可将有效数据大小保存至AR寄存器。
- [AscSqueezeWithStatus](../reg/compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：AscSqueezeWithStatus说明已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。
<!-- cannbot:related:end -->
