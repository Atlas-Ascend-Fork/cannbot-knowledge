---
type: API
title: 更多样例（数学计算）
description: 下面的样例展示了数学库kernel侧API和Tiling API GetXxxMaxMinTmpSize的配套使用方法，具体流程如下：
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/more_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 更多样例

数学计算高阶API的配套使用样例，展示kernel侧API与Host侧Tiling API的协作流程，包含四个典型场景。

样例一：展示GetXxxMaxMinTmpSize Tiling接口与kernel侧API配套使用。Host侧通过AscendC::TensorShape描述输入shape，调用GetXxxMaxMinTmpSize获取maxValue/minValue，结合PlatformAscendC获取UB剩余空间，选取合适的tmpSize写入tiling data；kernel侧读取tiling data分配临时空间并调用高阶API（以Asin为例）。

样例二：展示PlatformAscendC::ReserveLocalMemory与kernel侧API配合使用。通过ReserveLocalMemory预留内存空间，GetCoreMemSize获取实际可用UB大小，基于此计算最大支持Shape，避免多次调用GetXxxMaxMinTmpSize。kernel侧调用不带临时空间参数的API（接口框架自动申请），执行多种数学运算。

样例三：展示GetXxxTmpBufferFactorSize Tiling接口与kernel侧API配套使用。Host侧获取maxLiveNodeCount和extraBuf，结合可用临时空间currBuff推算单次最大计算元素数量currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，取多个API推算结果的最小值，实现分块计算（以Asin+Acos链式调用为例）。

样例四：以Exp接口为例展示模板参数isReuseSource的使用。isReuseSource为false时接口内部不复用源操作数内存，srcTensor保持原值；为true时接口内部复用srcTensor内存空间存放中间结果以节省内存，但接口执行完成后srcTensor不再是原始值。该参数仅在float数据类型时生效。

<!-- cannbot:related:start -->
## 相关

- [如何使用Kernel侧临时空间](../../../../guides/programming_guide/library_api/advanced_api/quick_reference/how_to_use_kernel_temp_space.md)（`explains`）：临时空间指南系统解释 sharedTmpBuffer、框架代申请、GetXxxMaxMinTmpSize 与 factor-size 两套计算方式，正好覆盖四个样例共同采用的内存流程。
- [Exp](exp_interface/exp.md)（`related`）：样例四直接以 Exp 展示 isReuseSource=false/true 对源 Tensor 保留与复用的差异；Exp 卡给出这一模板参数和临时空间重载的完整契约。
- [GetAcosTmpBufferFactorSize](acos_interface/get_acos_tmp_buffer_factor_size.md)（`related`）：样例三需分别计算 Asin、Acos 的单次最大元素数并取较小值，目标接口提供 Acos 这一半的 factor 参数。
- [GetAsinMaxMinTmpSize](asin_interface/get_asin_max_min_tmp_size.md)（`related`）：样例一明确在 Host 侧用 GetXxxMaxMinTmpSize 为 Asin 取得 maxValue/minValue，再把选定 tmpSize 写入 TilingData；目标卡正是该 Asin 专用接口。
- [GetAsinTmpBufferFactorSize](asin_interface/get_asin_tmp_buffer_factor_size.md)（`related`）：样例三正是用 Asin 的 maxLiveNodeCount 与 extraBuf 反推 currentShapeSize；目标接口给出这两个量的定义和参数类型。
- [GetCoreMemSize](../../../utils_api/platform_info/platform_ascend_c/get_core_mem_size.md)（`related`）：样例一、二都要在预留后查询实际可用 UB，再据此选择 tmpSize 或最大 Shape；GetCoreMemSize 是该预算步骤的直接输入。
<!-- cannbot:related:end -->
