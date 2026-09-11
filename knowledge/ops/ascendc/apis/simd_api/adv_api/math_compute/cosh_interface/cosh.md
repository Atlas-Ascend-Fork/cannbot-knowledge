---
type: API
title: Cosh
description: 按元素做双曲余弦函数计算
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cosh_interface/Cosh.md
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
- include/adv_api/math/cosh.h
---

# Cosh

## 功能说明

按元素做双曲余弦函数计算，计算公式如下：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002218334509.png)

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002222885545.png)

## 函数原型

-   通过sharedTmpBuffer入参传入临时空间
    -   源操作数Tensor全部/部分参与计算

        ```
        template <typename T, bool isReuseSource = false>
        __aicore__ inline void Cosh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)
        ```

    -   源操作数Tensor全部参与计算

        ```
        template <typename T, bool isReuseSource = false>
        __aicore__ inline void Cosh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer)
        ```

-   接口框架申请临时空间
    -   源操作数Tensor全部/部分参与计算

        ```
        template <typename T, bool isReuseSource = false>
        __aicore__ inline void Cosh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const uint32_t calCount)
        ```

    -   源操作数Tensor全部参与计算

        ```
        template <typename T, bool isReuseSource = false>
        __aicore__ inline void Cosh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor)
        ```

由于该接口的内部实现中涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。临时空间支持**接口框架申请**和开发者**通过sharedTmpBuffer入参传入**两种方式。

-   接口框架申请临时空间，开发者无需申请，但是需要预留临时空间的大小。

-   通过**sharedTmpBuffer**入参传入，使用该tensor作为临时空间进行处理，接口框架不再申请。该方式开发者可以自行管理**sharedTmpBuffer**内存空间，并在接口调用完成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较高。

接口框架申请的方式，开发者需要预留临时空间；通过**sharedTmpBuffer**传入的情况，开发者需要为tensor申请空间。临时空间大小BufferSize的获取方式如下：通过[GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)中提供的**GetCoshMaxMinTmpSize**接口获取需要预留空间大小的上下限。

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。支持的数据类型为：half、float。 |
| isReuseSource | 是否允许修改源操作数。该参数预留，传入默认值false即可。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstTensor | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。 |
| srcTensor | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| sharedTmpBuffer | 输入 | 临时缓存。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>临时空间大小BufferSize的获取方式请参考[GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)。 |
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
// 输入tensor长度为512,算子输入的数据类型为half,实际计算个数为256
AscendC::Cosh(dstLocal, srcLocal, sharedTmpBuffer, 256);
```

结果示例如下：

```
// 末尾使用三位特殊值验证
输入数据(srcLocal): [ 0.000000   0.010000  0.020000  ...  2.520000  -11.089000    0.000000  11.089000]
输出数据(dstLocal): [ 1.000000   1.000050  1.000200  ...  6.254528  32723.625000  1.000000  32723.625000]
```


<!-- cannbot:related:start -->
## 相关

- [GetCoshMaxMinTmpSize](get_cosh_max_min_tmp_size.md)（`related`）：Cosh 卡明确“临时空间大小通过GetCoshMaxMinTmpSize获取。”；Host Tiling 卡说明“host侧Tiling接口，用于获取Cosh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”，二者形成 Cosh 临时空间的 Host 计算到 Kernel 使用链，但主 API 的双曲余弦计算与 helper 的容量规划并非同一主题。
- [GetCoshTmpBufferFactorSize](get_cosh_tmp_buffer_factor_size.md)（`same_topic`）：“获取Cosh接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。”与“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCoshMaxMinTmpSize获取。”提供双方正文证据。factor 接口把固定可用缓冲换算为单次 Cosh 元素数，Cosh 卡给出显式 sharedTmpBuffer 与 calCount 重载；两端可共同确定分块大小和传入的计算元素数。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [ForeachCosh A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_cosh.md)（`related`）：算子正文包含对 `Cosh(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
