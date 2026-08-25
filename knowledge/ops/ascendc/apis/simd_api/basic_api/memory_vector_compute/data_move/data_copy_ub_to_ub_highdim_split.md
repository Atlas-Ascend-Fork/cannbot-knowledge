---
type: API
title: DataCopy
description: 支持UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_UBToUB_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

支持UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。

支持Unified Buffer与Unified Buffer之间的高维切分数据搬运，数据在传输过程中保持原始格式和内容不变。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Unified Buffer - VECIN -> VECCALC - VECCALC -> VECOUT 高维切分数据搬运可通过配置数据块个数、单个数据块长度、地址偏移等搬运参数，同时支持非连续和连续的数据搬运。

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Unified Buffer
    - VECIN -> VECCALC
    - VECCALC -> VECOUT

高维切分数据搬运可通过配置数据块个数、单个数据块长度、地址偏移等搬运参数，同时支持非连续和连续的数据搬运。


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：操作数的数据类型。支持的数据类型请参考[数据类型](#section4219135304818)。；dst：输出 目的操作数，类型为LocalTensor，存储位置为Unified Buffer，目的地址需要32字节对齐。；src：输入 源操作数，类型为LocalTensor，存储位置为Unified Buffer，源地址需要32字节对齐。；repeatParams：输入 搬运参数，DataCopyParams类型，参数说明请参考表3。通过该参数可配置搬运的数据块大小、个数、间隔等信息，同时支持非连续和连续搬运。 具体定义请参考`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_data_copy.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。；blockCount：搬运的数据块个数，数据类型为uint16_t，取值范围：blockCount∈[0, 4095]，默认值为1。

约束：位于Unified Buffer的地址必须32字节对齐。；当DataCopyParams结构体参数blockCount、blockLen任意一个值为0时，该接口将被视为NOP（空操作）。该说明针对如下型号生效：；- Atlas A3 训练系列产品/Atlas A3 推理系列产品；- Atlas A2 训练系列产品/Atlas A2 推理系列产品

<!-- cannbot:related:start -->
## 相关

- [Copy](copy_ub_to_ub_mask_highdim_split.md)（`related`）：Copy 的 mask 高维切分适合按元素有效位搬运，DataCopy 版本则以块和 stride 描述搬运。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_ub_to_l1_highdim_split.md)（`related`）：《DataCopy》明确“支持UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。”；它与《DataCopy》的“将矩阵从Unified Buffer搬运至L1 Buffer，支持非连续搬运和连续搬运，数据搬运时格式和内容保持不变。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopy](data_copy_gm_and_ub_highdim_split.md)（`related`）：GM-UB 高维切分使用相同 blockCount、blockLen 与 stride 模型，但跨存储层并受 MTE 路径约束。
- [DataCopy](data_copy_ub_to_ub_continuous.md)（`related`）：《DataCopy》说明支持UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。；《DataCopy》说明支持UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。。二者在两页分别给出UB到UB连续Copy与高维切分DataCopy，直接决定连续布局和切分布局下的接口选择上存在可执行的直接衔接。
<!-- cannbot:related:end -->
