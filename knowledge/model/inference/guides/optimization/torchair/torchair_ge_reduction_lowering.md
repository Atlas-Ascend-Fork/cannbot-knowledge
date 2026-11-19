---
type: Guide
title: GE归约与排序：空输入、精度与索引合同
description: 归并13组转换的空Tensor、维度列表、标准差版本差异、归约前后Cast及排序索引顺序，保留准确拒绝重载。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sum.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mean.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mean.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/argmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/argmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/argmin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/argmin.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/all.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/all.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/any.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/any.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logsumexp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logsumexp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/std.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/std.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/linalg_vector_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/linalg_vector_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cumsum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cumsum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/topk.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/topk.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sort.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sort.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:07:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE归约与排序：空输入、精度与索引合同

## 版本与使用前提

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的完整Converter合同。主线逐个审阅全部非空源码，发布版通过完整AST对比、所有AST变化及注释变化核对；不把AST相同当字节相同。平台矩阵未知，保持draft与空平台；未执行上游、GE编译、smoke或NPU数值/性能实验。

declare_supported只是声明与测试输入候选，不是已运行结果。Meta、显式Cast、GE节点的推导和设备kernel各自约束仍须核对，不能由Python分支存在推导所有dtype、广播、空输入及动态形状都支持。[类型转换辅助函数](torchair_ge_arithmetic_lowering.md)按调用方指定dtype转换，不自行选择完整PyTorch公共类型；本文保留各准确overload的不同调用顺序。

## 求和与均值的形状、dtype和空输入

sum.dim_IntList的普通路径将dim=None或空列表展开为全部rank轴，按meta_outputs.dtype处理输入后ReduceSum；dtype形参没有在这里单独传给GE，其影响依赖前端产生的正确Meta。sum.default也总是先Cast到Meta输出dtype，再对全部轴ReduceSum；不能用输入整数dtype直接推断累加或输出dtype。

sum.dim_IntList在普通路径**之前**检查symsize乘积是否为0；已知空输入时用Shape/Gather拼输出shape、Fill对应dtype的0。辅助函数要求dim为整数list，用d%rank、降序删除轴或置1；所以dim=None的空输入在展开全部轴之前会先触发AssertionError，dim=[]则不会删除任何轴。不能从普通路径支持None/[]推导空输入分支也保留同样输出shape。重复轴、rank=0及符号乘积的Python判定也需单独核对，不能把这些静态分支视为任意动态形状证明。

mean.default在显式dtype存在时先按该dtype处理输入，否则用Meta，再对全部轴ReduceMean。mean.dim把None/[]都展开全轴，显式dtype时用ReduceMeanWithCast及对应GE类型属性，否则直接ReduceMean，没有复制default的Meta转换分支。两者名称相近并不表示计算精度选择和图结构完全一致。

## 标准差：发布版与主线实现不同

这里只实现std.correction；std.default、std.dim及全部命名/输出重载仍直接拒绝。correction=None先设1。主线把dim=None/[]规范为[]，并在is_arch35()设备名分支调用ReduceStdV2(is_mean_out=False)，只返回std；其他分支先ReduceMean，必要时按排序轴Unsqueeze，再Expand为输入Shape，交ReduceStdWithMean。发布版没有ReduceStdV2分支，也没有dim规范化；不能把主线的处理回推到发布版。

特殊shape处理只在symsize存在、归约元素乘积不是SymInt、输出shape能够构造时生效：乘积为0，或乘积为1且常量correction不小于它时，Fill NaN；其他常量correction>1且乘积不大于correction时，Fill inf。它没有读取输入真实数值，不能据此认定常数输入、所有无自由度情形和完整PyTorch数值语义都一致。Tensor correction也不走这些常量比较分支。

需要保留三个源码缺口：发布版dim=None可能在len(dim)处失败；发布版calc_shape_prod的dim=[]分支调用functools.reduce，却既没有本文件import，也未从converter_utils导入该模块；主线补了import functools。两版get_output_size对dim=[]都保持原shape，没有在这个特殊Fill分支展开全轴；这与calc_shape_prod把空dim当全部元素的处理不一致。上述是静态控制流观察，不是设备复现；排查时比较实际Meta/输出shape，不将其写成已验证的标准差优化配方。

is_arch35()是设备名子串判定：发布识别Ascend910_95/Ascend950，主线另含Ascend350；不构成完整产品支持矩阵。普通路径对负轴的Unsqueeze排序、dim=[-1]特例与多个轴保留方式还需按真实输入检查，不能因均值已Expand就推定所有轴组合一致。

## 最大值、索引与排序的精度和输出次序

| 准确入口 | 静态实现与限制 |
| --- | --- |
| max.default | 构造全部轴的INT64 Const，输入转Meta dtype，ReduceMax。max.other二元逐元素重载仍直接拒绝，不能与maximum.default互换登记范围。 |
| max.dim | GE ArgMaxWithValue先返回index、value，Converter重排为value、index，索引按第二份Meta dtype处理。重排不是相同顺序透传。 |
| argmax.default、argmin.default | dim=None时先展平(-1,)后在axis0调用ArgMaxV2/ArgMin，这条分支未按keepdim恢复原rank；显式dim且keepdim=True时先把输入转FP32，再ArgMax/MinWithValue并把索引转INT64。大整数或FP64相近值可能因这个转换丢失区分，需单独数值核对；不能从keepdim=False路径推导保持相同计算精度。其他显式dim用INT64轴及ArgMaxV2/ArgMin。 |
| topk.default | k、sorted、dim、largest传TopKV2，返回value和按第二份Meta转换的indices；没有在本层校验全部k范围或证明动态k可执行。topk.values输出重载拒绝。 |
| sort.default | 负dim先加rank；非末轴排序会交换该轴和末轴，先Transpose，再末轴Sort，再将values/indices分别Transpose回去；索引最后固定INT64。额外转置的实际成本要看编译优化结果，不能直接宣称消除。stable、所有values输出及named重载都拒绝，不能由default推导稳定排序。 |

## 其他归约与累积

| 入口 | 本层合同 |
| --- | --- |
| all.default | 输入按Meta输出dtype处理后全轴ReduceAll；准确all.dim仍未实现。 |
| any.default、any.dim | 两者显式转BOOL；default对零维输入先Unsqueeze再归约axis0，其余全轴。dim分支通常包装单轴；dim==-sys.maxsize-1时却使用range(dim)，结果为空轴列表，并不是range(rank)。仅记录此静态分支，不把特殊哨兵当正常全轴保证。 |
| logsumexp.default | 输入先转Meta，保留维度求ReduceMax；将绝对值为inf的max替为0，再ReduceLogSumExp(self-max)，最后加回按keepdim处理的max。Squeeze辅助把负轴加rank、拒绝重复轴，空轴列表视全轴；是否覆盖全部非有限值和空输入需单独验证。 |
| linalg_vector_norm.default | ord的正/负inf映射为INT32最大/最小值，dim为None/[]时传空axes，调用LpNormV2(epsilon=0)。**显式dtype只在LpNormV2结果之后转换**，不能据返回dtype证明已用该精度累加；未指定时按输入dtype处理结果，而非Meta。 |
| cumsum.default | 显式dtype存在则先按它处理输入，否则用Meta输出dtype，再Cumsum；与范数的结果后Cast顺序不同。源码称INT16样例Eager dtype不正确只是既有注释，不是本次复现实验。 |

## 验收与优化判断

核对真实FX overload、dim=None/[]/负轴、keepdim、索引顺序、Meta及Cast在归约前还是归约后；覆盖空Tensor、大整数、近似极值、FP64相邻值、无自由度标准差和动态维度。对排序查看是否保留额外Transpose，对标准差分开比较两个固定快照的GE图。测量前不能仅按节点数或输出dtype声称精度/吞吐提升。

文档能力条目见[ATen入图约束](torchair_aten_constraint_review.md)，Softmax前反向另见[GESoftmax转换](torchair_ge_softmax_lowering.md)。

## 全部准确注册重载与拒绝边界

下表仅描述实际选中此内置Converter后的构图或直接拒绝。主线†表示getattr(...,None)兼容声明，目标不存在时不建立有效Converter；发布快照这些named overload使用直接属性访问。不把兼容声明变化当成计算实现新增，也不否定高层函数可经decomposition或其他后端执行。

| 来源主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| sum | `torch.ops.aten.sum.dim_IntList`、`torch.ops.aten.sum.default` | RuntimeError：`torch.ops.aten.sum.dim_DimnameList`†、`torch.ops.aten.sum.DimnameList_out`†、`torch.ops.aten.sum.IntList_out`、`torch.ops.aten.sum.out`、`torch.ops.aten.sum.int`、`torch.ops.aten.sum.float`、`torch.ops.aten.sum.complex`、`torch.ops.aten.sum.bool` |
| mean | `torch.ops.aten.mean.default`、`torch.ops.aten.mean.dim` | RuntimeError：`torch.ops.aten.mean.names_dim`†、`torch.ops.aten.mean.names_out`†、`torch.ops.aten.mean.out` |
| max | `torch.ops.aten.max.default`、`torch.ops.aten.max.dim` | RuntimeError：`torch.ops.aten.max.other`、`torch.ops.aten.max.dim_max`、`torch.ops.aten.max.names_dim`†、`torch.ops.aten.max.names_dim_max`†、`torch.ops.aten.max.unary_out`、`torch.ops.aten.max.out` |
| argmax | `torch.ops.aten.argmax.default` | RuntimeError：`torch.ops.aten.argmax.out` |
| argmin | `torch.ops.aten.argmin.default` | NotImplementedError：`torch.ops.aten.argmin.out` |
| all | `torch.ops.aten.all.default` | NotImplementedError：`torch.ops.aten.all.dim`、`torch.ops.aten.all.out`、`torch.ops.aten.all.all_out`、`torch.ops.aten.all.dimname`†、`torch.ops.aten.all.dimname_out`†、`torch.ops.aten.all.int`、`torch.ops.aten.all.float`、`torch.ops.aten.all.bool` |
| any | `torch.ops.aten.any.default`、`torch.ops.aten.any.dim` | NotImplementedError：`torch.ops.aten.any.out`、`torch.ops.aten.any.all_out`、`torch.ops.aten.any.dimname`†、`torch.ops.aten.any.dimname_out`†、`torch.ops.aten.any.str`、`torch.ops.aten.any.int`、`torch.ops.aten.any.float`、`torch.ops.aten.any.bool` |
| logsumexp | `torch.ops.aten.logsumexp.default` | RuntimeError：`torch.ops.aten.logsumexp.names`†、`torch.ops.aten.logsumexp.names_out`†、`torch.ops.aten.logsumexp.out` |
| std | `torch.ops.aten.std.correction` | NotImplementedError：`torch.ops.aten.std.default`、`torch.ops.aten.std.dim`、`torch.ops.aten.std.names_dim`†、`torch.ops.aten.std.names_out`†、`torch.ops.aten.std.out`、`torch.ops.aten.std.correction_out`、`torch.ops.aten.std.correction_names`†、`torch.ops.aten.std.correction_names_out`† |
| linalg_vector_norm | `torch.ops.aten.linalg_vector_norm.default` | NotImplementedError：`torch.ops.aten.linalg_vector_norm.out` |
| cumsum | `torch.ops.aten.cumsum.default` | NotImplementedError：`torch.ops.aten.cumsum.dimname`†、`torch.ops.aten.cumsum.dimname_out`†、`torch.ops.aten.cumsum.out` |
| topk | `torch.ops.aten.topk.default` | NotImplementedError：`torch.ops.aten.topk.values` |
| sort | `torch.ops.aten.sort.default` | RuntimeError：`torch.ops.aten.sort.stable`、`torch.ops.aten.sort.values_stable`、`torch.ops.aten.sort.values`、`torch.ops.aten.sort.dimname`†、`torch.ops.aten.sort.dimname_values`†、`torch.ops.aten.sort.dimname_stable`†、`torch.ops.aten.sort.dimname_values_stable`†、`torch.ops.aten.sort.int`、`torch.ops.aten.sort.float`、`torch.ops.aten.sort.Tensor`、`torch.ops.aten.sort.bool`、`torch.ops.aten.sort.str` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sum.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sum.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mean.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mean.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/max.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/max.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/argmax.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/argmax.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/argmin.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/argmin.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/all.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/all.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/any.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/any.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/logsumexp.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/logsumexp.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/std.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/std.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/linalg_vector_norm.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/linalg_vector_norm.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cumsum.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cumsum.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/topk.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/topk.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sort.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sort.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
