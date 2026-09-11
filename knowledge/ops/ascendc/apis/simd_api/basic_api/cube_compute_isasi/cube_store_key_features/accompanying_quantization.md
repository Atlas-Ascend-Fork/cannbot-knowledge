---
type: API
title: AccompanyingQuantization
description: 矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/accompanying_quantization.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# 随路量化<a name="ZH-CN_TOPIC_0000002568950983"></a>

## 特性说明

矩阵计算的搬出过程中支持随路cast能力，cast mode为CAST\_RINT模式。当L0C Buffer为float数据类型，输出为half/bfloat16数据类型，可以通过设置**Fixpipe搬运参数结构体**中的quantPre参数开启，或设置**DataCopyCO12DstParams结构体参数**中的quantPre参数开启，无需配置额外寄存器。使用cast输出half需配置为QuantMode\_t::F322F16，使用cast输出bfloat16\_t需配置为QuantMode\_t::F322BF16。

同时矩阵计算的搬出过程中支持随路quant能力，当前支持两种模式的随路带参数的量化能力：

- 同一系数（Scalar）的量化模式：整个C矩阵对应一个量化参数，量化参数的shape为\[1\]。可以通过设置quantPre参数，配置为对应的量化类型，若使用DataCopy实现矩阵搬出需要调用[SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)接口来设置scalar量化参数，其中scalar量化参数QUANT\_PRE为uint64\_t类型，低32位表示的是float类型的量化系数（硬件以\(1, 8, 10\)的格式进行计算，即1个符号位、8个指数位和10个尾数位，4B），量化参数QUANT\_PRE具体含义参见[表1](#zh-cn_topic_0000002547300781_table1273124313613)。
- 向量（Tensor/Vector）的量化模式：C矩阵的shape为\[m, n\]，每个channel维度即C矩阵的每一列，对应一个量化参数，量化参数的shape为\[n\]。可以通过设置quantPre参数，配置为对应的量化类型，若使用DataCopy实现矩阵搬出需要调用[SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)来设置tensor量化参数地址Quant\_PRE\_ADDR，其中tensor量化参数需要通过DataCopy从L1 Buffer搬运至Fixpipe Buffer。其中每个量化参数Quant\_PRE\_ADDR\[i\]为uint64\_t类型（i为列索引），低32位表示的是float类型的量化系数（硬件以\(1, 8, 10\)的格式进行计算，即1个符号位、8个指数位和10个尾数位，4B）。量化参数Quant\_PRE\_ADDR\[i\]具体含义参见[表1](#zh-cn_topic_0000002547300781_table1273124313613)。

当前支持的量化模式及其功能描述如下：

```text
DEQF16,                // DeQuant_Float16：int32_t反量化成half，scalar量化
VDEQF16,               // Vector_DeQuant_Float16：int32_t反量化成half，tensor量化
QF322B8_PRE,           // Quant_Float32_2_B8：float量化成int8_t/uint8_t，scalar量化
VQF322B8_PRE,          // Vector_Quant_Float32_2_B8：float量化成int8_t/uint8_t，tensor量化
REQ8,                  // ReQuant_int8：int32_t重量化成int8_t/uint8_t，scalar量化
VREQ8,                 // Vector_ReQuant_int8：int32_t重量化成int8_t/uint8_t，tensor量化
```

除上述量化模式外，Ascend 950PR/Ascend 950DT产品还额外支持以下量化模式：

```text
QF322FP8_PRE,          // Quant_Float32_2_FP8: float量化成fp8_e4m3fn_t，scalar量化
VQF322FP8_PRE,         // Vector_Quant_Float32_2_FP8: float量化成fp8_e4m3fn_t，tensor量化
QF322HIF8_PRE,         // Quant_Float32_2_HIF8: float量化成hifloat8_t(Half to Away Round)，scalar量化
VQF322HIF8_PRE,        // Vector_Quant_Float32_2_HIF8: float量化成hifloat8_t(Half to Away Round)，tensor量化
QF322HIF8_PRE_HYBRID,  // Quant_Float32_2_HIF8_Hybrid: float量化成hifloat8_t(Hybrid Round)，scalar量化
VQF322HIF8_PRE_HYBRID, // Vector_Quant_Float32_2_HIF8_Hybrid: float量化成hifloat8_t(Hybrid Round)，tensor量化
QS322BF16_PRE,         // Quant_Int32_2_BFloat16: int32_t量化成bfloat16_t，scalar量化
VQS322BF16_PRE,        // Vector_Quant_Int32_2_BFloat16: int32_t量化成bfloat16_t，tensor量化
QF322F16_PRE,          // Quant_Float32_2_Float16: float量化成half，scalar量化
VQF322F16_PRE,         // Vector_Quant_Float32_2_Float16: float量化成half，tensor量化
QF322BF16_PRE,         // Quant_Float32_2_BFloat16: float量化成bfloat16_t，scalar量化
VQF322BF16_PRE,        // Vector_Quant_Float32_2_BFloat16: float量化成bfloat16_t，tensor量化
QF322F32_PRE,          // Quant_Float32_2_Float32: float量化成float，scalar量化，精度可以达到双千分之一,无法达到双万分之一
VQF322F32_PRE,         // Vector_Quant_Float32_2_Float32: float量化成float，tensor量化，精度可以达到双千分之一,无法达到双万分之一
```


不同量化模式的量化算法详细介绍参见[随路量化与随路ReLU场景组合](accompanying_quantization_and_relu_scenario_combination.md)。


量化参数比特位含义见下表：


**表1** 量化参数QUANT\_PRE比特位含义映射表（[NPU架构版本2201](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md)）<a id="zh-cn_topic_0000002547300781_table1273124313613"></a>

| 模式 | 比特位数 | 变量名 | 作用介绍 |
| ------ | ---------- | -------- | ---------- |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 0~31 | M1 | 32位数视为float，硬件以(1, 8, 10)的格式，即1个符号位、8个指数位和10个尾数位作为量化计算所需要乘的值。其中31位为符号位，23~30位为指数位，13~22位为尾数位。 |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 32~35 | N | 4位比特位，表示范围为\[1, 16\]（b'0000对应表示1，b'1111对应表示16）。<br>当模式为(V)REQ8时，MCB标志位置为1时，将输入的值进行右移N比特位。当模式为(V)QF322B8_PRE，N为无效变量。 |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 36 | MCB标志位 | Mode Control Bit。如果置为0，输入的int32_t会被直接转换为float，N为无效值。如果置为1，输入的int32_t会先右移N比特位，转变成int16_t，然后转换为float。当模式为(V)QF322B8_PRE时，此标志位为无效比特。 |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 37~45 | Offset | 9bit的整型数据，源数据乘以量化系数或者随路系数的计算结果，可以与Offset表示的整数值进行相加。若不使用offset，请置为0。<br>当模式为(V)DEQF16时，此变量为无效变量。 |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 46 | Sign标志位 | 如果置为1，表明量化结果是signed(int8)；如果置为0，表明量化结果是unsigned(uint8)。仅在(V)REQ8、(V)QF322B8_PRE中会用到。 |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16 | 47~63 | - | 无效比特位，用户无需关注。 |



**表2** 量化参数QUANT\_PRE比特位含义映射表（[NPU架构版本3510](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md)）<a id="zh-cn_topic_0000002547300781_table1273124313714"></a>

| 模式 | 比特位数 | 变量名 | 作用介绍 |
| --- | --- | --- | --- |
| &bull;(V)REQ8<br>&bull;(V)QF322B8_PRE<br>&bull;(V)DEQF16<br>&bull;(V)QF322FP8_PRE<br>&bull;(V)QF322HIF8_PRE<br>&bull;(V)QF322HIF8_PRE_HYBRID<br>&bull;(V)QS322BF16_PRE<br>&bull;(V)QF322F16_PRE<br>&bull;(V)QF322BF16_PRE<br>&bull;(V)QF322F32_PRE | 0~12 | - | 无效比特位，用户无需关注。 |
| 同第一行 | 13~31 | M1 | 数据类型视为float，硬件以(1, 8, 10)的格式，即1个符号位、8个指数位和10个尾数位作为量化计算所需要乘的值。其中31位为符号位，23~30位为指数位，13~22位为尾数位。其值不能为inf/nan。 |
| 同第一行 | 32~36 | - | 无效比特位，用户无需关注。 |
| 同第一行 | 37~45 | Offset | 9bit整形数据，源数据乘以量化系数或者随路系数的计算结果，可以与Offset表示的整数值进行相加。若不使用offset，请置为0。当模式为(V)REQ8、(V)QF322B8_PRE时该变量生效。 |
| 同第一行 | 46 | Sign标志位 | 如果置为1，表明量化结果是signed(int8)；如果为置为0，表明量化结果是unsigned(uint8)。仅在(V)REQ8、(V)QF322B8_PRE中会用到。 |
| 同第一行 | 47~63 | - | 无效比特位，用户无需关注。 |



## 使用示例

完整样例请参考[fixpipe\_l0c2gm样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/03_matrix_compute/fixpipe_l0c2gm)。


<!-- cannbot:related:start -->
## 相关

- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：矩阵搬出过程中支持随路 cast 和 quant 能力。Cast 模式（CAST_RINT）：L0C float 输出 half 配 F322F16，输出 bfloat16_t 配 F322BF16，无需额外寄存器。Quant 模式分两种：Scalar 量化（整个 C 矩阵一个参数，shape［1］，通过 SetFixpipePreQuantFlag 设置 QUANT_PRE，uint64_t 低 32 位 float（1,8,10 格式））；Tensor 量化（每列一个参数，shape［n］，通过 SetFixPipeConfig 设置 Quant_PRE_ADDR，需从 L1 搬运至 Fixpipe Buffer）。；数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。。特性卡定义矩阵搬出的随路 cast/quant，L0C 到 GM 的 DataCopy 卡给出可达模式及必须配套的量化寄存器。
- [SetFixpipePreQuantFlag](../cube_store_aux_config/set_fixpipe_pre_quant_flag.md)（`related`）：DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 scalar 量化时，设置 scalar 量化参数。此参数代表整个输出矩阵使用的单一量化参数。；矩阵搬出过程中支持随路 cast 和 quant 能力。Cast 模式（CAST_RINT）：L0C float 输出 half 配 F322F16，输出 bfloat16_t 配 F322BF16，无需额外寄存器。Quant 模式分两种：Scalar 量化（整个 C 矩阵一个参数，shape［1］，通过 SetFixpipePreQuantFlag 设置 QUANT_PRE，uint64_t 低 32 位 float（1,8,10 格式））；Tensor 量化（每列一个参数，shape［n］，通过 SetFixPipeConfig 设置 Quant_PRE_ADDR，需从 L1 搬运至 Fixpipe Buffer）。。配置接口写入整个矩阵共用的 scalar 量化参数，特性卡明确该参数属于 Scalar 随路量化模式。
<!-- cannbot:related:end -->
