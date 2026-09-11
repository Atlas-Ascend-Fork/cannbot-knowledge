---
type: API
title: Trap
description: Kernel侧调试接口，NPU模式下中断AI Core运行，CPU模式下等同于assert，用于异常场景调试。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.debugging
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/Trap.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# Trap<a name="ZH-CN_TOPIC_0000001834672609"></a>

## 功能说明<a name="section259105813316"></a>

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

在核函数（Kernel）侧调用，NPU模式下会中断AI Core的运行，CPU模式下等同于assert。可用于核函数（Kernel）侧异常场景的调试。

## 函数原型<a name="section2067518173415"></a>

```cpp
__aicore__ inline void Trap()
```

## 参数说明<a name="section158061867342"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section43265506459"></a>

无

## 调用示例<a name="section82241477610"></a>

```cpp
AscendC::LocalTensor<half> src0Local;
AscendC::LocalTensor<half> src1Local;
AscendC::LocalTensor<half> dstLocal;
constexpr int32_t count = 512;    // 参与计算的元素个数。
if (src1Local[0] == 0) {    // 如果src1Local[0]为0，则程序终止。
    AscendC::Trap();
} else {
    AscendC::Divs(dstLocal, src0Local, src1Local[0], count);
}
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [GroupQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/group_quant.md)（`related`）：算子声明的固定版本源码包含对 `Trap(...)` 的直接调用（第 256 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/group_quant/op_kernel/group_quant_base.h#L256)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
