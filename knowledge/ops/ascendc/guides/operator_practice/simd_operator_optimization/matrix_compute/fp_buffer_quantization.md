---
type: Guide
title: 通过FP Buffer存放量化参数实现高效随路量化
description: 【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C
  Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，数据搬运的次数更少，内存使用效率更高。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/fp_buffer_quantization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2]
---

# 通过FP Buffer存放量化参数实现高效随路量化

【优先级】高
【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，数据搬运的次数更少，内存使用效率更高。
【反例】
对矩阵乘结果进行量化计算的过程如下：
-   将矩阵乘的结果从L0C Buffer（CO1）搬运到workspace上；
-   再从workspace搬运到UB上；
-   将量化参数搬运到UB上，和矩阵乘的结果一起在UB上进行一系列量化计算；
-   将最终量化结果从UB搬运到GM上。
相比于正确示例多增加了L0C Buffer（CO1）->workspace、workspace->UB的搬运过程和量化的vector计算。
【正例】
该算子对矩阵乘的结果进行量化计算时，可将量化参数搬运到FB(Fixpipe Buffer)上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。

<!-- cannbot:related:start -->
## 相关

- [AccompanyingQuantization](../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/accompanying_quantization.md)（`explains`）：AccompanyingQuantization 定义 Fixpipe 随路量化的参数和搬出能力，指南给出把参数放入 FP Buffer 的高效实现。
- [随路量化与随路ReLU场景组合](../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`explains`）：量化与 ReLU 组合卡说明在同一次 Fixpipe 中叠加后处理时的合法配置。
- [通过BT Buffer实现高效的bias计算](bt_buffer_bias_compute.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；通过FP Buffer存放量化参数实现高效随路量化正文说明“【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到Fixpipe Buffer（C2PIPE2GM）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩阵乘的结果从L0C Buffer（CO1）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过程，”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
<!-- cannbot:related:end -->
