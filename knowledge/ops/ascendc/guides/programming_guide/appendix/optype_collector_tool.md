---
type: Guide
title: optype_collector工具
description: optype_collector工具用于采集内置/自定义算子包中指定AI处理器的OpType信息，并检测自定义算子包与内置算子包、自定义算子包之间的OpType重名问题，帮助开发者在自定义算子安装或交付前提前发现命名冲突。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/optype_collector_tool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# optype_collector工具

optype_collector工具用于采集内置/自定义算子包中指定AI处理器的OpType信息，并检测自定义算子包与内置算子包、自定义算子包之间的OpType重名问题，帮助开发者在自定义算子安装或交付前提前发现命名冲突。
工具支持扫描以下信息来源：
- CANN安装目录下的CANN内置算子包。
- CANN安装目录下的自定义算子包。
- ASCEND_CUSTOM_OPP_PATH指定的一个或多个自定义算子包路径。
## 工具安装
1.  安装optype_collector工具。
工具跟随CANN软件包发布，参考环境准备完成CANN安装后，即可使用该工具。
2.  设置环境变量。
-   root用户安装Ascend-cann-toolkit包时
-   非root用户安装Ascend-cann-toolkit包时
多个自定义算子包路径使用系统路径分隔符分隔。
3.  检查工具是否安装成功。
执行如下命令，若能正常显示帮助信息，则表示工具环境正常，功能可正常使用。
## 命令格式
本文中的{soc_version}表示AI处理器的型号。
-   配置说明如下：
-   输出内置算子OpType清单的命令
参数说明
参数（区分大小写）：可选/必选：说明
{soc_version}：必选：指定待扫描的AI处理器型号，可填写CANN支持的产品AI处理器型号。
--builtin：可选：仅输出CANN内置算子包中的OpType清单。未指定清单模式时，默认使用该模式。
-   输出自定义算子OpType清单的命令
参数说明
参数（区分大小写）：可选/必选：说明
{soc_version}：必选：指定待扫描的AI处理器型号，可填写CANN支持的产品AI处理器型号。
--custom：必选：仅输出自定义算子包中的OpType清单。工具会扫描CANN包安装目录和ASCEND_CUSTOM_OPP_PATH指定路径下的自定义算子包。
-   输出内置算子与自定义算子OpType清单的命令
参数说明
参数（区分大小写）：可选/必选：说明
{soc_version}：必选：指定待扫描的AI处理器型号，可填写CANN支持的产品AI处理器型号。
--all：必选

<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](../../../runbooks/compilation/aclnn_optype_collision_built_in_ops_legacy_507035.md)（`related`）：检测自定义算子包与内置算子包、自定义算子包之间的OpType重名问题；built-in 路径优先于 vendor 路径。工具卡提供交付前的 OpType 重名探测，runbook 解释重名后 C++ runtime 会优先命中 built-in binary；联合可从预检结果直接判断 507035 与错误 kernel 加载的根因。
<!-- cannbot:related:end -->
