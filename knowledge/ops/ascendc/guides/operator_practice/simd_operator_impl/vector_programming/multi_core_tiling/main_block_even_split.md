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

<!-- cannbot:related:start -->
## 相关

- [AscGetBlockIdx](../../../../../apis/simd_api/c_api/sys_var/asc_get_block_idx.md)（`explains`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《AscGetBlockIdx》说明获取当前运行核的索引。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [GetBlockIdx](../../../../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`explains`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《GetBlockIdx》说明获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [DoubleBuffer场景](../double_buffer_scenario.md)（`related`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《DoubleBuffer场景》说明因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [SIMD算子实现概述](overview.md)（`related`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《SIMD算子实现概述》说明Ascend C核函数是在Device侧执行的并行函数。为了提高算子的执行效率，通常采用多核并行计算，将输入数据切分后分配到不同的逻辑核上处理；同时，由于单个核的Local Memory容量有限，无法一次完整容纳算子的输入和输出数据，需要分批搬运数据进行计算。这种对输入数据进行切分、分块计算的过程称为Tiling。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](../../../../../runbooks/performance/blocklength_slice_numblocks.md)（`related`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《blockLength 对齐 slice 致 numBlocks 塌缩单核》说明SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [基础矢量算子](../basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [SIMD算子实现尾块均分](tail_block_even_split.md)（`same_topic`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《SIMD算子实现尾块均分》说明该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [TailCoreSplit](tail_core_split.md)（`same_topic`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《TailCoreSplit》说明主块均分后剩余数据无法以DataBlock均匀分配到每个核时，将额外DataBlock分配给前几个整核，其余为尾核，分别处理不同数据量。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [TailCoreTailBlockSplit](tail_core_tail_block_split.md)（`same_topic`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《TailCoreTailBlockSplit》说明主块均分后剩余DataBlock无法均分到每个核时，整核和尾核都包含尾块，整核比尾核多处理一个DataBlock，需分别记录Tiling参数。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
<!-- cannbot:related:end -->
