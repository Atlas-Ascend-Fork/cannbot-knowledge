---
type: API
title: npu_mhc_post：残差映射与必填None位置
description: 说明950残差连接、FP32投影dtype和h_res允许None但没有省略默认值的Schema。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_post.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_post.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_post.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_post.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPostBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_post_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:52:35Z'
updated_at: '2026-11-09T23:51:27Z'
platforms:
- '950'
---

# npu_mhc_post：残差映射与必填None位置

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口

```text
npu_mhc_post(x, h_res, h_out, h_post) -> Tensor
```

x为FP16/BF16 ND的(T,n,D)或(B,S,n,D)，h_out同dtype的(T,D)或(B,S,D)，h_post为FP32(T,n)或(B,S,n)。h_res若存在，是经Sinkhorn后的FP32(T,n,n)或(B,S,n,n)双随机矩阵。按h_res混合原残差，加上h_out按h_post扩展的结果，返回同x形状/dtype的下一层残差。

h_res=None时跳过残差映射，直接使用x加上post扩展。文档称h_res默认None，但同提交Schema是Tensor? h_res、没有省略默认值；它允许传None，不等于可省略第二个位置参数。应显式传None并保持参数顺序。

产品页仅950PR及DT推理、单算子与TorchAir图模式；输入支持非连续与空Tensor，但形状和类型仍需配套。生成式包装输出同x形状，未声明原地覆盖x。

- [生成pre/post/res投影](npu_mhc_pre.md)
- [把未归一化res变成残差映射](npu_mhc_sinkhorn.md)


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 发布原型与主线可选残差

发布schema的h_res是必填Tensor；主线才改为Tensor?，两版都没有可省略的None默认。主线公开仅950PR及DT，不将新None行为回推到发布包装。两固定Meta和生成包装只分配同x形状的输出，未据此核实双随机性、全部形状或空输入的模型语义。

公开示例用随机h_res，未先执行Sinkhorn；它只展示调用形状，不能作为整个mHC残差链的数值配方。静态前向及反向参考实际采用sum_i H_res[i,j]*x[i,d]的存储方向，与公开简写H_res×x的轴约定需对照模型核对，不能直接照抄一个未经核对的matmul或自行转置。

## 主线独立反向与空输入边界

npu_mhc_post_backward(grad_y,x,h_res,h_out,h_post)返回四份梯度。包装要求CANN≥9.0和对应反向符号，grad_y/x/h_out为相同FP16/BF16，h_post及存在的h_res为FP32，grad_y形状必须完整等于x。前向公开支持空Tensor，反向包装却明确拒绝空输入，不能把前向空输入能力传递到训练。

h_res=None时反向仍分配完整(...,n,n)的FP32 grad_h_res，而不是None；测试只检查这个槽的shape/dtype，未证明其数值有有效梯度语义。其他三份梯度按各输入形状和类型分配。主线固定Meta文件没有找到本反向接口的手写注册，这不等同所有捕获后端均不支持，但不能据前向Meta存在宣称完整图反向已适配。

反向测试中两个名为TND的数值用例把grad_y构造成(T,D)，而x为(T,n,D)，与包装同shape检查冲突；不能把测试名计为有效TND覆盖。BSND数值比较、None残差的形状检查和参数反例分别保留，没有运行或新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_post.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_post.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_post.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_post.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPostBackwardNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_post_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
