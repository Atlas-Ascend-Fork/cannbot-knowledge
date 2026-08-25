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

<!-- cannbot:related:start -->
## 相关

- [C-API-Reg矢量计算接口理论性能汇总](../../../../../apis/appendix/c_api_reg_vector_compute_theoretical_perf_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《C-API-Reg矢量计算接口理论性能汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Load](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Load》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [MaskMergeMode](../../../../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/mask_merge_mode.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《MaskMergeMode》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_vector_compute.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口MergeMode支持情况汇总](../../../../../apis/appendix/reg_vector_compute_interface_mergemode_support_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口指令单双发汇总](../../../../../apis/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口指令单双发汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口理论性能汇总](../../../../../apis/appendix/reg_vector_compute_interface_theoretical_perf_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口理论性能汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口精度标准汇总](../../../../../apis/appendix/reg_vector_compute_interface_precision_standard_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口精度标准汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口软仿情况汇总](../../../../../apis/appendix/reg_vector_compute_interface_soft_simulation_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口软仿情况汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Reg矢量计算接口边界值汇总](../../../../../apis/appendix/reg_vector_compute_interface_boundary_value_summary.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Reg矢量计算接口边界值汇总》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Store](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Store》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [VF调用](../../../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《VF调用》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [asc_vf_call](../../../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《asc_vf_call》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [AI Core SIMD编程模型概述](../overview.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《AI Core SIMD编程模型概述》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](../../../../../runbooks/precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《AR 跨块循环放在 __simd_vf__ 只执行首块》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [__simd_vf__ if constexpr 致 hoisted 报错](../../../../../runbooks/compilation/simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《Reg矢量计算编程（C++ Tensor编程）》说明本文介绍如何使用基础API（C++模板接口）编写Reg矢量计算代码。基础API与Reg矢量计算编程（语言扩展C API）描述的是同一套Reg矢量硬件能力，功能语义一致，主要区别在于API命名、类型表达和可配置参数的表达方式。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《simd_vf 互调导致 helper 编译失败》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [静态Tensor编程](static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《Reg矢量计算编程（C++ Tensor编程）》说明本文介绍如何使用基础API（C++模板接口）编写Reg矢量计算代码。基础API与Reg矢量计算编程（语言扩展C API）描述的是同一套Reg矢量硬件能力，功能语义一致，主要区别在于API命名、类型表达和可配置参数的表达方式。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [CppTensorProgrammingOverview](cpp_tensor_programming_overview.md)（`same_topic`）：CppTensorProgrammingOverview 与《Reg矢量计算编程（C++ Tensor编程）》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [Reg矢量计算编程（C指针编程）](../c_pointer_programming/reg_vector_computation.md)（`same_topic`）：两篇 Reg 矢量编程指南明确描述同一套寄存器硬件、VF 执行域和 Load→Compute→Store 流程；差别仅是语言扩展 C 指针接口与 C++ Tensor 模板接口的表达。
<!-- cannbot:related:end -->
