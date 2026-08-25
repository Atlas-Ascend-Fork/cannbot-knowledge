---
type: Guide
title: 连续非对齐场景优化
description: 连续非对齐搬运场景的性能优化建议与接口介绍。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 连续非对齐场景优化

## 连续非对齐搬运优化建议
-   优先采用连续对齐搬运以避免额外开销，提升整体性能。
-   由于硬件支持限制，连续非对齐搬运时不建议使用AddrReg存储偏移量，推荐使用uint32_t类型存储偏移量，使用post update模式搬运，该场景下每次调用接口自动更新源操作数在UB上的地址。后续的优化建议均基于此场景展开。
-   连续非对齐搬入时，每次将UB数据搬运至RegTensor后，非对齐寄存器会缓存后续非对齐数据，下一次搬运时非对齐寄存器中的数据会写入RegTensor，因此连续非对齐搬入初始化仅需执行一次，应移至for循环外部。
-   连续非对齐搬出时，每次将RegTensor数据搬运至UB后，非对齐寄存器会缓存后续非对齐数据，下一次搬运时非对齐寄存器中缓存的数据将写入UB，因此连续非对齐搬出后处理只需执行一次，应移至for循环外部。
【正例】
【反例】
## 连续非对齐搬运接口介绍
为提升对不规则内存地址的处理能力，Reg矢量计算支持在数据搬运过程中对非32字节对齐的地址进行访问，适用于从UB向RegTensor非对齐搬运，或从RegTensor向UB非对齐搬运的场景。为降低非对齐访问带来的性能开销，RegBase引入非对齐寄存器缓存机制，该机制利用非对齐寄存器UnalignRegForLoad和UnalignRegForStore作为临时缓存区，用于暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。
在读非对齐地址前，应该先通过LoadUnAlignPre进行初始化，然后再使用LoadUnAlign。在写非对齐地址时，先使用StoreUnAlign，再使用StoreUnAlignPost进行后处理。使用uint32_t管理偏移量的搬入搬出接口和maskReg搬出接口如下：
-   连续非对齐搬入，使用uint32_t存储搬运量
-   连续非对齐搬出，使用uint32_t存储偏移量
-   连续非对齐搬出，将maskReg搬出至UB
## 非对齐寄存器原理
本节主要介绍在非对齐搬运过程中，非对齐寄存器如何发挥其作用，并详细解释内部原理，帮助开发者理解为什么上文的性能优化建议能够带来性能收益。首先介绍连续非对齐数据搬入、连续非对齐数据搬出以及MaskReg连续非对齐数据搬出的实现原理，然后通过一个具体的搬入搬出例子将这些关键流程串接起来。
-   非对齐数据搬入
如下图所示，从UB地址srcAddr \~ 304读取数据，并将其搬运至目标寄存器dstReg（256B）。处理流程如下：
-   调用LoadUnAlignPre进行非对齐搬入初始化。非对齐寄存器ureg缓存UB地址32 \~ 64的有效数据，作为后续非对齐访问的前置数据缓存。
-   调用LoadUnAlign，硬件指令将UB地址64 \~ 320的数据搬入临时寄存器tmpReg，并将ureg中srcAddr \~ 64对应的数据与tmpReg中地址64 \~ 304对应的数据拼接在一起，将结果写入dstReg。本次搬运后，UB地址288 \~ 320的数据会被写入ureg。

<!-- cannbot:related:start -->
## 相关

- [AscLoadunalignPre](../../../../../apis/simd_api/c_api/reg/reg_load/asc_loadunalign_pre.md)（`explains`）：AscLoadunalignPre 与《连续非对齐场景优化》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [AscStoreUnalign](../../../../../apis/simd_api/c_api/reg/reg_store/asc_storeunalign.md)（`explains`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“连续非对齐场景优化”明确连续非对齐搬运场景的性能优化建议与接口介绍。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [Copy](../../../../../apis/simd_api/basic_api/memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`explains`）：Copy 与《连续非对齐场景优化》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [Load](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load.md)（`explains`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《连续非对齐场景优化》明确“连续非对齐搬运场景的性能优化建议与接口介绍。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [LoadUnAlign](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_un_align_continuous.md)（`explains`）：连续非对齐场景优化 的核心契约是“连续非对齐搬运场景的性能优化建议与接口介绍”；LoadUnAlign 补充“将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移”。
- [StoreAlignNoncontinuous](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_noncontinuous.md)（`explains`）：StoreAlignNoncontinuous 与《连续非对齐场景优化》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [StoreUnAlignContinuous](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_un_align_continuous.md)（`explains`）：连续非对齐场景优化 的核心契约是“连续非对齐搬运场景的性能优化建议与接口介绍”；StoreUnAlignContinuous 补充“将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据”。
- [UnalignRegForLoadAndUnalignRegForStore](../../../../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`explains`）：UnalignRegForLoadAndUnalignRegForStore 与《连续非对齐场景优化》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [连续计算API](../../../../programming_guide/library_api/basic_api/interface_classification/continuous_compute_api.md)（`related`）：连续计算API 与《连续非对齐场景优化》的实质衔接是：连续计算 API 与高维切分的选择取决于布局连续性，非对齐优化给出连续但未对齐时的可执行分支。
<!-- cannbot:related:end -->
