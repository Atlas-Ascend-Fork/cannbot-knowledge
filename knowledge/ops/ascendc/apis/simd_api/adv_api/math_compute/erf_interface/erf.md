---
type: API
title: Erf
description: 按元素做误差函数计算，也称为高斯误差函数
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/Erf.md
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
---

# Erf

## 功能说明

按元素做误差函数计算（也称为高斯误差函数，error function or Gauss error function）。计算公式如下：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002327668200.png)

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002188205638.png)

## 函数原型

-   通过sharedTmpBuffer入参传入临时空间
    -   源操作数Tensor全部/部分参与计算

        ```
        template <typename T, bool isReuseSource = false, const ErfConfig& config = defaultErfConfig>
        __aicore__ inline void Erf(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)
        ```

    -   源操作数Tensor全部参与计算

        ```
        template <typename T, bool isReuseSource = false, const ErfConfig& config = defaultErfConfig>
        __aicore__ inline void Erf( const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer)
        ```

-   接口框架申请临时空间
    -   源操作数Tensor全部/部分参与计算

        ```
        template <typename T, bool isReuseSource = false, const ErfConfig& config = defaultErfConfig>
        __aicore__ inline void Erf(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const uint32_t calCount)
        ```

    -   源操作数Tensor全部参与计算

        ```
        template <typename T, bool isReuseSource = false, const ErfConfig& config = defaultErfConfig>
        __aicore__ inline void Erf(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor)
        ```

由于该接口的内部实现中涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。临时空间支持开发者**通过sharedTmpBuffer入参传入**和**接口框架申请**两种方式。

-   通过sharedTmpBuffer入参传入，使用该tensor作为临时空间进行处理，接口框架不再申请。该方式开发者可以自行管理sharedTmpBuffer内存空间，并在接口调用完成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较高。
-   接口框架申请临时空间，开发者无需申请，但是需要预留临时空间的大小。

通过sharedTmpBuffer传入的情况，开发者需要为tensor申请空间；接口框架申请的方式，开发者需要预留临时空间。临时空间大小BufferSize的获取方式如下：通过[GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)接口获取需要预留空间范围的大小。

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |
| isReuseSource | 是否允许修改源操作数。该参数预留，传入默认值false即可。 |
| config | Erf算法的相关配置，此参数可选配，ErfConfig类型，具体定义如下方代码所示，其中参数的含义为：<br>algo：Erf内部实现使用的算法。ErfAlgo类型，支持的取值如下：PADE_APPROXIMATION：默认值，高性能算法。该算法通过帕德近似算法实现Erf接口。SUBSECTION_POLYNOMIAL_APPROXIMATION：高精度算法。该算法通过将数值分段，采用不同的系数对分段的数据进行多项式逼近，以实现Erf接口。 |

```
enum class ErfAlgo {
    PADE_APPROXIMATION = 0,
    SUBSECTION_POLYNOMIAL_APPROXIMATION,
};

struct ErfConfig {
    ErfAlgo algo = ErfAlgo::PADE_APPROXIMATION;
};
```

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstTensor | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。 |
| srcTensor | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| sharedTmpBuffer | 输入 | 临时缓存。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>临时空间大小BufferSize的获取方式请参考[GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)。 |
| calCount | 输入 | 参与计算的元素个数。 |

## 返回值说明

无

## 约束说明

-   **不支持源操作数与目的操作数地址重叠。**

-   操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。


-   针对Ascend 950PR/Ascend 950DT，接口内部计算对Subnormal的处理方式受编译选项`--cce-ftz`控制（默认值为`true`）：
    -   配置为`false`时，计算过程中保留Subnormal，并按照其实际数值参与后续计算。
    -   配置为`true`时，启用FTZ（Flush-To-Zero）模式，计算过程中产生或参与运算的Subnormal将按0处理，可能导致计算结果与保留Subnormal时存在精度差异。


## 调用示例

完整的调用样例请参考[Erf样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/04_advanced_api/10_math/erf)。

```
// dstLocal: 存放计算结果的Tensor
// srcLocal: 参与计算的输入Tensor
AscendC::Erf<srcType, false>(dstLocal, srcLocal);
// algo：Erf内部使用的算法，默认为高性能算法。此处algo为高精度算法
// static constexpr AscendC::ErfAlgo algo = AscendC::ErfAlgo::SUBSECTION_POLYNOMIAL_APPROXIMATION;
// static constexpr AscendC::ErfConfig config = { algo };
// AscendC::Erf<srcType, false，config>(dstLocal, srcLocal);
```

结果示例如下：

```
输入数据(srcLocal): [2.015634   -2.3880906 -0.2151161  ... -2.5       0. 2.5      ]
输出数据(dstLocal): [0.99563545 -0.999268  -0.23903976 ... -0.9995931 0. 0.9995931]
```


<!-- cannbot:related:start -->
## 相关

- [ForeachErf A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erf.md)（`related`）：焦点算子路线明确为“R-002 FLOAT32 直接 `Erf<float,false>`”，候选 API 的计算合同是“按元素做误差函数计算（高斯误差函数，error function）。”；该 primitive 是 ForeachErf FLOAT32 Device 路线的直接计算节点。
- [GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取Erf接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”与“临时空间大小通过GetErfMaxMinTmpSize获取。”是双方正文中的具体合同。Tiling 卡说明如何取得最大最小临时空间，Erf 计算卡明确把该接口作为 workspace 尺寸来源，二者组成 Host 估算到 Kernel 调用的前置链。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。”。factor 接口反推可计算元素规模，Erf 接口消费 sharedTmpBuffer 和 calCount，构成 Tiling 到计算调用的直接合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [GeluMul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_mul.md)（`related`）：算子声明的固定版本源码包含对 `Erf(...)` 的直接调用（第 240 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_mul/op_kernel/gelu_mul.h#L240)
- [GeluMul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_mul_950.md)（`related`）：算子声明的固定版本源码包含对 `Erf(...)` 的直接调用（第 240 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_mul/op_kernel/gelu_mul.h#L240)
- [Gelu 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/activation/gelu_950.md)（`related`）：算子声明的固定版本源码包含对 `Erf(...)` 的直接调用（第 34 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_v2/op_kernel/arch35/gelu_v2_dag.h#L34)

### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [GeGlu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/ge_glu_950.md)（`related`）：算子正文包含对 `Erf(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
