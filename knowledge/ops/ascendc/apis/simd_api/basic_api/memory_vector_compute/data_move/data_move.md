---
type: API
title: 数据搬运
description: 矢量数据搬运接口集，涵盖 DataCopy、DataCopyPad、Copy 等 GM/UB 间连续、高维切分、非对齐搬运接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Memory矢量计算数据搬运

- **DataCopy（GM与UB连续数据搬运）**
- **DataCopy（GM与UB高维切分数据搬运）**
- **DataCopy（GM与UB切片数据搬运）**
- **DataCopy（GM -> UB随路转换ND2NZ搬运）**
- **DataCopy（UB -> GM随路转换NZ2ND搬运）**
- **DataCopy（GM -> UB多维数据搬运NDDMA）**
- **DataCopyPad（GM -> UB非对齐数据搬运）**
- **DataCopyPad（UB -> GM非对齐数据搬运）**
- **DataCopy（UB -> UB连续数据搬运）**
- **DataCopy（UB -> UB高维切分数据搬运）**
- **Copy（UB -> UB连续数据搬运）**
- **Copy（UB -> UB掩码式高维数据搬运）**

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_and_ub_highdim_split.md)（`related`）：DataCopy 与《数据搬运》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [DataCopy](data_copy_gm_and_ub_slice.md)（`related`）：《DataCopy》说明软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。；《数据搬运》说明矢量数据搬运接口集，涵盖 DataCopy、DataCopyPad、Copy 等 GM/UB 间连续、高维切分、非对齐搬运接口。。二者在切片DataCopy是高维分块搬运的具体重载，连续搬运和数据搬运总览用于界定它的适用边界上存在可执行的直接衔接。
- [DataCopy](data_copy_gm_to_ub_nddma.md)（`related`）：DataCopy 与《数据搬运》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [DataCopyPad](data_copy_pad_gm_to_ub.md)（`related`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《数据搬运》说明矢量数据搬运接口集，涵盖 DataCopy、DataCopyPad、Copy 等 GM/UB 间连续、高维切分、非对齐搬运接口。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [GmUbDataMove](../../data_move_guide/gm_ub_data_move.md)（`related`）：GmUbDataMove 与《数据搬运》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [Copy](copy_ub_to_ub_continuous.md)（`same_topic`）：Copy 与《数据搬运》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
<!-- cannbot:related:end -->
