---
type: API
title: Lgamma
description: 按元素计算x的gamma函数的绝对值并求自然对数
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/Lgamma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
source_headers:
- include/adv_api/math/lgamma.h
---

# Lgamma

## 功能说明

按元素计算x的gamma函数的绝对值并求自然对数，计算公式如下：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002218495125.png)

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002188278974.png)

## 函数原型

-   通过sharedTmpBuffer入参传入临时空间

    ```
    template <typename T, bool isReuseSource = false>
    __aicore__ inline void Lgamma(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)
    ```

-   接口框架申请临时空间

    ```
    template <typename T, bool isReuseSource = false>
    __aicore__ inline void Lgamma(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const uint32_t calCount)
    ```

由于该接口的内部实现中涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。临时空间支持开发者**通过sharedTmpBuffer入参传入**和**接口框架申请**两种方式。

-   通过sharedTmpBuffer入参传入，使用该tensor作为临时空间进行处理，接口框架不再申请。该方式开发者可以自行管理sharedTmpBuffer内存空间，并在接口调用完成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较高。
-   接口框架申请临时空间，开发者无需申请，但是需要预留临时空间的大小。

通过sharedTmpBuffer传入的情况，开发者需要为tensor申请空间；接口框架申请的方式，开发者需要预留临时空间。临时空间大小BufferSize的获取方式如下：通过[6.1.55 Lgamma Tiling](get_lgamma_max_min_tmp_size.md)中提供的接口获取需要预留空间范围的大小。

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |
| isReuseSource | 是否允许修改源操作数，默认值为false。该参数仅在输入的数据类型为float时生效。<br><br>true：开发者允许源操作数被改写，可以设置该参数取值为true开启，开启后本接口内部计算时复用srcTensor的内存空间，节省部分内存空间；<br><br>false：本接口内部计算时不复用srcTensor的内存空间。<br><br>isReuseSource的使用样例请参考[更多样例](../more_examples.md#section639165323915)。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstTensor | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。 |
| srcTensor | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| sharedTmpBuffer | 输入 | 临时缓存。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>用于Lgamma内部复杂计算时存储中间变量，由开发者提供。<br><br>临时空间大小BufferSize的获取方式请参考[GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)。 |
| calCount | 输入 | 参与计算的元素个数。 |

## 返回值说明

无

## 约束说明

-   **不支持源操作数与目的操作数地址重叠。**
-   不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
-   操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。


-   针对Ascend 950PR/Ascend 950DT，接口内部计算对Subnormal的处理方式受编译选项`--cce-ftz`控制（默认值为`true`）：
    -   配置为`false`时，计算过程中保留Subnormal，并按照其实际数值参与后续计算。
    -   配置为`true`时，启用FTZ（Flush-To-Zero）模式，计算过程中产生或参与运算的Subnormal将按0处理，可能导致计算结果与保留Subnormal时存在精度差异。


## 调用示例

```
// dstLocal: 存放计算结果的Tensor
// srcLocal: 参与计算的输入Tensor
// sharedTmpBuffer: 临时缓存,内部复杂计算时存储中间变量
// 输入tensor长度为1024,算子输入的数据类型为half,实际计算个数为512
AscendC::Lgamma(dstLocal, srcLocal, sharedTmpBuffer, 512);
```

结果示例如下：

```
输入数据(srcLocal): [0.000000  0.010000  0.020000  0.030000  0.040000  ...]
输出数据(dstLocal): [inf       4.599480  3.900805  3.489971  3.197078  ...]
```


<!-- cannbot:related:start -->
## 相关

- [GetLgammaMaxMinTmpSize](get_lgamma_max_min_tmp_size.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。；host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。Lgamma 的 sharedTmpBuffer 重载消费 Host Tiling 接口给出的容量上下界，二者构成明确的临时空间生产与消费合同。
- [GetLgammaTmpBufferFactorSize](get_lgamma_tmp_buffer_factor_size.md)（`related`）：参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。。因子接口把可用 UB 反推成 Lgamma 可处理 shape，Lgamma 的手工临时空间重载正是该容量规划的消费端。
- [Lgammaf](../../../../simt_api/math_functions/float_math_functions/lgammaf.md)（`same_topic`）：功能：获取输入数据x伽马值的绝对值并求自然对数。；按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(｜gamma(x)｜)）。模板参数T支持half/float。两卡核心数学对象均为 lgamma，分别覆盖 SIMT 标量 float 与高阶 LocalTensor 逐元素接口。
<!-- cannbot:related:end -->
