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
