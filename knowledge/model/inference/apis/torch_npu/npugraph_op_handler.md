---
type: API
title: NpuGraphOpHandler：注册、预分配与版本化参数更新
description: 保存无状态类协议、替换函数一致性、弱引用及主线UPDATE_SPECS差异。
tags:
- task.lookup
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/npugraph_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/npugraph_handler.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NpuGraphOpHandler：注册、预分配与版本化参数更新

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 注册及四个Hook

register_npu_graph_handler(op_names)以func.__name__匹配str或名称列表，存**类对象**并返回原类，推荐同时登记plain/.default；替换为.out后还必须为实际函数名登记兼容的update_args。两固定注册器重复名称会警告并覆盖，未做完整继承/协议校验；“注册成功”不代表自定义Kernel的全部图能力已适配。

| classmethod | 输入与结果 |
| --- | --- |
| prepare_capture(func,args,kwargs) | 返回实际func,args,kwargs；在任务组begin前，可预分配out/workspace或换重载；默认透传 |
| postprocess_result(result,kwargs) | 任务组end后整理返回，如TensorList转list；默认result |
| update_args(dispatch_record,update_input) | 更新已录制args/kwargs，不返回新图；版本行为见下节 |
| record_wrap_kwarg(key,value,tensor_param_names) | 捕获时保存kwargs表示，默认按NPU Tensor弱引用和其他值deepcopy |

方法用classmethod，不以self储存调用状态；类级可变属性仍需自律，不把设计意图说成Python已经禁止所有共享可变状态。发布页A2/A3训练/推理及旧Atlas推理卡，主线另列950DT。

## 默认更新行为发生变化

两版本文档均写默认update_args为空，但发布固定实现确为空，独立PyTorch主线已改为声明式UPDATE_SPECS：op名映射若干(loc,index_or_name,key)三元组。get_update_specs取列表，匹配update_input键后，arg在索引范围内写args，kwarg直接写kwargs；没有声明或缺少key时跳过。不能把主线默认机制回推发布，也不能因列表存在推定自动处理任意值、shape容量和错误索引。

调用g.update(cpu_update_input=[dict])再replay，框架按算子找到Handler并更新记录；此协议不自动重新捕获拓扑，也不证明任意batch/seq变更均满足输出、workspace与Kernel容量。

## 弱引用和示例边界

两固定record_wrap_kwarg对None透传；list/tuple逐元素将NPU Tensor包成_C._weak_ref_tensor，其他元素deepcopy，保留容器类型；单个schema指定的NPU Tensor也用弱引用，其余deepcopy。CPU Tensor不走NPU弱引用。弱引用目的不是复制数据或任意延长输入生命周期；更新阶段直接赋值又是另一种所有权路径。

文档示例用私有torch._C._weak_ref，与实际基类的NPU TensorWeakRef不同；发布import拼写register_npu_graph_handle在主线中英文更正为handler。示例自定义schema/Kernel、x/weight/seq_len/new_seq_len并未给出，不能直接运行；预分配两个empty_like也不是任意算子输出规格。源码调用链、输入寿命与多轮重放仍需验证，本次未运行捕获或加载自定义库。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu_npugraph_handlers.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/npugraph_handler.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/npugraph_handler.py)（implementation）
