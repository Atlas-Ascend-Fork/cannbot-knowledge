---
type: API
title: npu_batch_nms：旧产品、FP16和四输出有效数
description: 保留旧Atlas范围与批次/类别维，避免用contrib支持表补齐底层产品证据。
tags:
- task.lookup
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_batch_nms.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_batch_nms.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_batch_nms.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNMSKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNMSKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-09T20:42:31Z'
platforms: []
---

# npu_batch_nms：旧产品、FP16和四输出有效数

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## 未映射平台的原因

两版本产品页只列旧Atlas训练910及推理310p，没有A2/A3或950的独立确认，因此本卡draft、platforms为空。contrib上层页面支持范围、schema all_version或源码存在不能自动改这张底层页的范围；计划废弃且底层不维护，不建议新模型依赖。

## 输入和参数

boxes为FP16(B,N,q,4)，q=1或类别数C；scores为FP16(B,N,C)，B必须一致。score_threshold、iou_threshold是float阈值；max_size_per_class限制每类，max_total_size限制每批。change_coordinate_frame=False控制输出坐标正则化，transpose_box=False使用(N,4)，True用(4,N)排列。包装还明确拒绝空boxes，不从缺少更多本地检查推断任意形状均可用。

## 四输出

nmsed_boxes(B,max_total_size,4)、scores/classes(B,max_total_size)文档均FP16，nmsed_num(B)为INT32有效数量；labels不是默认INT64。实现按boxes的options分配前三输出，不能据这种宽松分配扩展到任意dtype。填充容量与有效数分开，[contrib多类NMS](contrib_multiclass_nms.md)会丢弃底层有效数，无法从其固定长度反推出有效检测数量。

发布样例用FP32且scores的B=3而boxes B=8，主线改为FP16及同B=8；旧例不作可用参数或性能依据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_batch_nms.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_batch_nms.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_batch_nms.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BatchNMSKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BatchNMSKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
