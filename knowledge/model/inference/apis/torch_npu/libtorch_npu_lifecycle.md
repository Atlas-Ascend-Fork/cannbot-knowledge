---
type: API
title: libtorch_npu生命周期API：初始化、同步和收尾
description: 依据固定C++声明与实现区分init_npu重载、无参finalize_npu及current_device未初始化返回值。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/init_npu.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/init_npu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/torch_npu.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10-npu-current_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10-npu-current_device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10-npu-current_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch-npu-synchronize.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch-npu-synchronize.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch-npu-synchronize.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch_npu-finalize_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch_npu-finalize_npu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch_npu-finalize_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch_npu-init_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch_npu-init_npu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch_npu-init_npu.md
  role: constraint
created_at: '2026-11-09T16:32:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# libtorch_npu生命周期API：初始化、同步和收尾

## 版本、声明与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，libtorch_npu构建/使用路径列A2/A3训练系列与950DT；不扩为950PR或其他推理产品，不回推26.0/PyTorch2.8。公共bundle入口torch_npu/torch_npu.h包含init_npu声明头；这里是静态声明/实现核对，没有编译或运行。

```cpp
namespace torch_npu {
void init_npu(c10::DeviceIndex device_index = 0);
void init_npu(const std::string& device_str);
void init_npu(const at::Device& device);
void finalize_npu();
}
namespace torch::npu { void synchronize(int64_t device_index = -1); }
namespace c10::npu { DeviceIndex current_device(); }
```

## 参数与可观察行为

字符串示例为"npu:0"；字符串/Device重载构造或接收at::Device，检查类型为PrivateUse1，再转交设备索引重载。不是CPU/CUDA字符串的通用初始化；也不把无索引"npu"与数值默认0自动视为完全相同。索引重载调用NpuSysCtrl.Initialize，在lazy模式且尚未lazy初始化时继续LazySetDevice/LazyInitialize；失败分支显示错误后return，返回类型void，不能将没有返回值当成功标记。

finalize_npu无参数。文档表格在该行误写输入npu:id，示例与真实声明均无参，以明确声明区分。已初始化时先设备同步，再HostFinalize、清理host/device缓存并系统Finalize；同步/缓存/系统收尾失败可抛错。未初始化时发警告，不承诺幂等成功值或每张卡独立销毁语义。不要在仍有业务任务/活跃资源时把它当普通缓存优化接口。

torch::npu::synchronize用NPUGuard选择设备后调用设备同步，默认索引-1；这是设备同步，不是仅等待某条流的Event。c10::npu::current_device在系统已初始化时读取当前设备，未初始化则警告并返回-1；-1不是实际卡编号，也不据此自动创建设备。

## 使用前后条件

先核对[构建ABI及运行依赖](../../guides/bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)，再初始化、构造NPU Tensor/模型并执行业务，收尾前确认业务生命周期已经结束。来源的初始化调用顺序不能证明任意模型/并发模式正确，设备可用性与最小数值结果仍需实际验证。

## OpPlugin C++接口页的发布与语言范围

补充OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中文及主线英文四类beta页：init_npu三重载、finalize_npu无参、torch::npu::synchronize默认-1、c10::npu::current_device。接口页列A2/A3训练及旧Atlas训练/推理条目，未列950；本卡既有950DT范围来自前述独立PyTorch主线LibTorch指南，不回灌到这些发布页或推定两个main配套。

init_npu索引默认0与synchronize的-1选择当前设备不能混同；finalize_npu是生命周期收尾，不是任意训练中途释放缓存后可无条件重新初始化的优化入口。同步等待所选设备已提交计算，不等同只排空Host TaskQueue。[核心c10_npu设备查询](cpp_device_and_sync_diagnostics.md)与c10::npu属于不同命名空间，不能合并未初始化与错误检查语义。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/init_npu.h)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/init_npu.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/torch_npu.h)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）c10-npu-current_device.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）c10-npu-current_device.md)（primary）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)c10-npu-current_device.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch-npu-synchronize.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch-npu-synchronize.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch-npu-synchronize.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch_npu-finalize_npu.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch_npu-finalize_npu.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch_npu-finalize_npu.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）torch_npu-init_npu.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）torch_npu-init_npu.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)torch_npu-init_npu.md)（constraint）
