---
type: API
title: AscLoadalignUpsamplePostupdate
description: 从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_upsample_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUpsamplePostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现2倍上采样搬入模式并启用Post Update，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_upsample_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscUpdateAddrReg》明确“更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [AscLoadalign](asc_loadalign.md)（`same_topic`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscLoadalign》明确“从UB中32字节对齐的起始地址搬入数据到矢量数据寄存器或掩码寄存器，支持连续、立即数偏移、地址寄存器偏移和非连续搬入四种模式。”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [AscLoadalignPostupdate](asc_loadalign_postupdate.md)（`same_topic`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscLoadalignPostupdate》明确“从UB对齐地址搬入数据到矢量数据寄存器或掩码寄存器，调用后自动更新源地址，支持立即数偏移和非连续搬入两种模式。”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
- [AscLoadalignUpsample](asc_loadalign_upsample.md)（`same_topic`）：《AscLoadalignUpsamplePostupdate》处理“从UB对齐搬入VL/2个数据并实现2倍上采样，调用后自动更新源地址。”。《AscLoadalignUpsample》明确“从UB对齐搬入VL/2个数据并实现2倍上采样，每个输入元素重复两次。”，可直接用于核对LoadAlign upsample/post-update 的搬运语义与地址寄存器推进合同。
<!-- cannbot:related:end -->
