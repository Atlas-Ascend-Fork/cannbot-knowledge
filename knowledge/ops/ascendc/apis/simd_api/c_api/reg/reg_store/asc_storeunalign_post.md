---
type: API
title: AscStoreUnalignPost
description: 从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，将非对齐寄存器中暂存的尾块搬出到UB，需在asc_storeunalign或asc_storeunalign_postupdate之后调用。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storeunalign_post.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscStoreUnalignPost

reg计算数据搬运接口，适用于从矢量数据寄存器连续非32B对齐的起始地址连续搬出到UB的尾块场景。 需要先调用下列接口之一后，再调用本接口。 搬运原理如下：
函数原型：void asc_storeunalign_post(__ubuf__ int8_t* dst, vector_store_unalign src, int32_t offset)
约束：该接口中的dst不需要32B对齐，但数据类型为T的dst需要sizeof(T) Byte对齐。；调用本接口之前，需要调用asc_storeunalign接口，或者asc_storeunalign_postupdate接口，且本接口与前序接口的非对齐寄存器要保持一致。；需要保证目的操作数的地址加上offset对应的偏移地址，结果等于数据搬运的结束地址，具体见调用示例。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreUnalignPostupdate](asc_storeunalign_postupdate.md)（`related`）：PostUpdate 版本在生成主体状态时自动更新地址；其 offset 类型决定随后应选择哪一种 Post 尾处理。
- [reg数据搬出](reg_store.md)（`related`）：RegStore 总览解释对齐、非对齐和 postupdate 存储族，给出 AscStoreUnalignPost 在完整写回流程中的位置。
- [AscStoreUnalign](asc_storeunalign.md)（`same_topic`）：“AscStoreUnalign”处理从矢量数据寄存器连续非32B对齐搬出到UB，使用uint32_t作为存储偏移量，不改变源操作数地址，每次循环需用户手动更新目的地址。；“AscStoreUnalignPost”明确从矢量数据寄存器连续非32B对齐搬出到UB的尾块场景，将非对齐寄存器中暂存的尾块搬出到UB，需在asc_storeunalign或asc_storeunalign_postupdate之后调用。。实质衔接：AscStoreUnalign 正文要求调用 Post 收尾；Postupdate 是自动更新地址的对应流程，优化指南说明连续非对齐搬出的使用模式。
- [AscStoreUnalignPost](asc_storeunalign_post_deprecated.md)（`same_topic`）：当前 AscStoreUnalignPost 是废弃同名接口的直接承接者，保留非对齐连续搬出并处理末尾暂存数据。
- [asc_storeunalign_post_postupdate](asc_storeunalign_post_postupdate.md)（`same_topic`）：AscStoreUnalignPost 与 post_postupdate 都完成非对齐连续搬出的尾块收尾；后者在相同收尾合同上自动推进目的地址，前者由调用方提供偏移。
<!-- cannbot:related:end -->
