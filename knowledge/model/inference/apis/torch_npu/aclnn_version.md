---
type: API
title: aclnn.version：预留查询、警告与None返回
description: 记录版本查询尚未实现，避免把空返回或产品支持表当作ACLNN兼容性检测。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-aclnn-version.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-aclnn-version.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-aclnn-version.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/aclnn/backends.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/aclnn/backends.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# aclnn.version：预留查询、警告与None返回

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 查询合同

`torch_npu.npu.aclnn.version()`无参数，两版本文档均说明暂不支持、默认返回None。产品表发布列A2/A3训练及旧Atlas，主线新增950DT，这个支持标记没有把占位接口变为可用的算子包版本查询。

两固定TorchNPU的aclnn/backends.py均在调用时warnings.warn，随后返回None；只改了说明空白。None不表示未安装、版本0、最新版本或全部算子可用，也不能用来选择某个优化分支。

需要组件版本时另按[get_cann_version](get_cann_version.md)的组件名、CANN门槛和空字符串处理，不把两个入口当同一个探针。版本信息仍不替代符号、参数、产品及数值验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-aclnn-version.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-aclnn-version.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-aclnn-version.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/aclnn/backends.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/aclnn/backends.py)（implementation）
