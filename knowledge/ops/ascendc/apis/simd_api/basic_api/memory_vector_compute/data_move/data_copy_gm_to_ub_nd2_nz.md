---
type: API
title: DataCopy
description: 软仿接口，支持从GM到UB搬运过程中进行ND到NZ格式的转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMToUB_ND2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

软仿接口，支持从GM到UB搬运过程中进行ND到NZ格式的转换。

该接口为软仿接口，从易用性角度出发进行设计，支持在从Global Memory到Unified Buffer的数据搬运过程中进行ND到NZ格式的转换。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Global Memory -> Unified Buffer
    - GM -> VECIN

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。支持的数据类型请参考[数据类型](#section4219135304818)。；enableSmallC0：SmallC0模式开关：当dValue小于等于4的时候，C0_SIZE会补齐到4 * sizeof(T)字节。 默认不开启。；dst：输出 目的操作数，类型为LocalTensor。；src：输入 源操作数，类型为GlobalTensor。；intriParams：输入 搬运参数，类型为Nd2NzParams，具体参数请参考[表3](#table_nd2nz_3)。 具体定义请参考`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_data_copy.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。

约束：该接口为软仿接口，从易用性角度出发进行设计。；Nd2NzParams结构体参数的值需在取值范围内：；

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_and_ub_continuous.md)（`related`）：连续 DataCopy 保持布局不变，ND2NZ DataCopy 改变分形格式，二者给出普通连续搬入与格式转换边界。
- [DataCopy](data_copy_gm_to_ub_nddma.md)（`related`）：NDDMA 处理任意多维 stride 搬入，而 ND2NZ 接口同时完成格式转换；应按目标布局是否为 NZ 选择。
- [DataCopy](data_copy_ub_to_gm_nz2_nd.md)（`related`）：DataCopy 与《DataCopy》的实质衔接是：该软仿 DataCopy 完成 UB→GM 的 NZ2ND；NZ2ND 概念说明格式语义，GM→UB ND2NZ 是逆向软仿路径，而 L0C→GM DataCopy/Fixpipe 及其配置接口是硬件矩阵搬出的对应实现。
<!-- cannbot:related:end -->
