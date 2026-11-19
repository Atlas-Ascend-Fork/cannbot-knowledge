---
type: API
title: npu_fused_causal_conv1d：固定核宽与原地历史状态
description: 说明950因果卷积的packed/固定batch输入、残差和APC入口，保留遗留参数与包装传递差异。
tags:
- task.lookup
- topic.compute.neighborhood.convolution
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_causal_conv1d.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dV2NpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d_v2.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-09T07:08:10Z'
updated_at: '2026-11-10T01:37:08Z'
platforms:
- '950'
---

# npu_fused_causal_conv1d：固定核宽与原地历史状态

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交Schema/包装代码，未执行上游实现、图编译或设备实验，不回推发布基线。

## 接口与副作用

```text
npu_fused_causal_conv1d(x, weight, conv_states, *,
    query_start_loc=None, cache_indices=None, initial_state_mode=None,
    bias=None, num_accepted_tokens=None, activation='None',
    pad_slot_id=-1, run_mode=0, residual_connection=0,
    max_query_len=-1, num_computed_tokens=None,
    block_idx_first_scheduled_token=None,
    block_idx_last_scheduled_token=None, initial_state_idx=None,
    block_size=128, conv_mode='default') -> y
```

主线产品页仅950PR/DT推理，单算子和图模式。读取历史缓存做序列头padding、执行逐特征因果卷积，再更新conv_states；Schema显式将状态标为可写，公开只返回同x形状/dtype的y，不另外返回状态。residual_connection=1在卷积后加原x，0关闭，不能与在输入端加残差互换。

x与conv_states可非连续，weight必须连续，三者同FP16或BF16、ND且非空。weight=(3,D)，核宽固定3；不是一般可变卷积核的接口。D为64..16384且16对齐，batch为1..256，不支持Inf/NaN输入。

## 输入场景

|场景|x|历史容量与长度|
|--|--|--|
|packed prefill或混合|总token数T×D，query_start_loc长度B+1必传|prefill基础状态末两维(2,D)，混合/投机需扩容；max_query_len按实际较长序列配置|
|packed decode|T×D，单序列长度1..8|T在B..8B，状态容量须覆盖最大token数加1|
|固定batch decode|(B,m+1,D)，m为0..7|状态末两维(2+m,D)|

所有INT32索引和长度Tensor要求连续。query_start_loc是包含起点和终点的累计偏移，长度B+1的最后合法下标是B；产品页写query_start_loc[B+1]为终点属于越界措辞，不能照写。

## 参数边界

conv_mode只按文档使用default(Qwen3-Next)或pangu(Pangu V2)，pangu要求num_computed_tokens；C++把其他字符串也落为default并不构成新模式支持。APC由二维cache_indices等组合启用，需要完整状态索引与已计算token数，见[APC与投机状态集成](../../guides/optimization/torch_npu_causal_conv_state_contract.md)。

产品页将initial_state_mode、bias、activation、run_mode列为无作用遗留参数，但包装仍把它们传到后端，且会把silu/swish映射为不同数值。这里不承诺激活或bias已支持，也不能仅据传参就推翻产品约束；通用使用保持文档默认值，专门需求需验证底层版本。

Meta只返回empty_like(x)，没有完整校验索引、APC、容量和投机接受数；捕获通过不是状态正确性的证明。与[npu_masked_causal_conv1d](npu_masked_causal_conv1d.md)的mask及状态协议不同，不能只按名称替换。

## 验证

对照按序列的历史拼接、K=3卷积、状态更新及残差顺序；同时验收y、被更新状态和未触及请求状态。性能比较包含缓存读写与实际请求调度，不只测一次无历史输入。

## 完整容量与版本差异

主线双语产品页明确950PR/DT，仅推理单算子/图。packed prefill及混合场景总T为[B,1048576]，D为64..16384且16对齐，还要求T*D在[64B,4G]；4G按来源写法保留，不当作字节数。状态第0维至少覆盖batch并覆盖cache_indices的条目规模，所有实际索引仍须落在有效缓存行，不能只按输出shape分配。数值输入不能含Inf/NaN，中间结果也须落在所选FP16/BF16范围。

发布dedc316708372c9a8bfde4527abd2a94b74840f5只有旧参数集，激活关键字叫activation_mode，没有主线的max_query_len、num_computed_tokens、APC索引、block_size和conv_mode。其functional入口显式克隆cache并返回(y,cache_clone)，普通入口才修改cache；主线删除该functional Schema并增加修改x和cache的V2。不能仅替换参数名，把主线Pangu/APC配置发送给发布。

TorchAir发布转换器注册旧functional入口，TensorMove cache后返回GE结果；固定生成GE的输出确为(y,cache)，与发布C++/Meta一致。主线生成GE改为(cache,y)，普通Converter取第二项作为y。迁移时必须核对该版本的输出顺序，不能跨版本解包。主线底层IR残差默认1，但公开Schema、C++和Converter均显式默认0，使用公开入口的默认值。

## 主线测试与文档仍有未决边界

主线5例与发布2例Fused测试全部无条件skip并标950，均未运行。主线参考允许accepted≤seq_len，文档却写≤seq_len-1；单token示例传1、固定3token示例传3也与文字冲突。薄包装和Meta没有完整值域检查，不能借这些示例、参考断言或可推导shape消除差异。

主线prefill测试使用最大长度7且省略max_query_len=-1，与文档prefill的>8条件不同。所谓APC测试的first/last都为0、长度小于128，跨块缓存填充循环没有执行。它们没有证明跨APC块、padding槽、图中的状态回写、多步请求隔离或吞吐正确。文档8个样例也只打印shape，没有实际设备验收结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_causal_conv1d.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dV2NpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
