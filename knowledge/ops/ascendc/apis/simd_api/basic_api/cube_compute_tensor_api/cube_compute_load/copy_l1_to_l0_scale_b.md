---
type: API
title: CopyL1ToL0ScaleB
description: 通过Tensor API的Copy接口将L1 Buffer中的右矩阵缩放数据搬运到L0ScaleB Buffer，数据类型固定为fp8_e8m0_t。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToL0ScaleB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到L0BScale数据搬运）

通过统一Copy接口将L1 Buffer中ScaleB数据搬运到L0BScale Buffer，用于MX矩阵计算中Scale系数输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [CopyL1ToL0B](copy_l1_to_l0_b.md)（`related`）：量化 B 还需单独搬入 ScaleB，普通 L0B 不包含 scale。
- [LoadData](../../cube_compute/cube_compute_load/load_data_2_d_mx.md)（`related`）：The tensor-API Copy route makes the ScaleB half of MX movement explicit, while the focal LoadData carries right-matrix scale data in its combined interface.
- [SetTensorScaleB](../../../adv_api/cube_compute/matmul_kernel/set_tensor_scale_b.md)（`related`）：Tensor API 的 CopyL1ToL0ScaleB 说明 scaleB 在 L1 到 L0ScaleB 的物理搬运要求，补充 SetTensorScaleB 绑定后的数据通路。
- [矩阵计算输入搬运约束](../../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`related`）：CopyL1ToL0ScaleB 是 MX Matmul 的 Scale 数据搬运，输入搬运约束专门列出 Scale 通路的对齐和格式限制，可用于验证 Layout 推导结果。
<!-- cannbot:related:end -->
