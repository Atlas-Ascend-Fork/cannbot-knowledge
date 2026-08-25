---
type: API
title: SetFixPipeAddr
description: DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# SetFixPipeAddr

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 Elementwise 操作时 LocalTensor 的地址。

参数：eleWiseData 为 L1 Buffer 上的源操作数（LocalTensor，TPosition A1/B1/C1，32B 对齐，仅支持 half）；c0ChStride 为 L1 Buffer 上的 C0 channel stride，单位 C0_SIZE（32B），表示沿 N 方向以 C0 为单位切分的数据块间隔。仅 Atlas 200I/500 A2 推理产品支持。
