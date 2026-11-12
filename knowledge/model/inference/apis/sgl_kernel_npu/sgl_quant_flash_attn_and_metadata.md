---
type: API
title: SGLang QFA的MXFP8尺度布局与配套调度接口
description: 说明950/CANN9.2量化GQA尺度与metadata合同，并区分dff源码的9.1版本声明、0/1/6实现事实及部署身份缺口。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/quant_flash_attn.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/quant_flash_attn_metadata.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/quant_flash_attn_metadata.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/quant_flash_attn.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/docs/torchapi_quant_flash_attn.md
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/version.cmake
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/torch_extension/quant_flash_attn.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/torch_extension/csrc/quant_flash_attn.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_api/aclnn_quant_flash_attn.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_host/checkers/quant_checker.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_host/checkers/metadata_checker.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_host/checkers/sinks_checker.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_host/arch35/quant_flash_attn_tiling_mxfp8.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_host/qfa_adjust_sinner_souter.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/quant_flash_attn.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_common_def.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_kernel_mxfp8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_block_cube_mxfp8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_block_vec_mxfp8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_block_cube_hif8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_block_vec_hif8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn/op_kernel/arch35/quant_flash_attn_block_vec_fp8.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/common/op_kernel/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_dn.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn_metadata/op_host/op_api/aclnn_quant_flash_attn_metadata.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn_metadata/op_kernel_aicpu/quant_flash_attn_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/dff221330eecd2132233b1e73ed1072cd8925140/attention/quant_flash_attn_metadata/op_kernel_aicpu/quant_flash_attn_metadata_aicpu.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- '950'
cann_versions:
- 9.2.0
aliases:
- quant_flash_attn
- quant_flash_attn_metadata
---

# SGLang QFA的MXFP8尺度布局与配套调度接口

## 接口原型

```python
from sgl_kernel_npu.operators.attention import quant_flash_attn

def quant_flash_attn(
    q,
    k,
    v,
    q_descale,
    k_descale,
    v_descale,
    quant_mode,
    *,
    block_table=None,
    p_scale=None,
    cu_seqlens_q=None,
    cu_seqlens_kv=None,
    seqused_q=None,
    seqused_kv=None,
    sinks=None,
    attn_mask=None,
    metadata=None,
    softmax_scale=1.0,
    mask_mode=0,
    win_left=-1,
    win_right=-1,
    max_seqlen_q=-1,
    max_seqlen_kv=-1,
    layout_q="BSND",
    layout_q_descale="BSND",
    layout_kv="BSND",
    layout_out="BSND",
    return_softmax_lse=False,
    impl="auto",
):
    ...
```

```python
from sgl_kernel_npu.operators.attention import quant_flash_attn_metadata

def quant_flash_attn_metadata(
    num_heads_q,
    num_heads_kv,
    head_dim,
    quant_mode,
    *,
    cu_seqlens_q=None,
    cu_seqlens_kv=None,
    seqused_q=None,
    seqused_kv=None,
    batch_size=None,
    max_seqlen_q=-1,
    max_seqlen_kv=-1,
    head_dim_v=None,
    mask_mode=0,
    win_left=-1,
    win_right=-1,
    layout_q="BSND",
    layout_q_descale="BSND",
    layout_kv="BSND",
    layout_out="BSND",
    is_grad_enabled=False,
    impl="auto",
):
    ...
```

## 依赖和量化语义

`auto`与cann_ops_transformer选择同一实现，无自动回退。仅arch35注册，要求CANN9.2.0、匹配Torch/torch_npu及单独安装导出QFA两个接口的cann_ops_transformer扩展；只安装sgl_kernel_npu不能提供全部依赖。

本卡覆盖独立参考支持的MXFP8 quant_mode=1：Q/K/V为FP8 E4M3，scale为E8M0，字节e表示2^(e-127)，255为NaN。Q/K沿通道每32值共用scale，V沿序列每32位置、每通道共用scale。末维2存相邻两组scale。p_scale还将softmax中间P舍入FP8；仅反量化Q/K/V后跑高精度attention不能模拟该精度边界。

Q为 `[T,Nq,D]`，D=64/128/256，Nq是Nkv的整数倍；KV为PA_BNBD `[P,Nkv,S,D]`，页大小S仅允许64/128/256/512/1024。Q scale为TND `[T,Nq,D/64,2]` 或N2TGD `[Nkv,T,G,D/64,2]`；K scale `[P,Nkv,S,D/64,2]`；V scale `[P,Nkv,S/64,D,2]`。Q/output须显式TND、KV显式PA_BNBD；默认BSND不能直接用于该子集。int32页表和Q累计边界、KV有效长度实际必需，所有tensor同NPU并遵守连续性/非零stride约束。

scale默认1.0，通常显式D^-0.5；p_scale应有限正值，集成常用1。mask0为decode无mask、3按KV尾部右对齐causal，并给标准int8 `[2048,2048]` mask。参考不支持sink/任意mask/非默认窗口，不把更宽CANN透传能力宣称为已独立验证。

## 返回和metadata

主调用返回BF16 `[T,Nq,D]` 与FP32 LSE，开启时 `[Nq,T]`、关闭时 `[0]`，输入不改。参考对padding Q、零KV或完全屏蔽行输出0，LSE相应+inf。

`quant_flash_attn_metadata(heads_q,heads_kv,head_dim,quant_mode,...)` 接受同设备连续int32长度，返回不透明NPU int32 `[2,max_schedule_size]`，不构造页表、不追加投机步偏移、不从shape推导设备长度。head_dim_v默认head_dim且本路径两者相等。auto/cann_ops_transformer主调用前必须生成并传入匹配的metadata，原型的metadata=None不表示该默认CANN路线可省略；torch_native数值参考不读取metadata。所有head/长度/量化/mask/布局须与主接口一致；参数不变时多层可共享，长度变化由调用者重建。

metadata无独立torch_native，auto与显式CANN是同一实现不能互为golden。CPU数值参考包含分块online softmax、ln2对齐最大值与P的FP8转换，忽略硬件调度；正确性需通过主接口消费metadata后组合验证。本卡不宣称graph重放已验收。

## 外置metadata绑定与透传边界

固定SGL metadata包装的auto与`cann_ops_transformer`直接绑定同一函数，arch35注册之外没有在函数体内检测CANN版本、转换dtype/contiguous、读取设备长度或构造页表。首次导入外置`cann_ops_transformer.ops.quant_flash_attn_metadata`后缓存callable，输入参数原样透传；文档中的同设备int32、长度值域与布局约束仍需由caller和匹配扩展保证，不能误写为该Python层已逐项校验。

`batch_size=None`、`head_dim_v=None`也由本层原样交给厂商函数，默认解释与输出分配都在所安装扩展中；`is_grad_enabled`默认False是独立推理调度属性，不能据本卡参数存在推导训练或反向支持。缺包/缺符号不会回退数值参考。

该外置扩展与sgl_kernel_npu wheel分开安装，不能用wheel内另一个ops-transformer profile的e7da固定提交替代实际安装版本。公开SGL说明的v9.2.0链接表达所需API版本，不构成已安装二进制与某源码commit一致的证明；取得匹配扩展的版本/构建来源前，本卡保留接口事实，不宣称已闭合metadata CPU实现或全部QFA Device链路。


## 固定 dff 源码案例与版本边界

下文新增的是公开 Git Reference 案例，固定到 ops-transformer 的 dff221330eecd2132233b1e73ed1072cd8925140，不能当成上文 CANN9.2 部署的完整 Operator 验收。SGL 文档要求9.2并指向官方 v9.2.0 文档链接，但该 tag 本轮解析到的 dff 的 version.cmake 实际声明9.1.0；这两项发布证据同时保留。SGL 的另一个 bundled e7 profile没有绑定此处外置wheel，不能用它消除冲突。当前没有与已安装扩展相互核实的SDK、编译器、驱动及构建来源，未建立二进制同源或9.2兼容结论。

在这份源码中，vendor Python→C++分别调用 aclnnQuantFlashAttnMetadata 与 aclnnQuantFlashAttn 两段式pair；主API再转generated aclnnInnerQuantFlashAttn，metadata API创建独立executor并以CommonOpExecutorRun提交AICPU节点。主C++新建BF16 O及FP32 LSE（关闭为[0]），metadata Python新建当前NPU上的INT32 [2,R]。SGL只缓存外置函数并透传，不在自身检查或实现这条Device数学。

## dff 的量化模式、布局与实际数学

令G=Nq/Nkv，对query头h使用KV头floor(h/G)。下表的反量化表达式定义量化轴；实际kernel将scale融入Cube或Vector，不等于创建完整FP32 Q/K/V副本再调用普通attention。

| dff主Host允许模式 | 数据与反量化轴 | Q/KV/O布局及scale布局 | 核心区别 |
|---|---|---|---|
| 0 HIF8 | q/k/v HIFLOAT8；三个FP32 [1] per-tensor scale；score=softmax_scale*sQ*sK*dot(q8,k8)，PV结果再乘sV | Q/KV/O同为TND、BSND或BNSD；layout_q_descale=BSND；D=Dv=128 | C++可把uint8包装成ACL_HIFLOAT8，不能将存储byte当E4M3数值 |
| 1 MXFP8 | Q/K沿D每32元素scale；V沿序列每32位置、每通道scale，E8M0字节定义沿用上文 | Q/O=TND；KV=TND、PA_BBND、PA_BNBD或PA_NZ；Qscale=TND或N2TGD | Cube使用Q/K/V block scale；Qscale布局决定prefill或decode实际内核，非仅转置接口标签 |
| 6 FP8 GQA | Q/K E4M3 per-token-head、FP32 Qscale[Nq,T]与Kscale[pages,Nkv,H]；V E4M3 per-head、FP32 Vscale[Nkv] | Q=NTD[Nq,T,D]、Qscale=NT、KV=PA_BNBD、O=TND；H=128、D=Dv=128 | Q/Kscale在Vector softmax前相乘，Vscale在PV在线更新/末归一化中消费，不在多个阶段重复乘 |

主Host的QuantChecker支持集合严格为{0,1,6}。Python枚举列0…9、主Python和C++还有mode5 uint8/MXFP4包装及输出末维×2分支，但mode5会在该Host检查被拒绝；这些包装不是一条已公开可执行的MXFP4 Device算法。内部key的MXFP8 decode值2由公开mode1映射而来，不能据此认为公开quant_mode=2通过Host。

原API中独立数值参考仍只覆盖mode1的既定子域，不自动扩大到dff的0/6、D72或其它布局。dff Doc对MXFP8列D=64/72/128/256，D72不允许PA_NZ；标准q/k/v/O物理维非零，0<B<65536、1≤Nq,Nkv≤256、G为正整数且≤64。合法有效长度为0与物理空tensor不同。

MXFP8分页的页大小H仅允许64/128/256/512/1024；满足H/64的整除条件不足以替代此集合限制。附加scale布局中，PA_NZ的Kscale为[pages,Nkv,H/16,ceil(D/64),16,2]，Vscale为[pages,Nkv,D/16,H/64,16,2]；数据本身为[pages,Nkv,D/32,H,32]。非PA TND Vscale第一维是Σ_b ceil(kv_alloc_len_b/64)，不是把全局KV_T直接整除64；每batch的scale基址独立对齐，batch尾部不能无缝拼成同一32元素量化组。PA_BBND则按[pages,H,Nkv,...]解释对应scale轴，不能把PA_BNBD的stride原样套入。

## dff 的分块数据流与中间精度

实际entry为单MIX_AIC_1_2 launch：AIC的QK/PV与AIV的scale、mask、online softmax、P转换和输出更新在同kernel交接。MXFP8的TND Qscale选择prefill/useDn，N2TGD选择decode/S1G merge；Host将公开mode1编码成相应内部1/2。标准CV1:2配置下M128，D64/72/128用S2=512，D256用S2=256；HIF8/FP8用S2=256。这里是固定source的tile选择，不是性能优劣结论。

MXFP8的ExecuteTask先按subLoop做当前QK/Vector1，再消费延迟的PV/Vector2；D128等512列块会拆成两subloop。Cube把Q/K及E8M0 scale送入相应Mmad，FP32结果到AIV；Vector求FP32 max/sum/exp、把P转换成8bit并以NZ写回L1，Cube再做PV，Vector累计历史输出，最后除sum并转换BF16。P的舍入位于两次矩阵乘之间，FP32 sum并不是对舍入后P重新求和，所以“先反量化后普通高精度attention”不能复现全部中间精度。

prefill DN使用ProcessVec1VfDnMxfp8，源码将当前最大值作ceil(max/ln2)*ln2后再减ln(p_scale)，两subloop以exp(旧max−新max)合并sum；还生成E8M0补偿scale放在L1 P区域之后供PV消费。decode走独立ProcessVec1Nd路径。该E8M0中间补偿不是caller提供的Q/K/V descale，也不意味着接口公开mode改变；不能只保留一个“P乘p_scale”而删除max、sum、历史u和补偿scale的相互关系。

mode6的ProcessVec1DnPerTokenHead加载当前Q/K scale，按其乘积修正分数；ProcessVec2读取runInfo.n2Idx对应Vscale再更新/归一化。HIF8则SetDescaleQK保存两个scalar乘积、SetVScale保存V scalar。二者均不能把Vscale误放到QK score中。

另有可复验的文档/实现差异：mode0的公开枚举名写P_FP8_E4M3，但本dff实际quant_flash_attn_hif8将INPUT_T设为hifloat8_t，ProcessVec1VfDnHif8的T2也为该类型，Cast<T2>生成HIFLOAT8 P，Cube PV使用INPUT_T×INPUT_T。本文保留真实类型链，不把枚举名替代body，也不推定其他版本或部署wheel相同。mode1/6的P为E4M3；具体指令舍入、饱和与未mask读取的SDK契约仍需匹配构建来源后再做完整闭包。

## dff metadata 的生产、消费与生命周期

vendor Python在layout_q="TND"时先要求batch_size必须为None，即便显式值与长度一致也拒绝。通过该准入后按seqused_q.shape[0]、cu_q.shape[0]−1、显式batch_size的顺序估计B；其中显式batch_size分支仅适用于非TND布局；未知/非正估计以1用于容量规划。令硬件查询得到Cmax/Vmax，则单行
R=align4096(16+16*(Cmax+Vmax)*B_estimate*Nq)，分配[2,R]。无NPU的meta/fallback路径使用36/72默认值；真机属性查询失败向外抛出。该分配上界不能当成实际section数量。

ACLNN metadata API优先查询当前线程的有效C/V资源，查询失败回退平台核数；把输出ViewShape的维数和行距作为attr交给AICPU，避免把flatten StorageShape当二维row stride。AICPU依次Prepare→ParamsInit→SectionStreamK::Compute→GenMetaData，以seqused优先、cu差分次之/累计表示处理各batch有效长度。layout_q_descale=N2TGD时以Nkv调度合并G，其它按Nq；只有quant_mode1开启FD规划。它仍不生成page table，不替调用方保证任意设备索引/长度内容正确。

设实际section数s、有效AIC数C、AIV数V。第一行的定义前缀长度L=16+s*(C+V)*16个uint32；FA起点word16，FD起点word16+s*C*16，record stride16。GenMetaData在shape信息有效时检查L≤R；shape完全不可用的旧调用边界跳过容量检查，不能概括成所有路径都已验容量。

| 第一行部分 | word/record位置 | 实际生产消费含义 |
|---|---|---|
| header | 0 | sectionNum |
| header | 1 | 是否存在FD任务；不是“每个core都有FD” |
| header | 2/3 | M/S2基础块；必须与主核配置一致 |
| header | 4/5 | C/V，决定FA/FD区间与每section步长 |
| header | 15 | needInitOutput，来自零长/Query padding/causal q>kv检查 |
| FA record | 0/1/2 | BN、M、S2起游标 |
| FA record | 3/4/5 | BN、M、S2终游标 |
| FA record | 6 | 当前core首个FD workspace slot |
| FD record | 0/1 | BN/M索引 |
| FD record | 2/3 | 首workspace slot及分片数 |
| FD record | 4/5 | 归并起始M行及行数；主核mLen>0才使用 |
| 其余record字 | 当前定义区内 | Clear先置0，未赋值字段保持0；不能解释成其它版本字段 |

主MXFP8 Init直接解析header、FA/FD记录和needInitOutput；section内FA写片输出与sum/max，AIV在FD之前及之后各SyncAll，后一个屏障阻止同section片workspace被下一section提前覆盖。FD的静态UB区在FA transient区内分时复用，固定源码有容量static_assert；这不是两套UB同时求和，也不是任意自定义metadata可以安全消费的证明。

needInitOutput为真时Vector分核把O清0、开启LSE清+Inf，再处理有效任务；不能把它写成每个tensor都预清或所有非法metadata都有数值fallback。第一行只清/写实际L前缀，尾[R−L]无初始化承诺；is_grad_enabled=False时第二行也没有有效FAG数据。True路径只允许mode0，按第二行起点R写FAG确定性轮次；这里不据一个字段宣称反向算子已闭合。

metadata、page table、长度与scale输入由caller保留至主kernel所在stream完成。独立metadata executor必须先完成写出再由主executor读取，同stream顺序或明确跨stream事件不能省略；长度、量化模式、head、布局、资源配置、mask变化后须重新匹配。虽然本案例与FlashMLA也出现16word header，二者tile、mode、record解释和两行ownership合同不构成跨算子可互换ABI；更不能复用SparseFlashMLA的1360word协议。

## dff 可用 Guard 与不可外推项

| 边界 | 固定dff可见行为 | 集成含义 |
|---|---|---|
| 主metadata | INT32/ND，rank1或2且dim0>0；存在性强制 | 这些是浅shape检查，不验证所有header、record或rank2行距值 |
| mask/sink | Doc当前mask0/3、window均−1；有效sink被SinksChecker拒绝；[0]sink在ACLNN先转nullptr | 不能用内部sink helper或MaskMode枚举4宣称公开可用 |
| p_scale | Host只查FP32 ND [1]，未读取其值 | 有限正值是ln(p_scale)数学前提，不能声称该Host已校验finite/positive |
| 非连续KV及scale | Python拒绝stride0；ACLNN检测weak NnopbaseSupportTensorV2的存在，旧包拒绝非连续；PA允许轴还由layout检查限制 | “接口支持view”依赖实际opbase，不能假设所有同名版本包接收 |
| 输出 | 主C++跟q.options创建BF16 O/FP32 LSE；metadata Python device="npu" | caller要使当前NPU、输入设备和两executor资源域一致，不虚构C++DeviceGuard |
| 输入内容 | 主Tiling不读取长度、page table、mask全部值；Doc要求caller保证 | shape合法不等于索引、page容量、scale值或跨调用配置已验证 |
| 环境 | dff packageversion9.1与SGL9.2要求冲突；SDK/driver/compiler/wheel映射仍未固定 | 本次只是局部源码Reference，未生成完整CV Operator，不宣称source_closed、运行正确、速度或兼容性 |

上述局部实现事实可用于解释scale重排、P中间舍入、负载均衡和buffer复用的必要条件；不替代匹配部署环境中的完整Host/Device/SDK闭包。这里没有补造不可见算法body，0/1/6主体文件可读，尚未完整验收的是版本/包身份及全路由资源与primitive合同。


## 证据与复核范围

本卡保留SGL固定提交的950/CANN9.2接口合同，并增量加入明确限定的dff源码案例；后者的packageversion冲突与部署映射缺口保持可见，不将它升级为CANN9.2完整算子证明。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
