---
type: Guide
title: 独立npugraph_ex回放输入：固定缓冲与地址变更复制
description: 核对capture时连续缓冲、参数和别名输入分类、逐次copy及storage基址比较，解释clone_input为何不是每步新建一套克隆。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T12:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex回放输入：固定缓冲与地址变更复制

## 固定实现与范围

本卡定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中的独立npugraph_ex包，覆盖输入分类、capture缓冲和process_input。它不是同仓python/torchair下的legacy实现；发布版和外部安装组合仍独立核对。

只有静态源码证据，没有导入、编译、执行捕获/回放、修改设备输入或测量搬运收益；整卡平台未知，保持draft与空平台。公共开关语义见[内存池与clone](npugraph_ex_memory_pool_and_clone.md)，graph key与重捕获见[恢复后的捕获键](npugraph_ex_restored_capture_keys_and_first_call.md)。

## 先看输入落入哪张表

fx2acl_converter.parse_input只给Tensor输入分类：有_dynamo_static_input_type或_torchair_is_parameter属性，或本身是Parameter时进入parameter_user_inputs；否则进入user_inputs_mapping。这里对两个属性检查hasattr，不是检查值是否为True；不能自行增加同名私有属性并只凭值为False断言仍走普通用户输入路径。

capture遍历user_inputs_mapping，但跳过mutated输入以及与输出引用关联的输入。因此clone_input处理的不是所有args，参数、静态标记、原地更新和输入输出别名须各自跟踪；不把改变公共开关理解为替换全部权重或KV存储的机制。

## clone_input在capture建立固定缓冲

普通NPU用户Tensor在clone_input=True时被empty_like(...,memory_format=contiguous_format)替换后参与capture，用以记录新的固定地址；同时记录metadata并构造userinputs_metatensor。它不是在每次回放时都新建同样的一套clone。capture之后可清掉retained_userinputs，后续process_input使用已登记的metadata Tensor作为复制目标。

empty_like创建缓冲而不复制原值；普通调用在compile/capture后先process_input，再replay，才返回重建结果。不能把capture期间的临时输出直接当成本次用户值已得到正确处理的证据。原输入的非连续布局和图里固定的view/stride合同还需验证，不能因目标缓冲连续就推导任意布局变更都合法。

## 每次输入复制的条件

| 输入路径 | process_input的复制判据与目标 |
| --- | --- |
| clone_input=True的普通用户输入 | 不比较data_ptr，每次加入copy列表，目标为已登记userinputs_metatensor。 |
| clone_input=False的普通用户输入 | metadata.data_ptr与本次Tensor.data_ptr不同才复制；目标为capture保留的原用户输入。 |
| 与输出引用关联的输入 | 独立比较记录的_userinput_ref_data_ptr；改变时复制到当前key保留的捕获输入，不因clone_input开关关闭而取消这个分支。 |
| 参数/静态标记或mutated输入 | 不在上述普通输入缓冲表中；地址key或重捕获前提按独立协议检查。 |

clone_input=True时reconstructed_inputs直接引用userinputs_metatensor，随后update(captured_userinput_ref_with_output)会原地把已有alias条目并入该字典，并按输入索引覆盖已有键。因此后续同key、未重新capture的调用中，alias也可能进入前面的无条件copy遍历；独立地址分支再命中时，还可能重复追加同一目标。不能把表中alias类别理解为始终只按独立地址分支处理，也不能用没有别名的用例估算全部copy次数；这里仅记录静态状态变化，没有测量实际复制开销。

clone_input=False因而不是“所有输入都免copy”：换对象/存储后仍可能写回capture时持有的旧输入，外部保留该对象或其别名会观察到相关存储变化。保持地址不变有助于避开此处部分copy判据，但不放宽shape、dtype、stride和数据依赖合同。

## 比较用的两种地址不能混为一谈

get_tensor_metadata保存的是untyped_storage().data_ptr及独立storage_offset，而普通非clone分支用replay_arg.data_ptr比较。非零storage_offset下，storage基址与Tensor逻辑起始地址可以不同；因此即使重用同一个Python Tensor，也不能只凭对象身份推断该分支会省去copy。

这个观察仅定位固定源码的免拷贝判据，不是本次设备性能复现，也不证明所有同storage视图都可互换。诊断时同时保存两个地址、offset、shape、stride及原捕获对象的存活引用。

## 批量copy路线的判断会缓存

copy列表多于一项时，首次检查源和目标列表是否均为base format，并把布尔结果存入实例的_input_base_format；为True用torch._foreach_copy_(...,non_blocking=True)，否则逐项copy_。仅一项时直接copy_，零项时不发起该列表复制。

_input_base_format不是每次重新判断，也不是按graph key单独保存的字段；不能因换key便假定所有格式条件已重新检查。non_blocking参数只出现在这条foreach调用，不独立保证任意源位置/存储组合的复制完全异步或可与实际replay重叠。应按真实输入合同与设备时间线对照，不以调用名推断收益。

## 测量完整的输入到结果路径

独立AclGraph.__call__先compile选择key，再process_input、run/replay，最后reconstruct_outputs。输入缓冲复用省去了某些分配，不自动省去逐次复制、元数据、动态图参数更新或输出处理。

run还明确检查该key的replay_func是否为None：捕获未成功时抛出针对前次capture失败的错误，而不是把字典中已有key当作可回放证明。这与输入数据已复制成功是两项独立验收。

对照clone输入策略时分别记录捕获缓冲地址、copy项数/字节数、base-format路线、参数/别名/原地更新输入，以及[输出重建成本](npugraph_ex_output_reconstruction_and_storage_lifetime.md)。本卡没有新增verified或性能数值。

## Evidence

- [独立输入捕获与处理](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：1072–1094、1458–1460、1492–1542、1638–1721。
- [输入分类](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：614–641。
- [metadata与地址重建](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：88–177、252–256。

## 发布输入开关与跨key地址基准

本节只补固定发布7c6c754的对应输入捕获、copy和别名登记块；原主线分类器与外部安装组合的范围仍按前文，不把整份1597行模块提升为已覆盖。

发布capture、capture完成后的retained_userinputs.clear以及process_input三个位置，都以config.get('clone_input', '1') == '1'判定。主线对应位置按config.get('clone_input', True)的真值判定。这里消费的是内部配置字典：直接把主线的Python True放入发布字典，并不等于字符串'1'；反过来非空字符串'0'在主线真值判断也不是False。它不是公开配置入口接受这些混合类型的承诺，必须连同各自序列化消费者核对，不能只迁移同名键。

所列发布输入消费者同样跳过mutated输入和输入引用输出，NPU普通输入在启用clone时先用连续empty_like登记固定地址。process_input仍是clone路线无条件排copy、非clone路线比较metadata的Storage基址与本次Tensor.data_ptr，别名再独立比较地址；多项copy的base-format结果仍缓存于实例，foreach分支才显式传non_blocking=True。前文“关闭clone不等于免copy”和别名update会改变同一输入字典的说明，在这些发布块也成立；没有执行异步拷贝或设备结果验证。

两版compile_for_graph_key对别名输入做两类登记：每key的captured_userinput_ref_with_output保留该次对象，而实例级_userinput_ref_data_ptr用setdefault按输入index保存首次登记地址。后续key或同key重捕获不会仅靠这条语句覆盖已有基准，process_input却仍用这个实例级地址作比较；它不是每key单独更新的地址快照。诊断应同时记录基准地址、本key捕获对象和本次输入，不能由“本次地址等于本key对象”直接断言别名copy分支不发生。这是局部静态状态边界，没有据此复现或认证所有多key别名组合。

## 有界版本对照来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：1397–1403、1458–1460、1492–1542、1638–1707；仅支持本节新增局部合同，不提升整模块或外部被调实现资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：1089–1093、1125–1127、1134–1175、1258–1327；仅支持本节新增局部合同，不提升整模块或外部被调实现资格。
