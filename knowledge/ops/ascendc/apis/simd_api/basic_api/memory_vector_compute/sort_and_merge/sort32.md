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

- [MrgSort](mrg_sort.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《Sort32》具体提供“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [ProposalConcat](proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《Sort32》明确提供“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [RpSort16（排序与合并）](rp_sort16.md)（`related`）：Sort32 面向 score+index 的 32 元素排序，而 RpSort16 面向 8 字段 Region Proposal；二者的输入布局与后续归并链不同，可用于选型。
- [SetLoadDataRepeat](../../cube_compute/cube_load_aux_config/set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《Sort32》说明一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [AscBitsort](../../../c_api/vector_compute/asc_bitsort.md)（`same_topic`）：Sort32 与 AscBitsort 都在一次迭代中按 score 降序排列 32 个元素，并把 score/index 成对写入结果；二者是基础 API 与 C API 的同一排序合同。
- [Concat（排序操作）](../../../adv_api/sort_operations/concat.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《Concat（排序操作）》提供“对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
- [GetMrgSortResult](get_mrg_sort_result.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《GetMrgSortResult》提供“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
- [MrgSort](../../../adv_api/sort_operations/mrg_sort.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《MrgSort》提供“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
- [ProposalExtract](proposal_extract.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《ProposalExtract》提供“与ProposalConcat功能相反，从Region Proposals内将相应位置的单个元素抽取后重排，每次迭代处理16个Region Proposals，抽取16个元素后连续排列。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
- [排序与合并概述](overview.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《排序与合并概述》提供“Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
<!-- cannbot:related:end -->
