---
type: API
title: 旧Tensor创建与写回：empty_with_format、copy_memory_和one_
description: 区分未初始化分配、原始内存复制和原地填充，保留废弃及替换语义。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-copy_memory_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-empty_with_format.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-one_.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyMemoryKernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyMemoryKernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 旧Tensor创建与写回：empty_with_format、copy_memory_和one_

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。未导入上游、加载模型、执行设备、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡来源范围，不作已闭合结论。


## empty_with_format

发布页计划废弃，建议torch.empty。创建未初始化内容，不能将示例全1当初始化保证。size为整数序列；dtype/device默认None，layout默认strided，acl_format默认2，pin_memory为可选项。两固定TorchNPU声明还含关键字base_addr_aligned_kb，不能由这份旧页面推断其硬件语义或任意pin_memory组合可用。

## copy_memory_与普通copy_不同

发布页建议迁移Tensor.copy_，旧接口只允许NPU、同dtype和设备index，原地返回self。两固定实现复制连续物理内存、忽略格式；padded存储要求offset0，长度按目标逻辑/存储大小计算。源码虽然计算src_size，实际传入复制的是目标字节数，没有在这一包装比较源容量，也没有普通copy_的广播/布局转换协议。不能仅满足dtype/device就认定任意大小或不同格式安全等价。

non_blocking=False还显式同步当前流；True只省去该同步，不证明数据已就绪或与计算实际重叠。迁移须保持逻辑值、shape、别名、格式与消费者顺序。

## one_和替代选择

one_(self)用1原地填充并返回self；发布页计划废弃，给fill_或ones_like。实际Tensor写法可用self.fill_(1)，ones_like分配新Tensor，不能保持所有原地别名语义。不要将创建、复制和填充合并为“零分配”优化；旧页主线未收录也不直接证明实现已删除。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-copy_memory_.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-empty_with_format.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-one_.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyMemoryKernel.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyMemoryKernel.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
