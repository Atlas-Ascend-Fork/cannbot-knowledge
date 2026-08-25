---
type: API
title: Get
description: 从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/Get.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Get

头文件路径为："basic_api/kernel_tpipe.h"。

从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。

约束：len的数值是Tensor中元素的个数，len*sizeof(T)不能超过TBuf初始化时的长度。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [TBuf 不能直接传给 LocalTensor 形参](../../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`exemplifies`）：TBuf::Get<T>() 正是把缓冲管理对象转换为 typed LocalTensor 视图的正式接口，是本卡修复调用点的直接契约。
- [未分配 TBuf 导致浮点索引随机错乱](../../../../../runbooks/precision/missing_tbuf_allocation_causes_undefined_ub_index_scratch.md)（`exemplifies`）：《未分配 TBuf 导致浮点索引随机错乱》处理“分支内使用未初始化的临时 TBuf 会造成静默索引错乱；在同一 Init 分支补齐 InitBuffer 后恢复精确结果。”。《Get》明确“从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。”，可直接用于核对TBuf 在同一分支先 InitBuffer 再 Get 的生命周期，以及无效/重叠 UB 地址的差分诊断。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](../../../../../runbooks/compilation/tbuf_get_ub_dav_2201.md)（`exemplifies`）：异常直接由多个独立 TBuf.Get<float>() 返回区间重叠触发；Get 定义取得 LocalTensor 的接口。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：InitBuffer 为 TBuf 分配实际块大小，Get 返回的 LocalTensor 容量由该分配决定。
- [TBufConstructor](t_buf_constructor.md)（`related`）：构造并分配 TBuf 后通过 Get 取得 LocalTensor；构造是该访问链的前置步骤。
- [GetWithOffset](get_with_offset.md)（`same_topic`）：GetWithOffset 与《Get》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [TBuf简介](t_buf_intro.md)（`same_topic`）：TBuf简介 与《Get》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
