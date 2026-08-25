---
type: Guide
title: 编译与执行RTC
description: RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# RTC

RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。
运行时编译库提供以下核心接口：
-   aclrtcCreateProg：根据输入参数（字符串形式表达的Ascend C源代码等）创建aclrtcProg程序实例。
-   aclrtcAddNameExpr（可选）：注册需要导出的核函数名表达式，支持模板参数（如"Kernel::add_custom\"），非模板核函数可跳过。
-   aclrtcCompileProg：编译给定的程序，支持用户自定义编译选项，比如指定NPU架构版本号：--npu-arch=dav-2201。支持的编译选项可以参考《毕昇编译器用户指南》。
-   aclrtcGetBinDataSize：获取编译后的Device侧二进制数据的大小。
-   aclrtcGetBinData：获取编译后的Device侧二进制数据。
-   aclrtcGetLoweredName（可选）：获取核函数编译后的mangled name，用于后续通过aclrtBinaryGetFunction查找核函数句柄，非模板核函数可跳过。
-   aclrtcDestroyProg：在编译和执行过程结束后，销毁给定的程序。
编译完成后需要调用如下接口完成（仅列出核心接口）Kernel加载与执行。完整流程和详细接口说明请参考《Runtime运行时API》中的“Kernel加载与执行”章节。
1.  调用aclInit、aclrtSetDevice等接口初始化运行环境并指定Device。
2.  通过aclrtBinaryLoadFromData接口解析由aclrtcGetBinData接口获取的算子二进制数据。加载时可通过ACL_RT_BINARY_LOAD_OPT_MAGIC指定二进制类型，如ACL_RT_BINARY_MAGIC_ELF_AICORE。
3.  调用aclrtBinaryGetFunction接口获取核函数句柄。
4.  调用aclrtLaunchKernelWithArgsArray接口，在已创建的Stream上按参数数组方式启动对应算子的计算任务。无参数核函数可传入空参数数组；有参数核函数需保证参数数组元素按核函数入参顺序排列，且每个元素指向Host侧的参数值。
5.  调用aclrtSynchronizeStream、aclrtBinaryUnLoad、aclrtDestroyStream、aclrtResetDevice、aclFinalize等接口完成同步和资源释放。
如下样例演示了如何使用aclrtc接口编译并运行一个核函数，该核函数中调用了printf进行打印。完整样例请参考LINK。
编译命令如下，编译时需要设置-I\$\{ASCEND_HOME_PATH\}/include，用于找到aclrtc相关头文件，并设置-L\$\{ASCEND_HOME_PATH\}/lib64链接acl_rtc动态库。
对于非模板核函数（如hello_world），编译器可自动导出符号，无需额外操作。
