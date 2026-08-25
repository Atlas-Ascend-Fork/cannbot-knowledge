---
type: API
title: GET_TILING_DATA
description: 用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GET_TILING_DATA

获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：该 runbook 记录把类型名误作首参导致变量遮蔽/宏展开失败，直接说明普通 GET_TILING_DATA 的参数语法。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](../../../../runbooks/compilation/gm_addr_tiling.md)（`exemplifies`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《GET_TILING_DATA》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [Host 缺 SetDataSize 致 TilingData 截断](../../../../runbooks/precision/host_setdatasize_tilingdata.md)（`exemplifies`）：Host 未 SetDataSize 会使传入 Kernel 的 TilingData 截断，即使 GET_TILING_DATA 宏本身编译正常也读到残缺内容。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：直调工程没有框架生成的 TilingData 注册环境时，WITH_STRUCT 宏不可用，应手动解释 tiling 指针。
- [多分支策略](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`explains`）：多分支策略 与《GET_TILING_DATA》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [通过TilingData传递属性信息](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“GET_TILING_DATA”明确用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使…。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [COPY_TILING_WITH_ARRAY](copy_tiling_with_array.md)（`related`）：GET_TILING_DATA说明用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
- [GetTiling](../../adv_api/convolution_compute/conv3_d_backprop_filter_tiling/get_tiling.md)（`related`）：GetTiling 与《GET_TILING_DATA》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA正文说明“用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`same_topic`）：MEMBER 只读取指定 tiling 字段，避免无须复制完整结构，是同一传递契约的细粒度变体。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`same_topic`）：WITH_STRUCT 显式指定结构体类型，适合多 TilingData 或需要栈地址的场景；普通宏返回默认注册结构。
<!-- cannbot:related:end -->
