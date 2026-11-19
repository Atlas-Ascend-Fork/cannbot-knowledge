---
type: Guide
title: ATB量化分页注意力：反量化输入与输出准备
description: 核对量化PA的注册、参数类型、反量化槽和caller out，并纳入固定PagedAttentionParam头文件的dtype、形状及组合约束。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/Fa3Atb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/Fa3Atb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-11T02:55:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ATB量化分页注意力：反量化输入与输出准备

## 固定注册和调用入口

OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的Fa3Atb.cpp实际声明`atb::_npu_paged_attention_quant`，并注册到PrivateUse1。该准确符号是本卡采用入口，文件名本身不增加FA3接口或产品支持依据。

两版完整非注释CPP token一致。整卡产品和ATB配套未知，保持draft、空平台；本次仅做静态审阅，未加载库、执行上游或进行设备实验。普通PA/MLA的输入整理、Operation缓存、捕获分派、Setup和workspace细节复用[执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。

## quant和输出类型先进入参数对象

入口以query建立OptionalDeviceGuard，构造PagedAttentionParam，并从num_heads、num_kv_heads和scale_value填写headNum、kvHeadNum、qkScale。quant_type通过static_cast转QuantType，outdata_type通过static_cast转aclDataType。

同一参数对象还固定batchRunStatusEnable=False、maskType=UNDEFINED、hasQuantOffset=False、compressType与calcType为UNDEFINED、scaleType=SCALE_TYPE_TOR、inputLayout=TYPE_BSND以及mlaVHeadSize=0。源码没有在这里按quant_type或outdata_type逐个列出可接受的值、shape与dtype组合。枚举转换和属性赋值需要和所配ATB合同一起核验，不能独立当作任意低精度格式已支持的证据。

## 反量化Tensor按确定顺序提交

| VariantPack槽位 | 输入 | format_trans请求 |
| --- | --- | --- |
| 0 | query | True |
| 1 | key_cache | 默认False |
| 2 | value_cache | 默认False |
| 3 | block_table | True |
| 4 | context_lens | True |
| 5 | k_descale | True |
| 6 | v_descale | True |

k_descale位于v_descale之前。两者是实际Tensor输入，分别经ParamSetter进行contiguous，需要时请求ND转换，CPU对象随后clone并保存；NPU对象保留准备后的Tensor。即使都称“scale”，也应按准确形状和语义核对两个输入，不能互换或按其它Attention接口的反量化槽位套用。

此入口的context_lens直接为Tensor，与[PA V2长度列表准备](torch_npu_atb_paged_attention_v2_and_splitfuse_preparation.md)采用的SymInt[] materialize路径分别核对。format_trans=True的请求也需结合实际对象和当前NPU格式判断转换成本，不能把标志出现直接计为一次物理复制。


## 固定头文件说明的量化组合

两版同仓PagedAttentionParam的QuantType声明一致，0为TYPE_QUANT_UNDEFINED，1为TYPE_DEQUANT_FUSION，2为TYPE_QUANT_QKV_OFFLINE，3为TYPE_QUANT_QKV_ONLINE。头文件将三个非零类型注释为仅支持Atlas 800I A2推理产品的功能；本卡保留该字段的局部产品条件，执行支持仍按实际ATB配套核验。

| quantType声明 | 头文件描述的Q与KV dtype |
| --- | --- |
| 0 | Q、keyCache、valueCache为BF16/FP16 |
| 1 | Q为BF16/FP16，keyCache、valueCache为INT8 |
| 2或3 | Q、keyCache、valueCache为INT8 |

量化段还要求K/V Cache的headsize等长、在(0,256]，并满足block_size×head_size≤128×128；outDataType需显式配置为ACL_FLOAT16或ACL_BF16，inputLayout仅BSND。hasQuantOffset表示启用量化时是否使用offset，而本入口固定False。这里没有增加offset Tensor槽。

CompressType的KVHEAD/KVHEAD_ROPE与ScaleType的LOGN均不支持quantType=2/3，CALC_TYPE_SPEC段只支持quantType=0。本入口固定compress/calc为UNDEFINED、scale为TOR，所以按这条实际赋值选择组合。整型输入经过包装层enum cast后，仍需按这些声明和值域验证，局部函数没有代做全部组合检查。

headNum/kvHeadNum在头文件中为int32_t、qkScale为float，入口参数则为int64/double；应记录转换后的属性值。两个descale Tensor的精确shape、元素语义和底层量化计算仍由对应ATB操作合同确认，参数声明没有在本节给出完整公式。

## caller-owned out和执行准备

Output直接接收调用方out并转换为ATB描述符，Schema为`Tensor(a!) out`且函数返回()。该包装层未另行按outdata_type分配Attention输出，因此调用者还需保证out的实际dtype、布局和容量与所选参数匹配。连续性和描述符转换的公共检查保持适用。

Operation由构造好的PagedAttentionParam取自OpParamCache，k_descale/v_descale通过本次VariantPack提交；随后走RunAtbCmd及其自动工作区。缓存键、每次Setup、捕获分派和异步资源寿命沿公共生命周期逐项核验，当前卡仅补量化变体的准确参数和槽位。

采用时保存quant_type、outdata_type、query/KV和两个descale的实际shape/dtype/stride、context_lens以及out配置，分别检查输入准备、Setup要求、实际workspace、执行结果和输出别名。执行库的实际量化计算、设备运行支持与精度/性能仍需准确配套证据，本次没有运行验证或新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/Fa3Atb.cpp)（primary）：19–84。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/Fa3Atb.cpp)（implementation）：19–74。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：172–213。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：157–205。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：559–568。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：508–517。


## 参数头文件增补证据

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：36–44、348–449。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：39–47、349–448。

## 缓存键与npugraph_ex更新缺席

quantType与outDataType在PagedAttentionParam的Operation缓存哈希键族内（见[执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)），不同quant_type/outdata_type组合会映射到不同缓存Operation；static_cast本身仍不认证组合可接受。在TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`两个固定版本的npugraph_ex更新白名单中，定向符号搜索没有`_npu_paged_attention_quant`条目；该入口在这些版本的npugraph_ex捕获图中没有动态任务更新消费者，长度或de-scale参数变化需要按各自guard与重捕获路径处理。此观察限于npugraph_ex包，不外推torchair其它路径，见[动态任务更新规则](optimization/torchair/npugraph_ex_task_update_rules_and_graph_keys.md)。

## 增补证据

- [TorchAir主线白名单](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：125–184。
- [TorchAir发布白名单](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：112–161。
- Fa3Atb.cpp两版完整文件阅读（1–84/1–74）与完整非注释token等价由确定性比较脚本独立复算。
