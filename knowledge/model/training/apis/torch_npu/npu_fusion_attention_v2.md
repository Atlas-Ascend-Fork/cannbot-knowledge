---
type: API
title: npu_fusion_attention_v2：训练RoPE、PSE顺序与随机数版本边界
description: 按固定主线限定A2/A3/950训练V2入口，说明RoPE与PSE组合、七输出和梯度、发布实现差异及Meta限制。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T04:44:07Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_fusion_attention_v2：训练RoPE、PSE顺序与随机数版本边界

## 来源与适用范围

公开合同依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中文、英文两页。产品为A2/A3及Ascend950系列（包含旧称Atlas A5）PR/DT，仅训练、单算子模式，明确不支持图模式和aclgraph。本卡另核对发布dedc316708372c9a8bfde4527abd2a94b74840f5实现、Schema、Meta与测试，说明实现差异；发布快照没有对应V2 Markdown，不能据主线产品表认证发布所有V2组合。

发布属于ascend_26_0_pt28来源组合；主线软件版本须单独配套，不把固定提交等同于运行验证。V2不是推理FIA，也不是V3张量化随机元数据入口。

## 调用与返回

```python
attention_out, softmax_max, softmax_sum, softmax_out, seed, offset, numels = torch_npu.npu_fusion_attention_v2(
    query, key, value, head_num, input_layout,
    pse=None, padding_mask=None, atten_mask=None,
    query_rope=None, key_rope=None, scale=1., keep_prob=1.,
    pre_tokens=2147483647, next_tokens=2147483647, inner_precise=0,
    prefix=None, actual_seq_qlen=None, actual_seq_kvlen=None,
    sparse_mode=0, gen_mask_parallel=True, sync=False,
    pse_type=1, q_start_idx=None, kv_start_idx=None,
    softmax_layout="", sink=None, dropout_mask=None, seed=0, offset=0)
```

前五项为位置参数，其后均为关键字参数；窗口名是pre_tokens/next_tokens，与[V1](npu_fusion_attention.md)的pre_tockens/next_tockens不同。scale默认1，keep_prob是保留概率(0,1]。前四个返回为Tensor，后三项整数。

attention_out随Q布局、尾维为Dv；softmax_max/sum为FP32，非TND分配[B,Nq,Sq,8]、TND分配[T,Nq,8]，用于反向；softmax_out为shape[0]预留Tensor。numels是dropout覆盖元素数，不是UINT8存储字节数。不要按FIA双返回解包。

## 布局、GQA与维度

Q/K/V为ND、3或4维，dtype一致，支持FP16/BF16/FP32；布局为BSH/SBH/BSND/BNSD/TND。Nq为1..256，Nq/Nkv须为非零整数，>1为GQA。D范围1..768；A2/A3明确要求Dq=Dk=Dv，950可Dq=Dk>Dv，其他K/V轴一致。C++按Dv分配输出不表示A2/A3公开允许不等D。

非TND B为1..2M，S为1..1M；TND表中A2/A3 B为1..20000，950 B为1..2K，S/T均1..1M。但actual_seq列表长度又写1..2K，存在范围冲突；有prefix时表列非TND最大2K、TND最大1K，稀疏约束却写B≤32。不要取各表最大值拼成新的有效合同，具体输入需核对真实后端。

TND必须给两项非空、等长的INT64累计长度，不含首个0；例如真实[2,2,2]传[2,4,6]。中间零长度batch使用重复前缀，如[2,4,4,6,8]，且此时无PSE；尾部不参加计算则使用单独的尾0规则，如[2,5,9,0,0]，不能推广为任意非单调前缀。禁止TND mask中有整行全True的padding场景。

## PSE计算顺序与压缩

|pse_type|文档语义|
|--|--|
|0|先scale*QK再加外部PSE|
|1（默认）|QK先加外部PSE，再整体乘scale|
|2|内部生成PSE，先乘再加；pse为FP32[B,N]或[N]|
|3|内部生成PSE，先乘、再加、再sqrt；pse为FP32[B,N]或[N]|

type2/3当前只支持Sq=Skv。普通PSE参数支持FP16/BF16/FP32、文档另要求与QKV同dtype；这与type2/3固定FP32的专门要求存在一般/特殊约束歧义，不能将任意混合dtype视为已支持。

普通非TND PSE支持BNSS、BN1Skv、1NSS；TND可按逐batch的N*Sq_i*Skv_i展平后拼接为pseTotalLen。ALiBi压缩可只保留PSE最后1024行，BN1024Skv或1N1024Skv；A2/A3仅非TND且Sq>1024、各batch Sq=Skv、因果下三角条件成立时支持，950另支持TND压缩。TND的一般shape列表不能绕过分产品限制。

## RoPE扩展与sink

query_rope/key_rope必须成对传入，只用于TND且必须给atten_mask与有效累计长度；keep_prob=1，不支持外部dropout_mask、PSE，pse_type仅1，TND下也不支持prefix压缩mode6。RoPE扩展是在打分时增加Q_rope*K_rope^T项，并不是在算子内对原Q/K执行旋转位置编码。

A2/A3含RoPE时Q/K/V及RoPE只支持BF16；950仍可FP16/BF16/FP32且RoPE与对应Q/K除D外各轴相同，目前只列Q/K D=128、RoPE D=64这一种。一般RoPE D要求两项相等、8倍数且≤Q/K/V的D，不能用宽泛D约束推导950所有形状。文档RoPE示例却取Q/K D64、RoPE D64，所以不适合作为950当前专门形状的示例。

sink为FP32[head_num]额外Softmax归一化项：分母增加exp(sink-m)，分子保持原QK的权重乘V，因此不是给V加偏置。非950有sink时要求ScoreV3/VarLenScoreV5及对应Grad符号；950V2前后向ScoreV4均传入sink，与V1前向未透传sink的静态差异应分开看。RoPE路径和sink的每种组合仍需完整梯度验收。

## 稀疏窗口、外切与统计布局

atten_mask为BOOL/UINT8，True/1遮蔽，False/0参与；非TND可BNSS/B1SS/11SS/SS，TND只支持maxSq×maxSkv的SS。mask=None时全计算，mode与窗口无效。padding_mask预留，传None。

mode0默认完整mask、1自定义完整mask、2左上因果、3右下因果、4右下band、5非压缩prefix、6压缩prefix、7/8分别为mode3/2的模型外部Q切分。TND允许0/1/2/3/4/6/7/8，其余布局0..6；mode1/2/3/5/6忽略pre/next，mode0/4需mask和窗口匹配且band有交集，mode7/8不支持PSE。压缩mask形状、极性和外切前缀的完整解释参见[V1掩码合同](npu_fusion_attention.md)，V2另遵守本卡RoPE禁用mode6等专门条件。

prefix表示逐batch保留矩形宽度：Sq>Skv时[0,Skv]，否则[Skv-Sq,Skv]；prefix场景B≤32。inner_precise0/1保留、2开启无效行处理可能降低性能；mode3且Sq>Skv可自动开启，不能据此允许TND整行padding mask。长序列超时文档建议切轴，未提供通用安全尺寸。

q_start_idx/kv_start_idx为INT64列表，表示当前外切块在全局Q/KV序列中的起点，不是actual_seq累计长度。外切由模型完成，算子不会自动切分/通信；索引、mask及窗口应共同描述同一个块。

softmax_layout只能""或"TND"，后者只用于TND。文档在A2/A3称默认NTD、显式TND；950称默认BNS8、显式TN8，而两版包装TND物理分配均[T,N,8]，不能仅按逻辑名称reshape统计。更具体地，非950且无sink的V2后端调用没有softmax_layout参数，有sink及950才明确传same_as_input；因此不能将接受该关键字当成各路径都遵守其排布的证明。保持同版本前后向统计配套，并验实际排列。

## 随机数与发布实现差异

内部dropout helper在非950、keep_prob介于0和1时从默认NPU生成器philox_engine_inputs(10)获取随机元数据，覆盖显式seed/offset；主线950把获取动作移入非950条件，保留传入的seed/offset，发布实现则在950也覆盖它们。文档默认确定性及seed控制不能抹去这项版本差异，固定参数不代表跨提交复现同一mask。

外部mask为同版本_npu_dropout_gen_mask生成的UINT8打包数据，p=1-keep_prob，并传入对应seed/offset；生成接口与位序说明见[V1](npu_fusion_attention.md)。V2同样在非TND显式外部mask时跳过内部helper，局部numels没有赋值却返回；Autograd只保存后三项元数据，反向重新生成mask，不传原外部mask，因此存在元数据及外部dropout梯度的静态风险。

TND的numels按Nq*sum(Sq_i*Skv_i)累计，host实现相邻前缀差乘积，尾0跳过场景须额外检查；不能因为输入文档允许尾0就认证所有dropout组合。gen_mask_parallel/ sync涉及DSA副流与事件顺序，不直接保证提速。

C++在转大写前选择TND稀疏/累计长度校验，建议始终使用大写布局；非TND不要附带不匹配的实际长度列表，后端分支会依赖其非空性。V2入口明确设置is_fp8=False；同文件共享量化函数及UINT8/FP8 wrapper不代表此API可接量化QKV，不能混用npu_quant_fusion_attention的尺度与参数。

## Autograd、Meta与验证依据

Autograd对Q/K/V/PSE/Q_rope/K_rope/sink七个输入接入梯度；npu_fusion_attention_grad_v2返回dQ、dK、dV、dPSE、dQ_rope、dK_rope、dSink。前向七返回与反向七返回的用途和类型不同。无PSE/RoPE时Eager对应梯度为undefined；sink缺省时分配空FP32梯度占位，不作有效梯度使用。

两版Meta函数文本相同：前向按Q原shape分配输出，忽略Dv变化；TND统计也按[B,head_num,S1,8]分配，其中B实际取T、S1取Q的D，与Eager[T,N,8]不符，BSND的S1也未按Sq修正；numels恒0。反向对dpse/dq_rope/dk_rope调用torch.empty_like([0])，参数是Python列表，构成静态类型错误风险，且没有依据实际可选输入形状分配。未执行FakeTensor/编译，不能称已观察异常。

固定两个TorchAir的ge_converter源码目录均未检出npu_fusion_attention_v2文本；这是该转换目录的静态清单结果，不推广为所有后端/第三方都不存在支持。公开文档已经明确图模式/aclgraph不支持。

主线forward6个方法，其中5个限定910B、新增1个950只断言out_seed=100/out_offset=200；发布forward只有5个910B方法。两个版本grad均2个910B方法，CPU算出三项梯度但只断言dQ。基础输出有CPU比对、外部mask方法只验shape、复现方法只比同mask两次前向；没有RoPE/PSE各类型/sink/TND外切/Dv差异、外部mask反向的完整测试覆盖。文档四组调用仅打印示例结果，无断言，不能把显示的seed=0或数值当作当前所有版本的保证。

本卡为静态文档/实现/测试审阅，没有执行上游、设备、分布式或性能测试，无新增verified。部署验证应覆盖真实使用的全部输出和七类输入梯度，单独确认统计排布、显式随机元数据、外部mask及软件栈配套。

- [软件栈来源与适用性](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v2.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fusion_attention_v2.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_v2.py)（example）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_flash_attention_grad_v2.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionV2KernelNpuOpApi.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_v2.py)（example）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_flash_attention_grad_v2.py)（example）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
