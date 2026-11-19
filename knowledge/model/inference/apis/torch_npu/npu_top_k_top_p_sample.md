---
type: API
title: TopK TopP 过滤与指数采样（torch_npu.npu_top_k_top_p_sample）
description: torch_npu.npu_top_k_top_p_sample：按 logits、top-k/top-p 和随机权重进行候选筛选及采样，并返回所选索引和相关分布。 输出 `logits_select_idx` 为所选位置，`logits_top_kp_select` 为 top-k/top-p 处理后的分布。 说明采样参数及旧接口未传递的新增选项，记录q=None、generator和输出分配的文档实现差异。
tags:
- task.lookup
- topic.compute.random_sampling
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p_sample.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TopKTopPSampleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MultinomialKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_top_k_top_p_sample.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TopKTopPSampleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MultinomialKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_top_k_top_p_sample.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_top_k_top_p_sample
- topK-topP-Sample
---


# npu_top_k_top_p_sample：采样分支、随机源与V2边界

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口与支持范围

```text
npu_top_k_top_p_sample(logits, top_k, top_p, q=None,
    eps=1e-8, is_need_logits=False, top_k_guess=32,
    min_ps=None, ks_max=1024, input_is_logits=True,
    post_sample='qSample', generator=None) -> (idx, filtered)
```

产品页确认A2/A3推理、当前不支持图模式。logits为非空二维(B,V)、FP16/BF16/FP32，top_k为非空INT32(B,)，top_p为同logits dtype的(B,)。不要把约束段另写的(B,1)跳过示例当成兼容广播承诺。idx为INT64(B,)，filtered包装分配为FP32(B,V)。

## 过滤参数

有效top_k为1..min(V,ks_max)，无效值跳过Top-K而非强行夹紧。top_p参数专节明确≤0只留最大项、(0,1)执行Top-P、≥1跳过；约束段又将≤0写成跳过，存在差异，不能据后一句构造跳过Top-P配方。min_ps在(0,1)按峰值相对阈值过滤，≤0跳过、≥1只留最大项。各分支输入shape和dtype仍须按对应产品验证。

input_is_logits=True在概率步骤前Softmax并用-inf屏蔽；False要求已归一化输入，避免重复Softmax，屏蔽值0。top_k_guess仅为跳过Top-K后的Top-P优化线索，不改变应验收的过滤语义。

## 运行库入口与未传递参数

非multiNomial分支先探测aclnnTopKTopPSampleV2；旧入口不接收min_ps、ks_max、input_is_logits。不能在旧运行库上依据Python参数已被接受就认定这些选项生效。multiNomial分支直接调用V2，无相同的旧入口探测回退；本提交未给出可据以承诺的最低CANN版本号。

## 随机源与输出的来源差异

- 文档说q=None强制无随机后处理，但C++先按post_sample=='multiNomial'进入V2→multinomial→gather路径，没有先检查q是否为空。因此不承诺multiNomial下q=None等价argmax。
- multiNomial的实际multinomial调用使用显式generator或默认NPU generator的Philox seed/offset，每行取一个样本，包装传replacement=True。文档另述q的INT64种子矩阵及无放回算法，不能当作该包装已实现的随机序列控制保证。q仍传入V2，底层如何消费不由本文件独立证明。
- qSample文档要求FP32(B,V)指数采样权重；generator在当前包装只用于multiNomial，不把设置generator理解为控制所有采样模式。
- is_need_logits=False时C++仍预先分配filtered及两份(B,V)辅助Tensor；不保证零分配，也不把返回shape当成内容已计算的证明。只有需要该输出且核对对应运行分支后才消费其内容。

内部存在capture相关随机数代码不提升产品页“当前不支持图”的范围。用相同过滤基准和明确随机源验证统计与复现性，不能只比较单次随机ID；当前差异未由设备实验消解。

- [只过滤logits的接口](npu_top_k_top_p.md)


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。接口签名存在不等于设备支持，也不代表取得性能收益。

## 发布对照、模式字符串和随机状态

发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5的产品页同样只列A2/A3推理、不支持图；主线与发布的关键C++分支相同，不把内部capture代码推成公开图能力。Schema均标nondeterministic_seeded，未给跨设备、跨运行库或跨后处理的随机序列一致性保证。

实际C++只对字符串multiNomial单独分支；qSample与字符串None均落入同一个非multiNomial路径，并不把post_sample继续传给V2，也没有依据字符串None先清空q。因而文档“显式None忽略非空q”并未由该包装分支落实，不能用改字符串保证关闭随机性。Python可选None在包装中还会补回默认qSample，与字符串None须区分。

multiNomial每行抽1项，包装固定replacement=True，再以中间原索引Gather；这与文档称“无放回”不同，单次只取一个样本也不能反推多次抽样契约。显式generator或默认NPU generator分别提供Philox seed/offset；普通非capture分支调用philox_engine_inputs(10)，不是每行读取q种子即可保证可复现。q仍透传V2，本文没有独立确认其底层全部用途。

若aclnnMultinomial不可用，单独的multinomial包装有到acl_op::multinomial的兼容分支；两版该实现均使用同类NPU generator状态和MultinomialWithReplacement命令。这个回退发生在V2过滤之后，不能据此宣称缺TopKTopPSampleV2时multiNomial整体可回退旧TopK入口。

## 阈值、形状和默认文字的冲突

主线中英文及发布页的Top-P公式段提到input_is_logits默认False，函数原型、Schema和C++却均默认True。调用应明确选择原始logits或已归一化输入，不能由所有值恰好在[0,1]判断已经满足概率契约。可选filtered保留通过mask的原始输入值，并非保证重新归一化的概率分布。

ks_max文档要求正数、上限1024并向8对齐，超过1024封顶；top_k_guess非正时走完整排序/cumsum路径，不是跳过Top-P。C++薄层没有实现这些值域修正，不能单凭签名接受任意整数推断底层结果。top_k无效值跳过Top-K，Top-P≤0仍只留一项，与“≤0跳过”的另段文字不同。

multiNomial专节的q是INT64[q_row,2]，不足batch时复用末行；qSample才是FP32[B,V]。文档通用约束又要求q与logits同shape，不能把这条概括覆盖两个不同模式的特定矩阵。top_k/top_p的一维要求与另段[B,1]示例也不一致，本文不扩展广播输入。关闭filtered时两版包装依旧分配完整[B,V]输出及辅助矩阵，不消费其未计算内容。

## 固定测试的实际覆盖

主线440行测试与发布只有155行完整空白/EOF差异；唯一major测试被unittest.skip无条件跳过，仅标A2。参数矩阵列出多种模式、dtype和开关是测试意图，不能计为已通过的覆盖。

参考大部分过滤用CPU Tensor，但multiNomial仍调用NPU上的torch.multinomial，并用两份分别设种子的NPU generator做对照，不能称独立CPU采样参考或分布统计验收。参考给False可选输出返回0元素，包装却分配完整矩阵，而测试只在True时比较该输出，没有验证关闭时的内容协议。

qSample参考用Uniform[0,1]权重，不能据此证明指数噪声采样分布；Python random选batch也没有随NumPy/torch种子一起固定。未运行测试，未建立A3、V2缺失回退、非连续输入、不同ks_max/top_k_guess、q种子矩阵或确定性的设备证明。

## 已有 OpPlugin 7.3.0 文档与版本边界

### TopK TopP 过滤与指数采样：torch_npu.npu_top_k_top_p_sample

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

按 logits、top-k/top-p 和随机权重进行候选筛选及采样，并返回所选索引和相关分布。

### 输入、输出与行为

输出 `logits_select_idx` 为所选位置，`logits_top_kp_select` 为 top-k/top-p 处理后的分布。topK、topP、指数采样可分别使能；仅走 Softmax-Argmax 路径时按最大值选择，不能把含随机权重 q 的所有采样路径都等同于 argmax。

### 文档签名

```text
torch_npu.npu_top_k_top_p_sample(logits, top_k, top_p, q=None, eps=1e-8, is_need_logits=False, top_k_guess=32) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p_sample.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TopKTopPSampleKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p_sample.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MultinomialKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_top_k_top_p_sample.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TopKTopPSampleKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MultinomialKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_top_k_top_p_sample.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）
