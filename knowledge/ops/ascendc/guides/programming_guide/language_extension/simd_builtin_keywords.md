---
type: Guide
title: SIMD BuiltIn关键字
description: 如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simd_builtin_keywords.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SIMD BuiltIn关键字

## 预定义宏
如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
-   __NPU_ARCH__
__NPU_ARCH__是Device侧AI Core代码中的预处理宏，用于标识AI处理器的架构版本。该宏由四位数字组成，其中前三位数字用于标识AI Core的IP核(Intellectual Property Core)类型，第四位数字标识该AI Core同一个IP核的配置版本。通过该宏，开发者可以针对不同AI处理器，差异化进行代码适配和优化。产品型号和NPU架构版本的对应关系如下：
- Ascend 950PR/Ascend 950DT：3510
- Atlas A3 训练系列产品/Atlas A3 推理系列产品：2201
- Atlas A2 训练系列产品/Atlas A2 推理系列产品：2201
- Atlas 200I/500 A2 推理产品：3002
- Atlas 推理系列产品：2002
- Atlas 训练系列产品：1001
以下为通过__NPU_ARCH__控制在不同AI处理器上算子输出值舍入模式的示例。
-   ASCEND_IS_AIV、ASCEND_IS_AIC
ASCEND_IS_AIV和ASCEND_IS_AIC是通过C++宏实现的条件判断语句，用于在__aicore__修饰的函数中实现代码的条件编译。基于分离模式（AIC核和AIV核分离）开发融合算子时，算子逻辑中同时涉及AIV核和AIC核的处理逻辑，并需要进行核间同步，此时需要通过ASCEND_IS_AIV/ ASCEND_IS_AIC进行AIV和AIC核代码的隔离。
以MatmulNzCustom算子为例，该算子在分离模式下需要分别在AIV核和AIC核上实现不同的逻辑。具体而言，AIV核负责将矩阵数据搬入Unified Buffer，完成数据的重排（将矩阵数据转换为NZ格式），并将其写入Global Memory。而AIC核则直接从Global Memory读取已经重排好的NZ格式数据，并执行矩阵乘法（Matmul）计算。由于AIV核和AIC核的代码逻辑不同，需要通过ASCEND_IS_AIV和ASCEND_IS_AIC宏进行代码隔离，确保在编译时分别生成适用于AIV核和AIC核的代码。
示例伪码如下：
-   ASCENDC_CUBE_ONLY
ASCENDC_CUBE_ONLY是通过C++宏实现的条件判断语句，用于在__aicore__修饰的函数中实现代码的条件编译。
基于分离模式开发非融合算子时，在只有矩阵计算的算子场景下，可以通过设置ASCENDC_CUBE_ONLY，开启纯Cube模式完成Matmul计算，减少消息通信的性能开销，提升算子性能。

<!-- cannbot:related:start -->
## 相关

- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`related`）：Runbook 将 __NPU_ARCH__ 从 SoC ini 的 NpuArch 一直追到 dispatcher 与 dav_c* 变体，给出 BuiltIn 宏用于源码分支之外的可执行查证链。
- [__simd_vf__ if constexpr 致 hoisted 报错](../../../runbooks/compilation/simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《SIMD BuiltIn关键字》说明如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [SIMD&SIMT BuiltIn关键字](simd_simt_hybrid_builtin_keywords.md)（`same_topic`）：SIMD&SIMT BuiltIn关键字 与《SIMD BuiltIn关键字》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
<!-- cannbot:related:end -->
