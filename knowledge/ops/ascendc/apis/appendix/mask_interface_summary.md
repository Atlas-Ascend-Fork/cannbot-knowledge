---
type: API
title: Mask接口汇总（附录）
description: 汇总 Atlas A2、A3 系列接口的 isSetMask 参数支持情况及 Mask 设置方式。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Mask_interface_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# Mask接口汇总（附录）

以下内容针对如下型号生效： - Atlas A3 训练系列产品/Atlas A3 推理系列产品 - Atlas A2 训练系列产品/Atlas A2 推理系列产品 本节汇总了各接口中模板参数isSetMask的支持情况。 针对Tensor前n个数计算和Tensor高维切分计算两种接口，Mask设置方式分为以下情形： - isSetMask参数情况： - 模板参数有isSetMask，支持接口外设置Mask。 - 模板参数无isSetMask，不支持接口外设置Mask。 - 模板参数有isSetMask，该参数不起作用。 - Mask设置方式： - 接口内已设置Mask：接口内部调用SetMaskCount、SetVectorMask、SetMaskNorm、ResetMask。

适用：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [基于全局掩码复用的计算性能优化](../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：Mask 支持矩阵界定哪些接口可复用全局 mask。
- [SetMaskCount](../simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_count.md)（`same_topic`）：SetMaskCount说明设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。
- [SetMaskNorm](../simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《Mask接口汇总（附录）》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
<!-- cannbot:related:end -->
