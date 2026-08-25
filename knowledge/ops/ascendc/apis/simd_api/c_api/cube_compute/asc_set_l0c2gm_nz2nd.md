---
type: API
title: AscSetL0c2gmNz2nd
description: 数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_l0c2gm_nz2nd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSetL0c2gmNz2nd

数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。

参数：nd_num(输入): ND矩阵的个数，取值范围为[1, 65535]。；src_nd_stride(输入): 以分形大小为单位的源步长，源相邻NZ矩阵的偏移。取值范围为[0, 65535]，单位为32B。；dst_nd_stride(输入): 目的相邻ND矩阵的偏移。取值范围为[1,  - 1]，单位为元素。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`related`）：AscSetL0c2gmNz2nd 与《AscSetMmadDirectionN》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [DataCopy](../../basic_api/memory_vector_compute/data_move/data_copy_ub_to_gm_nz2_nd.md)（`related`）：DataCopy 与《AscSetL0c2gmNz2nd》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [AscSetL0cCopyParams](../cube_data_move/asc_set_l0c_copy_params.md)（`same_topic`）：AscSetL0c2gmNz2nd 与《AscSetL0cCopyParams》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [NZ2ND](../../basic_api/cube_compute/cube_store_key_features/nz2_nd.md)（`same_topic`）：AscSetL0c2gmNz2nd 与《NZ2ND》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [SetFixpipeNz2ndFlag](../../basic_api/cube_compute/cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`same_topic`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《AscSetL0c2gmNz2nd》说明数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
<!-- cannbot:related:end -->
