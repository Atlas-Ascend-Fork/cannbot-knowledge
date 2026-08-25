---
type: Guide
title: 基于样例工程完成Kernel直调
description: '>本章节介绍的基于样例工程完成Kernel直调的方式，后续不再演进。推荐开发者直接使用命令行或者编写Cmake文件进行编译，详细内容请参考AI
  Core SIMD编译。'
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/kernel_direct_call_from_sample.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基于样例工程完成Kernel直调

下文将以Add矢量算子为例对Kernel直调算子开发流程进行详细介绍。
## 环境准备
-   使用Kernel Launch算子工程之前，需要参考环境准备章节安装驱动固件和CANN软件包，完成开发环境和运行环境的准备。
-   使用该算子工程要求cmake版本为3.16及以上版本，如不符合要求，请参考如下的命令示例更新cmake版本，如下示例以更新到3.16.0版本为例。
## 工程目录
样例目录结构如下所示：
基于该算子工程，开发者进行算子开发的步骤如下：
-   完成算子kernel侧实现。
-   编写算子调用应用程序main.cpp。
-   编写CMake编译配置文件CMakeLists.txt。
-   根据实际需要修改输入数据和真值数据生成脚本文件gen_data.py；验证输出数据和真值数据是否一致的验证脚本verify_result.py。
-   根据实际需要修改编译运行算子的脚本run.sh并执行该脚本，完成算子的编译运行和结果验证。
## 算子Kernel侧实现
请参考工程目录中的矢量算子、矩阵算子、融合算子的Kernel实现完成Ascend C算子实现文件的编写。
## 算子调用应用程序
下面代码以固定shape的add_custom算子为例，介绍算子核函数调用的应用程序main.cpp如何编写。您在实现自己的应用程序时，需要关注由于算子核函数不同带来的修改，包括算子核函数名，入参出参的不同等，合理安排相应的内存分配、内存拷贝和文件读写等，相关API的调用方式直接复用即可。
1.  按需包含头文件，通过ASCENDC_CPU_DEBUG宏区分CPU/NPU侧需要包含的头文件。需要注意的是，NPU侧需要包含对应的核函数调用接口声明所在的头文件aclrtlaunch_\{kernel_name\}.h（该头文件为工程框架自动生成），kernel_name为算子核函数的名称。
2.  应用程序框架编写。该应用程序通过ASCENDC_CPU_DEBUG宏区分代码逻辑运行于CPU侧还是NPU侧。
3.  CPU侧运行验证。完成算子核函数CPU侧运行验证的步骤如下：
4.  NPU侧运行验证。完成算子核函数NPU侧运行验证的步骤如下：
## CMake编译配置文件编写
本节会介绍CMake文件中一些关键环境变量和Cmake命令参数的说明，通常情况下不需要开发者修改，但是这些参数可以帮助开发者更好的理解编译原理，方便有能力的开发者对Cmake进行定制化处理。
环境变量说明
Cmake命令语法说明
简化的编译流程图如下图所示：将算子核函数源文件编译生成kernel侧的库文件（*.so或*.a库文件）；工程框架自动生成核函数调用接口声明头文件；编译main.cpp（算子调用应用程序）时依赖上述头文件，将编译应用程序生成的目标文件和kernel侧的库文件进行链接，生成最终的可执行文件。
编译安装结束后在CMAKE_INSTALL_PREFIX目录下生成的编译产物示例如下；最终的可执行文件会生成在cmake命令的执行目录下。

<!-- cannbot:related:start -->
## 相关

- [GM_ADDR 标量不可解引用为 tiling 结构体指针](../../../runbooks/compilation/gm_addr_tiling.md)（`related`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《基于样例工程完成Kernel直调》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [SIMT 核类型推导失败 — 补 __vector__](../../../runbooks/compilation/direct_launch_kernel_requires_vector_qualifier.md)（`related`）：The runbook resolves a direct-launch kernel-type inference failure by adding the required __vector__ qualifier to the kernel shown by this guide.
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`related`）：The runbook shows that direct-invoke builds cannot rely on GET_TILING_DATA_WITH_STRUCT and must decode the tiling pointer explicitly.
- [核函数直调算子额外适配说明](../advanced_programming/super_kernel/kernel_direct_call_adaptation.md)（`same_topic`）：样例给出 direct call 的声明、绑定和构建写法，可用于适配验证。
<!-- cannbot:related:end -->
