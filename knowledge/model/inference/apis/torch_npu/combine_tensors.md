---
type: API
title: NPU Tensor合并API：值拷贝、局部视图与指针有效性
description: 区分组合存储和torch.cat，保存偏移单位、空输入、有限有效性检查和底层边界缺口。
tags:
- task.lookup
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-get_part_combined_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-get_part_combined_tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-get_part_combined_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-is_combined_tensor_valid.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-is_combined_tensor_valid.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-is_combined_tensor_valid.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-npu_combine_tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-npu_combine_tensors.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-npu_combine_tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/combine_tensors.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/combine_tensors.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ChangeDataPtr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ChangeDataPtr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NPU Tensor合并API：值拷贝、局部视图与指针有效性

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 三个入口

```text
npu_combine_tensors(list_of_tensor, require_copy_value=True) -> Tensor
get_part_combined_tensor(combined_tensor, index, size) -> Tensor
is_combined_tensor_valid(combined_tensor, list_of_tensor) -> bool
```

均位于torch_npu.utils。文档要求连续、同dtype的NPU Tensor；combine分配一段新存储，把原Tensor指针指向对应偏移，原Tensor之后访问该区域，不等同torch.cat只返回新值而保持原存储不动。默认复制原值；False在所查实现跳过原值复制，新组合缓冲由zeros分配，不能再把原Tensor值视为保留。

## 两固定PyTorch实现的补充

两版combine对空列表或总storage元素数0返回None；None元素、dtype不同或非NPU会报错。主线新增显式contiguous检查，发布包装层没有这项显式判断，文档前提仍须满足。包装只检查设备类型，未逐一确认相同设备编号，新分配在当前NPU，不能作为跨卡合并配方。

get_part对combined=None或size=0返回None，否则检查index+size不超过get_storage_size，再分配并重定向。偏移由storage元素数累加；C++按有类型指针加index，**不是字节偏移**，底层只支持FP32/FP16/BF16及相同dtype。文档泛称内存大小不能扩大为任意dtype合并。

is_combined_tensor_valid对空列表返回True、combined=None且非空列表返回False；只检查各Tensor非None及data_ptr起点在组合缓冲内，主线另外检查连续。它没有在这段包装中验证完整尾部范围、逐Tensor dtype、重叠和分片覆盖，True不等于所有别名、边界及所有权已被证明。

## 边界校验与存储寿命

两版ChangeDataPtr.cpp按类型指针偏移，却用`index + dst_storage_size * element_size <= src_storage_size * element_size`做边界检查，index与其余字节量混用；不能把这个检查当完整元素边界证明。调用者保持有效非负偏移、完整目标storage范围和正确设备/dtype，不能靠有效性探针绕过前提。

指针设置没有在此路径建立源Tensor所有权关联，应保持组合缓冲及相关异步消费者所需资源的寿命，避免只留下局部Tensor后丢弃真实存储。主线在重定向前针对待处理DVM数据加入flush，发布无该分支；这不等于所有流均同步完成。结合[融合优化器生命周期](../../../training/guides/torch_npu_fused_optimizer_lifecycle.md)核对参数/梯度持有者，未运行指针改写或设备测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-get_part_combined_tensor.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-get_part_combined_tensor.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-get_part_combined_tensor.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-is_combined_tensor_valid.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-is_combined_tensor_valid.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-is_combined_tensor_valid.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-npu_combine_tensors.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-npu_combine_tensors.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-npu_combine_tensors.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/combine_tensors.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/combine_tensors.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ChangeDataPtr.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ChangeDataPtr.cpp)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py)（implementation）
