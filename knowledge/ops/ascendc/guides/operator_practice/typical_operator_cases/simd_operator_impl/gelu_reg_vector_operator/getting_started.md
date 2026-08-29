---
type: Guide
title: 入门功能落地
description: 本节以GELU（高斯误差线性单元）激活函数为例，介绍基于Ascend C RegBase编程模型实现向量算子的基本方法，帮助开发者快速入门Reg矢量算子开发。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/getting_started.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 入门功能落地

本节以GELU（高斯误差线性单元）激活函数为例，介绍基于Ascend C RegBase编程模型实现向量算子的基本方法，帮助开发者快速入门Reg矢量算子开发。
## 算子概述
GELU近似计算公式为：

- x：输入，shape为[256, 32]，数据类型为float；
- y：输出，shape为[256, 32]，数据类型为float；
## 算子实现
GELU算子采用RegBase编程方式实现——通过asc_vf_call调用VF函数，在寄存器中完成逐步计算。与传统MemBase（基于LocalTensor + Compute API）方式相比，RegBase允许中间计算结果暂存在寄存器而非UB中，减少了UB读写次数，适合多步骤融合计算场景。
完整的数据通路为：GM → UB → 寄存器（逐步计算）→ UB → GM。
核心计算逻辑封装在VF函数中：
完整样例代码请参见Gelu入门样例。
## 可优化方向分析
序号：可优化方向：当前实现的问题：预期优化收益
1：VF融合双发优化：VF函数内GELU计算依赖路径较长，VF融合的双发特性未充分利用，IPC较低：利用VF融合双发特性，常规计算指令并行度可达512 bytes/cycle，向量化指令耗时可减少55%以上
2：循环展开优化：VF函数内循环为简单for循环，编译器无法充分调度指令级并行：使用#pragma unroll N展开循环，提高指令发射并行度和IPC，在VF融合基础上向量指令耗时可进一步减少约4.6%
3：流水线串行执行：搬入、计算、搬出三个阶段严格串行执行，各硬件单元（MTE2/V/MTE3）无法同时工作：采用多缓冲机制，使搬入、计算、搬出可并行执行，提升硬件利用率
4：核数固定：固定使用2个核，未根据实际可用核数动态分配：动态获取可用核数，充分利用多核并行能力

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](intermediate_optimization.md)（`related`）：本节以GELU（高斯误差线性单元）激活函数为例，介绍基于Ascend C RegBase编程模型实现向量算子的基本方法，帮助开发者快速入门Reg矢量算子开发。；本节在入门功能落地的基础上，介绍GELU算子的中级性能优化方法。。入门卡提供 GELU RegBase 基线实现，中级卡明确以该功能落地为优化起点。
- [高阶极限打磨](extreme_optimization.md)（`related`）：本节以GELU（高斯误差线性单元）激活函数为例，介绍基于Ascend C RegBase编程模型实现向量算子的基本方法，帮助开发者快速入门Reg矢量算子开发。；本节在中级性能优化的基础上，介绍GELU算子的高阶极限打磨方法。。入门卡定义同一 GELU RegBase 实现对象，极限卡说明其依赖中级阶段继续打磨的进阶链。
<!-- cannbot:related:end -->
