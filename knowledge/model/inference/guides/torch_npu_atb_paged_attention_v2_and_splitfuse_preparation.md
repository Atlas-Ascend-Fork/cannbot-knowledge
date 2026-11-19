---
type: Guide
title: ATB分页变体准备：长度列表、掩码与SplitFuse
description: 对照分页V2和SplitFuse的长度、掩码、格式和工作区准备，并绑定固定ATB参数头文件的枚举、默认值与条件。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtbV2.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtbV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionSplitfuse.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionSplitfuse.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionSplitfuseV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-11T02:55:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ATB分页变体准备：长度列表、掩码与SplitFuse

## 固定入口和来源范围

核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`中的`atb::_npu_paged_attention_v2.out`、`atb::_npu_paged_attention_v2_get_workspace`和`atb::_npu_paged_attention_splitfuse`。主线新增的`atb::_npu_paged_attention_splitfuse_v2`单独标注。普通分页和MLA的Operation缓存、Setup、自动/显式workspace及资源寿命参见[分页注意力执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。

本卡按静态源码解释输入准备，平台与完整ATB软件配套仍待确认，保持draft、空平台。PA V2 docstring中的产品条件在下文按局部范围保留。主线TorchAir更新规则仅作为独立消费者对照，配套关系仍按固定软件栈核验。本次没有导入、执行、编译上游或进行设备实验。

## PA V2先把长度列表变为Tensor

PA V2的context_lens是`SymInt[]`，入口使用`c10::asIntArrayRefUnchecked(context_lens)`，再调用只指定`at::kInt`的`at::tensor`创建长度Tensor。源码在此没有另加符号表达式求值或INT32范围检查，也没有显式把构造设备设为query.device。采用时记录长度列表是否已具体化、INT32值域和真实构造设备，再评估这次materialize及后续准备的开销。

两个PA V2函数均把num_heads、num_kv_heads和scale_value分别映射为headNum、kvHeadNum和qkScale。其余固定赋值如下，get_workspace与执行入口保持一致。

| 属性 | 局部赋值 |
| --- | --- |
| batchRunStatusEnable | False |
| quantType / outDataType | TYPE_QUANT_UNDEFINED / ACL_DT_UNDEFINED |
| hasQuantOffset | False |
| compressType / calcType | COMPRESS_TYPE_UNDEFINED / CALC_TYPE_UNDEFINED |
| scaleType / inputLayout | SCALE_TYPE_TOR / TYPE_BSND |
| mlaVHeadSize | 0 |

输入参数的顺序与ATB VariantPack槽位需要分别核对。

| maskType分支 | VariantPack输入顺序 |
| --- | --- |
| UNDEFINED | query、key_cache、value_cache、block_table、context_lens_tensor |
| MASK_TYPE_ALIBI | 上述五项后追加mask |

value_cache和mask都通过Optional Input重载。缺少Optional值时，ParamSetter仍压入一个空`atb::Tensor`，保留对应槽位；已定义的Tensor先contiguous，CPU输入随后clone，NPU输入保存准备对象。所有这些PA V2 Input调用均使用默认`format_trans=False`，与旧普通PA对query/block_table/context_lens显式开启格式转换的写法不同。

mask_type先static_cast为枚举，所读入口只在UNDEFINED和ALIBI分支填充VariantPack。落入其它值时，这两段都不填输入和out，之后仍进入getOperation和执行准备。该局部控制流需要结合实际ATB错误处理核验，不能据整数能传入就扩出额外掩码模式。docstring也将当前接口的mask_type列为0和2。

## out和workspace查询保持同一准备条件

PA V2将调用方out填入Output，并返回同一引用，Schema标`Tensor(a!) out -> Tensor(a!)`。Output本身直接转换描述符，连续性和实际容量沿公共生命周期核对。

get_workspace重复同组PagedAttentionParam属性、长度列表构造和两种mask槽位，再调用GetAtbWorkspaceSizeCmd，以query.options和Byte申请所需长度的Tensor。它只完成Setup和工作区申请。因此查询与实际执行应使用一致的context_lens、cache/mask、head、scale、out布局和其它参数。每次重新查询也会重做该处长度Tensor和输入准备。

执行入口仅在workspace有值且defined时使用显式workspace路径，其余走自动分配。提供容量、storage offset和Setup所需字节的关系继续按公共生命周期检查。将查询得到的字节Tensor与不同参数的后续调用混用，需要重新核验对应关系。

## SplitFuse的长度与掩码合同

| 入口 | 固定参数和输入准备 |
| --- | --- |
| 旧_npu_paged_attention_splitfuse，两固定版本 | maskType固定MASK_TYPE_SPEC，calcType固定CALC_TYPE_SPEC；query/key_cache/value_cache/block_table/context_lens/mask/seq_len七个Tensor槽位，query、block_table、context_lens和seq_len显式format_trans=True。 |
| 主线_npu_paged_attention_splitfuse_v2 | mask_type缺值时取MASK_TYPE_NORM_COMPRESS，并在构造Operation前TORCH_CHECK只接受该值5；七个槽位与上述格式标志一致，calcType仍为CALC_TYPE_SPEC。 |

两条SplitFuse入口的其余PagedAttentionParam赋值沿上述head/scale映射与固定值；maskType和calcType按本表分别设置。

V2的MaskTypeToString列出多个枚举名，用于报错文本，采用条件由只接受5的TORCH_CHECK决定。context_lens和seq_len在这两条接口中直接作为Tensor输入，和PA V2的SymInt[] materialize路径不同。两条SplitFuse函数都将调用方out作为输出，Schema返回()，走RunAtbCmd自动工作区。

固定发布快照的准确`PagedAttentionSplitfuseV2.cpp`路径缺失，发布ops/atb目录的同名符号定向搜索无命中。本卡只限定这份源码差异，发布组合的其它位置或外部实现继续另行核验。

独立TorchAir主线对旧SplitFuse仅在schema名字和位置匹配时登记context_lens位置4与seq_len位置6的动态任务更新。V2及其它变体在采用前应按实际target、schema和更新规则核对。相关图key和Replay边界见[动态任务更新规则](optimization/torchair/npugraph_ex_task_update_rules_and_graph_keys.md)。

## PA V2文档条件按产品和场景核对

两版所选Python docstring相同。它将query写为`[num_tokens,num_heads,head_size]`，block_table写为INT32的`[num_tokens,max_num_blocks_per_query]`，out写为FP16/BF16的`[num_tokens,num_head,head_size_v]`。num_heads虽然有Schema默认0，说明明确要求用户配置。GQA条件为head_num大于kv_head_num且可整除。

A2/A3对应段将K/V Cache列为`[num_blocks,block_size,kv_head_num,head_size_k/v]`的ND，ALIBI mask列为`[batch,num_head,1,max_seq_len]`或`[num_head,1,max_seq_len]`的ND。另一个“Atlas推理系列产品”段保留NZ Cache和分块mask布局，并要求query/cache/mask仅FP16、batch在(0,2048]。这些局部产品描述不能合成同一布局表应用给所有产品或SplitFuse变体。

block_table元素应在`[0,num_blocks)`，block_size要求16对齐，Cache为NZ时head_size要求16倍数。该docstring同时保留“一般block_size≤128”的文字、A2下`block_size=head_size=256`的条件及使用256的样例；head_size的一般(0,256]限制后也列出特定非量化场景可到576的条件。通用mask说明还提到NORM，而当前接口段与所读入口按0/2分支。应以准确产品、布局和场景逐项核对这些条件，不能把一般上限或样例独立提升为全部组合的合同。


## 固定参数头文件的枚举与约束

同一固定仓内的`third_party/atb/inc/infer_op_params.h`提供PagedAttentionParam声明。本节将这些字段约束落到上述包装器的实际赋值，执行库版本与头文件仍需保持配套。

两版MaskType均有UNDEFINED=0、NORM=1、ALIBI=2和SPEC=3；主线另有MASK_FREE=4（注释限FP16）与NORM_COMPRESS=5，发布所读枚举到SPEC为止。主线SplitFuse V2使用5与这份新增声明对应，PA V2的本地装填分支仍按0/2处理。

头文件的headNum和kvHeadNum为int32_t、qkScale为float，默认0/0/1.0。包装入口的int64/double会赋入这些字段，采用时核对实际值域与转换后的精度。batchRunStatusEnable默认False，outDataType默认ACL_DT_UNDEFINED，hasQuantOffset默认False；本卡包装器沿这些固定默认。

CompressType为UNDEFINED=0、KVHEAD=1、KVHEAD_ROPE=2及MAX边界值。头文件注明两种KV-head压缩仅A2推理产品支持，均不支持quantType=2/3，ROPE压缩还要求maskType=0；MAX仅用于边界判断。CalcType为UNDEFINED=0和SPEC=1，SPEC段只支持quantType=0。ScaleType为TOR=0、LOGN=1及MAX边界值，LOGN段不支持quantType=2/3。InputLayout声明BSND=0、BNSD=1；上述包装器固定BSND。mlaVHeadSize默认0，大于0表示合并KV Cache的V head_size，声明范围[0,576]。

两版QuantType均为0未量化、1反量化融合、2离线INT8 QKV、3在线INT8 QKV。量化字段的dtype/head-size/输出条件见[量化PA输入准备](torch_npu_atb_quantized_paged_attention_preparation.md)。本卡固定quantType=0；头文件中的非默认压缩、LogN和MLA字段需要各自入口的实际赋值及执行合同。

## 优化验收

将context_lens列表materialize、Tensor连续化、需要时的格式转换与CPU clone、Operation选择、Setup、workspace以及Attention执行分开记录。先核对输出别名、mask、长度列表和实际更新参数，再比较捕获与稳态成本。本文未展开ATB厂商kernel的全部shape/量化/错误清理合同，也没有提供运行数值、吞吐或verified事件。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtbV2.cpp)（primary）：19–151。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtbV2.cpp)（implementation）：19–153。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionSplitfuse.cpp)（implementation）：19–78。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionSplitfuse.cpp)（implementation）：19–69。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionSplitfuseV2.cpp)（implementation）：21–107。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：172–213。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：157–205。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：559–568。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：508–517。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（implementation）：243–313。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（implementation）：243–313。
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：156–178。


## 参数头文件增补证据

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：36–44、348–449。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：39–47、349–448。

## 旧PA槽序对照与两版完整文件等价

上文两版行为差异由确定性比较确认：两固定版本的PagedAttentionAtbV2.cpp、PagedAttentionSplitfuse.cpp与PagedAttentionAtb.cpp在去除注释后的标点级token流完全一致（有序预处理指令与许可头亦一致），SplitFuseV2仅存在于主线快照。完整读取旧_npu_paged_attention两版文件补充schema槽序对照：旧入口把value_cache列为第3个必选位置参数，num_kv_heads/num_heads/scale_value、block_table/context_lens、out依次跟随，仅workspace是keyword-only；V2则把block_table/context_lens提前到位置参数，value_cache/mask/num_kv_heads/num_heads/scale_value/mask_type/workspace全部改为带默认值的keyword-only参数。迁移调用方不能按旧位置顺序改写V2调用；两版V2的VariantPack前五槽（query、key_cache、value_cache、block_table、context_lens）与旧PA一致，ALIBI分支在第六槽追加mask。

SplitFuseV2的schema与旧SplitFuse一样把context_lens留在位置4、seq_len留在位置6，仅mask_type新增为keyword-only默认5；但npugraph_ex白名单按hasattr探测旧算子名，V2不会因此继承旧的位置4/位置6更新规则。

## npugraph_ex两版白名单均无V2与量化入口

上文要求"采用前核对"的V2更新规则，在TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`两个固定版本中已定向核验为缺席：npugraph_ex的_REPLACE_FUNC_MAP中ATB项仅含旧`atb._npu_paged_attention`（updated_param_indices=[7]）与`atb._npu_paged_attention_splitfuse`（[4,6]），均以hasattr探测旧算子名并要求schema参数名/位置与预设一致；两版都没有`_npu_paged_attention_v2`、`_npu_paged_attention_splitfuse_v2`或`_npu_paged_attention_quant`的白名单或更新消费者命中。旧splitfuse的位置4/位置6规则在这些固定版本中不能外推到V2，V2的SymInt[]长度列表在入口内物化也与旧PA的placeholder张量更新机制不同。该否定性观察限于两个固定pin的npugraph_ex包，不覆盖torchair其它图执行路径，见[动态任务更新规则](optimization/torchair/npugraph_ex_task_update_rules_and_graph_keys.md)。

## 增补证据

- [主线旧PA完整文件](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtb.cpp)（implementation）：完整本地文件1–119。
- [发布旧PA完整文件](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtb.cpp)（implementation）：完整本地文件1–104。
- [TorchAir发布白名单](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：112–161。
- 主线TorchAir同文件增读125–184（上文证据仅156–178），配合对两个固定pin的定向符号搜索确认V2/quant无白名单条目；PagedAttentionAtbV2/Splitfuse/SplitFuseV2的完整1–N阅读与两版token等价由确定性比较脚本复算。
