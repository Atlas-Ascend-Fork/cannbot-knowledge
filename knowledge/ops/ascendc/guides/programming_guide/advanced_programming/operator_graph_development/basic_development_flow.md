---
type: Guide
title: 基本开发流程
description: 该开发流程以工程化算子开发为基础，除了需要提供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件。本节仅提供算子入图代码文件的开发指导。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基本开发流程

该开发流程以工程化算子开发为基础，除了需要提供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件。本节仅提供算子入图代码文件的开发指导。
假设下图是我们需要使用的网络模型，您可能会想直接逐个算子调用，根据输入tensor得到输出tensor就可以完成网络的运行，但在图模式场景下，实际的网络模型生成过程中，会先进行tensor shape以及datatype的推导。这样可以让我们在图执行之前，就知道各tensor的数据类型和形状，提前校验其正确性；同时提前推理出算子的输出张量描述，包括张量的形状、数据类型及数据排布格式等信息，算子构图准备阶段就可以为所有的张量静态分配内存，避免动态内存分配带来的开销。
下面的网络模型经过shape和datatype推导之后，可以得到灰色底纹框中的推导信息：
除了tiling实现外，算子入图时需要额外提供的实现代码有以下几种：
-   datatype推导：根据算子的输入datatype、算子逻辑及算子属性等信息，推理出算子的输出张量datatype。
-   shape推导：根据算子的输入shape、算子逻辑及算子属性等信息，推理出算子的输出张量shape。
-   ShapeRange推导：编译时无法推导输出shape，只能推导输出shape range，执行完才能得出输出shape。在下发时需要按照输出shape range来申请最大输出内存，该类算子需要提供ShapeRange推导函数。
-   声明数据依赖：部分算子在InferShape时，需要依赖某个输入的具体值才可以进行，这类算子被称为“数据依赖算子”，对应的输入被称为“数据依赖输入”。该类算子在注册时，需要声明其数据依赖输入。
下表列出了不同类型的算子对上述实现代码的要求。
不同的类型的算子对入图实现代码的要求
实际开发时通过固定的datatype和shape推导原型实现推导函数，然后再通过SetInferShape、SetInferDataType接口来关联对应的shape推导函数，样例如下。
## datatype推导
以AddCustom算子为例，InferDataType的实现如下所示。该样例中输出tensor的数据类型与输入tensor的数据类型相同，所以直接将任意一个输入tensor的数据类型赋给输出tensor即可。
如下示例则给出了更灵活的datatype推导样例，当输入的数据类型为DT_INT4时，其输出的数据类型为DT_INT32。
## shape推导
简单的shape推导逻辑可以使用Follow接口来表达，比如输出shape和输入shape相同的情况。示例如下：输出“y1”Follow输入“x1”场景，指定Follow模式为SHAPE，此时“y1”的shape将会和“x1”保持一致。
无法在原型定义中通过Follow表达的情况需要开发者编写InferShape函数，InferShape函数的原型是固定的，如下示例，接受一个InferShapeContext作为输入，从此context上可以获取到输入、输出的shape指针等内容。输入shape为const类型，因此InferShape时，输入shape是只读、不允许修改的。

<!-- cannbot:related:start -->
## 相关

- [图编译和图执行](graph_compilation_and_execution.md)（`related`）：先编译算子（例如，使用ATC工具将Ascend IR定义的单算子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接口执行算子；除了需要提供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件；基本开发流程给出图编译执行前必须交付的入图代码边界。
<!-- cannbot:related:end -->
