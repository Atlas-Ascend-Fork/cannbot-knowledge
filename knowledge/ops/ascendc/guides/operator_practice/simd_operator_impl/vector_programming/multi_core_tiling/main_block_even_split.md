---
type: Guide
title: SIMD算子实现主块均分
description: 长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/main_block_even_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 主块均分

长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。
图 1  数据切分示意图
本场景样例的完整代码请参考场景0：主块均分。样例中固定使用8个核，主块长度mainTileLength为3200个half元素，数据整体长度为256000个half元素。数据平均分配到8个核上处理，每个核计算32000个元素；每个核内共切分成10个主块，不涉及尾块和尾核处理。
## Tiling实现
基于本节的切分策略，Tiling需要定义如下参数：
- blockLength：每个核处理的数据长度，单位为元素。
- tileNum：每个核需要计算的主块个数。
据此定义MainTileOnlyTiling结构体，代码如下：
接下来完成Tiling参数的计算。涉及的主要变量包括：逻辑核数numBlocks、一个DataBlock的字节数dataBlockSize、一个half元素的字节数halfSize、一个DataBlock包含的half元素数量alignNum、一个主块包含的half元素数量mainTileLength。步骤如下：
1. 根据dataBlockSize和halfSize计算alignNum，本样例中alignNum为16。totalLength为输入数据的元素总数，将其按alignNum向上对齐后得到对齐后的元素总数totalLengthAligned。
2. 用totalLengthAligned除以numBlocks * mainTileLength得到每个核均分到的主块数量mainTileNum，取余得到主块均分后的剩余元素数量mainTileRemainder；再将mainTileNum乘以mainTileLength得到每个核已分配的元素数量baseLength，baseTileNum直接取mainTileNum。
3. 当mainTileRemainder为0时，表示所有数据都能按主块均匀分配到各核，此时使用MainTileOnlyTiling结构体传递Tiling切分信息。
## 算子类实现
Kernel侧算子采用静态Tensor编程方式实现，通过LocalTensor构造函数直接指定Local Memory地址。静态Tensor编程中的内存管理和同步管理请参考对应章节，本节重点说明各核GM地址的计算以及主块数据的循环处理流程。
- Kernel入口接收Host侧传入的Tiling结构体，并依次调用算子类的Init与Process函数完成初始化与计算。主块均分场景中，传入的结构体类型为MainTileOnlyTiling。
- 由于数据被分配到多个核上处理，每个核访问的Global Memory地址范围各不相同。Init函数通过tiling.blockLength获取每个核处理的元素数量，并结合GetBlockIdx计算当前核所处理数据在Global Memory上的起始偏移offset，随后将偏移与长度传入InitGm完成GM地址设置；同时将tiling.tileNum保存到成员变量，供Process函数使用。
