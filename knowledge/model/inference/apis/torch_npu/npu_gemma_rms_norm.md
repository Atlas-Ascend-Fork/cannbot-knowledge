---
type: API
title: npu_gemma_rms_norm：偏移权重与Rstd输出边界
description: 区分Gemma参考的gamma+1、FP32 rstd与Meta尺寸校验缺口，说明被跳过数值测试及设备Meta比较的边界。
tags:
- task.lookup
- topic.compute.normalization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GemmaRmsNormKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gemma_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GemmaRmsNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_gemma_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:58:30Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_gemma_rms_norm：偏移权重与Rstd输出边界

## 固定入口与参考语义

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的完整小型Host包装和测试，以及有界Meta、尺寸helper和Schema。两CPP逐字节同一；两测试整个AST相同，原始差异只有空白行。没有运行NumPy参考、算子、Meta、NPU或性能测试；平台未认证，保持draft与空平台。

```text
torch_npu.npu_gemma_rms_norm(self, gamma, epsilon=1e-6) -> (y, rstd)
```

两版Schema为op_api all_version，这不证明任意PyTorch/CANN/驱动搭配或全部产品都可用。仓内参考将输入及gamma先转FP32，按最后一轴计算：

```text
variance = mean(x_fp32 ** 2, axis=-1, keepdims=True)
rstd = 1 / sqrt(variance + 1e-6)
y = cast_to_input_dtype(x_fp32 * rstd * (gamma_fp32 + 1))
```

这里的权重是参考中的gamma+1，不能直接将普通RMSNorm的乘法权重视为同一表示。Host没有先计算gamma+1，而是将原gamma直接交 `aclnnGemmaRmsNorm`；不要在接入同一Gemma入口时仅凭算子名自行重复偏移。这个公式来自拟测参考，不是本次Kernel数值实测，也没有由该最后一轴用例认证任意多维gamma的归一化语义。

## 输出分配与本地尺寸校验

C++调用 `rms_norm_npu_output_size(self,gamma)`，只显式要求self.rank≥gamma.rank；y.shape=self.shape，rstd保留前self.rank−gamma.rank个尺寸，其余轴置1。例如已读测试的self=(256,512)、gamma=(512,)得到rstd=(256,1)。helper没有比较每个gamma尺寸与self尾轴，也没有在这里完整验证epsilon、dtype、设备、连续性或归一化轴数据。

y按self.options分配，rstd按self设备选项并固定FP32分配，两者均请求ND格式，命令依次传self、gamma、epsilon、y、rstd，返回(y,rstd)。包装本身没有普通RMSNorm入口那样的DO_COMPATIBILITY旧ACL回退表达式，也没有运行失败后重试其他实现。真实符号可用性、工作区、底层格式及产品规格仍需独立证据，不能从分配成功或同shape推出支持。

## Meta省略了Eager尺寸前提

两版完整Meta函数以self.rank−gamma.rank构造同样的rstd尺寸列表，但没有C++尺寸helper中的rank前提检查，也不核对gamma尾轴尺寸。它构造FP32、device='meta'的rstd，再返回empty_like(self)及empty_like(rstd)，不调用ACLNN。非法rank或不匹配gamma时，Meta描述与真实执行可能有不同失败位置，不能把Meta通过当作Eager输入认证。

## 完整小测试的覆盖范围

两份测试使用相同self=(256,512)、gamma=(512,)、均匀正数0..100、默认epsilon1e-6，覆盖FP32和FP16两个dtype。直接比较NumPy数值参考的两个测试方法都被unittest.skip标记为暂时跳过，因此不能计作已执行精度证据。

另外两个未被skip标记的Meta方法也受Ascend910B装饰器筛选，先创建NPU输入并调用真实算子，再创建Meta输入比较两个输出的shape/dtype；它们不是完全不需要设备的纯Meta测试，也没有比较数值。装饰器只说明拟测筛选，不在本卡增加已验证平台或verified。

没有由这些测试覆盖BF16、负值或更广分布、其他epsilon、多维gamma、空Tensor、错误shape/设备、梯度、图捕获、融合收益及其他产品。接入Gemma模型时，应分别核对权重偏移、真实rstd形状/类型、精度与下游保存需求，再测实际运行成本；本卡没有上述运行结论。

## Evidence

- [GemmaRmsNormKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GemmaRmsNormKernelOpApi.cpp)（primary）：1–35；完整本地小文件。
- [test_npu_gemma_rms_norm.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_gemma_rms_norm.py)（example）：1–97；完整本地小文件。
- [_meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：2909–2919；仅所列完整函数或Schema。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1929–1947；仅所列完整函数或Schema。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：6835–6837；仅所列完整函数或Schema。
- [GemmaRmsNormKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GemmaRmsNormKernelOpApi.cpp)（implementation）：1–35；完整本地小文件。
- [test_npu_gemma_rms_norm.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_gemma_rms_norm.py)（example）：1–97；完整本地小文件。
- [_meta_registrations.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：2558–2568；仅所列完整函数或Schema。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1737–1757；仅所列完整函数或Schema。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：6635–6637；仅所列完整函数或Schema。
