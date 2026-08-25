---
type: API
title: Reset
description: 完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

完成自定义TbufPool资源的释放与eventId等变量的复位对消。

约束：切换自定义TBufPool资源池时调用该接口，调用后对应资源池及资源池分配的Buffer不能继续使用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ExternImplBufpool](extern_impl_bufpool.md)（`related`）：Reset 是自定义 TBufPool 生命周期的释放/复位阶段，与宏要求实现初始化和释放相呼应。
- [Init](init.md)（`related`）：“Reset”定义：完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。；“Init”定义：完成自定义TBufPool资源与eventId等变量的初始化操作，可在自定义构造函数中调用。。实质衔接：Custom pool Reset 会释放资源并使 Buffer 失效，必须与 Init 生命周期配对；普通 TBufPool.Reset 只切换事件且资源仍在，差异直接影响后续可用性。
- [Reset](../t_buf_pool/reset.md)（`related`）：“Reset”定义：完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。；“Reset”定义：切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在。。实质衔接：Custom pool Reset 会释放资源并使 Buffer 失效，必须与 Init 生命周期配对；普通 TBufPool.Reset 只切换事件且资源仍在，差异直接影响后续可用性。
- [自定义TBufPool](custom_t_buf_pool.md)（`related`）：“Reset”定义：完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。；“自定义TBufPool”定义：自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。。实质衔接：Custom pool Reset 会释放资源并使 Buffer 失效，必须与 Init 生命周期配对；普通 TBufPool.Reset 只切换事件且资源仍在，差异直接影响后续可用性。
- [GetCurAddr](get_cur_addr.md)（`same_topic`）：焦点处理自定义 TBufPool 当前地址游标的读取、设置与生命周期；Reset正文说明“完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用”。候选读写同一个 pool 游标/块计数，或决定这些值何时初始化、复位和失效。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《Reset》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
<!-- cannbot:related:end -->
