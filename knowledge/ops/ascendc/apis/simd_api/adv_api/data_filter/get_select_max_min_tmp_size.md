---
type: API
title: GetSelectMaxMinTmpSize
description: 在host侧获取Select接口申请临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/GetSelectMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSelectMaxMinTmpSize

kernel侧Select接口的计算需要开发者申请临时空间，本接口用于在host侧获取申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间申请。

函数原型：
void GetSelectMaxMinTmpSize(const AscendC::TensorShape& src0Shape, const AscendC::TensorShape& src1Shape, const uint32_t srcTypeSize, const AscendC::TensorShape& maskShape, const uint32_t maskTypeSize, const bool isReuseMask, uint32_t& maxValue, uint32_t& minValue)
void GetSelectWithBytesMaskMaxMinTmpSize(const AscendC::TensorShape& src0Shape, const AscendC::TensorShape& src1Shape, const uint32_t srcTypeSize, const AscendC::TensorShape& maskShape, const uint32_t maskTypeSize, const bool isReuseMask, uint32_t& maxValue, uint32_t& minValue)

参数：
- src0Shape（输入）：输入src0的shape信息，参数类型为AscendC::TensorShape。src0为scalar时，shape应为{1}。
- src1Shape（输入）：输入src1的shape信息，参数类型为AscendC::TensorShape。src1为scalar时，shape应为{1}。
- srcTypeSize（输入）：输入srcTensor的数据类型大小，比如数据类型为half，此处应传入2。
- maskShape（输入）：输入maskTensor的shape信息，参数类型为AscendC::TensorShape。
- maskTypeSize（输入）：输入maskTensor的数据类型大小，比如数据类型为bool，此处应传入1。

返回值：GetSelectMinTmpSize返回Select接口能完成计算所需最小临时空间大小。

<!-- cannbot:related:start -->
## 相关

- [Select dst==src 别名破坏张量输入值](../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：Runbook 记录 Select 目的与源别名破坏输入的实测，补充空间查询之外的地址重叠正确性边界。
- [Select](select.md)（`same_topic`）：该 Host 接口给出高阶 Select 执行所需 workspace 上下界，是调用 Select 前完成 Tiling 资源分配的直接配套契约。
<!-- cannbot:related:end -->
