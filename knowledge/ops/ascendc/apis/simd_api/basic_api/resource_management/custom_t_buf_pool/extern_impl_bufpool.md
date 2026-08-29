---
type: API
title: ExternImplBufpool
description: 辅助开发者自定义TBufPool以管理Unified Buffer和L1 Buffer内存的宏，支持不连续内存块和跨TQue共享等自定义分配需求。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/EXTERN_IMPL_BUFPOOL.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# ExternImplBufpool

头文件路径为："basic_api/kernel_tpipe.h"。

开发者可以通过TBufPool类手动管理Unified Buffer、L1 Buffer物理内存。

TBufPool类切分的内存块都是连续的，开发者可能有一些自定义的内存块分配需求，比如不连续内存块、内存块在不同TQue之间共享等，这时就需要开发者自定义一个TBufPool的实现。

为了简化开发者的自定义实现，提供EXTERN_IMPL_BUFPOOL宏来辅助用户自定义TBufPool。使用自定义TBufPool功能时，需要注意
-   自定义TBufPool之前，必须通过TPipe::InitBufPool接口进行TBufPool内存资源池初始化。
-   自定义TBufPool需要开发者自行实现对TQue/TBuf内存块的分配、初始化、释放等操作。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetBufHandle](get_buf_handle.md)（`related`）：焦点接口“根据offset取出自定义TBufPool中管理的内存块。”，候选宏则“提供EXTERN_IMPL_BUFPOOL宏来辅助用户自定义TBufPool。”；宏建立自定义池实现，GetBufHandle 按 offset 取得该实现管理的块，两者构成定义与访问合同。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`related`）：焦点卡规定“自定义TBufPool之前，必须通过TPipe::InitBufPool接口进行TBufPool内存资源池初始化”，候选卡说明初始化后“在整体内存资源中划分出一块子资源池”；该调用是使用自定义宏前不可省略的资源准备步骤。
<!-- cannbot:related:end -->
