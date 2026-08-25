---
type: Guide
title: 算子适配说明
description: 自定义算子要支持融合进SuperKernel，开发流程上与普通算子并无显著差异，但需要遵循以下一系列特定约束。这些约束与具体的开启方式（npugraph_ex后端或GE图模式）无关，大部分约束与算子启动核数（block
  num）以及SuperKernel启动核数之间的关系相关，需要开发者在算子设计阶段就予以关注。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/super_kernel/operator_adaptation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子适配说明

自定义算子要支持融合进SuperKernel，开发流程上与普通算子并无显著差异，但需要遵循以下一系列特定约束。这些约束与具体的开启方式（npugraph_ex后端或GE图模式）无关，大部分约束与算子启动核数（block num）以及SuperKernel启动核数之间的关系相关，需要开发者在算子设计阶段就予以关注。
## 全核同步约束
自定义算子若进行全核同步，需注意该子Kernel启动的核数需要与SuperKernel的核数一致，通常需要启动当前硬件满核。若子Kernel启动的核数少于SuperKernel的核数，全核同步会等待所有核完成，导致卡住超时。
## MIX 1:1算子核数比例约束
若自定义算子的Kernel类型设置为KERNEL_TYPE_MIX_AIC_1_1，因为SuperKernel会根据启动核数等信息调整SuperKernel的启动比例，此时需特别注意该算子也可以适应SuperKernel的1:2启动比例，确保AIC与AIV之间的硬同步操作正确执行。比如：
- 算子内部使用了AIC与AIV之间的硬同步接口（CrossCoreSetFlag和CrossCoreWaitFlag），不要单独指定某些AIV核调用硬同步接口，要使所有AIV核均调用硬同步接口，防止因为硬同步数量不匹配而导致卡死超时。
- 使用Matmul高阶API时，算子逻辑应保证仅有一个AIV0核调用Matmul接口，防止启动两个AIV核之后出现AIV1核消息无法接收导致卡死超时。
## 标量读写与Cache一致性
在开发自定义算子时，开发者必须确保所有对GM的标量读写操作都按需正确插入DataCacheCleanAndInvalid指令。
- 在单算子编译场景下，毕昇编译器自动在算子末尾添加DataCacheCleanAndInvalid指令，刷新整个DCache（数据缓存）。
- 在SuperKernel中，子Kernel被当作普通函数处理，编译器不会自动插入该指令来确保数据缓存一致性，开发者需要自行保证，避免因容错机制改变而导致错误。
出于性能考虑，SuperKernel场景下Cache刷新机制如下：
- 如果开发者调用GlobalTensor的GetValue和SetValue接口对GM进行标量读写，在GE入图及npugraph_ex后端aclnn调用场景，SuperKernel编译时会自动在两个接口内部插入DataCacheCleanAndInvalid指令刷新单个Cache Line，保证一定的数据缓存一致性。不会在子Kernel调用前后插入DataCacheCleanAndInvalid。
- 如果开发者通过GlobalTensor的()运算符接口来获取值（读值时会插入DataCacheCleanAndInvalid指令刷新单个Cache Line保证数据缓存一致性），但通过该接口直接改写了GlobalTensor对应位置的值时，则不会自动插入DataCacheCleanAndInvalid指令，开发者需要自行保证数据缓存一致性。
