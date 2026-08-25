---
type: API
title: IcpuSetTilingKey
description: 指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/ICPU_SET_TILING_KEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# IcpuSetTilingKey

指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。

进行核函数的CPU侧运行验证时，CPU调测总入口，完成CPU侧的算子程序调用。

本接口组包含 <<<>>>, ICPU_RUN_KF。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

约束：为了保留接口兼容，推荐 >>编译使用。；除了func、blkdim以外，其他的变量都必须是通过GmAlloc分配的共享内存的指针；传入的参数的数量和顺序都必须和kernel保持一致。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《IcpuSetTilingKey》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《IcpuSetTilingKey》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：IcpuSetTilingKey 与《TilingKey 缓存 correction 致 tilingdata 复用》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：IcpuSetTilingKey 与《sub-kernel 后缀 _N 是 tilingKey 位编码非序号》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：IcpuSetTilingKey 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [GET_TPL_TILING_KEY](../../../../utils_api/tiling_template_programming/get_tpl_tiling_key.md)（`related`）：IcpuSetTilingKey 与《GET_TPL_TILING_KEY》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [IcpuRunKf](icpu_run_kf.md)（`related`）：IcpuRunKf 运行 Kernel 前由 ICPU_SET_TILING_KEY 注入当前 tiling key，才能在 CPU 孪生环境走与设备一致的模板分支。
- [TILING_KEY_IS](../../kernel_tiling/tiling_key_is.md)（`related`）：IcpuSetTilingKey 与《TILING_KEY_IS》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [CPU孪生调试](cpu_twin_debug.md)（`same_topic`）：IcpuSetTilingKey 与《CPU孪生调试》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [TILING_KEY_LIST](../../kernel_tiling/tiling_key_list.md)（`same_topic`）：IcpuSetTilingKey说明指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。
<!-- cannbot:related:end -->
