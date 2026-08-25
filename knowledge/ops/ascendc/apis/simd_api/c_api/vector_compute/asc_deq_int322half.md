---
type: API
title: AscDeqInt322half
description: 对输入的int32_t类型的数据按元素做量化并转换为half类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_deq_int322half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscDeqInt322half

对输入的int32_t类型的数据按元素做量化并转换为half类型。计算公式如下： 其中的scale可通过asc_set_deq_scale设置。
函数原型：void asc_deq_int322half(__ubuf__ half* dst, __ubuf__ int32_t* src, uint32_t count)
约束：需配合asc_set_deq_scale接口的非向量模式使用，该接口用于设置量化参数。；dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDeqInt162b8](asc_deq_int162b8.md)（`related`）：int16→b8 的反量化具有不同源/目标位宽与 scale 编码，不能复用 int32→half 契约。
- [AscInt322float](asc_int322float.md)（`related`）：若目标是 fp32 应用 Int32→Float 而非经 half 反量化；目标 dtype 和 scale 需求决定选型。
- [AscSetDeqScale](asc_set_deq_scale.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；AscDeqInt322half正文说明“对输入的int32_t类型的数据按元素做量化并转换为half类型”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [SetDeqScale](../../basic_api/memory_vector_compute/type_conversion_aux_config/set_deq_scale.md)（`same_topic`）：AscDeqInt322half 需要预先设置 dequant scale；该辅助接口定义同一反量化比例契约。
<!-- cannbot:related:end -->
