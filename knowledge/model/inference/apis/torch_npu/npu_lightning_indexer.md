---
type: API
title: 稀疏 token 索引（torch_npu.npu_lightning_indexer）
description: torch_npu.npu_lightning_indexer：为每个 Query 选择关键 KV 位置的 TopK 索引，供后续稀疏注意力消费。 说明浮点 DSA Indexer 的 D=128、Q/K 头数、分页/累计长度以及无效第二返回值。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_lightning_indexer.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LightningIndexerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LightningIndexerGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_lightning_indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_lightning_indexer_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LightningIndexerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LightningIndexerGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_lightning_indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_lightning_indexer_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/lightning_indexer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/lightning_indexer.py
  role: implementation
created_at: '2026-11-10T03:38:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_lightning_indexer
---


# npu_lightning_indexer：稀疏索引的布局、长度与头维

## 版本与范围

前面的基本推理路径依据ascend_26_0_pt28发布来源；后文完整补充固定主线950DT、评分返回、普通反向与图转换差异。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_lightning_indexer(query, key, weights, *, actual_seq_lengths_query=None, actual_seq_lengths_key=None, block_table=None, layout_query="BSND", layout_key="BSND", sparse_count=2048, sparse_mode=3, pre_tokens=9223372036854775807, next_tokens=9223372036854775807, return_value=False) -> (Tensor, Tensor)
```

基于 Index Query/Key、ReLU、weights 和 TopK 选择稀疏位置，返回 (sparse_indices,sparse_values)。indices 为 INT32，BSND 时 (B,Sq,Nk,sparse_count)，TND 时 (Tq,Nk,sparse_count)。推理保留 return_value=False，第二项不作为有效评分消费。

## 参数与组合限制

- 连续 ND 的 query/key 同为 FP16 或 BF16，D 均固定为 128；Q 头数≤64，K 头数只支持 1。weights 为 FP32 或与 Q/K 同 dtype，shape=(B,Sq,Nq) 或 (Tq,Nq)。
- Q 布局支持 BSND/TND，K 支持 BSND/TND/PA_BSND。非分页时布局相同；分页 K=(blocks,block_size,1,128)，block_size 为 16 倍数且≤1024。
- TND 长度为必传 INT32(B,) 累计边界，非负单调不减；普通 BSND 使用各 batch 独立长度。PA_BSND 必须提供实际 K 长度和二维 INT32 block_table=(B,至少最大页数)。
- sparse_count 支持 [1,2048] 及 3072/4096/5120/6144/7168/8192；sparse_mode 只支持 0/3，pre_tokens/next_tokens 仅保留最大 INT64。Python 数值写 (1<<63)-1，不能照搬文档数学记法 2^63-1 为异或表达式。
- return_value=True须按版本核对训练、非分页和图模式条件；本卡的基本推理范例不启用，主线950DT及普通评分反向见后文。

## 验证与模型关联

用显式相关性、ReLU、加权和 TopK 检查索引，并与下游 SFA 的稀疏索引形状配套；分别验证 TND 与分页长度，不能将位置索引当专家路由 ID。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py#L550)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950与评分返回范围

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页列A2/A3推理系列与950DT。950的Nq只8/16/24/32/64、weights不支持FP32，仅PA_BSND的key允许0轴非连续；A2/A3仍按原≤64头与连续key范围。D=128、K头=1及稀疏数量限制保持。

主线写return_value图模式仅950DT支持，同时保留“评分输出仅训练且非PA_BSND”的参数限制；不能把这一图扩展直接变成推理可启用评分的保证。本卡推理仍用False，C++/Meta确认第二槽是与query同dtype的[0]空Tensor。默认前向确定性与普通反向非确定性分别表述，不把它们移植到独立融合KL接口。

## 固定版本、图模式与评分返回

本节完整核对OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda和发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布组合为ascend_26_0_pt28，主线配套未知；主线950仍仅DT，不推导PR。

两版Eager前向/普通反向C++逐字节相同，主线新范围主要体现在文档与Meta/图转换，不把它描述成所有底层路径都已发生相同修复。发布Meta无条件拒绝return_value=True进入PyTorch compile；主线移除了这一拒绝，公开文档只把评分图支持扩到950DT，并保留评分仅训练、非PA_BSND条件。英文参数行还写评分不支持graph capture，而中文该行已去掉这句；TorchAir编译图与设备捕获是否都支持须分别核对，不能混为一个“图模式已验证”。

两版TorchAir均用custom_op创建LightningIndexer，透传三输入、两长度Tensor、block_table和所有attrs，输出两槽；GE属性名为return_values。主线Python形参是公开的return_value，发布却为return_values，与OpPlugin Schema不同，显式关键词的实际绑定需核对，不凭同名算子判断跨版本兼容。转换器本身不按产品、分页或训练分支校验新组合。

## token位置、分页与长度的区别

公式先对每Indexer头的QK结果做ReLU，再乘该query/head的weights，跨头相加后按有效key token取TopK。输出是token位置，虽然参数文字称block数量，它不是PagedAttention的物理页号，也不是block mask或MoE专家ID。分页key必须经block_table把逻辑token定位到真实KV块，再按每batch有效K长度裁剪；不能用cache物理顺序代替逻辑序列顺序。

普通BSND长度表示各batch独立长度；TND的INT32 Tensor表示累计边界，元素数决定B，边界非负且不减；PA_BSND的K长度仍是每batch有效token数。这个推理Indexer的Tensor参数与稠密/稀疏KL训练接口的SymInt累计列表不同，不能只按相似名字共用同一个对象。

模式3是右下角对齐因果可见性，Q/K不等长时应按Sk-Sq对齐；模式0不额外套同样的因果截断。pre/next只支持最大INT64默认值，不能看到参数就构造任意滑窗。代码只检查sparse_count>0及query/key非空和各shape轴>0，不完整验证产品支持的TopK离散集合、头数、D128、长度、block table、连续性或dtype，调用者仍按文档合同选择。

## 普通评分梯度与融合KL的区别

两版derivatives仅第二个评分返回值可微，INT32索引不可微；它保存同次indices，并将评分的上游grad传给npu_lightning_indexer_grad，返回Qindex、Kindex、weights三梯度。若return_value=False，第二槽是[0]空Tensor，不能只消费indices就期待普通评分反向自动学习。独立稀疏KL入口会计算自己的损失和梯度，不等于这个评分VJP。

普通grad入口接query、key、dy、sparse_indices、weights及两长度Tensor，只有一个layout，没有block_table或单独layout_key；不能将PagedAttention推理路径直接接成通用分页训练反向。C++直接分配三份同形同dtype梯度，head_num传0，sparse_mode显式None时回退0，而公开Schema省略时默认3；显式None与省略不完全相同。

普通grad把全局deterministicAlgorithms标志传给ACLNN，但文档明确反向默认非确定且不支持开启确定性；这一透传不构成确定性保证或可用性测量。它与稀疏融合KL固定传true的调用事实分别记录。前向默认确定性也不能用来保证TopK分数相等时某个任意排序规则。

Meta前向仅验证必选Tensor存在、Q/K非空和sparse_count正数，再按布局分配索引/评分；反向仅创建三梯度。主线Meta删除compile拒绝并不增加对950头数、weights禁FP32、分页首轴非连续等产品条件的完整验证。

## 全部被跳过测试的覆盖限度

两版前向测试各158行、字节相同，BSND和TND两个Eager方法均无条件skip；都只测BF16、PA_BSND key、block256、Nq64/Nk1/D128、K2048。TND样例Q累计边界[1,3,5]、分页K独立长度[8192,8192,8192]，可说明二者的表示差异，但未运行。文档图样例也只是打印indices，没有测试return_value=True或自动反向。

CPU前向参考按block_table收集页并裁剪，再ReLU/加权/跨头求和、右对齐mask并降序排序；不足输出槽预填-1。它按min(sparse_count,Sk)拷贝候选，没有逐行过滤因果mask后的-inf候选，因此不能据此保证TopK大于实际可见token时的填充、全屏蔽行或并列分数语义。

普通grad测试两版各209行，仅8行文件末尾差异；唯一方法也skip，三份梯度比较断言全部被注释。参考计算还调用NPU，不是独立纯CPU标杆；其前向用左上角triu(1)因果mask，而传给算子的模式3为右下角、Sq20/Sk2048不等长，不能当成同一可见性。TND分支未被当前BSND方法执行，且引用未限定的变量；不存在完整TND梯度验收。

参考ReLU反向只把负值置0，没有覆盖恰为0的梯度约定；pairwise求和helper遇奇数长度会舍掉尾项，而当前K2048只覆盖偶数。不能将这些测试细节当作所有TopK、梯度归约和精度保证。本次未执行上游、NPU、图或性能实验，无新增verified；模型复核需用对应真实前向索引/评分、相同mask和有效长度，独立比较三梯度再测端到端收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 稀疏 token 索引：torch_npu.npu_lightning_indexer

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

为每个 Query 选择关键 KV 位置的 TopK 索引，供后续稀疏注意力消费。

### 文档签名

```text
torch_npu.npu_lightning_indexer(query, key, weights, *, actual_seq_lengths_query=None, actual_seq_lengths_key=None, block_table=None, layout_query="BSND", layout_key="BSND", sparse_count=2048, sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, return_value=False) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_lightning_indexer.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LightningIndexerKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_lightning_indexer.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LightningIndexerGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_lightning_indexer.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_lightning_indexer_grad.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LightningIndexerKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LightningIndexerGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_lightning_indexer.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_lightning_indexer_grad.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/lightning_indexer.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/lightning_indexer.py)（implementation）
