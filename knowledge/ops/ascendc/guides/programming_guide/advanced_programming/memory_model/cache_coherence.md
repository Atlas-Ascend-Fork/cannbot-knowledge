---
type: Guide
title: 缓存一致性
description: 本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/memory_model/cache_coherence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 缓存一致性

本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性。
## 缓存一致性的基本概念
### Cache、Cache Line与缓存副本
Cache用于缓存后续可能重复访问的数据或指令，降低访问GM的开销。一次Cache加载通常不是只加载被访问的单个字节或单个变量，而是把该地址所在的一段连续数据作为一个整体加载到Cache中，这个整体称为Cache Line。
Cache Line是Cache加载、失效、写回的最小操作粒度。例如访问GM内存时，会将GM里一个Cache Line长度内相邻的数据加载到L2 Cache缓存，利用空间局部性提高访问效率。Cache Line是硬件真正搬入、标记、替换和写回缓存数据的最小粒度，直接影响性能和一致性。NPU架构版本2201支持L2 Cache、DCache和ICache。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid](../../../../apis/simd_api/basic_api/cache_control/data_cache_clean_and_invalid.md)（`explains`）：一致性指南解释各存储层和显式维护时机，为区分 clean、invalid 与 barrier 提供机制依据。
- [DataCachePreload](../../../../apis/simd_api/basic_api/cache_control/data_cache_preload.md)（`explains`）：DataCachePreload 与《缓存一致性》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [缓存控制](../../../../apis/simd_api/basic_api/cache_control/cache_control.md)（`explains`）：缓存控制卡说明何时预取、清理 DCache/ICache，指南补充 Cache Line 粒度以及 DCache、ICache、SIMT DCache 与 GM 的一致性机制，帮助判断应使用哪类控制操作。
- [缓存控制](../../../../apis/simd_api/c_api/cache_ctrl/cache_control.md)（`explains`）：C API 缓存控制为 C 扩展层提供同类维护原语，需按实际编程模型选择。
- [Aclnn算子工程化开发快速入门](../aclnn_operator_development/aclnn_quick_start.md)（`related`）：aclnn Host/Kernel 调用边界涉及数据生产和消费时机，一致性指南可用于判断同步和 cache 维护位置。
- [内存层级（SIMD与SIMT混合编程）](../advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`related`）：存储层级页解释 GM/L2/片上缓存的可见范围，为理解何时需要显式一致性操作提供基础。
- [单算子API调用](../aclnn_operator_development/invocation/single_operator_api_call.md)（`related`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；缓存一致性正文界定“本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
- [算子适配说明](../super_kernel/operator_adaptation.md)（`same_topic`）：算子适配说明 与《缓存一致性》的实质衔接是：SuperKernel 适配要求算子 block 数、SK_BIND、核间 flag 与缓存可见性匹配；原理、流程和 mix-mode 失败案例给出可执行约束。
<!-- cannbot:related:end -->
