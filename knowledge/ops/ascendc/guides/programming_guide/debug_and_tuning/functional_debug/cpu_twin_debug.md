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

<!-- cannbot:related:start -->
## 相关

- [CPU孪生调试](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/cpu_twin_debug.md)（`explains`）：指南说明 CPU 孪生方法与限制，接口集给出 GmAlloc、ICPU_RUN_KF、tilingKey 和 KernelMode 等实际控制入口。
- [GmAlloc](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/gm_alloc.md)（`explains`）：GmAlloc 与《CPU域孪生调试（功能调试）》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
- [GmFree](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/gm_free.md)（`explains`）：GmFree 与《CPU域孪生调试（功能调试）》的实质衔接是：GmFree 只释放 GmAlloc 在 CPU 孪生调试中创建的共享映射，调试指南给出这对接口的执行边界。
- [IcpuRunKf](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/icpu_run_kf.md)（`explains`）：ICPU_RUN_KF 是 CPU 调测的核函数调用总入口，把指南中的 CPU 域编译结果真正执行起来。
- [SetKernelMode](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/set_kernel_mode.md)（`explains`）：SetKernelMode 与《CPU域孪生调试（功能调试）》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
- [printf（AI CPU API）](../../../../apis/ai_cpu_api/printf.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；CPU域孪生调试（功能调试）正文界定“本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当前SIMT编程场景不支持”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [NPU域上板调试（功能调试）](npu_board_debug.md)（`related`）：CPU 孪生不模拟所有 Device 关键字、同步和硬件行为；NPU 上板调试是后续验证 DumpTensor、内存异常和真实执行的互补路径。
- [算子调试（功能调试）](../../../operator_practice/functional_debug/operator_debug.md)（`related`）：算子调试总流程中的 Host/CPU 调试由该卡展开为 CPU 孪生编译、GDB 单步及 BuiltIn 置空导致的重定义边界。
- [调试与调优概述](../overview.md)（`related`）：总览把 CPU 孪生调试定位为无需 NPU 的功能与基础 API 排查入口；该子指南给出具体执行条件。
- [运行正常（功能调试）](../../../operator_practice/functional_debug/running_normally.md)（`related`）：CPU 孪生可在上板前验证控制流、用 gdb/printf 定位基础逻辑，但不支持 SIMT 且 BuiltIn 限定符被置空，适合作为前置而非设备等价验证。
- [精度正常（功能调试）](../../../operator_practice/functional_debug/accuracy_normal.md)（`same_topic`）：《精度正常（功能调试）》处理“性能优化的基础是算子运行得到正确的计算结果。评判计算结果正确性需要有一定的评判标准，即使用已知的正确的输出和实际结果进行比较。优化过程中，每次迭代修改后，都需要验证性能优化的新结果是否满足精度评判标准。”。《CPU域孪生调试（功能调试）》明确提供“本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当前SIMT编程场景不支持。”，其参数、调用或验证步骤直接接入精度正常时的基线固定、二分定位、误差对比和复现流程。
<!-- cannbot:related:end -->
