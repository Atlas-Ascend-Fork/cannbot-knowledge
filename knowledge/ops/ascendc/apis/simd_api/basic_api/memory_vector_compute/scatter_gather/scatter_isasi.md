---
type: API
title: Scatter
description: 根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Scatter_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Scatter

按索引分散接口，根据索引 tensor 将源 tensor 元素分散写入目的 tensor。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [FP16 scatter 归约逐次回写放大相消误差](../../../../../runbooks/precision/low_precision_scatter_reduction_needs_fp32_accumulator.md)（`exemplifies`）：《FP16 scatter 归约逐次回写放大相消误差》给出“已验证边界仅为 FP16 scatter-add：逐步回写 half 会累积舍入误差，须用 FP32 中间缓冲；BF16、multiply、amin、amax 需分别验证。”；该约束/探针可直接复现、解释或前置验证《Scatter》中的“根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。”。
- [Scatter 非散射维可缩小，更新量须按 indices 计算](../../../../../runbooks/precision/scatter_update_count_must_follow_indices_shape.md)（`exemplifies`）：《Scatter 非散射维可缩小，更新量须按 indices 计算》给出“将 Scatter 的非散射维错误约束为与 data 等长会拒绝合法输入，并按 data 行数展开索引造成越界；应分离输出行数与更新行数。”；该约束/探针可直接复现、解释或前置验证《Scatter》中的“根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。”。
- [CreateVecIndex](../data_padding/create_vec_index.md)（`related`）：同一索引向量也可驱动 Scatter 写入，形成索引生产到离散存储的任务链。
- [ScatterDiscrete](../../reg_vector_compute/reg_data_store/scatter_discrete.md)（`related`）：ScatterDiscrete 与《Scatter》的实质衔接是：ScatterDiscrete 与 Gather、C/基础 Scatter 形成索引读写对偶；两张故障卡直接约束重复索引归约和 updates 形状。
- [asc_scatter](../../../c_api/reg/reg_store/asc_scatter_deprecated.md)（`related`）：asc_scatter 与《Scatter》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
- [AscScatter](../../../c_api/reg/reg_store/asc_scatter.md)（`same_topic`）：《AscScatter》明确“根据索引值index将源操作数src中的元素分散存储到目的操作数dst中。”；它与《Scatter》的“根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
