---
type: Guide
title: GE索引与Scatter：掩码、累加及类型边界
description: 归并索引、Embedding与SearchSorted转换，核对INT32/INT64处理、输入保护、掩码重载及前反向不同条件。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_index.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_index.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index_select.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index_select.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding_dense_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding_dense_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/searchsorted.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/searchsorted.py
  role: implementation
created_at: '2026-11-10T08:14:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE索引与Scatter：掩码、累加及类型边界

## 版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013，本卡包含初始11组索引、掩码、累加与EmbeddingConverter及后文补充的SearchSorted。主线全部非空源码及发布完整AST/注释差异均已核对；两版差异为named overload兼容声明和等价range/list写法，不把它们记成计算算法升级。

这里限定静态构图合同，平台矩阵未知，保持draft与空平台；未执行上游、GE编译、NPU精度/别名/确定性或性能实验。declare_supported只表示候选声明，源码警告和TODO不构成本次复现。需要区分准确overload、前反向、图中原地节点和外围函数化，不能只凭有注册就认证所有dtype、动态边界、重复索引及存储语义。

## 高级索引与Gather的类型处理不同

| 准确入口 | 本层构图行为 |
| --- | --- |
| index.Tensor | 按Python真值构造indices_mask，筛选剩余项并分别转INT64，然后IndexByTensor(self,indices,indices_mask=mask)。不由这个转换认证任意bool-mask索引、广播或越界语义。 |
| _unsafe_index.Tensor | self为BOOL或UINT8时明确拒绝；同样筛选indices并构造mask，但没有复制index.Tensor的逐项INT64转换。unsafe名字不表示可以忽略类型与范围。 |
| index_select.default | dim转INT64，然后GatherV2(self,index,dim)，index在此函数未统一转换。 |
| gather.default | index转INT64后GatherElements(self,index,dim=dim)，sparse_grad形参未参与此函数分支或GE属性；不能从前向入图推导稀疏梯度合同已实现。 |

不同Gather入口不能仅按数学功能共享Cast规则。shape为0、空索引及不同dtype的declare_supported候选只提供验证线索，不是全部这些组合已实测的矩阵。

## index_add的维度、广播和输入保护

index_add.default先把alpha转self.dtype；来源警告称类型不一致可能段错误，但本次未复现。index.rank==0时先Unsqueeze为一维，**这是零维索引判断，不是零长度索引的完整保护**，不能照注释里的size0混写。

函数在index Cast之前取得index.rank及Shape(index)/Shape(self)，随后将非INT32索引转INT32；源警告里的INT64 kernel问题仅作为此转换动机。负dim只加一次self.rank，不在这里完整校验任意越界轴。它用self各轴大小、在目标轴替换为index长度构造pad_size，并BroadcastTo(source,pad_size)。这不是逐项按输出Meta统一提升，也不能证明任意source形状或大INT64索引范围无损。

调用InplaceIndexAdd之前先TensorMove(self)，再传index、广播后的source及alpha。不能为了消除搬运就任意删掉这一步，也不能把GE节点名字中的Inplace等同公开index_add已经改写用户输入。重复索引的累加顺序、浮点精度及确定性需按目标kernel验证；当前没有测量。

## MaskedFill与Scatter的重载边界

| 入口 | 本层参数与更新方式 |
| --- | --- |
| masked_fill.Scalar、masked_fill.Tensor | value按Meta输出dtype处理，再MaskedFill(self,mask,value)，没有在该函数把self一并转Meta。 |
| masked_fill_.Scalar | 直接MaskedFill(self,mask,value)，没有同样的value提升，也没有在此层另加Assign；外围如何保持原地别名需单独核对。准确masked_fill_.Tensor仍直接拒绝。 |
| scatter.value | value转self.dtype并按Shape(index)填成src，然后ScatterElements(...,axis=dim)。 |
| scatter.src | 直接ScatterElements(self,index,src,axis=dim)，不复制gather的索引INT64 Cast或index_add的INT32处理。 |
| scatter_add.default | 同样直接ScatterElements，但指定reduction='add'；这不是scatter.reduce/value_reduce全部模式可用的证明，后两者准确入口仍直接拒绝。 |

值覆盖、加法归约与原地函数化是不同合同；不从同一个ScatterElements名字推导重复索引、dtype、空index和梯度规则相同。文档[ATen约束](torchair_aten_constraint_review.md)要求scatter_add非空index，也不能因Python函数未显式检查就抹去这条限制。

## Embedding前反向的条件分别保留

embedding.default明确拒绝scale_grad_by_freq=True及sparse=True，随后GatherV2(weight,indices,[0])；padding_idx没有在这里单独传交，不能据此替代完整Embedding模块的前反向行为分析。

embedding_dense_backward.default反而允许scale_grad_by_freq形参：为True时将indices转INT32，为False时保留原索引类型；num_weights或padding_idx若为GE Tensor则RuntimeError，其他情况交EmbeddingDenseGrad的对应属性。不能把前向拒绝某参数直接传播为此反向也拒绝，也不能由反向有属性推导前向支持。

## 优化与验收

保存真实FX overload、index dtype/rank、dim、alpha/value类型、mask及Meta输出；检查索引是转INT32、INT64还是保持原类型，source是否被Broadcast，输入是否先TensorMove。覆盖大索引、重复索引、空index、混合类型、原地后续mutation与Embedding频次缩放；数值和别名确认后再测吞吐。当前只做静态审阅，不将候选声明或警告当实验结论。

切片与反向形状恢复另见[GE切片与写回](torchair_ge_slice_scatter_lowering.md)，视图和复制见[GE视图与复制](torchair_ge_view_copy_lowering.md)。

## 准确overload与直接拒绝清单

主线†表示getattr(...,None)兼容声明，目标缺失不形成有效Converter；发布版相应named目标用直接属性访问。表中有构图分支仍受正文条件限制，直接拒绝不扩展到高层函数、其他overload或其他后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _unsafe_index | `torch.ops.aten._unsafe_index.Tensor` | 无无条件拒绝壳；仍有正文参数边界 |
| index | `torch.ops.aten.index.Tensor` | RuntimeError：`torch.ops.aten.index.Tensor_out`、`torch.ops.aten.index.Tensor_hacked_twin`、`torch.ops.aten.index.str`、`torch.ops.aten.index.list_int`、`torch.ops.aten.index.list_float`、`torch.ops.aten.index.list_bool`、`torch.ops.aten.index.list_Tensor`、`torch.ops.aten.index.list_str` |
| index_add | `torch.ops.aten.index_add.default` | RuntimeError：`torch.ops.aten.index_add.out`、`torch.ops.aten.index_add.dimname`† |
| index_select | `torch.ops.aten.index_select.default` | RuntimeError：`torch.ops.aten.index_select.out`、`torch.ops.aten.index_select.dimname`†、`torch.ops.aten.index_select.dimname_out`† |
| gather | `torch.ops.aten.gather.default` | NotImplementedError：`torch.ops.aten.gather.out`、`torch.ops.aten.gather.dimname`†、`torch.ops.aten.gather.dimname_out`† |
| masked_fill | `torch.ops.aten.masked_fill.Scalar`、`torch.ops.aten.masked_fill.Tensor` | NotImplementedError：`torch.ops.aten.masked_fill.Scalar_out`、`torch.ops.aten.masked_fill.Tensor_out` |
| masked_fill_ | `torch.ops.aten.masked_fill_.Scalar` | NotImplementedError：`torch.ops.aten.masked_fill_.Tensor` |
| scatter | `torch.ops.aten.scatter.value`、`torch.ops.aten.scatter.src` | RuntimeError：`torch.ops.aten.scatter.reduce`、`torch.ops.aten.scatter.value_reduce`、`torch.ops.aten.scatter.src_out`、`torch.ops.aten.scatter.value_out`、`torch.ops.aten.scatter.reduce_out`、`torch.ops.aten.scatter.value_reduce_out`、`torch.ops.aten.scatter.dimname_src`†、`torch.ops.aten.scatter.dimname_value`† |
| scatter_add | `torch.ops.aten.scatter_add.default` | RuntimeError：`torch.ops.aten.scatter_add.out`、`torch.ops.aten.scatter_add.dimname`† |
| embedding | `torch.ops.aten.embedding.default` | NotImplementedError：`torch.ops.aten.embedding.out` |
| embedding_dense_backward | `torch.ops.aten.embedding_dense_backward.default` | NotImplementedError：`torch.ops.aten.embedding_dense_backward.out` |

## SearchSorted的side覆盖和索引输出类型

同两固定快照的searchsorted.py全文与AST/注释差异已核对，AST相同。准确torch.ops.aten.searchsorted.Tensor根据out_int32选INT32或INT64；side非None时必须left/right，并用side=='right'覆盖原right值。本层没有单独拒绝side与right冲突组合，不能从两个参数同时出现推导其冲突语义已验证。

SearchSorted将sorted_sequence、self与sorter原样传入，dtype属性控制输出索引类型，right控制边界侧；本层没有统一转换sorter和输入dtype、检查排序性/索引合法性或任意NaN规则。torch.ops.aten.searchsorted.Tensor_out、torch.ops.aten.searchsorted.Scalar及torch.ops.aten.searchsorted.Scalar_out均无条件NotImplementedError，不从Tensor版本认证标量输入已入图。真实输入应分别核对插入侧、sorter、边界值及输出宽度后再评估性能。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_index.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_index.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index_add.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index_add.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/index_select.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/index_select.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/gather.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/gather.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill_.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/masked_fill_.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter_add.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scatter_add.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding_dense_backward.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/embedding_dense_backward.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/searchsorted.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/searchsorted.py)（implementation）
