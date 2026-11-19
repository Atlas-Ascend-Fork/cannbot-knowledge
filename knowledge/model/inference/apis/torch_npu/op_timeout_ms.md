---
type: API
title: set_op_timeout_ms：算子毫秒超时与图副作用标记
description: 区分算子执行超时与设备/通信超时，记录主线Dispatcher包装及Fake分支边界。
tags:
- task.lookup
- task.debugging
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# set_op_timeout_ms：算子毫秒超时与图副作用标记

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 参数和适用范围

`torch_npu.npu.set_op_timeout_ms(timeout)`接收int，单位**毫秒**，设置NPU算子执行超时时间；无返回数据对象。发布A2/A3训练/推理及旧Atlas，主线另列950DT。页面未给完整默认、上下界和所有错误恢复机制，不自行补成可用0/负值关闭的合同。

它与ACL_DEVICE_SYNC_TIMEOUT的秒单位设备同步等待、HCCL连接/执行超时不同。提高算子超时不修复死锁、错误依赖或其他通信超时。

## 两固定包装的不同

发布utils.py懒初始化后直接调用_C._npu_set_op_timeout_ms。独立主线定义npu::set_op_timeout_ms(int)->None的FRAGMENT算子，注册PrivateUse1/BackendSelect/CPU实现，给FX标has_side_effect并注册空Fake实现，公开函数改调torch.ops.npu.set_op_timeout_ms。

Fake空实现不会设置真实设备超时；图中存在该节点、编译成功或假执行返回不证明真实runtime已应用。此处只审阅Python注册，不宣称所有捕获/后端均能重放该状态副作用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-set_op_timeout_ms.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）
