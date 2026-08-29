---
type: Guide
title: AI CPU算子编译
description: 与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AI CPU算子编译

与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。
## 通过bisheng命令行编译
下文基于一个Hello World打印样例来讲解如何通过bisheng命令行编译AI CPU算子。该样例包含hello_world.aicpu文件（AI CPU核函数定义）和main.asc文件（通过内核调用符调用AI CPU核函数）。
hello_world.aicpu文件内容如下：
Host侧使用内核调用符>>进行AI CPU算子的调用， main.asc示例代码如下：
开发者可以使用bisheng命令行将hello_world.aicpu与main.asc分别编译成.o，再链接成为可执行文件，编译命令如下：
-   编译hello_world.aicpu时，通过-I指定依赖头文件所在路径；通过--cce-aicpu-laicpu_api为Device链接依赖的库libaicpu_api.a，通过--cce-aicpu-L指定libaicpu_api.a的库路径。
-   编译main.asc时，通过--npu-arch编译选项指定对应的架构版本号。
${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
各产品型号对应的架构版本号请通过对应关系表进行查询。
上文我们通过一个入门示例介绍了使用bisheng命令行编译生成可执行文件的示例。除此之外，使用bisheng命令行也支持编译生成AI CPU算子的动态库与静态库，用户可在asc代码中通过内核调用符>>调用AI CPU算子的核函数，并在编译asc代码源文件生成可执行文件的时候，链接AI CPU动态库或者静态库，注意：若单独编译AI CPU算子代码生成动态库、静态库时，需要手动链接表格中的库文件。
-   编译生成算子动态库
-   编译生成算子静态库
## AI CPU算子常用编译选项
AI CPU算子常用的编译选项说明如下：
## CMake方式编译
项目中可以使用CMake来更简便地使用毕昇编译器编译AI CPU算子，生成可执行文件、动态库、静态库或二进制文件。
仍以通过bisheng命令行编译中介绍的Hello World打印样例为例，除了代码实现文件，还需要在工程目录下准备一个CMakeLists.txt。
CMakeLists.txt内容如下：
各产品型号对应的架构版本号请通过对应关系表进行查询。
如果需要CMake编译编译生成动态库、静态库，下面提供了更详细具体的编译示例：
-   编译.cpp文件生成动态库
-   编译.asc文件与.aicpu文件生成静态库
