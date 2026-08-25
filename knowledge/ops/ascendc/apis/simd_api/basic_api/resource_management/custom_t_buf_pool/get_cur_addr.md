---
type: API
title: GetCurAddr
description: 获取自定义TBufPool当前已分配的内存地址，用户可从该地址向后继续分配内存块。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/GetCurAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetCurAddr

头文件路径为："basic_api/kernel_tpipe.h"。

获取当前已经被自定义TBufPool分配的地址，用户可以从该地址值开始向后分配内存块。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetCurBufSize](get_cur_buf_size.md)（`related`）：块数与当前地址共同描述自定义池分配游标，诊断重叠或越界需同时检查。
- [ExternImplBufpool](extern_impl_bufpool.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；ExternImplBufpool正文说明“辅助开发者自定义TBufPool以管理Unified Buffer和L1 Buffer内存的宏，支持不连续内存块和跨TQue共享等自定义分配需求”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [GetBufHandle](get_buf_handle.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；GetBufHandle正文说明“根据offset取出自定义TBufPool中管理的内存块，返回TBufHandle类型的内存块句柄”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [GetCurAddr](../local_mem_allocator/get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；GetCurAddr正文说明“返回当前物理位置空闲的起始地址”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [Init](init.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；Init正文说明“完成自定义TBufPool资源与eventId等变量的初始化操作，可在自定义构造函数中调用”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [Reset](reset.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；Reset正文说明“完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [SetCurAddr](set_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；SetCurAddr正文说明“设置自定义TBufPool已分配完的地址，保证后续内存块从指定地址开始分配”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [SetCurBufSize](set_cur_buf_size.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；SetCurBufSize正文说明“设置自定义TBufPool当前已分配的内存块个数”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [自定义TBufPool](custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；自定义TBufPool正文说明“自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
<!-- cannbot:related:end -->
