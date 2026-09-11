---
type: API
title: LogicalOr
description: 按元素进行或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOr_interface/LogicalOr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/adv_api/math/logical_or.h
---

# LogicalOr

## 功能说明

按元素进行或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002386255958.png)

## 函数原型

```
template <const LogicalOrConfig& config = DEFAULT_LOGICAL_OR_CONFIG, typename T, typename U>
__aicore__ inline void LogicalOr(const LocalTensor<T>& dst, const LocalTensor<U>& src0, const LocalTensor<U>& src1, const uint32_t count)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| config | LogicalOr算法的相关配置。此参数可选配，LogicalOrConfig类型，具体定义如下方代码所示，其中参数的含义为：<br><br>isReuseSource：该参数预留，传入默认值false即可。 |
| T | 目的操作数的数据类型。支持的数据类型为：bool。 |
| U | 源操作数的数据类型。支持的数据类型为：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。 |

```
struct LogicalOrConfig {
    bool isReuseSource;
};
```

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dst | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。 |
| src0、src1 | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型与目的操作数保持一致。 |
| count | 输入 | 参与计算的元素个数。 |

## 返回值说明

无

## 约束说明

-   **不支持源操作数与目的操作数地址重叠。**
-   操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。

## 调用示例

```
AscendC::LocalTensor<bool> dst;
AscendC::LocalTensor<half> src0, src1;
uint32_t count = 512; // 参与计算的元素个数
AscendC::LogicalOr(dst, src0, src1, count);
```

结果示例如下：

```
输入数据（src0）:
[1, 2, 0, -1, -2, 0, 3, 4, 0, -3, -4, 0, 5, 6, 0, -5, -6, 0, ... 0]
输入数据（src1）:
[1, 0, 0, -1, 0, 0, 3, 0, 0, -3, 0, 0, 5, 0, 0, -5, 0, 0, ... 0]
输出数据（dst）:
[ True,  True,  False,  True,  True,  False,  True,  True,  False,  True,
  True,  False,  True,  True,  False,  True,  True,  False,  ...  False]
```


<!-- cannbot:related:start -->
## 相关

- [BitwiseOrTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/bitwise_or_tensor_950.md)（`related`）：若 `P=BOOL`，源码改提交 `LogicalOr`；零视为False，非零视为True；算子 BOOL Route 直接切换到 LogicalOr 语义。
- [GetLogicalOrTmpBufferFactorSize](get_logical_or_tmp_buffer_factor_size.md)（`related`）：获取LogicalOr接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素进行逻辑或操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。。FactorSize 的输出专门用于规划 LogicalOr 单次计算量，LogicalOr 页定义被规划的 Kernel 运算及平台范围。
- [GetLogicalOrMaxMinTmpSize](get_logical_or_max_min_tmp_size.md)（`same_topic`）：获取LogicalOr接口所需的最大和最小临时空间大小；按元素进行逻辑或操作；连接 Host 临时空间生产与 Kernel 计算。
<!-- cannbot:related:end -->
