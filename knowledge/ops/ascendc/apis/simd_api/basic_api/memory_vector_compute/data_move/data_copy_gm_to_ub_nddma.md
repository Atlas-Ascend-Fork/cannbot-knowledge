---
type: API
title: DataCopy
description: 多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMToUB_NDDMA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# DataCopy

多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。

多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Global Memory -> Unified Buffer
    - GM -> VECIN


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。；dim：搬运的数据维度，数据类型为uint8_t，支持的维度为[1, 5]。；config：搬运配置选项，NdDmaConfig类型，定义如下，具体参数说明请参考[表3](#table_nddma_3)。 struct NdDmaConfig {     static constexpr uint16_t unsetPad = 0xffff;     bool isNearestValueMode = false;     uint16_t loopLpSize = unsetPad; // Left padding size of all dimensions, must be less than 256.     uint16_t loopRpSize = unsetPad; // Right padding size of all dimensions, must be less than 256.     bool ascOptimize = false;       // used for Ascend C optimization on special scenario. };；dst：输出 目的操作数，类型为LocalTensor。；src：输入 源操作数，类型为GlobalTensor。

约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。

<!-- cannbot:related:start -->
## 相关

- [NDDMA 快速路径 C=1 中间轴漏维判别](../../../../../runbooks/precision/nddma_c_1.md)（`exemplifies`）：“`chanStride_==1` 才是 channel 真末轴的可靠判据。”给出焦点端事实；“支持的维度为［1, 5］。”给出候选端事实。runbook 的失败来自用 C=1 误判 NDDMA 末轴布局，DataCopy NDDMA API 又把单个描述符限制为最多 5 维；两端共同约束何时能安全构造该快速搬运。
- [NDDMA 最内层 srcStride=0 广播读越界](../../../../../runbooks/precision/nddma_srcstride_0.md)（`exemplifies`）：1. **检查最内层 srcStride**：打印或断言 `nddmaParams_［IN_MASK］.loopInfo.loopSrcStride［0］`，若为 0 即命中本 bug。；多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。。该 runbook 用实际最内层 srcStride=0 广播失败验证了 DataCopy NDDMA 的维度与 Stride 配置边界，可直接指导参数探针和回退。
- [NDDMA多维dstStride致data搬运偏移的判别](../../../../../runbooks/precision/nddma_dststride_data.md)（`exemplifies`）：“约束：一条指令所能获取的所有数据的地址范围宽度不能超过40位（1TB），即：；源操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopSrcSize，目的操作数的每一次循环的大小为：(loopLpSize + loopSize + loopRpSize -1 ) * loopDstSize，所有的循环的大小加起来不超过2的40次方位。；当每层循环的dstStride为升序序列，则不同循环间的地址空间不能交织或者重叠。以一个2D Padding场景为例，loopSrcStride、loopDstStride第二个维度的stride值最小是3，数据3不能落在维度1的循环中。；该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。”与“NDDMA `nddma_out_to_ub_b32` 在 `RANK=4` 模板（ND=4，含 filler 维度）下、当**实际维度 ≥ 2** 时，`loopDstStride` 参数被硬件错误应用，导致 GM→UB 搬运后 UB 内 data 错位；1 维（仅一个实际维度）时 filler 不触发该路径，搬运正确。被诊断的 NDDMA 搬运机制单元（`CopyInBrcImpl`，RANK≤5 分支）：”。API 规定 dstStride 地址空间约束，Runbook 给出多维 dstStride 被错误应用时的错位诊断。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：“- **API 路径**：AscendC `DataCopy<T, dim, NdDmaConfig>`（GM→UB NDDMA）与 `DataCopyPad`（UB→GM 回写）；`NdDmaConfig` / `MultiCopyLoopInfo<dim>` / `DataCopyParams` / `DataCopyExtParams` 结构定义于 `asc/include/basic_api/kernel_struct_data_copy.h` 与 `kernel_operator_data_copy_intf.h`，arch35 实现于 `asc/impl/basic_api/dav_3510/kernel_operator_data_copy_impl.h`。”与“多维数据搬运接口，相比于基础数据搬运接口，可更加自由配置搬入的维度信息以及对应的Stride。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN”提供双方正文证据。runbook 在非对齐尾轴修复中实际采用 GM→UB 的 NDDMA DataCopy，并围绕 NdDmaConfig 配 padding；API 卡定义该多维搬入和 stride 合同。
- [NdDmaDci](../data_move_aux_config/nd_dma_dci.md)（`related`）：“刷新NDDMA DataCache，确保多核场景下DataCopy多维搬运前缓存数据为最新状态。”定义 NdDmaDci 是多核 DataCopy 前的缓存刷新动作；“该接口通过NDDMA进行数据搬运，对应的NDDMA Cache大小为32KB，在使用DataCopy接口进行数据搬运前，需要使用NdDmaDci接口刷新缓存，否则多核场景下读写同一块Global Memory地址可能会导致部分核读取数据错误。”在 GM→UB NDDMA 搬运页给出不刷新会读旧 GM 数据的失败条件。两端构成必须先 flush 再 DataCopy 的顺序合同。
<!-- cannbot:related:end -->
