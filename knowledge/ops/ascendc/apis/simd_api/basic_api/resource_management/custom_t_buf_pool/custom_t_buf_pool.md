---
type: API
title: 自定义TBufPool
description: 自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/custom_TBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 自定义TBufPool

自定义 TBufPool 接口集合，允许用户自行管理 Buffer 池内存。EXTERN_IMPL_BUFPOOL 宏声明自定义实现；Init/Reset 初始化与重置池；GetBufHandle 获取 buffer 句柄；SetCurAddr/GetCurAddr/SetCurBufSize/GetCurBufSize 管理当前 buffer 地址与大小。适用于对内存布局有特殊需求的场景，使用前需配合 TPipe 的 InitBufPool 完成初始化。

<!-- cannbot:related:start -->
## 相关

- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：CustomTBufPool 提供外部/手动池管理；只有需要自定义地址布局时才替代普通 TBufPool。
- [Reset](reset.md)（`related`）：“Reset”定义：完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。；“自定义TBufPool”定义：自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。。实质衔接：Custom pool Reset 会释放资源并使 Buffer 失效，必须与 Init 生命周期配对；普通 TBufPool.Reset 只切换事件且资源仍在，差异直接影响后续可用性。
- [TBufPool](../t_buf_pool/t_buf_pool_constructor.md)（`related`）：CustomTBufPool 仅在需要外部地址/手动布局时替代普通池。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；自定义TBufPool正文说明“自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [InitBufPool](../t_buf_pool/init_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；InitBufPool正文界定“从Tpipe或TBufPool划分资源池，支持非共享模式和共享模式（复用已有资源池地址）”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；InitBufPool正文界定“初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
- [Reset](../t_buf_pool/reset.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；Reset正文界定“切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
- [TBufPool](../t_buf_pool/t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；TBufPool正文界定“TBufPool接口索引页，包含简介、构造函数、InitBufPool、InitBuffer与Reset”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；TBufPool简介正文界定“TPipe可以管理全局内存资源，而TBufPool可以手动管理或复用Unified Buffer/L1 Buffer物理内存，主要用于多个stage计算中Unified Buffer/L1 Buffer物理内存不足的场景”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
