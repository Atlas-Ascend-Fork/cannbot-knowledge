---
type: Guide
title: TBuf的使用
description: 在大多数算子开发时，核函数计算过程需要使用临时内存来存储运算的中间结果，这些中间结果以临时变量表示，临时变量占用的内存可以使用TBuf数据结构来管理，具体介绍请参考TBuf。下文将以输入的数据类型为bfloat16_t、在单核上运行的Add算子为例，介绍TBuf的使用方式。本文中介绍的算子完整代码请参见使用临时内存的Add算子样例。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/tbuf_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2]
---

# TBuf的使用

在大多数算子开发时，核函数计算过程需要使用临时内存来存储运算的中间结果，这些中间结果以临时变量表示，临时变量占用的内存可以使用TBuf数据结构来管理，具体介绍请参考TBuf。下文将以输入的数据类型为bfloat16_t、在单核上运行的Add算子为例，介绍TBuf的使用方式。本文中介绍的算子完整代码请参见使用临时内存的Add算子样例。
在Atlas A2 训练系列产品/Atlas 800I A2 推理产品上，Add接口不支持对数据类型bfloat16_t的源操作数进行求和计算。因此，需要先将算子输入的数据类型转换成Add接口支持的数据类型，再进行计算。为保证计算精度，调用Cast接口将输入bfloat16_t类型转换为float类型，再进行Add计算，并在计算结束后将float类型转换回bfloat16_t类型。
通过以上分析，得到Ascend C  Add算子的设计规格如下：
-   算子类型（OpType）：Add
-   算子输入输出：
Add算子输入输出规格
-   核函数名称：tmp_buffer_custom
-   使用的主要接口：
-   DataCopy：数据搬移接口
-   Cast：矢量精度转换接口
-   Add：矢量基础算术接口
-   EnQue、DeQue等接口：Queue队列管理接口
-   算子实现文件名称：tmp_buffer.asc
## 算子类实现
该样例的CopyIn，CopyOut任务与基础矢量算子相同，Compute任务的具体流程如下图所示。
在计算过程中，表示Cast转换结果、Add计算结果的临时变量均需要使用临时内存存储。与基础矢量算子实现的KernelAdd算子类相比，本样例新增两个TBuf类型的成员变量tmpBuf0、tmpBuf1，用于管理计算过程中使用的临时内存，因此初始化阶段除原有步骤外，需要调用InitBuffer接口为TBuf变量分配内存，具体的初始化阶段代码如下：
基于矢量编程范式，核函数需要实现3个基本任务：CopyIn，Compute，CopyOut。与基础矢量算子实现相同，核函数按顺序进行CopyIn，Compute，CopyOut。其中，CopyIn，CopyOut与基础矢量算子的CopyIn、基础矢量算子的CopyOut的实现没有差异，此处不过多赘述。Compute的实现步骤如下：
1.  使用DeQue从UB（VECIN）的Queue中取出LocalTensor。
2.  使用TBuf.Get从TBuf上获取全部长度的Tensor作为临时内存。
3.  使用Cast接口将LocalTensor转换为float类型，并存入临时内存。
4.  使用Add接口完成矢量计算，将计算结果存入临时内存。
5.  使用Cast接口将临时内存中的计算结果转换为bfloat16_t类型。
6.  使用EnQue将bfloat16_t类型的结果LocalTensor放入UB（VECOUT）的Queue中。
7.  使用FreeTensor释放不再使用的LocalTensor。

<!-- cannbot:related:start -->
## 相关

- [GetWithOffset](../../../../apis/simd_api/basic_api/resource_management/t_buf/get_with_offset.md)（`explains`）：GetWithOffset 与《TBuf的使用》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [InitBuffer](../../../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)（`explains`）：指南初始化阶段调用 TPipe::InitBuffer 为两个 TBuf 分配 UB，是样例可运行的必要资源步骤。
- [TBuf](../../../../apis/simd_api/basic_api/resource_management/t_buf/t_buf.md)（`explains`）：TBuf API 定义 Get 获得 LocalTensor 和缓冲生命周期，正是指南样例管理 Cast/Add 中间结果的底层契约。
- [TBuf简介](../../../../apis/simd_api/basic_api/resource_management/t_buf/t_buf_intro.md)（`explains`）：TBuf简介 与《TBuf的使用》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`related`）：InitOutput GM 专用，UB 清零用 Duplicate 与《TBuf的使用》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [TBuf 不能直接传给 LocalTensor 形参](../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`related`）：该 runbook 强调 helper 形参需要 LocalTensor，必须先 TBuf.Get<T>()；与指南 Compute 步骤的类型化获取一致。
- [基础矢量算子](basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《TBuf的使用》说明在大多数算子开发时，核函数计算过程需要使用临时内存来存储运算的中间结果，这些中间结果以临时变量表示，临时变量占用的内存可以使用TBuf数据结构来管理，具体介绍请参考TBuf。下文将以输入的数据类型为bfloat16_t、在单核上运行的Add算子为例，介绍TBuf的使用方式。本文中介绍的算子完整代码请参见使用临时内存的Add算子样例。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [未分配 TBuf 导致浮点索引随机错乱](../../../../runbooks/precision/missing_tbuf_allocation_causes_undefined_ub_index_scratch.md)（`related`）：该 runbook 给出遗漏 TBuf 分配后索引临时区随机错乱的验证信号，补充指南的失败路径。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](../../../../runbooks/compilation/tbuf_get_ub_dav_2201.md)（`related`）：TBuf 指南给出 InitBuffer、Get/GetWithOffset 生命周期，本卡补充 dav-2201 地址重叠探针和单池切分。
<!-- cannbot:related:end -->
