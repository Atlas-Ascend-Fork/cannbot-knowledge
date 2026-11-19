---
type: Guide
title: GERNG与Dropout：种子、重放和分布参数
description: 审阅11组随机与Dropout转换、图RNG账本及checkpoint映射，区分显式Generator、分布参数、mask和高阶绑定缺口。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rand.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rand.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randint.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randint.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randn.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randn.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randperm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randperm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/multinomial.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/multinomial.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bernoulli.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bernoulli.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/uniform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/uniform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_and_save_rng_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_and_save_rng_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_with_rng_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_with_rng_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T07:56:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GERNG与Dropout：种子、重放和分布参数

## 固定来源与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。完整审阅11组随机、Dropout与higher-order Converter，另读取两版RNG状态类/回调、GeGraph初始化及RNG方法、checkpoint映射函数的准确范围；其余大文件不据此宣称全文完成。Converter中9组AST相同，2组仅named overload兼容声明不同；辅助实现分别按本版核对。

平台矩阵未知，保持draft和空平台。未执行上游、随机数生成、GE编译、NPU精度/分布/性能或重放实验；declare_supported只是候选输入。stateless名字、相同seed、保存了两个值，都不能独立认证Eager/GE序列一致、完整概率分布、跨进程缓存或捕获重放安全。

## 图RNG状态：构图种子与调用时offset分开

_GraphRngState初始化时把所选Generator.initial_seed()构造为INT64 Const；offset使用CPU放置的Data输入，并建立一个随随机节点数量扩展的Unpack。next(philox_num)返回该种子与对应offset输出，记录每个节点的相对offset，累计量按int((philox_num+3)/4)*4推进。

本组各随机checkpoint辅助都请求philox_num=10，因此这层账本每个此类节点增加12；这是**offset预留规则**，不是已测出的每个kernel实际随机数消耗量或任意shape下无重叠的证明。输入回调_RngStatusInput.__call__调用consume：读取Generator当前offset，向前推进本图累计量，再返回相对offset列表加上起点。其codegen只生成插入None占位的字符串，导出/缓存执行仍需外围正确恢复输入，不据此认证可移植重放。

种子在图状态创建时成为Const，consume只读取offset，不在这里重新取initial_seed；更换种子、设备或Generator后是否重建/更新图必须单独核对。未显式Generator时，已导入torch_npu的路径取当前设备的默认Generator；另一分支为来源ST测试调用torch.manual_seed(10)并取默认Generator，不当作CPU产品可用性声明，本任务未执行它。

还有一个参数透传缺口：GeGraph用defaultdict(map_graph_rng_state)，再以传入gen作为字典key查询；defaultdict的factory调用不传key，所示map_graph_rng_state()因而以None创建状态。虽然_GraphRngState构造函数支持显式gen，**当前所示惰性创建路径并没有把那个key透传进去**。两快照python/torchair范围的静态检索未找到这份字典的其他填充调用；不能仅凭公开签名就认证多个显式Generator独立生效，需对真实运行上下文验证。

## 普通Converter与checkpoint支持范围不同

rand.default、randint.default、randperm.default分别调用对应checkpoint辅助，丢弃返回的(seed,offset)，只取随机结果；rand.generator、randint.generator、randperm.generator却都是直接拒绝壳。辅助函数有generator形参不等于这些公开准确重载已支持。

randn.default和randn.generator两者都有构图分支；uniform、bernoulli与multinomial的所列普通入口也会把generator转交各辅助，但仍受上面的图状态创建缺口约束。checkpoint映射是另一张独立表：仅登记指定对象；若传OpOverloadPacket给登记器，会展开该packet当前overloads，重复登记拒绝，查找缺项也明确RuntimeError，不是未登记随机算子自动回退。

## 随机分布、dtype与未使用的参数

| 家族 | 此固定实现的构图合同与缺口 |
| --- | --- |
| rand、randn | 新状态来自图RNG，已有rng_state则Unpack(num=2,axis=0)。seed转UINT64并Unsqueeze作为key，构造[0,offset]再转UINT64作为counter，alg=INT32的1；分别调用StatelessRandomUniformV2/StatelessRandomNormalV2。显式dtype映射，否则从Meta（序列取最后项）选输出类型，不认证任意状态shape/dtype或所有分布精度。 |
| randint.default | 拒绝GE Tensor形式size，非Tensor high<=0时拒绝；实际以FP32 Uniform×high，再经INT64及目标dtype转换。映射前若原始dtype等于DT_UINT8会直接返回INT64 Cast；这个比较发生在类型域转换之前，不可按符号名翻译成“所有PyTorch uint8均返回INT64”，默认签名4与torch.dtype实参需分别核对。映射后BOOL分支以Python high==0选择全0/1 Fill，不是逐元素Uniform比较；Tensor high及大范围整数分布不由此认证。准确low重载仍直接拒绝。 |
| randperm.default | 非Tensor n<=0就拒绝，包括0；StatelessRandperm的layout被固定为1，输出dtype取Meta，公开dtype/layout参数没有作为同名属性独立转交。不从接口名字推导空排列或任意布局已实现。 |
| multinomial.default | 仅接受rank为1或2；实际总调用MultinomialWithReplacement(...,numsamples=num_samples)，replacement参数未参与分支或GE属性。不能将签名默认replacement=False当成无放回算法已实现，也未在此层完整验证概率值或样本数。 |
| bernoulli.default、p、Tensor | default将self同时作为形状来源及概率p，另两个入口分别传标量/GE Tensor p；StatelessBernoulli输出dtype取self.dtype。没有在此函数完整检查所有p范围、广播及Meta规格。 |
| uniform.default | 生成self.dtype的Uniform；from_/to在math.isclose的指定判断下视为0/1时直接返回，否则构造u*to-(u*from_-from_)。端点先按self.dtype转换，实数代数上相当于区间仿射变化不代表浮点舍入/全部区间校验已通过；未在本层检查所有from/to关系。 |

部分device、layout、pin_memory参数虽在签名里，未驱动这些函数中的完整设备/布局路径；不能由候选声明device='npu'直接认证所有产品和组合。上述分布参数缺口需先解决或验证，再讨论随机算子融合带来的实际吞吐收益。

## Dropout训练、推理与反向mask不可混用

native_dropout_checkpoint把train=None或True视为训练路径：prob=1-p并按输入dtype处理，取RNG seed/offset，seed1固定0，构造[0,offset]，StatelessDropOutGenMask后DropOutDoMask，返回真实训练mask及RNG对。p=0/1在此函数没有独立快捷/边界分支，不由Python代码存在认证全部极值合法。

train=False则不消费RNG，返回(None,None)状态对、原输入Tensor对象以及Shape(input)的BOOL全1 Fill mask。它与训练mask的生成形式、dtype/shape不能混为同一ABI；来源也明确因mask与CPU不同而未提供通用testcase。CPU bool mask与设备训练mask是否可互换，需要对应IR/设备合同，不能由数值全1单独认证。

native_dropout_backward.default先算retain=1.0/scale，再DropOutDoMask(grad_output,mask,retain)；不是把scale原样传给第三参数，scale=0也没有此层特判。前反向需核对mask来源与保留概率关系，本次没有执行验证。

## higher-order保存/重放有静态绑定缺口

run_and_save_rng_state按op取checkpoint辅助，拿到seed/offset后直接ConcatV2返回(rng_state,result)；run_with_rng_state用传入rng_state调用辅助并只返回结果。这个状态是本实现的(seed,offset)构图对，不能当作完整框架RNG字节状态或任意后端通用快照。

两份wrapper只从converter_utils通配导入，却调用get_checkpoint_func；所审阅完整converter_utils只导入register_checkpoint_func等，没有绑定get_checkpoint_func。两版对应源码及静态调用检索都显示此名称解析缺口，不能因注册函数确实存在就声称wrapper可直接运行。当前未执行，外部注入若存在仍需独立证据，不能用猜测补齐。

即使补齐名称绑定，保存包装器也没有为native_dropout train=False返回的(None,None)状态对做特判，而是继续Concat；这条组合路径同样不能仅靠helper签名认证。固定输入、dtype与seed仍不足以证明checkpoint重算、评估态及缓存加载后序列一致。

## 优化与验收

先核对普通/高阶准确overload、generator实际指向、图创建时seed、调用时offset输入及保存状态形状，再验证replacement、整型生成范围、Dropout train/p及mask和反向scale。覆盖多次调用、显式多Generator、重建图、训练/评估切换、checkpoint重算与真实分布，再测优化前后性能。当前只记录静态证据和明确缺口，未将候选代码视为精度、可复现性或性能已验证。

一般构图方法见[Converter开发](torchair_converter_implementation.md)，初始化生成精度见[GE创建与初始化](torchair_ge_factory_lowering.md)。

## checkpoint专用注册映射

这是源码明确登记的映射，普通Converter注册与此映射分开；登记成功也不等于保存/重放已运行验证。

| checkpoint辅助函数 | 明确登记的准确对象 |
| --- | --- |
| rand_checkpoint | `torch.ops.aten.rand.default` |
| randint_checkpoint | `torch.ops.aten.randint.default` |
| randn_checkpoint | `torch.ops.aten.randn.default`、`torch.ops.aten.randn.generator` |
| randperm_checkpoint | `torch.ops.aten.randperm.default` |
| multinomial_default_checkpoint | `torch.ops.aten.multinomial.default` |
| bernoulli_checkpoint | `torch.ops.aten.bernoulli.default`、`torch.ops.aten.bernoulli.p`、`torch.ops.aten.bernoulli.Tensor` |
| _uniform_checkpoint | `torch.ops.aten.uniform.default` |
| native_dropout_checkpoint | `torch.ops.aten.native_dropout.default` |

## 准确Converter入口及直接拒绝边界

主线†表示getattr(...,None)兼容声明，目标缺失时不建立有效Converter；发布快照相应named声明为直接属性。higher-order两行还受正文名称绑定缺口限制，“有构图分支”不是已能运行。直接拒绝仅指实际选中此内置Converter，不扩大到高层函数、其他overload或后端。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| rand | `torch.ops.aten.rand.default` | RuntimeError：`torch.ops.aten.rand.generator`、`torch.ops.aten.rand.names`†、`torch.ops.aten.rand.generator_with_names`†、`torch.ops.aten.rand.out`、`torch.ops.aten.rand.generator_out`、`torch.ops.aten.rand.names_out`†、`torch.ops.aten.rand.generator_with_names_out`† |
| randint | `torch.ops.aten.randint.default` | RuntimeError：`torch.ops.aten.randint.generator`、`torch.ops.aten.randint.low`、`torch.ops.aten.randint.low_generator`、`torch.ops.aten.randint.out`、`torch.ops.aten.randint.generator_out`、`torch.ops.aten.randint.low_out`、`torch.ops.aten.randint.low_generator_out` |
| randn | `torch.ops.aten.randn.default`、`torch.ops.aten.randn.generator` | RuntimeError：`torch.ops.aten.randn.names`†、`torch.ops.aten.randn.generator_with_names`†、`torch.ops.aten.randn.out`、`torch.ops.aten.randn.generator_out`、`torch.ops.aten.randn.names_out`†、`torch.ops.aten.randn.generator_with_names_out`† |
| randperm | `torch.ops.aten.randperm.default` | NotImplementedError：`torch.ops.aten.randperm.generator`、`torch.ops.aten.randperm.out`、`torch.ops.aten.randperm.generator_out` |
| multinomial | `torch.ops.aten.multinomial.default` | NotImplementedError：`torch.ops.aten.multinomial.out` |
| bernoulli | `torch.ops.aten.bernoulli.default`、`torch.ops.aten.bernoulli.p`、`torch.ops.aten.bernoulli.Tensor` | RuntimeError：`torch.ops.aten.bernoulli.out`、`torch.ops.aten.bernoulli.Tensor_out`、`torch.ops.aten.bernoulli.float_out` |
| uniform | `torch.ops.aten.uniform.default` | NotImplementedError：`torch.ops.aten.uniform.out` |
| native_dropout | `torch.ops.aten.native_dropout.default` | NotImplementedError：`torch.ops.aten.native_dropout.out` |
| native_dropout_backward | `torch.ops.aten.native_dropout_backward.default` | NotImplementedError：`torch.ops.aten.native_dropout_backward.out` |
| run_and_save_rng_state | `torch.ops.higher_order.run_and_save_rng_state` | 无无条件拒绝壳；仍有正文参数/绑定边界 |
| run_with_rng_state | `torch.ops.higher_order.run_with_rng_state` | 无无条件拒绝壳；仍有正文参数/绑定边界 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rand.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rand.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randint.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randint.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randn.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randn.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/randperm.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/randperm.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/multinomial.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/multinomial.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bernoulli.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bernoulli.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/uniform.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/uniform.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout_backward.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_dropout_backward.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_and_save_rng_state.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_and_save_rng_state.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_with_rng_state.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/run_with_rng_state.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
