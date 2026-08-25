---
type: Guide
title: 高级编程调用样例
description: 完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现一个使用推理工具进行推理的过程，目的在于让您快速体验推理场景下网络中自定义算子调用的过程。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/ai_framework_adaptation/onnx_framework/call_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 调用样例

完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现一个使用推理工具进行推理的过程，目的在于让您快速体验推理场景下网络中自定义算子调用的过程。
在完成如下步骤之前，您需要先参考上文内容完成自定义LeakyRelu算子kernel侧和host侧的开发、ONNX适配插件的开发，并完成算子的编译部署。
LeakyRelu算子实现的完整样例请参考LINK。ONNX框架调用的完整示例请参考LINK。
1.  通过如下命令获取ONNX框架网络模型。作为示例，该模型中仅包含一个LeakyRelu算子。
2.  执行如下命令生成离线模型。（如下命令中使用的目录以及文件均为样例，请以实际为准）
关键参数的解释如下：
-   --model：ONNX框架网络模型文件（*.onnx）的路径。
-   --framework：原始框架类型。5表示ONNX。
-   --output：转换后的离线模型的路径以及文件名。请注意，记录保存该om模型文件的路径，后续开发应用时需要使用。
-   --soc_version：AI处理器的型号。
-   --input_shape：指定模型输入数据的shape，请基于算子支持的shape范围和实际使用场景进行设置，这里设置输入X为固定shape [8,16,1024]。
-   --input_format：指定模型输入数据的格式，请基于算子支持的格式和实际使用场景进行设置，这里配置为ND。
3.  使用export ASCEND_GLOBAL_LOG_LEVEL=1改变日志级别为INFO，若出现如下提示信息，则说明进入了Ascend C自定义算子编译流程且模型转换成功。
成功执行命令后，在--output参数指定的路径下，可查看离线模型（如：leaky_relu.om）。
4.  通过aclmdlExecute等接口在应用中加载模型执行推理。
