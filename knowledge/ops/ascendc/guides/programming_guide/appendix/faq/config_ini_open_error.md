---
type: Guide
title: 调用算子时出现无法打开config.ini的报错
description: 自定义算子包安装部署后，在调用已部署的算子时，出现如下json文件获取失败的报错信息：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/config_ini_open_error.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 调用算子时出现无法打开config.ini的报错

## 现象描述
自定义算子包安装部署后，在调用已部署的算子时，出现如下json文件获取失败的报错信息：
通过查询前文的报错信息，上述json文件获取失败的原因是前置流程中无法打开config.ini，提示信息如下：
## 问题根因
根因在于当前调用算子的用户缺少对算子包部署目录下的config.ini（*/opp/vendors/config.ini）文件的读权限。config.ini文件权限默认为640，仅允许部署用户和同属组用户访问，当前执行用户与安装用户非同一属组，缺少读权限，导致算子调用失败。
比如下述场景即会导致调用算子时出现执行报错：root用户安装部署自定义算子包，HwHiAiUser属组用户调用已部署的自定义算子。
## 处理步骤
联系自定义算子包安装用户修改config.ini权限为644：

<!-- cannbot:related:start -->
## 相关

- [RTC错误码（RTC运行时编译）](../../../../apis/utils_api/rtc/rtc_error_code.md)（`explains`）：调用算子时出现无法打开config.ini的报错 与《RTC错误码（RTC运行时编译）》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [ShowKernelDebugData工具](../show_kernel_debug_data_tool.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《ShowKernelDebugData工具》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [TilingDebug](../common_operations/tiling_debug.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《TilingDebug》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [msobjdump工具](../msobjdump_tool.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《msobjdump工具》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [optype_collector工具](../optype_collector_tool.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《optype_collector工具》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [算子包部署时出现权限不足报错](operator_deploy_permission_error.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《算子包部署时出现权限不足报错》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
<!-- cannbot:related:end -->
