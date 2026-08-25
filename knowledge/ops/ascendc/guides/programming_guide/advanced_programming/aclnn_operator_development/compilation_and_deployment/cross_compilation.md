---
type: Guide
title: 高级编程交叉编译
description: 本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 交叉编译

本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。
## 概述
完成算子代码实现后，如果编译平台和运行平台架构一致，直接参考基本流程编译即可。如需交叉编译（编译平台架构与运行平台架构不同），参考本文档。
交叉编译的典型场景：
- 在x86_64开发机上编译，部署到aarch64边缘设备。
- 在aarch64服务器上编译，部署到x86_64服务器。
## 交叉编译工具下载
以Ubuntu系列操作系统为例，交叉编译工具下载命令如下表所示。其他操作系统请替换为实际的下载命令。
当前平台架构：运行环境平台架构：编译工具下载命令
x86_64：aarch64：sudo apt-get install -y g++-aarch64-linux-gnu
aarch64：x86_64：sudo apt-get install -y g++-x86-64-linux-gnu
安装完成后，可通过以下命令验证工具是否可用：
## CMakePresets.json配置
交叉编译需修改算子工程目录下CMakePresets.json的两个配置项：
### 使能交叉编译
将ENABLE_CROSS_COMPILE设置为True：
### 指定交叉编译工具路径
使用which命令查找交叉编译工具的安装路径：
假设安装在 /usr/bin/ 下，将CMAKE_CROSS_PLATFORM_COMPILER设置为交叉编译工具的安装路径：
## 执行交叉编译
交叉编译Kernel二进制时，编译框架需要先加载本机架构可执行的Tiling动态库来获取编译参数。因此设置完ENABLE_CROSS_COMPILE=True且ENABLE_BINARY_PACKAGE=True之后，需要执行两步才能完成交叉编译：
- 要先在本机模式下生成libcust_opmaster_rt2.0.so；
- 再通过HOST_NATIVE_TILING_LIB传给交叉编译阶段。
下面以快速入门里的AddCustom、在aarch64编译机上生成x86_64目标算子包为例演示：
建议本机Tiling库和交叉编译产物使用两个不同的构建目录，避免本机架构产物和目标架构产物混在一起：
- build_native_tiling：只用于生成本机架构可加载的Tiling动态库。
- build_out：用于生成目标架构的算子包。
步骤1：本机模式生成Tiling库
HOST_NATIVE_TILING_LIB指向的是本机架构动态库。例如当前编译机是aarch64时，该库应为aarch64动态库。
