---
type: API
title: FlashAttention 增量与全量分支（torch_npu.npu_fused_infer_attention_score）
description: torch_npu.npu_fused_infer_attention_score：适配增量和全量推理场景的FlashAttention算子，既可以支持全量计算场景（PromptFlashAttention），也可支持增量计算场景（IncreFlashAttention）。 该版文档按 query 的 S=1 选择 IncreFlashAttention，其余进入 PromptFlashAttention。 区分发布浮点路径和主线A2/A3、950的布局、长度、分页、量化参数及文档冲突。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_with_workspace.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_with_workspace.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py
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
- torch_npu.npu_fused_infer_attention_score
---


# npu_fused_infer_attention_score：发布与主线的推理契约

## 版本与调用范围

本文区分ascend_26_0_pt28发布A2/A3与主线对应产品分支；A3的具体软件配套见版本基线卡。普通浮点入口见本卡，量化、MLA及mask组合见已链接专题；所有结论分别绑定固定版本，不构成其他硬件/软件的完整支持表。接口返回attention_out与softmax_lse两个Tensor。

关键调用形态（省略量化、MLA、共享前缀等可选参数）：

```python
out, lse = torch_npu.npu_fused_infer_attention_score(
    query, key, value, num_heads=..., num_key_value_heads=...,
    input_layout="BNSD", scale=...,
    actual_seq_lengths=..., actual_seq_lengths_kv=...,
    block_table=..., block_size=..., softmax_lse_flag=False)
```

query 的 S=1 选择增量分支，其余进入全量分支；不能只用上层阶段名字替代实际 shape 检查。Q/K/V 的 layout、连续性、head 数与 dtype 必须一致地解释；GQA 要求 KV head 数整除 Query head 数，来源限制比值不大于 64。

## 长度与分页

普通布局中，有效长度通常按每个 batch 的序列长度解释；但 Q_S=1 的增量分支在 query 的 input_layout 非 TND 时，actual_seq_lengths 无效，真实 KV 长度由 actual_seq_lengths_kv 描述。TND 相关布局的累计长度及分页例外须按相应分支核对，不能把独立长度和累计长度混用；非分页 TND 场景按长度列表元素个数确定 batch。

增量 PagedAttention 需要有效 block_table、非零 block_size 和真实 KV 长度，KV 存储须与块表对应。发布文档中 Q_S=1 时 block_size 最大 512，FP16/BF16 按 16 对齐，推荐值 128；块表是二维，行数与 batch 相同，列数覆盖实际最大块数。不同 Q layout 下允许的 KV 布局还需逐项核对。分页与 tensorlist、左 padding 等能力存在组合限制。

## 输出与验证

softmax_lse_flag=False 时第二个返回值是占位，不应作为有效 LSE 合并。至少覆盖 Q_S=1 与多 Token、不同 batch、TND 累积长度、页边界和空 KV，并与参考 Attention 比较。MLA、量化、prefix、特殊 sparse/mask 和跨版本组合需另行读对应约束；本卡不宣称这些组合已适配或测量性能。本次未运行算子。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 主线普通浮点契约与完整参数入口

以下仅适用主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，产品页覆盖A2/A3与950PR/950DT，不扩大上文发布版范围。Python Schema的Q/K/V均为Tensor，K/V被C++/Converter包装为单元素TensorList；底层TensorList说明不授权把list直接传给Python公共入口。GQA需显式正确KV头数，0表示MHA，Qheads>0、Qheads/KVheads为整数且≤64。scale默认1.0，不会自动取1/sqrt(D)，应显式使用模型缩放系数。

| 参数组 | 主线v1入口与含义 |
| --- | --- |
| 普通注意力 | pse_shift、atten_mask、num_heads、num_key_value_heads、scale、pre_tokens、next_tokens、input_layout、sparse_mode、inner_precise |
| 有效长度/分页 | actual_seq_lengths、actual_seq_lengths_kv、block_table、block_size |
| INT8与后量化 | dequant_scale1、quant_scale1、dequant_scale2、quant_scale2、quant_offset2 |
| KV合并/分离伪量化 | antiquant_scale/offset/mode；key/value_antiquant_scale/offset/mode |
| padding/prefix | query_padding_size、kv_padding_size、key/value_shared_prefix、actual_shared_prefix_len |
| MLA与LSE | query_rope、key_rope、key_rope_antiquant_scale、softmax_lse_flag |

普通连续ND浮点layout为BSH、BSND、BNSD，BSH的H=N×D；BNSD_BSND表示输出转BSND且仅多Token分支。其他NBSD/packed布局有产品、Q_S与MLA尺寸限制，不能由shape推导代码识别就认定全部支持。K/V对应shape一致；空Q返回空，非空Q但KV S2=0时attention_out为对应shape全零。

prefill一般B≤65536、N≤256、D≤512、S≤20971520；A2/A3在D非32Byte对齐时B≤128，浮点D需16对齐。950非量化prefill D=1..512均列支持。decode KV S≤262144。上限不是时延保证，大B/N/S/D乘积可能触发timeout，需考虑切S与真实工作量。

普通长度支持单元素广播或长度≥B取前B项；非PA packed长度为累计边界，PA的KV长度为独立实际长度。950非TND且无RoPE的decode忽略Query长度，不能照搬带RoPE的分支。普通prefill PA块128..512、步长128，decode浮点16对齐，A2/A3栏限定块≤512、950栏未列同一上限；TND/MLA的16倍数≤1024为特化例外，不与普通块范围合并。

完整复核后确认两版Meta与C++关闭LSE时均分配[0] FP32，文档却写[1]零Tensor。开启LSE时packed布局为(T,Q_N,1)，普通布局为(B,Q_N,Q_S,1)；返回attention_out的逻辑D取自V并处理低比特打包。仅shape/分配成功不证明数值路径可用。

非950的v1在CANN≥8.1.RC1选择aclnnV3，否则V2；带RoPE的旧CANN会被拒绝。950选择aclnnV5，不能把Python v1等同于底层aclnnV1。主线配套仍按独立基线核对，未运行算子。

## 主线专题与已记录差异

- [KV伪量化、PA及GQA NZ](../../guides/fia_kv_antiquant_modes.md)：包括950不支持合并antiquant参数。
- [INT8/FP8全量化与后量化](../../guides/fia_quantized_attention_paths.md)：v1 Query类型表与INT8示例的冲突保留为未确认，未据此认定全产品可用。
- [MLA与TND/NTD输出](../../guides/fia_mla_and_packed_layouts.md)：包括v1 NBSD表与实际(N,B,S,D)形状差异。
- [mask、prefix、padding与LSE](../../guides/fia_mask_prefix_and_lse.md)：因果mask示例冲突不作为可运行配方。

## 两版实现及文档完整复核

本卡完整核对主线英文906行、中文差异与发布中文412行，并审阅两版包装、Meta、Schema、TorchAir转换器、工作区测试与PyTorch graph handler。发布与主线的FIA v1 C++全文651行完全相同，Meta的共享形状helper和v1入口也逐行相同；因此以下已核实的分配/调用事实可用于两个固定提交，产品支持仍分别由各自文档限定。发布公开A2/A3，主线另列Ascend950系列（包含旧称Atlas A5）PR/DT，发布测试内有950方法不等于发布产品声明。

文档基础段要求K/V对应shape一致，部分packed/测试却使用不同QK/V维度，且包装有独立Dv分配；这些局部形状分支不构成任意D组合的许可。通用Query类型段仅列FP16/BF16，与全INT8表/例子冲突；950总表禁止PSE/TensorList等，特化段又分别描述PSE或D128的TensorList。按明确场景保留这些差异，不能把总表、特化与实现分支取并集。

## 输出分配、空输入与Meta

两版关闭LSE实际都是FP32[0]，不是文档所写[1]零Tensor，也不是None；开启时TND、NTD、TND_NTD、NTD_TND均为(T,Nq,1)，其他布局为(B,Nq,Sq,1)。输出NBSD实际为(N,B,S,Dv)，与文档部分表格的(B,N,S,Dv)不同，现有布局专题按实现记录。

一般Dv由value的布局推导，INT32容器按8倍还原逻辑INT4维度；Dv或Q的对应维度为0时helper回退Q维度。quant_scale2存在时分配INT8，Q为INT8且无输出量化时优先取query_rope dtype、无RoPE则FP16，否则沿Q dtype。这里描述分配顺序，不承诺非法参数组合可算；quant_offset2单独存在不会由分配代码自动建立合法后量化。

空Q返回空、非空Q但KV S2=0返回零是文档的后端语义；包装先构造输出再调用后端，没有在这里实现完整零填充。不要把empty分配认作零值来源，也不要把Meta能推shape当作精度或平台验证。BSH需num_heads>0，Nkv=0在形状helper中按Nq解释；公共Schema的Q/K/V是Tensor，内部单元素TensorList不授权直接传Python列表。

## 工作区、out与软件栈分派

两版普通v1在非950且CANN≥8.1.RC1时调用aclnnFusedInferAttentionScoreV3，否则V2；旧CANN带任一RoPE相关Tensor则拒绝。950调用V5并传query_quant_mode=0、pse_type=0及空的新参数，不因Python名为v1就调用aclnnV1。Schema范围为v2.1起，并不表示所有后端CANN版本支持所有参数。

同一文件还包含.out、_get_max_workspace及_infer_output。out返回传入的两个可写Tensor引用；workspace存在时以其存储地址及numel×element_size字节数传更新宏，否则走普通执行宏。调用者提供的输出/工作区不能靠公开基本示例中的尺寸替所有布局、dtype或LSE配置分配。

非950的_get_max_workspace即使旧版普通路径可走V2，也固定查询V3；它只有“旧版带RoPE拒绝”检查，没有同样的V2回退。不能据普通调用可用推断工作区查询同样可用。该helper先分配Attention/LSE临时输出，再取后端workspace_size，并按query dtype分配该数量的元素，返回的是Tensor；其numel不是独立的通用字节容量接口，也不是无分配的纯整数探针。_infer_output只返回分配结果，不执行注意力，不生成有效数值。

## 图转换与捕获更新的版本差异

两个固定TorchAir转换器分别对INT32 K/V及共享前缀做INT4 Bitcast并把末维乘8，再包装单元素K/V列表；长度及有效prefix长度经dtype_promote到INT64。该过程重解释存储，不做量化校准、任意缓存重排、mask极性纠正或TensorList公开接口扩展。Converter的List或Tensor注解也不覆盖公开SymInt[]/List[int]合同，不能直接据此把device Tensor传给这个公共入口。

两版PyTorch的ifa_handler在普通FIA捕获前查询workspace、推导两项输出后换用.out；显式.out则直接透传，postprocess返回kwargs中的out列表。发布handler仅在记录args长度≥7时改写第6项KV实际长度，没有更新Q长度的对应代码；主线改成声明Q/KV两组UPDATE_SPECS，由基类处理。该差异需结合记录的参数归一化与基类核对，不能据局部handler宣称所有位置/keyword参数都可动态更新。

文档NPUGraph例子用copy_保留捕获输入地址，改变窗口标量时重新捕获；graph/eager的allclose只打印结果，没有assert，亦未比较新窗口图与对应eager。发布文档仍是TorchAir compile打印示例，文字称“with mask”而调用无mask。本次未运行任一图或建立两个仓库主线兼容关系。

## 测试实际证明的范围

两版基础测试各18方法，10个无条件skip，8个950限定方法未skip。前6个skip方法只取输出没有数值断言，部分还缺少TND长度或使用4维Tensor调用TND，不能据名字认证相应分支。旧INT4测试把mode构造成Tensor，但Schema要求int，也不能当可运行参数示范。

950方法大多用全1输入及全1目标做.equal断言，覆盖若干Dv、分页、INT4和布局分配用例；不能证明任意稀疏mask、PSE、量化scale、长序列或LSE数值。一个BNSD_BSND方法还使用Sq=1，与文档“仅Sq>1”冲突；NSD方法与代码识别也不扩展公开产品layout。TND方法有BF16输入，却与FP16全1目标比较，值相等检查不替代完整dtype合同。

PA的CPU golden把整个物理缓存展平并按seq_lens屏蔽，不按block_table恢复逻辑顺序，只支持MHA或Nkv=1；skip用例甚至在只有1个物理块时随机生成0..9页号。该参考不覆盖任意分页映射或普通GQA，更不能绕过块ID合法性要求。

工作区文件两版113行完全相同，3个方法全skip，且仅取返回项没有数值assert。所谓“不传workspace”helper先查询workspace却没有把它传给.out；显式工作区路径也不能凭这组skip测试宣称验证通过。上游断言与方法存在分别记录，本次没有设备执行、性能测量或新增verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### FlashAttention 增量与全量分支：torch_npu.npu_fused_infer_attention_score

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

适配增量和全量推理场景的FlashAttention算子，既可以支持全量计算场景（PromptFlashAttention），也可支持增量计算场景（IncreFlashAttention）。

### 输入、输出与行为

该版文档按 query 的 S=1 选择 IncreFlashAttention，其余进入 PromptFlashAttention。这是该版本 API 的分支描述，不能代替模型实际布局、mask 和长度参数的检查。

### 文档签名

```text
torch_npu.npu_fused_infer_attention_score(query, key, value, *, pse_shift=None, atten_mask=None, actual_seq_lengths=None, actual_seq_lengths_kv=None, dequant_scale1=None, quant_scale1=None, dequant_scale2=None, quant_scale2=None, quant_offset2=None, antiquant_scale=None, antiquant_offset=None, block_table=None, query_padding_size=None, kv_padding_size=None, key_antiquant_scale=None, key_antiquant_offset=None, value_antiquant_scale=None, value_antiquant_offset=None, key_shared_prefix=None, value_shared_prefix=None, actual_shared_prefix_len=None, query_rope=None, key_rope=None, key_rope_antiquant_scale=None, num_heads=1, scale=1.0, pre_tokens=2147483647, next_tokens=2147483647, input_layout="BSH", num_key_value_heads=0, sparse_mode=0, inner_precise=0, block_size=0, antiquant_mode=0, softmax_lse_flag=False, key_antiquant_mode=0, value_antiquant_mode=0) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_fused_infer_attention_score.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_infer_attention_score_with_workspace.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedInferAttentionScoreKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_infer_attention_score_with_workspace.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_infer_attention_score.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/ifa_handler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/ifa_handler.py)（implementation）
