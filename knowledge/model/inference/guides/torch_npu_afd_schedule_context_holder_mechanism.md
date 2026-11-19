---
type: Guide
title: AFD ScheduleContext 生产侧：1024字节上下文、窗口布局与停止语义
description: 记录 torch_npu._afd 调度上下文 holder 的参数门槛、FFN/Attention 窗口切分、设备副本与 stop_schedule 机制；两版均在、接线不同，仓内无业务调用方。
tags:
- task.lookup
- topic.model_serving
- topic.mixture_of_experts
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_afd/_schedule_context.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_afd/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/ScheduleContext.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/ScheduleContext.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/Init.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_afd_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_afd/test_ffn_worker_schedule.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_afd/_schedule_context.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_afd/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/afd/ScheduleContext.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/afd/ScheduleContext.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_afd_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-12T04:15:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# AFD ScheduleContext 生产侧：1024字节上下文、窗口布局与停止语义

## 固定版本与适用范围

两版均含该机制：主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b都有`torch_npu/_afd/`（发布`_schedule_context.py`与主线逐字节一致，`__init__.py`仅差一个docstring错别字）、`csrc/afd/`（发布`ScheduleContext.h/.cpp`与主线仅格式/缩进差异，1024字节结构、static_assert与校验/停止逻辑一致，`.cpp`溢出报错一处日志拼接风格不同）、`utils/_afd_ops.py`与`test/_afd`测试。差异在接线：发布在`torch_npu/__init__.py`第67行直接`import torch_npu._afd`、第78行`import torch_npu.utils._afd_ops`（后者在模块级把`torch.ops.npu`的`ffn/attention_worker_scheduler{,_}`四个op挂到`torch_npu._afd`命名空间）；主线`__init__.py`无此直接导入，由`module_loader`经`_afd_ops.initialize_afd_bindings`完成同样的op绑定。仓内调用链只有该绑定层与`test/_afd`测试；调度算子本体来自op-plugin（消费侧合同见[FFN Worker 上下文](torch_npu_ffn_worker_context_and_reference_limits.md)、GE侧见[Worker Scheduler 降级合同](optimization/torchair/torchair_ge_worker_scheduler_lowering.md)）。无公开文档与产品矩阵，draft、platforms为空；本次静态阅读，未初始化`_afd`模块、未分配窗口或设备Tensor。

## 上下文结构

`ScheduleContext`按`#pragma pack(1)`紧凑布局并`static_assert`整体1024字节：CommonArea（128B：session/micro_batch/batch/selected_expert/expert数量、两方向token字节大小、schedule_mode）、ControlArea（128B：run_flag）、AttentionArea（128B）、FfnArea（256B：token_info/data缓冲及大小、polling_index，layer/session/micro_batch/expert ID输出缓冲及大小、out_num）、尾部384B保留。头文件注释声明schedule_mode `2:ffn+attention`，但`CheckParams`当前只接受0/1（"only support [0, 1] now"），不把注释值当可用的组合模式。

## 参数门槛

`session_num`、`micro_batch_num`、`micro_batch_size`、`selected_expert_num`、`expert_num`非零；`attn_to_ffn_token_size`、`ffn_to_attn_token_size`必须512对齐；FFN模式要求`ffn_window`/`ffn_window_size`非零，Attention模式要求`attention_window`/`attention_window_size`非零；token_info尺寸经乘加溢出检查；窗口大小必须大于`AlignUp512(token_info_size)`。任一失败`init()`返回非零，Python包装`raise RuntimeError`。`Init`幂等（`init_flag`），重复调用直接返回成功。

## FFN窗口初始化

token_info按(session, micro_batch)记录：flag=0、layer_id=0、`micro_batch_size*selected_expert_num`个expert_id置`INT32_MAX`哨兵；host构造后经`aclrtMemcpy`写入`ffn_window`头部。`token_data_buf=ffn_window+AlignUp512(token_info_size)`，大小为`ffn_window_size−对齐尺寸`（token dtype未知，不计算内容大小）。输出区四个缓冲——layer/session/micro_batch_ids各`session_num`个int32、expert_ids为`session_num*micro_batch_size*selected_expert_num`个int32——由一次`at::empty`(PrivateUse1, int8)的workspace按对齐尺寸顺序切分（workspace大小=3*align(layer_ids)+align(expert_ids)）。

## Attention窗口初始化

token_info经`aclrtMemset`清零（无host暂存拷贝）；`token_data_buf`同上按对齐偏移切分；`micro_batch_id`初始化为`micro_batch_num-1`（设计为调度器从`(id+1)%num`起扫描），此扫描协议由消费侧算子实现，不在本卡证据内。

## 设备副本与停止语义

host侧`context_`经`at::from_blob`零拷贝包成1024字节int8 Tensor后`copy_`到NPU int8 Tensor；`get_schedule_context_tensor()`返回该设备副本（未init时返回失败码，Python层`RuntimeError`）。`stop_schedule()`把`run_flag`置0，并按`offsetof(ScheduleContext.control)+offsetof(ControlArea.run_flag)`切片设备Tensor、只`copy_`该4字节偏移段——停止语义是精确局部更新，不重写整个上下文。`get_schedule_context_info()`把设备副本整体拷回host后格式化（run_flag、各缓冲地址/大小、polling_index、out_num）。

## 生命周期边界

外部窗口（ffn_window/attention_window是裸设备地址）由调用方持有Tensor并保证生存期（测试形态见下）；holder不接管窗口、析构不做设备同步，消费算子的异步完成协议不由holder保证。参数计算含溢出防护，但窗口地址/大小的真实性与设备间可见性仍取决于调用方。

## 测试形态与未验证项

`test_ffn_worker_schedule.py`：200MiB int8 NPU窗口、attn_workers=2、micro_batch=3、batch=6、top_k=8（`selected_expert_num=top_k+1`）、expert_num=288、token大小`(7168+4+511)//512*512`与`7168*2`；构造后把窗口前`attn_workers*micro_batch*(8+batch*top_k*4)`字节按int32视图整体置1作flag预置。所有设备方法标注`Ascend910B`且`unittest.skip("skip case until cann supported")`，本次未运行——不据此宣称任何平台上已可用。部署拓扑与收益见[Attention-FFN 解耦部署](../optimizations/rules/afd_attn_ffn_disaggregation.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_afd/_schedule_context.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_afd/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/ScheduleContext.h)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/ScheduleContext.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/afd/Init.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_afd_ops.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py)（implementation，定向阅读绑定调用段）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_afd/test_ffn_worker_schedule.py)（example）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_afd/_schedule_context.py)（implementation，与主线逐字节一致）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_afd/__init__.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/afd/ScheduleContext.h)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/afd/ScheduleContext.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_afd_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，定向阅读`import torch_npu._afd`接线段）
