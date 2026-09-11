---
type: API
title: Power（数学计算）
description: 实现按元素做幂运算功能，提供3类接口，处理逻辑如下： ! !
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Power_interface/Power.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# Power

## 功能说明

实现按元素做幂运算功能，提供3类接口，处理逻辑如下：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002218328733.png)

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002192030526.png)

## 函数原型

-   Power\(dstTensor, src0Tensor, src1Tensor\)
    -   通过sharedTmpBuffer入参传入临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const LocalTensor<T>& src1Tensor, const LocalTensor<uint8_t>& sharedTmpBuffer, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const LocalTensor<T>& src1Tensor, const LocalTensor<uint8_t>& sharedTmpBuffer)
            ```

    -   接口框架申请临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const LocalTensor<T>& src1Tensor, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const LocalTensor<T>& src1Tensor)
            ```

-   Power\(dstTensor, src0Tensor, src1Scalar\)
    -   通过sharedTmpBuffer入参传入临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const T& src1Scalar, const LocalTensor<uint8_t>& sharedTmpBuffer, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const T& src1Scalar, const LocalTensor<uint8_t>& sharedTmpBuffer)
            ```

    -   接口框架申请临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const T& src1Scalar, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const LocalTensor<T>& src0Tensor, const T& src1Scalar)
            ```

-   Power\(dstTensor, src0Scalar, src1Tensor\)
    -   通过sharedTmpBuffer入参传入临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const T& src0Scalar, const LocalTensor<T>& src1Tensor, const LocalTensor<uint8_t>& sharedTmpBuffer, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const T& src0Scalar, const LocalTensor<T>& src1Tensor, const LocalTensor<uint8_t>& sharedTmpBuffer)
            ```

    -   接口框架申请临时空间
        -   源操作数Tensor全部/部分参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const T& src0Scalar, const LocalTensor<T>& src1Tensor, uint32_t calCount)
            ```

        -   源操作数Tensor全部参与计算

            ```
            template <typename T, bool isReuseSource = false, const PowerConfig& config = defaultPowerConfig>
            __aicore__ inline void Power(const LocalTensor<T>& dstTensor, const T& src0Scalar, const LocalTensor<T>& src1Tensor)
            ```

由于该接口的内部实现中涉及复杂的数学计算，需要额外的临时空间来存储计算过程中的中间变量。临时空间支持**接口框架申请**和开发者**通过sharedTmpBuffer入参传入**两种方式。

-   接口框架申请临时空间，开发者无需申请，但是需要预留临时空间的大小。

-   通过sharedTmpBuffer入参传入，使用该tensor作为临时空间进行处理，接口框架不再申请。该方式开发者可以自行管理sharedTmpBuffer内存空间，并在接口调用完成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较高。

接口框架申请的方式，开发者需要预留临时空间；通过sharedTmpBuffer传入的情况，开发者需要为sharedTmpBuffer申请空间。临时空间大小BufferSize的获取方式如下：通过[GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)中提供的GetPowerMaxMinTmpSize接口获取需要预留空间的范围大小。

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数的数据类型。不同型号支持的数据类型请参考[支持的数据类型](#li559613463410)。 |
| isReuseSource | 是否允许修改源操作数。该参数预留，传入默认值false即可。 |
| config | Power计算的相关配置。此参数可选配，PowerConfig类型，具体定义如下方代码所示，其中参数的含义为：<br>algo：不同的数据类型支持的不同Power算法。该参数支持的取值如下：INTRINSIC：默认值。如果数据类型是整型，INTRINSIC算法使用快速幂算法实现Power计算，支持的数据类型为uint8_t、int8_t、uint16_t、int16_t、uint32_t、int32_t。如果数据类型是浮点数类型，INTRINSIC算法按照公式Power(x, y) = exp(y * ln(x))进行Power计算，支持的数据类型为half、float。DOUBLE_FLOAT_TECH：DOUBLE_FLOAT_TECH算法是高精度浮点数算法，将源操作数的精度提升后，按照公式Power(x, y) = exp(y * ln(x))进行Power计算，减少计算过程中的精度损失，支持的数据类型为bfloat16_t、half、float。 |

```
enum class PowerAlgo {
    INTRINSIC = 0,
    DOUBLE_FLOAT_TECH,
};

struct PowerConfig {
    PowerAlgo algo = PowerAlgo::INTRINSIC;
};
```

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstTensor | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。 |
| src0Tensor | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| src1Tensor | 输入 | 源操作数。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>源操作数的数据类型需要与目的操作数保持一致。 |
| src0Scalar/src1Scalar | 输入 | 源操作数，类型为Scalar。源操作数的数据类型需要与目的操作数保持一致。 |
| sharedTmpBuffer | 输入 | 临时内存空间。<br><br>类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>针对3个power接口，不同输入数据类型情况下，临时空间大小BufferSize的获取方式请参考[GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)。 |
| calCount | 输入 | 参与计算的元素个数。 |

## 返回值说明

无

## 约束说明

- **不支持源操作数与目的操作数地址重叠。**

-   对于Atlas 推理系列产品AI Core，幂运算的指数必须小于2<sup>31</sup>-1。

-   操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。
-   支持的数据类型<a id="li559613463410"></a>

    
    Ascend 950PR/Ascend 950DT，支持的数据类型为：uint8\_t、int8\_t、uint16\_t、int16\_t、uint32\_t、int32\_t、half、bfloat16\_t、float。
    
    
    Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：half、float、int32\_t。
    
    
    Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：half、float、int32\_t。
    
    
    Atlas 推理系列产品AI Core，支持的数据类型为：half、float、int32\_t。
    


-   针对Ascend 950PR/Ascend 950DT，接口内部计算对Subnormal的处理方式受编译选项`--cce-ftz`控制（默认值为`true`）：
    -   配置为`false`时，计算过程中保留Subnormal，并按照其实际数值参与后续计算。
    -   配置为`true`时，启用FTZ（Flush-To-Zero）模式，计算过程中产生或参与运算的Subnormal将按0处理，可能导致计算结果与保留Subnormal时存在精度差异。


## 调用示例

完整的调用样例请参考[Power样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/04_advanced_api/10_math/power)。

```
// dstLocal: 存放计算结果的Tensor
// srcLocalExp: Power计算使用的指数Tensor
// srcLocalBase: Power计算使用的底数Tensor

// 使用srcLocalBase做底数对srcLocalExp中的全部元素做幂运算
AscendC::Power<T, false>(dstLocal, srcLocalBase, srcLocalExp);

// scalarValueBase: Power计算使用的底数
T scalarValueBase = srcLocalBase.GetValue(0);
// 使用同一个底数scalarValueBase对srcLocalExp中的全部元素做幂运算
AscendC::Power<T, false>(dstLocal, scalarValueBase, srcLocalExp);

// scalarValueExp: Power计算使用的指数
T scalarValueExp = srcLocalExp.GetValue(0);
// 使用同一个指数scalarValueExp对srcLocalBase中的全部元素做幂运算
AscendC::Power<T, false>(dstLocal, srcLocalBase, scalarValueExp);

// static constexpr AscendC::PowerConfig config = { AscendC::PowerAlgo::DOUBLE_FLOAT_TECH };
// AscendC::Power<srcType, false, config>(dstLocal, scalarValue, srcLocal2);
```

AscendC::Power<T, false\>\(dstLocal, srcLocalBase, srcLocalExp\)示例数据如下：

```
输入数据(srcLocalBase): [2 3 4 5 6 7 8 9]
输入数据(srcLocalExp): [4 3 2 1 4 3 2 1]
输出数据(dstLocal): [16 27 16 5 1296 343 64 9]
```

AscendC::Power<T, false\>\(dstLocal, scalarValueBase, srcLocalExp\)示例数据如下：

```
输入数据(scalarValueBase): 2
输入数据(srcLocalExp): [4 3 2 1 4 3 2 1]
输出数据(dstLocal): [16 8 4 2 16 8 4 2]
```

AscendC::Power<T, false\>\(dstLocal, srcLocalBase, scalarValueExp\)示例数据如下：

```
输入数据(srcLocalBase): [2 3 4 5 6 7 8 9]
输入数据(scalarValueExp): 4
输出数据(dstLocal): [16 81 256 625 1296 2401 4096 6561]
```


<!-- cannbot:related:start -->
## 相关

- [ApplyAdamW A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_adam_w.md)（`related`）：“每个模板在 `Init` 中读取单元素 `step`、绑定本核 GM基址、初始化 Queue/TBuf、每核只计算一次两个 bias correction”需要幂运算形成 beta 的 step 次方，“按元素做幂运算（dst = src0 ^ src1）”提供可对照的 Power 计算合同。
- [ForeachPowScalar A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_scalar.md)（`related`）：`Power<half,false>`，公共 unary foreach；按元素做幂运算（dst = src0 ^ src1），提供三类接口：Power(dstTensor, src0Tensor, src1Tensor)两个Tensor输入、Power(dstTensor, src0Tensor, src1Scalar)Tensor+标量、Power(dstTensor, src0Scalar, src1Tensor)标量+Tensor。；候选是 A2/A3 foreach FP16/FP32 tile 的直接数学 primitive。
- [ForeachPowScalarList A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_scalar_list.md)（`related`）：ForeachPowScalarList 的 Device 语义是“Kernel 调用 `Power<T,false>` 计算 `y_i［j］=x_i［j］^{e_i}`。”；Power 页定义“按元素做幂运算（dst = src0 ^ src1）”并提供 Tensor+标量重载，后者是每个列表元素 tile 的直接计算原语。
- [GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)（`related`）：“临时空间大小通过GetPowerMaxMinTmpSize获取。”在 Power 调用契约中指定 sizing 入口；“在minValue到maxValue范围内，临时空间越大性能越好。”说明该入口返回区间内的性能取舍。
- [GetPowerTmpBufferFactorSize](get_power_tmp_buffer_factor_size.md)（`related`）：“currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize”从固定 UB 预算反推单次元素数；“临时空间大小通过GetPowerMaxMinTmpSize获取。”说明 Power kernel 的另一种显式临时空间获取入口，两者构成 host 分块与 kernel 调用的选型链。
- [InplacePowTensorScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/inplace_pow_tensor_scalar_950.md)（`related`）：otherwise -> Power<T,false,{INTRINSIC}>(x,T(e),len)；模板参数isReuseSource预留，传false；config为PowerConfig类型，其中algo指定算法：INTRINSIC（默认，整型使用快速幂算法支持uint8_t/int8_t/uint16_t/int16_t/uint32_t/int32_t，浮点型按exp(y*ln(x))计算支持half/float）或DOUBLE_FLOAT_TECH（高精度浮点算法，精度提升后按exp(y*ln(x))计算减少精度损失，支持bfloat16_t/half/float）。；候选给出整数通用指数分支所调用的 Power 算法合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [InplaceExp2 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/inplace_exp2_950.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 236 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/pow/op_kernel/arch35/pow_tensor_scalar_float.h#L236)
- [ForeachPowList A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_list.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 43 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_pow_list/op_kernel/foreach_pow_list.h#L43)
- [PowTensorTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/pow_tensor_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 236 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/pow/op_kernel/arch35/pow_tensor_scalar_float.h#L236)
- [ForeachPowScalarAndTensor A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_scalar_and_tensor.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 39 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_pow_scalar_and_tensor/op_kernel/foreach_pow_scalar_and_tensor.h#L39)
- [ApplyAdamWQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_adam_w_quant.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 81 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/optim/apply_adam_w_quant/op_kernel/apply_adam_w_quant_base.h#L81)
- [ApplyFusedEmaAdam A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_fused_ema_adam.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 95 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/optim/apply_fused_ema_adam/op_kernel/apply_fused_ema_adam_base.h#L95)
- [ApplyFusedEmaAdam 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_fused_ema_adam_950.md)（`related`）：算子声明的固定版本源码包含对 `Power(...)` 的直接调用（第 95 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/optim/apply_fused_ema_adam/op_kernel/apply_fused_ema_adam_base.h#L95)

### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [InplacePowTensorTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/inplace_pow_tensor_tensor_950.md)（`related`）：算子正文包含对 `Power(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
