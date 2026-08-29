---
type: API
title: LoadDataUnzip
description: 将GM上的数据解压并搬运到L1 Buffer（A1/B1）或L0B Buffer（B2）上。执行该API前需要执行LoadUnzipIndex加载压缩索引表。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/LoadDataUnzip.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# LoadDataUnzip

将 GM 上的压缩数据解压并搬运到 L1 Buffer（A1/B1）或 L0B Buffer（B2）。执行前须先调用 LoadUnzipIndex 加载压缩索引表到内部寄存器。

参数：dst 为 LocalTensor（TPosition A1/B1 时 32B 对齐，B2 时 512B 对齐）；src 为 GlobalTensor，数据类型与 dst 一致。仅支持 int8_t 数据类型。

仅 Atlas 推理系列产品 AI Core 支持，其他型号不支持。

<!-- cannbot:related:start -->
## 相关

- [LoadUnzipIndex](load_unzip_index.md)（`related`）：将 GM 上的压缩数据解压并搬运到 L1 Buffer（A1/B1）或 L0B Buffer（B2）。执行前须先调用 LoadUnzipIndex 加载压缩索引表到内部寄存器。；加载 GM 上的压缩索引表到内部寄存器，供 LoadDataUnzip 使用。索引表由压缩工具根据权重数据离线生成，包含压缩长度等信息。一个 LoadUnzipIndex 可加载多个索引表，每个 LoadDataUnzip 只消耗一个，索引表顺序须与压缩数据对应。。LoadDataUnzip 明确以前置 LoadUnzipIndex 为执行条件，目标接口负责加载并排序其消费的压缩索引表，二者组成索引准备后解压搬运到 L1/L0B 的有序调用链。
<!-- cannbot:related:end -->
