---
type: API
title: DataCopy
description: 软仿接口，支持从UB到GM搬运过程中进行NZ到ND格式的转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_UBToGM_NZ2ND.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

软仿接口，支持从UB到GM搬运过程中进行NZ到ND格式的转换。

该接口为软仿接口，从易用性角度出发进行设计，支持在从Unified Buffer到Global Memory的数据搬运过程中进行NZ到ND格式的转换。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECOUT -> GM - CO2 -> GM（仅Atlas 推理系列产品AI Core支持）

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Global Memory
    - VECOUT -> GM

    - CO2 -> GM（仅Atlas 推理系列产品AI Core支持）


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。支持的数据类型请参考[数据类型](#section4219135304818)。；dst：输出 目的操作数，类型为GlobalTensor。；src：输入 源操作数，类型为LocalTensor。；intriParams：输入 搬运参数，类型为Nz2NdParamsFull，具体参数请参考[表3](#table_nz2nd_3)。 具体定义请参考`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_data_copy.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。；ndNum：传输NZ矩阵的数目，取值范围：ndNum∈[0, 4095]。

约束：该接口为软仿接口，从易用性角度出发进行设计。；Nz2NdParamsFull结构体参数的值需在取值范围内：；

<!-- cannbot:related:start -->
## 相关

- [AscSetL0c2gmNz2nd](../../../c_api/cube_compute/asc_set_l0c2gm_nz2nd.md)（`related`）：DataCopy 与《AscSetL0c2gmNz2nd》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [DataCopy](data_copy_gm_to_ub_nd2_nz.md)（`related`）：DataCopy 与《DataCopy》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [DataCopyL0CToGM](../../cube_compute/cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：DataCopy 与《DataCopyL0CToGM》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [FixpipeL0CToGM](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：DataCopy 与《FixpipeL0CToGM》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
- [SetFixpipeNz2ndFlag](../../cube_compute/cube_store_aux_config/set_fixpipe_nz2nd_flag.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《DataCopy》说明软仿接口，支持从UB到GM搬运过程中进行NZ到ND格式的转换。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [NZ2ND](../../cube_compute/cube_store_key_features/nz2_nd.md)（`same_topic`）：DataCopy 与《NZ2ND》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
<!-- cannbot:related:end -->
