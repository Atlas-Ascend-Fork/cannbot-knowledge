---
type: API
title: DataCopyPad
description: 将数据从UB非对齐搬运至GM。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_data_copy_intf.h
---

# DataCopyPad（UBToGM非对齐数据搬运）<a name="ZH-CN_TOPIC_0000001894460401"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_data_copy_intf.h"`。

该接口提供将数据从Unified Buffer（UB）非对齐搬运至Global Memory的功能。

具体支持的数据通路为（以[逻辑位置TPosition](../../aux_data_structures/t_position.md)表示）：

- UB -> Global Memory
    - VECIN -> GM
    - VECOUT -> GM

- 如[图1](#fig_datacopypad3)所示，对于32字节对齐搬运场景，从UB读取的所有数据都会搬运至Global Memory。
- 如[图2](#fig_datacopypad4)所示，对于非32字节对齐的场景，在读取UB数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现UB到Global Memory的非对齐搬运。

## 函数原型<a name="section620mcpsimp"></a>

- 不支持配置设置数据搬运模式mode

    ```cpp
    template <typename T>
    __aicore__ inline void DataCopyPad(const GlobalTensor<T>& dst, const LocalTensor<T>& src, const DataCopyExtParams& dataCopyParams)
    ```



- 支持配置设置数据搬运模式mode（仅Ascend 950PR/Ascend 950DT支持）

    ```cpp
    // 该函数原型仅支持Ascend 950PR/Ascend 950DT
    template <typename T, PaddingMode mode = PaddingMode::Normal>
    __aicore__ inline void DataCopyPad(const GlobalTensor<T>& dst, const LocalTensor<T>& src, const DataCopyExtParams& dataCopyParams)
    ```



## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| :--- | :--- |
| T | 操作数的数据类型。各产品支持的数据类型请参考[数据类型](#section4219135304818)。 |
| mode | 配置数据搬运模式。PaddingMode类型，定义如下：<br>enum class PaddingMode : uint8_t {<br>    Normal = 0,  // 默认模式，与原有数据搬运格式保持一致，每次数据搬运都会补齐至32字节对齐<br>    Compact,     // 紧凑模式，允许单次搬运不对齐，统一在整块数据末尾补齐至32字节对齐<br>}; |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :---: | :--- |
| dst | 输出 | 目的操作数，类型为[GlobalTensor](../../data_structures/global_tensor/global_tensor_intro.md)。<br>起始地址无地址对齐约束。 |
| src | 输入 | 源操作数，类型为[LocalTensor](../../data_structures/local_tensor/local_tensor_intro.md)。<br>起始地址需要保证32字节对齐。 |
| dataCopyParams | 输入 | 搬运参数，DataCopyExtParams类型，具体参数说明请参考[表3](#table_ub2gm_pad_3)。 |

下文表格中列出的结构体参数定义请参考`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_data_copy.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。

**表3**  DataCopyExtParams结构体参数定义<a name="table_ub2gm_pad_3"></a>

| 参数名 | 描述 |
| :--- | :--- |
| blockCount | 指定该指令包含的连续传输数据块个数，数据类型为uint16_t，取值范围：blockCount∈[0, 4095]。 |
| blockLen | 指定该指令每个连续传输数据块长度，**该指令支持非对齐搬运**，**每个连续传输数据块长度单位为字节**。数据类型为uint32_t，取值范围：blockLen∈[0, 2097151]**，blockLen必须是sizeof(T)的整数倍，需要注意不要超过UB空间大小**。 |
| srcStride | 源操作数，相邻连续数据块的间隔（即前一个数据块**结束地址**与后一个数据块**起始地址**的差值）。<br>源操作数的逻辑位置为VECIN/VECOUT，单位为dataBlock（32字节）。<br>数据类型为uint32_t，取值范围为[0, 2^32-1]。不同产品中srcStride的数据类型和支持的取值范围可能不同，详细请参考[约束说明](#section633mcpsimp)。 |
| dstStride | 目的操作数，相邻连续数据块间的间隔（即前一个数据块**结束地址**与后一个数据块**起始地址**的差值）。<br>目的操作数的逻辑位置为GM，单位为字节。<br>数据类型为uint32_t，取值范围为[0, 2^32-1]。不同产品中dstStride的数据类型和支持的取值范围可能不同，详细请参考[约束说明](#section633mcpsimp)。 |
| rsv | 保留字段。 |

下面通过两个场景介绍UB到Global Memory的非对齐搬运，分别对应32字节对齐和非32字节对齐：

- 32字节对齐场景<a name="32字节对齐场景"></a>

    如[图1](#fig_datacopypad3)所示，blockLen为64，每个连续传输数据块包含64字节；srcStride为1，源操作数的逻辑位置为VECIN/VECOUT，srcStride的单位为dataBlock（32字节），即源操作数相邻数据块之间间隔1个dataBlock；dstStride为1，目的操作数的逻辑位置为GM，dstStride的单位为字节，即目的操作数相邻数据块之间间隔1字节。

    对于32字节对齐搬运场景，从UB读取的所有数据都会搬运至Global Memory。

    **图1**  blockLen为32字节对齐时UB到Global Memory的非对齐搬运示意图<a name="fig_datacopypad3"></a><br>
    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/datacopypad3.png)

- 非32字节对齐场景<a name="非32字节对齐场景"></a>

    如[图2](#fig_datacopypad4)所示，blockLen为47，每个连续传输数据块包含47字节，不满足32字节对齐；srcStride为1，表示源操作数相邻数据块之间间隔1个dataBlock；dstStride为1，表示目的操作数相邻数据块之间间隔1字节。

    对于非32字节对齐的场景，由于UB要求32字节对齐，框架在搬出时会自动补充17字节的假数据来保证对齐，搬到Global Memory时再自动将填充的假数据丢弃掉，从而实现UB到Global Memory的非对齐搬运。

    **图2**  blockLen不满足32字节对齐时UB到Global Memory的非对齐搬运示意图<a name="fig_datacopypad4"></a><br>
    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/datacopypad4.png)

## 数据类型<a name="section4219135304818"></a>



- Ascend 950PR/Ascend 950DT，支持的数据类型为：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、double、complex64。





- Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、double。





- Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、double。





- Atlas 200I/500 A2 推理产品，支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。



## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 位于UB的源地址必须32字节对齐，位于Global Memory的目的地址必须1字节对齐。
- DataCopyExtParams结构体参数的值需在取值范围内：

    **表4**  DataCopyExtParams结构体参数取值范围

    | 参数名 | 取值范围 |
    | --- | --- |
    | blockCount | [0, 4095] |
    | blockLen | [0, 2097151] |
    | srcStride | [0, 2^32 - 1] |
    | dstStride | [0, 2^32 - 1] |

    

    > [!NOTE]说明
    > 特别地，针对Ascend 950PR/Ascend 950DT，srcStride和dstStride的数据类型和取值范围如下：
    > - srcStride：数据类型为int64_t，取值范围为[0, 65535]。
    > - dstStride：数据类型为int64_t，取值范围为[0, 2^40-1]。

    


- 当DataCopyExtParams结构体参数blockCount、blockLen任意一个值为0时，该接口将被视为NOP（空操作）。该说明针对如下型号生效：
  
  - Atlas A3 训练系列产品/Atlas A3 推理系列产品
  
  
  - Atlas A2 训练系列产品/Atlas A2 推理系列产品
  
  
  - Ascend 950PR/Ascend 950DT
  


## 调用示例<a name="section177231425115410"></a>

```cpp
AscendC::DataCopyExtParams copyParams{1, dstTotalLength * sizeof(T), 0, 0, 0};
AscendC::DataCopyPad(dstGlobal, srcLocal, copyParams);
```

完整样例请参考[DataCopyPad样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/00_data_movement/data_copy_pad_gm2ub_ub2gm)。


<!-- cannbot:related:start -->
## 相关

- [DataCopyPad UB→GM 四参调用导致编译失败](../../../../../runbooks/compilation/datacopypad_ub_to_gm_has_no_pad_params.md)（`exemplifies`）：`GlobalTensor <- LocalTensor` 的 UB→GM `DataCopyPad`；将数据从UB非对齐搬运至GM。runbook 的四参编译失败与三参修复正是该 UB→GM API 的方向特定重载案例；API 方向合同可用于排除误套 GM→UB padding 参数。
- [DataCopyPad stride 表示 block 间隙](../../../../../runbooks/precision/datacopypad_stride_is_inter_block_gap.md)（`exemplifies`）：这里的 stride 字段是相邻 block 有效 payload 之间的额外 gap。DataCopyPad 已按硬件块粒度组织 UB 行；再写入 `padRowBytes-rowBytes` 会把对齐差重复计入地址推进。以有效字节数 `L`、对齐后行宽 `P` 为例，正确下一行地址是当前行起点加 `P`；错误配置又加 `(P-L)`，实际推进变成 `P+(P-L)`，因此从第二行开始访问错误位置。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。。runbook 同时修正 UB 到 GM 写回的多行 stride，API 卡明确非对齐写回时 dummy 对齐数据会被丢弃，说明不能再把补齐差重复计入 gap。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：`DataCopyPad` 的目标 `GlobalTensor<T>` 一律按元素偏移 `outputGm［dst_elem］` 索引；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。运行手册要求 UB→GM 输出使用 typed GlobalTensor 的元素偏移并匹配 LocalTensor 类型，API 卡给出该搬出方向的源/目的类型、对齐和 dummy 丢弃语义。
- [窄尾 tile 行距错位：补齐 UB gap](../../../../../runbooks/precision/datacopypad_narrow_tile_needs_explicit_ub_row_gap.md)（`exemplifies`）：分别在 GM→UB 的 `dstStride` 与 UB→GM 的 `srcStride` 中补上相同的 UB gap：；将数据从UB非对齐搬运至GM。。Runbook 的修复在 UB→GM 搬出端设置 srcStride，目标 API 卡确认该方向会丢弃对齐 dummy 数据，从而定位正确的 scatter 接口与源行距参数。
- [逐元素 DataCopyPad 做 strided gather 输出全零](../../../../../runbooks/precision/datacopypad_strided_gather.md)（`exemplifies`）：机制链：逐元素 `DataCopyPad` strided gather（1-元素 blockLen + `LocalTensor` 切片 dst）→ GM 值未有效落入写出路径读取的 UB → 写回 GM 全零。这不是"算式错"或"对齐越界"，而是"块搬运 DMA 被误用为元素级标量 gather"的语义不匹配。元素级 GM 读写应使用 `GlobalTensor.GetValue(offset)` / `GlobalTensor.SetValue(idx, val)`。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。。runbook 的全零信号在错误 GM→UB gather 后由 UB→GM 整片写回暴露，API 卡明确该后半段只是块写回，不能补救前半段未落入 UB 的元素。
- [DataCopyPad](data_copy_pad_gm_to_ub.md)（`same_topic`）：DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。。两端记录同一 DataCopyPad 非对齐搬运契约的 GM 到 UB 与 UB 到 GM 两个方向，联合阅读可按数据流方向选择入口并核对填充与丢弃 dummy 数据的差异。
<!-- cannbot:related:end -->
