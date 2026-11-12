---
type: API
title: SGLang MLA Prolog V4 的五输出、无RoPE与量化边界
description: 说明CANN9.2 V4五输出与双缓存、16量化组合的平台和Host约束，以及七输出functional、GE拷贝与原地恢复边界。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/mlaprolog_v4.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/mlaprolog_v4.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/docs/aclnnMlaPrologV4WeightNz.md
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/version.cmake
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_api/aclnn_mla_prolog_v4_weight_nz.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_api/aclnn_mla_prolog_v4_weight_nz.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/torch_extension/mla_prolog.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/torch_extension/csrc/mla_prolog.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/torch_extension/graph_convert_mla_prolog.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_def.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling_check.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling_check.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_infershape.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
cann_versions:
- 9.2.0
---

# SGLang MLA Prolog V4 的五输出、无RoPE与量化边界

## 接口原型

```python
from typing import Optional, Tuple

import torch

from sgl_kernel_npu.operators.attention import mlaprolog_v4

def mlaprolog_v4(
    token_x: torch.Tensor,
    weight_dq: torch.Tensor,
    weight_uq_qr: torch.Tensor,
    weight_uk: torch.Tensor,
    weight_dkv_kr: torch.Tensor,
    rmsnorm_gamma_cq: torch.Tensor,
    rmsnorm_gamma_ckv: torch.Tensor,
    kv_cache: torch.Tensor,
    kr_cache: torch.Tensor,
    *,
    rope_sin: Optional[torch.Tensor] = None,
    rope_cos: Optional[torch.Tensor] = None,
    cache_index: Optional[torch.Tensor] = None,
    dequant_scale_x: Optional[torch.Tensor] = None,
    dequant_scale_w_dq: Optional[torch.Tensor] = None,
    dequant_scale_w_uq_qr: Optional[torch.Tensor] = None,
    dequant_scale_w_dkv_kr: Optional[torch.Tensor] = None,
    quant_scale_ckv: Optional[torch.Tensor] = None,
    quant_scale_ckr: Optional[torch.Tensor] = None,
    smooth_scales_cq: Optional[torch.Tensor] = None,
    actual_seq_len: Optional[torch.Tensor] = None,
    k_nope_clip_alpha: Optional[torch.Tensor] = None,
    rmsnorm_epsilon_cq: float = 1e-5,
    rmsnorm_epsilon_ckv: float = 1e-5,
    cache_mode: str = "PA_BSND",
    query_norm_flag: bool = False,
    weight_quant_mode: int = 0,
    kv_cache_quant_mode: int = 0,
    query_quant_mode: int = 0,
    ckvkr_repo_mode: int = 0,
    quant_scale_repo_mode: int = 0,
    tile_size: int = 128,
    qc_qr_scale: float = 1.0,
    kc_scale: float = 1.0,
    token_x_dtype: Optional[int] = None,
    weight_dq_dtype: Optional[int] = None,
    weight_uq_qr_dtype: Optional[int] = None,
    weight_dkv_kr_dtype: Optional[int] = None,
    kv_cache_dtype: Optional[int] = None,
    impl: str = "auto",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    ...
```

## 公开入口与生命周期

`mlaprolog_v4` 的auto/cann调用 `cann_ops_transformer.mla_prolog`，底层为aclnnMlaPrologV4WeightNz，要求CANN9.2.0。该接口返回五个tensor并原地更新kv_cache/kr_cache，不能与七输出functional变体互换。它完成MLA投影、归一化、可选RoPE和缓存写入，不计算attention或最终V投影。

rope_sin/cos同时非空才启用RoPE，同时缺省或空则禁用；仅一份非空在公共分发前报ValueError。启用时投影通道相邻配对旋转，旋转后偶数通道在输出前半、奇数在后半；不要预先把正弦前半取负。关闭RoPE保留原通道顺序。这与固定启用RoPE的某些V3入口不同。

token_x为 `[T,H]` 或 `[B,S,H]`。投影权重分别逻辑 `[H,Rq]`、`[Rq,N*(D+R)]`、`[H,C+R]`，原生要求FRACTAL_NZ且保留逻辑shape；absorb weight_uk为BF16 `[N,D,C]` ND。参考场景C=512、R=64、D=128/192、Rq=1536/2048。PA_BSND cache分别 `[pages,P,1,C]` 与 `[pages,P,1,R]`，cache_index逻辑slot s对应 `[s//P,s%P,0,:]`；PA_NZ以其物理tile存同一slot。调用方管理容量和生命周期。

## 模式与舍入

| 场景 | weight/kv/query量化模式 | 关键边界 |
| --- | --- | --- |
| BF16+C16 | 0/0/0 | arch22/arch35均声明支持；双cache与query为BF16。 |
| 动态INT8+C16 | 2/0/0 | arch22/arch35均有公开域；激活逐token、权重逐输出channel的FP32 scale，INT32累加后FP32反量化；归一化latent直接动态量化INT8，中间不先舍入BF16。 |
| MXFP8+C16 | 3/0/0 | 仅arch35；归一化latent先按CAST_ROUND转BF16，再32元素一组E8M0量化。 |
| MXFP8+C8 | 3/1/1 | 仅arch35；query与latent cache为FP8 E4M3FN、kr_cache仍BF16；quant_scale_ckv为反量化scale的倒数。 |

C8在可选RoPE/BF16转换后对query_rope做Q/KV尺度补偿，消费端不要重复补偿；全零query行产生零Q scale，不任意替换为1或加epsilon。mode2的RoPE前投影使用反量化FP32，不能提前转BF16。模式字段存在不代表任意组合都有效。

五输出为query、query_rope、dequant_scale_q_nope、query_norm、dequant_scale_q_norm；未开启项为空tensor，元组不再返回cache。query_norm_flag=True时mode2输出INT8 latent+FP32逐token scale，mode3即使C16也输出FP8 latent+E8M0 group scale，不能从attention query的BF16推断latent dtype。

## 固定 CANN V4 的 16 组合与公开平台

SGL 文档明确指向 ops-transformer 的 `d462156cf5d97712fcfeef95070d649f47d3bb6e`，该树 `version.cmake` 为 9.2.0。以下是这份公开 V4 文档与 `GetQuantizationMode/CheckAttrsRange/CheckScenarParam` 的交集；不把其他版本或已安装 wheel 自动视为这份实现。SGL 的 CANN 分发透传全部模式；其独立 Torch 参考覆盖的四组仍限于前文，不能将下表等同参考已支持或本次已验证。

三元组依次是 `(weight_quant_mode, kv_cache_quant_mode, query_quant_mode)`；“内部模式”是固定 Host 的 QUANT_MODE 值，不是新的公共参数。FP8 均指 E4M3FN；HIF8 指 HIFLOAT8。

| 公共三元组 | 内部模式 | 投影输入与归一化 latent | Cache / attention Query | 公开平台 |
| --- | --- | --- | --- | --- |
| (0,0,0) | 0 | BF16 X 与三组投影权重 | KV、Kr、Query 均 BF16 | A2/A3、950 |
| (1,0,0) | 1 | 仅 UqQr 权重 INT8，归一化 Cq 动态 INT8；X、Dq、DkvKr 为 BF16 | KV、Kr、Query 均 BF16 | A2/A3、950 |
| (1,2,0) | 2 | 同 w1 | KV、Kr 为 INT8 perchannel；Query BF16 | A2/A3、950 |
| (1,3,0) | 5 | 同 w1 | INT8 Ckv 与 BF16 Kr、FP32 group scale 合并；Query BF16 | A2/A3、950 |
| (2,0,0) | 3 | X、Dq、UqQr、DkvKr INT8；归一化 Cq 动态 INT8 | KV、Kr、Query 均 BF16 | A2/A3、950 |
| (2,1,1) | 4 | 同 w2 | KV INT8 pertensor，Query INT8 pertoken-head；Kr BF16 | A2/A3、950 |
| (2,3,0) | 6 | 同 w2 | INT8 Ckv 合并存储；Query BF16 | A2/A3、950 |
| (3,0,0) | 7 | X、三组投影权重及归一化 Cq 为 MXFP8 E4M3FN；E8M0 分组 scale | KV、Kr、Query 均 BF16 | 950 |
| (3,1,1) | 8 | 同 w3 | KV FP8 pertensor，Query FP8 pertoken-head；Kr BF16 | 950 |
| (3,3,0) | 9 | 同 w3 | FP8 Ckv 合并存储；Query BF16 | 950 |
| (4,0,0) | 10 | X、三组投影权重及归一化 Cq 为 FP8；FP32 scale | KV、Kr、Query 均 BF16 | 950 |
| (4,1,1) | 11 | 同 w4 | KV FP8 pertensor，Query FP8 pertoken-head；Kr BF16 | 950 |
| (4,3,0) | 14 | 同 w4 | FP8 Ckv 合并存储；Query BF16 | 950 |
| (5,0,0) | 12 | X、三组投影权重及归一化 Cq 为 HIF8；FP32 scale | KV、Kr、Query 均 BF16 | 950 |
| (5,1,1) | 13 | 同 w5 | KV HIF8 pertensor，Query HIF8 pertoken-head；Kr BF16 | 950 |
| (5,3,0) | 15 | 同 w5 | HIF8 Ckv 合并存储；Query BF16 | 950 |

A2/A3 的公开文档明确不支持 FP8、HIF8、MXFP8 全量化；Host 在该架构将 w 限于 0、1、2。950 公开覆盖全部量化场景，但 DAV_3510 的 GenTilingKey 在 AIV 数等于 AIC 数的 CV1:1 配置拒绝正常量化路线；公开支持不是任意核比例、形状或缓存布局都能执行的承诺。

### dtype、scale 与存储必须随模式一致

- w1 的 dequant_scale_w_uq_qr 为 FP32 `[1,N*(D+64)]`；可选 smooth_scales_cq 为 FP32 `[1,Hcq]`。这里按 Host 的输出通道轴合同记录，不从公开页面“pertoken 权重”的措辞推导另一套 scale 形状。w2、w4、w5 另要求 X 的 FP32 `[T,1]` scale，以及 Dq、DkvKr 的 FP32 `[1,Hcq]`、`[1,576]` scale；UqQr scale 保持输出通道轴。
- w3 的四份 scale 均为 E8M0：X `[T,He/32]`、Dq `[Hcq,He/32]`、UqQr `[N*(D+64),Hcq/32]`、DkvKr `[576,He/32]`。FillMxfp8FullQuantParamInfo 明确要求 X、Dq、UqQr、DkvKr 为 E4M3FN；CheckTokenX/CheckWDq/CheckWUqQr/CheckWDkvKr 不接受 E5M2。通用单字节 Bitcast 枚举出现 E5M2，不增加一个 E5M2 算法路线，dtype override 也不绕过 Host 检查。
- kv=1 时 quant_scale_ckv 为 FP32 `[1]`，query_quant_mode 必须为 1；对应 dequant_scale_q_nope 为 FP32 `[T,N,1]`。kv=2 只属于 w1，KV 与 Kr 使用各自 FP32 `[1,512]`、`[1,64]` perchannel scale。其余 kv 模式的 query_quant_mode 必须为 0。
- kv=3 是 pertoken-pergroup：`ckvkr_repo_mode=quant_scale_repo_mode=1`、`tile_size=128`，cache mode 只许 PA_BSND/BSND/TND。一条 KV slot 的名义 656 字节依次装 512 个单字节 Ckv、64 个 BF16 Kr（128 字节）及 4 个 FP32 scale（16 字节）；独立 Kr cache 必须是含零维的空 tensor，例如 shape `(0,)`。(1,3,0)/(2,3,0)还必须提供非空FP32 `[1]` 的k_nope_clip_alpha，默认None会被场景检查拒绝；w3/4/5的kv=3场景则禁止该参数，必须为None。非 kv=3 的两个 repo mode 均为 0，独立 cache 的末维仍为 512/64。不能把混合字节 slot 当作 656 个同质浮点数消费。
- query_norm_flag 开启时，w0 latent 为 BF16；w1/2 为 INT8 + FP32 逐 token scale；w3 为 E4M3FN + E8M0 分组 scale；w4 为 E4M3FN + FP32 scale；w5 为 HIF8 + FP32 scale。w3 在 attention Query 仍为 BF16 的 kv=0/3 时也保持量化 latent。固定 eager C++ 的 CheckMxfp8Inputs 要求四份输入 scale 的实际 dtype 均为 torch.float8_e8m0fnu；MakeDequantScaleQNormTensor 继承 dequant_scale_x.scalar_type()，因此 w3 的该 scale 输出也是原生 E8M0 dtype。其编码占一个字节不表示此入口接受或输出普通 uint8；GE Bitcast 与 HIF8 的 uint8 包装另按各自路径解释。
- query_norm 的逻辑形状随 X 布局为 TND `[T,Hcq]` 或 BSND `[B,S,Hcq]`；对应 scale 始终展平 token 轴：w1/2/4/5 为 `[T,1]`，w3 为 `[T,Hcq/32]`，其中 BSND 的 T=B*S。不能按 query_norm 的三维形状推成 `[B,S,1]`。
- gamma 与 absorb weight_uk 仍为 BF16。三组投影权重必须使用 FRACTAL_NZ；逻辑二维矩阵与显式四维物理存储不能凭 torch shape 相互替换。这五个 dtype override 在固定 vendor 中主要供 w5 的 uint8/HIF8 场景校验并强制 HIF8 解释；其他模式的 TensorWrapper 仍按实际 tensor.scalar_type() 转换，不因 override 改成任意 ACL dtype，也不绕过 Host 检查。它们不执行量化数值转换；调用方须提供匹配的编码、scale 和容量。

w5 的 vendor IsHifloat8Scene 由四个X/投影tensor中“任一是Byte”触发，再检查四份override（kv1/3再含KV override）均为ACL_HIFLOAT8；它没有逐个证明实际storage全为uint8。进入该分支后ResolveTensorAclDtype统一强制HIF8解释。因此不能把混合actual dtype一定拒绝当作保证：四份编码、容量、布局与scale均正确仍是调用方合同。

逻辑shape与物理storage也分层处理：V3 InferShape的ValidateInputShapeDims要求weightDq逻辑view为二维，Host GetStorageShape则可核对其四维FRACTAL_NZ物理存储。vendor ResolveLogicalDims另有普通4D Torch tensor的维度推导；这不证明同一个任意4D tensor可原样通过eager或公开ACLNN全部校验。适配时必须保留逻辑view、format及物理storage的一致性。

### Host guard 与调度边界

固定 Host 检查 B≤65536、He∈{1024,2048,3072,4096,5120,6144,7168,7680,8192}、Hcq∈{1536,2048}、N∈[1,128]、Hckv=512、Dr=64、D∈{128,192}、Nkv=1；分页 block size 在 [16,1024] 且为 16 的倍数。合法基础布局为 BSND/TND/PA_BSND/PA_NZ/PA_BLK_BSND/PA_BLK_NZ，再与各模式限制取交集。TND 对应 `[T,He]`，BSND 对应 `[B,S,He]`；分页索引按 token 或 block 布局提供，固定场景检查要求其为 INT64，不能仅凭 SGL 参数注释中的 int32/int64 认为二者均被该 Host 接受。合轴 block 分页要求 INT32 `actual_seq_len[B]`，其值是累计 token 终点，最后一个须等于 T；调用方仍须保证页索引、缓存容量和长度值合法，shape guard 不证明这些 GM 值安全。

w3 在 `T>=8192 && He∈{7168,7680} && N==128` 时选 splitM，其余选 splitN；不能只读小 T 的 splitN 后概括全部 MXFP8。w1/2 中 N≥8 启用 dequant 优化，N≤7 保留另一条实现；w3/4/5 的 FP8/HIF8 权重使该优化开启。源码中的 group-compute 分支另需 Nkv=8，而公共维度检查固定 Nkv=1，因此不能将该私有模板写成此公共入口可达能力。

公开空 T 或空 cache 合同仍保留：空 T 不写 cache；空 cache 仍计算 Query。实际 tiling 的返回值处理、950 CV1:1 guard 与 SDK Debug/nonDebug selector 差异须按实际分支分析；不能由“允许空 tensor”推导所有配置已正确落到空实现。浮点源码卡记录了可复验静态限制，未据此宣称真机故障。

## 七输出 functional、GE 与原地恢复

这里的 functional 是依赖仓的 `cann_ops_transformer.mla_prolog_functional` / `torch.ops.cann_ops_transformer.mla_prolog_functional.default`，并非 SGL 五输出函数新增一个 impl 名。返回顺序为：

`(query, query_rope, dequant_scale_q_nope, query_norm, dequant_scale_q_norm, kv_cache_out, kr_cache_out)`。

| 路径 | cache 所有权与结果顺序 | 已固定实现边界 |
| --- | --- | --- |
| eager 原地五输出 | Torch schema 将输入 cache 标为 Tensor(a!)/Tensor(b!)；ACLNN 直接更新它们；五输出不包含 cache | Python→C++→V4 workspace/execute pair 可定位；调用方保留 cache、输入、输出与 workspace 至 stream 工作完成。 |
| eager functional 七输出 | C++ 先 kv_cache.clone()、kr_cache.clone()，再将两份副本传入同一原地 MLA 实现，最后附加两个副本输出 | 原 cache 不作为该函数中的 MLA 写目标；aten.clone 的 NPU Device body、拷贝实现与任意 stride/padding 保留合同未在这份源码中闭合。 |
| GE 原地 converter | 构造 ge_op("MlaPrologV3")，以原 cache 作输入并只向 Torch 返回五项 | GE op 名保持 V3；增加 do_rope 等 attrs，不将其重命名为另一个公开 API。 |
| GE functional converter | 先两次 ge.TensorMove，再将副本输入 MlaPrologV3，重排七输出 | GE 原生结果为 Q、Qr、KV、Kr、Qscale、QN、QNscale；converter 重排成 Torch 七输出。TensorMove 的 Device body 和 torchair 后续 lowering 未固定，不能宣称整个 functional 图源码闭包。 |

GE 的 _resolve_do_rope_ge 只检查对象是否为 None；成对非 None 的空 GE Tensor 仍选 do_rope=True，与 eager 的 numel()>0 检查不同。两者 None 时 converter 建立 BF16 空常量并下传 do_rope=False。使用空 tensor 关 RoPE 的 eager 写法不能不经分析地迁到该图入口。直接 ACLNN 的 doRope=False 要求原始 rope 指针为 nullptr，eager C++ 会将未定义/零元素可选 tensor 归一化为空指针。

图 converter 在 w5 将合格的单字节 X/投影权重以及 kv=1/3 的 KV Bitcast 为 HIF8，在 w3 将四份 scale Bitcast 为 E8M0；它不将 BF16 cache 当成单字节量化 cache。这个重解释不是重新计算量化值，也不使 Host 未接受的组合成为合法输入。

Python 同时注册 py_functionalize_impl 与 C++ dispatcher 的 Functionalize kernel：unwrap 输入→redispatch 七输出 functional→对两个 cache 执行 ctx.replace/commit_update/sync→仅 wrap 前五输出。这里 ctx.sync 是 Functionalize 状态操作，不能写成 ACL stream 同步或据此缩短 Device tensor 的生命周期。

ACL graph reinplace 注册以 functional op 映射回 inplace op，mutated_arg=[7,8]；代码依次尝试三个 torchair/torch_npu 模块路径，使用可用的 check_multi_stream_for_multi_reinplace，缺失时以返回 True 的函数占位。可证明的是注册意图与可变参数位置；是否实际应用、alias 安全和多 stream 调度仍取决于未固定框架的 pass 与运行条件。缺少 torchair 时两个 converter 明确抛出 RuntimeError。不能将“有 functional schema / 有 reinplace 注册”当作整个编译图可安全原地复用的证明。

## 源码级实现导航

下列卡片逐个闭合公开三元组在对应平台的 Host、POD、实际 Device 分支、内存、同步和静态限制。每行是独立数学语义；平台拆卡不增加数学组合数。

| 三元组 | A2/A3 | 950 |
| --- | --- | --- |
| (0,0,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_float.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_float_950.md) |
| (1,0,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv0.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv0_950.md) |
| (1,2,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv2.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv2_950.md) |
| (1,3,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv3.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w1_kv3_950.md) |
| (2,0,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv0.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv0_950.md) |
| (2,1,1) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv1.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv1_950.md) |
| (2,3,0) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv3.md) | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w2_kv3_950.md) |
| (3,0,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w3_kv0_950.md) |
| (3,1,1) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w3_kv1_950.md) |
| (3,3,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w3_kv3_950.md) |
| (4,0,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w4_kv0_950.md) |
| (4,1,1) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w4_kv1_950.md) |
| (4,3,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w4_kv3_950.md) |
| (5,0,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w5_kv0_950.md) |
| (5,1,1) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w5_kv1_950.md) |
| (5,3,0) | 公开不支持 | [实现卡](../../operators/aclnn/transformer/attention/sgl_mlaprolog_v4_w5_kv3_950.md) |

这些原地 MLA 实现卡不包含 `aten.clone`、GE `TensorMove` 和未固定框架 pass 的 Device 实现；functional 路径仍遵守前述外部边界。

## 参考与验证

独立参考在CPU做FP32计算并保留规定的BF16/INT8/FP8转换阶段，输出回输入设备并更新cache；仅覆盖文档表中的0/2/3模式和PA_BSND/PA_NZ双缓存。比较应克隆两份cache，检查全部五输出及写入slot，分别检验无RoPE、INT8码值和scale；公开接口与direct-CANN parity不是独立golden。来源中的测试矩阵和容差是上游设计，不代表本次已运行或可直接推广到其他模型尺寸。

## 证据与复核范围

本卡保留固定 SGL 提交的第一方 API 合同，并增量核对其文档明确引用的 ops-transformer d462 9.2.0 的公开 V4 文档、ACLNN、Host 与 Torch/GE 接入源码；架构编号映射为 A2/A3（arch22）及 950（arch35），具体子功能仍受正文限制。依赖仓的源码身份不证明当前环境已安装的 wheel、SDK 或算子包与之相同；量化矩阵为文档与 Host 事实，functional 拷贝与框架 pass 保留外部实现边界。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
