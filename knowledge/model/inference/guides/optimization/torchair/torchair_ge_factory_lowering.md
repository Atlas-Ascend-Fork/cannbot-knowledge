---
type: Guide
title: GE创建与初始化：生成精度、Fill及布局边界
description: 归并18组工厂转换，区分Range生成前后Cast、标量shape、Empty与零填充、默认dtype和stride存储约束。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/arange.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/arange.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/linspace.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/linspace.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scalar_tensor.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scalar_tensor.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/full.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/full.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/full_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/full_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_full.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_full.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/empty.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/empty.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/empty_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/empty_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty_strided.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty_strided.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_zeros.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_zeros.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ones.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ones.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ones_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ones_like.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_ones.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_ones.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/fill.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/fill.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zero.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zero.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:39:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE创建与初始化：生成精度、Fill及布局边界

## 固定版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的18组Tensor创建/初始化Converter。主线全部非空源码及发布完整AST、注释差异已审阅；14组AST相同，4组差异只涉及named overload的getattr兼容声明，所审阅计算分支相同，不把注册兼容变化写成新的初始化算法。

本文限定静态构图合同。未执行上游、GE编译、smoke或NPU精度/存储/性能实验，没有覆盖整卡的产品矩阵，保持draft与空平台。declare_supported是候选声明，不表示运行已通过；Fill、Empty和Cast等图节点也不独立证明实际设备启动次数、内存成本或输出别名。

## 序列创建：生成前与生成后转换不同

| 准确入口 | 此层计算顺序 |
| --- | --- |
| arange.default | start=INT32 Const(0)、step=INT32 Const(1)，先Range，再按显式dtype真值或Meta输出dtype处理结果。没有在该函数先统一end与两个Const到输出dtype。 |
| arange.start | step为INT32 Const(1)，先Range(start,end,step)再处理结果dtype，不能从输出FP16/BF16推定序列在该精度生成。 |
| arange.start_step | 先把start/end/step全部按目标dtype处理，再Range，最后再次按目标dtype处理结果；与前两个overload的精度顺序不同。 |
| linspace.default | steps<0拒绝；layout非None时仅接受strided；先LinSpace，只有显式dtype非None时转换结果，没有在此函数统一端点或按Meta输出dtype转换。 |

arange各分支的layout、device、pin_memory不参与构图计算；linspace也没有依据device/pin_memory建立对应迁移或固定页内存路径。参数被绑定不表示这些配置完整实现，不能用相同返回dtype认定不同序列生成路径数值等价。需要分别覆盖浮点步长、端点、steps=0/1、大整数和极端值，当前没有执行这些实验。

## 标量、Full与零维shape

scalar_tensor.default在显式dtype存在时通过dtype_promote转Cast/Const；未指定dtype且s已经是GE Tensor时直接返回s，否则Const(s)。这里没有再用Meta覆盖默认dtype，也没有处理device/layout/pin_memory的独立分支；接口名字不能认证一定产生新的设备对象。

full.default按显式dtype（is not None）或Meta处理fill_value；size不是GE Tensor且np.array(size).size为0时直接返回处理后的fill_value，其他情况Fill(size,fill_value)。这针对**空shape列表所代表的零维规格**，与shape=[0]的零元素Tensor不是同一个判断，也不认证任意非标量fill_value已广播。

new_full.default默认用self.dtype、显式dtype则用指定类型处理fill_value，layout只允许None/strided，再Fill。full_like.default先取Shape(self)，显式dtype真值生效时还可能转换self，再把fill_value Cast至目标dtype进行Fill；它没有将memory_format/device/pin_memory变为独立构图控制。由于Fill依赖shape和值，不应仅凭源码出现self Cast就断言设备必定为它搬运整张输入，是否消除仍看实际GE图。

## Empty与Fill的初始化成本分别判断

| 准确入口 | 本层节点、dtype与布局限制 |
| --- | --- |
| empty.memory_format | layout仅None/strided，memory_format仅None/contiguous_format；实际返回Fill(size,Cast(0.0,Meta输出dtype))，不是直接Empty。dtype参数没有在此函数独立选择输出类型，其效果依赖正确Meta。 |
| empty_like.default | layout仅None/strided，memory_format允许None/contiguous_format/preserve_format；实际同样按Meta输出dtype零填充输入Shape。源码注释称动态INT8的Empty问题导致替换，只记录为来源动机，不当作本次复现结果或所有版本故障。 |
| new_empty.default | 缺省dtype取self.dtype，显式dtype映射成GE类型；size转INT32，layout仅None/strided，再Empty(size,dtype)。不是上述全零Fill路径。 |
| new_empty_strided.default | 与new_empty相同先按size调用Empty，然后AsStrided(result,size,stride,0)。没有在本层另按stride计算所需Storage跨度或扩充分配；不能从入口接受stride推定任意大stride/重叠/越界均合法。 |

empty_like虽然接受preserve_format，所示分支也没有显式传入原stride来证明任意布局完整保持；new_empty_strided则需把分配范围与视图范围一并核对。不能为了消除初始化成本，把这些入口全部当成同一种“只分配不写数据”。Fill是否在下游覆盖前被消除、Empty是否真正节省带宽，需观察编译后图并实测。

## Zeros、Ones和继承型创建的dtype来源

| 准确default入口 | 静态类型处理 |
| --- | --- |
| zeros | dtype=None时Fill(size,0.0)，不读取Meta输出dtype；显式dtype时将0.0 Cast到指定GE类型后Fill。不能仅从Meta推导该无显式dtype分支的所有默认类型。 |
| ones | dtype=None固定选DT_FLOAT，否则显式类型映射；Const(1,dtype)后Fill。该函数没有读取可变外部默认类型或Meta，不把注释“default float”当任意默认配置已验证。 |
| zeros_like | 显式dtype时先转换self，再ZerosLike；否则原self直接ZerosLike。layout/device/pin_memory/memory_format没有在此函数建立完整布局和迁移处理。 |
| ones_like | 默认取self.dtype，显式dtype映射；layout真值存在且非strided时拒绝；输入按目标dtype处理再OnesLike。 |
| new_zeros | 默认取self.dtype或显式类型映射，layout真值存在且非strided时拒绝；Fill(size,同dtype的0)。 |
| new_ones | 默认取self.dtype或显式类型映射，layout非None且非strided时拒绝；Fill(size,同dtype的1)。这个layout判断与前两行的真值判断并非相同原码。 |

这些创建接口对显式dtype、默认类型、self继承和Meta的选择不同，不能为统一描述而抹平。device/pin_memory等未使用参数也不能依名字推导任意跨设备创建；需要与图输入放置和实际运行环境单独核对。

## Fill、Zero与输出重载

fill.Scalar和fill.Tensor都取Shape(self)，将value Cast至self.dtype再Fill；本层没有按全部Tensor value形状补广播或输出Meta类型，也没有使用Assign改写self。zero.default则直接ZerosLike(self)。准确非原地注册入口与fill_/zero_的函数化或mutation路径应分开确认，不能由普通Schema说明推导任意原地写回已保持。

全部out/named拒绝入口逐项列在下表；其中RuntimeError、NotImplementedError及new_empty_strided的AssertionError保留区别。消息中的旧PyTorch版本或out拼写错误只作为源码诊断，不当成当前兼容矩阵或较新版本自动支持证明。

## 优化与验收

记录准确FX overload、size列表或GE shape Tensor、dtype来源、value类型及布局请求；检查Cast在生成前还是生成后，以及实际出现Fill、Empty、ZerosLike还是OnesLike。比较零维shape、零元素Tensor、极端序列、动态INT8、非连续布局及stride所需存储范围，再确认初始化是否被覆盖/消除，最后测实际成本。当前只有静态审阅，没有把候选分支写成已验证的性能配方。

类型转换辅助见[GE算术转换](torchair_ge_arithmetic_lowering.md)，复制、视图和符号shape边界见[GE视图与复制](torchair_ge_view_copy_lowering.md)，通用方法见[Converter开发](torchair_converter_implementation.md)。

## 准确注册入口与拒绝边界

主线†表示getattr(...,None)兼容声明，目标不存在时没有有效Converter；发布快照相应named overload为直接属性访问。下表只描述实际选中内置Converter后的分支，不将同名高层函数、decomposition或其他后端一概判断为不支持。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| arange | `torch.ops.aten.arange.default`、`torch.ops.aten.arange.start`、`torch.ops.aten.arange.start_step` | RuntimeError：`torch.ops.aten.arange.start_out`、`torch.ops.aten.arange.out` |
| linspace | `torch.ops.aten.linspace.default` | RuntimeError：`torch.ops.aten.linspace.out` |
| scalar_tensor | `torch.ops.aten.scalar_tensor.default` | NotImplementedError：`torch.ops.aten.scalar_tensor.out` |
| full | `torch.ops.aten.full.default` | NotImplementedError：`torch.ops.aten.full.names`†、`torch.ops.aten.full.names_out`†、`torch.ops.aten.full.out` |
| full_like | `torch.ops.aten.full_like.default` | RuntimeError：`torch.ops.aten.full_like.out` |
| new_full | `torch.ops.aten.new_full.default` | RuntimeError：`torch.ops.aten.new_full.out` |
| empty | `torch.ops.aten.empty.memory_format` | RuntimeError：`torch.ops.aten.empty.out`、`torch.ops.aten.empty.names`†、`torch.ops.aten.empty.names_out`† |
| empty_like | `torch.ops.aten.empty_like.default` | RuntimeError：`torch.ops.aten.empty_like.out` |
| new_empty | `torch.ops.aten.new_empty.default` | RuntimeError：`torch.ops.aten.new_empty.out` |
| new_empty_strided | `torch.ops.aten.new_empty_strided.default` | AssertionError：`torch.ops.aten.new_empty_strided.out` |
| zeros | `torch.ops.aten.zeros.default` | RuntimeError：`torch.ops.aten.zeros.names`†、`torch.ops.aten.zeros.names_out`†、`torch.ops.aten.zeros.out` |
| zeros_like | `torch.ops.aten.zeros_like.default` | RuntimeError：`torch.ops.aten.zeros_like.out` |
| new_zeros | `torch.ops.aten.new_zeros.default` | RuntimeError：`torch.ops.aten.new_zeros.out` |
| ones | `torch.ops.aten.ones.default` | NotImplementedError：`torch.ops.aten.ones.names`†、`torch.ops.aten.ones.names_out`†、`torch.ops.aten.ones.out` |
| ones_like | `torch.ops.aten.ones_like.default` | RuntimeError：`torch.ops.aten.ones_like.out` |
| new_ones | `torch.ops.aten.new_ones.default` | RuntimeError：`torch.ops.aten.new_ones.out` |
| fill | `torch.ops.aten.fill.Scalar`、`torch.ops.aten.fill.Tensor` | RuntimeError：`torch.ops.aten.fill.Scalar_out`、`torch.ops.aten.fill.Tensor_out` |
| zero | `torch.ops.aten.zero.default` | NotImplementedError：`torch.ops.aten.zero.out` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/arange.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/arange.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/linspace.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/linspace.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/scalar_tensor.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/scalar_tensor.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/full.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/full.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/full_like.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/full_like.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_full.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_full.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/empty.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/empty.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/empty_like.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/empty_like.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty_strided.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_empty_strided.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros_like.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zeros_like.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_zeros.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_zeros.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ones.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ones.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ones_like.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ones_like.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/new_ones.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/new_ones.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/fill.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/fill.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/zero.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/zero.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
