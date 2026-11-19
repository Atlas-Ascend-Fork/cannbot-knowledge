---
type: API
title: npu_mhc_pre：六输出、残差投影与HF32门槛
description: 说明950 mHC前处理、H_post维度、未做Sinkhorn的H_res及CANN/V2精度模式要求。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_pre.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPreNpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_pre.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MhcPreNpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_pre.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_pre.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPreBackwardNpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_pre_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-09T06:52:35Z'
updated_at: '2026-11-09T23:51:27Z'
platforms:
- '950'
---

# npu_mhc_pre：六输出、残差投影与HF32门槛

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口与输入

```text
npu_mhc_pre(x, phi, alpha, bias, *, gamma=None,
    norm_eps=1e-6, hc_eps=1e-6, out_flag=0, inner_precise=0)
    -> (h_in, h_post, h_res, inv_rms, h_mix, h_pre)
```

x为FP16/BF16的(T,n,D)或(B,S,n,D)，n∈{4,6,8}，D≤16384且16对齐；x/phi/alpha/bias非空。phi/bias/alpha及可选gamma为FP32，gamma=(n,D)。残差投影模式alpha有3项、phi=(n²+2n,nD)、bias=(n²+2n,)；仅pre/post模式alpha有2项、phi=(2n,nD)、bias=(2n,)。参数排列为pre、post、res，不能随意交换。

先归一化并做投影，pre经sigmoid加hc_eps、post经2*sigmoid，由pre加权残差得到h_in。h_res是尚未做Sinkhorn的投影，需经过[npu_mhc_sinkhorn](npu_mhc_sinkhorn.md)后才作为残差双随机映射交给[npu_mhc_post](npu_mhc_post.md)。它不同于一次融合了Sinkhorn的Recipes HcPre实现。

## 输出形状与有效槽

h_in=(T,D)或(B,S,D)，dtype同x；h_post依据C++/Meta为(T,n)或(B,S,n)、FP32，**不是产品页返回段误写的尾维D**。完整h_res为(T,n,n)或(B,S,n,n)、FP32；alpha两项时C++只分配FP32[1]占位，不把该槽当成有效零残差矩阵。

out_flag仅0/1，后三个输出必须一起启用：inv_rms=(T,)或(B,S)，h_mix尾维为phi.size(0)，h_pre尾维n，均FP32。C++在0时不分配这三项，Meta却仍构造完整shape；调用者不应因Meta有shape而消费无效缓存。

## 运行库与精度

950PR及DT推理，单算子和TorchAir图模式。包装明确要求CANN≥9.0，inner_precise=0用Cube FP32，可回退V1；inner_precise=1用HF32且额外要求aclnnMhcPreV2。有V2时优先V2，不将CANN最低版本与V2符号存在等同。

来源列默认确定性但不默认batch一致，后者需单独配置与核验；确定性不是batch形状变化后数值完全相同的承诺。


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 发布实现与主线精度、缓存分支

公开产品范围仅主线950PR及DT，主线软件配套尚未确认。发布快照虽已有包装及测试，没有本次主线公开页的产品契约，不据代码存在宣称发布基线支持全部主线功能。

发布包装只接受alpha三项，没有inner_precise参数，CANN≥9.0且aclnnMhcPre存在才调用V1。发布在out_flag=0时仍为后三项分配完整缓冲，但向底层传空Tensor，返回缓冲未参与写入。主线改为0时不分配后三项，仍返回六个槽；两版Meta却始终构造全部六份形状。它们都不能让关闭的缓存变成有效计算结果。

主线前向即使FP32也优先V2，只有没有V2且FP32时才回退V1；HF32不允许回退V1。CANN版本与符号检查均缓存，不能以版本号代替V2能力确认。inner_precise只改变Cube计算模式，不把权重或所有中间结果改成FP16。

主线中文参数段列alpha两项/三项与对应phi、bias；英文参数段仍只列三项，但约束段又列两项，两种模式分别按完整条件使用。alpha两项时主线C++/Meta的h_res为FP32(1,)占位，包装不显式清零；测试也跳过该槽，不能依据公开“输出为0”把它当作全零(n,n)残差矩阵。后处理要走无Res Mapping时应显式传None。

## 静态参考与batch一致性范围

两版参考都将每token的n*D维一起计算RMS；h_mix是原x按可选gamma加权后与phi的线性投影，inv_rms随后乘到投影上。h_in最终用原始x按h_pre求和，不能误用归一化后的x进行第二次残差加权。主线HF32参考对两矩阵输入做舍入模拟，不是设备测量。

主线batch一致性测试设置deterministic_level=3，比较[A]、[A,B]、[B,A]中相同样本的前三项，再恢复原设置。它只覆盖BF16、B=1、S=64、n=4、D=2560的一组案例，不能推广成所有shape、精度和可选缓存的逐bit一致性保证。其他标为training的前向测试只比较前向结果，公开页仍仅推理。

## 主线内部反向的缓存与合并梯度

主线新增npu_mhc_pre_backward，返回dx、dphi、dalpha、dbias、dgamma。输入包含三份输出梯度以及inv_rms、h_mix、h_pre、h_post；可选grad_x_post把后处理分支的dx累加进本次dx。该融合累加可避免应用另行表达一次加法，但本仓没有测量收益；普通自动求导声明传None，不自动连接此额外梯度。

反向FP32模式固定要求aclnnMhcPreBackward V1符号，HF32固定要求V2，均要求CANN≥9.0。这与前向FP32优先V2不同：只有前向符号可用不代表反向配套满足。

反向包装/Meta始终按完整残差模式分配dphi=(n²+2n,nD)、dalpha=(3,)、dbias=(n²+2n,)、dgamma=(n,D)，即使gamma缺省也分配gamma梯度槽；不能由前向alpha两项支持推断反向已经适配两项模式。dx沿用x类型，其余为FP32，所需缓存和三个输出梯度都要求非空。

自动求导只把前三个前向输出标为可微，保存后三份缓存，但没有自动把out_flag改成1。需要反向时缓存有效性是独立前提，不能用默认0的无效槽继续计算。主线反向测试使用CPU前向构建缓存后调用独立反向，主要为BF16、n=4、D=512、T=128，并非完整NPU前后向训练或所有alpha模式的证明。本次仅静态审阅，不扩充公开训练支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_pre.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPreNpuOpapi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_pre.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MhcPreNpuOpapi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_pre.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_pre.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcPreBackwardNpuOpapi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_pre_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
