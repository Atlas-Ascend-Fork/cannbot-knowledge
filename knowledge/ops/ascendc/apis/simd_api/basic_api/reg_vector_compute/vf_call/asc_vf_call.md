---
type: API
title: asc_vf_call
description: 在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。
tags:
- task.lookup
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/vf_call/asc_vf_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# asc\_vf\_call<a name="ZH-CN_TOPIC_0000002563057755"></a>

## 功能说明<a name="section618mcpsimp"></a>

在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <auto funcPtr, typename... Args>
__aicore__ inline void asc_vf_call(Args &&...args)
```

## 参数说明<a name="section0866173114710"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| :-- | :------------ | 
| funcPtr | 用于指定SIMD入口核函数（Kernel）。 |
| Args | 定义可变参数，用于传递实参到SIMD入口核函数（Kernel）。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| :-- | :------------ | :-- |
| args | 输入 | 可变参数，用于传递实参到SIMD入口核函数（Kernel）。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

-   asc\_vf\_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用\_\_simd\_vf\_\_修饰宏。
-   asc\_vf\_call启动SIMD VF子任务时，入参仅支持Ascend C的内置数据类型（half、int32_t、uint32_t、float等）及其组成的指针、数组、结构体类型，且指针类型必须指向Unified Buffer（UB）内存。

## 调用示例<a name="section1316724610428"></a>

使用SIMD VF函数对UB数据做加法计算。

```cpp
// SIMD函数
template <typename T>
__simd_vf__ inline void AddVF(
    __ubuf__ T* dstAddr, __ubuf__ T* src0Addr, __ubuf__ T* src1Addr, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
{
    AscendC::Reg::RegTensor<T> src0Reg;
    AscendC::Reg::RegTensor<T> src1Reg;
    AscendC::Reg::RegTensor<T> dstReg;
    AscendC::Reg::MaskReg mask;
    for (uint16_t i = 0; i < repeatTimes; i++) {
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::LoadAlign(src0Reg, src0Addr + i * oneRepeatSize);
        AscendC::Reg::LoadAlign(src1Reg, src1Addr + i * oneRepeatSize);
        AscendC::Reg::Add(dstReg, src0Reg, src1Reg, mask);
        AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
    }
}

template <typename T>
__aicore__ inline void Compute()
{
    AscendC::LocalTensor<T> dst = outQueueZ.AllocTensor<T>();
    AscendC::LocalTensor<T> src0 = inQueueX.DeQue<T>();
    AscendC::LocalTensor<T> src1 = inQueueY.DeQue<T>();
    constexpr uint16_t oneRepeatSize = AscendC::GetVecLen() / sizeof(T);
    uint32_t count = 512;
    // 向上取整，计算循环次数
    uint16_t repeatTimes = AscendC::CeilDivision(count, oneRepeatSize);
    __ubuf__ T* dstAddr = (__ubuf__ T*)dst.GetPhyAddr();
    __ubuf__ T* src0Addr = (__ubuf__ T*)src0.GetPhyAddr();
    __ubuf__ T* src1Addr = (__ubuf__ T*)src1.GetPhyAddr();
    asc_vf_call<AddVF<T>>(dstAddr, src0Addr, src1Addr, count, oneRepeatSize, repeatTimes);
    outQueueZ.EnQue(dst);
    inQueueX.FreeTensor(src0);
    inQueueY.FreeTensor(src1);
}
```


<!-- cannbot:related:start -->
## 相关

- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`exemplifies`）：“在用 ops-registry-invoke-glacier 工作流（ACLNN 算子仓开发路线）实现 `add` 算子（`out = self + alpha*other`，Broadcast 范式）时，按 DESIGN.md §3.5 的 RegBase 路线编写 kernel 头 `operators/add_package/op_kernel/arch35/add_kernel.h`：把逐元素加法 fusion 链封装成一个 VF 函数 `AddVF`，用 `__simd_vf__ inline` 标注，函数体内调用 `AscendC::Reg::Add` / `AscendC::Reg::Muls`（参数为 `AscendC::Reg::RegTensor<T>`），并由 Process 通过 `AscendC::asc_vf_call<AddVF<T>>(...)` 调用。目标芯片 `ascend950`，架构 `DAV_3510` / arch35，CANN 9.1.0。”记录按普通 `__simd_vf__` 函数调用 asc_vf_call 仍触发毕昇 139/70 的平台实测；“约束：- asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。”给出接口层的函数形态合同。两端一起表明该实现虽满足公开签名，仍需在指定 950/CANN 版本回退 LocalTensor 基础向量 API。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；选择显式包含 `simt_api/common_functions.h`，因为它同时解决类型别名与带线程维度的 `asc_vf_call` 重载可见性，机制闭环比只把调用点改成 `cce::dim3` 更完整。API 说明启动职责，runbook 给出混合 SIMD/SIMT 带线程维度重载的头文件前置条件与可复现编译信号。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；顶层函数继续保留 `__simd_vf__` 并由 `asc_vf_call` 进入；API 给出顶层 VF 启动，runbook 明确被启动入口与内部 `__simd_callee__` helper 的调用层级，能闭合编译器属性诊断。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；为每个 `asc_vf_call` 写出有效地址代数；调用前后的 offset 总和必须恰好出现一次。API 定义 VF 启动点，runbook 约束 wrapper 与 callee 的地址责任，可直接诊断多 chunk 从第二块开始错位。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 71 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 128 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/arch35/col2im_simt.h#L128)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 82 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_simt.h#L82)
- [DeformableConv2d 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 189 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/deformable_offsets/op_kernel/arch35/deformable_offsets.h#L189)
- [MoeInitRoutingV3 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/moe/moe_init_routing_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 195 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_init_routing_v3/op_kernel/arch35/moe_v3_expert_tokens_count.h#L195)
- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 154 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_simt_hw.h#L154)
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 425 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L425)
- [ForeachAcos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_acos_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 170 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h#L170)
- [MoeTokenPermuteWithRoutingMap 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/moe/moe_token_permute_with_routing_map_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 162 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute_with_routing_map/op_kernel/arch35/gather_v2_simt_two_dim.h#L162)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 157 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_simt_nchw.h#L157)
- [ConfusionTranspose 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/confusion_transpose_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_vf_call(...)` 的直接调用（第 268 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/transpose/op_kernel/arch35/transpose_small_shape.h#L268)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
