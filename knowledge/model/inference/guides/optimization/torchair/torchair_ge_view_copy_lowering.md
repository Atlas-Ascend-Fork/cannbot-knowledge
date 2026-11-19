---
type: Guide
title: GE视图与复制：别名、布局及符号形状
description: 审阅24组视图和复制转换，区分Identity、Assign与搬运、Bitcast版本差异、转置快捷分支及Meta输出数量。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/alias.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/alias.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/detach.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/detach.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clone.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clone.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lift_fresh_copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lift_fresh_copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/copy_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/copy_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_to_copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_to_copy.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_view.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_view.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/permute.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/permute.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/t.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/t.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/squeeze.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/squeeze.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/unsqueeze.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/unsqueeze.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/expand.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/expand.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/repeat.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/repeat.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cat.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cat.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/stack.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/stack.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/split.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/split.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/split_with_sizes.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/split_with_sizes.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/unbind.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/unbind.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sym_size.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sym_size.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/symbolic_shapes.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/symbolic_shapes.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:31:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE视图与复制：别名、布局及符号形状

## 固定版本与使用范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013中24组视图、复制、拼接/分割及符号形状Converter。主线全部非空源码与发布完整AST/注释差异已逐项审阅：18组AST相同，6组差异中view.dtype新增实际Bitcast，其他为说明、range表达和named overload兼容声明调整。

本文限定构图合同，未执行上游、GE编译、NPU数值、存储别名或性能实验。没有覆盖整卡的产品矩阵，保持draft和空平台；declare_supported只是候选声明，不能把图上Reshape/Identity或节点减少认定为设备零拷贝、任意布局合法或性能已提升。

## 复制与对象身份：不同入口不能合并解释

| 准确入口 | 本层行为和边界 |
| --- | --- |
| alias.default | 读取Shape、转INT64，再Reshape；不是在这里直接返回Python输入对象。 |
| detach.default、lift_fresh_copy.default | 都调用Identity；仅此构图形式不能认证运行时存储独立、梯度或生命周期的全部语义。 |
| clone.default | memory_format仅接受None或对象身份为torch.contiguous_format，其他明确拒绝，然后Identity。不能由clone这个名字推导所有preserve/channels_last布局或深拷贝合同在这里实现。 |
| copy.default | self与src为同一对象时Identity(src)；否则src转self.dtype。双方_symsize字符串相等就直接返回src，不同则BroadcastTo(src,Shape(self))。这是字符串比较而非完整符号等式/stride校验，规格未知或碰巧同字符串不能据此认证广播和别名。non_blocking没有参与此函数分支；源码将GE图内copy限定为同设备数值语义，不能当任意跨设备复制实现。 |
| copy_.default | 直接Assign(self,src)，没有复制copy.default的dtype与广播预处理；non_blocking也没有在这里转成交给设备的控制量。copy_.Tensor/int/float仍是独立拒绝壳。 |
| _to_copy.default | layout非None时仅接受torch.strided，memory_format非None时仅接受torch.contiguous_format；dtype不同则Cast，否则TensorMove。device、pin_memory、non_blocking没有驱动此层跨设备/固定页内存或异步路径，不能由参数存在推导已完成迁移。 |

Identity、TensorMove、Assign、Reshape、Cast和直接返回输入/源对象是不同图结构；最终是否共享Storage、是否真正搬运、外围函数化是否负责写回，需结合GE优化及图输出绑定验证。不能为了消除复制仅替换名字或把它们一概称为零拷贝。涉及输出重载的直接拒绝见下表。

## View、布局与额外转置

view.default和同文件注册的reshape.default：Python size/shape list转INT64；GE shape Tensor已有INT32/INT64时保留，其他类型才转INT64，随后Reshape。_unsafe_view.default则始终按INT64处理size，再Reshape。此处减少shape Cast的条件是源码分支，不认证任意非连续输入、元素数、别名或所有动态规格。

view.dtype是实质版本变化：发布版直接NotImplementedError，主线将dtype映射到GE类型后Bitcast(x=self,type=...)。Bitcast与数值Cast不能互换；本层没有完整验证字节宽度、stride和shape变化的所有条件，不能据新映射宣称所有dtype重解释合法。

as_strided.default把缺省storage_offset设0。静态Python List形式的stride/size且**stride[-1]>=256**时，按(stride,(原轴,size))降序排序，构造重排后的AsStrided，显式把offset转INT64，再用逆置换Transpose回原轴顺序；其他情况直接AsStrided。源码注释说“greater than256”，实际条件包含256，不能照注释写成严格大于。空stride对[-1]、输入offset与GE输入布局、重叠/越界仍需核对；没有在这里证明任意视图都安全。额外Transpose的收益只是候选设计意图，未测性能。

transpose.int在Python构造轴交换列表、转INT64后Transpose。t.default对rank<2用Identity，rank==2才交换[1,0]，rank>2拒绝；不要套用另一后端或一般permute的rank规则。

permute.default先在输入dims列表中改写负轴，再从self._symsize找出非1轴；若它们与目标去掉1轴后的顺序相同，用Squeeze再按Meta中1轴位置Unsqueeze，避免真正Transpose；否则将dims转INT64后Transpose。这个快捷分支依赖输入及输出符号规格和对size==1的判断，不是任意动态rank、缺Meta或任意置换都可消除转置，也不能据此认证元数据/stride完全等价。

## Squeeze、Expand与拼接

squeeze.default在symsize存在时只移除**非SymInt且等于1**的轴，没有这些轴则Identity；symsize缺失才直接Squeeze。squeeze.dim也仅在已知该轴为非SymInt的1时移除，否则Identity；缺规格则带轴调用Squeeze。准确squeeze.dims多轴重载仍拒绝，不能从重复单轴调用推定该overload接入。

unsqueeze.default把dim包装为axes=[dim]交Unsqueeze。expand.default明确拒绝implicit=True；只有输入与Meta都带_symsize且字符串相等时直接返回self，其余BroadcastTo(self,size)。repeat.default直接Tile(self,repeats)，源码仍有rank与repeats长度检查TODO；不能将缺检查写成任意重复规格合法。

cat.default逐个输入按Meta输出dtype处理，再ConcatV2并指定N=len(tensors)；stack.default直接Pack(tensors,N=len(tensors),axis=dim)，没有相同的逐项Meta转换。二者都不凭当前代码独立认证空列表、混合类型及所有轴关系；不要把cat的提升规则复制给stack。

## 分割输出数量依赖Meta

split.Tensor根据len(meta_outputs)创建每段split_size，最后一段设-1，再Pack、转INT64并SplitV；这个列表非空是当前索引赋值所需条件，不表示任意动态输出数量都支持。split_with_sizes.default按给定split_sizes转INT64，但num_split同样来自Meta数量。两者的dim仅在大于2147483647时转INT64，否则INT32，没有在这里完整检查负数下界或轴合法性。

unbind.int用len(meta_outputs)作为Unpack的num。split.sizes、split.default等同名准确入口仍直接拒绝，不能将另一个split_with_sizes的支持转嫁到它们。Meta输出数量、每份规格和真实维度必须一致；图上的多个输出不独立证明PyTorch分割视图的运行存储别名。

## 符号尺寸：常量专门化与GE形状表达分开

sym_size和sym_size.int共用辅助函数：Meta._meta为Python int时直接返回；为SymInt且int(str(...))成功时也作为静态数返回，否则构造INT64 Shape和Gather(dim)。Gather随后只设置_force_unknown_shape布尔属性并原样返回Tensor，并未在辅助函数里读取设备值或完成任意符号求解。sym_size.default返回整个形状列表的准确入口仍拒绝。

sym_numel及sym_numel.default都以Shape→ReduceProdD(axes=[0])→最终Cast INT64表达；最终输出是INT64不能独立证明Shape/乘积的中间累加精度或所有大尺寸无溢出。不要在缺乏中间dtype证据时把它表述成全流程64位计算。

symbolic_shapes.py尝试从torch导入sym_sqrt，失败才改从torch.fx.experimental.symbolic_shapes导入。GE Tensor实参走Sqrt；非GE Tensor分支却调用未在本文件或converter_utils绑定的sqrt符号，静态看有名称解析缺口。不能把math模块导入当成已导入sqrt函数，也不能据函数名认定Python标量回退已验证；当前未执行该分支。

## 优化与验收

保存准确FX overload、Meta符号规格、shape Tensor dtype、stride/offset及输出数量，检查Cast、Identity、TensorMove、Assign、Reshape、Transpose/Squeeze/Unsqueeze的实际组合。用后续mutation和输出Storage检查别名，再覆盖非连续视图、隐式expand、动态1维度、大尺寸、分割尾段与符号标量分支；最后对目标版本测实际搬运与稳态耗时。本次没有执行这些实验。

一般[GE构图对象与控制边](ge_converter_tensor_and_control_edges.md)和[Converter开发](torchair_converter_implementation.md)提供接口背景；foreach整数输出对象复用另见[GE批量更新转换](../../../../training/guides/torchair_ge_foreach_lowering.md)。

## 全部准确注册入口与拒绝边界

主线†表示通过getattr(...,None)兼容声明，目标不存在时没有有效Converter；发布快照相应named overload使用直接属性。表中view.dtype的构图分支仅主线，发布直接NotImplementedError。这里不将准确入口的拒绝扩展成高层函数、其他overload或其他后端全部不支持。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| alias | `torch.ops.aten.alias.default` | 无无条件拒绝壳；仍受正文分支限制 |
| detach | `torch.ops.aten.detach.default` | 无无条件拒绝壳；仍受正文分支限制 |
| clone | `torch.ops.aten.clone.default` | RuntimeError：`torch.ops.aten.clone.out` |
| lift_fresh_copy | `torch.ops.aten.lift_fresh_copy.default` | NotImplementedError：`torch.ops.aten.lift_fresh_copy.out` |
| copy | `torch.ops.aten.copy.default` | NotImplementedError：`torch.ops.aten.copy.out` |
| copy_ | `torch.ops.aten.copy_.default` | NotImplementedError：`torch.ops.aten.copy_.Tensor`、`torch.ops.aten.copy_.int`、`torch.ops.aten.copy_.float` |
| _to_copy | `torch.ops.aten._to_copy.default` | RuntimeError：`torch.ops.aten._to_copy.out` |
| view | `torch.ops.aten.view.default`、`torch.ops.aten.view.dtype`、`torch.ops.aten.reshape.default` | 无无条件拒绝壳；仍受正文分支限制 |
| _unsafe_view | `torch.ops.aten._unsafe_view.default` | NotImplementedError：`torch.ops.aten._unsafe_view.out` |
| as_strided | `torch.ops.aten.as_strided.default` | 无无条件拒绝壳；仍受正文分支限制 |
| transpose | `torch.ops.aten.transpose.int` | NotImplementedError：`torch.ops.aten.transpose.Dimname`† |
| permute | `torch.ops.aten.permute.default` | 无无条件拒绝壳；仍受正文分支限制 |
| t | `torch.ops.aten.t.default` | 无无条件拒绝壳；仍受正文分支限制 |
| squeeze | `torch.ops.aten.squeeze.default`、`torch.ops.aten.squeeze.dim` | NotImplementedError：`torch.ops.aten.squeeze.dims`、`torch.ops.aten.squeeze.dimname`† |
| unsqueeze | `torch.ops.aten.unsqueeze.default` | 无无条件拒绝壳；仍受正文分支限制 |
| expand | `torch.ops.aten.expand.default` | 无无条件拒绝壳；仍受正文分支限制 |
| repeat | `torch.ops.aten.repeat.default` | NotImplementedError：`torch.ops.aten.repeat.out` |
| cat | `torch.ops.aten.cat.default` | NotImplementedError：`torch.ops.aten.cat.names`†、`torch.ops.aten.cat.names_out`†、`torch.ops.aten.cat.out` |
| stack | `torch.ops.aten.stack.default` | NotImplementedError：`torch.ops.aten.stack.out` |
| split | `torch.ops.aten.split.Tensor` | NotImplementedError：`torch.ops.aten.split.sizes`、`torch.ops.aten.split.str`、`torch.ops.aten.split.default` |
| split_with_sizes | `torch.ops.aten.split_with_sizes.default` | 无无条件拒绝壳；仍受正文分支限制 |
| unbind | `torch.ops.aten.unbind.int` | NotImplementedError：`torch.ops.aten.unbind.Dimname`† |
| sym_size | `torch.ops.aten.sym_size`、`torch.ops.aten.sym_size.int`、`torch.ops.aten.sym_numel`、`torch.ops.aten.sym_numel.default` | NotImplementedError：`torch.ops.aten.sym_size.default` |
| symbolic_shapes | `sym_sqrt` | 无无条件拒绝壳；仍受正文分支限制 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/alias.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/alias.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/detach.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/detach.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clone.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clone.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/lift_fresh_copy.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/lift_fresh_copy.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/copy.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/copy.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/copy_.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/copy_.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_to_copy.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_to_copy.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/view.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/view.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_view.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_unsafe_view.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/as_strided.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/transpose.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/transpose.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/permute.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/permute.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/t.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/t.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/squeeze.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/squeeze.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/unsqueeze.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/unsqueeze.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/expand.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/expand.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/repeat.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/repeat.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/cat.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/cat.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/stack.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/stack.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/split.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/split.py)（implementation）
- [固定来源 41](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/split_with_sizes.py)（implementation）
- [固定来源 42](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/split_with_sizes.py)（implementation）
- [固定来源 43](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/unbind.py)（implementation）
- [固定来源 44](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/unbind.py)（implementation）
- [固定来源 45](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sym_size.py)（implementation）
- [固定来源 46](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sym_size.py)（implementation）
- [固定来源 47](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/symbolic_shapes.py)（implementation）
- [固定来源 48](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/symbolic_shapes.py)（implementation）
- [固定来源 49](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 50](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 51](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 52](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
