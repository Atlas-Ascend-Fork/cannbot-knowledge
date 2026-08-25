---
type: Guide
title: Matmul高阶API开启多核K轴错峰访问内存
description: 多核执行Matmul时开启K轴错峰访问内存，使不同核从不同起始地址访问数据，缓解地址冲突。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_k_stagger.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul高阶API开启多核K轴错峰访问内存

## 案例介绍
本案例呈现在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，开启多核K轴错峰访问Device内存对算子性能的提升效果。在多核并行执行Matmul计算时，如果输入矩阵A或B的内存位置位于GM，并且参与多核计算的矩阵相同，那么将出现多核同时访问相同GM地址的情况，导致地址访问冲突，从而影响算子性能。若开启多核K轴错峰访问Device内存，切分的矩阵K轴方向对应的不同核将尽量从不同的GM起始地址开始访问和搬运数据，缓解地址访问冲突，提升算子性能。
-   开启多核K轴错峰访问内存的适用场景：
多核执行Matmul，且输入矩阵的K轴较大。
-   开启多核K轴错峰访问内存的约束条件：
-   输入矩阵的K轴非全载，K轴非全载即矩阵的K方向数据不能同时搬入及保持在L1 Buffer中。
-   仅支持MDL模板。
-   在多核上执行Matmul计算。
-   A矩阵或B矩阵的内存位置位于GM。
本案例的算子规格如下：
算子用例规格
## 获取性能数据
使用msOpProf工具获取算子仿真流水图和上板Profiling数据，重点分析MTE2的流水。
## 分析主要瓶颈点
优化前的Profiling数据（PipeUtilization.csv）如下所示，aic_mte2_ratio平均达到0.93，MTE2在算子整体执行时长中占比较高，算子当前为MTE2 Bound。本案例中，矩阵按M和N方向切分，单核shape[singleCoreM，singleCoreN，singleCoreK]为[128, 512, 6144]，基本块shape[baseM，baseN，baseK]为[128, 256, 64]，每次加载A矩阵的数据时，多核有概率同时访问同一GM地址，引发地址冲突，导致MTE2搬运效率降低，MTE2执行耗时增加。
MTE2的搬运效率还可以通过查看其带宽利用率进行验证，如下图所示，通过分析Memory.csv，发现MTE2平均带宽利用率只有34.4%。
查看OpBasicInfo.csv文件，优化前算子整体耗时为98.72us。
## 设计优化方案
开启K轴错峰访问内存：在创建Matmul对象时，将MatmulConfig中的enableKdimReorderLoad参数设置为true。enableKdimReorderLoad参数的详细介绍请参考MatmulConfig。
开启K轴错峰访问内存的完整样例请参考K轴错峰加载数据的算子样例。开启该功能的主要步骤如下：
1.  配置MDL模板参数，将其中的enableKdimReorderLoad参数设置为true，开启多核K轴错峰访问Device内存。
2.  基于自定义的MatmulConfig模板参数，创建Matmul对象。
## 验证优化方案性能收益
算子Tiling参数不变，优化后的Profiling数据（PipeUtilization.csv）如下所示。可以看到，MTE2耗时显著降低，MTE2的平均耗时从90us降低到69.87us，最大耗时从91.94us降低到75.82us。

<!-- cannbot:related:start -->
## 相关

- [MatmulConfig](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_config.md)（`explains`）：K 轴错峰的实际开关 enableKdimReorderLoad 属于 MatmulConfig，且案例要求 MDL 模板；配置卡是将性能诊断落实到模板参数的直接接口桥梁。
- [Matmul高阶API开启多核切K](matmul_multi_core_split_k.md)（`same_topic`）：《Matmul高阶API开启多核K轴错峰访问内存》明确“多核执行Matmul时开启K轴错峰访问内存，使不同核从不同起始地址访问数据，缓解地址冲突。”；它与《Matmul高阶API开启多核切K》的“当M、N轴较小无法有效切分时，开启多核切K功能实现K轴切分，使算子多核并行执行。”在实际调用参数、数据流或结果校验上直接衔接。
- [多核对齐切分](../../simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《Matmul高阶API开启多核K轴错峰访问内存》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
<!-- cannbot:related:end -->
