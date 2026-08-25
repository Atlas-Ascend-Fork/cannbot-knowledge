---
type: API
title: PlatformInfo
description: 将指向fe::PlatFormInfos的指针传入TilingContext。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/PlatformInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# PlatformInfo

## 功能说明
将指向fe::PlatFormInfos的指针传入TilingContext。
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，Platform()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [te_fusion 未调 TilingPrepare 致 GEIR FPE](../../../../runbooks/compilation/te_fusion_tilingprepare_geir_fpe.md)（`exemplifies`）：“te_fusion 未调 TilingPrepare 致 GEIR FPE”定义：GEIR 图测试全 case 返回 GE error 4294967295 并抛 Python FPE；根因是 GE te_fusion/build_single_op 编译子路径不调 TilingParse<TilingPrepare> 填 compileInfo，tiling 函数读 compileInfo=0 除零。用 fprintf 探针判别三条 run 路径的 TilingPrepare 调用语义。；“PlatformInfo”定义：将指向fe::PlatFormInfos的指针传入TilingContext。。实质衔接：两卡都定位 TilingParse/TilingPrepare 未填 CompileInfo；ContextBuilder 的平台与 CompileInfo 注入接口用于构造可执行探针和避免除零。
- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《TilingDebug》说明通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [BuildTilingContext](build_tiling_context.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《BuildTilingContext》说明构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Conv3DBackpropFilter Tiling构造函数](../../../simd_api/adv_api/convolution_compute/conv3_d_backprop_filter_tiling/conv3_d_backprop_filter_tiling_constructor.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [Tiling调测](../tiling_tuning.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Tiling调测》说明Tiling调测接口索引。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Utils API简介](intro.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Utils API简介》说明ContextBuilder类提供一系列的API接口，支持手动构造TilingContext类来验证Tiling函数以及KernelContext类用于TilingParse函数的验证。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Utils API简介](../op_tiling_registry/intro.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Utils API简介》说明OpTilingRegistry类属于context_ascendc命名空间，主要用于加载Tiling实现的动态库，并获取算子的Tiling函数指针以进行调试和验证。该类通常与ContextBuilder类配合使用，后者用于构造Tiling函数所需的输入参数。具体用法可参考如何进行Tiling调测。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [AddPlatformInfo](add_platform_info.md)（`same_topic`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《AddPlatformInfo》说明设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式： - 自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。 - 指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。 若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
<!-- cannbot:related:end -->
