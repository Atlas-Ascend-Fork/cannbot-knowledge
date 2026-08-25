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

<!-- cannbot:related:start -->
## 相关

- [图编译和图执行](../../operator_graph_development/graph_compilation_and_execution.md)（`related`）：图编译和图执行说明本节通过单算子模型执行的样例来介绍图模式下图编译和图执行流程。单算子模型执行是指基于图IR执行算子，先编译算子（例如，使用ATC工具将Ascend IR定义的单算子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接口执行算子。
- [适配插件开发](adaptation_plugin_development.md)（`related`）：调用样例验证 REGISTER_CUSTOM_OP 映射、插件 so 加载和 ONNX 模型执行是否闭环。
- [高级编程概述](../overview.md)（`related`）：高级编程概述：该概述的任务就是把自定义算子接入 AI 框架；PyTorch、TensorFlow和 ONNX 插件/调用卡分别展开正文点名的三条适配流程。 目标卡《高级编程调用样例》补充：完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现一个使用推理工具进行推理的过程，目的在于让您快速体验推理场景下网络中自定义算子调用的过程。
- [单算子API调用](../../aclnn_operator_development/invocation/single_operator_api_call.md)（`same_topic`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；高级编程调用样例正文界定“完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
<!-- cannbot:related:end -->
