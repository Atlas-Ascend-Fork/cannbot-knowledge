---
type: Guide
title: FX容器元数据：ValuePack配对与符号列表
description: 核对两版FX解释器的Meta/NPU值配对、字典取项、递归解包及符号列表条件，区分元数据计算和实际执行。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_concrete_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_concrete_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/_concrete_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/_concrete_graph.py
  role: implementation
created_at: '2026-11-10T10:21:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FX容器元数据：ValuePack配对与符号列表

## 固定快照与使用范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的core/_concrete_graph.py和npu_fx_compiler.py。本卡解释FX解释器如何成对传递Meta与NPU图值，产品矩阵未知，保持draft与空平台；未导入、执行上游或运行设备用例。

容器可以通过某个Python分支，不代表所有嵌套输出都被具体GE/ACL算子、导出和执行器支持；抽象接口也不构成后端能力证明。编译模式、优化次序和AOT见[编译管线](torchair_fx_compiler_pipeline.md)。

## ValuePack保留两路值，主线字典取项更严格

ValuePack(meta,npu_meta=None)保存meta与npu_meta；后者为None时直接使用meta，不复制或计算设备结果。meta/npu属性原样暴露保存值，__repr__对FakeTensor、Tensor、SymInt作日志格式化，不转换dtype或分配输出。

主线ValuePack.__getitem__只处理Mapping：要求npu也是Mapping，以meta[key]取值并检查NPU键存在，再返回ValuePack(meta_value,npu_value)。缺少Meta键会先触发取项异常；缺NPU键则显式AssertionError。发布版只对dict使用meta.get(key)，直接返回Meta值，缺键可返回None，未将两路结果重新配对。两版不能共用“字典取项总能保留NPU图值”的结论。

主线_NpuGraphConverter._get_value_pack要求Mapping两路同时出现，长度和key集合相同，再按Meta键顺序重排NPU字典，形成一个包住整个Mapping的ValuePack。发布版没有相同Mapping检查。两版对list/tuple均递归zip配对，此分支未显式检查两路长度；不能据zip本身宣称长度不一致会被拒绝。

## Meta解包与NPU解包具有不同容器合同

主线_unpack_meta递归解开ValuePack.meta，保留tuple/list类别，Mapping转普通dict并递归其值；位置参数最外层仍返回list。发布版主要处理直接ValuePack及一层list/tuple或dict，不具备相同的任意深度递归。

主线_unpack_npu递归ValuePack.npu；非空tuple/list若满足_is_symlist则交parse_symlist，否则一律归一成list，以保持既有Converter ABI。空tuple/list直接保留，Mapping转dict并递归。Meta侧保留tuple而NPU侧非空tuple变list，是有意保留的两路差别，不能要求中间容器类型总一致。

发布版的解包与符号列表识别较浅，不能把主线的Mapping递归、容器对齐校验直接回填为发布能力。需要逐层检查FX输入、Meta计算结果、具体图parse_node结果和最终输出结构。

## 符号列表：有ValuePack不等于存在动态尺寸

主线_is_symlist要求非空list/tuple，所有元素要么是普通int，要么是meta为int或torch.SymInt的ValuePack，并且至少存在一个ValuePack。普通int列表返回False；包住int的ValuePack也满足has_symbol，因此True不等于列表一定含真正动态SymInt。

发布版只要发现一个meta为int/SymInt的ValuePack便可返回True，没有主线的全部元素类型约束；混合非数值元素可能在两版走不同路径。此处只是分派条件，不自动证明parse_symlist后续接受全部表达式或动态范围。

## FX节点的Meta计算与图构造分开

run在graph.context中解释FX并返回graph；每个run_node进入converter_context(node=...)。placeholder先由FX解释器取得Meta输入，再经graph.parse_input构造NPU值，打包成ValuePack。

call_function/call_method/call_module共用_wrap：部分builtin直接由FX解释器处理；列入_binary_operator的加减乘除、整除、幂、floor/ceil、mod和neg进入Converter路线。主线额外把operator.getitem列为直接求值，避免非OpOverload目标被送入不匹配的Converter流程，发布版没有该显式特例。

其余目标先解包Meta，在FakeTensor模式中计算meta_outputs，再解包NPU参数调用graph.parse_node，最后重新配对。主线detect_fake_mode(None)为None时新建FakeTensorMode(allow_non_fake_inputs=True)；发布版没有这个回退。Meta求值不是实际NPU执行，也不是数值正确性验证。

主线_record_asc_ir打开时在parse_node前记录GE算子数量，之后重置；该局部重置没有finally保护，异常恢复不能仅由正常路径推导。output先解包Meta，源码调用super().placeholder取得meta_output，再把原始参数交parse_output；这里只记录实际调用，未运行例子，不将其推断为已复现错误。

## 抽象图合同与验证边界

ConcreteGraphBase仅声明context、parse_input、parse_output、parse_symlist、parse_node、dump、compile和__call__等抽象方法；它们的pass不能证明任一具体后端已实现某类输出。具体输入布局、符号绑定、内存复用、dtype与设备支持仍须追到相应实现。

验证新容器时分别检查两路key集合、键顺序、list/tuple长度、空容器、嵌套ValuePack、纯int列表和混合符号列表，并在匹配软件栈独立做执行与精度实验。本次只完成静态源码和版本差异核对，没有运行这些实验。

- [GE元数据占位与符号hint](torchair_ge_metadata_support_helpers.md)
- [Converter注册与Prims层次](torchair_ge_registration_prims_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_concrete_graph.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_concrete_graph.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）

## 独立ACL消费者的输入、符号与输出合同

本节补独立npugraph_ex的fx2acl_converter实际消费者，固定双版与前文相同；这个包导入自己的npugraph_ex.core._concrete_graph.ValuePack和acl_graph.is_sym，不把它与python/torchair命名空间中的类身份混同。只覆盖所列解析和生成段，整份转换器仍保留未覆盖内容。

parse_symlist遇本包ValuePack便取.npu；其他项只接受isinstance(...,int)，因此普通bool也满足该Python判据。取出的.npu没有在这里再次强制转int；all项是int时直接返回，否则也只是记日志后返回。它不是“任何ValuePack都已验证为合法动态整数列表”的检查器，后续表达式和实际算子仍各自核对。

parse_input将所有placeholder的meta顺序追加到_meta_inputs，也记录所有输入名；Tensor的参数/普通输入分类仍按[输入缓冲指南](npugraph_ex_replay_input_buffers_and_copy_paths.md)。另外，符号输入按meta.node.expr→位置存入_all_sym_input_idx，同一表达式再次出现会覆盖该键的位置，而非保留所有同表达式占位符。主线只把Tensor登记到_all_meta_tensor_input，普通非Tensor且未被is_sym识别的值只记日志后返回；发布则把所有非Sym值放进这张表，没有相同Tensor筛选。

这个版本差异有实际消费者：生成断言时会直接对表项调用numel/shape/stride，输出别名收集也把表项交torch._C._is_alias_of。因此发布若有普通标量等非Tensor表项，存在在这些消费者先失败的静态路径；不能由前面的parse_input已返回就认定已支持所有常量占位符。主线的筛选也只解决这张表的类别问题，不认证任意输入、符号、布局或下游执行。

parse_node函数体直接调用target(*args,**kwargs)并返回，不在这里建立通用算子替换或能力表。parse_output只验证最外层args为list/tuple且长度1，再直接遍历args[0]；没有在本函数递归展开任意输出树。每项缺meta或meta为None就跳过，有meta则与_all_meta_tensor_input中的项逐个做_is_alias_of，记录输入index→输出index列表。它没有再按parameter类别过滤输入，也没有先要求输出meta一定是Tensor；这个收集动作不是对所有嵌套结果和元数据类型都成立的通用别名证明。

## 生成的首调检查不能代替逐次运行合同

两版_codegen_input只在存在符号输入记录时生成按全部FX输入名从args解包的语句，单输入保留尾逗号；随后仅为sympy.Symbol生成名称绑定，数字或复合表达式不在此单独赋值。它没有为每个任意表达式建立求解器，也不在该段从kwargs补绑定。

_codegen_assert_size_stride按_all_meta_tensor_input逐项生成assert_size_stride(args[idx],shape,stride)，numel为0的项跳过。_codegen_kernel把这些语句放在_is_first_run分支中，和可选事件/流表更新一起执行；后续再调用acl_graph。这里的形状/步幅检查不是每个graph key、每次replay的完整输入验证，也没有本地覆盖全部dtype、device、值或业务条件。

首调flag在解包、可选更新和断言之前已置False，本函数没有异常时恢复True的逻辑；这点与[流事件首调恢复](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)的既有边界一致，不把重复调用当成自动重做全部首调检查。需要分别确认外层Guards、这些生成语句和实际捕获/回放合同；只读生成字符串，没有执行target、alias检查、断言或设备用例，也没有新增verified。

## 有界独立ACL实现证据

- [固定消费者 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：21–27、590–706、826–874；仅此处局部函数/生成字符串和导入，不提升整个转换器或外部被调实现资格。
- [固定消费者 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：18–24、379–487、594–639；仅此处局部函数/生成字符串和导入，不提升整个转换器或外部被调实现资格。

## 独立包ValuePack仍采用宽松的字典与符号列表路线

本节补独立npugraph_ex/core/_concrete_graph.py的完整双版本地定义，承接前节独立ACL消费者。主线该文件102行、发布116行；前文主线Mapping配对严校来自集成python/torchair，不适用于这里的同名类。

独立包两版ValuePack都直接保存meta/npu_meta，npu_meta为None时用meta作后备；meta/npu属性直接返回这些对象。__getitem__仅接受meta为dict，调用meta.get(key)并返回Meta值，缺键可得None，不按NPU字典检查键，也不把结果重新封成两路ValuePack。其他Mapping不能仅因集成主线已接受就推定此处同样接受。

两版__repr__按FakeTensor、Tensor、SymInt格式化日志，其余尝试类型名和值的字符串表示，异常后只用类型名；没有由这个展示函数推导布局转换、分配或设备执行。构造、属性读取与展示成功均不能替代具体消费者的dtype/shape/device合同。

两版本地_is_sym识别torch.SymInt、SymFloat和SymBool；_is_symlist却只要求非空list/tuple里有任意一个本包ValuePack，其meta满足int或SymInt的isinstance条件，就立即True。它不检查其余元素，纯普通整数列表为False，包住普通int的ValuePack可使它为True；True不表示确有动态尺寸，也不证明每项均可被后面的parse_symlist消费。主线独立包在此仍与发布保持同一宽松条件，不能搬用集成主线“所有元素均满足条件”的约束。

独立ConcreteGraphBase两版均以抽象方法声明context、parse_input、parse_output、parse_symlist、parse_node和__call__；发布另有dump、compile两个抽象方法，主线已移除这两项抽象声明。这是基类接口面差异，pass本身不执行构图/编译，也不能据主线没有该抽象声明推断所有具体实现没有dump或compile。

完整文件资格只到这两个本地模块。集成包及先前独立ACL消费者按各自既有证据保留，外部PyTorch类型、日志表示或模型输入仍须单独核对；没有导入这些类、构造ValuePack、运行符号判断或设备测试，也没有新增verified。

## 完整独立元数据源码证据

- [固定模块 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/_concrete_graph.py)（implementation）：1–102；完整本地定义，其他包及外部被调实现另计。
- [固定模块 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/core/_concrete_graph.py)（implementation）：1–116；完整本地定义，其他包及外部被调实现另计。
