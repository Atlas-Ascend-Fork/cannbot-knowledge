---
type: API
title: MLA Prolog v3 四路前处理（torch_npu.npu_mla_prolog_v3）
description: torch_npu.npu_mla_prolog_v3：推理场景下Multi-Head Latent Attention前处理的计算操作。 MLA 前处理有四条并行路径：Query 的非 RoPE 分量、Query 的 RoPE 分量、压缩 KV cache 与 RoPE key cache。 区分发布A3与主线A2/A3/950的量化组合、别名、ABI、可选输出及图转换和测试边界。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mla_prolog_v3.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MlaPrologV3KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MlaPrologV3KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog_v3.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog_v3.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_mla_prolog_v3
---


# npu_mla_prolog_v3：版本化量化、Cache与图适配

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_mla_prolog_v3(token_x, weight_dq, weight_uq_qr, weight_uk, weight_dkv_kr, rmsnorm_gamma_cq, rmsnorm_gamma_ckv, rope_sin, rope_cos, kv_cache, kr_cache, cache_index=None, dequant_scale_x=None, dequant_scale_w_dq=None, dequant_scale_w_uq_qr=None, dequant_scale_w_dkv_kr=None, quant_scale_ckv=None, quant_scale_ckr=None, smooth_scales_cq=None, actual_seq_len=None, k_nope_clip_alpha=None, rmsnorm_epsilon_cq=1e-05, rmsnorm_epsilon_ckv=1e-05, cache_mode='PA_BSND', query_norm_flag=False, weight_quant_mode=0, kv_cache_quant_mode=0, query_quant_mode=0, ckvkr_repo_mode=0, quant_scale_repo_mode=0, tile_size=128, qc_qr_scale=1.0, kc_scale=1.0) -> (Tensor, Tensor, Tensor, Tensor, Tensor)
```

本卡聚焦 A3、非量化 weight_quant_mode=kv_cache_quant_mode=query_quant_mode=0：融合投影、RMSNorm、RoPE 和 Cache 原地写入，返回 (query,query_rope,dequant_scale_q_nope,query_norm,dequant_scale_q_norm)。后几项仅在对应请求/量化模式有效，不因元组有五项就全部消费。

## 参数与组合限制

- He 只支持 7168/7680，Hcq=1536、Hckv=512、D=128、Dr=64、Nkv=1；N∈{1,2,4,8,16,32,64,128}。token_x 为连续 BF16 ND 的 (T,He) 或 (B,S,He)。
- 下采样及 Q 上采样权重为连续 BF16 FRACTAL_NZ：weight_dq=(He,1536)、weight_uq_qr=(1536,N*(128+64))、weight_dkv_kr=(He,512+64)；weight_uk 为 ND 的 (N,128,512)。gamma、sin/cos 为 BF16、尺寸匹配对应分支。
- 非量化 query 输出 (T,N,512) 或 (B,S,N,512)，query_rope 尾维 64；query_norm_flag=False 时 query_norm 为 shape=[0] 占位，非量化的反量化 scale 输出不作为有效量化参数使用。
- PA_BSND/PA_NZ 的 cache_index 为 INT64 token 偏移、范围 [0,BlockNum*BlockSize)；PA_BLK_* 改为块索引 [0,BlockNum)，合轴时还必须传 INT32 的累计 actual_seq_len。BSND/TND 模式不需 cache_index。来源不校验这些值，调用方保证合法。
- block_size 为 [16,1024] 内 16 倍数；Cache 尺寸/格式按具体模式配套。量化各模式的 weight/scale/Cache 组合不能任意混合；来源参数段只列 weight_quant_mode=0/1/2，但场景表出现 3，本卡不把该分歧合成无条件开放模式 3。

## 验证与模型关联

用四条显式投影/归一化/RoPE 路径对比 Q、Q_rope 和 Cache 修改；检查 NZ 权重、索引单位及可选输出占位，再按目标量化模式另做专项验证。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py#L1309)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 固定版本与主线扩展

上文保留发布A3非量化子集。完整固定来源为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda；TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013、主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c。发布属于ascend_26_0_pt28；主线软件配套未知，不能凭提交日期互相搭配。

发布产品表只有A3推理；主线增加A2/A3和Ascend950系列（包含旧称Atlas A5）PR/DT。主线明确A2/A3不支持FP8、HiF8、MXFP8全量化及E8M0尺度，不因通用dtype表列出这些类型就扩大产品范围。

V3普通Schema明确两个Cache为Tensor(a!)/Tensor(b!)原地突变，cache_index移到关键字区且可None。公开返回(query,query_rope,dequant_scale_q_nope,query_norm,dequant_scale_q_norm)，不返回Cache；与[V2](npu_mla_prolog_v2.md)的尺度第五项和两个Cache返回位置不同。原型文字没有写出的*不等于Schema允许把其后参数继续按位置传入。实际关键字为kv_cache_quant_mode，转换器NB注释中的kv_quant_mode不是可调用参数名。

## 输入维度、RoPE与Cache寻址

token_x为ND[T,He]或[B,S,He]；三个融合权重DQ、UQ-QR、DKV-KR为FRACTAL_NZ[He,Hcq]、[Hcq,N*(D+Dr)]、[He,Hckv+Dr]；weight_uk为BF16 ND[N,D,Hckv]。gamma为BF16[Hcq]/[Hckv]、sin/cos为BF16[T,Dr]或[B,S,Dr]。文档全部这些输入不支持非连续；NZ需真实格式转换，不用view代替。

主线He可1024/2048/3072/4096/5120/6144/7168/7680/8192，Hcq1536/2048，D128/192；发布仅He7168/7680、Hcq1536、D128。两版Hckv512、Dr64、Nkv1，N为1/2/4/8/16/32/64/128；B0..65536，S与合轴T不限制。BlockSize为16..1024内16倍数，BlockNum按ceil(B*Skv/BlockSize)描述，不把S/T无限制解释成显存无界。

RoPE主线补充interleave-half：先取x[...,::2]、x[...,1::2]并拼接为前后半，再按拼接正负半和sin/cos计算。文字“奇数/偶数位”易因零/一基下标混淆，按公式索引核对；不能把普通half版RoPE直接替代这一重排。

|cache_mode|Cache逻辑shape|cache_index|
|--|--|--|
|PA_BSND / PA_NZ|[BlockNum,BlockSize,1,Dtile]，KR尾轴Dr|INT64[T]或[B,S]，每token线性槽位[0,BlockNum*BlockSize)|
|PA_BLK_BSND / PA_BLK_NZ|同上|INT64[sum(ceil(S_i/BlockSize))]或[B,ceil(S/BlockSize)]，每项是块号[0,BlockNum)|
|BSND|[B,S,1,Dtile]，KR尾轴Dr|不需传|
|TND|[T,1,Dtile]，KR尾轴Dr|不需传|

BS合轴的PA_BLK路径还必须传actual_seq_len=INT32[B]累计前缀长度，不是各条独立长度列表。文档不检查这些索引/长度值合法性，调用方确保真实token、容量与分页管理一致；普通槽位与块号不能混用。

Dtile在主线pertoken-pergroup模式记656，其余512；发布称per-tile并写“非per-tensor为512”，存在措辞歧义，不据此推导per-tensor另一个任意大小。656是文档逻辑合同，不是授权按测试自行拼内部cache/scale字节协议。PA模式允许B0/Skv0相关空Cache，BSND/TND不支持空Cache，Nkv0始终不支持；RoPE支持B/S/T0相关空输入。不同空分支仍需后端验收，不能将V1/V2空输入行为直接搬来。

## 主线量化组合与发布差异

令W=weight_quant_mode、K=kv_cache_quant_mode、Q=query_quant_mode。模式必须按组合选择：

|组合|数据/尺度与输出要点|
|--|--|
|W0,K0,Q0|BF16非量化|
|W1,K0或K2或K3,Q0|仅UQ-QR权重INT8；K2两Cache INT8，K3仅KV为分组INT8、KR BF16，query仍BF16|
|W2,K0,Q0|token及三权重INT8，Cache和query BF16|
|W2,K1,Q1|token/三权重INT8、KV INT8、KR BF16，query INT8及逐token/head FP32尺度|
|W2,K3,Q0|INT8全量化、KV分组INT8、KR/query BF16|
|W3,K0或K1或K3|950 MXFP8：token/三权重E4M3、E8M0分组尺度；K1/Q1时KV与query E4M3，否则query BF16|
|W4,K0或K1或K3|950 FP8：E4M3数据及FP32尺度；K1/Q1时KV与query E4M3，否则query BF16|
|W5,K0或K1或K3|950 HiF8及FP32尺度；K1/Q1时KV与query HiF8，否则query BF16|

W3/4/5的K0与K3搭Q0，K1搭Q1。公开weight_uk始终BF16，不因量化参数描述提及它就将其量化。K2仅列部分量化组合，不能与任意W全量化做笛卡尔积。

发布文档多处枚举与其参数表不一致：部分K2写W2、部分K3写W3、全量K3写W3/Q1，却描述INT8输入；主线修正为W1及W2/4/5等组合。发布实现已有W3入口，但公开产品没有950/MX支持，不能以宽包装认证发布完整MX能力。

主线仍有文档冲突：英文W1/K3段要求quant_scale_ckv，中文段及参数/类型表写无需传；W2/4/5,K3,Q0段声称query量化，而dtype表及Eager分配均为BF16；Q反量化尺度参数段按W2..5统称有效，场景表/实现实际只在K1生成。卡片保留差异，不拼成新的未公开组合。

## 尺度形状与存储配置

|尺度|W1/2/4/5|W3 MXFP8|
|--|--|--|
|dequant_scale_x|W2/4/5为FP32[T,1]或[B*S,1]，W1无|E8M0[T,He/32]或[B*S,He/32]|
|dequant_scale_w_dq|W2/4/5 FP32[1,Hcq]，W1无|E8M0[Hcq,He/32]|
|dequant_scale_w_uq_qr|FP32[1,N*(D+Dr)]|E8M0[N*(D+Dr),Hcq/32]|
|dequant_scale_w_dkv_kr|W2/4/5 FP32[1,Hckv+Dr]，W1无|E8M0[Hckv+Dr,He/32]|
|smooth_scales_cq|FP32[1,Hcq]，具体场景可选|无需传|

发布dequant_scale_x还写[T]，smooth写[1,Hcq]或[1]；主线收为[T,1]/[B*S,1]及[1,Hcq]，不能跨版本只换提交号而保留旧shape。E8M0存储的是共享指数，不能当普通FP32尺度cast或直接逐元素数值乘。

K1的quant_scale_ckv为FP32[1]；K2为FP32[1,Hckv]，并需quant_scale_ckr=FP32[1,Dr]；K3不传这两项，采用每token每group量化。k_nope_clip_alpha=FP32[1]在部分及INT8/FP8/HiF8分组模式中使用，MX表不列。tile_size默认128、仅K3有效。ckvkr_repo_mode=0/1分别存两个Cache或合并存储；quant_scale_repo_mode=0/1分别存尺度或与数据合存。这些配置会改变实际Cache解释，须由同版本上下游配套消费，不靠逻辑shape推导字节拼接。

qc_qr_scale、kc_scale为Q/K尺度修正，默认1；不能与反量化scale交换。CPU测试参考只在部分路径应用它们，不能由参考代码自动建立所有量化分支的精确公式。

## 可选输出与Meta差异

query与query_rope的shape为[T,N,Hckv/Dr]或[B,S,N,Hckv/Dr]；query_rope始终BF16。Eager按W2/3/4/5且K1分配量化query与FP32[T,N,1]/[B*S,N,1]尺度，分配条件本身不检查Q是否1，所以形状成功不代表其他Q枚举合法。

query_norm_flag=True时返回RMSNormCq后的低秩中间值[T,Hcq]或[B,S,Hcq]，位于UQ投影前；文档将其对应公式qC，但形状与实现表明是cQ，不能当[T,N*D]投影输出。它的dtype随UQ权重，HiF8用容器解释；W1/2/4/5另有FP32[T,1]/[B*S,1]尺度，W3为E8M0[T,Hcq/32]/[B*S,Hcq/32]。flag=False时两项无效，W0即便flag=True也没有有效量化尺度。

主线文档把无效输出写nullptr，Eager两版在返回前却把undefined换为shape[0] Tensor；Python不应据文字判断为None。W3空norm尺度仍保留E8M0 dtype。Meta根据CANN阈值在新版本给[0]、旧版本给[1]占位，而C++两版最终都补[0]，因此旧CANN的Meta/Eager占位shape不能假定一致。占位Tensor不是数值为1的尺度。

## CANN ABI、HiF8与顺序依赖风险

两版都用IsGteCANNVersion判断8.5.0.alpha003：达到阈值时调用aclnnMlaPrologV3WeightNz省去query_norm_flag参数，旧版则传入。它是同名符号的ABI分支，不是缺符号自动回退；固定CANN与TorchNPU/OpPlugin配套必须核验，不能单独升级一个库。

主线W3先要求AclnnOnly，并对四个反量化输入要求原生torch.float8_e8m0fnu；TorchNPU≤2.6明确拒绝、≥2.7编译分支检查dtype。发布W3则把scale容器通过TensorWrapper强制解释为ACL_FLOAT8_E8M0，TorchAir发布也做四个Bitcast；这不表示可以在主线继续传INT8普通尺度。两者都不是普通数值类型转换。

主线W5任一输入是UINT8时，要求四个输入dtype override都为HiF8；K1/K3还要求KV Cache override=HiF8，再用wrapper解释字节。TorchAir主线逐字段Bitcast且补输出desc，未复现所有Eager一致性检查；不能用图转换成功替代参数完整性验证。

主线C++的is_hifloat8_dtype是文件作用域全局量，在普通V3和functional的HiF8路径置true，全文未按调用重置；后续输出dtype和wrapper选择依赖它，而Meta使用每次重置的局部变量。这是同进程切换量化模式及并发的静态状态风险，尚无运行复核，不能写成已观察故障或把任意混合调用当安全路径。

## 原地、functional与GE输出次序

普通V3原地更新两个Cache、公开返回五输出。functional无突变Schema，Eager先clone两Cache，返回原五项后再附更新的两个副本；不能按普通V3次序直接解包七项，输入不变与返回存储隔离也应独立验证。

TorchAir functional用两次ge.TensorMove再调用同一GE节点，普通转换器则使用输入Cache。底层ge.MlaPrologV3原始七输出次序为(query,query_rope,KV,KR,Qscale,query_norm,normscale)，和functional公开次序不同。它们属于不同层的接口，不能直接以raw GE元组索引替换torch_npu索引。Schema别名和框架输出处理需与所用转换器配套，不把原始七输出自动定性为五输出API错误。

两版原始GE IR字符串仍主要列INT8/BF16，没有完整列FP8/HiF8/E8M0，而主线转换器有HiF8处理；这类层间描述差异须核对实际后端。functional复制两Cache会增加数据搬运及内存需求，源码不能证明这些开销已被编译消除或被融合收益抵消。

## 测试覆盖与实际复核

两版测试1150行、发布仅96行空白差异，四个方法全部无条件skip：两个A2 INT8/K1（普通与functional）和两个950 MX/K1，均B2/S1/He7168/Hcq1536/N32/D128、PA_BSND、BlockSize128。普通方法使用clone Cache保护独立参考，优于V2调用后复制已修改输入的做法；但没有断言query_norm或其尺度，也没有functional输入不变/alias对照。

MX测试仍传四个INT8尺度，与主线原生E8M0检查不符，不能作为主线合法用例。MX CPU参考还没应用调用时10倍qc_qr_scale/kc_scale；量化helper的nearest分支引用未定义round_abs，默认rint没有触发，不作为通用可运行MX量化库。四个方法的存在均不构成已执行精度结果。

没有测试覆盖主线HiF8、FP8、模式切换的全局状态、16种dtype组合、可选norm输出、BLK/BSND/TND、合并Cache/尺度、空输入、图回放或性能。文档图样例只是打印、复用同一原地Cache，日志开关也仍是普通Python变量，不提供独立精度或收益证据。

真实验收应先按固定产品和ABI选择合法组合，再用独立初始Cache分别运行Eager/图/functional，检查五或七输出、未写槽位、真实索引单位、量化误差与内存/时延。本次仅静态审查，没有执行上游、设备、图、分布式或性能实验，无新增verified。

- [V1维护入口](npu_mla_prolog.md)
- [V2非标准Cache突变](npu_mla_prolog_v2.md)
- [模型Cache图适配](../../optimizations/rules/graph_mode_kvcache_inplace_mla_prolog_adaptation.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### MLA Prolog v3 四路前处理：torch_npu.npu_mla_prolog_v3

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

推理场景下Multi-Head Latent Attention前处理的计算操作。

### 输入、输出与行为

MLA 前处理有四条并行路径：Query 的非 RoPE 分量、Query 的 RoPE 分量、压缩 KV cache 与 RoPE key cache。它们分属 Query 和 KV 两侧，不能因接口名称相近而套用 v2 的五路输出清单。

### 文档签名

```text
torch_npu.npu_mla_prolog_v3(token_x, weight_dq, weight_uq_qr, weight_uk, weight_dkv_kr, rmsnorm_gamma_cq, rmsnorm_gamma_ckv, rope_sin, rope_cos, kv_cache, kr_cache, cache_index=None, dequant_scale_x=None, dequant_scale_w_dq=None, dequant_scale_w_uq_qr=None, dequant_scale_w_dkv_kr=None, quant_scale_ckv=None, quant_scale_ckr=None, smooth_scales_cq=None, actual_seq_len=None, k_nope_clip_alpha=None, rmsnorm_epsilon_cq=1e-05, rmsnorm_epsilon_ckv=1e-05, cache_mode='PA_BSND', query_norm_flag=False, weight_quant_mode=0, kv_cache_quant_mode=0, query_quant_mode=0, ckvkr_repo_mode=0, quant_scale_repo_mode=0, tile_size=128, qc_qr_scale=1.0, kc_scale=1.0) -> (Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mla_prolog_v3.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mla_prolog_v3.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MlaPrologV3KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MlaPrologV3KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mla_prolog_v3.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mla_prolog_v3.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
