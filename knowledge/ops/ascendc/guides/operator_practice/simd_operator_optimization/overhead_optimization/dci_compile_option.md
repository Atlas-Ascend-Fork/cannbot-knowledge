---
type: Guide
title: 设置DCI编译选项来减少算子尾开销
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 设置DCI编译选项来减少算子尾开销

>该性能优化建议适用于如下型号：
>
>- Ascend 950PR/Ascend 950DT
>

【优先级】高

【描述】算子执行结束时，需要将DCache置为无效，防止后续算子继续使用DCache中的数据而受到影响。可以通过在编译选项中添加--cce-no-dcache-flush，用于在算子尾部增加DCI（DataCacheInvalid）指令来使DCache失效。如果不开启该选项，则会默认增加DCCI（DataCacheCleanAndInvalid）指令来使DCache失效。

插入DCI指令相比于插入DCCI指令，其减少了数据从DCache同步到GM（Clean）的过程，性能上会有一定优势。插入DCCI是一种额外的容错保证，如果开发者使用了* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数时，没有正确的调用DataCacheCleanAndInvalid接口来保证Cache一致性，编译框架自动插入DCCI恰好可以保证算子精度正常。

所以在如下场景，可以通过开启该编译选项来降低算子尾部开销：

-   算子使用* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数时，正确的使用DataCacheCleanAndInvalid接口，手动将数据从DCache中回刷到GM上，保证Cache的一致性。不依赖编译框架自动插入DCCI指令来保证一致性。
-   算子不包含使用* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数的代码。

<!-- cannbot:related:start -->
## 相关

- [AscDcci](../../../../apis/simd_api/c_api/cache_ctrl/asc_dcci.md)（`explains`）：AscDcci 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [DataCacheCleanAndInvalid](../../../../apis/simd_api/basic_api/cache_control/data_cache_clean_and_invalid.md)（`explains`）：开启 --cce-no-dcache-flush 后编译器不再用尾部 DCCI 兜底，所有 *GM/SetValue 写必须自行 DataCacheCleanAndInvalid 回刷；API 卡给出该显式一致性动作。
- [asc_dci（缓存控制）](../../../../apis/simd_api/c_api/cache_ctrl/asc_dci.md)（`explains`）：指南把 DCI 缓存失效用于减少算子尾部维护开销，并说明编译选项和适用条件。
- [缓存控制](../../../../apis/simd_api/c_api/cache_ctrl/cache_control.md)（`explains`）：缓存控制 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`related`）：指南要求显式 DataCacheCleanAndInvalid，Runbook 进一步以编译器重载证明该接口必须带 LocalTensor/GlobalTensor 目标，不能臆造无参全缓存调用。
- [指令双发优化](../vector_compute/vf_optimization/dual_issue_optimization.md)（`related`）：指令双发优化 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
<!-- cannbot:related:end -->
