---
type: API
title: SetFixPipeConfig
description: DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeConfig.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- kirin_x90
- kirin_9030
---

# SetFixPipeConfig<a name="ZH-CN_TOPIC_0000002538231208"></a>

## 功能说明<a name="zh-cn_topic_0000002547729135_section618mcpsimp"></a>

DataCopy数据搬运（[L0C Buffer->GM](../cube_compute_store/fixpipe_l0_c_to_gm.md)、[L0C Buffer->L1 Buffer](../cube_compute_store/fixpipe_l0_c_to_l1.md)）过程中进行随路量化时，通过调用该接口设置量化的参数。

## 函数原型<a name="zh-cn_topic_0000002547729135_section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void SetFixPipeConfig(const LocalTensor<T>& reluPre, const LocalTensor<T>& quantPre, bool isUnitFlag = false)

template <typename T, bool setRelu = false>
__aicore__ inline void SetFixPipeConfig(const LocalTensor<T>& preData, bool isUnitFlag = false)
```

## 参数说明<a name="zh-cn_topic_0000002547729135_section622mcpsimp"></a>

**表1** 模板参数说明

| 参数名 | 描述 |
| ---------- | ---------- |
| T | 操作数的数据类型。 |
| setRelu | 针对设置一个tensor的情况，setRelu当前仅支持设置为false，即只支持设置随路quantPre系数。 |

**表2** 参数说明

| 参数名称 | 输入/输出 | 含义 |
| ---------- | ---------- | ---------- |
| reluPre | 输入 | 源操作数，ReLU操作时参与计算的tensor，类型为LocalTensor，支持的物理内存为Fixpipe Buffer（TPosition为C2PIPE2GM），为后续的功能扩展做保留，传入一个空LocalTensor即可。 |
| quantPre | 输入 | 源操作数，quant tensor，量化操作时参与计算的tensor，类型为LocalTensor，支持的物理内存为Fixpipe Buffer（TPosition为C2PIPE2GM）。 |
| isUnitFlag | 输入 | unitFlag清空标志位，类型为bool。如果设为true，L0C Buffer中所有内存块的单元标志位都会设为0。旨在消除之前操作中unitFlag产生的多余影响。 |
| preData | 输入 | 支持设置一个tensor，通过开关控制是ReLU tensor还是Quant tensor，支持的物理内存为Fixpipe Buffer（TPosition为C2PIPE2GM）。当前仅支持传入quant tensor。对于单独设置unitFlag清空标志位isUnitFlag的场景，支持的物理地址为L0C Buffer（TPosition设置为CO1）。 |

## 数据类型

支持的数据类型为：uint64_t。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="zh-cn_topic_0000002547729135_section633mcpsimp"></a>

quantPre和reluPre必须是Fixpipe Buffer上的tensor。

## 调用示例<a name="section642mcpsimp"></a>

完整示例可参考[data_copy_l0c2gm](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/00_data_movement/data_copy_l0c2gm)。

```cpp
__aicore__ inline void SetFPC(const LocalTensor <int32_t>& reluPreTensor, const LocalTensor <int32_t>& quantPreTensor)
{
 
    AscendC::LocalTensor<uint64_t> workA1 = inQueueDeqA1.AllocTensor<uint64_t>();
    uint16_t deqSize = 128; // deq tensor的size
    AscendC::DataCopy(workA1, deqGlobal, deqSize); // deqGlobal为量化系数的gm地址
    AscendC::LocalTensor<uint64_t> deqFB = inQueueDeqFB.AllocTensor<uint64_t>(); // deq tensor在Fix上的地址
    uint16_t fbufBurstLen = deqSize / 128;  // l1->fix, burst_len unit is 128Bytes
    AscendC::DataCopyParams dataCopyParams(1, fbufBurstLen, 0, 0);
    AscendC::DataCopy(deqFB, workA1, dataCopyParams); // 通过DataCopy搬入C2PIPE2GM。
    AscendC::SetFixPipeConfig(deqFB); // 设置量化tensor
    AscendC::PipeBarrier<PIPE_FIX>();
}
```


<!-- cannbot:related:start -->
## 相关

- [DataCopyL0CToGM](../cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。量化模式含 NoQuant、F322F16、F322BF16、DEQF16、VDEQF16、QF322B8_PRE、VQF322B8_PRE、REQ8、VREQ8，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag / SetFixpipeNz2ndFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”把 tensor 量化模式的寄存器前置配置列为必需步骤；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。”定义 SetFixPipeConfig 正是 L0C→GM tensor 量化参数的生产接口。该边直接支撑量化 DataCopy 的正确调用顺序。
- [DataCopyL0CToL1](../cube_compute_store/data_copy_l0_c_to_l1.md)（`related`）：“数据类型：float→{int8_t,uint8_t,half,bfloat16_t,float}，int32_t→{int8_t,uint8_t,half,int32_t}。F322F16/F322BF16 为 Cast 模式，DEQF16/VDEQF16/REQ8/VREQ8 等为 scalar/tensor 量化，需配合 SetFixPipeConfig / SetFixpipePreQuantFlag 设置寄存器；Atlas 200I/500 A2 还支持 SetFixPipeClipRelu、SetFixPipeAddr。”要求 L0C→L1 的 tensor 量化先设置 FixPipe 寄存器；“DataCopy 数据搬运（L0C Buffer→GM、L0C Buffer→L1 Buffer）过程中进行随路 tensor 量化时，设置量化参数。”定义 SetFixPipeConfig 覆盖该通路的 tensor 参数。该边直接用于校验量化搬出的前置调用。
<!-- cannbot:related:end -->
