---
type: Guide
title: 高级编程概述
description: 本章节内容介绍AI框架调用自定义算子的方法。如下图所示，Pytorch支持单算子和图模式两种，TensorFlow仅支持图模式。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/ai_framework_adaptation/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

本章节内容介绍AI框架调用自定义算子的方法。如下图所示，Pytorch支持单算子和图模式两种，TensorFlow仅支持图模式。

AI框架调用时，除了需要提供CANN框架调用时需要的代码实现文件，还需要进行插件适配开发。

<!-- cannbot:related:start -->
## 相关

- [PyTorch框架](pytorch_framework.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《PyTorch框架》补充：通过PyTorch框架进行模型的训练、推理时，会调用很多算子进行计算。开发者开发的自定义算子如果需要集成部署到PyTorch框架，有如下几种方式：
- [TensorFlow框架](tensorflow_framework.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《TensorFlow框架》补充：>针对Ascend 950PR/Ascend 950DT，暂不支持TensorFlow框架算子调用。
- [适配插件开发](onnx_framework/adaptation_plugin_development.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《适配插件开发》补充：>针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，暂不支持ONNX框架算子调用。
- [高级编程调用样例](onnx_framework/call_examples.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《高级编程调用样例》补充：完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现一个使用推理工具进行推理的过程，目的在于让您快速体验推理场景下网络中自定义算子调用的过程。
<!-- cannbot:related:end -->
