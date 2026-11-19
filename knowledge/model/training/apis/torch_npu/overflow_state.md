---
type: API
title: NPU溢出查询API：Inf/NaN输入检查与硬件状态
description: 保存两模式不同语义、隐式Host同步与清除行为，保留950文档冲突和FORCE版本门槛。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-clear_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-is_support_inf_nan.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-npu_check_overflow.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: '2026-11-09T19:31:30Z'
platforms:
- a2
- a3
---

# NPU溢出查询API：Inf/NaN输入检查与硬件状态

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 两种检测语义

is_support_inf_nan()->bool仅查询当前计算模式，True为Inf/NaN、False为饱和，不是“所有算子支持非有限输入”的能力列表。npu_check_overflow(grad)在普通Inf/NaN模式检查传入Tensor或float；两固定utils对Tensor转FP32求和再转Python float，会产生Host读取/同步，检查聚合量是否Inf/NaN，也可能受求和自身溢出影响，不能当完全逐元素检测。

饱和/强制状态查询分支忽略grad，查硬件get_npu_overflow_flag；若True，npu_check_overflow还清标志。因此它不是无副作用的重复读取器。直接get通过8元素状态Tensor回CPU取首项；clear重置硬件标志。普通Inf/NaN模式发布get抛不支持、clear警告返回，不改变数值计算模式。

## 主线FORCE和产品冲突

独立PyTorch主线增加is_force_overflow_check：仅FORCE_OVERFLOW_CHECK严格1且CANN>=9.1才使Inf/NaN模式走硬件状态路线；发布没有该条件，不回推CANN9.0。A2/A3此条件来自环境专页，不能从旧API页缺产品推为永不可能查询。

OpPlugin get_flag两版本独立页仍只列旧Atlas训练；clear发布相同，主线另列950DT/310p却不列A2/A3；is_support_inf_nan/npu_check_overflow主线又列950DT。与此同时固定PyTorch环境页明确950不支持状态查询。故本API整体metadata限定A2/A3的有条件路径，**不提供950硬件状态查询配方**；不把产品标记、普通输入检查和强制硬件检测合并。

模式切换和检测的环境门槛见[Inf/NaN指南](../../guides/torch_npu_inf_nan_and_overflow_detection.md)。保留窗口、首次异常及清标志时机，未运行异常输入、状态查询或设备实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-clear_npu_overflow_flag.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_npu_overflow_flag.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-is_support_inf_nan.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-npu_check_overflow.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）
