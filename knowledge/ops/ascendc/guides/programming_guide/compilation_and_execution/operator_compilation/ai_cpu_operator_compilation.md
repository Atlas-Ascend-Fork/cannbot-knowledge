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

<!-- cannbot:related:start -->
## 相关

- [DataStoreBarrier](../../../../apis/ai_cpu_api/data_store_barrier.md)（`explains`）：DataStoreBarrier 只能通过 >> 在异构编译场景调用；AI CPU 算子编译说明补齐 .aicpu/.asc 双文件、libaicpu_api 链接和 >> 调用的构建契约。
- [ExtendCfgInfo](../../../../apis/utils_api/prototype_register_management/op_aicpu_def/extend_cfg_info.md)（`explains`）：ExtendCfgInfo 与《AI CPU算子编译》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
- [UserDefined](../../../../apis/utils_api/prototype_register_management/op_aicpu_def/user_defined.md)（`explains`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《AI CPU算子编译》说明与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [assert（AI CPU API）](../../../../apis/ai_cpu_api/assert.md)（`explains`）：assert 依赖 AI CPU 的 .aicpu/.asc 双文件编译、`>>` 调用和 libaicpu_api.a 链接；编译指南给出这些落地步骤。
- [printf（AI CPU API）](../../../../apis/ai_cpu_api/printf.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；AI CPU算子编译正文界定“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [AI CPU编程（编程模型）](../../programming_model/ai_cpu_programming.md)（`related`）：AI CPU 编程模型给出 __aicpu__+__global__ 入口、.aicpu/-x aicpu 源文件和 Device 侧库环境；焦点编译指南把这些输入转成可运行产物。
- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`related`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《AI CPU算子编译》具体提供“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [编译与执行约束说明](constraints.md)（`same_topic`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《AI CPU算子编译》明确提供“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
<!-- cannbot:related:end -->
