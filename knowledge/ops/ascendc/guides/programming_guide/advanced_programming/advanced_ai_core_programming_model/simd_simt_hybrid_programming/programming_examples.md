---
type: Guide
title: 编程示例（SIMD与SIMT混合编程）
description: 本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/programming_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 编程示例

本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。
## 场景说明
样例从长度为100000的一维输入input中，按照index数组指定的位置离散读取8192个元素，并对读取结果执行加1操作：
其中，离散读取input[index[i]]适合使用SIMT线程并行完成；加1操作面向连续UB数据，适合使用SIMD向量计算完成。
数据：Shape：数据类型：说明
input：[100000]：float：被离散读取的输入数据
index：[8192]：uint32_t：每个输出元素对应的input下标
output：[8192]：float：gather后加1的输出结果
样例启动8个Vector Core，每个Vector Core处理1024个输出元素。每个核内通过asc_vf_call启动一个SIMT VF函数，dim3(THREAD_COUNT)配置1024个SIMT线程，每个线程负责一个index元素。
## 定义SIMT VF函数
SIMT VF函数使用__simt_vf__修饰，函数内可以使用blockIdx、blockDim、threadIdx等SIMT内置变量。下面代码中，每个线程根据自己的threadIdx.x读取一个index，再从GM输入input中读取对应数据并写入UB缓存local_output。
关键点如下：
-   __simt_vf__标识该函数在SIMT单元执行。
-   __launch_bounds__(THREAD_COUNT)声明该SIMT VF函数的最大线程数。
-   __gm__用于标识GM指针，__ubuf__用于标识UB指针。
-   threadIdx.x表示当前线程在线程块内的索引，用于让不同线程处理不同元素。
## 调用VF函数
在__global__ __vector__核函数中，申请UB空间作为共享内存，再通过asc_vf_call调用SIMT VF函数完成gather计算，而后通过asc_vf_call调用SIMD VF函数执行后续的加法计算。在调用SIMT VF函数时，asc_vf_call的第一个参数dim3(THREAD_COUNT)表示本次SIMT VF调用启动1024个线程。
asc_vf_call调用后，当前Vector Core内会启动一个SIMT线程块。以本样例为例，index_total_length_per_block为1024，THREAD_COUNT也为1024，因此一个线程块即可处理当前核负责的全部输出元素。
## 配置核函数启动
Host侧通过>>内核调用符启动__global__ __vector__核函数。下面代码中，num_blocks表示启动8个Vector Core，dyn_ub_size表示动态UB大小，本样例取值为THREAD_COUNT * sizeof(float)，stream用于维护异步执行顺序。

<!-- cannbot:related:start -->
## 相关

- [扩展语法内置变量](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：扩展语法内置变量 与《编程示例（SIMD与SIMT混合编程）》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [SIMD与SIMT混合编程概述](overview.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“SIMD与SIMT混合编程概述”定义：为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《编程示例（SIMD与SIMT混合编程）》明确“本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [内存层级（SIMD与SIMT混合编程）](memory_hierarchy.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“内存层级（SIMD与SIMT混合编程）”定义：在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量最小，访问效率最高。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
- [整数除法的快速算法](../../../../operator_practice/simd_simt_hybrid_optimization/instruction_optimization/fast_integer_division.md)（`related`）：The hybrid example shows device-side index arithmetic in a complete kernel, providing an integration point for replacing expensive integer division by the focal helper.
- [核函数与VF函数（SIMD与SIMT混合编程）](kernel_and_vf_functions.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“核函数与VF函数（SIMD与SIMT混合编程）”定义：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
- [算子实现（SIMD与SIMT混合算子实现）](../../../../operator_practice/simd_simt_hybrid_operator_impl/operator_impl.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“算子实现（SIMD与SIMT混合算子实现）”定义：以下内容以gather & adds算子为例，介绍SIMD与SIMT混合算子的实现过程。完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样例。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
<!-- cannbot:related:end -->
