---
type: API
title: TorchNPU C++ HCCL：ProcessGroup与批量P2P合同
description: 保存Backend构造、通信成员与Work完成点，区分batch_isend_irecv的版本签名和global rank。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md
  role: constraint
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU C++ HCCL：ProcessGroup与批量P2P合同

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 类型、版本和构造

`c10d_npu::ProcessGroupHCCL`继承`c10d::Backend`，定义于`torch_npu/csrc/distributed/ProcessGroupHCCL.hpp`。产品表确认A2/A3训练系列，不从Python分布式支持范围扩到950或其他型号。

构造传入Store intrusive_ptr引用、rank、size及options，默认options为`Options::create()`；析构override。主线进一步列Options的高优先级布尔构造默认false、`create(bool=false, timeout=kNoTimeout)`及opTimeout/is_high_priority_stream字段；这不等于所有历史版本均有相同options布局，未据目录名验证实际运行时超时和优先级效果。

## 通信入口族

文档详细原型包含broadcast、allreduce、allreduce_coalesced、reduce的Tensor向量与相应options，allgather的嵌套输出向量、reduce_scatter的嵌套输入向量，barrier的options，以及send/recv的Tensor向量、rank、tag，alltoall_base的输入输出Tensor、split向量和options。输出引用与split布局按相应原型消费，不能把不同集合通信的向量层次或分片顺序互换。

接口清单还列allgather_into_tensor_coalesced、reduce_scatter_tensor_coalesced、gather、scatter、recv_anysource及alltoall；其中有字面拼写`allgather_togather`。该拼写仅作为来源清单差异保留，未查真实头文件前不把它当可编译成员名，也不从清单补造这些成员的完整原型/支持组合。外链社区文档不作为本卡证据。

## batch_isend_irecv

```text
batch_isend_irecv(vector<string>& op_type,
                 vector<at::Tensor>& tensors,
                 vector<uint32_t> [&] remote_rank_list) -> intrusive_ptr<c10d::Work>
```

方括号标记版本差异：发布原型remote_rank_list按值，主线中英文原型改为非const引用，而参数说明仍写按值。实际构建须核对版本头文件，不能视为ABI不变或复制出一个混合原型。

op_type的元素是isend/irecv，三个列表数量一致；remote_rank_list是对端**global rank**，不能用本机设备编号替代。批量方法返回一份Work，代表这批异步P2P请求，不是每个元素分别返回一个句柄；取用接收Tensor需等相应Work完成。对端匹配、顺序和缓冲区寿命依然由通信调用方保证。

## 完成与验收

文档说通信异步，通过WorkHCCL的wait/synchronize等待完成；完整实现不在本卡来源范围，不能把这里的完成点提升为整个设备所有流屏障或完整超时/故障恢复保证。[C++ HCCL单机样例](../../guides/torch_npu_libtorch_hccl_example.md)另存单机rank映射和局部打印验收缺口；样例草稿不因本API产品表自动变为已验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL-batch_isend_irecv.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/c10d_npu-ProcessGroupHCCL.md)（constraint）
