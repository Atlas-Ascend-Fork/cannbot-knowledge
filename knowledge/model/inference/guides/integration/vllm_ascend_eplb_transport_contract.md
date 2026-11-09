---
type: Guide
title: vLLM Ascend EPLB通信：Gloo staging、HIXL READ与注册退出
description: 接入异步EPLB通信时核对显式迁移坐标、真实专家weight view、Gloo pinned staging与NZ接收、共享HIXL session的地址和storage寿命、终态handle及ctypes
  ABI；将传输安全与placement提交分别验收。
tags:
- task.implementation
- task.debugging
- topic.data_movement
- topic.mixture_of_experts
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/eplb_communicator.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/explicit_transfer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/hixl_compat.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_communicator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_explicit_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_hixl_compat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_hixl_communicator.py
  role: evidence
created_at: '2026-11-03T01:11:21Z'
updated_at: '2026-11-03T01:11:21Z'
platforms: []
aliases:
- AscendHixlEplbCommunicator
- AscendGlooEplbCommunicator
- stage_explicit_layer_transfer
- _HixlSession
- hixl_compat
- HIXL专家权重迁移
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend EPLB通信：Gloo staging、HIXL READ与注册退出

## 任务边界

本卡聚合Ascend `ceac1a2b` 的communicator、显式迁移及ctypes封装和四份专项UT，服务新量化专家布局、主模型与draft共享资源、异步搬运失败和退出问题。没有运行上游、UT、线程、CANN库或NPU，也没有新增verified；局部950 workaround与CANN ABI注释不能证明整卡支持范围，保持draft/空平台。

模型注册、统计、routing refresh与commit/ACK仍按[EPLB模型接入](vllm_ascend_eplb_model_weight_contract.md)；本卡负责buffer staging和通信资源。通用[HIXL概念](../../concepts/techniques/hixl.md)及Mooncake KV传输不替代这条专家权重READ路径的契约。

## 迁移计划先校验，再向buffer搬运

`stage_explicit_layer_transfer` 接收CPU上的old/new一维非负整数placement，按group size等分成 `[ranks,slots]`。source_rank_ids/source_slot_ids必须是同形状整数坐标、范围合法，且从old placement按坐标取出的专家逐项等于new placement。weights/buffers必须非空且一一对齐，每个本地slot的tensor shape、dtype和device相同；这些检查在设置通信context或copy之前完成。

该helper假设dense、等容量placement且同rank没有重复专家，调用方还要验证完整policy计划。局部坐标和值校验不是所有全局唯一性/覆盖要求的完整实现；尤其HIXL后续按expert ID查旧slot，不能把同rank重复专家视为无关紧要。

同rank同slot标unchanged；同rank换slot在本地copy到buffer；跨rank登记send/recv。receiver_initiated的communicator只遍历本rank目的槽，HIXL的add_send本身无操作，实际由接收端READ。返回TransferMetadata中的is_unchanged、is_received_locally、recv_primary_mask及recv_count/紧凑有效前缀应分别消费，不能将初始-1尾部当实际专家。

函数只stage到buffer并返回metadata，不在这里将live weight与routing同时提交。调用execute完成也不等于模型placement已经生效或接收区已可再次覆盖。

## Gloo staging：CPU缓冲区与设备stream

`AscendGlooEplbCommunicator` 继承上游CPU-staged实现，按 `(dtype,shape)` 缓存pinned CPU buffers；同一execute内的计数避免并行操作复用同一槽，下次execute从缓存开头复用。缓存属于communicator寿命，不是每次传输自动释放的临时对象。

发送先异步拷到CPU；P2POp显式使用CPU group与group-local peer rank。提交batch_isend_irecv前同步指定stream，未指定时同步当前device stream，保证CPU发送数据已就绪；所有request.wait后，再将收到的CPU数据异步copy回目的tensor。

目的tensor为NPU且格式为NZ时，先把CPU staging搬到目的device、format_cast成NZ，再copy；源码将其解释为950不能直接CPU→NZ的workaround，实际分支仍按device/format判断。不能只凭目的shape相同就省掉格式或stream交接。该路径needs_profile_buffer_reservation=False，不代表零CPU拷贝、零同步或零pinned-memory成本。

操作队列在准备阶段finally清空；失败后再次调用空execute不等于原计划已经重新提交。重试需按调用方的事务与buffer状态重新组织，不能仅由本类缓存存在推导自动恢复。

## HIXL专家view与跨rank地址清单

`AscendHixlEplbCommunicator` 要求非空NPU专家tensor。view可为expert-first stacked tensor，或每个专家一个tensor的序列；stacked首维必须等于local experts且整体contiguous，只有weak-contiguous仍不足。列表中的专家tensor需要相同nbytes，每个storage须同device、非标量且weak-contiguous。

本地metadata按 `(layer_idx,tensor_idx)` 保存各专家地址和单专家字节跨度；stacked地址按row stride生成，列表保留各自地址。主模型/draft共用一个 `_HixlSession`，但保留各自model key、layer与tensor清单。session要求同一个CPU group对象、同一个NPU device；各rank模型顺序、key、每view专家数与stride要相容，不能只比较模型集合而忽略顺序。

这些metadata检查不证明跨rank量化语义相同：相同nbytes仍可能对应不同dtype、打包、scale顺序或专家身份。新scheme必须另外对照真实活动weight/scale view与输出，不能让kernel继续读旧转置参数。

## 注册范围、storage与共享session

session在preflight、engine初始化、metadata交换、内存注册与建链之间执行全rank确认。先验证tensor非空字节范围位于其untyped_storage内，再持有storage引用；注册范围向外按2MiB对齐，排序合并交叠或相邻范围。合并后最多4000个region，超限在backend首次register前拒绝；输入tensor超过4000不一定超限，取决于合并结果。

这里依据真实可传输tensor/storage注册，不使用allocator memory_snapshot中的整个可扩张segment作为稳定identity。tensor.data重绑后，旧storage仍由session引用维持，不能提前回收或用新参数地址替换旧登记地址。初始化成功后communicator释放其原始weight/buffer容器引用，state与session分别承担模型和注册storage所有权；删除单个draft communicator不等于整个session已结束。

初始化失败会回滚已经成功登记的handle；本地尚无engine的rank也需参与规定的分组清理。若回滚失败，把session挂到fatal异常链并SystemExit，避免普通RPC异常序列化后丢失尚在远程访问的storage owner。不能把创建失败统一处理成“清空对象再试”。

## READ执行、终态handle与失败传播

set_stream恢复初始化时的NPU/ACL context，HIXL使用自己的streams。每层set_transfer_context建立旧placement的expert→slot查找，add_recv按源rank聚合READ描述符，并检查目的tensor字节数等于remote stride；存在pending reads时不能直接开始下一层。

execute先同步EPLB指定stream或当前stream，让此前consumed-event等待真正结束，再让HIXL私有stream覆盖共享接收区。按源rank调用transfer_async，等待已成功提交的request；即使后一个源提交失败，也先drain前面已提交请求，然后通过全rank确认传播错误。确认失败会使整个共享session不可用，不能只让出错模型局部改用另一backend继续运行。

查询返回非SUCCESS，或状态已非WAITING时，代码先从pending和session请求列表移除该handle，再检查是否COMPLETED或抛错：CANN终态查询可能消费handle，关闭时不能再查询已失效handle。轮询超时仍保留未完成请求；不能将其当作已取消、已释放或可安全注销。默认传输/集体确认超时300秒，轮询间隔0.5毫秒；这些是实现常量，不是性能结果。

每次execute分别记录launch、background transfer、confirmation耗时、request_count和bytes；它们不能直接替代新模型端到端延迟/吞吐，也不证明foreground已commit该层。

## 退出必须证明对端READ结束

正常close先恢复context并drain本地request，再全rank确认；随后disconnect全部peer并再次全rank确认，然后逆序deregister成功handle，最后finalize，并在各阶段传播失败。本地发起的READ完成，不足以证明对端对本地storage的READ已结束；因此不能在disconnect集体确认前释放注册内存。

deregister成功才pop对应handle；中途失败保留剩余handle、engine与storage引用，session进入error状态。已经poisoned的session会拒绝继续使用或普通close；state层需要终止worker来维持资源寿命。CPU group本身失败后不再次盲目复用该group做清理集体操作。无错误且资源已关闭时重复close可返回，不能把这一幂等成功路径推广到失败清理。

## ctypes兼容入口的ABI限制

`_resolve_hixl_module` 在official hixl可导入时优先返回它；只有ImportError才尝试hixl_compat，不能假定已安装但不可用的official包总会触发ctypes回退。兼容层先加载AscendString提供库，再加载HIXL库，并绑定实际导出C++符号。

本实现说明其对象布局对照GCC libstdc++ / CANN9.1 aarch64：AscendString16字节、空map48字节、vector24字节；UT还断言MemDesc144、TransferOpDesc24、TransferArgs128字节及reserved清零。它们是该封装的假设与静态测试内容，不能由找到共享库或符号存在推导任意CANN/架构ABI兼容。符号缺失、构造器不符均需明确失败；本次没有实际加载库或执行sizeof探针。

ctypes入口只支持空initialize options；engine string按handle缓存。销毁字符串时遇异常引用计数/控制块状态会保留分配，避免非法释放；解释器终结时析构不再调用HIXL。正常finalize、engine析构、进程退出兜底是不同阶段，不把Python对象回收当作远端已断连证据。

## 接入与故障验收

适配Agent应保存：完整placement与source坐标；每slot真实weight/scale的shape/dtype/device/stride；各model清单顺序、local/remote地址与注册handle；stream/context、已提交request及终态查询；commit、routing refresh、ACK和close各阶段结果。先用真实topk和至少两次重排校验输出，再比较Gloo/HIXL下相同workload的端到端收益。

四份UT定义了group-local rank、pinned复用、NZ接收、错误source/buffer前置拒绝、共享主/draft session、部分提交drain、handle不重复查询、4000合并区域门槛、重绑storage保活和失败退出等mock断言。本次仅阅读，未运行UT或真机通信；HIXL内部传输引擎与实际CANN ABI仍属于外部证据边界。
