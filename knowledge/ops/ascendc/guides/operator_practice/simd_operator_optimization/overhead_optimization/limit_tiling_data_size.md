---
type: Guide
title: 限制TilingData结构大小
description: 限制TilingData结构大小以减少GM到栈空间的拷贝开销，通过精简变量、选择合适类型和合理排布实现。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 限制TilingData结构大小

【优先级】中
【描述】TilingData结构是Tiling切分信息的载体，当Host侧按照Tiling切分策略计算完Tiling后，算子会以入参的方式将Tiling切分信息从Host侧传递到Device侧，此时Tiling信息存放在GM上。调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。拷贝耗时为us级别，在小shape的场景下，进行此类优化收益会更加明显。
限制TilingData结构大小，可以从以下方面考虑：
-   减少不必要的TilingData结构变量；
-   根据Tiling的数据范围选择合适的变量类型；
-   合理排布TilingData结构；
-   TilingData整体结构要求8字节补齐。
【反例】
-   如下的示例中存在TilingData结构变量冗余的情况：NumBlocks信息已经通过SetSimdNumBlocks接口进行设置，可以在Kernel侧调用GetBlockNum接口获取，无需通过TilingData结构传递。
-   此外，变量的数据类型也不合理：formerNum和tailNum分别为计算整块数据的核数和计算尾块数据的核数，不会超过NUM_BLOCKS的值，使用uint8_t类型即可；formerLength等变量根据其计算逻辑，不会超出uint32_t的范围，使用uint32_t类型即可。
【正例】
Tiling变量无冗余，变量数据类型最小化。
【反例】
如下的示例中TilingData结构不合理：由于AI处理器访存需要8字节对齐，在用户定义TilingData结构后，Ascend C工程框架会按照8字节对齐的方式对字节进行补齐，并保证整体TilingData结构满足8字节对齐要求。如下TilingData结构formerNum和tailNum变量都会补充3个字节，整体TilingData结构会因为8字节对齐再补充4个字节，该TilingData结构共计补充10个字节。
【正例】
如下的示例中，对Tiling参数的排布进行了调整，字节排布合理，只需要补充2个字节，达到了减小TilingData结构的目的。

<!-- cannbot:related:start -->
## 相关

- [TilingData结构定义](../../../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`explains`）：字段类型和排布在结构定义处决定总字节数，是优化落点。
- [Tiling数据结构注册](../../../../apis/utils_api/tiling_data_structure_register/tiling_data_structure_register.md)（`explains`）：Tiling数据结构注册 与《限制TilingData结构大小》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [Host 缺 SetDataSize 致 TilingData 截断](../../../../runbooks/precision/host_setdatasize_tilingdata.md)（`related`）：精简结构后仍需 SetDataSize 与实际序列化长度一致，否则 Kernel 读取残缺。
- [TilingData 追加数据超额致 INVALID_TILING](../../../../runbooks/compilation/tilingdata_invalid_tiling.md)（`related`）：focal 的 INVALID_TILING 由 SetDataSize 超过默认 capacity 触发；指南给出精简字段、缩窄类型和排布以控制 TilingData 总大小的直接修复方向。
- [核函数内删除Workspace相关冗余操作](remove_workspace_redundancy.md)（`related`）：精简 tiling data 与去冗余 workspace 都降低固定搬运/初始化开销。
<!-- cannbot:related:end -->
