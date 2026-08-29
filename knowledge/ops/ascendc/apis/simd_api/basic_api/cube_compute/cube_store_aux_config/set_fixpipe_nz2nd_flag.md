---
type: API
title: SetFixpipeNz2ndFlag
description: DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixpipeNz2ndFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFixpipeNz2ndFlag

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路 NZ2ND 格式转换时，设置格式转换配置。

参数：ndNum 为 ND 矩阵数量[1,65535]；srcNdStride 为源相邻 NZ 矩阵偏移；dstNdStride 为目的相邻 ND 矩阵偏移。a2/a3/Atlas 200I/500 A2：srcNdStride[1,512]单位 1024B（ndNum=1 时可设 0），dstNdStride[1,65535]单位 element。950：srcNdStride[0,65535]单位 C0_SIZE（ndNum=1 时可设 0），dstNdStride[1,2^32-1]单位 element。支持 950/a2/a3/Atlas 200I/500 A2/Kirin X90/9030。

<!-- cannbot:related:start -->
## 相关

- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：焦点卡规定“DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路 NZ2ND 格式转换时，设置格式转换配置。”，候选卡确认 FixpipeL0CToGM “支持随路 scalar/tensor 量化（QuantMode_t）、ReLU、NZ2ND/NZ2NZ/NZ2DN 格式转换和通道切分。”；配置接口与实际搬出载体属于同一调用链。
- [NZ2ND](../cube_store_key_features/nz2_nd.md)（`related`）：焦点卡通过“DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路 NZ2ND 格式转换时，设置格式转换配置。”定义配置入口，候选卡说明“通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。”；两卡直接闭合 NZ2ND 功能的使能与步幅参数合同。
<!-- cannbot:related:end -->
