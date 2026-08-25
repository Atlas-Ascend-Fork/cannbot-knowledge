---
type: Guide
title: 合理配置线程数避免寄存器溢出
description: 【描述】在SIMT编程的程序中应合理配置线程数避免寄存器溢出。SIMT编程模式下，核函数通过__launch_bounds__指定的最大线程数决定每个线程可用的寄存器数量。最大线程数越大，每个线程可分配的寄存器越少，二者的对应关系如下：
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/execution_config/thread_count_register_overflow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 合理配置线程数避免寄存器溢出

【优先级】中
【描述】在SIMT编程的程序中应合理配置线程数避免寄存器溢出。SIMT编程模式下，核函数通过__launch_bounds__指定的最大线程数决定每个线程可用的寄存器数量。最大线程数越大，每个线程可分配的寄存器越少，二者的对应关系如下：
最大线程数：每个线程可用寄存器个数
1025~2048：16
513~1024：32
257~512：64
1~256：127
__launch_bounds__(N)是核函数上的可选限定符，在核函数定义时配置，用于在编译期向编译器声明执行该核函数的最大线程数为N，编译器据此确定每个线程可分配的寄存器数量。当核函数未配置__launch_bounds__时，最大线程数默认为1024，此时每个线程可使用32个寄存器。对于计算密集型算子，单个线程占用的寄存器通常较多，在默认配置下容易超出寄存器上限，超出部分的中间数据会溢出到栈空间（位于Global Memory），引入额外的Global Memory访问，导致性能下降。
避免寄存器溢出的思路是：先通过--cce-res-usage编译选项查看核函数的寄存器使用情况（Stack size大于0即表明存在溢出），再根据上表中寄存器与最大线程数的对应关系，选择一档能满足算子单线程寄存器需求的最大线程数，并通过__launch_bounds__(N)将其配置给编译器。编译器据此放宽每线程的寄存器配额，从而避免寄存器溢出，将中间数据保留在寄存器中，减少Global Memory访问，提升性能。一般建议计算密集型算子：若需多于32个寄存器（如sincos），建议配置512线程；若不超过32个，可配置1024线程。关于__launch_bounds__的详细说明，请参考SIMT BuiltIn关键字。
【样例介绍】以SinCosCompute算子为例，使用sincosf接口同时计算sin和cos结果，计算公式为 $output_sin[i] = sin(input[i])$、$output_cos[i] = cos(input[i])$。输入数据为float类型，数据规模为393216个元素，配置48个线程块、每个线程块512个线程，每个线程循环计算16个输入值。基线版本与优化版本的核函数计算逻辑完全相同，仅在是否配置__launch_bounds__上存在差异。
【反例】不配置__launch_bounds__，最大线程数取默认值1024，编译器据此分配寄存器，导致寄存器溢出。
在上述实现中，由于未配置__launch_bounds__，最大线程数取默认值1024，编译器据此为每个线程仅分配32个寄存器，而sincosf计算所需的寄存器超出该上限，超出部分溢出到栈空间。使用--cce-res-usage编译选项可查看寄存器使用情况：
其中Stack size: 32 bytes表明存在寄存器溢出（栈位于Global Memory），Used register number: 32已达到1024线程下的寄存器上限。

<!-- cannbot:related:start -->
## 相关

- [线程块数量配置优化](thread_block_config.md)（`related`）：《线程块数量配置优化》明确“SIMT算子线程块数量应结合物理核数与数据规模设置，大数据量匹配物理核数，小数据量需实测最优值。”；它与《合理配置线程数避免寄存器溢出》的“【描述】在SIMT编程的程序中应合理配置线程数避免寄存器溢出。SIMT编程模式下，核函数通过__launch_bounds__指定的最大线程数决定每个线程可用的寄存器数量。最大线程数越大，每个线程可分配的寄存器越少，二者的对应关系如下：”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
