---
type: Guide
title: 算子实现（SIMD与SIMT混合算子实现）
description: 以下内容以gather & adds算子为例，介绍SIMD与SIMT混合算子的实现过程。完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样例。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_operator_impl/operator_impl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 算子实现

以下内容以gather & adds算子为例，介绍SIMD与SIMT混合算子的实现过程。完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样例。
## 算子功能
gather & adds算子从长度为100000的一维向量input中，按index指定的位置提取8192个数据，并对提取后的数据执行加1计算。算子输出output中第i个数据为：
计算过程可拆分为gather和adds两个阶段：gather阶段根据index从input中离散读取数据，并将结果写入UB；adds阶段对UB上的连续中间数据执行加1计算，计算结果原地写回UB，最后将结果数据搬运到GM上的output中。
其中，gather阶段包含索引映射和离散访问，使用SIMT表达每个线程的数据访问逻辑；adds阶段处理连续数据，使用SIMD完成向量计算。
## 算子分析
图 1  gather & adds算子整体执行流水
gather & adds算子整体执行流水如图1所示。simt_gather和simd_adds同属Vector流水，按调用顺序执行；将adds结果从UB搬出到GM属于MTE3搬出流水。由于Vector流水与MTE3搬出流水异步并行执行，MTE3搬出操作可能在Vector流水写入adds结果完成前读取UB数据，因此需在搬出前插入同步指令，确保adds结果写入UB后再启动搬出。
图 2  gather & adds算子执行流程
gather & adds算子的详细执行流程如图2所示。基于该流程，按照输入输出、核函数参数、执行配置和VF函数参数的顺序分析gather & adds算子的实现方式。
输入输出分析： gather & adds算子有两个输入input和index，输出为output。其中，input为原始数据，index表示需要从input中读取的数据位置，output保存读取并加1后的结果。
本样例中，input的数据类型为float，shape为[100000]；index的数据类型为uint32_t，shape为[8192]，取值范围为\0, 100000)；output的数据类型与input相同，shape与index相同。算子输入输出[format均为ND。
核函数名称和参数： 根据上述输入输出和执行流程，本样例中核函数命名为gather_and_adds_kernel，函数原型如下。
当前SIMD与SIMT混合编程仅使用Vector Core（AIV核），核函数可使用__vector__标识只启动AIV核。
其中，input_total_length和index_total_length分别表示input和index的长度。gather阶段需要根据index访问input，input_total_length用于校验index中保存的input访问位置是否越界，index_total_length用于校验线程访问index的位置是否越界。
执行配置： 明确SIMT线程配置和分核策略。
本例中每个SIMT线程处理1个数据，单核线程数设置为1024，即单核处理1024个数据。

<!-- cannbot:related:start -->
## 相关

- [基础知识（SIMD与SIMT混合算子实现）](basics.md)（`related`）：“SIMD编程提供了基于寄存器（Regbase）开发的Reg矢量计算API，Reg矢量计算API可以直接操作Vector Core中的SIMD寄存器，API单次处理的数据量上限等于寄存器的大小，通过GetVecLen接口获取该值。在算子实现中，需要多次调用Reg矢量计算API完成对单核数据的处理。”与“其中，gather阶段包含索引映射和离散访问，使用SIMT表达每个线程的数据访问逻辑；adds阶段处理连续数据，使用SIMD完成向量计算。”是双方正文中的具体合同。基础卡区分 SIMD 寄存器批处理与 SIMT 索引访问，实例卡把两种模式分别落到 gather 与 adds 阶段，能推进混合算子的阶段划分和实现。
<!-- cannbot:related:end -->
