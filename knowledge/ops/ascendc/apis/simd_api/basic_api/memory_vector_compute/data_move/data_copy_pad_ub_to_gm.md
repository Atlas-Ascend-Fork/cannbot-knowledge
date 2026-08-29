---
type: API
title: DataCopyPad
description: 将数据从UB非对齐搬运至GM。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DataCopyPad

将数据从UB非对齐搬运至GM。

该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Global Memory
    - VECIN -> GM
    - VECOUT -> GM

- 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。
- 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：操作数的数据类型。各产品支持的数据类型请参考[数据类型](#section4219135304818)。；mode：配置数据搬运模式。PaddingMode类型，定义如下： enum class PaddingMode : uint8_t {     Normal = 0,  // 默认模式，与原有数据搬运格式保持一致，每次数据搬运都会补齐至32字节对齐     Compact,     // 紧凑模式，允许单次搬运不对齐，统一在整块数据末尾补齐至32字节对齐 };；dst：输出 目的操作数，类型为GlobalTensor。 起始地址无地址对齐约束。；src：输入 源操作数，类型为LocalTensor。 起始地址需要保证32字节对齐。；dataCopyParams：输入 搬运参数，DataCopyExtParams类型，具体参数说明请参考[表3](#table_ub2gm_pad_3)。

约束：位于Unified Buffer的源地址必须32字节对齐，位于Global Memory的目的地址必须1字节对齐。；DataCopyExtParams结构体参数的值需在取值范围内：；

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad UB→GM 四参调用导致编译失败](../../../../../runbooks/compilation/datacopypad_ub_to_gm_has_no_pad_params.md)（`exemplifies`）：`GlobalTensor <- LocalTensor` 的 UB→GM `DataCopyPad`；将数据从UB非对齐搬运至GM。runbook 的四参编译失败与三参修复正是该 UB→GM API 的方向特定重载案例；API 方向合同可用于排除误套 GM→UB padding 参数。
- [DataCopyPad stride 表示 block 间隙](../../../../../runbooks/precision/datacopypad_stride_is_inter_block_gap.md)（`exemplifies`）：这里的 stride 字段是相邻 block 有效 payload 之间的额外 gap。DataCopyPad 已按硬件块粒度组织 UB 行；再写入 `padRowBytes-rowBytes` 会把对齐差重复计入地址推进。以有效字节数 `L`、对齐后行宽 `P` 为例，正确下一行地址是当前行起点加 `P`；错误配置又加 `(P-L)`，实际推进变成 `P+(P-L)`，因此从第二行开始访问错误位置。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。。runbook 同时修正 UB 到 GM 写回的多行 stride，API 卡明确非对齐写回时 dummy 对齐数据会被丢弃，说明不能再把补齐差重复计入 gap。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：`DataCopyPad` 的目标 `GlobalTensor<T>` 一律按元素偏移 `outputGm［dst_elem］` 索引；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。运行手册要求 UB→GM 输出使用 typed GlobalTensor 的元素偏移并匹配 LocalTensor 类型，API 卡给出该搬出方向的源/目的类型、对齐和 dummy 丢弃语义。
- [窄尾 tile 行距错位：补齐 UB gap](../../../../../runbooks/precision/datacopypad_narrow_tile_needs_explicit_ub_row_gap.md)（`exemplifies`）：分别在 GM→UB 的 `dstStride` 与 UB→GM 的 `srcStride` 中补上相同的 UB gap：；将数据从UB非对齐搬运至GM。。Runbook 的修复在 UB→GM 搬出端设置 srcStride，目标 API 卡确认该方向会丢弃对齐 dummy 数据，从而定位正确的 scatter 接口与源行距参数。
- [逐元素 DataCopyPad 做 strided gather 输出全零](../../../../../runbooks/precision/datacopypad_strided_gather.md)（`exemplifies`）：机制链：逐元素 `DataCopyPad` strided gather（1-元素 blockLen + `LocalTensor` 切片 dst）→ GM 值未有效落入写出路径读取的 UB → 写回 GM 全零。这不是"算式错"或"对齐越界"，而是"块搬运 DMA 被误用为元素级标量 gather"的语义不匹配。元素级 GM 读写应使用 `GlobalTensor.GetValue(offset)` / `GlobalTensor.SetValue(idx, val)`。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。。runbook 的全零信号在错误 GM→UB gather 后由 UB→GM 整片写回暴露，API 卡明确该后半段只是块写回，不能补救前半段未落入 UB 的元素。
- [DataCopyPad](data_copy_pad_gm_to_ub.md)（`same_topic`）：DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。；该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。。两端记录同一 DataCopyPad 非对齐搬运契约的 GM 到 UB 与 UB 到 GM 两个方向，联合阅读可按数据流方向选择入口并核对填充与丢弃 dummy 数据的差异。
<!-- cannbot:related:end -->
