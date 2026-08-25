---
type: API
title: DataCopyL1ToUB（L1到UB数据搬运）
description: 提供从L1 Buffer搬运数据到Unified Buffer的基础能力，数据在传输过程中保持原始格式和内容不变，支持连续和非连续的数据搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopyL1ToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# DataCopyL1ToUB（L1到UB数据搬运）

提供从 L1 Buffer 搬运数据到 Unified Buffer 的基础能力，保持原始格式和内容不变，支持连续和非连续搬运。仅 Ascend 950PR/950DT 支持。

连续搬运：DataCopyL1ToUB(dst, src, count)。非连续搬运：DataCopyL1ToUB(dst, src, repeatParams)。参数：dst/src 为 LocalTensor（均 32 字节对齐）；count 为元素个数，count×sizeof(T) 须 32 字节对齐，未对齐向下取整；repeatParams 为 DataCopyParams（blockCount[1,4095]、blockLen[1,65535]单位 DataBlock(32B)、srcGap、dstGap）。

模板参数 subBlockId 指定 Vector 核 ID，将数据搬运至对应核的 UB 地址。数据类型支持 b8、b16、b32、b64。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [L1OrL0CUbDataMove](../../data_move_guide/l1_or_l0_c_ub_data_move.md)（`same_topic`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《DataCopyL1ToUB（L1到UB数据搬运）》说明提供从L1 Buffer搬运数据到Unified Buffer的基础能力，数据在传输过程中保持原始格式和内容不变，支持连续和非连续的数据搬运。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
