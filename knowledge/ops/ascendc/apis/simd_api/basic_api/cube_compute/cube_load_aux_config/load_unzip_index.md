---
type: API
title: LoadUnzipIndex
description: 加载GM上的压缩索引表到内部寄存器。 索引表包含LoadDataUnzip所需的压缩信息，例如压缩长度等，用于获取压缩后的数据。 索引表由压缩工具根据对应的权重数据离线生成。一个LoadUnzipIndex指令可以加载多个索引表，而每个LoadDataUnzip指令只能消耗一个索引表。因此，索引表之间的顺序应该由用户来确定，以确保其与压缩数据的对应性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/LoadUnzipIndex.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# LoadUnzipIndex

加载 GM 上的压缩索引表到内部寄存器，供 LoadDataUnzip 使用。索引表由压缩工具根据权重数据离线生成，包含压缩长度等信息。一个 LoadUnzipIndex 可加载多个索引表，每个 LoadDataUnzip 只消耗一个，索引表顺序须与压缩数据对应。

参数：src 为 GlobalTensor（索引表地址，2B 对齐，长度须 512B 整数倍，最大 32KB）；numOfIndexTabEntry 为加载的索引表个数（须大于 0）。模板参数 T 须为 int8_t。

仅 Atlas 推理系列产品 AI Core 支持。
