---
type: API
title: ReduceAll
description: 对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2,
  3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0\]。 图1 ReduceAll按第一个维度计算示例
  ! 图2 ReduceAll按最后一个维度计算示例 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAll_interface/ReduceAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceAll

对多维向量按指定维度进行逻辑与归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceAllMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。

接口参数：dstTensor输出；srcTensor输入；sharedTmpBuffer临时缓存；srcShape输入shape数组；srcInnerPad指示内轴是否已补齐。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [All 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/all_950.md)（`related`）：非空 950 上，FLOAT/FLOAT16/BFLOAT16 保持原 dtype 进入 ReduceAll，DAG 先把每个元素显式正规化为 0/1；其余数值 dtype 先由 Cast 转成 BOOL。ReduceAll 最终写 BOOL；`out=UINT8` 时再做 BOOL→UINT8，`out=BOOL` 时 L0 Cast 直接返回原 Tensor。；对多维向量按指定维度进行逻辑与归约。定义指定计算维度为R轴，非指定维度为A轴。模板参数T支持half/float，pattern指定reduce模式。；算子卡的主 Device 节点就是 ReduceAll，目标补齐其轴模型、临时空间与 Kernel 调用合同。
- [GetReduceAllMaxMinTmpSize](get_reduce_all_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取ReduceAll接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetReduceAllMaxMinTmpSize获取。模板参数isReuseSource预留（传false）。。Host 查询接口产出临时空间范围，Kernel ReduceAll 重载直接消费这项大小决策。
<!-- cannbot:related:end -->
