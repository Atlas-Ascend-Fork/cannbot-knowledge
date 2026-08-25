---
type: Guide
title: 图编译和图执行
description: 本节通过单算子模型执行的样例来介绍图模式下图编译和图执行流程。单算子模型执行是指基于图IR执行算子，先编译算子（例如，使用ATC工具将Ascend
  IR定义的单算子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接口执行算子。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/operator_graph_development/graph_compilation_and_execution.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 图编译和图执行

本节通过单算子模型执行的样例来介绍图模式下图编译和图执行流程。单算子模型执行是指基于图IR执行算子，先编译算子（例如，使用ATC工具将Ascend IR定义的单算子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接口执行算子。
## 环境要求
-   已参考环境准备，完成CANN驱动和软件的安装，配置CANN软件所需基本环境变量。
安装CANN软件后，使用CANN运行用户进行编译、运行时，需要以CANN运行用户登录环境，执行source ${INSTALL_DIR}/set_env.sh命令设置环境变量。${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
-   已参考Aclnn算子工程化开发完成算子的开发和部署。
## 准备验证代码工程
代码工程目录结构如下，您可以单击LINK，获取样例工程的完整样例：
## 生成单算子离线模型文件
1.  构造静态shape单算子描述文件add_custom_static_shape.json，描述算子的输入、输出及属性等信息。
AddCustom静态shape算子的描述文件示例如下：
2.  使用ATC工具，将该算子描述文件编译成单算子模型文件（*.om文件）
ATC工具的命令示例如下：
关键参数解释如下：
-   --singleop：单算子描述文件（json格式）的路径。
-   --output：存放om模型文件的目录。
-   --soc_version：配置为AI处理器的型号，请根据实际环境进行替换。
以上命令执行后，会在output参数指定路径下生成*.om后缀的离线模型文件。
## 编写验证代码
您可以参考如下样例编写单算子加载、执行的代码逻辑。
以下是关键步骤的代码示例，不可以直接拷贝编译运行，仅供参考，调用接口后，需增加异常处理的分支，并记录报错日志、提示日志，此处不一一列举。
## 运行和验证
1.  开发环境上，设置环境变量，配置单算子验证程序编译依赖的头文件与库文件路径，如下为设置环境变量的示例。${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。{arch-os}为运行环境的架构和操作系统，arch表示操作系统架构，os表示操作系统，例如x86_64-linux。
2.  编译样例工程，生成单算子验证可执行文件。
1.  切换到样例工程根目录，然后在样例工程根目录下执行如下命令创建目录用于存放编译文件，例如，创建的目录为“build“。
mkdir -p build
2.  进入build目录，执行cmake编译命令，生成编译文件
命令示例如下所示：
cd build
cmake ../src -DCMAKE_SKIP_RPATH=TRUE
3.  执行如下命令，生成可执行文件。

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：图中 AI Core 节点需先生成可加载 kernel binary，是图编译阶段的底层依赖。
- [开启Tiling下沉](enable_tiling_sink.md)（`related`）：启用 tiling sink 会改变 tiling 在图编译/执行阶段的生成与下发位置，是该流程的关键优化分支。
- [异步执行（编译与执行）](../../compilation_and_execution/async_execution.md)（`related`）：图执行可异步提交，完成性与资源生命周期需按异步执行契约处理。
- [高级编程调用样例](../ai_framework_adaptation/onnx_framework/call_examples.md)（`related`）：图编译和图执行说明本节通过单算子模型执行的样例来介绍图模式下图编译和图执行流程。单算子模型执行是指基于图IR执行算子，先编译算子（例如，使用ATC工具将Ascend IR定义的单算子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接口执行算子。
- [基本开发流程](basic_development_flow.md)（`same_topic`）：基础流程给出建图、编译、加载、执行顺序，编译执行页展开其中后半段。
- [高级编程概述](overview.md)（`same_topic`）：高级编程概述 与《图编译和图执行》的实质衔接是：图高级编程概述由基本开发流程展开，并以图编译执行和 tiling 下沉说明 GE 从构图到下发的生命周期；编译部署流程是产物落点。
<!-- cannbot:related:end -->
