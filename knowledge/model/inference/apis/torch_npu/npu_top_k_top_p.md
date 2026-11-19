---
type: API
title: 采样候选过滤（torch_npu.npu_top_k_top_p）
description: torch_npu.npu_top_k_top_p：对 logits 进行 top-k 与 top-p 候选过滤。 说明Top-K后Top-P的顺序、被过滤值与同shape输出，区分抽样接口及可选参数Schema。
tags:
- task.lookup
- topic.compute.random_sampling
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_top_k_top_p.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_top_k_top_p.py
  role: example
created_at: '2026-11-10T03:38:50Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_top_k_top_p
- top-k top-p
---


# npu_top_k_top_p：过滤logits而不抽样

## 固定版本与证据边界

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页及同提交接口/包装代码，不回推发布基线。本文是静态审阅，未运行上游实现、图编译或设备性能实验。

## 接口与计算

```text
npu_top_k_top_p(logits, p=None, k=None) -> Tensor
```

Schema允许p、k省略，但产品参数页主要描述显式提供二者的过滤路径，本卡不从None签名推定所有缺省组合的设备行为。logits为二维(B,V)、FP16/BF16/FP32，p为(B,)且同dtype，k为INT32(B,)，有效k为1..min(V,1024)。

先按logit稳定排序，通过Top-K阈值屏蔽较小值，再对保留部分Softmax，按升序概率的累积和与1-p比较执行Top-P，至少保留一个token。结果为原词表顺序、同shape/dtype的过滤logits，屏蔽处为-inf；不是归一化概率，也不是采样到的token ID。阈值比较不能直接等同于所有并列值场景恰好保留k项。

生成式包装分配与logits相同的输出并调用aclnnApplyTopKTopP；Meta只返回同shape空占位，不证明阈值正确性。文档提到V>1024时平均性能优于组合实现，仍须按目标batch/词表与真实数据分布比较。

- [带随机后处理的不同接口](npu_top_k_top_p_sample.md)


## 验证

检查目标产品、执行模式、数据类型、输出形状与实际运行库入口；使用可追踪的小输入对照参考计算，覆盖边界和空值策略。Meta推导成功不等于设备支持，也不代表取得性能收益。

## 过滤规则的参考实现与产品范围

两版静态CPU参考先升序稳定排序，用严格小于第k大阈值的条件过滤，因此并列阈值可以保留多于k项；再以FP32 Softmax计算升序累积概率，用小于等于1-p的条件过滤，同时保留最高项。最后通过scatter写回原词表索引。公开公式中用sorted_values[sorted_indices]恢复顺序的写法不能直接抄作逆排列，参考实际是散射。

参考分别包含p=None时仅Top-K和k=None时仅Top-P的分支，但两版三个设备测试入口都被skip标记CI尚不支持，拟测也仅A2/FP32；不把这些分支或两个参数都省略推定为全部产品的有效设备用法。生成包装分配同shape输出，Meta仅empty_like，不会补充这些数值证据。

发布公开A2/A3，主线增加950DT，未列950PR。输入支持非连续；公开V>1024时的平均性能建议没有由这些跳过的用例重新测量。该API始终是logits过滤阶段，不负责随机数、归一化概率或token选择。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 采样候选过滤：torch_npu.npu_top_k_top_p

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对 logits 进行 top-k 与 top-p 候选过滤。

### 文档签名

```text
torch_npu.npu_top_k_top_p(logits, p, k) -> torch.Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_top_k_top_p.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_top_k_top_p.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_top_k_top_p.py)（example）
