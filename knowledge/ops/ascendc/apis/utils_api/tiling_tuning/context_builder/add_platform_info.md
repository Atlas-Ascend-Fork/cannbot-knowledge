---
type: API
title: AddPlatformInfo
description: 设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式： - 自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。
  - 指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。 若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddPlatformInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# AddPlatformInfo

## 功能说明
设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式：
-   自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。
-   指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。
若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
## 函数原型
## 参数说明
customSocVersion：输入：AI处理器型号。
## 返回值说明
当前ContextBuilder对象。
## 约束说明
AddPlatformInfo调用后需要通过BuildTilingContext来构建Tiling的上下文，并传递给Tiling函数来使用。

<!-- cannbot:related:start -->
## 相关

- [te_fusion 未调 TilingPrepare 致 GEIR FPE](../../../../runbooks/compilation/te_fusion_tilingprepare_geir_fpe.md)（`exemplifies`）：“te_fusion 未调 TilingPrepare 致 GEIR FPE”定义：GEIR 图测试全 case 返回 GE error 4294967295 并抛 Python FPE；根因是 GE te_fusion/build_single_op 编译子路径不调 TilingParse<TilingPrepare> 填 compileInfo，tiling 函数读 compileInfo=0 除零。用 fprintf 探针判别三条 run 路径的 TilingPrepare 调用语义。；“AddPlatformInfo”定义：设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式： - 自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。 - 指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。 若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。。实质衔接：两卡都定位 TilingParse/TilingPrepare 未填 CompileInfo；ContextBuilder 的平台与 CompileInfo 注入接口用于构造可执行探针和避免除零。
- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：ContextBuilder构造函数 与《AddPlatformInfo》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [PlatformAscendC](../../platform_info/platform_ascend_c/platform_ascend_c.md)（`related`）：AddPlatformInfo 与《PlatformAscendC》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [PlatformAscendCManager](../../platform_info/platform_ascend_c_manager.md)（`related`）：AddPlatformInfo 与《PlatformAscendCManager》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [PlatformAscendC简介](../../platform_info/platform_ascend_c/platform_ascend_c_intro.md)（`related`）：AddPlatformInfo 与《PlatformAscendC简介》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《AddPlatformInfo》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [BuildKernelRunContext](build_kernel_run_context.md)（`same_topic`）：AddPlatformInfo 与《BuildKernelRunContext》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：AddPlatformInfo 与《BuildTilingContext》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [ContextBuilder](context_builder.md)（`same_topic`）：AddPlatformInfo 与《ContextBuilder》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [PlatformInfo](platform_info.md)（`same_topic`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《AddPlatformInfo》说明设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式： - 自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。 - 指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。 若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
<!-- cannbot:related:end -->
