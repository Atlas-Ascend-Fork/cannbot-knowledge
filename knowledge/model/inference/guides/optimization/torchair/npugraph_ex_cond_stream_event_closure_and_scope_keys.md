---
type: Guide
title: npugraph_ex流事件：前AOT降低、cond闭环与scope结构键
description: 保留图降低与cond闭环，补完整tag字典、dispatcher/Functionalize、record_stream和双版通信依赖边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_tagged_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_record_wait.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_tagged_event.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_record_wait.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_utils.py
  role: implementation
created_at: '2026-11-10T14:28:50Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# cond多流闭包：分支事件隔离与scope结构键

## 固定范围与实质补充

本卡只绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`中`npugraph_ex/npugraph_ex/`独立包，闭合cond分支多流的事件标记、图闭环、scope重绑定和Python运行消费者。它补充[多流文档](graph_multistream_dependencies.md)与[cond捕获合同](npugraph_ex_conditional_capture.md)，不把同仓集成TorchAir或发布版推成同一实现。整卡平台未知，保持draft、空平台；没有运行上游、图变换、生成代码、捕获或设备。

[cond编译门控](npugraph_ex_cond_compile_validation_and_unwrap.md)已解释wrapper/别名检查，[条件运行链](npugraph_ex_cond_dispatch_and_output_buffers.md)已解释双IF与统一输出缓冲；本卡只补跨GraphModule的事件和流scope消费者，任务更新协议仍按其独立卡消费。

## 前AOT降低与后续闭环是两个阶段

_compile_graph_with_aot发现cond时，按GraphModule后序树逐个运行replace_stream_event_pass、lint/recompile；没有cond保留root单图路线。这一前AOT树遍历使用通用子图迭代器，不能与后续只沿cond分支的local Pass遍历混为一套。

replace_stream_event_pass为当前GraphModule分配graph_N_前缀，并独立维护事件索引表、流栈和流信息。支持外部对象索引接口的分支，record_event/wait_event先通过本图事件表解析tag；索引不在本图时明确报错，提示record/wait必须在同一分支。这里的版本分支按接口是否存在判断，不只是比较版本字符串；本卡没有把所有旧式事件方法也当成通过同一索引检查。

set_stream在该Pass中改成scope_enter/exit栈；结束仍有未退出流则报错，不能凭代码里出现set_stream就认为捕获作用域完整。生成scope参数带图前缀label及可得的stream/device身份；默认流可保留专用标记，不能按捕获时固定整数把所有默认流语义复制到任意新进程。

## 每个分支独立构造fork/join

AclConcreteGraph优化时，apply_event_closure_with_multi_stream对root与每个cond分支分别运行。每次传入新的标签set、信息dict和事件列表；孩子图名追加分支路径，避免两分支相同placeholder/node名直接共用同一闭环tag。收集完再把信息合并到root的AclGraphCacheInfo，供后续统一重建。

有stream_id/device_index/device_type的信息按这三元组去重；闭环在首节点前record入口Event，再在所列用户流wait；输出前在这些流record出口Event，当前流wait。用户自定义Pass只提供label而没有stream_id时，另一分支在首次scope_enter后wait入口Event、最后scope_exit前record出口Event、图输出前wait它。

这些是让辅助流工作进入同一次捕获的首尾依赖，不会自动推导分支内部任意生产者/消费者的数据依赖。真实业务跨流顺序仍由用户Event等明确表达；tensor.record_stream是存储寿命记录，不代替这些record/wait。

函数只在既无stream_info、又无用户Pass流入口时直接跳过；最终返回的enabled布尔却只看stream_info是否非空。因此label-only路线也可能已经插入闭环而返回False，不以这个标志单独判定“没有任何多流图改写”。不完整身份信息和不配对scope也不是由该布尔值认证为合法。

## 为什么跨解包保存结构键

闭环先于输入mutation的函数化解包，解包可能替换branch GraphModule对象；仅保存id(branch_gm)会失去后续引用。cond_branch_scope_keys因此为root与按cond出现顺序的true/false分支生成root、root/0/true等位置键；裸cond读args，包装形式读kwargs中的true_fn/false_fn，并递归识别get_attr指向的分支。

闭环元数据先按这些键存储。完成其它Pass后，codegen在当前图重新计算`id(GraphModule)->结构键`，再把结构键查回为当前id索引。该查表没有静默空值fallback；也没有证明任意自定义Pass重排/删除cond后仍语义对应。它依赖前后结构位置保持所需对应，缺键要作为编译问题核对，不能任意删scope元数据绕过。

根图的key固定root，因此无cond时同一映射仍可用。结构位置是本次编译的桥梁，不是跨进程持久对象身份或全局唯一事件ID。

## 分支代码确实切流，而非只留下scope标记

根与分支代码生成在scope_enter对应位置发射`with torch.npu.stream(_GLOBAL_USER_TAG_TO_STREAM[label])`并缩进，scope_exit对应位置退缩进。分支生成器先复制本分支enter字典/exit列表，再逐项消费，避免同一分支被内联多次时第一次pop掉共享元数据，后续丢失切流上下文。

这只是所审生成文本的作用域机制，不是执行结果或全部嵌套流/异常退出均正确的证明。分支中真正切流、子图池与用户Event要求应与条件节点运行合同一起验收；不能把保留scope节点名当作已运行在正确流。

## 首调重建与实际record/wait

生成模块先定义用户tag到Stream字典及锁，首调按缓存的完整stream身份重新包装流，缺身份的label才创建新Stream；事件列表则在锁内逐tag新建Event并写入_GLOBAL_SCOPE_TAG_TO_EVENT。第一次kernel调用先把_is_first_run置False，再做事件/流重建和shape/stride断言，异常时不能依赖本生成函数自动重新进入同一初始化分支。

tagged_event_record/wait在新建Schema的分支注册side effect和CompositeExplicitAutograd消费者；created_inside=True从scope事件字典取对象，缺tag报错。普通版本对current_stream调用Event.record/wait，on_stream版本先重建指定身份的Stream再record/wait。Meta仅返回None，不执行真实同步。

首调重建会覆盖所列tag的Event对象；全局字典和局部锁不独自证明任意并发编译、多个生成模块或缓存复用都安全。Event/Stream存在、图里有record/wait或生成代码可解析，都不构成设备依赖正确或性能收益的运行证据。本次未执行首调、捕获、重放、通信或数据反序列化，未新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（primary）：定向范围231–240, 348–415, 546–562, 788–845, 937–954, 1088–1111, 1181–1188, 1250–1279。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（implementation）：定向范围572–767。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/cond_utils.py)（implementation）：定向范围264–280, 310–316, 348–356, 482–539。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：定向范围999–1034。
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py)（implementation）：定向范围12–112, 274–326, 329–349, 431–483。
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_tagged_event.py)（implementation）：定向范围31–132, 181–231, 251–275。

## 双版完整前AOT流与事件降低

已补完整主线483行与发布331行replace_stream_event.py，以及graph_pass的相应事件闭环/默认流解析定义。旧cond调用链和结构键证据保留；发布对照只指固定7c6c754快照，不把缺少主线分支直接解释成整个发布软件栈缺少能力。发布target写torch.ops.air，主线写torch.ops.npugraph_ex，不预设这两个命名空间始终别名。

GraphCounter.COUNT初始-1，graph_id每次先加1再生成graph_N_，set_graph_id可直接重设；本地没有锁或跨进程唯一性保证。每图事件索引表也不跨GraphModule共享。主线_event_tag对缺索引明确报错并附节点来源；发布直接查表。这个诊断说明所存降低前提，不在本组重证底层ModelRI/CANN协议。

_torch_high_version按两个Dynamo外部对象接口是否存在判定。_is_event识别Event构造器，也把legacy get_user_object_from_id调用直接认作事件；只有新外部对象接口路径另做isinstance(Event)。_is_stream对Stream构造器或新接口取得的Stream对象判定，不是任意用户对象均可靠识别。发布入口缺torch.npu或fake_record_stream时整Pass跳过；主线只在fake_record_stream分支局部hasattr，不能沿用发布的总跳过条件。

新接口record/wait可从外部流对象取身份；主线与捕获入口current_stream的stream_id相同就用当前流tagged操作，其余身份转字符串给on_stream；发布显式流路线直接传原身份值。比较点只是stream_id，不是这里完整比较所有设备字段。fake_record_stream转为按节点名record_tagged_stream_，主线另支持streams.record_stream，转换成显式身份的record_tagged_on_stream_；这些是存储寿命记录，不能代替事件先后。

旧式call_method的event.record/wait、stream.wait_event/wait_stream改写为对应tagged操作，显式流通过信息表转换；stream.record_event已有Event时重定向用户到原Event，无Event时按节点名新建tag。它们没有统一走新接口的事件索引缺失检查。原Event/Stream节点也不在本Pass统一删除或DCE。

## 流栈、身份和默认流marker的实际范围

_get_stream_info必须从example_value取得stream_id/device_index/device_type，缺Meta或属性报错；返回priority固定0，并非读取对象优先级。_get_stream_info_from_node要求已有信息表条目，入口stream_id相同则将三个字段换成DEFAULT标记，最终str返回；_build_scope_enter_args总写图前缀label和priority=0，仅对可得身份追加属性，缺表条目没有同一强制报错。

set_stream先用current_stream_map还原符号流；新流入栈时将该节点改scope_enter，切回栈中旧流时弹出较深作用域并插入scope_exit，切回入口流时全部弹出。后两条路线不是把每个原set_stream都统一替换掉；同栈顶无需弹出时也没有额外退出。不能解析的流报错，Pass结束仍有栈项也报错，成功只recompile，不另lint。

主线先识别CURRENT_STREAM_INDEX对应的外部入口流对象，再识别一般Stream；发布没有该专用分支。主线还把带_is_core_limit_scope_marker的3实参节点改为scope_enter：符号入口流用完整默认marker，显式流写稳定身份并清kwargs；参数个数不符或无法读身份会报错。完整控核消费者见[资源scope](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)。

## 两版闭环、record共享和解析位置

两版_create_event_by_name均在全局字典锁内按tag新建一次Event，本文件没有销毁该缓存。_extract_user_stream_info对身份int转换，不读priority，也没有先保证得到的dict含全部三个键。scope栈假定平衡，exit的pop没有通用空栈恢复。主线按_user_stream_label实际key位置取值；发布直接用args[1][0]。

主线显式身份去重和label-only首次入口/最后出口闭环按前文；发布遍历所有所收集stream入口/出口，入口后wait统一入口tag、出口前record各节点tag再于输出前wait，返回是否有入口。主线返回值只看身份信息非空，label-only改图仍可能False。两版均给scope加need_execute=True，不把闭环布尔当所有流已合法。

apply_event_record为wait依赖复用已有record节点，否则在相应依赖之后插一个record并缓存，让多个wait共享；这里只改图并lint，不创建所有真实硬件事件。默认marker解析仅作用于四个白名单tagged操作/scope_enter的直接位置字符串，不递归列表或kwargs；创建getattr读取stream_id/device_index/device_type后str的节点，源码注释的getitem不是实际发射。

发布每次所需解析会新插图入口current_stream；主线复用带is_default_current_stream标记的节点，缺少才插。这个复用只看元数据标记，不重新验证该节点target或位置；控核与事件因此可共享入口快照，但不是一般图不变量认证。两版缺torch.npu.current_stream均告警跳过解析。

## 完整本地源码证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（implementation）：1–1631；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py)（implementation）：1–483；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/graph_pass.py)（implementation）：1–1441；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/replace_stream_event.py)（implementation）：1–331；本地定义按主题分段落入本卡及关联卡，未将外部被调实现提升资格。

## 完整tag字典、dispatcher注册和record_stream消费者

完整审阅独立ops包两版_tagged_event.py、_utils.py、_record_wait.py、_lib.py及__init__.py，前文图降低与cond消费者继续按原来源范围保留。本组主线使用npugraph_ex FRAGMENT Library，发布使用air FRAGMENT；ops/__init__只导入_record_wait，并没有在此自动导入全部HCOM或tagged模块。注册均先查对应base op是否已存在，存在就跳过该组define/impl；不能由这份文件推断进程里既有同名dispatcher一定采用本实现。

_tagged_event必须能导入torch_npu，否则抛RuntimeError。按packaging.version解析torch版本：≥2.6选TaggedEventBidict，以id(event)作反向字典；较旧用TaggedEventFakeBidict逐项==查找。两个类都强持有正向Event；Bidict直接set同tag没有独立清除旧Event反向项，源码也没有通用delete接口。公开创建helper在锁内拒绝重复tag、构造Event并写表；该锁不意味着所有字典读写、多个生成模块或事件生命周期都由同一锁认证。

created_inside=False从这份用户tag双向字典查，True从graph_pass的_GLOBAL_SCOPE_TAG_TO_EVENT查，两者不是同一表。record/wait查不到Event会AssertionError，正常路线分别对current_stream调用Event.record/wait。对象形式的_npu_tagged_event_record/wait先反查tag；_get_tag_by_event缺项已先ValueError，后续None断言不构成另外的自动创建/修复路径。

on_stream record/wait把三身份字段转换成int、重新包装指定身份的Stream，再调用Event.record/wait；stream_wait_stream同样包装两份Stream后委托wait_stream。_resolve_stream_markers的实际实现只有int三转换，字面DEFAULT标记不会在此动态解析；必须由前文图Pass先改写成运行值。局部函数注释提及动态解析不改变这段实际代码，也不证明任意FX Node可被int成功转换。

普通record/wait、on_stream和stream_wait_stream在新注册分支标has_side_effect，Meta均返回None，运行消费者注册CompositeExplicitAutograd；Meta成功没有执行真实同步。record_tagged_stream的非下划线与Tensor(a!)下划线形式共用运行helper：从_scope_attr外部tag流表取/建Stream，取不到报错，随后直接input.record_stream(stream)，不clone输入。这里的存储使用记录与前文事件顺序不同；若先clone再记录，就记录到另一份Tensor存储，不能机械插复制替代原调用。

这一组仅为非下划线record_tagged_stream显式has_side_effect；两版下划线形式的Functionalize只调用非下划线形式，不做结果copy回写，Meta均None。主线另有显式身份record_tagged_on_stream/_两形式，两者都标side effect，同样直接record_stream、Functionalize委托非下划线，不补数据copy；两个Meta函数虽同Python名字，装饰器分别注册。这些是源码实际声明差别，不以名称或返回None独立认证所有功能化/别名行为。发布所存文件没有这项显式身份record_stream的新增分支，不外推完整发布栈缺少存储寿命处理。

## record/wait占位本身不实现硬件事件

_record_wait定义record(*,Device? device=None)->Tensor，BackendSelect返回该device的零长度empty，Meta返回meta设备零长度empty；本文件没有显式给record标has_side_effect。wait接Tensor列表且无输出，标side effect，但BackendSelect与Meta本体都只返回None。它们为图保留依赖表达，后续代码生成怎样消费要单独核对；不能说直接运行这些本体就已经完成Event同步。

没有执行导入注册、Event/Stream构造、Functionalize、record_stream或设备操作，所有外部Torch、_scope_attr、C++ allocator与运行库合同仍保留独立边界。

## 完整本地ops来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_tagged_event.py)（implementation）：1–316；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/__init__.py)（implementation）：1–1；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_lib.py)（implementation）：1–3；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_record_wait.py)（implementation）：1–31；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_utils.py)（implementation）：1–34；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_tagged_event.py)（implementation）：1–257；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/__init__.py)（implementation）：1–1；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_lib.py)（implementation）：1–3；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_record_wait.py)（implementation）：1–37；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_utils.py)（implementation）：1–34；仅完整本地定义与注册，外部被调实现另计。
