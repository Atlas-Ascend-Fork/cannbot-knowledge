---
type: API
title: 数据压缩
description: 寄存器侧数据压缩类接口汇总，提供pack_to_low、pack_to_high、unpack、unsqueeze等数据打包与解包能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/data_compress.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据压缩

寄存器侧数据压缩接口提供数据的打包与解包能力。asc_pack_to_low/asc_pack_to_high将数据打包到低位/高位，asc_unpack执行解包，asc_unsqueeze进行维度扩展。
asc_pack已废弃，建议使用asc_pack_to_low/asc_pack_to_high替代。

<!-- cannbot:related:start -->
## 相关

- [Unsqueeze](../../../basic_api/reg_vector_compute/data_compression/unsqueeze.md)（`related`）：Unsqueeze 与《数据压缩》的实质衔接是：AscUnsqueeze 是 Unsqueeze 的 C Reg 对应入口；数据压缩说明给出它与压缩寄存器数据布局之间的使用位置，而非仅列目录成员。
- [数据压缩](../../../basic_api/reg_vector_compute/data_compression/data_compression.md)（`same_topic`）：数据压缩 与《数据压缩》的实质衔接是：C Reg 数据压缩是同一 Pack/UnPack/Unsqueeze 能力的另一入口；B16 UnPack 后必须数值 Cast 的案例揭示压缩位布局不能直接当作 FP32 数值。
<!-- cannbot:related:end -->
