---
type: Guide
title: GE EmbeddingBag：模式、索引与辅助输出
description: 区分两个EmbeddingBag入口的默认mode、INT32索引转换和参数透传，不继承普通Embedding的前向拒绝规则。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag_forward_only.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag_forward_only.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T09:13:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE EmbeddingBag：模式、索引与辅助输出

## 固定版本与证据边界

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线完整非空源码、发布完整AST/注释差异均已阅读；本卡平台矩阵未知，保持draft与空平台，未执行上游、GE编译、NPU精度/反向或性能实验。Support只是候选声明，静态构图不替代kernel、ABI和高层函数验证。

## 两条EmbeddingBag入口并不完全相同

_embedding_bag.default与_embedding_bag_forward_only.default都将weight、indices、offsets、per_sample_weights及scale_grad_by_freq/sparse/include_last_offset/padding_idx传EmbeddingBag，并原序返回GE结果；Schema列四返回，本层没有按各Meta再Cast或重新排序，辅助输出的真实语义与ABI不能从数量单独认证。

两函数的Python mode默认**1**，Schema注释却写默认0；实际调用链是否显式补上Schema默认值需要另审，不能默认为这里省略参数就是sum。_get_mode_str只把0映射sum、2映射max，其他所有值都回退mean，没有0..2范围检查。

forward_only入口先将indices和offsets都转INT32；普通_embedding_bag入口没有同样Cast。大INT64索引与offset是否无损，以及底层支持的索引组合需按准确入口核对；“forward_only”名字不表示全部参数已验证，也不由另一个入口的Cast推导这条路径相同。

## 参数透传与独立验证

本层没有单独拒绝scale_grad_by_freq=True或sparse=True，也没有完整校验per_sample_weights与mode、offsets边界、include_last_offset和padding_idx。不能把普通[Embedding转换](torchair_ge_index_scatter_lowering.md)对频次/稀疏参数的明确拒绝直接套用，也不能以这里没有拒绝来认证训练和稀疏梯度能力。

两份out重载无条件AssertionError；报错中的旧PyTorch版本和未来支持措辞不是版本承诺。两快照此组AST相同，未运行实际样例。优化前确认FX准确入口、实际mode默认来源、indices/offsets dtype和取值、权重/辅助输出及分组规则，再验证数值、梯度与吞吐。

## 准确入口与拒绝重载

可构图入口仍受正文条件限制；拒绝仅指准确映射，不扩高层函数或其他后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _embedding_bag | `torch.ops.aten._embedding_bag.default` | `torch.ops.aten._embedding_bag.out` (AssertionError) |
| _embedding_bag_forward_only | `torch.ops.aten._embedding_bag_forward_only.default` | `torch.ops.aten._embedding_bag_forward_only.out` (AssertionError) |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag_forward_only.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_embedding_bag_forward_only.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
