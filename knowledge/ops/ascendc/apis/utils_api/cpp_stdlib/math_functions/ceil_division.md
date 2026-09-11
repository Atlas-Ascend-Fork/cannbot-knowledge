---
type: API
title: CeilDivision
description: 计算两个整数num1和num2相除后向上取整结果。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/CeilDivision.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# CeilDivision

## 功能说明

计算两个整数num1和num2相除后向上取整结果。

## 函数原型

```cpp
__aicore__ constexpr inline int32_t CeilDivision(int32_t num1, int32_t num2)
```

## 参数说明

**表1** 参数说明

| 参数名 | 描述 |
| --- | --- |
| num1 | 参数1，被除数。 |
| num2 | 参数2，除数。 |

## 返回值说明

两个整数相除的向上取整结果。

## 约束说明

- 当num2为0时，结果为0。
- 该接口仅支持在num1和num2为正数场景下使用。

## 调用示例

本示例中使用CeilDivision计算迭代次数repeatTimes，通过对数据量count与单次处理数据量进行向上取整除法，确保所有数据（包括尾块）均被完整处理。

```cpp
template <typename T>
__aicore__ inline void AddCustomImpl(__local_mem__ T *dst, __local_mem__ T *src0, __local_mem__ T *src1,
    uint32_t count)
{
    AscendC::Reg::RegTensor<T> srcReg0;
    AscendC::Reg::RegTensor<T> srcReg1;
    AscendC::Reg::RegTensor<T> dstReg;
    AscendC::Reg::MaskReg mask;
    constexpr uint32_t oneRepeatSize = AscendC::GetVecLen() / sizeof(T);
    uint16_t repeatTime = AscendC::CeilDivision(count, oneRepeatSize);
    for (uint16_t i = 0; i < repeatTime; ++i) {
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::LoadAlign(srcReg0, src0 + i * oneRepeatSize );
        AscendC::Reg::LoadAlign(srcReg1, src1 + i * oneRepeatSize );
        AscendC::Reg::Add(dstReg, srcReg0, srcReg1, mask);
        AscendC::Reg::StoreAlign(dst + i * oneRepeatSize, dstReg, mask);
    }
}
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Xlog1py 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/xlog1py_950.md)（`related`）：算子声明的固定版本源码包含对 `CeilDivision(...)` 的直接调用（第 231 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/xlog1py/op_kernel/arch35/xlog1py_kernel.h#L231)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `CeilDivision(...)` 的直接调用（第 181 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec.hpp#L181)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
