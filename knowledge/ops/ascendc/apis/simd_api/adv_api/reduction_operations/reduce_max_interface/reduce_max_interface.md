---
type: API
title: ReduceMax接口
description: 对多维向量在指定维度求最大值，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMax_interface/ReduceMax_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceMax接口

对多维向量在指定维度求最大值，并提供临时空间大小获取接口。

对一个多维向量在指定的维度求最大值。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维求最大值，输出结果为[4, 5, 6]；指定在第二维求最大值，输出结果为[3, 6]。第一维是外层轴，简称外轴；第二维是内层轴，简称内轴。 图1 ReduceMax按第一个维度计算示例 图2 ReduceMax按最后一个维度计算示例

本接口组包含 ReduceMax。

本接口属于高阶归约运算接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；当srcInnerPad为True时，输入向量的内轴必须为32字节的整数倍。当原始向量的内轴长度n占据的字节长度不是32的整数倍时，需要开发者将其向上补齐到32的整数倍。开发者自行padding补齐后的内轴大小为inner = (n * sizeof(T) + 32 - 1) / 32 * 32 / sizeof(T)。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reduce count 必须排除 DMA 对齐填充元素](../../../../../runbooks/precision/reduction_count_excludes_dma_padding.md)（`exemplifies`）：Reduce count 必须排除 DMA 对齐填充元素说明count-form ReduceMax/ReduceSum 只应传逻辑归约长度；传 alignUp 后填充元素会参与 exp/sum 并改变 Softmax 分母。
- [Reduce work buf 额外占 UB 致 507035](../../../../../runbooks/compilation/reduce_work_buf_ub_507035.md)（`exemplifies`）：Reduce work buf 额外占 UB 致 507035说明Ascend950 上为 ReduceSum/ReduceMax 单独开 fp32 work buffer，N>=14336 时 UB 总占用超限，kernel 启动后访问越界 UB 区触发 device error type 3 error code 507035。判别=缩小复现定位 N 阈值 + 逐 InitBuffer 累加字节对照 UB 上限 + 删冗余 work buffer 复用闲置 fp32 buffer 反向证明。根因为 work buffer 与主数据 buffer 同量级，把 UB 从刚好够推到超额；InitBuffer 划分超额编译期不报错，崩在 kernel 启动后。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差说明仅限 fp32 末轴 Softmax 的安全回退：归约结果经 32B UB 槽 GetValue 后标量 Duplicate；FP16/BF16 不适用，应走 UB 槽 LoadAlign 到 Reg 后广播。
- [Reg::Reduce 跨 chunk 覆写导致规约失真](../../../../../runbooks/precision/reg_reduce_per_chunk_result_must_accumulate_explicitly.md)（`exemplifies`）：Reg::Reduce 跨 chunk 覆写导致规约失真说明dav-3510 Reg::Reduce 每次只产当前 chunk 的标量结果；循环复用 dstReg 会丢失前序 chunk，须显式折叠 lane 0。
- [如何使用归约计算API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：如何使用归约计算API说明归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不同，归约指令分为以下几种，可参考归约指令示意图：。
- [AscReduceMax](../../../c_api/reg/reduce_compute/asc_reduce_max.md)（`related`）：AscReduceMax说明根据mask对源操作数进行归约最大值操作，将最大值及其索引写入目的操作数。
- [ReduceMax](../../../basic_api/memory_vector_compute/reduction_compute/reduce_max.md)（`related`）：ReduceMax说明从所有输入数据中找出最大值，可选返回最大值索引。
- [asc_reduce_max](../../../../simt_api/warp_functions/warp_reduce_functions/asc_reduce_max.md)（`related`）：asc_reduce_max说明对Warp内所有活跃线程输入的val求最大值。Warp内所有活跃线程返回相同的结果。
- [GetReduceMaxMaxMinTmpSize](get_reduce_max_max_min_tmp_size.md)（`same_topic`）：GetReduceMaxMaxMinTmpSize：该 host 接口专门为 ReduceMax 计算选择 sharedTmpBuffer，ReduceMax 正文中的 isReuseSource/shape 必须与这里的估算入参保持一致。 目标卡《ReduceMax接口》补充：对多维向量在指定维度求最大值，并提供临时空间大小获取接口。
- [ReduceMax](reduce_max.md)（`same_topic`）：ReduceMax说明对多维向量在指定维度求最大值，通过pattern参数指定Reduce轴和Normal轴，当前支持AR和RA两种模式。
<!-- cannbot:related:end -->
