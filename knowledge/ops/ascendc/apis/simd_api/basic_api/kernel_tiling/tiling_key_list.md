---
type: API
title: TILING_KEY_LIST
description: TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey
  == key1或TilingKey == key2条件的分支逻辑。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_LIST.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TILING_KEY_LIST

TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey

TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey == key1或TilingKey == key2条件的分支逻辑。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：TILING_KEY_LIST运用于if和else if分支，不支持else分支，即用TILING_KEY_LIST函数来表征N个分支，必须用N个TILING_KEY_LIST(key1,key2)来分别表示。；支持传入两个TilingKey，每个TilingKey具备唯一性。；使用该接口时，必须设置默认的Kernel类型，也可以为某个TilingKey单独配置Kernel类型，该配置会覆盖默认Kernel类型。Kernel类型仅支持配置为KERNEL_TYPE_MIX_AIC_1_1、KERNEL_TYPE_MIX_AIC_1_2。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《TILING_KEY_LIST》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TILING_KEY_LIST》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：TilingKey 缓存 correction 致 tilingdata 复用 与《TILING_KEY_LIST》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：sub-kernel 后缀 _N 是 tilingKey 位编码非序号说明编译产出的 .o 中 sub-kernel 后缀 _N 是 FastEncodeTilingKeyDirect 的位编码 tilingKey（T|E<<1|R<<2），非连续序号；_3 空位是设计性 gap，[0,4,2,1,5] 是 TPL_SEL 展开顺序副产物。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：tilingKey 编码与 TPL 位打包不一致致路由错误说明host ComputeTilingKey 用语义顺序值 (0/1/2/3/4) 与 ASCENDC_TPL GET_TPL_TILING_KEY 的位打包编码 (0/4/2/1/5) 不一致，normal-tail-R 被路由到 group-tail-A 存根 sub-kernel 产出垃圾。
- [GET_TPL_TILING_KEY](../../../utils_api/tiling_template_programming/get_tpl_tiling_key.md)（`same_topic`）：GET_TPL_TILING_KEY说明Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
- [IcpuSetTilingKey](../debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`same_topic`）：IcpuSetTilingKey说明指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`same_topic`）：REGISTER_TILING_FOR_TILINGKEY说明用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围。
- [TILING_KEY_IS](tiling_key_is.md)（`same_topic`）：TILING_KEY_IS说明在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
<!-- cannbot:related:end -->
