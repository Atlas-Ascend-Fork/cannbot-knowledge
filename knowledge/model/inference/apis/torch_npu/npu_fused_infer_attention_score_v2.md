---
type: API
title: FlashAttention v2 版本化选型（torch_npu.npu_fused_infer_attention_score_v2）
description: torch_npu.npu_fused_infer_attention_score_v2：适配增量&全量推理场景的FlashAttention算子，既可以支持全量计算场景（PromptFlashAttention），也可支持增量计算场景（IncreFlashAttention）。 该版文档推荐在不涉及 system prefix、左 padding、KV 量化参数合一、pertensor 全量化时使用 v2；涉及这些场景时转查老接口 `npu_fused_infer_attention_score`。 区分发布接口与主线950量化增量、GQA整除修订、Eager例外、输出类型和LSE差异。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_fused_infer_attention_score_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k3/models/modeling_kimi_k3.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_v2_with_workspace.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_v2_with_workspace.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/ifa_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/ifa_handler.py
  role: implementation
created_at: '2026-11-10T03:38:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_fused_infer_attention_score_v2
---


# npu_fused_infer_attention_score_v2：版本迁移与量化边界

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_fused_infer_attention_score_v2(query, key, value, *, query_rope=None, key_rope=None, pse_shift=None, atten_mask=None, actual_seq_qlen=None, actual_seq_kvlen=None, block_table=None, dequant_scale_query=None, dequant_scale_key=None, dequant_offset_key=None, dequant_scale_value=None, dequant_offset_value=None, dequant_scale_key_rope=None, quant_scale_out=None, quant_offset_out=None, learnable_sink=None, num_query_heads=1, num_key_value_heads=0, softmax_scale=1.0, pre_tokens=2147483647, next_tokens=2147483647, input_layout="BSH", sparse_mode=0, block_size=0, query_quant_mode=0, key_quant_mode=0, value_quant_mode=0, inner_precise=0, return_softmax_lse=False, query_dtype=None, key_dtype=None, value_dtype=None, query_rope_dtype=None, key_rope_dtype=None, key_shared_prefix_dtype=None, value_shared_prefix_dtype=None, dequant_scale_query_dtype=None, dequant_scale_key_dtype=None, dequant_scale_value_dtype=None, dequant_scale_key_rope_dtype=None) -> (Tensor, Tensor)
```

普通浮点入口先按A2/A3、FP16/BF16、MHA理解；MLA、量化、Sink及特殊mask的发布/主线合同分别见后文和已链接专题。相较旧接口，num_heads→num_query_heads、scale→softmax_scale、actual_seq_lengths→actual_seq_qlen、actual_seq_lengths_kv→actual_seq_kvlen、softmax_lse_flag→return_softmax_lse，不能只改函数名。返回 (attention_out,softmax_lse)，不请求LSE时两版实现均为FP32[0]空占位，文档[1]零Tensor描述与实现不符。

## 参数与组合限制

- Q/K/V 为连续 ND 浮点 Tensor，K/V shape 一致；Q_S=1 是增量路径，其余为全量。普通布局的长度为独立 batch 长度；TND 为必传的非负累计长度。增量、非 TND 时 actual_seq_qlen 无效，KV 实际长度仍需核对。
- 本卡 MHA 使用等量 Q/KV 头数，并与 shape N 轴一致。v2 文档的 GQA 整除方向与旧接口文字相反，但同时要求 Q/KV 比值≤64；不据这句冲突配置 GQA，需结合实际 CANN 契约复核。
- 全量浮点 D 需 16 对齐，D≤512、N≤256，发布文档对 D 非 32Byte 对齐场景写“仅支持到128”，对象表述含混，不能直接当作 D≤128；规模大仍可能超时，不把 S 的支持上限当作可运行时延保证。
- 普通浮点分页必须提供有效 block_table 与 actual_seq_kvlen；block_table 为二维 (B,至少最大页数)，block ID 合法性由调用方保证。Q_S>1 时 block_size∈{128,256,384,512}；Q_S=1 时浮点需 16 对齐，不能直接继承前一分支的配置。
- 该版本不覆盖 system prefix、左 padding、KV 量化参数合一和 pertensor 全量化等旧接口场景。签名中的多个 *_dtype 与 dequant_scale_key_rope 为预留项，不代表这些能力已开放。
- sparse_mode=0 且 mask=None 时忽略 pre/next tokens；需要因果语义时必须按对应模式和正确 mask 配套，不能仅依赖参数名字。

## 验证与模型关联

迁移前后保持相同 layout、softmax scale、有效长度和 mask，对比增量/全量输出及 LSE；量化、GQA、MLA 等超出本页路线的调用保留为单独核对项。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k3/models/modeling_kimi_k3.py#L2893)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [旧 FIA 浮点契约](npu_fused_infer_attention_score.md)

## 主线增量、默认值与 GQA 修订

以下为主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的A2/A3与950PR/950DT范围，与上文发布版分开。主线文档比发布文档原型多列quant_scale_p=None及out_dtype=None；两版Schema/Meta/C++实际均已包含这两个参数，不能把文档增补记成主线才新增实参，其余关键字仍按精确提交Schema核对。num_query_heads默认1、KV头默认0、softmax_scale默认1.0、inner_precise默认0；Query头数必须正，0 KV头在Meta/C++按Query头补齐，不自动纠正错误GQA。

主线文档已把整除方向改为KVheads整除Qheads，Q/KV比值≤64；这解决本提交的GQA文字方向问题，不修改发布快照的原始歧义。scale仍需显式传模型值，不自动按head_dim缩放。Python Q/K/V为Tensor，不能把底层KV TensorList能力当成此Schema的list输入能力。

950普通浮点prefill D支持1..512，A2/A3仍需16对齐；一般B≤65536、N≤256、D≤512、S≤20M，A2/A3非32Byte对齐D时B≤128。旧发布段“只支持≤128”的对象表述含混，主线明确指B而非把D上限降为128。普通PA与packed/MLA特化的块大小、格式和长度要分别核对，不能继承另一分支的全套条件。

主线Meta/C++关闭LSE均分配[0] FP32，与文档[1]零占位有差异；开启后packed各布局统一(T,Q_N,1)，普通布局(B,Q_N,Q_S,1)。输出D来自V，INT4/FP4需要还原逻辑D。输出量化或INT8/E4M3/指定HIFLOAT8分支可转发out_dtype，但分配分支存在不证明任意dtype组合可用。

## 主线量化、Sink 与编译边界

主线新增950的MXFP8全量化、GQA FP8、FP4 KV伪量化等明确路径，各有mode三元组和物理scale；quant_scale_p在A2/A3文档仍预留，950为FP32 shape(1,)的P量化因子。key/value_dtype与E8M0 scale提示在相应950路径有作用，不能把发布版“全部预留”沿用到主线。query_dtype及其他提示的预留表述与实现分支仍有差异，详见专题中的待确认项。

Meta显式禁止E4M3 Q/K/V + query/key/value模式3/3/2编译入图，注明该GQA FP8组合只支持Eager。普通“支持图模式”不能覆盖这个例外，也不凭GE Converter存在绕过限制。learnable_sink仅非量化，A2/A3限TND/NTD_TND且V_D≤128，950限V_D为64或128，不与PSE、左padding、prefix、后量化组合。

950 C++使用aclnnV5，非950使用V4；TorchAir Converter把quant_scale_p映射至底层quant_scale1，prefix/左padding/combined量化数据置None。两个固定主线仅作各自实现审阅，不据Converter证明软件组合兼容。本文未运行任何NPU或编译实验。

- [KV伪量化、打包与NZ](../../guides/fia_kv_antiquant_modes.md)
- [全量化、产品冲突与Eager限定](../../guides/fia_quantized_attention_paths.md)
- [MLA与packed长度/布局](../../guides/fia_mla_and_packed_layouts.md)
- [稀疏mask、Sink相关互斥及LSE](../../guides/fia_mask_prefix_and_lse.md)

## 完整版本复核与参数公开程度

本卡完整核对主线英文954行、中文完整差异及发布中文388行，并结合已有四张专题审阅16个精确代码来源。发布与主线的FIA v2 C++全文699行相同，两个Schema范围也完全相同：发布实现已包含quant_scale_p和out_dtype，发布文档原型未列出。主线文档补列参数，不等于它们是主线才加入的Python实参，也不证明发布CANN9.0已支持主线950全部量化路线。

发布公开产品仅A2/A3，主线另列Ascend950系列（包含旧称Atlas A5）PR/DT。发布描述GQA整除方向相反，主线已修订为Nkv整除Nq且比值≤64；已有C++并不对所有头数约束逐项校验，不能靠能分配输出替错误GQA认证。默认Nkv=0表示与Query相同的多头数，不是示例文字所说的单头注意力。

两版公开数据入口都没有prefix、padding或combined antiquant_scale/offset。文档“分离参数同时传入时优先”的表述及antiquantScale/Offset的(2,B,S)形状是遗留描述，不应据此向v2传不存在的keyword；需要这些路线应另核旧v1。*_shared_prefix_dtype等提示也不创建共享前缀数据输入。

## dtype分配、LSE与工作区

两版实际关闭LSE都分配FP32[0]，修正文档及本卡旧段的[1]零Tensor描述。开启时TND、NTD、TND_NTD、NTD_TND统一(T,Nq,1)，其他布局(B,Nq,Sq,1)，输出NTD不表示LSE也转成(N,T,1)。NBSD输出为(N,B,S,Dv)，按实际V的逻辑维度推导；INT32的INT4容器扩8、相应FP4容器扩2，不把物理字节末维当逻辑Dv。

quant_scale_out存在时默认分配INT8，可用out_dtype覆盖；否则INT8/E4M3 Q或指定HiF8的uint8 Q分支可选out_dtype、RoPE dtype或默认FP16。其他浮点分支沿Q类型分配。输出dtype提示不保证任意枚举/容器组合满足后端；包装的make_wrapper只校验itemsize并指定ACL解释，没有量化、校准或字节重排。

普通、out及工作区查询两版均按非950 V4、950 V5分派，无v1的旧CANN V2回退。out返回两个预分配输出引用，外部workspace按numel×element_size字节容量传给更新调用；_get_max_workspace先分配输出再查询后端，并以query dtype分配workspace_size个元素，返回Tensor，不能当成纯整数字节查询。_infer_output只分配形状/dtype，不计算注意力数值。

query/key/value、RoPE和部分scale的dtype提示被C++包装使用，但key_shared_prefix_dtype/value_shared_prefix_dtype/dequant_scale_key_rope_dtype没有在该包装内形成相应数据转换。quant_scale_p仅950 V5转发到对应P量化位置，非950 V4使用空quant_scale1。实现存在某些预留参数分支，不能反向认定文档未开放的组合已经可用。

## 编译、捕获与低精度转换

只有主线Meta新增精确拦截：Q/K/V均E4M3且模式3/3/2时报“only supports eager mode”。发布Meta没有该检查；缺少拦截不证明发布允许该组合入图，更不把主线950路线回推发布产品。6/6/8 MXFP8与3/3/2 GQA FP8仍分别按现有全量化专题的scale、layout和页大小使用。

两版TorchAir转换器将INT32 K/V都按INT4 Bitcast并末维扩8，FP4按对应提示Bitcast并扩2；E8M0 scale、HiF8 Q/K/V也只做位解释。K/V被包装单元素列表，长度提升INT64；query_rope_dtype/key_rope_dtype等提示并未在这个转换器中逐项应用，不能从C++所有wrapper推断GE有同样转换。输出HiF8另修改GE输出描述类型，不替代输出分配或底层支持检查。

两版PyTorch handler已在v1复核中按同一SHA审阅：v2捕获前查询workspace，_infer_output只取Q/V及相关dtype、布局、输出scale、页表、head数、LSE/RoPE提示，再换为.out；显式.out直接透传。发布只更新记录的KV长度槽位，主线声明Q/KV两组更新spec，不能据示例推断任意动态shape/layout/量化参数都可重放。

主线文档图例改为torch.compile backend="npugraph_ex"，发布仍用TorchAir npu_backend；两者都只打印，没有数值assert，调用无mask却打印“with mask”。Python局部TORCH_LOGS/TORCHDYNAMO_VERBOSE赋值也不是os.environ配置。图例只覆盖普通FP16 BNSD，不能认证所有FP8、Sink、分页或tree mask组合。

## 文档内部差异与场景选择

主线中文明确允许K/V模式6/8这一MXFP8例外，英文通用参数只提0/1例外，但同页又列6/6/8；按专门路线区分，不能因为一般“模式相同”文字删除合法路线，也不能把两套scale表混用。中文PA通用段只禁止TensorList，英文仍多写“禁止伪量化”，而950产品专节明确列PA伪量化；文档差异保留并按专门条件核对，不能据一句通用文字生成跨产品支持表。

发布及主线的tree mask专节要求MLA/RoPE，GQA NZ专节却同时列mode9并禁止RoPE，不能组合成可运行方案。MLA D512段允许INT8全量化，A2/A3 Query类型表不列INT8，TND D512限制又禁止全量化；已有专题已保留这些冲突，不用随机/常量测试消除它们。

主线BNSD_NBSD表在英文重复两行，一处说Sq>1、一处说1..16；中英文产品段均说Sq>1且≤16，不能因重复表格扩大到Sq=1。950无RoPE的Query长度“无效”描述与TND两组长度必传的专节也需分开，packed边界按专门合同解释。通用PA段的FP32/BF16类型文字与FP16/BF16参数/例子不一致，不据该处将FP32 Q扩入公开支持。

对于后量化的无效行，v2两版仍列与v1对应的拦截公式：输出INT8且offset非空时，mode0有mask并actualQ-actualKV-pre>0或next<0；mode3实际KV短于Q；mode4的pre<0或next+actualKV-actualQ<0；mode1/2无此项。inner_precise不是绕过非法量化/窗口组合的开关，不能把TND累计边界直接代入逐batch差值。

## 测试数量、失效用例与未验证范围

基础文件两版均398行，差异仅行尾空白。AST有17个test_定义，但同名test_npu_fused_infer_attention_score_v2出现两次，后面的TND PA定义覆盖前面的基础FP16定义；实际仅16个唯一方法，5个无条件skip、11个950限定。不能把17个定义都算作有效测试或覆盖普通FP16路径。

最早的两个LSE skip方法只是取输出没有断言；PA skip方法对三维输入使用四维参考操作，transpose传多轴且引用未定义attention_out，调用还未给完整分页长度/block_size。Sink方法虽有参考比较，但无条件skip且仅常量数据。本次没有执行任何方法。

四个950方法调用npu_fused_infer_attention_v2，缺少本接口名称中的score；两版公共Schema与TorchNPU源码范围未找到该同名别名，不能算本接口可运行证据。输出dtype两个方法拿独立随机Tensor做.equal目标，未构造参考Attention，不能作精度基准；NSD方法还使用本方法未定义的softmax_scale和return_softmax_lse。常量Dv/布局方法不覆盖任意mask、量化、数值分布或LSE，部分Sq=1 BNSD_BSND用例还与文档限制冲突。

工作区文件两版115行完全相同，3个方法全部skip且无数值断言；非workspace helper查询了workspace却没有传给.out。源码中的断言、skip及静态缺陷分别记录，不作为发布或主线精度/性能认证，也没有新增verified。真实迁移应固定有效长度、模型scale、mask和量化参数，在匹配软件栈下比较输出/LSE，并分别验证页映射、尾页、Sink与捕获更新。

## 已有 OpPlugin 7.3.0 文档与版本边界

### FlashAttention v2 版本化选型：torch_npu.npu_fused_infer_attention_score_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

适配增量&全量推理场景的FlashAttention算子，既可以支持全量计算场景（PromptFlashAttention），也可支持增量计算场景（IncreFlashAttention）。

### 输入、输出与行为

该版文档推荐在不涉及 system prefix、左 padding、KV 量化参数合一、pertensor 全量化时使用 v2；涉及这些场景时转查老接口 `npu_fused_infer_attention_score`。这是版本化选型条件，不意味着其他版本具有同样的分界。

### 文档签名

```text
torch_npu.npu_fused_infer_attention_score_v2(query, key, value, *, query_rope=None, key_rope=None, pse_shift=None, atten_mask=None, actual_seq_qlen=None, actual_seq_kvlen=None, block_table=None, dequant_scale_query=None, dequant_scale_key=None, dequant_offset_key=None, dequant_scale_value=None, dequant_offset_value=None, dequant_scale_key_rope=None, quant_scale_out=None, quant_offset_out=None, learnable_sink=None, num_query_heads=1, num_key_value_heads=0, softmax_scale=1.0, pre_tokens=2147483647, next_tokens=2147483647, input_layout="BSH", sparse_mode=0, block_size=0, query_quant_mode=0, key_quant_mode=0, value_quant_mode=0, inner_precise=0, return_softmax_lse=False, query_dtype=None, key_dtype=None, value_dtype=None, query_rope_dtype=None, key_rope_dtype=None, key_shared_prefix_dtype=None, value_shared_prefix_dtype=None, dequant_scale_query_dtype=None, dequant_scale_key_dtype=None, dequant_scale_value_dtype=None, dequant_scale_key_rope_dtype=None) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_fused_infer_attention_score_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_v2_with_workspace.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_v2_with_workspace.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/ifa_handler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/ifa_handler.py)（implementation）
