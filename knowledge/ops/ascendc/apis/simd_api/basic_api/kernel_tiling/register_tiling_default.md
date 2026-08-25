---
type: API
title: REGISTER_TILING_DEFAULT
description: 用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_DEFAULT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# REGISTER_TILING_DEFAULT

用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。

用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：若TilingData结构体在命名空间内，注册时需要携带对应的命名空间作用域符。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《REGISTER_TILING_DEFAULT》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [REGISTER_NONE_TILING 致 UnboundLocalError](../../../../runbooks/compilation/register_none_tiling_unboundlocalerror.md)（`exemplifies`）：接口卡定义 REGISTER_TILING_DEFAULT 注册具体 TilingData 的契约，正是绕过 REGISTER_NONE_TILING dfx 未初始化路径所采用的替代入口。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《REGISTER_TILING_DEFAULT》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《REGISTER_TILING_DEFAULT》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [多分支策略](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`explains`）：多分支策略 与《REGISTER_TILING_DEFAULT》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`related`）：当不同 TilingKey 需要不同结构体时应从唯一 default 槽切换到按 key 注册，正是多 struct 冲突的接口级替代契约。
- [Tiling数据结构注册](../../../utils_api/tiling_data_structure_register/tiling_data_structure_register.md)（`related`）：Tiling数据结构注册 与《REGISTER_TILING_DEFAULT》的实质衔接是：TilingData 定义、注册、读取宏、尺寸限制与三张冲突/截断故障卡共同覆盖 host→kernel 数据契约。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；REGISTER_TILING_DEFAULT正文说明“用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
<!-- cannbot:related:end -->
