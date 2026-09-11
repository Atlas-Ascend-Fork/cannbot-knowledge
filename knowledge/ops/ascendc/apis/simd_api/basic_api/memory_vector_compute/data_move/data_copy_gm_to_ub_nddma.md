---
type: API
title: DataCopy
description: 多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMToUB_NDDMA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_operator_data_copy_intf.h
---

# DataCopy（GMToUB多维数据搬运NDDMA）<a name="ZH-CN_TOPIC_0000002544407954"></a>

## 功能说明<a name="section474617392321"></a>

头文件路径为：`"basic_api/kernel_operator_data_copy_intf.h"`。

多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。

具体支持的数据通路为（以[逻辑位置TPosition](../../aux_data_structures/t_position.md)表示）：

- Global Memory -> UB
    - GM -> VECIN

## 函数原型<a name="section1954364615315"></a>

- Global Memory -> UB，支持多维度搬运

    ```cpp
    template <typename T, uint8_t dim, const NdDmaConfig& config = kDefaultNdDmaConfig>
    __aicore__ inline void DataCopy(const LocalTensor<T>& dst, const GlobalTensor<T>& src, const NdDmaParams<T, dim>& params)
    ```

- NDDMA Cache刷新，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新NDDMA Cache缓存保证为最新状态。

    ```cpp
    __aicore__ inline void NdDmaDci()
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| :--- | :--- |
| T | 源操作数或者目的操作数的数据类型。 |
| dim | 搬运的数据维度，数据类型为uint8_t，支持的维度为[1, 5]。 |
| config | 搬运配置选项，NdDmaConfig类型，定义如下，具体参数说明请参考[表3](#table_nddma_3)。<br>struct NdDmaConfig {<br>    static constexpr uint16_t unsetPad = 0xffff;<br>    bool isNearestValueMode = false;<br>    uint16_t loopLpSize = unsetPad; // Left padding size of all dimensions, must be less than 256.<br>    uint16_t loopRpSize = unsetPad; // Right padding size of all dimensions, must be less than 256.<br>    bool ascOptimize = false;       // used for Ascend C optimization on special scenario.<br>}; |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :---: | :--- |
| dst | 输出 | 目的操作数，类型为[LocalTensor](../../data_structures/local_tensor/local_tensor_intro.md)。 |
| src | 输入 | 源操作数，类型为[GlobalTensor](../../data_structures/global_tensor/global_tensor_intro.md)。 |
| params | 输入 | 搬运参数NdDmaParams类型，定义如下，具体参数说明请参考[表4](#table_nddma_4)。<br>template &lt;typename T, uint8_t dim&gt;<br>struct NdDmaParams  {<br>    NdDmaLoopInfo&lt;dim&gt; loopInfo;<br>    T constantValue;  // 若有左右Padding，且不使能NearestValueMode时，该值将作为Padding值填充。<br>};<br>NdDmaLoopInfo类型，定义如下，具体参数说明请参考[表5](#table_nddma_5)。<br>template &lt;uint8_t dim&gt;<br>struct NdDmaLoopInfo  {<br>    uint64_t loopSrcStride[dim] = {0}; // src stride info per loop.<br>    uint32_t loopDstStride[dim] = {0}; // dst stride info per loop.<br>    uint32_t loopSize[dim] = {0}; // Loop size per loop.<br>    uint8_t loopLpSize[dim] = {0}; // Left padding size per loop.<br>    uint8_t loopRpSize[dim] = {0}; // Right padding size per loop.<br>};<br>// 注意：dim的有效范围为[1,5]。 |

**表3**  NdDmaConfig结构体参数定义<a name="table_nddma_3"></a>

| 参数名 | 描述 |
| :--- | :--- |
| unsetPad | 表示未在NdDmaConfig中统一设置PaddingSize，固定为0xFFFF，为uint16_t数据类型的常量。当loopLpSize或loopRpSize取该值时，对应的PaddingSize由NdDmaLoopInfo中的同名参数按维度设置。 |
| isNearestValueMode | 表示Padding值填取方式，类型为bool。<br>true：使能最近值填充方式，即左右Padding值会选取当前维度最左或最右的值进行填充，可参考[图1](#fig10722115123919)。<br>false：使能常数填充方式，即所有Padding值填充为固定值NdDmaParams::constantValue。<br>当数据类型为b64时，参数isNearestValueMode的值应为false。 |
| loopLpSize | 所有维度统一使用的左Padding大小，单位为元素个数。取值范围为[0, 255]或unsetPad，默认值为unsetPad。设置为[0, 255]时，所有维度均使用该值，NdDmaLoopInfo::loopLpSize不生效；设置为unsetPad时，按维度使用NdDmaLoopInfo::loopLpSize。 |
| loopRpSize | 所有维度统一使用的右Padding大小，单位为元素个数。取值范围为[0, 255]或unsetPad，默认值为unsetPad。设置为[0, 255]时，所有维度均使用该值，NdDmaLoopInfo::loopRpSize不生效；设置为unsetPad时，按维度使用NdDmaLoopInfo::loopRpSize。 |
| ascOptimize | 预留参数，暂不支持。 |

**表4**  NdDmaParams结构体参数定义<a name="table_nddma_4"></a>

| 参数名 | 描述 |
| :--- | :--- |
| loopInfo | 每维进行搬运的信息，类型为NdDmaLoopInfo&lt;dim&gt;。<br>NdDmaLoopInfo结构中数组类型参数的元素个数由模板参数dim决定。dim的取值范围为[1, 5]，数组的有效索引范围为[0, dim - 1]。具体参数介绍可参考[表5](#table_nddma_5)。 |
| constantValue | 数据类型为T的数值，当存在维度左右Padding，且不使能NearestValueMode时，该值将作为Padding值填充。<br>当数据类型为b64时，参数constantValue的值应为0。 |

**表5**  NdDmaLoopInfo结构体参数定义<a name="table_nddma_5"></a>

| 参数名 | 描述 |
| :--- | :--- |
| loopSrcStride | 表示每个维度内，该源操作数元素与下一个元素间的间隔。<br>单位为元素个数。数据类型为uint64_t，loopSrcStride需在[0, 2<sup>40</sup>)。 |
| loopDstStride | 表示每个维度内，该目的操作数元素与下一个元素间的间隔。<br>单位为元素个数。数据类型为uint32_t，loopDstStride需在[0, 2<sup>20</sup>)。 |
| loopSize | 表示每个维度内，处理的元素个数（不包含Padding元素）。<br>单位为元素个数。数据类型为uint32_t，loopSize需在[1, 2<sup>20</sup>)。 |
| loopLpSize | 表示每个维度内，左侧需要补齐的元素个数。<br>单位为元素个数。数据类型为uint8_t，loopLpSize不要超出该数据类型的取值范围：[0, 255]。 |
| loopRpSize | 表示每个维度内，右侧需要补齐的元素个数。<br>单位为元素个数。数据类型为uint8_t，loopRpSize不要超出该数据类型的取值范围：[0, 255]。 |

以下以2维的例子介绍几个典型使用场景。

**图1**  2D Padding场景<a name="fig10722115123919"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/2d_padding_scenario.png "2D-Padding场景")

**图2**  2D Transpose场景<a name="fig104451143104510"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/2d_transpose_scenario.png "2D-Transpose场景")

**图3**  2D BroadCast场景<a name="fig4654326132913"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/2d_broadcast_scenario.png "2D-BroadCast场景")

**图4**  2D Slice场景<a name="fig13061435132915"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/2d_slice_scenario.png "2D-Slice场景")

## 数据类型

源操作数和目的操作数支持的数据类型保持一致。


Ascend 950PR/Ascend 950DT支持的数据类型为：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、double、complex64。


## 返回值说明<a name="section7607175220218"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：

    源操作数的每一次循环的大小为：\(loopLpSize + loopSize + loopRpSize -1 \) \* loopSrcSize，目的操作数的每一次循环的大小为：\(loopLpSize + loopSize + loopRpSize -1 \) \* loopDstSize，所有的循环的大小加起来不超过2的40次方位。

- 当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。

    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/nddma_padding_2d.png)

- 该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。

## 调用示例<a name="section122101199486"></a>

- 场景1：2D Padding场景，常数填充方式

    ```cpp
    // xGmShape：[16, 32]，搬运8列2行数据，左Padding 15，上Padding 13，右Padding 17，下Padding 3，xLocalShape：[32, 64]。
    AscendC::NdDmaLoopInfo<2> loopInfo{{1, 32}, {1, 64}, {32, 16}, {15, 13}, {17, 3}};
    AscendC::NdDmaParams<T, 2> params{loopInfo, 0};  // padding的值为0
    AscendC::NdDmaDci();  // 刷新cache
    static constexpr AscendC::NdDmaConfig dmaConfig;  // 使用默认参数，也可以不传。
    AscendC::DataCopy<T, 2, dmaConfig>(xLocal, xGm, params);
    ```

- 场景2：2D Padding场景，最近值填充方式

    ```cpp
    // xGmShape：[28, 15]，搬运3列4行数据，左Padding 11，上Padding 3，右Padding 6，下Padding 1，xLocalShape：[32, 32]。
    AscendC::NdDmaLoopInfo<2> loopInfo{{1, 15}, {1, 32}, {15, 28}, {11, 3}, {6, 1}};
    AscendC::NdDmaParams<T, 2> params{loopInfo, 0};
    AscendC::NdDmaDci();  // 刷新cache
    // isNearestValueMode = true左右Padding值会选取当前维度最左或最右的值进行填充。
    static constexpr AscendC::NdDmaConfig dmaConfig = {true};
    AscendC::DataCopy<T, 2, dmaConfig>(xLocal, xGm, params);
    ```

- 场景3：2D Transpose场景

    ```cpp
    // xGmShape：[16, 64]，搬运8列4行数据，xLocalShape：[64, 16]。
    AscendC::NdDmaLoopInfo<2> loopInfo{{1, 64}, {16, 1}, {64, 16}, {0, 0}, {0, 0}};
    AscendC::NdDmaParams<T, 2> params{loopInfo, 0};
    AscendC::NdDmaDci();  // 刷新cache
    static constexpr AscendC::NdDmaConfig dmaConfig;  // 使用默认参数，也可以不传。
    AscendC::DataCopy<T, 2, dmaConfig>(xLocal, xGm, params);
    ```

- 场景4：2D BroadCast场景

    ```cpp
    // xGmShape：[1, 16]，搬运16列1行数据并进行广播，xLocalShape：[3, 16]。
    AscendC::NdDmaLoopInfo<2> loopInfo{{1, 0}, {1, 16}, {16, 3}, {0, 0}, {0, 0}};
    AscendC::NdDmaParams<T, 2> params{loopInfo, 0};
    AscendC::NdDmaDci();  // 刷新cache
    static constexpr AscendC::NdDmaConfig dmaConfig;  // 使用默认参数，也可以不传。
    AscendC::DataCopy<T, 2, dmaConfig>(xLocal, xGm, params);
    ```

- 场景5：2D Slice场景

    ```cpp
    // xGmShape：[32, 64]，将16*10的矩阵截取为一个5*7的矩阵，xLocalShape：[16, 16]。
    AscendC::NdDmaLoopInfo<2> loopInfo{{1, 64}, {1, 16}, {16, 16}, {0, 0}, {0, 0}};
    AscendC::NdDmaParams<T, 2> params{loopInfo, 0};
    AscendC::NdDmaDci();  // 刷新cache
    static constexpr AscendC::NdDmaConfig dmaConfig;  // 使用默认参数，也可以不传。
    AscendC::DataCopy<T, 2, dmaConfig>(xLocal, xGm, params);
    ```

完整样例请参考：[多维数据搬运样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/00_data_movement/data_copy_gm2ub_nddma)。


<!-- cannbot:related:start -->
## 相关

- [NDDMA 快速路径 C=1 中间轴漏维判别](../../../../../runbooks/precision/nddma_c_1.md)（`exemplifies`）：“`chanStride_==1` 才是 channel 真末轴的可靠判据。”给出焦点端事实；“支持的维度为［1, 5］。”给出候选端事实。runbook 的失败来自用 C=1 误判 NDDMA 末轴布局，DataCopy NDDMA API 又把单个描述符限制为最多 5 维；两端共同约束何时能安全构造该快速搬运。
- [NDDMA 最内层 srcStride=0 广播读越界](../../../../../runbooks/precision/nddma_srcstride_0.md)（`exemplifies`）：1. **检查最内层 srcStride**：打印或断言 `nddmaParams_［IN_MASK］.loopInfo.loopSrcStride［0］`，若为 0 即命中本 bug。；多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。。该 runbook 用实际最内层 srcStride=0 广播失败验证了 DataCopy NDDMA 的维度与 Stride 配置边界，可直接指导参数探针和回退。
- [NDDMA多维dstStride致data搬运偏移的判别](../../../../../runbooks/precision/nddma_dststride_data.md)（`exemplifies`）：“约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。”与“NDDMA `nddma_out_to_ub_b32` 在 `RANK=4` 模板（ND=4，含 filler 维度）下、当**实际维度 ≥ 2** 时，`loopDstStride` 参数被硬件错误应用，导致 GM→UB 搬运后 UB 内 data 错位；1 维（仅一个实际维度）时 filler 不触发该路径，搬运正确。被诊断的 NDDMA 搬运机制单元（`CopyInBrcImpl`，RANK≤5 分支）：”。API 规定 dstStride 地址空间约束，Runbook 给出多维 dstStride 被错误应用时的错位诊断。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：“- **API 路径**：AscendC `DataCopy<T, dim, NdDmaConfig>`（GM→UB NDDMA）与 `DataCopyPad`（UB→GM 回写）；`NdDmaConfig` / `MultiCopyLoopInfo<dim>` / `DataCopyParams` / `DataCopyExtParams` 结构定义于 `asc/include/basic_api/kernel_struct_data_copy.h` 与 `kernel_operator_data_copy_intf.h`，arch35 实现于 `asc/impl/basic_api/dav_3510/kernel_operator_data_copy_impl.h`。”与“多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN”提供双方正文证据。runbook 在非对齐尾轴修复中实际采用 GM→UB 的 NDDMA DataCopy，并围绕 NdDmaConfig 配 padding；API 卡定义该多维搬入和 stride 合同。
- [NdDmaDci](../data_move_aux_config/nd_dma_dci.md)（`related`）：“刷新NDDMA DataCache，确保多核场景下DataCopy多维搬运前缓存数据为最新状态。”定义 NdDmaDci 是多核 DataCopy 前的缓存刷新动作；“该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。”在 GM→UB NDDMA 搬运页给出不刷新会读旧 GM 数据的失败条件。两端构成必须先 flush 再 DataCopy 的顺序合同。
<!-- cannbot:related:end -->
