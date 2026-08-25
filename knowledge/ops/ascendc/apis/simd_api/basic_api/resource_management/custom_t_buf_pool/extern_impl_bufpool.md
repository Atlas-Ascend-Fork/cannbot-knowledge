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

- [GetCurBufSize](get_cur_buf_size.md)（`related`）：自定义分配实现需要读取当前剩余/可用区大小，避免跨越池边界。
- [Init](init.md)（`related`）：自定义池必须实现 Init 并在 TPipe::InitBufPool 后绑定可管理的 UB/L1 范围。
- [Reset](reset.md)（`related`）：Reset 是自定义 TBufPool 生命周期的释放/复位阶段，与宏要求实现初始化和释放相呼应。
- [SetCurAddr](set_cur_addr.md)（`related`）：不连续内存块或跨 TQue 共享时需显式更新当前地址，正是 ExternImplBufpool 允许自定义的核心能力。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；ExternImplBufpool正文说明“辅助开发者自定义TBufPool以管理Unified Buffer和L1 Buffer内存的宏，支持不连续内存块和跨TQue共享等自定义分配需求”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《ExternImplBufpool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
<!-- cannbot:related:end -->
