---
type: API
title: ProposalConcat
description: 将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。
  Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/ProposalConcat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ProposalConcat

将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。

将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式： 对于数据类型half，每一个Region Proposal占16Bytes，Byte[15:12]是无效数据，Byte[11:0]包含6个half类型的元素，其中Byte[11:10]定义为label，Byte[9:8]定义为score，Byte[7:6]定义为y2，Byte[5:4]定义为x2，Byte[3:2]定义为y1，Byte[1:0]定义为x1。 如下图所示，总共包含16个Region Proposals。 对于数据类型float，每

本接口属于 UB 矢量计算排序与合并接口。

支持的数据类型为 half。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：用户需保证dst中存储的proposal数目大于等于实际所需数目，否则会存在tensor越界错误。；用户需保证src中存储的元素大于等于实际所需数目，否则会存在tensor越界错误。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Atlas 推理系列产品AI Core, Atlas 训练系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ProposalExtract](proposal_extract.md)（`related`）：将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。；与ProposalConcat功能相反，从Region Proposals内将相应位置的单个元素抽取后重排，每次迭代处理16个Region Proposals，抽取16个元素后连续排列。。两个接口分别把连续元素写入 proposal 字段和从相同布局抽取字段，构成同一 Region Proposal 布局的互逆数据变换。
<!-- cannbot:related:end -->
