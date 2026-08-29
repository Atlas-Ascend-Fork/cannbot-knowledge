---
type: Guide
title: Reg矢量计算编程（C++ Tensor编程）
description: 本文介绍如何使用基础API（C++模板接口）编写Reg矢量计算代码。基础API与Reg矢量计算编程（语言扩展C API）描述的是同一套Reg矢量硬件能力，功能语义一致，主要区别在于API命名、类型表达和可配置参数的表达方式。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算编程

本文介绍如何使用基础API（C++模板接口）编写Reg矢量计算代码。基础API与Reg矢量计算编程（语言扩展C API）描述的是同一套Reg矢量硬件能力，功能语义一致，主要区别在于API命名、类型表达和可配置参数的表达方式。
Reg矢量编程的硬件原理、内存层级、VF函数执行域、流水线同步、Hardware Loop、VF融合等与API接口命名无关的内容，请参见Reg矢量计算编程（语言扩展C API）。本文只说明基础API的接口定位、模板参数、数据类型体系、API分类和典型调用方式。
## 基础API定位
基础API Reg矢量计算接口位于AscendC::Reg命名空间，是语言扩展C API的C++模板化封装。基础API并不改变Reg矢量计算的编程模型：仍然需要在__aicore__域通过asc_vf_call进入__simd_vf__函数，并在VF函数内完成Load -> Compute -> Store。
基础API的主要特点如下：
- 使用C++类型表达寄存器对象，例如RegTensor、MaskReg、AddrReg、UnalignRegForLoad、UnalignRegForStore ,对应关系参考数据对象与寄存器类型。
- 使用模板参数表达数据类型、搬运模式、PostUpdate模式等配置。
- 多数接口可通过参数自动推导寄存器类型。
- 搬运接口可以与LocalTensor衔接，可以支持不操作UB地址，也可以外层__aicore__代码从LocalTensor::GetPhyAddr()获取UB物理地址，再传入VF函数内的Reg搬运接口。
- 部分计算接口提供MaskMergeMode模板参数，用于控制未被mask选中的元素如何写入目的寄存器。
> 📌 提示：
>
> 1. 基础API和C API功能一致。若需要理解“为什么需要Reg矢量编程”“寄存器与UB/GM的关系”“哪些场景需要同步”等模型性内容，请直接阅读C API版本文档。
>
> 2. 搬运接口支持LocalTensor参数，在后续版本提供，暂未支持。
## 与C API的对应关系
基础API与C API的核心差异是表达形式不同。
