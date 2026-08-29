---
type: Guide
title: 避免UB的Bank冲突
description: 【描述】SIMT编程模式下，一个Warp内的多个线程可能在同一条UB访问指令中同时访问UB。对于使用UB中转做转置、重排等操作的算子，即使GM读写已经连续，仍需要分析UB访问模式，避免UB内部访问成为新的性能瓶颈。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/avoid_ub_bank_conflict_simt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 避免UB的Bank冲突

【优先级】高
【描述】SIMT编程模式下，一个Warp内的多个线程可能在同一条UB访问指令中同时访问UB。对于使用UB中转做转置、重排等操作的算子，即使GM读写已经连续，仍需要分析UB访问模式，避免UB内部访问成为新的性能瓶颈。
下图为UB bank结构示意图。Ascend 950PR/Ascend 950DT的UB划分为16个bank，并组织为8个bank group；SIMT编程模式下，每个bank进一步划分为4个subbank。若同一个Warp内多个线程在同一条UB访问指令中访问同一个bank group的相同编号subbank，硬件需要排队处理，从而形成subbank冲突并增加访问延迟。
图 1 bank结构示意图
SIMT编程方式下，bank冲突为更细粒度的subbank冲突，主要有以下两类：
- 写写冲突：多个写操作同时访问同一个bank group的相同编号subbank。
- 读读冲突：多个读操作同时访问同一个bank group的相同编号subbank。
详细的UB地址低位交织规则以及冲突场景可参考bank_conflict样例。
【样例介绍】以矩阵转置为例，输入矩阵shape为1024×1024，数据类型为float。样例采用32×32的tile。当前基础配置中，Thread Block数量固定为硬件vector core数，每个Thread Block启动1024个线程，循环处理多个32×32 tile。全局访存合并版本先用UB暂存tile，使GM读写尽量保持连续；在此基础上，避免UB Bank冲突版本通过给UB tile增加padding，调整转置读阶段的UB行跨度，减少同一个Warp内线程集中访问相同subbank资源。
【反例】矩阵转置使用UB做中转，转置读阶段产生较严重bank冲突。
上述实现通过UB中转保证了GM读写连续，这里的UB中的tile数组表示用于暂存32×32矩阵块的二维UB数组。tile数组的数据在UB中的排布为32×32。每行32个float，共128B，恰好跨越4个bank。转置写回时，同一个Warp的线程会读取UB中的一列元素，即访问tile[tx][ty]。由于行跨度固定为32个float，32个线程读取同一列时，访问地址会集中落到两个bank group的subbank 0，属于读读冲突场景。
下图展示了UB中的tile数组前12行元素按照行优先存储的排布，其中蓝色标记表示每行的第一个元素。按照地址低位交织规则，tile数组的第1行覆盖bank0到bank3，第2行覆盖bank4到bank7，第3行覆盖bank8到bank11，其余行依次类推。在32×32的UB tile中，同一个Warp的32个线程读取同一列时，会集中访问两个bank group的subbank 0。
