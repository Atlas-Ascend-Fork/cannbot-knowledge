---
type: Guide
title: 适配插件开发
description: '>针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，暂不支持ONNX框架算子调用。'
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/ai_framework_adaptation/onnx_framework/adaptation_plugin_development.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 适配插件开发

您可以参考本章节进行算子适配插件的开发，将ONNX框架的算子映射成适配AI处理器的算子（下文简称CANN算子），从而完成从ONNX框架调用Ascend C自定义算子的过程。如果只涉及插件开发，也可以不依赖自定义算子工程，参考LINK生成算子插件so后，通过ASCEND_CUSTOM_OPP_PATH指定so所在路径进行使用。
完成算子工程创建后，会在算子工程目录下生成framework/onnx_plugin目录，用于存放ONNX框架适配插件实现文件。以自定义CANN算子LeakyReluCustom为例，算子工程目录如下：
下文主要讲解ONNX框架适配插件实现文件（leaky_relu_custom_plugin.cc ）的开发流程。
1.  包含所需头文件。
-   register.h，存储在CANN软件安装后文件存储路径的“include/register/”目录下，包含该头文件，可使用算子注册相关类，调用算子注册相关的接口。
-   operator.h（可选），存储在CANN软件安装后文件存储路径的“include/graph/”目录下，包含该头文件，可以使用Operator类相关接口，获取算子输入输出及属性等算子信息。
-   json.hpp，用于进行ONNX数据定义的解析，将String类型的算子参数定义转换为json格式。若样例工程中未提供“json.hpp”文件，用户可以自行下载，并将“json.hpp”放在工程可以找到的任意路径下，然后包含此头文件即可，下载路径可参见json.hpp。
2.  使用REGISTER_CUSTOM_OP宏，完成CANN算子和ONNX框架的算子映射关系注册。使用方法如下：
-   REGISTER_CUSTOM_OP：注册自定义算子，OpType为算子类型名称，需要与算子原型注册中的OpType保持一致。
-   FrameworkType：ONNX代表原始框架为ONNX。
-   OriginOpType：算子在原始框架中的类型。例如自定义算子_OpTypeA_，对应ONNX算子库版本opset_version=11，应传入“ai.onnx::11::_OpTypeA_”，当前支持的ONNX版本范围为9\~15。
-   ParseParamsByOperatorFn(_ParseParamByOpFunc_)：用来注册解析算子参数实现映射关系的回调函数，需要用户自定义实现回调函数ParseParamByOpFunc。具体实现方式参考3。
-   ImplyType：指定算子的实现方式。Ascend C算子实现类型设置为TVM。
3.  实现回调函数ParseParamByOpFunc。其函数声明如下所示：
-   _ParseParamByOpFunc_：函数名称，用户自定义。
-   op_src：ONNX框架定义的Operator类对象，包含ONNX模型中自定义的算子属性信息，定义来源于ONNX框架的原始模型文件。
-   op_dest：CANN算子数据结构，保存算子信息。

<!-- cannbot:related:start -->
## 相关

- [高级编程调用样例](call_examples.md)（`related`）：插件开发卡要求“使用REGISTER_CUSTOM_OP宏，完成CANN算子和ONNX框架的算子映射关系注册。”；调用示例说明“完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。”。注册完成是后续 ONNX 推理调用样例的直接前置。
<!-- cannbot:related:end -->
