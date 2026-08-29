---
type: Guide
title: 高级编程概述
description: 本文是基础内容，说明Aclnn算子工程化开发这组文档的范围、阅读顺序和前置条件。建议先确认环境满足要求，再按快速入门跑通AddCustom示例，跑通后回到对应章节逐步补齐细节。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 概述

本文是基础内容，说明Aclnn算子工程化开发这组文档的范围、阅读顺序和前置条件。建议先确认环境满足要求，再按快速入门跑通AddCustom示例，跑通后回到对应章节逐步补齐细节。
## 什么是工程化算子开发
### 关键术语
先介绍几个核心概念：
名称：含义
自定义算子工程：根据算子原型定义编写或者生成的工程骨架，包含原型定义、Tiling实现、Kernel实现和CMake编译配置。
算子原型：描述算子的输入、输出、属性、数据类型、格式、Shape推导等信息。
Host侧：运行在CPU侧的准备逻辑，例如Shape推导、Tiling计算、workspace大小设置。
Kernel侧：运行在AI Core上的计算逻辑，是算子真正执行计算的部分。
Tiling：根据输入Shape、数据类型等信息切分计算任务，并把Kernel需要的参数传递到Kernel侧。
aclnn单算子API：算子工程编译后基于算子原型自动生成的C语言API，应用程序可通过该接口直接调用自定义算子。
### 工程化开发是什么
工程化算子开发是指基于自定义算子工程完成算子实现、编译部署和调用验证的开发方式，主要面向CANN相关场景对接：单算子调用场景通过aclnn API完成接入，算子入图场景通过GE图执行链路完成接入。通过工程化开发，算子原型、Host侧Tiling、Kernel实现和编译部署配置可以在两类场景中最大化复用同一份交付件。相比手动组织编译流程和分别对接调用链路，工程化开发由msOpGen生成工程骨架，CMake管理编译，编译产物自动包含aclnn API以及入图所需的原型定义等文件，部署时只需安装.run包或者链接静态/动态库。
### 集成方式
围绕同一份算子工程，常见集成方式如下：
集成方式：说明：适用场景
单算子API调用：通过生成的aclnn接口直接调用算子，基于C语言API执行算子。：算子功能验证、单算子调用。
算子入图：补充Shape推导等入图适配代码后，基于GE图执行链路执行自定义算子。：图模式、IR构图、多算子组合。
AI框架调用：在工程化算子基础上增加框架插件适配后，通过PyTorch/TensorFlow等框架调用自定义算子。：融入AI训练或推理流程。
## 推荐阅读路径
首次接触建议从快速入门开始，先用5分钟跑通AddCustom算子的端到端流程。跑通后再按以下路径逐步补齐细节。
本指南共22个文档，按开发流程分为四个部分。首次阅读只需关注[基础]文档，遇到具体问题时再查阅[扩展]文档。
### 设计与实现
[基础]（按顺序阅读）：
- 算子功能设计 — 支持范围、场景划分、Kernel组织。
- 算子原型定义 — 输入输出属性定义、Shape推导。
- Host侧Tiling实现 — Tiling函数与数据结构、使用约束。
- Kernel侧算子实现 — 核函数编程与API使用。
