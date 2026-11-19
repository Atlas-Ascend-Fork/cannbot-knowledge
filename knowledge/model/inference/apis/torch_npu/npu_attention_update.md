---
type: API
title: npu_attention_update：SP 局部 Attention 的稳定合并
description: 按 LSE 权重合并已取得的局部输出，说明 SP/head_dim 范围与 update_type=0 的无效 LSE 槽。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_update.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_attention_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionUpdateKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_attention_update.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_attention_update.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_update.py
  role: implementation
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-10T00:05:16Z'
platforms:
- a2
- a3
- '950'
---

# npu_attention_update：SP 局部 Attention 的稳定合并

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口与计算

```text
torch_npu.npu_attention_update(lse, local_out, update_type) -> (out, lse_out)
```

lse/local_out为相同长度的Tensor列表，长度SP在1..16；每个lse为FP32、shape=(B*S*N,)，对应local_out为FP16/BF16/FP32、shape=(B*S*N,D)。D在8..512且8整除。输入必须连续，支持空Tensor，但空列表不等于空Tensor：包装层读取第0个元素，列表仍要满足SP≥1。

令M=max(lse_i)，全局L=M+log(sum exp(lse_i-M))，out=sum local_out_i*exp(lse_i-L)。不能简单平均局部Attention输出，局部LSE决定归一化权重。输出out同local_out的shape/dtype。

update_type=1时lse_out为FP32的全局L；0时只有out有效。固定包装层仅在1时分配LSE输出，但Python仍返回两个槽，不把第二槽当正常LSE参与后续合并。文档列默认确定性与Eager/GE图示例，这不是所有融合Attention产品矩阵的替代。

接口接收已取得的Tensor列表，包装层直接调用aclnnAttentionUpdate，没有在此实现跨rank取数的HCCL流程。SP通信与本地数值合并分别验收。


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## Meta 与无效输出槽的差别

同提交Meta无论update_type都返回两个非空shape描述，而Eager C++只在update_type=1分配LSE输出；因此Meta显示LSE形状不能证明update_type=0的运行返回槽有效。保留文档的有效性约定，图组合也需核对这一差异，不从符号输出推定真实数据已经生成。

## 两版范围、图转换与跳过的测试

发布公开A2/A3；主线双语增加950PR/DT，并明确不支持非连续输入。空Tensor与空列表分开处理，不能把支持空Tensor解释为允许SP=0。包装依据首个local_out及lse分配输出，未在此核验全部列表长度、FP32 LSE或每个head_dim，仍须满足公开约束。

两固定TorchAir转换器均直接生成ge.AttentionUpdate，SP取len(lse)，没有在该转换器执行通信或补全不匹配的列表。转换器存在只证明所审阅的图转换路径，不是对所有捕获后端、产品或组合输入的验证。

两版同名测试唯一入口都被skip标记为等待CANN支持，拟测范围仅A2、update_type=0和非空输入；不能计作已运行的950、有效LSE输出或空输入覆盖。CPU参考用FP32稳定归一化并在log中加1e-20，再将out转回输入类型。全为负无穷的LSE等边界没有由这段参考确立统一策略，不能自行补成设备承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_update.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_update.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_attention_update.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionUpdateKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_attention_update.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_attention_update.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_update.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_update.py)（implementation）
