---
type: API
title: AscStoreAlignPostupdate
description: 将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到UB，启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续调用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreAlignPostupdate

将矢量数据寄存器或掩码寄存器中的数据连续对齐搬出到Unified Buffer（UB），启用Post Update模式在搬出后自动累加目的地址指针，便于硬件循环内连续多次调用时无需手动维护目的地址。当源操作数为矢量数据寄存器时，单次搬出量为VL（256字节），支持配置掩码用于指示参与搬出的元素，掩码为1的元素写入目的地址，掩码为0的元素保留目的地址原数据。当源操作数为掩码寄存器时，单次搬出量为掩码寄存器长度（32字节），不支持配置掩码。搬运过程中数据格式与内容保持不变。本接口在Vector Function（__simd_vf__标记的函数）内使用，目的操作数为UB地址。 矢量数据寄存器搬出场景提供以下两种模式： 掩码寄存器搬出场景提供以下一种模式：
约束：非AIV调用直接返回。；本接口在Vector Function（__simd_vf__标记的函数）内调用。；dst_align32b/dst起始地址需32字节对齐，否则会报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [asc_storealign (废弃)](asc_storealign_v5_deprecated.md)（`same_topic`）：启用Post Update模式在搬出后自动累加目的地址指针；该接口已废弃，请使用asc_storealign_postupdate实现此功能。。右卡明确把废弃 asc_storealign 的连续对齐 UB 搬出迁移到左卡，左卡提供 post-update 自动推进目的地址的现行合同；两端共同决定旧调用的替代入口。
<!-- cannbot:related:end -->
