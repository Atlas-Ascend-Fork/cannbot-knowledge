---
type: API
title: 矩阵计算
description: 汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/cube_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算

汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。

本接口组包含 Matmul Kernel侧接口, Matmul Tiling类, 获取Matmul计算所需空间。

本接口属于 Cube 矩阵计算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算》说明汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [矩阵计算（ISASI）](../../basic_api/cube_compute/cube_compute_overview.md)（`related`）：高阶 Cube 入口面向 Matmul 等封装，而基础 ISASI 总览展开 GM/L1/L0A/L0B→Mmad→L0C 搬出链；在需要从高阶接口下沉定位通路或缓存约束时形成实质桥梁。
<!-- cannbot:related:end -->
