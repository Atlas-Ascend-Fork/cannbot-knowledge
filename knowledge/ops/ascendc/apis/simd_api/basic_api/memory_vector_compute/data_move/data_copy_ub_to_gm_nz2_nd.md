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

- [DataCopy](data_copy_gm_to_ub_nd2_nz.md)（`same_topic`）：该接口为软仿接口，从易用性角度出发进行设计，支持在从Global Memory到Unified Buffer的数据搬运过程中进行ND到NZ格式的转换。；该接口为软仿接口，从易用性角度出发进行设计，支持在从Unified Buffer到Global Memory的数据搬运过程中进行NZ到ND格式的转换。。两端是 GM/UB 之间成对的 ND→NZ 搬入与 NZ→ND 搬出，联合阅读可闭合转换后的片上矩阵往返数据路径。
<!-- cannbot:related:end -->
