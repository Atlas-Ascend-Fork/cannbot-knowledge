---
type: API
title: 旧浮点状态Tensor：alloc/get/clear及不维护边界
description: 区分状态Tensor和新溢出API，保留get返回类型与clear结果不保证零值的实际路径。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_alloc_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_clear_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_get_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧浮点状态Tensor：alloc/get/clear及不维护边界

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## 接口与来源限制

npu_alloc_float_status(input)、npu_get_float_status(self)、npu_clear_float_status(self)均计划废弃且底层不再维护，文档明确不保证性能/精度。不要与torch_npu.npu命名空间的[溢出状态查询](overflow_state.md)混为同一接口；这些旧页未列950。

文档alloc给FP32的8元素全零状态Tensor，input用于设备信息；get/clear输入FP32。两版声明还含get/clear的mode=0，1为调试模式，只接受0/1。旧示例任意rand(2)不构成完整状态Tensor初始化协议，状态清除窗口也不由输入名字自动建立。

## 版本实现的返回值区别

两版FloatStatusKernelNpu.cpp逐字节相同：普通mode在较新SoC走V2，get返回新分配INT32[8]，旧分支调用NPUGetFloatStatus后返回self，不可把所有get返回都当INT32或新对象。debug get同样INT32[8]。

clear先分配result；V2/debug清状态调用没有把result作为Output写入，因此不能消费其返回内容为文档所称“全零”的可靠检测信号。旧分支才向Kernel传self/result。入口存在或不抛异常不证明清除/查询值已有效，需按具体计算模式和实际环境核验；本卡不提供这些不维护接口的新模型优化配方。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_alloc_float_status.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_clear_float_status.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_get_float_status.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
