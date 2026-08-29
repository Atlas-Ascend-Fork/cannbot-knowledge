---
type: Guide
title: 如何使用Kernel侧临时空间
description: Kernel侧接口的内部实现一般涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。除矩阵计算、HCCL通信类、卷积计算等，对于多数高阶API中临时空间的处理，开发者可以通过Kernel侧接口的入参sharedTmpBuffer传入提前申请的临时空间、通过接口框架申请临时空间两种方式。
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/advanced_api/quick_reference/how_to_use_kernel_temp_space.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 如何使用Kernel侧临时空间

Kernel侧接口的内部实现一般涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。除矩阵计算、HCCL通信类、卷积计算等，对于多数高阶API中临时空间的处理，开发者可以通过Kernel侧接口的入参sharedTmpBuffer传入提前申请的临时空间、通过接口框架申请临时空间两种方式。
-   通过sharedTmpBuffer入参传入，Kernel侧接口使用该传入的Tensor作为临时空间。该方式下，开发者可以自行管理sharedTmpBuffer内存空间，并在接口调用完成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较高。
-   接口框架申请临时空间，开发者无需在Kernel侧申请临时空间，但是需要预留临时空间的大小，即在分配内存空间时，应在可用空间大小中减去需预留的临时空间大小。
无论开发者采用上述哪种方式，在申请Tensor空间或预留临时空间时，都需要提前获取Kernel侧接口所需的临时空间大小BufferSize，为此相应类别API中提供了GetxxxMaxMinTmpSize接口，用于获取所需预留空间的大小范围，其中xxx为对应的Kernel侧接口。开发者在Host侧调用GetxxxMaxMinTmpSize接口，获取预留/申请的最大和最小临时空间的字节数，基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用。
-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
以下以Asin接口为例，示例使用AscendC::TensorShape描述输入数据的Tensor形状：
另外，多数高阶API中提供了GetxxxTmpBufferFactorSize接口，该接口用于获取maxLiveNodeCnt和extraBuf，maxLiveNodeCnt表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示Kernel侧接口所需的临时空间大小的字节数。在固定空间大小的情况下，通过maxLiveNodeCnt和extraBuf可以推算算子单次最大计算元素数量。
