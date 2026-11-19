---
type: Guide
title: npugraph_ex动态任务更新规则与图key分工
description: 核对Attention/ATB更新白名单、placeholder规则与cond索引，区分参数刷新和未更新符号进入捕获key。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T13:12:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npugraph_ex动态任务更新规则与图key分工

## 固定入口与版本

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中独立npugraph_ex包的任务更新白名单、参数规则、符号输入分类与cond分支收集。发布快照也有同名模块，本卡未将主线cond和更新规则回推为发布合同；也不混用python/torchair旧执行器或GE tiling_schedule_optimize。未运行上游、生成代码、设备或反序列化缓存/模型，保持draft与空平台。

fx2acl_converter在图优化后先计算unupdated_sym_input_index，再收集ops_update_rulers/updated_ops_param，另递归收集cond分支。AclGraph首次编译建立graph key函数和updated-input函数；前者选捕获图，后者在Replay时重建允许更新的参数。这里不是所有变化都靠重新捕获，也不是所有动态参数都能脱离key。捕获键已有条件见[捕获键与首调](npugraph_ex_restored_capture_keys_and_first_call.md)。

## 白名单由实际算子及schema决定

_REPLACE_FUNC_MAP在模块加载时按算子存在性填入：

| 原始算子/协议 | 可更新参数 | 输出/workspace处理 |
| --- | --- | --- |
| npu_fused_infer_attention_score | actual_seq_lengths、actual_seq_lengths_kv、actual_shared_prefix_len | 最大workspace helper与out重载，两个输出 |
| npu_fused_infer_attention_score_v2 | actual_seq_qlen、actual_seq_kvlen | 对应最大workspace helper与out重载，两个输出 |
| atb._npu_paged_attention | 位置7的context_lens | 原算子直接作为更新目标，不额外构造输出/workspace |
| atb._npu_paged_attention_splitfuse | 位置4的context_lens、位置6的seq_len | 同上 |

ATB两项还要求从算子signature枚举得到的参数名/位置与预设一致；不一致只警告且不加入该map。这里不是所有Attention、任意同名算子、任意版本schema或量化参数的通用更新协议。算子存在也不替代产品、shape、dtype及底层task-update能力核验。

## 可重建列表与直接placeholder

get_update_ruler仅查看白名单kwargs，要求其值为list/tuple；每个元素必须是当前图的直接placeholder，或int/float/bool常量。至少含一个placeholder才记录该参数；纯常量列表不会新建更新项。任意FX运算节点、嵌套表达式或其他元素类型不在这里求值，而会报错。位置参数仅在预设位置且实参本身是placeholder时建立单项索引规则。

运行期函数根据规则从本次args取索引值、混入固定值，生成每算子的参数字典；相同str(规则)签名复用一次构造结果。它不是读取所有Tensor内容或求任意Python表达式，也不是完整捕获缓存身份。常量变化、非白名单参数、dtype/地址/shape变化仍要由各自FX guard、图key和重捕获逻辑约束。

根图placeholder数量须与记录的meta_inputs数量一致。cond分支用位置映射转为根图runtime args索引，并给节点名加累计分支前缀；根收集函数只扫本GraphModule，fx2acl另外遍历两分支并合并规则。若某条更新规则依赖的分支placeholder不能映射到根输入，_remap_branch_update_rulers实际抛RuntimeError，不是静默跳过后保证仍更新。所读函数部分注释称drop，不能据注释覆盖这个消费者行为。

## 哪些符号仍进入graph key

get_unupdated_sym_input_index扫描含符号Meta的placeholder。一个直接用户不在更新目标map内，或当前符号还出现在该用户的非更新参数里，就把它视为未更新用户：符号标量保留其输入值到key；Tensor的符号shape若能映射独立符号输入则用该输入值，否则记录该Tensor shape。无用户或只出现在允许更新参数中的输入可不加入这一符号key部分。

当前get_node_all_placeholder_inputs检查参数与嵌套list/tuple/dict里的直接placeholder，没有沿任意非placeholder FX表达式继续反向遍历；不能把函数名字解释为完整依赖分析。符号算术节点本身若作为直接用户且不在白名单，也会触发保留key的路线。相关Meta形态/容器和上游图结构仍需按准确输入核对。

对成功解析的cond，只有两个分支中该operand的所有相应用户都符合更新资格，才允许这项用户不阻止符号离开key；嵌套cond继续递归，不确定时保守返回False。若其中一支有普通shape计算、未支持用户或参数使用，符号仍参与捕获图选择。本卡没有验证任意控制流、分支生命周期或设备执行，不能据该分类推广为任意动态cond都无需捕获。

这里的key部分与[参数地址/捕获合同](npugraph_ex_restored_capture_keys_and_first_call.md)、[输入缓冲复制](npugraph_ex_replay_input_buffers_and_copy_paths.md)分开：允许更新actual_seq列表不意味着权重指针、mutated输入、输出shape和stream限制全部动态化。

## 验收要同时看key与更新规则

排查actual_seq变化时，应核对优化后准确out target、schema位置、列表中直接placeholder、分支到根索引、未更新用户与最终key。参数出现在白名单、key没有变化、或有一次捕获成功，各自都不证明后续任务已用新参数执行；还须核对[捕获与Replay更新协议](npugraph_ex_task_update_capture_and_streams.md)。本卡没有新增verified或性能收益。

## Evidence

- [独立acl_graph白名单、规则与符号分类](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)：86–178、183–247、302–470、473–601、603–686、1191–1214。仅这些范围，不表示大模块全文审阅。
- [优化后收集与cond分支映射](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)：502–522、882–932。

## 双版placeholder检查的异常边界

仅将固定发布7c6c754的对应helper与主线对照，不把前文主线cond递归整体移植到发布。两版get_node_all_placeholder_inputs仍只找容器内的直接placeholder，不沿普通FX运算节点继续追依赖；未命中Node/list/tuple/dict时，isinstance的类型元组实际写为(int,float,bool,str,None)。None是对象而非type(None)，所以输入不是前四类时，存在先在isinstance本身抛TypeError的静态路径，不能把None写成已安全跳过，也不能把后面的RuntimeError当作所有不支持输入的统一包装。本次没有执行这一分支或复现真实模型故障。

另一个check_all_sym_updated辅助函数把各规则里的输入index先汇总。对每个有用户的符号placeholder，只要找到一个对应用户/索引就令is_updated=True并break；未知用户直接continue。它不是逐个用户都必须可更新的全称检查，也不能代替前文get_unupdated_sym_input_index的未更新用户分析。

两版get_updated_ops_fn只返回gen_updated_input_func；在所存两份acl_graph.py中check_all_sym_updated仅有定义，没有本地调用点，不把这个名字当作捕获前已自动执行的全量断言。外部调用者是否另行调用仍独立，不据本文件缺调用推定整个软件栈完全不使用它。

## 有界实现对照

- [固定版本 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：213–247, 684–731；只对应本卡增补块，不提升整模块或外部被调实现资格。
- [固定版本 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：190–223, 479–519；只对应本卡增补块，不提升整模块或外部被调实现资格。
