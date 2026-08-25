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

- [DataCopyExtParams blockLen 窄化编译失败](../../../../../runbooks/compilation/datacopyextparams_block_len_requires_uint32.md)（`exemplifies`）：该案例补充 blockLen 必须保持 uint32_t，和 blockCount 的窄类型形成逐字段初始化约束。
- [DataCopyExtParams 运行时块数窄化编译失败](../../../../../runbooks/compilation/datacopyextparams_block_count_requires_uint16.md)（`exemplifies`）：该 API 消费 DataCopyExtParams，卡片中的窄化修复正发生在 UB 到 GM 的 DataCopyPad 调用边界。
- [DataCopyPad UB→GM 四参调用导致编译失败](../../../../../runbooks/compilation/datacopypad_ub_to_gm_has_no_pad_params.md)（`exemplifies`）：该 API 正文规定 UB→GM DataCopyPad 的三参数搬出契约，直接解释 focal 四参数调用为何没有可匹配 overload。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../../../../../runbooks/compilation/nddma_nddmaconfig_datacopypad.md)（`exemplifies`）：《DataCopyPad》明确“将数据从UB非对齐搬运至GM。”；它与《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》的“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopy](data_copy_gm_and_ub_continuous.md)（`related`）：UB 到 GM 非对齐尾块需用 DataCopyPad 的字节长度语义，补足连续 DataCopy 无法覆盖的搬出边界。
- [DataCopyPad](data_copy_pad_gm_to_ub.md)（`related`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad》说明将数据从UB非对齐搬运至GM。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopy](data_copy_gm_to_ub_nddma.md)（`same_topic`）：DataCopy 与《DataCopyPad》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
<!-- cannbot:related:end -->
