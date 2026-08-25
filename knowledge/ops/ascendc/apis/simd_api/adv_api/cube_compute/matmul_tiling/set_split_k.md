---
type: API
title: SetSplitK
description: EnableMultiCoreSplitK接口功能与该接口相同，建议使用EnableMultiCoreSplitK。 多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSplitK.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetSplitK

EnableMultiCoreSplitK接口功能与该接口相同，建议使用EnableMultiCoreSplitK。 多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。

函数原型：void SetSplitK(bool flag)

参数：
- flag（输入）：是否开启切K轴。 true：开启切K轴 false：不开启切K轴

约束：
- 如果在算子中使用该接口，获取C矩阵结果时仅支持输出到Global Memory。
- 如果在算子中使用该接口，需在Kernel侧代码中首次将C矩阵分片的结果写入Global Memory之前，先清零Global Memory，随后在获取C矩阵分片的结果时，再开启AtomicAdd累加。如果不预先清零Global Memory，可能会因为累加Global Memory中原始的无效数据而产生精度问题。

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](../../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/matmul_atomic_add.md)（`explains`）：SetSplitK 与《Matmul开启AtomicAdd选项》的实质衔接是：SplitK 必须与 multi-core split、split range、single range/shape、core 数和 AtomicAdd 汇合配置一致。
- [Matmul高阶API开启多核切K](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md)（`explains`）：SetSplitK 与《Matmul高阶API开启多核切K》的实质衔接是：SplitK 必须与 multi-core split、split range、single range/shape、core 数和 AtomicAdd 汇合配置一致。
- [EnableMultiCoreSplitK](enable_multi_core_split_k.md)（`same_topic`）：SetSplitK 与《EnableMultiCoreSplitK》的实质衔接是：SplitK 必须与 multi-core split、split range、single range/shape、core 数和 AtomicAdd 汇合配置一致。
<!-- cannbot:related:end -->
