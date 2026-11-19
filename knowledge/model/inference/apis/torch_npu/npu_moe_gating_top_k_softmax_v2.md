---
type: API
title: npu_moe_gating_top_k_softmax_v2：归一化与Meta/图输出边界
description: 区分renorm、FP32可选Softmax与旧row_idx，记录固定版本Meta和GE签名冲突，作为待核验迁移依据。
tags:
- task.lookup
- topic.mixture_of_experts
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKSoftmaxV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_gating_top_k_softmax_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKSoftmaxV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_gating_top_k_softmax_v2.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k_softmax_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_apis.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k_softmax_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_apis.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T23:08:09Z'
updated_at: '2026-11-09T23:08:09Z'
platforms:
- '950'
---

# npu_moe_gating_top_k_softmax_v2：归一化与Meta/图输出边界

## 固定证据与待核验状态

主线旧接口产品页建议950PR及DT迁移到本接口；两个固定OpPlugin提交已有schema、包装及参考，两个TorchAir也有转换器。本卡以这条950迁移建议限定平台，保留draft：缺少独立完整产品契约，且发现Meta与GE转换冲突。A2测试装饰器不代替950或其他产品验证，主线软件配套尚未确认。

## 实际接口与第三返回

    torch_npu.npu_moe_gating_top_k_softmax_v2(x, *, k=1,
        finished=None, renorm=0, output_softmax=False)
        -> (y, expert_idx, softmax_result)

两版C++要求x二维/三维、FP16/BF16/FP32，finished若提供为BOOL且shape等于x的前缀。y与x同dtype，shape为x前缀加k；expert_idx同shape、INT32。第三项是FP32 softmax结果，不是旧接口的INT32 row_idx，不能原样送给依赖旧row_idx的初始化路由。

两固定CPU参考中，renorm=0先在全部专家上算FP32 Softmax再选TopK；renorm=1先选TopK logits再在选中项内算Softmax，最后权重转回x类型。这是静态参考算法说明，未执行或证明所有内核等价。C++只允许renorm为0或1，显式None按0；finished行参考用专家数E作无效ID，本卡不把参考填充值扩成所有版本已验证的协议。

只有renorm=0且output_softmax=True才分配与x同shape的FP32第三输出，其他情况是真实shape(0,)的FP32 Tensor。renorm=1时即使请求第三输出，也不能获得完整Softmax。host允许k=0并提前返回；此时完整Softmax缓冲若已分配，并未因分配而获得有效数值。host校验0≤k≤E没有给出全部底层上限，不从这里推定任意大k合法。

## 两版Meta的形状与None冲突

两个固定Meta均写if x.dim == 3，把方法对象和整数比较，没有调用x.dim()。因此三维输入请求完整Softmax时，它们给第三项二维(x.size(0),x.size(1))，与C++的三维输入shape不同。Meta对renorm=None也不做C++的None→0归一化，此时output_softmax=True会走空输出分支。Meta通过不是Eager/图形状一致的证明。

## GE转换中的接口不匹配

两个固定Converter都把renorm/output_softmax传给GE MoeGatingTopKSoftmax。固定自动生成IR中这个旧函数只接收k，第三输出是row_idx；另有独立MoeGatingTopKSoftmaxV2才接收新属性、返回FP32 softmax_result。ge_apis导出及Converter导入也指向这组固定函数，存在静态签名和输出协议不匹配，不能将Converter文件存在视为图路径可用证明。这里没有执行上游导入、编译或重现运行异常。

核验时需同时确认运行库、renorm顺序、返回解包、三维Meta和正确GE入口；来源的950性能建议不构成已经测得的加速或稳定可用配方。与[旧三返回接口](npu_moe_gating_top_k_softmax.md)分别管理。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKSoftmaxV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_gating_top_k_softmax_v2.py)（example）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKSoftmaxV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_gating_top_k_softmax_v2.py)（example）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k_softmax_v2.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_apis.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k_softmax_v2.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_apis.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
