---
type: API
title: 确定性前后向标记：Tensor 依赖与反向切换
description: 合并说明 enable/disable_deterministic_with_backward 的全局布尔副作用、梯度依赖和禁图条件。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/deterministic.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/deterministic.py
  role: implementation
created_at: '2026-11-09T08:47:30Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 确定性前后向标记：Tensor 依赖与反向切换

## 固定版本与接口

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 两份完整API页及TorchNPU `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的deterministic.py。本卡选择文档声明的A2/A3，不从全局set_deterministic_level支持950DT推导这两个接口也已纳入950。

```python
torch_npu.npu.enable_deterministic_with_backward(tensor) -> Tensor
torch_npu.npu.disable_deterministic_with_backward(tensor) -> Tensor
```

接口在数据上透传Tensor，不做数值转换；dtype/格式按该产品已有PyTorch能力，不能由“无额外约束”扩大底层支持。传入Tensor必须参与最终output及反向依赖链，否则对应反向状态切换不会发生；requires_grad=False、detach或丢弃输出不满足反向触发前提。

## 前向与反向的切换方向

| 标记 | forward | 该标记的backward |
| --- | --- | --- |
| enable_deterministic_with_backward | torch.use_deterministic_algorithms(True) | 切为False，透传梯度 |
| disable_deterministic_with_backward | 切为False | 切为True，透传梯度 |

利用反向执行顺序，在与损失关联的依赖链中放置配对标记，才能为对应区域建立前后向切换。实现操作的是全局布尔状态，不保存任意外层level或先前状态；它不是可任意嵌套、退出自动恢复的上下文管理器，也不只影响被传入的一个Tensor。不要把断开依赖的旁路Tensor当控制令牌，或与其他线程、全局level和局部图scope混配后仍承诺隔离。

## 图模式与验收

两页明确不支持图模式，Python函数也设置_dynamo_forbidden=True。示例虽导入TorchAir并创建backend，实际执行的是Eager model；这不能覆盖禁止入图约束。数据透传也不代表编译器可把状态标记当普通identity删除。

检查标记输出确实进入损失，分别记录前向越过每个边界与反向越过边界时的布尔状态，再对目标区域做重复执行比较。未执行反向时不能据前向状态证明backward切换正确；没有运行验证就不宣称它修复特定模型的非确定性。本文未运行示例或设备测试。

- [全局level接口](set_deterministic_level.md)
- [算法范围与版本冲突](../../guides/torch_npu_deterministic_algorithm_scope.md)

## 发布及英文页补充

两固定OpPlugin版本和主线英文均保留Tensor透传、必须进入output依赖与禁止图模式；产品表未列950，不由全局等级范围扩大。本卡完整核对两个页面的示例都只做前向标志断言，没有backward、编译执行或重复数值验收。TorchNPU发布使用Dynamo的forbid_in_graph，主线改为本地_dynamo_forbidden标记，前后向切换方向不变。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/deterministic.py)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-disable_deterministic_with_backward.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-enable_deterministic_with_backward.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/deterministic.py)（implementation）
