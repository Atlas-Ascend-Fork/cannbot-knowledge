---
type: Guide
title: GE工作调度：上下文拷贝与组合参数
description: 对照GE与Eager的上下文隔离，补充Worker token类型、八返回容量及Attention Combine层号Meta分歧。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_worker_scheduler.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_worker_scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/distribute_barrier.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/distribute_barrier.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_worker_scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_worker_scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_worker_combine.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_worker_combine.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_ffn_worker_batching.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_ffn_worker_batching.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionWorkerCombineOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionWorkerCombineOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T09:30:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE工作调度：上下文拷贝与组合参数

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。所选主线完整非空源码、发布完整AST/注释差异已审阅；这批成对Converter的差异为说明字符串、导入顺序、等价异常字符串写法，计算映射不变。QuantMax的同路径仅主线存在，缺路径不推导发布软件缺能力。

本卡限定静态构图及新增OpPlugin Eager/Meta合同，整卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、真机精度/别名/通信或性能实验。Support只是候选，警告和注释不是本次复现。IR参数与真实kernel、调度及外围函数化需分别核对。

## 调度器先隔离上下文

attention_worker_scheduler.default先TensorMove(schedule_context)，再AttentionWorkerScheduler(copy)；ffn_worker_scheduler.default同样复制，再FfnWorkerScheduler(copy,sync_group_size=1,execute_mode=0)。这些拷贝有隔离输入目的，不能凭调度函数名字判为纯读取而删除；实际调度与缓存协议还依赖kernel/调用方。

I8(1024)及sync_group_size/execute_mode的Support候选不是完整上下文布局、合法大小、时序或产品矩阵。本层没有解释schedule_context二进制字段，不能从固定shape示例自行编造ABI。

## 组合与分批参数不做统一类型转换

npu_attention_worker_combine.default直接AttentionWorkerCombine(schedule_context,expert_scales,layer_id,hidden_size,token_dtype=0,need_schedule=0)。npu_ffn_worker_batching.default直接FfnWorkerBatching(schedule_context,expert_num,max_out_shape,token_dtype=0,need_schedule=0,layer_num=0)。两者没有上面调度器的显式TensorMove，也没有本地统一Meta dtype转换或完整的层号、专家、输出shape值域校验。

文件虽然导入dtype_promote，但函数体没有调用；不能把导入当作已完成Cast，更不能直接用token_dtype属性解释数据已经重编码。调度器、combine与batching承担不同合同，不共享拷贝和输出别名保证。

## Eager上下文隔离及Worker输出容量

本节补充OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的四份Worker包装、Schema和局部Meta。两版所述复制、分配和参数分支一致；这些是前端合同，不补造schedule_context内部字段、设备同步或产品矩阵。

### 带下划线与不带下划线的调度器不同

attention_worker_scheduler与ffn_worker_scheduler的Eager实现先按self的shape/options分配out，执行out.copy_(self)，再分别调用aclnnInplaceAttentionWorkerScheduler或aclnnInplaceFfnWorkerScheduler更新**副本**。所以底层ACLNN名称带Inplace不表示不带下划线的Python入口改写原self；与GE先TensorMove的隔离方向一致。Meta仅empty_like，不执行该数据复制。

对应attention_worker_scheduler_和ffn_worker_scheduler_在Schema标注Tensor(a!)输入/返回别名，并由生成配置直接调用同一Inplace ACLNN。不能把两组入口互换后仍假定原上下文保持不变；需要依据调用方生命周期验证。这里读取生成配置，未生成或执行代码。

### Attention Combine的dtype和层号shape

npu_attention_worker_combine的Eager y为[expert_scales.size(0),hidden_size]，沿schedule_context设备分配。token_dtype仅在等于1时选BF16，其余分支分配FP16；本函数没有完整枚举检查，所以不能把token_dtype=2理解成该Combine也返回INT8，更不能把其他整数判为设备支持。

next_layer_id在两版C++都分配INT32[1]，两版Meta却用INT32[layer_id.size(0)]。layer_id长度大于1时存在静态输出规格分歧，Meta成功不能证明真实返回具有相同长度；先核对底层是否本就要求单元素层号，再验实际返回。hidden_size、layer_id内容和need_schedule仍需完整接口/调用链检查，包装没有据此验证上下文就绪。

### FFN Batching的八返回与容量

npu_ffn_worker_batching要求expert_num>0、max_out_shape恰好四个正数、token_dtype为0/1/2、need_schedule为0/1。令Y=max_out_shape[0]*max_out_shape[1]*max_out_shape[2]、H=max_out_shape[3]，返回顺序为：

| 槽 | Eager与局部Meta的分配 |
| --- | --- |
| y | [Y,H]，token_dtype=0/1/2分别FP16/BF16/INT8 |
| group_list | INT64[expert_num,2] |
| session_ids、micro_batch_ids、token_ids、expert_offsets | 各INT32[Y]，四个独立槽 |
| dynamic_scale | FP32[Y] |
| actual_token_num | INT64[1] |

Y是最大输出容量，不是本次有效token数。需要按真实actual_token_num和分组/恢复协议消费，不能把[expert_num,2]直接当作普通GMM的一维cumsum，也不能因dynamic_scale已分配便认定所有token_dtype模式都有有效尺度。包装将Y和H保存为C++ int，Meta使用Python整数，超大max_out_shape还应检查乘积与窄化范围；本次没有做溢出实验。

FFN Batching的INT8分支和Attention Combine的FP16/BF16选择不同，token_dtype不是跨整个Worker链可不加区分套用的统一dtype枚举。评估分离Attention/FFN的优化时，同时记录上下文副本成本、Y容量和实际token量、八输出有效性、层号返回以及真实通信完成条件；不能以一份Meta或GE节点成功证明端到端时序与收益。本次未运行Worker、通信或性能测试。

## 分布式屏障只是GE节点构造

torch.ops.npu._npu_distribute_barrier.default传x_ref、time_out、elastic_info、group及world_size到DistributeBarrier。可选Tensor超时和弹性信息原样传递，本层没有创建进程组、校验成员或在Python执行host barrier，也没有可独立证明的完成/内存可见性协议。

优化应结合调用方核对上下文来源、group/world_size、调度顺序、输出/缓存别名以及实际通信完成条件，再验证性能。不能由节点存在认证跨卡同步、任意elastic配置或无死锁；本次没有执行通信实验。

## 准确映射清单

仅列所选文件实际注册，有构图分支不证明全部参数或产品可用；未声明的其他重载不作能力否定。

| 文件主题 | 准确入口 |
| --- | --- |
| attention_worker_scheduler | `torch.ops.npu.attention_worker_scheduler.default` |
| distribute_barrier | `torch.ops.npu._npu_distribute_barrier.default` |
| ffn_worker_scheduler | `torch.ops.npu.ffn_worker_scheduler.default` |
| npu_attention_worker_combine | `torch.ops.npu.npu_attention_worker_combine.default` |
| npu_ffn_worker_batching | `torch.ops.npu.npu_ffn_worker_batching.default` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_worker_scheduler.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/attention_worker_scheduler.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/distribute_barrier.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/distribute_barrier.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_worker_scheduler.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn_worker_scheduler.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_worker_combine.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_attention_worker_combine.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_ffn_worker_batching.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_ffn_worker_batching.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）

## 补充实现证据

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionWorkerSchedulerKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttentionWorkerCombineOpApi.cpp)（implementation）

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionWorkerSchedulerKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionWorkerCombineOpApi.cpp)（implementation）

- [固定实现来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
