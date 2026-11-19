---
type: Guide
title: 条件节点运行链：预热派发、统一输出缓冲与子图池
description: 区分cond预热和正式捕获，解释双IF子图、false输出拷贝及原生条件/流/内存池门槛。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_conditional_nodes.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp
  role: implementation
created_at: '2026-11-10T13:59:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 条件节点运行链：预热派发、统一输出缓冲与子图池

## 固定入口与证据组合

本卡定向对照TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`独立npugraph_ex调用，与PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的torch_npu条件节点Python/C++消费者；这是两份固定源码的调用核对，不证明它们已配套运行。公开版本、平台及mutation要求继续见[条件捕获文档](npugraph_ex_conditional_capture.md)，整卡平台未知，保持draft、空平台。

AclGraph预热和静态kernel dump通过ControlFlowOpWarmupCtx，正式捕获通过NPUGraphCaptureCtx；enabled=False两者只yield，不安装对应分派Mode。True时由已检查的依赖字典取得torch_npu的warmup或capture Mode。编译侧入口/别名条件另见[编译门控](npugraph_ex_cond_compile_validation_and_unwrap.md)。

## 预热与正式捕获不同

| Mode与状态 | 所读分派行为 |
| --- | --- |
| Warmup且当前流已在捕获 | 在本Mode中直接走if_else_node |
| Warmup且未在捕获 | 在专门capture_stream上的临时NPUGraph中先走if_else_node，再调用普通cond取得本轮结果 |
| 正式Capture Mode遇到cond | 在本Mode中调用if_else_node；其他操作原样转发 |

所以预热不是只执行当前pred选中的一份Python分支，也不是承诺整个预热从不走普通cond或Host条件处理；正式图捕获的设备条件合同与预热准备分开。临时探测、两支Python调用、分配及后续普通cond都是应保留的启动成本，本次没有测量次数或耗时。

## 两个IF子图共用第一支输出缓冲

if_else_node先要求pred位于NPU。随后依次用pred捕获true_fn、用logical_not(pred)捕获false_fn；每支通过_if_body开始IF节点捕获，并在finally结束条件子节点。源码是两个IF子任务，不是在Host以if/else只调用一支。

第二支的捕获体内，按pytree.tree_iter遍历两支输出并zip，向第一支对应叶子执行`if_out.copy_(else_out)`；最终总是返回outs[0]。这样false分支也把值写入统一返回缓冲。它不是先返回任意一支的Python对象，更不是可以因“只需要false输出”而删除的无用拷贝。

这份Python helper没有独立完整检查两树等长、全部叶子类型或shape；zip自身也不是完整结构验收。输出数量/结构、dtype/device/layout/shape一致，以及不能返回operand/view等要求依赖公开合同、trace与编译门控，不能凭copy_存在认证任意分支组合。复制的实际设备成本和编译消除情况未在本次验证。

## 原生条件必须匹配当前图和设备

Python方法经pybind进入NPUGraph::begin_capture_to_if_node。原生层要求图尚未持有可执行实例、当前流处于active捕获，且当前捕获modelRI为root或栈顶条件子图。条件Tensor须PrivateUse1、numel()==1、Bool且设备索引与capture_dev一致；numel为1不等于只接受0维shape。

条件handle的指针非空后，原生在当前流先异步清零uint64缓冲，再从pred bool地址异步D2D复制一个bool字节，不通过这一函数回读Host。Python入口只检查is_npu，不能代替这些更强原生门槛；也不能因接口存在推导驱动/固件条件节点全部可用。

## 子流、共享图池与恢复

原生添加IF任务取得非空child modelRI，在同一mempool_id下先停止root/当前分配过滤，再切换为按child capture id匹配的Host与NPU分配过滤。随后从池取child stream，开始向该child modelRI捕获，并将modelRI/流及捕获图关联压入状态。

结束时从当前child流停止捕获，校验结束modelRI，弹出栈并恢复root过滤，或嵌套时恢复父child过滤。这里的流/模型ID检查与池归属是实际消费者，不代表每个分支拥有独立无共享Storage；更不证明任意跨流用户事件或输出保存安全。公共分支内创建Event、scope和mutation限制仍适用。

末尾若发现generator在child capture id上有捕获状态就报不支持数据依赖条件节点内RNG。所读路径没有给所有异常步骤提供完整事务回滚保证；_if_body的finally也不能证明native开始失败前后全部资源已恢复。未执行捕获、随机数、流、精度、内存或性能实验，未新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py)（primary）：定向范围52–94, 543–557。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：定向范围1178–1205, 1543–1548。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_conditional_nodes.py)（implementation）：定向范围1–86。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp)（implementation）：定向范围864–874。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp)（implementation）：定向范围535–722。
