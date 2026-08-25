---
type: API
title: NZ2NZ
description: 矩阵计算的搬出过程中NZ2NZ的核心功能体现为，矩阵计算结果搬出前后保持NZ数据排布不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/NZ2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NZ2NZ

矩阵搬出时保持 NZ 数据排布不变，不进行格式转换。通过 Fixpipe/DataCopy 的 config=CFG_NZ 或不开启 NZ2ND/NZ2DN 时默认使用。

参数：mSize/nSize 为矩阵 M/N 方向维度、srcStride 为源 NZ 矩阵不同 Z 分形列间隔（单位 C0_Size=16×sizeof(T)）、dstStride 为目的 NZ 矩阵不同 Z 分形列间隔。a2/a3：dstStride 单位为 datablock(32B)；950（FixpipeParamsArch3510）：dstStride 单位为 element。支持 a2/a3 和 950。

<!-- cannbot:related:start -->
## 相关

- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：FixpipeL0CToGM 通过 CFG_NZ 或关闭转换 flag 执行 NZ2NZ 搬出。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：L0C→UB 也可保持 NZ，并可结合双目标模式，但需满足其拆分约束。
- [NZ2DN](nz2_dn.md)（`related`）：NZ2DN 面向 DN 目标排布，是同一 L0C 搬出阶段的另一布局转换。
- [NZ2ND](nz2_nd.md)（`related`）：NZ2ND 在搬出时把分形 NZ 转为普通 ND；与保持 NZ 的 focal 是直接格式选型。
- [Transpose](../../../adv_api/tensor_transform/transpose.md)（`related`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NZ2NZ》明确提供“矩阵计算的搬出过程中NZ2NZ的核心功能体现为，矩阵计算结果搬出前后保持NZ数据排布不变。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
<!-- cannbot:related:end -->
