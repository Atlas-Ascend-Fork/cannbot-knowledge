---
type: API
title: npu_ffn_to_attention：A3 回传的 token 定位与专用通信域
description: 说明有效 token 数、目标 Attention 映射、形状文字歧义及通信域不得混用的要求。
tags:
- task.lookup
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_to_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_ffn_to_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_ffn_to_attention.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_to_attention.py
  role: implementation
created_at: '2026-11-09T08:36:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
---

# npu_ffn_to_attention：A3 回传的 token 定位与专用通信域

## 固定版本与执行形态

来源为OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 产品页、生成包装配置及Meta，图路径另核对TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品仅Atlas A3；该场景的“本卡”按单DIE计，不按双DIE物理卡数计算world_size。不能外推A2或950。两主线是否配套仍需独立核对。

这两个接口都返回空结果`()`，其作用是向对端通信窗口写入数据/状态，不返回接收Tensor。Schema为无返回，Meta也直接return，但显式has_side_effect登记；不能因没有输出消费者就把调用当作无效计算删去。生成包装分别直调对应aclnn，GE Converter直接建相应通信节点；这些薄层没有完成参数语义、窗口容量或对端就绪验证。配置中的all_version是生成范围，不能理解为所有历史CANN、产品都支持。

通信组名长度1..127，world_size范围2..768。分离系列算子和对端窗口协议需配套；来源示例先注册并交换窗口后再发起调用。私有_window_register_and_exchange只是固定版本示例的准备步骤，不是用sleep(10)即可替代的通信协议，也不表示两个传输接口本身已包括完整FFN调度、专家计算、回收和加权合并。

## 接口与图模式

```python
torch_npu.npu_ffn_to_attention(x, session_ids, micro_batch_ids, token_ids,
    expert_offsets, actual_token_num, group, world_size,
    token_info_table_shape, token_data_shape, *, attn_rank_table=None) -> ()
```

用于Attention/FFN分离链路的FFN回传，固定页给单算子与静态图示例；图模式只按dynamic=False接入，不因Converter存在就承诺动态图或训练反向。

## 有效行数与目的位置

x为FP16/BF16 ND二维[Y,H]，Y是本DIE最大可分发token容量。session_ids、micro_batch_ids、token_ids、expert_offsets均为INT32 ND一维[Y]，分别选择目标Attention Worker、micro-batch、batch内token及该token的专家槽位。它们的值分别位于对应目标数量、MicroBatchNum、BS和ExpertNumPerToken范围内。数据及这些索引允许非连续。

actual_token_num为INT64 ND [1]，值0..Y，表示真正发送的token数；不能把Y容量自动当作有效行数，也不能因本次少发token就改变通信双方的窗口形状。ExpertNumPerToken=K+sharedExpertNum，K为1..16，共享专家数0..4，BS为1..512，MicroBatchNum当前仅1；FFN与Attention Worker数量均须大于0且小于world_size。

attn_rank_table是INT32 ND可选映射。参数文字写shape[Y]，但两个示例都用arange(attention_worker_num)，长度为Attention Worker数；语义为Worker到实际卡ID映射，页面的值范围又写0..attnRankNum-1。Meta不校验、生成包装和GE均直接透传，尚不能从这些薄层确定非平凡映射的完整合法长度/值域。保留此歧义，不能直接把示例构造当作任意部署的已确认契约。

## 窗口形状与通信域

token_info_table_shape含[MicroBatchNum,BS,ExpertNumPerToken]，token_data_shape再包含数据/scale长度HS。group、world_size、两组shape与HCCL_BUFFSIZE在所有rank、各层保持一致；本接口的通信域中不允许有其他算子，不能把通用EP组里插入其他collective当作已支持混用。

固定页把x的H范围写为[1152,8320]，把含hidden与scale的HS写为[1024,8192]；示例却取x列H=7168、窗口HS=H+128。两组范围与变量语义存在反常，不能自行对调后写成正式要求，也不能强制所有回传x都附加128列。应核对实际配套窗口协议和底层接口，本文保留原页范围及歧义，不给未证实的统一长度公式。

- [Attention 到 FFN 派发](npu_attention_to_ffn.md)
## 核验

检查真实DIE/rank布局、发送者到接收者映射、窗口注册/容量、token计数与ID范围，覆盖非连续输入及无效token剪枝。编译时检查通信节点保留与先后依赖，执行时检查远端窗口状态/数据和后续消费者就绪，而不是仅检查返回None或本地Python调用结束。

本文仅静态审阅，未执行示例、上游测试、NPU或多卡通信；没有吞吐、延迟或正确性实测结论。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布样例、独立协议和测试边界

发布中文与主线中英文的回传范围一致，均为A3推理及静态图。英文把token_ids文字误写成micro-batch索引，中文及参数组合指向batch内token位置；不能将它与micro_batch_ids交换。H、HS和attn_rank_table的文字/样例差异在两版都存在，薄包装与GE直接透传，仍不能替文档歧义给出通用合法映射。

回传样例使用16个设备、前11个Attention Worker和后5个FFN Worker；派发页主线样例却用4个设备、前3个FFN Worker。两份发送者样例不是同一端到端部署，不能直接拼接，其他角色sleep也不等于接收、专家计算和完成状态都已实现。窗口注册、域专用性、各rank形状及HCCL_BUFFSIZE一致均是独立前提；sleep不能替代就绪协议。

两版测试每份只有一个通信入口，明确unittest.skip并要求16个NPU。装饰器列950不能扩充仅A3的公开产品契约。测试静态使用BF16、固定映射和量化模式0，没有建立非连续、任意映射、异步或跨层场景的数值证明。原始窗口地址及create_npu_tensors视图只说明这个固定测试的消费布局，不作为调用方手工生产通用窗口协议的教程。

Schema无返回、Meta的has_side_effect及GE通信节点只保留调用语义，没有完成窗口容量、ID范围或远端就绪的验证。本文未运行多卡、进程或端口样例，不把跳过测试计为verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_to_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn_to_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_ffn_to_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_ffn_to_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_to_attention.py)（implementation）
