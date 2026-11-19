---
type: API
title: vLLM 生成步状态原地更新（torch_npu.npu_advance_step_flashattn）
description: torch_npu.npu_advance_step_flashattn：vLLM 生成步状态原地更新。在NPU上执行vLLM库中advance_step_flashattn的功能，在每个生成步骤中原地更新`input_tokens`，`input_positions`，`seq_lens`和`slot_mapping`。 区分四个原地输出、主线一维投机缓冲区、关键字可选参数及 V2 依赖。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_advance_step_flashattn.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdvanceStepKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_advance_step_flashattn.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdvanceStepKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_advance_step_flashattn
---


# npu_advance_step_flashattn：生成步推进与投机缓冲区

## 版本与范围

本卡依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`；发布子模块 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的对应页另作版本约束。主线候选与ascend_26_0_pt28组合分别管理，不能只因接口同名推断可混用。 文档列A2/A3，限推理，无反向；未给出完整图模式契约，本卡不据void Schema推断捕获或GE支持。

## 实际接口与原地修改

主线Schema明确最后两项为关键字可选参数，修正文档原型省略星号和默认值的表达：

```text
torch_npu.npu_advance_step_flashattn(input_tokens, sampled_token_ids, input_positions, seq_lens, slot_mapping, block_tables, num_seqs, num_queries, block_size, *, spec_token=None, accepted_num=None) -> ()
```

无返回Tensor；input_tokens、input_positions、seq_lens、slot_mapping均带可写别名并原地更新。block_tables在文档参数行称输入/输出，但Schema与C++均为只读输入，不应等待它被此算子重建。

## 主线缓冲区与请求数

各张量用INT64，不支持空Tensor；num_seqs/num_queries/block_size为正整数。非投机场景四个原地缓冲区均为[num_seqs]，sampled_token_ids为[num_queries,1]，页面要求num_seqs>num_queries。

投机场景四个原地缓冲区均为一维[num_seqs*(1+spec_num)]；sampled_token_ids为[num_seqs,1+spec_num]，spec_token为[num_seqs,spec_num]，accepted_num记录每请求接受数量，num_queries=num_seqs。计算时才把input_tokens看成二维视图，不能直接沿用发布页中的二维缓冲区示例；发布页对其他几个缓冲区也有形状与综合约束不一致，旧栈需单独确认。

block_tables为[num_seqs,max_blocks]，第二维须大于最大seq_lens除以block_size的整数部分。槽位更新依赖推进后的位置、对应请求的逻辑块与物理块映射；页面简式不能代替完整分页寻址实现。

## V2分支与案例限制

C++实际在spec_token或accepted_num任一存在时直接调用aclnnAdvanceStepV2，两者均None才调用旧AdvanceStep。因此仅传accepted_num也会改变分支，不应按文档“仅看spec_token”来判定。包装没有提供缺V2的回退，需确认目标CANN交付件。

源码测试中的普通与投机用例均被skip，投机skip说明提到等待CANN 8.3.RC1；这是历史测试注释，不是本卡验证过的最低依赖证明。投机参考实现处理sampled_token_ids中的无效标记并按二维block_tables逐请求寻址，但测试参考不构成所有无效值协议或未使用缓冲区填充值的保证。


## 验证边界

按实际软件栈验证目标shape、dtype、mask语义和输出，再比较稳态性能。本次只做固定文档与实现的静态审阅，未执行上游代码或NPU数值/性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 完整版本与输入协议核对

发布中文的参数与示例把投机四个可写缓冲区写为二维，主线中英文统一为长度num_seqs*(1+spec_num)的一维，公式只借二维视图说明token排列。发布非投机参数段把positions/seq_lens/slot写为(num_queries,1)，同页综合约束与示例却按num_seqs；不能把不同段落拼成一种固定正确形状。上方按主线列示，旧包另外核对。

两版schema都将spec_token/accepted_num置于星号后、默认None，修正文档原型漏星号与默认值；两个C++都按“任一个Optional存在”选择AdvanceStepV2，没有符号探测后的降级。显式None与零元素Tensor不同：后者仍是存在的Optional，不能当作选择普通路径的手段。block_tables为只读输入，四个可写缓冲区才原地更新，产品是A2/A3训练系列硬件但用途明确仅推理、无反向，不能由硬件名称推定训练接口。

主线示例randint(10)会生成0，与参数段“大于0”文字不完全一致；accepted_num示例也未按spec_num=2收紧采样范围。页面未在这一段完整定义accepted_num合法值协议，不能将随机示例扩为任意接受数量都支持。分页地址简式没有完整表达逻辑页查表过程，不充作物理slot金标准。固定Meta文件和GE转换树的局部检索未找到本入口的手写注册，不据此断言所有图后端的运行能力；未执行任何样例。

## 已有 OpPlugin 7.3.0 文档与版本边界

### vLLM 生成步状态原地更新：torch_npu.npu_advance_step_flashattn

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

在NPU上执行vLLM库中advance_step_flashattn的功能，在每个生成步骤中原地更新`input_tokens`，`input_positions`，`seq_lens`和`slot_mapping`。

### 文档签名

```text
torch_npu.npu_advance_step_flashattn(input_tokens, sampled_token_ids, input_positions, seq_lens, slot_mapping, block_tables, num_seqs, num_queries, block_size) -> ()
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_advance_step_flashattn.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdvanceStepKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_advance_step_flashattn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_advance_step_flashattn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdvanceStepKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
