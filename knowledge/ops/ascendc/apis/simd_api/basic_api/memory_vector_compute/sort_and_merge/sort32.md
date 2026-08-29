---
type: API
title: Sort32
description: 一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/Sort32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Sort32

一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。

Sort32接口实现一次迭代内对32个数的降序排列操作。 如下图所示，src0和src1分别表示待排序的数据score和对应RP的索引index，排序完成后以（score, index）的结构存储在dst中。 src1固定为uint32_t类型，无论src0是float还是half类型，dst中的（score, index）结构总是占据8B空间。其中： - 当src0为float类型时，dst中的index存储在高4B，score存储在低4B； - 当src0为half类型时，dst中index存储在高4B，score存储在低2B，中间的2B保留。 图1 Sort32排序示意图

本接口属于 UB 矢量计算排序与合并接口。

参数说明：T：操作数数据类型。；dst：输出 目的操作数。  类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT  LocalTensor的起始地址需要32字节对齐。；src0：输入 源操作数。  类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT  LocalTensor的起始地址需要32字节对齐。；src1：输入 源操作数。  类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT  LocalTensor的起始地址需要32字节对齐。  **注：src1的数据类型固定为uint32_t。**；repeatTime：输入 重复迭代次数。每次迭代完成32个元素的排序，下次迭代src0跳过128字节空间，src1跳过128字节空间，dst跳过256字节空间。每次迭代输入src0要求128字节对齐，src1要求128字节对齐，输出dst要求256字节对齐。repeatTime∈[0, 255]。

约束：地址对齐约束参考通用地址对齐约束。；当参数repeatTime取值为0时，该接口的行为如下：；- 针对如下型号，当参数repeatTime取值为0时，不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。；- Atlas A3 训练系列产品/Atlas A3 推理系列产品

<!-- cannbot:related:start -->
## 相关

- [MrgSort](mrg_sort.md)（`related`）：Sort32 卡说明“Sort32接口实现一次迭代内对32个数的降序排列操作。”；MrgSort 卡规定“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”，形成先局部 32 元素排序、后最多四路归并的流水线。
<!-- cannbot:related:end -->
