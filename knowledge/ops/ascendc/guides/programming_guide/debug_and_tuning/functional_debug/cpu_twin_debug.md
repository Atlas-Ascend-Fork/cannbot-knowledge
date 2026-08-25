---
type: Guide
title: CPU域孪生调试（功能调试）
description: 本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当前SIMT编程场景不支持。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# CPU域孪生调试

本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当前SIMT编程场景不支持。
## CPU侧验证核函数
在非昇腾设备上，开发者可以利用CPU仿真环境先行进行算子开发和测试，并在准备就绪后，利用昇腾设备进行加速计算。在编译与运行章节，我们已经介绍了算子Kernel程序NPU域的编译运行。相比于NPU域的算子运行逻辑，CPU域调试将算子Kernel程序以Host程序的形式进行编译，此时算子Kernel程序链接CPU调测库，执行编译生成的可执行文件，可以完成算子CPU域的运行验证。CPU侧的运行程序，通过GDB通用调试工具进行单步调试，可以精准验证程序执行流程是否符合预期。
推荐使用CMake编译方式，可在最小化修改的情况下快速开启CPU域孪生调试功能。
1.  通过在CMake配置阶段传入变量CMAKE_ASC_RUN_MODE和CMAKE_ASC_ARCHITECTURES即可开启CPU域编译。命令示例如下：
cpu表示开启CPU域编译，dav-后为NPU架构版本号，请根据实际情况参考对应关系表进行填写。
其他CMakeLists.txt项目配置通过CMake编译进行编写。
> [!CAUTION] 注意
> 在CPU孪生调试模式下，编译器不识别Ascend C提供的SIMD-BuiltIn关键字及SIMT-BuiltIn关键字，包括
> - 函数执行空间限定符：如__aicore__、__global__、__host__等;
> - 函数标记宏：如__simd_vf__、__simd_callee__、__simt_vf__等；
> - 地址空间限定符：如__gm__ 、__ubuf__等。
>
> 这些关键字与Device侧执行强相关，在CPU孪生调试模式下无需实际生效，因此系统框架将这些关键字定义为空。
> 由于这种置空处理，仅通过BuiltIn关键字区分的函数签名将被视为相同，会导致重定义编译错误。
>
> 典型问题场景包括：
> 1. Device侧函数与Host侧函数同名
>
>
> 如下例中，add函数仅通过__aicore__区分运行域，在CPU孪生调试模式下两个声明将冲突：
> 	__aicore__ inline void add(int x, int y);  // Device侧
> void add(int x, int y);                    // Host侧（等同于 __host__）
>
>
> 2. 参数类型仅有地址空间限定符不同
>
>
> 如下例中，两个Device侧函数仅在指针的地址空间限定符上不同：
> 	__aicore__ inline void process(__gm__ void* data, int size);
> __aicore__ inline void process(__ubuf__ void* data, int size);
>
>
> 在孪生调试场景下需特别注意：请勿定义仅依赖BuiltIn关键字来区分的函数。
## gdb调试
可使用gdb单步调试算子计算精度。
