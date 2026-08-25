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

- [DataCopy](../../memory_vector_compute/data_move/data_copy_ub_to_gm_nz2_nd.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《DataCopy》说明软仿接口，支持从UB到GM搬运过程中进行NZ到ND格式的转换。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《FixpipeL0CToGM》说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [NZ2DN](../cube_store_key_features/nz2_dn.md)（`related`）：SetFixpipeNz2ndFlag说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。
- [NZ2ND](../cube_store_key_features/nz2_nd.md)（`related`）：“NZ2ND”定义：矩阵搬出时，NZ2ND功能即为实现NZ格式到ND格式的矩阵转换。；“SetFixpipeNz2ndFlag”定义：DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。。实质衔接：NZ2ND 是 L0C 搬出的格式转换能力；卷积 NHWC 输出复用该能力，实际 DataCopy 前需通过 Fixpipe NZ2ND 标志配置。
- [SetFixPipeConfig](set_fix_pipe_config.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《SetFixPipeConfig》说明DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [矩阵搬出关键特性说明](../cube_store_key_features/cube_store_key_features.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《矩阵搬出关键特性说明》说明矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [矩阵搬出寄存器配置说明](cube_store_aux_config.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《矩阵搬出寄存器配置说明》说明本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [AscSetL0c2gmNz2nd](../../../c_api/cube_compute/asc_set_l0c2gm_nz2nd.md)（`same_topic`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《AscSetL0c2gmNz2nd》说明数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《SetFixpipeNz2ndFlag》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [卷积格式转换](../cube_store_key_features/convolution_format_conversion.md)（`same_topic`）：焦点处理Cube 搬出阶段的 NZ/ND 格式转换；SetFixpipeNz2ndFlag正文界定“DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置”。候选给出 ND2NZ 实现、Fixpipe 开关与 NZ 分形布局，能执行并验证焦点所述格式转换。
<!-- cannbot:related:end -->
