---
type: Guide
title: ATB MLA分页注意力：LSE、工作区与图更新合同
description: 聚合五个MLA schema、18实参和LSE/工作区分支，区分Meta与设备输出、文档类型冲突及完整图更新测试边界。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/MultiHeadLatentAttentionAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_mla_with_lse.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/MultiHeadLatentAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_mla_with_lse.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
created_at: '2026-11-11T04:51:24Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# ATB MLA分页注意力：LSE、工作区与图更新合同

本卡限定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布dedc316708372c9a8bfde4527abd2a94b74840f5的MultiHeadLatentAttentionAtb.cpp、Meta、docstring及完整test_atb_mla_with_lse.py。两版CPP完整非注释token一致，测试完整AST一致；只读文本/AST，没有导入或执行上游、构建/动态加载或设备验证，保持draft。准备与Ring统计见[MLA预处理/Ring](torch_npu_atb_mla_preprocess_and_ring_preparation.md)，普通PA的另一实现见[ATB生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)，不能因名称相似合并两套宏ABI。

## 模式、schema与长度转换

get_mla_mode通过同一get_op_mode逐项查询三张map，按mask/calc/cache顺序返回三个int：

| 参数 | 精确可选键→值 | None默认 |
| --- | --- | --- |
| mask_type | undefined→0、mask_type_spec→1、mask_type_free→2 | undefined |
| calc_type | calc_type_undefined→0、calc_type_spec→1、calc_type_ring→2 | calc_type_undefined |
| cache_mode | krope_ctkv→1、int8_nzcache→2、nzcache→3 | krope_ctkv |

未知键由TORCH_CHECK报Unsupported及参数名；本helper不校验三个模式之间的组合。所有入口以q_nope建立OptionalDeviceGuard，double qk_scale转float。

五个schema分别为npu_multi_head_latent_attention、.out、.lse、_npu_multi_head_latent_attention_get_workspace.lse及npu_multi_head_latent_attention.lse_out；PrivateUse1分别映射到同名普通/out/lse/工作区/引用返回实现。共同位置参数为q_nope、q_rope、ctkv、k_rope、block_tables这五个Tensor，context_lens为SymInt[]，随后q_headnum、qk_scale、kv_headnum。三种LSE相关schema再要求位置bool return_lse；它不是默认True。共同关键字mask/qk_descale/pv_descale是Optional Tensor，qseqlen为Optional SymInt[]，mask_type/calc_type/cache_mode为Optional字符串，均默认None。lse及lse_out才有workspace=None，普通及out没有该参数；out额外提供Tensor(a!) output，lse_out再提供Tensor(b!) lse并返回对应引用。

每个入口都把context_lens经asIntArrayRefUnchecked构造新的at::kInt Tensor；qseqlen存在时同样构造int Tensor，否则是undefined Tensor。构造未提供q_nope的options/device，源代码没有把这两组长度转成设备Tensor的分支，也没有为符号未具体化或int32范围额外做本地检查。mask、两组descale原样交给宏。

传给AtbMLA的18项实参依次为：

| 序号 | 固定顺序 |
| --- | --- |
| 1–5 | q_nope、q_rope、ctkv、k_rope、block_tables |
| 6–10 | context_lens_tensor、mask、qseqlen_tensor、qk_descale、pv_descale |
| 11–16 | head_num、qkScale_float、kv_headnum、mask_type、calc_type、cache_mode |
| 17–18 | output、lse |

return_lse没有传入这18项。动态执行、工作区宏及缓存的通用合同复用[执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)中原有宏说明，不把厂商动态符号视为本CPP内部Kernel实现。

## LSE分配与return_lse是两层条件

普通入口用q_nope.sizes与q_rope.options申请output，创建undefined lse、执行宏后只返回output；普通out直接用调用者output并同样创建undefined lse。它们没有因为calc_type_ring就申请lse，也没有输出shape/dtype的本地校验。

值返回的.lse入口先申请上述output，只有calc_type整数等于ring=2才申请[q_nope.size(0),q_nope.size(1),1]、q_rope.options的lse；该分配与return_lse真假无关。执行后，return_lse=True返回(output,lse)，False返回(output,undefined Tensor)。因此True不等于所有calc_type都分配LSE，False也不等于执行前不分配。

工作区getter同样先申请output，并仅按ring模式申请lse，随后把完整18项交EXEC_GET_ATB_MAX_WORKSPACE_CMD，得到uint64 workspace_size，再按q_nope.options的Byte dtype申请[workspace_size]并返回。return_lse形参在该函数没有参与分支或宏实参；它不是workspace大小随return_lse自动改变的本地证据。

`.lse_out`直接使用调用者的output与lse，不替调用者申请LSE，也不因return_lse=False取消向宏传递lse。True分支返回forward_as_tuple(output,lse)；False分支在返回类型为tuple<Tensor&,Tensor&>的方法里写forward_as_tuple(output,at::Tensor())。此处第二项是临时Tensor表达式，不能把它描述成已证明安全的持久输出引用；本次没有编译或执行来证明该分支的可用性。

值返回.lse和.lse_out都只在workspace.has_value且defined时复制Tensor句柄到局部并走EXEC_ATB_CMD_WITH_WORKSPACE；否则走普通EXEC_ATB_CMD。本CPP未在该分支单独检查workspace字节数、dtype、device或足够容量，也未因传入workspace而完成图更新协议。

## 固定文档和Meta的实际差异

docstring把Q拆为q_nope[num_tokens,num_heads,512]和q_rope[...,64]，前者float16/bf16/int8、后者float16/bf16。krope_ctkv缓存分别为[num_blocks,block_size,kv_heads,512/64]；int8_nzcache的ctkv为[blockNum,kv_heads×512/32,block_size,32]、int8，k_rope为[blockNum,kv_heads×64/16,block_size,16]。block_tables为int32[batch,max_blocks_per_query]，context_lens为整数数组。文档约束block_size≤128且建议128、batch≤8192，int8_nzcache不支持num_heads=128；这些约束未在本包装逐条实现。

文档只说明部分mask/calc/cache模式，源码map还接受spec/free/ring/nzcache键；接受字符串不证明组合或产品可执行。文档把qseqlen写成Device浮点Tensor，与实际schema的SymInt[]?不一致，并重复qk_descale一行而没有独立写pv_descale说明；不能据重复行交换两个真实参数或改写qseqlen类型。文档输出维为[num_tokens,num_heads,head_size_vo]、float16/bf16，LSE为[...,1]且列float16/bf16/float；真实分配仍按前述Tensor options决定。文档样例为token/head各32、kv_heads1、qk576/vo512、block128、64块和随机block表，使用默认模式不取LSE，不构成int8/NZ或ring验证。

普通Meta返回empty_like(q_nope,dtype=q_rope.dtype)。lse Meta无论return_lse/calc_type如何都返回attention和已定义[token,head,1] LSE；LSE dtype/device取q_nope，而CPP ring分配取q_rope.options，二者不能合成同一个不加条件的输出合同。该Meta签名没有workspace关键字，本地也没有按return_lse隐藏LSE；不由这些静态差异直接断言外部编译路径一定成功或失败。

## 完整LSE测试的参考实现与局限

test_atb_mla_with_lse.py的compare_output_data先flatten到float32，旧ratio计数只打印；真正返回的新阈值按head_size_qk×max_context_len+4是否<2048选择：bf16为2^-7/2^-6，其他为2^-8/2^-7，并要求每项abs差≤max(abs(golden),1)×阈值。不是旧计数打印True就判定通过。

参考helper包括：按最大二次幂构造并补奇数幂的ALiBi slopes；group_mm按KV组分配查询头，float32 matmul，int8分支可加offset再乘descale；process_deq_scale将float字节重解释uint32再扩uint64。两种softmax均减行max再exp/sum，NumPy版本同时返回max+log(sum)。ND→NZ以16×16 ceil形状和转置轴生成，但convert本体直接reshape，需要输入已对齐，没有补零分支。

ref_masked_attention按QK、scale、可选bias、NumPy softmax/LSE、PV构造参考，并同时保留低精度P与高精度P输出及QK诊断。分页参考按block_table[j//block_size]和j%block_size收集K/V；context_len=0跳过且不递增紧凑query索引；mask_dim4/3分别切ALiBi或普通mask，其他分支才写LSE。compressHead会重排query/output/mask并复制长度；这只是测试的参考数据布局。

calc_data构造随机query/cache，可让V别名K前head_size_vo维，动态batch时直接用传入长度；mask_dim4建ALiBi，dim3按序号屏蔽前缀，其余None。block表为各样本连续的独立页段，query和key按512/64拆分；可选NZ转换后重排缓存。它另保留int8分支，但该分支引用的head_size在本文件没有定义；golden_compare调用的compare_cv也未在本文件定义/导入。golden_calc忽略传入in_tensors并取保存参考；golden_compare按output与可选ring LSE组合双标准，但三个实际测试没有调用这两个helper，不把这些未走分支说成已验证。

三个测试均有Ascend910B装饰，使用token32、head32、kv_head1、qk576、vo512、block128、64块、context256、float16、无mask、combined KV和非NZ、calc_type_ring，return_lse=True。前两个分别是值返回与预分配out，断言attention和LSE与参考；没有覆盖False、默认模式、bf16、int8、NZ或所有文档限制。

ACLGraph测试先以context_new=1024做普通out并申请该长度的workspace；捕获图内仍用旧context256，ExternalEvent先wait/reset，再graph_task_group_begin/end取得handle。update_stream中graph_task_update_begin(handle)后用新长度、同workspace、同graph输出重发算子，结束更新并record该event，随后g.replay；最后比较普通新长度结果与图结果。block表仍来自初始256/128=2列，源代码没有为新1024长度重建为所需8列或扩充缓存；不能仅凭这两个调用结果比较证明新输入页映射合法。该顺序是上游测试文本，不是本次跑出的捕获/更新结果，也不证明任意动态shape、工作区容量或跨流调度都支持。

## 固定证据

两版MultiHeadLatentAttentionAtb.cpp与test_atb_mla_with_lse.py均完整审阅；Meta只审13–28、Utils.h只审81–91、docstring只审_atb_api_docs.py14–70。准确版本URL、原始字节SHA和读取范围见下列固定来源；这些选段及调用到的外部库不因本卡而提升整文件/依赖实现覆盖。

- [固定源码 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/MultiHeadLatentAttentionAtb.cpp)（primary）：1–400。
- [固定源码 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_mla_with_lse.py)（implementation）：1–618。
- [固定源码 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：13–28。
- [固定源码 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（implementation）：14–70。
- [固定源码 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [固定源码 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/MultiHeadLatentAttentionAtb.cpp)（implementation）：1–196。
- [固定源码 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_mla_with_lse.py)（implementation）：1–609。
- [固定源码 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：13–28。
- [固定源码 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（implementation）：14–70。
- [固定源码 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
