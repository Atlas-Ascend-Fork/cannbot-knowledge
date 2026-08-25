---
type: API
title: AscSetDeqScale
description: 设置DEQSCALE（量化参数）寄存器的值。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_deq_scale.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetDeqScale

设置DEQSCALE（量化参数）寄存器的值。
函数原型：void asc_set_deq_scale(__ubuf__ uint64_t* tmp, float scale_arr[ASC_VDEQ_SIZE], int16_t offset_arr[ASC_VDEQ_SIZE], bool sign_mode_arr[ASC_VDEQ_SIZE])
参数：tmp（输入）：一块临时内存区域，用于存储一组大小为16的量化参数。；scale_arr（输入）：float数组类型，大小为16，用于存储一组量化参数。；offset_arr（输入）：int16_t数组类型，大小为16，用于存储一组量化参数。；sign_mode_arr（输入）：bool数组类型，大小为16，用于存储一组量化参数。；scale（half）（输入）：量化参数，half类型。适用于cast_deq等接口的int32_t转化为half的场景。；scale（float）（输入）：量化参数，float类型。设置DEQSCALE寄存器的值。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [ASC_VDEQ_SIZE 未声明 — 勿直引 vector_compute.h](../../../../runbooks/compilation/asc_simd_umbrella_header_for_c_api_symbols.md)（`exemplifies`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；ASC_VDEQ_SIZE 未声明 — 勿直引 vector_compute.h正文说明“CANN 9.2.0 的 vector_compute.h 是声明源头但不是自包含用户入口；直接 include 会缺内部前置定义，改用 asc_simd.h umbrella”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [AscDeqInt162b8](asc_deq_int162b8.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；AscDeqInt162b8正文说明“将 int16_t 转换为 int8_t 或 uint8_t，并把结果写入每个 DataBlock 的高半块或低半块；调用前需通过 asc_set_deq_scale 设置量化参数”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [AscDeqInt322half](asc_deq_int322half.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；AscDeqInt322half正文说明“对输入的int32_t类型的数据按元素做量化并转换为half类型”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [AscVdeqInt162b8](asc_vdeq_int162b8.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；AscVdeqInt162b8正文说明“将 int16_t 转换为 int8_t 或 uint8_t，并把结果写入每个 DataBlock 的上半块或下半块；调用前需通过 asc_set_deq_scale 设置量化参数”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [CastDequant](../../basic_api/memory_vector_compute/composite_compute/cast_dequant.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；CastDequant正文说明“对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [SetDeqScale](../../basic_api/memory_vector_compute/type_conversion_aux_config/set_deq_scale.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；SetDeqScale正文说明“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [类型转换辅助配置接口](../../basic_api/memory_vector_compute/type_conversion_aux_config/type_conversion_aux_config.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；类型转换辅助配置接口正文说明“类型转换辅助配置接口索引页，包含SetDeqScale”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
<!-- cannbot:related:end -->
