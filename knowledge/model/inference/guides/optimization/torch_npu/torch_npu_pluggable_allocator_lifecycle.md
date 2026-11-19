---
type: Guide
title: NPUPluggableAllocator：初始化前切换、回调 ABI 与能力边界
description: 限定 A2/A3 的分配器接入，按真实绑定修正 free 回调参数数目，不推定 IPC 和图池自动兼容。
tags:
- task.implementation
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/custom_memory_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.h
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/custom_memory_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/memory.py
  role: implementation
created_at: '2026-11-09T03:52:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# NPUPluggableAllocator：初始化前切换、回调 ABI 与能力边界

## 版本与范围

依据 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 和 PyTorch `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，选取两份来源不冲突的 A2/A3 范围。950DT 的接口产品页与 PyTorch 特性指南仍相互冲突，本卡不承诺该产品；IPC 也不在本卡的稳定平台范围中。

## 加载与切换时机

NPUPluggableAllocator(path_to_so_file,alloc_fn_name,free_fn_name) 用 ctypes.CDLL 加载 so 并查符号；change_current_allocator(new_alloc) 更换当前分配器，不是某个 Tensor 的临时设置。固定实现只允许当前分配器未初始化时切换；已经发生分配后调用会报 Can't swap an already initialized allocator。

应在实际 NPU Tensor 分配前建立新分配器；仅“模型还未创建”不保证第三方代码尚未触发默认分配器初始化。新分配器构造与当前分配器是否已用过需区分，不能把反复切换当作普通运行期配置。

## 以实际绑定确定回调 ABI

固定 Module.cpp、头文件及 raw_delete 一致使用：

```text
alloc: void*(size_t size, int device, aclrtStream stream)
free:  void(void* ptr, size_t size, int device, aclrtStream stream)
```

memory.py 的 free docstring 只写三项，漏了 device，而实际绑定和调用为四项；接口文档的 C++ 示例也含 device。函数同名、可加载和 ABI 正确是不同条件，应按所装版本的真实声明核对；本卡没有编译或加载 so。

实现记录指针的大小、设备和原分配流，释放时取回再调用 free。回调应保证资源归属及异步寿命，不能只保证 malloc 返回非空。该类注明仅 Unix OS 路线，不把接口产品表视为所有操作系统保证。

## 替换分配器不自动继承所有能力

recordStream/eraseStream 及图池 begin/end/release 仅在相应回调存在时执行所指功能，不能凭普通 alloc/free 就假定跨流回收和图捕获生命周期已正确适配。统计/快照和 emptyCache 的若干重载也有未支持或依赖回调的实现，不能把默认缓存分配器的观测结果直接套入。

getIpcDevPtr/shareIpcHandle 在固定实现中明确提示未支持；自定义分配器与 IPC 组合的边界由[IPC 组合卡](torch_npu_custom_allocator_and_ipc.md)持有。

## 验证

记录 alloc/free 的指针、大小、设备、流，检查实际成对释放、重复分配及业务需要的跨流行为。只核对静态实现，未进行编译、so 加载、IPC 或设备实验。

- [自定义分配器与 IPC 的组合证据缺口](torch_npu_custom_allocator_and_ipc.md)
- [默认分配器的统计口径](torch_npu_memory_counters.md)

## 原生CUDA适配页的产品边界

同提交PyTorch2.7.1、2.9至2.14的中文原生CUDA页对NPUPluggableAllocator/change_current_allocator仅列A2/A3，英文七版本明确950DT不支持。保留该原生产品表与前述接口页/特性指南的差异，不由普通分配或MemPool默认分配器的950支持补齐自定义分配器的整体范围；本卡仍限定A2/A3。

## 发布与英文自定义API的完整补充

发布类原型使用npu.NPUPluggableAllocator，主线补memory命名空间；它不是两个不同分配器能力的证明。主线change示例由torch.npu改为torch_npu.npu，实际对象与当前allocator初始化时机仍按前文核对。

两版本C回调样例虽然标“安全”，但aclrtMalloc没有查返回值、失败指针也未完整初始化，device/stream参数未用于切换或异步寿命处理；不能当生产错误处理范本。页面外链test从发布分支改master，不自动把外部测试视为当前固定提交的已执行证据。主线独立页列950DT仍与原生清单冲突，本指南继续限定A2/A3。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/custom_memory_allocator.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.h)（header）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPUPluggableAllocator.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/custom_memory_allocator.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch-npu-npu-NPUPluggableAllocator.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch-npu-npu-change_current_allocator.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/memory.py)（implementation）
