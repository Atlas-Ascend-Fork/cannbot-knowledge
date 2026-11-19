---
type: API
title: npu_sim_exponential_：原地指数分布与跨版本RNG偏移
description: 保留连续ND输入、lambda边界和主线计数算法，不承诺跨版本随机序列相同。
tags:
- task.lookup
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SimExponentialNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SimExponentialNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/RandomUtil.h
  role: implementation
created_at: '2026-11-09T20:57:33Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_sim_exponential_：原地指数分布与跨版本RNG偏移

## 固定版本与复核边界

文档为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda各自收录页；发布对应ascend_26_0_pt28。实现分别为TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b和独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把独立main当已配套发行。

产品逐接口/版本限定；950条目如仅DT便不扩PR，旧Atlas不自动映射新型号。静态阅读不表示已调用设备、图捕获、回调、文件解析或性能验证；stable不表示运行verified。本卡没有执行上游或加载任何模型、检查点和dump数据。


## 声明与输入

npu_sim_exponential_(input,lambd=1,*,generator=None)->Tensor原地填充指数分布，返回同一输入。文档连续ND、rank0..8、BF16/FP16/FP32，lambda为正double，generator指定NPU随机发生器、未给用默认。注册范围PyTorch>=2.6且标nondeterministic_seeded，不由存在性扩展到更早版本。

公式为-ln(1-u)/lambda，页面u∈(0,1]含u=1的数学奇点，不能据这一写法断言真实Kernel一定产生或排除Inf。两固定包装先检查lambda>0，0、负数及NaN拒绝；+Inf则直接zero_并返回，未消费后续RNG。文档“正实数”与实现额外边界分开，空Tensor也不等同任意版本完全相同的RNG消耗。

## RNG状态版本差异

发布固定从所选NPU生成器申请Philox偏移4；main改用RandomUtil.calc_final_counter_offset(self,false)，false表示不切换CANN随机模式，非ACLNN-only取旧偏移10，ACLNN-only按shape、stride、dtype和索引分块计算，空输入可为0。大索引还涉及拆分计数，不简写为固定每元素偏移。

显式相同manual_seed也不能据此承诺发布/main或不同SoC路径逐位相同、对后续算子RNG影响相同。main文档新增950PR/DT，发布仅A2/A3；该产品扩展及RNG差异分别消费，不能回推发布环境。未执行随机采样、统计分布或性能实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sim_exponential_.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SimExponentialNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SimExponentialNpuOpApi.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/RandomUtil.h)（implementation）
