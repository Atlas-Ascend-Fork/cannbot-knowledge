---
type: API
title: DataCopy
description: 多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMToUB_NDDMA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# DataCopy

多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。

多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Global Memory -> Unified Buffer
    - GM -> VECIN


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。；dim：搬运的数据维度，数据类型为uint8_t，支持的维度为[1, 5]。；config：搬运配置选项，NdDmaConfig类型，定义如下，具体参数说明请参考[表3](#table_nddma_3)。 struct NdDmaConfig {     static constexpr uint16_t unsetPad = 0xffff;     bool isNearestValueMode = false;     uint16_t loopLpSize = unsetPad; // Left padding size of all dimensions, must be less than 256.     uint16_t loopRpSize = unsetPad; // Right padding size of all dimensions, must be less than 256.     bool ascOptimize = false;       // used for Ascend C optimization on special scenario. };；dst：输出 目的操作数，类型为LocalTensor。；src：输入 源操作数，类型为GlobalTensor。

约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。
