---
type: Guide
title: 因果卷积的APC、投机接受与状态隔离
description: 按950固定接口管理冷启动、读写缓存行与状态容量，保留接受数量和遗留参数的未决边界。
tags:
- task.implementation
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
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
updated_at: '2026-11-14T01:59:28Z'
platforms:
- '950'
---

# 因果卷积的APC、投机接受与状态隔离

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交Schema/包装代码，未执行上游实现、图编译或设备实验，不回推发布基线。

## 适用场景

在950使用[npu_fused_causal_conv1d](../../apis/torch_npu/npu_fused_causal_conv1d.md)做packed prefill、混合或投机decode时，输出正确还需要历史状态与调度记录一致。下面以文档的K=3、FP16/BF16模型为范围，不扩展到其他因果卷积接口。

## 按请求组织状态

先确定每请求实际长度、query_start_loc累计起止、缓存行和已计算token数。首轮num_computed_tokens=0时文档读取逻辑使用零历史，普通历史路径从状态尾部取K-1个token；这不等于每次自动清零整块conv_states，复用请求槽仍须遵守生命周期。

没有APC时cache_indices为一维请求到状态行的映射，None时按batch序号。不得在同次调用中复用本应唯一的状态行索引；状态共享、跨流并发和请求回收需要调度层明确安排，Meta不检查这些值。

## APC不是只传二维索引

二维cache_indices=(B,maxNumBlocks)表示APC，需同时提供num_computed_tokens、block_idx_first_scheduled_token、block_idx_last_scheduled_token和initial_state_idx。每请求满足initial_state_idx≤first+1、initial_state_idx≤last、first≤last<maxNumBlocks；maxNumBlocks覆盖ceil(max_query_len/block_size)，block_size≥2，文档典型值128/256不是任意实现都已验证的调优空间。

读取行由cache_indices[b,initial_state_idx[b]]决定，写回当前末块的行并在跨块边界填充历史。只比对最终y会漏掉APC缓存错误，应检查读行、写行、完整块边界和未写行内容。

## 投机decode与容量

固定batch每次输入m+1个token，m为0..7，状态容量2+m；packed decode每请求1..8，文档另要求状态长度大于本批最大token数加1。混合路径不能沿用纯prefill仅2行历史容量。

num_accepted_tokens非空时文档令读取offset=accepted-1；约束段又要求accepted>0且≤当前请求token数-1。单token没有可满足该正值范围的接受数，因此不从默认decode长度1构造强行传1的通用配方；没有投机需求时保留None，投机回滚语义按实际生成策略和版本单独验收。

Pangu模式在已计算token不足K-1时先将部分卷积输出重置为0，再做可选残差相加；重置后加残差与最后把完整输出置零不同。不要把“输出开头非零”直接判断成冷启动失败，应对照residual_connection。

## 验收与停止条件

用两个不同请求交错调度，覆盖首次、连续decode、跨APC页边界及投机接受数量变化；对照历史、y和所有相关状态行。索引重复、容量不足、接受数量不满足文档或参数模式含糊时先解决契约，不能凭一次图捕获成功继续复用错误状态。当前只有静态审阅，没有状态机/NPU运行验证。

## 迁移时区分三种状态协议

发布旧functional入口克隆缓存，Python返回(y,cache_clone)，调用方若要继续历史必须显式接续该新状态；发布普通入口则修改传入cache。主线普通入口修改cache并返回新y，不能套用functional的双返回接法。主线生成GE输出顺序也从发布的(y,cache)变为(cache,y)，由各自Converter适配，不在应用代码中混用底层顺序。

主线另有npu_fused_causal_conv1d_v2的实现分支：Schema将x与conv_states都标为可写，返回()；C++返回void、Meta返回None，图Converter为副作用适配返回x_out。应用不能把这个内部图返回当作Eager返回值，或直接用y=V2(...)替代普通接口。该分支没有独立产品页，不因与普通接口同名或测试标950而追加所有产品、版本或性能承诺。

发布激活参数名为activation_mode，主线改activation并增加APC/Pangu相关参数；发布参考还使用initial_state_mode与run_mode处理历史。主线把这些参数列为遗留无作用的文字不能向发布传播。同一aclnn名称也不保证不同版本形参、状态协议完全相同，必须固定整套配对。

## 先核对约束再验证缓存

接受数文字≤seq_len-1、主线参考≤seq_len以及文档单token/固定长度样例的冲突都保留；没有用未运行参考覆盖产品约束。max_query_len必须按实际模式填写，不能把测试省略为-1当作prefill的通用配置。padding槽的参考有主线初始化1、发布初始化0的差异，而C++新y只是分配；未参与计算的行不保证统一置零，应只消费有明确有效性的请求输出。

当前APC测试长度均小于块且first=last=0，代码里存在跨块循环不等于测试执行过跨块填充。实际验收需要至少一次first<last的合法跨块调度，同时核对读初始行、完整块边界回填、当前末块写回、未写行以及下一次调用历史；只比较最终y会遗漏缓存错误。

普通5例、V2 3例、旧发布2例均无条件skip。V2测试比较修改后的x和cache，但没有图模式闭环，也不证明节省分配或加速。以上只是静态可复核的使用边界，没有执行上游或NPU状态机测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_causal_conv1d.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedCausalConv1dNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_causal_conv1d.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedCausalConv1dV2NpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_causal_conv1d_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_fused_causal_conv1d.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
