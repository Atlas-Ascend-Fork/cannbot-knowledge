---
type: API
title: NPU布局开关：私有格式与Linear中MM/BMM的ND策略
description: 保留仅后续Tensor、Conv/JIT分支、950DT例外和ND初值注释冲突。
tags:
- task.lookup
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-config-allow_internal_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-config-allow_internal_format.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-config-allow_internal_format.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_mm_bmm_format_nd.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_mm_bmm_format_nd.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_mm_bmm_format_nd.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_mm_bmm_format_nd.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_mm_bmm_format_nd.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_mm_bmm_format_nd.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NPU布局开关：私有格式与Linear中MM/BMM的ND策略

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 配置、范围与初值

`torch_npu.npu.config.allow_internal_format`为属性：A2/A3默认False，旧Atlas训练/推理默认True；主线950DT仅可设False。页面限定影响之后新创建的Tensor，不是对已存在模型存储的批量格式转换。

`set_mm_bmm_format_nd(is_nd=True)`和`get_mm_bmm_format_nd()->bool`只描述Linear中的MM/BMM选择；不能据标志推导所有Tensor或所有matmul均为ND。两固定npu_config.py中的注释写Default False，但实际`_MM_BMM_ND_ENABLE=True`，setter默认True；如依赖缺省应核对实际安装，而不是照抄注释。它是Python全局配置，未在这段实现提供线程隔离。

## 格式转换与卷积的例外

主线通用配置页称False时format_cast、format_cast_和C++ npu_format_cast会降级base格式，data/shape不变，True才真实转换私有格式；但同一OpPlugin提交的[C++特定接口](cpp_npu_format_cast.md)明确950DT私有转换不受False限制。保留特定接口的950限制与通用页的冲突，不用通用说法删除C++特例，也不据此扩展customize_dtype参数。

Conv1d/2d在allow_internal_format=False且JIT关闭时走ACLNN，其他组合走aclop；Conv3d不受这条开关影响。这是来源条件，不证明两路线的数值、性能与产品能力相同。布局、算子输入格式、dtype和真实消费者分别核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-config-allow_internal_format.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-config-allow_internal_format.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-config-allow_internal_format.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_mm_bmm_format_nd.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_mm_bmm_format_nd.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_mm_bmm_format_nd.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_mm_bmm_format_nd.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_mm_bmm_format_nd.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_mm_bmm_format_nd.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）
