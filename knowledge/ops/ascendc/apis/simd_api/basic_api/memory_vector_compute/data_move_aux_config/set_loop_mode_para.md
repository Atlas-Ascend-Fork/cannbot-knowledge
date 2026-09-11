---
type: API
title: SetLoopModePara
description: 使能并设置DataCopy/DataCopyPad的loop mode参数，支持GM与UB之间的双向数据搬运循环模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/SetLoopModePara.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_operator_data_copy_intf.h
---

# SetLoopModePara<a name="ZH-CN_TOPIC_0000002414107833"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_data_copy_intf.h"`。

DataCopy、DataCopyPad过程中通过该接口使能loop mode并且设置loop mode的参数，在数据搬运结束后通过[ResetLoopModePara](reset_loop_mode_para.md)重置loop mode的参数。

具体支持的数据通路为（以[逻辑位置TPosition](../../aux_data_structures/t_position.md)表示）：

- Global Memory -> UB
    - GM -> VECIN
- UB -> Global Memory
    - VECOUT -> GM

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetLoopModePara(const LoopModeParams& loopParams, DataCopyMVType type)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| loopParams | 输入 | 循环模式参数LoopModeParams类型，定义如下，具体参数说明请参考[表2](#table_setloop_2)。<br>struct LoopModeParams {<br>        loop1Size = 0;<br>        loop2Size = 0;<br>        loop1SrcStride = 0;<br>        loop1DstStride = 0;<br>        loop2SrcStride = 0;<br>        loop2DstStride = 0 ;<br>}; |
| type | 输入 | 数据搬运模式。DataCopyMVType为枚举类型，定义如下，具体参数说明请参考[表3](#table1166074612214)。<br>enum class DataCopyMVType : uint8_t {<br>    UB_TO_OUT = 0,<br>    OUT_TO_UB = 1,<br>}; |

**表2**  LoopModeParams结构体参数说明<a name="table_setloop_2"></a>

| 参数名 | 描述 |
| --- | --- |
| loop1Size | 用于设置内层循环的循环次数，数据类型为uint32_t，取值范围为[0, 2^21)。 |
| loop2Size | 用于设置外层循环的循环次数，数据类型为uint32_t，取值范围为[0, 2^21)。 |
| loop1SrcStride | 用于设置内层循环中相邻迭代源操作数的数据块间的间隔，单位为字节，数据类型为uint64_t。<br>&bull;当数据搬运模式是UB_TO_OUT的时候取值范围为[0, 2^21)，并且loop1SrcStride必须32字节对齐。<br>&bull;当数据搬运模式是OUT_TO_UB的时候取值范围为[0, 2^40)。 |
| loop1DstStride | 用于设置内层循环中相邻迭代目的操作数的数据块间的间隔，单位为字节，数据类型为uint64_t。<br>&bull;当数据搬运模式是UB_TO_OUT的时候取值范围为[0, 2^40)。<br>&bull;当数据搬运模式是OUT_TO_UB的时候取值范围为[0, 2^21)，并且loop1DstStride必须32字节对齐。 |
| loop2SrcStride | 用于设置外层循环中相邻迭代源操作数的数据块间的间隔，单位为字节，数据类型为uint64_t。<br>&bull;当数据搬运模式是UB_TO_OUT的时候取值范围为[0, 2^21)，并且loop2SrcStride必须32字节对齐。<br>&bull;当数据搬运模式是OUT_TO_UB的时候取值范围为[0, 2^40)。 |
| loop2DstStride | 用于设置外层循环中相邻迭代目的操作数的数据块间的间隔，单位为字节，数据类型为uint64_t。<br>&bull;当数据搬运模式是UB_TO_OUT的时候取值范围为[0, 2^40)。<br>&bull;当数据搬运模式是OUT_TO_UB的时候取值范围为[0, 2^21)，并且loop2DstStride必须32字节对齐。 |

**表3**  DataCopyMVType结构体参数说明 <a name="table1166074612214"></a>

| 参数名 | 描述 |
| --- | --- |
| UB_TO_OUT | 从UB搬运到GM的通路。 |
| OUT_TO_UB | 从GM搬运到UB的通路。 |

下面的样例呈现了SetLoopModePara的使用方法。

- 样例中在数据类型为int8\_t的场景下，数据块大小为384，配置DataCopyPad的数据搬运模式为Compact模式，blockLen = 48，blockCount = 2，表明每个连续传输数据块包含48字节，且连续传输数据块有两个，srcStride = 0，dstStride = 0，isPad = false，表明源操作数相邻数据块之间没有间隔且不需要填充用户自定义的数据；
- 再设置SetLoopModePara中LoopModeParams的参数：loop1Size = 2，loop2Size = 2，loop1SrcStride = 96，loop2SrcStride =192，loop1DstStride = 128，loop2DstStride = 288，DataCopyMVType为OUT\_TO\_UB，表明内层循环和外层循环的次数分别为2次，内层循环和外层循环中相邻迭代源操作数的数据块间隔分别为96字节和192字节，内层循环和外层循环中相邻迭代目的操作数的数据块间隔分别为128字节和288字节，通路是从GM搬运到Unified Buffer（UB）；
- 使用以上配置，调用SetLoopModePara再调用DataCopyPad就可以开启DataCopyPad的loop模式完成数据类型为int8\_t的数据块大小为384的数据搬运。详细图解如下：

**图1**  源操作数搬运场景示例<a name="fig6671114911311"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/source_operand_transfer_scenario.png "源操作数搬运场景示例")

**图2**  目的操作数搬运场景示例<a name="fig226181311513"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/destination_operand_transfer_scenario.png "目的操作数搬运场景示例")

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 源操作数和目的操作数的起始地址需要保证32字节对齐。
- 目的操作数的数据不能重叠，如果有重叠，硬件层面不会报错或者告警，同时也不能保证重叠数据的正确性；但是不同迭代可以交织，例如内层循环中相邻迭代目的操作数的数据块间的间隔可以小于相邻连续目的操作数的数据块的间隔。
- 需要在每次使能loop mode并且设置loop mode的参数后通过ResetLoopModePara进行寄存器的复位，否则会影响到下一次对应通路的搬运的使用，引发异常。

## 调用示例<a name="section1227835243314"></a>

- SetLoopModePara使能loop mode，Compact模式

    ```cpp
    // 场景4：使用SetLoopModePara使能loop mode进行数据搬运（仅支持Ascend 950PR/Ascend 950DT）。
    // Compact模式：每次内层循环搬运80B后填充16B使其96字节对齐。
    // padding值设为-1。
    AscendC::DataCopyExtParams copyParams{BLOCK_COUNT, BLOCK_LEN, 0, 0, 0};
    AscendC::DataCopyPadExtParams<T> padParams{true, 0, 0, -1};

    AscendC::LoopModeParams loopParam2Ub {LOOP1_SIZE, LOOP2_SIZE, LOOP1_SRC_STRIDE, LOOP1_DST_STRIDE, LOOP2_SRC_STRIDE, LOOP2_DST_STRIDE};
    AscendC::SetLoopModePara(loopParam2Ub, AscendC::DataCopyMVType::OUT_TO_UB);
    AscendC::DataCopyPad<int8_t, AscendC::PaddingMode::Compact>(srcLocal, srcGlobal, copyParams, padParams);
    AscendC::ResetLoopModePara(AscendC::DataCopyMVType::OUT_TO_UB);
    ```

- SetLoopModePara使能loop mode，Normal模式

    ```cpp
    // 场景5：使用SetLoopModePara使能loop mode进行数据搬运（仅支持Ascend 950PR/Ascend 950DT）。
    // Normal模式：每个block搬运40B后填充24B使其64字节对齐。
    // padding值设为-1。
    AscendC::DataCopyExtParams copyParams{BLOCK_COUNT, BLOCK_LEN, 0, 0, 0};
    AscendC::DataCopyPadExtParams<T> padParams{true, 0, 0, -1};

    AscendC::LoopModeParams loopParam2Ub {LOOP1_SIZE, LOOP2_SIZE, LOOP1_SRC_STRIDE, LOOP1_DST_STRIDE, LOOP2_SRC_STRIDE, LOOP2_DST_STRIDE};
    AscendC::SetLoopModePara(loopParam2Ub, AscendC::DataCopyMVType::OUT_TO_UB);
    AscendC::DataCopyPad<int8_t>(srcLocal, srcGlobal, copyParams, padParams);
    AscendC::ResetLoopModePara(AscendC::DataCopyMVType::OUT_TO_UB);
    ```

- 五维数据搬运

    ```cpp
    // 场景6：五维数据搬运GM[2, 4, 3, 128, 126]int8 -> UB[512, 128]int8。
    // Normal模式，使用loop mode。
    // 搬运规格：[2, 2, 2, 64, 126]，每个126字节补2字节padding到128字节。
    // 最终UB连续存放为[512, 128]。

    // Stride参数说明：
    // - loop1SrcStride=128*126：第2维stride，每次loop1源地址跳过128*126字节
    // - loop1DstStride=64*128：每次loop1目的地址跳过64*128字节（64行×128字节/行）
    // - loop2SrcStride=3*128*126：第1维stride，每次loop2源地址跳过3*128*126字节
    // - loop2DstStride=2*64*128：每次loop2目的地址跳过2*64*128字节

    AscendC::LoopModeParams loopParam2Ub {
        2,  // loop1Size=2（第2维搬运2次）
        2,  // loop2Size=2（第1维搬运2次）
        128 * 126,  // loop1SrcStride（第2维stride）
        64 * 128,   // loop1DstStride
        3 * 128 * 126,  // loop2SrcStride（第1维stride）
        2 * 64 * 128    // loop2DstStride
    };
    AscendC::SetLoopModePara(loopParam2Ub, AscendC::DataCopyMVType::OUT_TO_UB);

    AscendC::DataCopyExtParams copyParams{
        64,  // blockCount=64（第3维搬运64次）
        126,  // blockLen=126（第4维搬运126字节，padding到128）
        0, 0, 0  // srcStride=0, dstStride=0, rsv=0
    };
    AscendC::DataCopyPadExtParams<int8_t> padParams{true, 0, 0, 0};

    // 第0维for循环搬运2次。
    for (uint32_t dim0 = 0; dim0 < 2; dim0++) {
        constexpr uint32_t dim0SrcStride = 4 * 3 * 128 * 126;  // 第0维源stride
        constexpr uint32_t dim0DstStride = 2 * 2 * 64 * 128;   // 第0维目的stride
        uint32_t srcOffset = dim0 * dim0SrcStride;
        uint32_t dstOffset = dim0 * dim0DstStride;

        AscendC::DataCopyPad<int8_t>(srcLocal[dstOffset], srcGlobal[srcOffset], copyParams, padParams);
    }

    AscendC::ResetLoopModePara(AscendC::DataCopyMVType::OUT_TO_UB);
    ```

完整样例请参考[DataCopyPad样例场景4、5、6](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/00_data_movement/data_copy_pad_gm2ub_ub2gm)。


<!-- cannbot:related:start -->
## 相关

- [ResetLoopModePara](reset_loop_mode_para.md)（`related`）：重置loop mode参数，与SetLoopModePara搭配使用，在使能loop mode的数据搬运结束后调用。；约束：与SetLoopModePara搭配使用。在使能loop mode并完成数据搬运后，必须调用该接口重置loop mode参数，否则会影响下一次对应通路的数据搬运，引发异常。。SetLoopModePara 使能循环，ResetLoopModePara 在同次搬运后复位，构成必须配对的生命周期。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 33 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 135 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nchw.h#L135)
- [ConfusionTranspose 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/confusion_transpose_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 301 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/transpose/op_kernel/arch35/transpose_cut_one_axis.h#L301)
- [LogSoftmaxBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/log_softmax_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 226 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/log_softmax_grad/op_kernel/arch35/log_softmax_grad_ara_full_load.h#L226)
- [ApplyRotaryPosEmb 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/apply_rotary_pos_emb_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 259 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/posembedding/apply_rotary_pos_emb/op_kernel/arch35/apply_rotary_pos_emb_aba_and_ba.h#L259)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 110 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_point_copy.h#L110)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 257 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_normal.h#L257)
- [SoftmaxBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/softmax_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 225 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/softmax_grad/op_kernel/arch35/softmax_grad_ara_full_load.h#L225)
- [GridSampler3D 950 Direct Invoke 算子知识](../../../../../operators/direct/cv/image/grid_sampler_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 301 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/transpose/op_kernel/arch35/transpose_cut_one_axis.h#L301)
- [ReplicationPad2d 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/replication_pad_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 230 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_normal_w.h#L230)
- [Embedding 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/embedding_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoopModePara(...)` 的直接调用（第 524 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_v2/op_kernel/arch35/gather_v2_ga_all_load.h#L524)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
