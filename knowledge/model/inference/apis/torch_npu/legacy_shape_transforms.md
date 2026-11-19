---
type: API
title: 旧形状变换：广播、reshape、转置及融合顺序
description: 记录旧接口迁移和真实分配路径，避免把连续输出当作普通共享视图；含 npu_confusion_transpose 实现层的 950
  门控与反向逆 perm。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_broadcast.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_confusion_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_confusion_transpose.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_confusion_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_reshape.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TransposeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TransposeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReshapeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReshapeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BroadcastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BroadcastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConfusionTransposeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConfusionTransposeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConfusionTransposeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConfusionTransposeKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 旧形状变换：广播、reshape、转置及融合顺序

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。未导入上游、加载模型、执行设备、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡来源范围，不作已闭合结论。


## 广播与reshape

npu_broadcast(self,size)计划废弃，文档称新视图且连续；两实现实际分配输出，BOOL经INT32再转回，私有格式可能先转base。torch.broadcast_to的视图/stride/别名不能由这个旧包装直接继承，迁移后核对写回行为。

npu_reshape(self,shape,can_refresh=False)计划用torch.reshape替换，旧原型里bool类型标识不是可执行Python签名。两个ACL Op及OpAPI包装均先分配result：False复制内存，True只给out设置存储描述，没有把self内容复制过去。不能把can_refresh=True当作任意输入安全原地reshape或新输出已含原数据的保证；接口不能直接经aclopExecute调用。

## transpose与require_contiguous

npu_transpose(self,perm,require_contiguous=True)计划废弃、底层不维护，中文建议permute；声明FakeTensor不证明设备数值。它实际分配并运行Transpose，不能把文档“视图”当共享存储合同。True用普通Input处理输入，False走InputWithoutContiguous，后者服务内部转置连续化场景；文档关于何时设True的文字不完整，不能用False跳过任意不连续张量的处理。

## confusion_transpose

npu_confusion_transpose(self,perm,shape,transpose_first)计划用Tensor.view/permute组合替换。True先转置后reshape，最终shape直接取shape；False先reshape再permute，输出为shape[perm]，perm针对不同阶段。主线修正shape为reshape目标，不能仍按旧“输入shape”说明使用。

源码forward没有完整规范化负perm，main反向另加0<=perm<len检查并换掉变长栈数组。不要因普通permute允许负维就推定此融合入口所有负perm及反向均等价；使用合法非负、不重复排列并核对布局、梯度与分配成本。

## npu_confusion_transpose 实现层：950 门控与反向逆 perm

上文记录的是文档页组合语义；本节覆盖 `ConfusionTransposeKernelNpuOpApi.cpp`（87 行，两 pin 去空白等价）实现层。**版本门控**：`GetSocVersion() < Ascend950` 时前向/反向全部委托 `acl_op`（老 GE AsStrided 实现，行为不变）；950 及以上走 `DO_COMPATIBILITY(aclnnConfusionTranspose, acl_op 回退)`。前向 `npu_confusion_transpose(self, perm, shape, transpose_first)`：`transpose_first=true` 时输出尺寸直接取 shape 原序；false 时按 perm 重排（TORCH_CHECK `shape.size() > perm[i]`，报错文案含 "npu_confusion_transpose forward/backward input invalid"），`apply_tensor_without_format` 分配后 `EXEC_NPU_CMD(aclnnConfusionTranspose, self, perm, shape, transpose_first, y)`。反向 `npu_confusion_transpose_backward_symint`：**逆 perm**（`backward_perm[perm[i]] = i`）+ 同一 `transpose_shape` 规则，输出按 shape 与 `grad.options()` 复用同一条 aclnnConfusionTranspose 命令。设备侧命令语义与 950 以下 acl_op 路径细节不在本卡来源范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_broadcast.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_confusion_transpose.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_confusion_transpose.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_confusion_transpose.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_reshape.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_transpose.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TransposeKernelNpu.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TransposeKernelNpu.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReshapeKernelNpu.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReshapeKernelNpu.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BroadcastKernelNpu.cpp)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BroadcastKernelNpu.cpp)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConfusionTransposeKernelNpu.cpp)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConfusionTransposeKernelNpu.cpp)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [ConfusionTransposeKernelNpuOpApi.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConfusionTransposeKernelNpuOpApi.cpp)（implementation）：全文 87 行；发布去空白等价。
