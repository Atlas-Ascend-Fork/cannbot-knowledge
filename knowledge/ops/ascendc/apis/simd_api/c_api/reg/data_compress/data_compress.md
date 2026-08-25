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
