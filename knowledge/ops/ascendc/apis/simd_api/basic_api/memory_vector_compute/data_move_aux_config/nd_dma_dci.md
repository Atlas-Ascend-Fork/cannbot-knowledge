---
type: API
title: NdDmaDci
description: 刷新NDDMA DataCache，确保多核场景下DataCopy多维搬运前缓存数据为最新状态。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/NdDmaDci.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# NdDmaDci

刷新NDDMA DataCache，确保多核场景下DataCopy多维搬运前缓存数据为最新状态。

多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN

本接口组包含 DataCopy（GMToUB多维数据搬运NDDMA）, DataCopy（GMToUB多维数据搬运NDDMA）, DataCopy（GMToUB多维数据搬运NDDMA）。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [数据搬运辅助配置接口](data_move_aux_config.md)（`related`）：NdDmaDci 配置 NDDMA 的数据压缩信息，是 DataMoveAuxConfig 下的具体搬运控制项。
- [DataCopy](../data_move/data_copy_gm_to_ub_nddma.md)（`same_topic`）：DataCopy 与《NdDmaDci》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
<!-- cannbot:related:end -->
