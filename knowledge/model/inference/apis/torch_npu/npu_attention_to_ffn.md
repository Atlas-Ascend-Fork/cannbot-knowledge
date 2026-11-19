---
type: API
title: npu_attention_to_ffn：A3 分离部署的派发与动态量化
description: 记录无返回通信副作用、专家映射、前缀 active_mask、静态图和窗口配套约束。
tags:
- task.lookup
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_to_ffn.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_attention_to_ffn.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_attention_to_ffn.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_to_ffn.py
  role: implementation
created_at: '2026-11-09T08:36:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
---

# npu_attention_to_ffn：A3 分离部署的派发与动态量化

## 固定版本与执行形态

来源为OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 产品页、生成包装配置及Meta，图路径另核对TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品仅Atlas A3；该场景的“本卡”按单DIE计，不按双DIE物理卡数计算world_size。不能外推A2或950。两主线是否配套仍需独立核对。

这两个接口都返回空结果`()`，其作用是向对端通信窗口写入数据/状态，不返回接收Tensor。Schema为无返回，Meta也直接return，但显式has_side_effect登记；不能因没有输出消费者就把调用当作无效计算删去。生成包装分别直调对应aclnn，GE Converter直接建相应通信节点；这些薄层没有完成参数语义、窗口容量或对端就绪验证。配置中的all_version是生成范围，不能理解为所有历史CANN、产品都支持。

通信组名长度1..127，world_size范围2..768。分离系列算子和对端窗口协议需配套；来源示例先注册并交换窗口后再发起调用。私有_window_register_and_exchange只是固定版本示例的准备步骤，不是用sleep(10)即可替代的通信协议，也不表示两个传输接口本身已包括完整FFN调度、专家计算、回收和加权合并。

## 接口

```python
torch_npu.npu_attention_to_ffn(x, session_id, micro_batch_id, layer_id,
    expert_ids, expert_rank_table, group, world_size,
    ffn_token_info_table_shape, ffn_token_data_shape,
    attn_token_info_table_shape, moe_expert_num, *, scales=None,
    active_mask=None, quant_mode=0, sync_flag=0, ffn_start_rank_id=0) -> ()
```

支持推理、单算子示例与静态图，图模式显式dynamic=False；当前X=1、L=1，不从micro-batch维度的存在推导多组/多层支持。group、world_size、moe_expert_num在所有rank及网络不同层保持一致。

## 输入与派发映射

- x为FP16/BF16 ND，[X,BS,H]，H∈[1024,8192]，BS为1..512；支持非连续Tensor。
- session_id、micro_batch_id、layer_id为INT32 ND，[X]；分别标记Attention域本DIE、micro-batch组与层，不能把局部Attention索引直接换成全局rank而不核对映射。
- expert_ids为INT32 ND，[X,BS,K]；1≤K≤16且K≤moe_expert_num，同token的K个专家不能重复，取值0..moe_expert_num-1。moe_expert_num为1..1024。
- expert_rank_table为INT32 ND，[L,shared_expert_num+moe_expert_num,M]，调用方保证实际部署映射正确；共享专家数0..4，M随部署确定，不是固定常数。上述ID/表Tensor允许非连续。
- ffn_token_info_table_shape为长度3的FFN状态表形状，ffn_token_data_shape为长度5的数据窗口形状，attn_token_info_table_shape为长度3的Attention状态表形状；含Attention节点数、micro-batch、BS、每token含共享专家的派发槽位和数据长度等维度，必须与对端布局一致，不能传本地x.shape代替。

## 量化、剪枝和完成语义

quant_mode只支持0（非量化）或2（动态量化）。0时scales必须None；2时scales可选，提供时是连续FP32 ND，[L,shared_expert_num+moe_expert_num,H]。其含义是派发量化参数，不能把专家权重矩阵当scales输入。动态量化窗口的数据长度需与所用协议相符；示例的H+128布局只是该示例配置，不作为所有形状通用公式。

active_mask是BOOL ND，[X,BS]，允许非连续；True参与通信，必须形成True在前、False在后的前缀，不能传True/False交错的稀疏掩码。None表示全部参与。sync_flag仅0同步/1异步，默认0；异步发起并不证明远端消费者此时可读，必须遵循配套状态协议。ffn_start_rank_id为0..world_size-1的FFN域起始ID。

调用前核对HCCL通信缓冲区大小，文档默认200MB；不能用示例里某个window_size字节常量替代实际容量核算。

- [FFN 到 Attention 回传](npu_ffn_to_attention.md)
## 核验

检查真实DIE/rank布局、发送者到接收者映射、窗口注册/容量、token计数与ID范围，覆盖非连续输入及无效token剪枝。编译时检查通信节点保留与先后依赖，执行时检查远端窗口状态/数据和后续消费者就绪，而不是仅检查返回None或本地Python调用结束。

本文仅静态审阅，未执行示例、上游测试、NPU或多卡通信；没有吞吐、延迟或正确性实测结论。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布样例修正与容量差异

完整主线中英文和发布中文均只公开A3推理。主线补充expert_rank_table的M为部署维度说明，不把某个固定M推广到所有副本映射。相同token的K个MoE专家ID仍必须唯一，active_mask仍只能是True前缀，默认同步也不替代接收方状态检查。

发布中文样例把_window_register_and_exchange错接到torch.device对象中，括号结构存在语法错误；主线修正该调用，并把若干写死rank偏移改成dev_num、修正专家ID示例及增加子进程exitcode检查。这些是固定快照样例的差异，不能保证修正后整个分离部署已通过运行验证。

派发样例window_size=120*1024*200实际为23.4375MiB，与页面默认通信缓冲200MB以及回传页的200MiB窗口不同。样例常量不能替代容量核算或HCCL_BUFFSIZE配置。派发与回传样例的设备数和FFN位置也不同，需统一角色、窗口和映射后才能验证同一流水线。

## 无返回副作用与有限参考

两版Schema的返回均为()，Meta显式has_side_effect后直接return，四份通信GE转换器仅转发参数。它们没有检查所有shape、动态量化scales、前缀mask或映射值；静态编译存在对应节点不代表异步传输已完成或支持动态形状。

两版单入口测试均skip且要求16设备，仅覆盖静态BF16、quant_mode=0、默认sync_flag，未覆盖quant_mode=2、sync_flag=1、非零FFN起始rank、有效mask、多个micro-batch或层。参考用session取模选择副本，共享专家槽位固定写成expert_num-1，在本例K等于MoE专家数时恰好匹配，不能当作任意top-K映射公式；mask虽被构造却未用于全量断言。固定原始窗口视图、sleep和单例参考均不能推广为完整生产协议或通用黄金结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_to_ffn.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_attention_to_ffn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_attention_to_ffn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_attention_to_ffn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_to_ffn.py)（implementation）
