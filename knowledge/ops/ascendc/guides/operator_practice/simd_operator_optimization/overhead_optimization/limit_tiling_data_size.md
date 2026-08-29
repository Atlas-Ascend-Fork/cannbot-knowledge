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

- [GET_TILING_DATA](../../../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data.md)（`explains`）：“调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。”。Guide 解释为何要减小 GET_TILING_DATA 从 GM 到栈的搬运量，API 卡界定该宏的实际取数行为。
- [GetBlockNum](../../../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_num.md)（`explains`）：“NumBlocks信息已经通过SetSimdNumBlocks接口进行设置，可以在Kernel侧调用GetBlockNum接口获取，无需通过TilingData结构传递。”；“获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。”。Guide 给出删除冗余 NumBlocks 字段的具体替代调用，API 卡说明 GetBlockNum 返回的是任务逻辑核数。
- [TilingData结构定义](../../../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`explains`）：“- CheckAlignAndGenPlaceHolder：该接口是内部关联接口，用于框架侧检查Tiling结构体中成员变量是否满足字节对齐要求，并对不对齐的变量进行补齐，开发者无需关注。”；“调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。”。指南把结构定义的对齐与长度直接转成字段精简、排布和 GM→栈开销优化决策。
- [Host 缺 SetDataSize 致 TilingData 截断](../../../../runbooks/precision/host_setdatasize_tilingdata.md)（`related`）：“【描述】TilingData结构是Tiling切分信息的载体，当Host侧按照Tiling切分策略计算完Tiling后，算子会以入参的方式将Tiling切分信息从Host侧传递到Device侧，此时Tiling信息存放在GM上。”；“任何在 op_host 自定义 TilingData 结构体的 ACLNN 算子，TilingFunc 末尾填完字段后必须 `rawTilingData->SetDataSize(sizeof(<TilingData>))`，再 `SetBlockDim`/`SetTilingKey`。”。精简 TilingData 时还必须由 Host 声明实际传输字节数，否则 Device 只收到截断结构，优化会变成功能错误。
<!-- cannbot:related:end -->
