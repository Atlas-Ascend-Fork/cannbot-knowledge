---
type: Guide
title: 整数除法的快速算法
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_optimization/instruction_optimization/fast_integer_division.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 整数除法的快速算法

【优先级】低
【描述】整数除法指令在AI处理器上相比乘法和移位，执行开销显著更高。当除数固定时，可以使用基于乘法和移位的快速除法算法，在SIMD中根据除数预计算乘法魔数magic和移位量shift，在SIMT并行计算中使用乘法和移位操作，得到与普通整数除法一致的结果，从而降低每次除法的执行开销。
【样例介绍】以uint32类型整数除法算子为例，算子功能为将输入input的每个元素除以固定除数divisor，并将结果写入输出output。样例对比在SIMT中直接使用普通除法，以及针对固定除数预计算magic和shift后使用乘法和移位替代普通除法的性能差异。完整的算子实现代码请参考SIMD与SIMT混合编程实现快速除法算子样例。
样例规格
名称：name：shape：data type：format
算子输入：input：[8388608]：uint32：ND
算子输入：divisor：标量：uint32：-
算子输出：output：[8388608]：uint32：ND
SIMT线程层次结构为：
-   Kernel启动线程块数：4096
-   单次SIMT VF调用线程数：2048
【反例】
基于SIMT的普通整数除法实现：对应样例中的场景0（SCENARIO_NUM=0）。在该场景中SIMT每个线程处理1个元素，并直接使用执行开销较高的普通除法完成计算，代码如下。
场景0和场景1采用相同的数据搬运和写回流程：每个线程块将负责处理的对应数据从GM搬运到UB，在SIMT VF中完成计算并将结果写入UB，随后在核函数中将结果从UB写回GM。两个场景的性能差异主要来自SIMT计算过程中的除法实现方式。
【正例】
基于SIMD与SIMT混合编程的快速除法实现：对应样例中的场景1（SCENARIO_NUM=1）。当除数固定时，可以在SIMD编程中预先计算所需的magic和shift，再在SIMT编程中使用乘法和移位组合运算的方式替代普通除法。
对于uint32类型整数除法，可作如下变形，将除法计算转换为乘法和移位操作：

其中 $n$ 为被除数，$d$ 为除数，$m = \frac{2^s}{d}$。$n$ 除以 $2^s$ 可通过右移 $s$ 位实现。

<!-- cannbot:related:start -->
## 相关

- [CeilDivision](../../../../apis/simd_api/basic_api/scalar_compute/ceil_division.md)（`explains`）：CeilDivision 与《整数除法的快速算法》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
- [编程示例（SIMD与SIMT混合编程）](../../../programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/programming_examples.md)（`related`）：The hybrid example shows device-side index arithmetic in a complete kernel, providing an integration point for replacing expensive integer division by the focal helper.
<!-- cannbot:related:end -->
