---
type: Guide
title: TensorFlow框架
description: '>针对Ascend 950PR/Ascend 950DT，暂不支持TensorFlow框架算子调用。'
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/ai_framework_adaptation/tensorflow_framework.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# TensorFlow框架

本章节介绍TensorFlow框架算子适配的流程，用于将TensorFlow框架的算子映射成CANN算子（开发者基于CANN框架自定义开发的算子），从而完成从TensorFlow框架调用到CANN算子的过程。同时给出TensorFlow框架侧算子调用的示例，便于开发者了解完整流程。
下图展示了完整的开发流程，具体步骤如下：
1.  环境准备。
1.  CANN软件安装请参考环境准备。
2.  安装框架插件包，请参考TensorFlow模型迁移中《TensorFlow 1.15模型迁移》或《TensorFlow 2.6.5模型迁移》的环境准备 > 安装框架插件包章节，获取框架插件包详细的安装步骤。
3.  创建算子工程。使用msOpGen工具创建算子开发工程。TensorFlow框架算子适配场景下，需要通过framework参数指定具体的框架为tf或者tensorflow，工具会自动生成框架适配代码。以自定义CANN算子AddCustom为例，使用msOpGen工具创建算子开发工程的具体命令如下：
2.  算子实现。
-   算子原型定义。通过原型定义来描述算子输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。
-   Kernel侧算子实现和host侧tiling实现请参考SIMD算子实现；工程化算子开发，支持开发者调用Tiling API基于CANN提供的编程框架进行tiling开发，kernel侧也提供对应的接口方便开发者获取tiling参数，具体内容请参考Kernel侧算子实现和Host侧Tiling实现，由此而带来的额外约束也在上述章节说明。
3.  算子入图（GE图）开发。算子入图场景下，需要提供shape推导等算子入图适配函数的实现。
4.  TensorFlow框架适配插件开发。详细说明见适配插件开发。
5.  编译部署。通过工程编译脚本完成算子的编译部署，分为算子包编译和算子动态库编译两种方式。
6.  TensorFlow框架算子调用。详细说明见TensorFlow原生算子映射到CANN算子和TensorFlow自定义算子开发并映射到CANN算子。完整样例请参考LINK。
## 适配插件开发
完成算子工程创建后，会在算子工程目录下生成framework/tf_plugin目录，用于存放TensorFlow框架适配插件实现文件。以自定义CANN算子AddCustom为例，算子工程目录如下：
当TensorFlow算子与CANN算子原型定义一致时，TensorFlow框架适配插件实现代码如下：
当TensorFlow算子与CANN算子原型定义不一致时，TensorFlow框架适配插件实现代码如下：
-   包含插件实现函数相关的头文件。
register.h存储在CANN软件安装后文件存储路径的“include/register/”目录下，包含该头文件，可使用算子注册相关类，调用算子注册相关的接口。
-   REGISTER_CUSTOM_OP：注册自定义算子，传入算子的_OpType_，需要与算子原型注册中的_OpType_保持一致。

<!-- cannbot:related:start -->
## 相关

- [高级编程概述](overview.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《TensorFlow框架》补充：>针对Ascend 950PR/Ascend 950DT，暂不支持TensorFlow框架算子调用。
<!-- cannbot:related:end -->
