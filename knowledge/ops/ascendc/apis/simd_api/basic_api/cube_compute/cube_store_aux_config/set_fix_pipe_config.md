---
type: API
title: SetFixPipeConfig
description: DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFixPipeConfig

DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。有两个重载：传入 reluPre 和 quantPre 两个 tensor，或传入 preData 一个 tensor（模板 setRelu 当前仅支持 false，即只设置 quantPre）。

参数：reluPre 为 ReLU tensor（Fixpipe Buffer/C2PIPE2GM，当前保留，传空 LocalTensor）；quantPre 为 quant tensor（Fixpipe Buffer，uint64_t）；preData 为单个 tensor（当前仅支持 quant tensor）；isUnitFlag 为 bool，true 时清空 L0C Buffer 所有内存块的 unitFlag 标志位。约束：quantPre 和 reluPre 必须在 Fixpipe Buffer 上。支持 950/a2/a3/Atlas 200I/500 A2/Kirin X90/9030。
