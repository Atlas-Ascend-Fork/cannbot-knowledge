---
type: Guide
title: Aclnn算子工程化开发快速入门
description: 本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/aclnn_quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Aclnn算子工程化开发快速入门

本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
## 前置环境准备
### 编译工具链
在开始之前，请确保系统中已安装以下工具：
工具：版本建议：说明
CMake：≥ 3.19：构建系统生成器。
GCC / G++：≥ 7.5：C++编译器。
Python：≥ 3.9：msOpGen工具运行依赖。
Make：—：构建执行工具。
msOpGen是CANN软件包提供的算子工程生成工具。加载CANN环境变量后，可通过msopgen --help验证工具是否可用；如果命令不在PATH中，也可使用${INSTALL_DIR}/python/site-packages/bin/msopgen调用，其中${INSTALL_DIR}为CANN软件安装路径。
可通过以下命令检查工具版本：
### CANN环境变量
编译和运行均依赖CANN提供的环境变量，在开始任何步骤前，先加载环境变量：
> 每次打开新终端时都需要重新执行该命令。后续步骤中不再重复提示。
## 快速入门流程
### 步骤概览
步骤：内容：预计时间
步骤1：创建工程：1分钟
步骤2：查看目录结构：—
步骤3：修改Kernel侧代码：1分钟
步骤4：修改Host侧Tiling：1分钟
步骤5：编译：1分钟
步骤6：部署：—
步骤7：调用算子：1分钟
### 创建工程
编写算子原型定义文件add_custom.json（建议放在全英文路径下），然后使用msOpGen工具生成工程骨架。JSON中每个输入/输出的format和type列表长度必须一致，保持一一对应关系。
-   -i：指定算子原型定义文件add_custom_.json所在路径，请根据实际情况修改。
-   -c：ai_core-ascendxxyy代表算子在AI Core上执行，ascendxxyy为昇腾AI处理器的型号soc_version。JSON中的type/format列表定义算子支持的数据类型和格式组合。msOpGen会基于这些信息生成对应的Kernel编译配置。
-   -lan：参数cpp代表算子基于Ascend C编程框架，使用C/C++编程语言开发。
-   -out：生成文件所在路径，可配置为绝对路径或者相对路径，并且工具执行用户对路径具有可读写权限。若不配置，则默认生成在执行命令的当前路径。
将ascendxxyy替换为您的AI处理器型号soc_version。msOpGen会自动将芯片型号映射为框架统一标识，并写入CMakePresets.json的ASCEND_COMPUTE_UNIT和原型定义的AddConfig中。
### 查看目录结构
msOpGen生成的工程目录结构如下：
需要修改的文件已用[需修改]标注，后续步骤将逐一修改这些文件。
