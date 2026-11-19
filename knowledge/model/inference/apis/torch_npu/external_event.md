---
type: API
title: ExternalEvent：图外事件的record、wait与reset边界
description: 保留单流限制和自动复位冲突，区分Host提交、设备依赖与reset弃用提示。
tags:
- task.lookup
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/streams.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/streams.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu_list.md
  role: constraint
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# ExternalEvent：图外事件的record、wait与reset边界

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 构造与三种操作

`torch_npu.npu.ExternalEvent()`包装AscendCL Event，NPUGraph捕获时作为外部节点建立图内外顺序。每对象占32B设备资源，数量还受硬件限制；不是无成本的任意事件池。发布A2/A3训练/推理及旧Atlas，主线新增950DT。

record(stream)将指定流之前已提交任务纳入事件顺序，提交返回不等于设备已执行。wait(stream)约束该流后续执行，不是全设备或CPU阻塞同步；可先wait后record。独立wait页要求**单Stream等待单Event**并说明wait自动复位，但总目录页声称多个Stream可等同一个Event；保留冲突，不能把目录短句作为多流扇出配方。

## reset的文档与实现差异

中文reset页称因wait自动复位，后续版本废弃reset；主线英文还写底层Kernel不再维护、性能/精度不保证。该提示针对reset，不扩成整个ExternalEvent弃用。四个graph_task示例仍手工wait+reset，不能以样例覆盖接口限制。

两固定streams.py的旧docstring仍称复用前需reset，与API页自动复位有张力；包装默认stream=None会取当前流，而API页面以stream必填简写展示。构造传graph_external=True、enable_timing/blocking/interprocess均False；这些默认不是普通Event的所有能力保证。reset包装要求用户保证流任务完成，不能把它当CPU清理对象的无顺序操作。

图捕获、信号生产者/消费者、事件复用及内存生命周期需一并核对，未通过多次重放和异常路径验证前不承诺无死锁；本次未运行捕获或事件操作。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().record().md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().reset().md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent().wait().md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-ExternalEvent.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/streams.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/streams.py)（implementation）

- [总目录冲突的固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_list.md)（constraint）

- [总目录冲突的固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu_list.md)（constraint）

- [总目录冲突的固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu_list.md)（constraint）
