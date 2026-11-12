---
type: Operator
title: MLA Prolog V4 FP8 投影与 BF16 缓存 950 ACLNN 算子知识
description: 说明V4(4,0,0)的E4M3投影与FP32 scale、26个splitN selector、208B POD和逐head同步，保留MX搬运特化、零scale及UB边界。
tags:
- task.implementation
- task.lookup
- topic.data_movement
- topic.memory
- topic.precision
- topic.programming_model
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/mlaprolog_v4.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/mlaprolog_v4.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
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
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/torch_extension/cann_ops_transformer/common/aclnn_common.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/torch_extension/cann_ops_transformer/op_builder/builder.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_def.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_tiling_register.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_tiling.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_infershape.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_host/mla_prolog_v3_infershape.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_infershape.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling_check.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_host/mla_prolog_tiling_check.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/mla_prolog_tiling_data.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/mla_prolog_template_tiling_key.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/mla_prolog_comm_arch35.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/mla_prolog_vector_comm_arch35.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_matmul_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_rms_norm_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_gather_sin_cos_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_rotary_position_embedding_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_rope_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_rope.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_rms_norm.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_comm.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_operator_block_sync_intf.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/kernel_operator_block_sync_intf_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_operator_sys_var_intf.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/kernel_operator_sys_var_intf_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/utils/tiling/template_argument.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_struct_mm.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/utils/tiling/template_argument.cpp
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_tpipe.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/kernel_tpipe_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_tensor.h
  role: header
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/kernel_tensor_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_operator_sys_var_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_operator_sync_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_tpipe_impl_c310.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_dequant.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_dynamic_quant.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/torch_extension/cann_ops_transformer/utils/arg_check.py
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_struct_fixpipe.h
  role: header
created_at: '2026-11-09T16:29:46Z'
updated_at: '2026-11-09T16:29:46Z'
platforms:
- '950'
cann_versions:
- 9.2.0
---

# MLA Prolog V4 FP8 投影与 BF16 缓存 950 ACLNN 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | aclnnMlaPrologV4WeightNzGetWorkspaceSize / aclnnMlaPrologV4WeightNz，公开 ACLNN；SGL auto/cann 调外置 cann_ops_transformer.mla_prolog |
| 计算语义 | 唯一 (weight,kv,query)=(4,0,0)：三次 E4M3FN 投影以 FP32 累加/反量化，Cq RMS+动态 E4M3FN；第四次 BF16 吸收投影；BF16 Query、QueryRope 和双 cache |
| 输入输出 | X/WDq/WUqQr/WDkvKr E4M3FN；四份 FP32 scale；WUk/gamma/sin/cos BF16；可选 E4M3FN QueryNorm+FP32 scale |
| 执行类型 | 一次 MIX_CV，AIC_CUBE 四矩阵乘与 AIV_VECTOR 反量化/RMS/量化/RoPE/scatter；空 query 在 entry 提前返回 |
| Kernel 路线 | R-001–005 是五种 cache 寻址族，全部 dequantOpt=true/splitN；26 正常 typed selector；R-006–008 为空和条件错误终点 |
| 核心资源 | FP32 W0/W1/W2、E4M3 Cq、BF16 Qc；每 AIC 的 L1 A/B 各双128KiB，L0A/B 各双32KiB，L0C 双64KiB；每 AIV 的192KiB设计预算 |
| 来源闭包 | source_closed：V4 pair→InnerV3/OpDef→Host/POD/key→arch35 splitN 及本实例 helper；生成 bridge、普通布局准备、通用硬件 primitive 与外置 wheel 身份是集成边界 |
| 验证状态 | 本次知识提取未执行编译、真机、数值或性能测试。draft 保留选中搬运特化、UB、零 scale 和条件 key 边界；源码闭合不等同已验证正确。 |

## 接口与语义

### 计算语义

记 T 为 token 展平数，H=Hcq，N 为 head 数，D 为每 head Qc 宽度；Ckv=512、Dr=64。MM8 是 E4M3FN×E4M3FN、FP32 L0C 累加并保留 FP32 GM 输出。dq(z,sx,sw) 在本平台先乘逐输出 channel 的 FP32 sw，再乘逐 token 的 FP32 sx；不与 MXFP8/E8M0 组 scale 混用。b16 为 Vector CAST_RINT，MM4 的输出则使用 Fixpipe F322BF16。

```text
zQ = MM8(X,WDq)                                         [T,H]
fQ = RMS_FP32(dq(zQ,sX,sWDq),gammaQ,epsQ)
fQ *= aq if abs(aq-1)>=float_epsilon
fQ *= smoothQ if provided
sCq[t] = max(abs(fQ[t,:]))/448                           FP32 [T,1]
Cq8 = E4M3FN_RINT_SAT(fQ/sCq)                           无中间BF16舍入
zQR = MM8(Cq8,WUqQr)                                    [T,N,D+64]
Qc16 = b16(dq(zQR[:,:,:D],sCq,sWUqQr[:,:,:D]))           [T,N,D]
Query = MM4_BF16(Qc16,WUk)                              [T,N,512]
QueryRope = b16(rot(dq(zQR[:,:,D:],sCq,sWUqQr[:,:,D:])))  doRope=true
            或 b16(反量化原通道顺序)                    doRope=false
zKVKr = MM8(X,WDkvKr)                                   [T,576]
KV = b16(RMS_FP32(dq(zKVKr[:,:512],sX,sWDkvKr[:512]),gammaKV,epsKV)*ak)
Kr = b16(rot(dq(zKVKr[:,512:],sX,sWDkvKr[512:])))         或关闭RoPE时直通
scatter(KV,Kr)                                          双cache副作用
```

旋转使用相邻偶/奇通道配对，输出前32为 even*cos−odd*sin，后32为 odd*cos+even*sin；GatherSinCos 已把 sin 前半乘−1。关闭时保持原通道顺序。RMS 以64lane逐块平方/累加→Reduce SUM→1/H→epsilon→Sqrt→Div→gamma，aq/ak 条件 Muls 随后执行。Cq pertoken 量化两遍寄存器读取、amax/448、Div、直接 FP32→E4M3FN RINT/SAT；M=0 没有 pertile M=1 的1e−4阈值。全零行继续除 scale0，不能补造零行保护或宣称其 FP8 结果已验证。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| tokenX | [T,He] 或 [B,S,He]，ND/NCHW | E4M3FN | He∈{1024,2048,3072,4096,5120,6144,7168,7680,8192}；B≤65536；T=B*S 的 u32运算需不溢出 |
| weightDq | 逻辑[He,H]，NZ物理[H/32,He/16,16,32] | E4M3FN | H∈{1536,2048}；逻辑二维 shape 与实际 NZ storage 分开 |
| weightUqQr | 逻辑[H,N*(D+64)]，NZ [N*(D+64)/32,H/16,16,32] | E4M3FN | N=1..128，D=128/192，不支持 E5M2 |
| weightDkvKr | 逻辑[He,576]，NZ [18,He/16,16,32] | E4M3FN | 前512 Ckv、后64 Kr |
| weightUk | [N,D,512] ND | BF16 | 第四矩阵乘吸收权重 |
| dequantScaleX | [T,1] | FP32 | 必需逐token scale，不是 E8M0 |
| dequantScaleWDq/WUqQr/WDkvKr | [1,H] / [1,N*(D+64)] / [1,576] | FP32 | 必需逐输出channel scale |
| gammaCq/Ckv | [H] / [512] | BF16 | 各AIV首step加载并驻留 |
| smoothScalesCq | 缺省或[1,H] | FP32 | RMS及aq后、量化前；存在性额外占4H UB |
| ropeSin/Cos | [T,64] 或 [B,S,64] | BF16 | 原始ACLNN doRope=false要求双nullptr，true要求非null；SGL/vendor按成对numel>0归一化 |
| kvCacheRef/krCacheRef | TND [T,1,512/64]，BSND [B,S,1,512/64]，分页逻辑[Pnum,P,1,512/64] | BF16 IN/OUT | 内轴连续，首轴stride可含padding；NZ由route解释物理tile；双cache由caller持有 |
| cacheIndex | tokenPA [T]/[B,S]；blockPA [B,ceil(S/P)]或合轴一维页表 | INT64 ND | ND不传；负slot跳写；正上界/容量/冲突由caller保证 |
| actualSeqLen | 合轴blockPA [B] | INT32 ND | 累计终点、末值T；shape检查不扫描其值 |
| Query/QueryRope | [T,N,512/64] 或 [B,S,N,512/64] | BF16 | 新输出；不得与仍在读的输入、cache或workspace任意重叠 |
| QueryNorm/dequantScaleQNorm | 可选[T,H]或[B,S,H] / [T,1] | E4M3FN / FP32 | 开启时同一 Cq8 直接作为MM3输入；不开启返回空tensor |
| dequantScaleQNope | 原始nullptr，vendor返回[0] | FP32空 | kv0不计算 Query动态量化 |
| quantScaleCkv/Ckr/kNopeClipAlpha | 缺省 | N/A | 当前tuple不量化cache，不是可任意传入的保留输入 |
| attrs | w4/kv0/q0，repo0/scaleRepo0，tile128 | mode INT64；double标量转float | eps默认1e−5，aq/ak默认1，cache默认PA_BSND；doRope两值、QN与smooth均可达 |

### 入口与版本

本卡冻结 SGL dda6 文档明确引用的 ops-transformer d462 的 CANN9.2.0；SDK 固定 a63d9.2。公开产品表与场景表明确 FP8 全量化仅950，A2/A3不支持，不从 arch35 文件名扩大范围。SGL 的 torch_native 只覆盖0/2/3若干组合，w4由 auto/cann 透传，不能把公共参考当成此 tuple 的独立 golden。

[SGL V4 API](../../../../apis/sgl_kernel_npu/sgl_mlaprolog_v4.md)说明16组合和functional边界。本卡为原地五输出语义，不纳入 clone/TensorMove 的外部 Device 实现。V4 复用 InnerV3 注册名并增加 doRope，不意味着旧 V3 固定RoPE/旧172B POD是本卡ABI。当前(4,0,0)与INT8、MXFP8、HIF8及kv1/kv3各自为独立数学。

## Host/Launcher 执行流程

### 参数校验与前处理

SGL先判sin/cos成对，lazy导入vendor callable。vendor schema标注cache Tensor(a!)/Tensor(b!)，PrivateUse1→OpBuilder.load→C++。Builder可复用加载结果并选择CANN/vendor头库，arg_check代理只拒绝可解析pybind doc中的明确类型不匹配，未识别类型透传；这不是值域或设备安全检查。本次未运行load、编译或安装。

C++ OptionalDeviceGuard(tokenX.device)→形状与NZ格式校验→分配五输出→ACLNN_CMD。w4实际Tensor.scalar_type透传；HIF8 override强制解释只属于w5，不将uint8或E5M2改成合法w4。ResolveLogicalDims对Torch可见4D采用(s0*16,s1*16)，Host又按实际NZ storage首轴*c0恢复输出宽；inferShape要求权重逻辑rank2。QueryNorm分配取weight_dq.size(1)，故不能把裸4D storage Tensor与保留二维逻辑shape的format29权重直接等价。

V4检查模式/可选指针/doRope，TensorHolder将原始nullptr替为[0]临时descriptor；禁用Qscale、QNscale是否允许由原始nullptr身份决定，非null空descriptor不是同一合同。holder假数据地址不可当有效GM，query返回销毁descriptor。OpDef输入AutoContiguous、cache IgnoreContiguous；普通生成bridge/布局准备为框架边界，不隐藏自有核心算子。

Host：ConvertContext校验cache内轴连续、首轴stride≥逻辑连续跨度；空cache stride0=0，缺stride descriptor才回退连续值。GetNpuInfo要求C/V>0且V=C或2C→attrs/required/cache mode→shape/scenario→repo/query模式、quant/dims/special/expected参数→attrs→ProcessBaseInputs→四MM分核→POD/WS/key。tile只接受128，即使kv0不用其计算。Host不扫描页表/累计终点、scale有限性、重复slot或全部乘法溢出。真实错误状态停止后续，空query的GenTilingKey例外见R007。

### 参数、Workspace 与生命周期

记m=min(T,D==192?64:128)、g=N(D+64)、h=ND、qnf∈{0,1}；运算限定于源码u32/size_t/int64未溢出域。

```text
W_Host = W_lib + 32m + 6mH + 2304m + 4mg + 2mh
Device slices，从workspace参数原址开始：
Sscale [0,32m)                     FP32 [m,8]广播槽
W0     [32m,+2304m)                FP32 [m,576]，E1仍预留
W1     W0后4mH                    FP32 [m,H]
Cq8    W1后(1-qnf)mH              E4M3FN；qnf1直接正式QN
W2     Cq8后4mg                   FP32 [m,N,D+64]
Qc16   W2后2mh                    BF16 [m,N,D]
W_Device = 32m+2304m+4mH+(1-qnf)mH+4mg+2mh
```

Host按2mH预算归一化结果，实际Cq仅mH或正式QN；不能把Host上界误作同时活跃片之和。W_lib由平台GetLibApiWorkSpaceSize取得，Device未自行跳过该固定常量；生成Runtime包装如何传workspace是集成边界，不臆造16MiB偏移。

ACLNN query取得size/executor→caller分配→execute同stream。vendor使用当前NPU stream，必要时UseStreamResInCurrentThread；query/execute失败清理descriptor并抛错。byte workspace tensor为Host局部，回调捕获raw资源，未自行证明allocator/延迟队列所有权。输入、输出、两cache、index、length与workspace需存活至stream工作完成；后继cache读由同stream或event排序，不用descriptor析构替代Device完成。

### 启动图与失败传播

正常T>0一次InnerV3 MIX_AIC_1_2，blockDim=C，运行AIV线性索引v=c*r+s，r=GetSubBlockNum=2；全部950量化V=C被Host拒绝。空T正常block1、W_lib、entry在POD/TPipe/GM之前返回。Host Debug selector不匹配和空分支吞GenTilingKey错误分别见R008/R007。

```mermaid
flowchart LR
  H["V4 query/execute → 单MIX"] --> A["MM1 FP8→FP32 W1"] --> V["dq/RMS/smooth→Cq8+scale"]
  V --> B["MM3 FP8→FP32 W2"] --> D["逐head dq Qc→BF16"] --> C["MM4 BF16→Query"]
  B --> R["dq Qr→RoPE/直通→BF16 Qr"]
  H --> K["MM2 FP8→FP32 W0"] --> S["dq/RMS/Kr旋转→双BF16 cache"]
```

## Route 与参数设计

### 分核与资源计算

w4的dequantOpt始终true，不按N≥8再分支；splitM只属w3，KN只属DAV9201，group要求部分量化及Nkv8，均不属于本tuple。m的D192上限64对全部N生效。Veff=min(m,V)，末step m'=min(m,T−b0)，AIV v分q=floor(m'/Veff)+[v<m'%Veff]，start=v*floor(m'/Veff)+min(v,m'%Veff)。无token核仍参加公共屏障；每对AIV在后续Qc沿D/2分列、Qr沿m'分行，不能混用两种划分。

| 段 | M/N/K与分核 | base/step及tail |
|---|---|---|
| MM1 | m/H/He；n1=max(64,32ceil(H/(32C)))，b1=ceil(H/n1) | baseN128、baseK256；stepK=(He/256)%4==0?4:3，K_L1=1024/768；末核n=H−(b1−1)n1 |
| MM2 | m/576/He；E1 b2=n2=0；否则C≥9取64/9，否则n2=32ceil(576/(32C)) | baseN128、baseK256、stepK同MM1；末核有效N；E1 constexpr跳计算 |
| MM3 | m/g/H；n3=(D+64)ceil(N/C)，b3=ceil(g/n3) | baseK128、stepK4；初始m≤64取baseN256，否则128；末step不重选baseN；当前m'≤64整载A否则分K |
| MM4 | 每head m/512/D；hp=ceil(N/C)，b4=ceil(N/hp) | baseN128；D128 K128×1、全B128KiB；D192 K64×3、ND B splitK；末核head余数 |

所有Cube内部M=align16(m')，Fixpipe只提交m'有效行。FP8 NZ C0=32、BF16 C0=16。L1/L0按实际base与双bank逐项算，不能仅按逻辑tensor长度认定资源足够。

### Route 选择

K(c,E,A,e)=(c,2,10,true,false,E,A,0,e,7)。c0归一BSND/TND，c1/2为tokenPA，c3/4为blockPA；E0正常/E1空cache，A1仅合轴blockPA，e=doRope。qnf、smooth、D、末step是同key的运行时分支。

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R006 | 空selector | 全部参数校验后T=0且GenTilingKey guard通过 | V=C进入R007，其它前置错失败 |
| 2 | R001–005 | K(c,E,A,e) | T>0，C>0,V=2C，合法w4kv0/q0与layout | 不合法Host失败，没有dense或Torch fallback |
| 3 | R007 | 遗留key0 | DAV3510,V=C,T=0；GenTilingKey拒绝量化，但空分支忽略返回值 | 未选中合法自有body，Runtime结果不补造 |
| 4 | R008 | UINT64_MAX | T>0,e0，Host ASCENDC_DEBUG且未外部定义MLA_PROLOG_VERSION=3 | 非Debug可编码；实际构建宏需核对 |

```text
validate inputs/modes/strides/CV → T0优先
  T0: FillTiling/libWS/GenKey(状态被忽略)/block1
  T>0: deq1/splitN → FillMM1..4/WS/POD → GenKey
    V=C: GRAPH_FAILED
    V=2C: c0..4→各Route；e0在条件Debug形成R008
```

### 模板/实现执行矩阵

正常实例唯一为 `MlaPrologVecS1CubS2<MLAPType<FP8E4M3,FP8E4M3,bfloat16_t,float,CACHE_MODE(c),true,false,EMPTY(E),ACTUAL(A),false,2,e>>`。前三MM输出float、Cq输出FP8，WUk/MM4/Query/Kr均BF16。实际entry指针顺序保留X、四权重、两gamma、sin/cos、cache双输入/index、四scale、两quantScale、smooth、length、clip、七GE输出、workspace、tiling；两cache的实际计算使用输出别名，不由输入指针的存在推导额外拷贝。

| Route | key/selector | 完整命中条件 | 执行族与节点 | 实际body | 内存与同步 | tail/fallback |
|---|---|---|---|---|---|---|
| R001 | K(0,0,0,e) | BSND rank3 X/cache4或TND rank2 X/cache3；非空cache | 单MIX_CV四MM与Vector | splitN→ScatterCache<BF16,false> | 公共W/L1/L0/UB；直接token地址 | m'行；无index fallback |
| R002 | K(1,E,0,e) | PA_BSND，rank2/3对应token index | 同上；E1跳MM2/cache | ScatterCache<BF16,false> | slot→页/页内；free9 | 负slot跳写；正界由caller |
| R003 | K(2,E,0,e) | PA_NZ，逻辑cache4，物理NZ | 同上 | ScatterCache<BF16,true> | 32B channel tile，独立stride0 | 同上 |
| R004 | K(3,E,A,e) | PA_BLK_BSND；rank3 A0，rank2 A1+actualSeqLen | 同上 | ComputeBlkScatterOffsets→MaterializeOffsets<BF16,false>→MultiRows | 累计终点与页表游标；A1预留8m UB | row1；值域未扫描 |
| R005 | K(4,E,A,e) | PA_BLK_NZ；A0/1条件同R004 | 同上 | 对应NZ Materialize/MultiRows | tile内地址与独立stride0 | row1；无非法页安全fallback |
| R006 | 空key | T0,V=2C，前置合同满足 | entryreturn | 不建TPipe/不读POD | 仅libWS | cache不动 |
| R007 | key0 | T0,V=C | 无合法选定body | Host吞失败 | block1/libWS | Runtime边界 |
| R008 | INVALID_KEY | 条件Debug e0 | 无合法选定body | SDK Encode/SEL拒绝 | 正常Host预留 | Host不再检查INVALID_KEY |

SDK实际DECL宽度为4/2/4/1/1/2/2/2/1/8，数值为 `K=c+32+(10<<6)+(1<<10)+(E<<12)+(A<<14)+(e<<18)+(7<<19)`。头文件旧bit注释不能当ABI。Debug Encode验证SEL，非Debug FastEncode仅DECL；Host默认VERSION=-1使ENABLE_ROPE_SEL只含1，Device TU定义3允许0/1。正常26交集逐项如下；SEL中deq0、group、A1与不合layout的组合不扩大Host可达域。

| Route | (c,E,A,e) | uint64 key |
|---|---|---|
| R001 | (0,0,0,0) | 3671712 |
| R001 | (0,0,0,1) | 3933856 |
| R002 | (1,0,0,0) | 3671713 |
| R002 | (1,0,0,1) | 3933857 |
| R002 | (1,1,0,0) | 3675809 |
| R002 | (1,1,0,1) | 3937953 |
| R003 | (2,0,0,0) | 3671714 |
| R003 | (2,0,0,1) | 3933858 |
| R003 | (2,1,0,0) | 3675810 |
| R003 | (2,1,0,1) | 3937954 |
| R004 | (3,0,0,0) | 3671715 |
| R004 | (3,0,0,1) | 3933859 |
| R004 | (3,0,1,0) | 3688099 |
| R004 | (3,0,1,1) | 3950243 |
| R004 | (3,1,0,0) | 3675811 |
| R004 | (3,1,0,1) | 3937955 |
| R004 | (3,1,1,0) | 3692195 |
| R004 | (3,1,1,1) | 3954339 |
| R005 | (4,0,0,0) | 3671716 |
| R005 | (4,0,0,1) | 3933860 |
| R005 | (4,0,1,0) | 3688100 |
| R005 | (4,0,1,1) | 3950244 |
| R005 | (4,1,0,0) | 3675812 |
| R005 | (4,1,0,1) | 3937956 |
| R005 | (4,1,1,0) | 3692196 |
| R005 | (4,1,1,1) | 3954340 |
| R006 | (0,0,0,0,0,2,0,0,1,7) | 3940352 |

### 隐藏性能 Guard

| Guard | Host/Tiling条件 | Device/资源原因 | Route | 不满足去向 | 符号 |
|---|---|---|---|---|---|
| w4类型 | E4M3FN+FP32 scale | 不是MXFP8/E8M0或E5M2实例 | 全正常 | Host失败 | FillFP8FullQuantParamInfo |
| CV1:2 | V=2C | 950量化白名单 | 全部 | 非空失败，空R007 | GenTilingKey |
| D192 step | cap64 | MM3波与UB容量；全部N均生效 | 全正常 | 无动态缩tile fallback | ProcessBaseInputs |
| MM3 A全载 | 当前m'≤64 | align16(m')*H≤128KiB；H2048时刚满bank | 全正常 | m'>64分K | MatmulQcQr |
| stepK3 | (He/256)%4!=0 | 合法He7680用768步长无K尾，其他枚举1024 | 全正常 | 无任意He tail补救 | MmCq/CkvKrParamInit |
| UB资源 | F_alloc+stage≤实际UB/pool | 对齐独立TBuf；实际pool起点U0也占空间 | 全正常 | 没有逐stage Host guard | VectorBufferInit/TPipe |
| 数值 | scale值、epsilon及amax合法 | Cq零行无epsilon/保护 | 全正常 | 原代码继续计算 | ComputeVFImpl M0 |
| 索引与宽度 | u32 shape不溢出、页表/slot合法无冲突 | 非atomic散写、标量GM索引不验正上界 | 全正常 | caller合同 | SetShapeInfo/ScatterCache |
| FP8 L0B特化 | T=E4M3FN,S=float仍选MX LoadData | 搬运与Mmad模板条件不同，不能改写为普通B搬运 | 全正常前三MM | 没有自有替代分支 | MatmulL0/LoadDataL1ToL0B |

### POD/ABI

唯一Host序列化结构为 MlaPrologTilingData.baseParams，静态自然ABI推导sizeof208/align8，188–191 padding；未执行目标编译器sizeof/offsetof。逐字段如下。kNopeClipAlpha字段未被FillTiling赋值，本tuple不读，不称其为0。MM/offset等其余结构只在Device局部构造，不另造Host ABI。

| 结构 | 字段 | 类型/位宽 | ABI布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| BaseParams | batchSize | uint32_t/32 | offset0，4B | batch，TND其它路线为0 | FillTiling/CoreParams：B；fusedblockPA由actualSeqLen.shape[0] | ComputeBlkScatterOffsets批游标界 | batch，TND其它路线为0 |
| BaseParams | stepBatchSize | uint32_t/32 | offset4，4B | token；T0=0且不读 | FillTiling/CoreParams：min(T,D192?64:128) | Process步进/UB/WS/MM m | token；T0=0且不读 |
| BaseParams | mSubSize | uint32_t/32 | offset8，4B | inactive，本tuple无splitM | FillTiling/CoreParams：成员初始化0/FillTilingCoreParams | 当前splitN不读 | inactive，本tuple无splitM |
| BaseParams | mSubCoreNum | uint32_t/32 | offset12，4B | inactive | FillTiling/CoreParams：成员初始化0 | 当前splitN不读 | inactive |
| BaseParams | stepNumHeadDequant | uint32_t/32 | offset16，4B | head；仍写POD | FillTiling/CoreParams：D128?min(64,N):min(16,N) | deq恒1，由head波分工不直接读 | head；仍写POD |
| BaseParams | tokenSize | uint32_t/32 | offset20，4B | token；u32原始乘法域 | FillTiling/CoreParams：X前导维展平T | Process总步数 | token；u32原始乘法域 |
| BaseParams | seq1Size | uint32_t/32 | offset24，4B | token | FillTiling/CoreParams：rank3 X的S；rank2默认0 | blockPA A0批内token/ND BSND跨度 | token |
| BaseParams | seq2Size | uint32_t/32 | offset28，4B | 保留字段，不解释成真实KV长度 | FillTiling/CoreParams：nkvSize=1 | 本FP8 splitN不读 | 保留字段，不解释成真实KV长度 |
| BaseParams | headSizeX | uint32_t/32 | offset32，4B | 元素 | FillTiling/CoreParams：He | MM1/MM2 K与X行跨度 | 元素 |
| BaseParams | headSizeCq | uint32_t/32 | offset36，4B | 元素 | FillTiling/CoreParams：Hcq | MM1输出/MM3 K/NormCq | 元素 |
| BaseParams | headSizeCkv | uint32_t/32 | offset40，4B | 元素 | FillTiling/CoreParams：512 | MM2切片/NormKV/MM4 N | 元素 |
| BaseParams | headSizeQc | uint32_t/32 | offset44，4B | 元素 | FillTiling/CoreParams：N*D | MM3/Qn输入跨度 | 元素 |
| BaseParams | headSizeQr | uint32_t/32 | offset48，4B | 元素 | FillTiling/CoreParams：N*64 | QueryRope行跨度 | 元素 |
| BaseParams | headSizeKr | uint32_t/32 | offset52，4B | 元素 | FillTiling/CoreParams：Dr=64 | MM2完整输出/分核 | 元素 |
| BaseParams | numHeadSize | uint32_t/32 | offset56，4B | head | FillTiling/CoreParams：N | MM4 head循环/QueryRope row | head |
| BaseParams | numHeadKvSize | uint32_t/32 | offset60，4B | head | FillTiling/CoreParams：Nkv=1 | 本FP8 splitN无直接关键读取 | head |
| BaseParams | dimHeadSizeQc | uint32_t/32 | offset64，4B | 元素 | FillTiling/CoreParams：D | MM4 K/Qc切片 | 元素 |
| BaseParams | dimHeadRope | uint32_t/32 | offset68，4B | 元素 | FillTiling/CoreParams：64 | SinCos/Rotary/Kr尺寸 | 元素 |
| BaseParams | blockNum | uint32_t/32 | offset72，4B | cache slice数；P0选EMPTY_CACHE | FillTiling/CoreParams：cache首轴P/T/B | 本域scatter不做正index上界校验 | cache slice数；P0选EMPTY_CACHE |
| BaseParams | blockSize | uint32_t/32 | offset76，4B | token；PA16..1024且16倍数 | FillTiling/CoreParams：PA H或BSND S；TND0 | GetCacheOffset解页/blockPA余数 | token；PA16..1024且16倍数 |
| BaseParams | mm1BlockNum | uint32_t/32 | offset80，4B | core | FillTiling/CoreParams：ceil(H/n1) | MM1活跃核/末核N | core |
| BaseParams | mm2BlockNum | uint32_t/32 | offset84，4B | core | FillTiling/CoreParams：非空ceil(576/n2)，E1=0 | MM2活跃核；E1前置constexpr return | core |
| BaseParams | mm3BlockNum | uint32_t/32 | offset88，4B | core | FillTiling/CoreParams：ceil(N(D+64)/n3) | MM3活跃核/末核N | core |
| BaseParams | mm4BlockNum | uint32_t/32 | offset92，4B | core | FillTiling/CoreParams：ceil(N/headsPerCore) | Qn head核范围 | core |
| BaseParams | vectorBlockNum | uint32_t/32 | offset96，4B | AIV调度数；运行subblock修正见正文 | FillTiling/CoreParams：min(m,V) | Init Veff/分token | AIV调度数；运行subblock修正见正文 |
| BaseParams | mm1SingleCoreN | uint32_t/32 | offset100，4B | 元素 | FillTiling/CoreParams：n1 | MmCqParamInit/ComputeAicOffset | 元素 |
| BaseParams | mm2SingleCoreN | uint32_t/32 | offset104，4B | 元素；E1不执行MM2 | FillTiling/CoreParams：n2；E1默认0 | MmCkvKrParamInit/ComputeAicOffset | 元素；E1不执行MM2 |
| BaseParams | mm3SingleCoreN | uint32_t/32 | offset108，4B | 元素 | FillTiling/CoreParams：n3 | MmQcQrParamInit/ComputeAicOffset | 元素 |
| BaseParams | mm4SingleCoreBatch | uint32_t/32 | offset112，4B | head | FillTiling/CoreParams：headsPerCore | Qn loops/weightUkOffset | head |
| BaseParams | dtileSize | uint32_t/32 | offset116，4B | 元素 | FillTiling/CoreParams：512 | ScatterCkv tokenStride | 元素 |
| BaseParams | kvQuantMode | uint32_t/32 | offset120，4B | mode | FillTiling/CoreParams：0 | KV不量化；值0 | mode |
| BaseParams | tileSize | uint32_t/32 | offset124，4B | 元素，Host仍校验128 | FillTiling/CoreParams：attr128 | 本tuple不读pertile消费者 | 元素，Host仍校验128 |
| BaseParams | ckvkrRepoMode | uint32_t/32 | offset128，4B | mode | FillTiling/CoreParams：0 DIVIDE | ScatterKr合并分支inactive | mode |
| BaseParams | quantScaleRepoMode | uint32_t/32 | offset132，4B | mode | FillTiling/CoreParams：0 DIVIDE | scale回写分支inactive | mode |
| BaseParams | queryNormFlag | uint32_t/32 | offset136，4B | bool编码u32 | FillTiling/CoreParams：原始queryNormOut非null?1:0 | OutputInit/WorkspaceInit/Process | bool编码u32 |
| BaseParams | reciprocalCq | float/32 | offset140，4B | FP32 | FillTiling/CoreParams：float(1/H) | NormCq Reduce后Muls | FP32 |
| BaseParams | epsilonCq | float/32 | offset144，4B | FP32，不验证所有数值域 | FillTiling/CoreParams：rmsnormEpsilonCq Float | NormCq Adds/Sqrt | FP32，不验证所有数值域 |
| BaseParams | reciprocalCkv | float/32 | offset148，4B | FP32 | FillTiling/CoreParams：float(1/512) | NormKV Reduce后Muls | FP32 |
| BaseParams | epsilonCkv | float/32 | offset152，4B | FP32 | FillTiling/CoreParams：rmsnormEpsilonCkv Float | NormKV Adds/Sqrt | FP32 |
| BaseParams | kNopeClipAlpha | float/32 | offset156，4B | inactive，值不可宣称为0 | FillTiling/CoreParams：FillTiling未赋此标量字段 | 本tuple不读；其它quant helper另读GM | inactive，值不可宣称为0 |
| BaseParams | qcQrScale | float/32 | offset160，4B | FP32 | FillTiling/CoreParams：attr Float aq | NormCq gamma后Muls | FP32 |
| BaseParams | kcScale | float/32 | offset164，4B | FP32 | FillTiling/CoreParams：attr Float ak | NormKV gamma后Muls | FP32 |
| BaseParams | isQcQrScaleEnable | uint16_t/16 | offset168，2B | bool编码u16 | FillTiling/CoreParams：abs(aq-1)>=float epsilon | NormCq条件Muls | bool编码u16 |
| BaseParams | isKcScaleEnable | uint16_t/16 | offset170，2B | bool编码u16 | FillTiling/CoreParams：abs(ak-1)>=float epsilon | NormKV条件Muls | bool编码u16 |
| BaseParams | mm1NGroup | uint16_t/16 | offset172，2B | 组，9201才可能变化 | FillTiling/CoreParams：1 | 当前arch22/35 splitN不读KN分组 | 组，9201才可能变化 |
| BaseParams | mm1KGroup | uint16_t/16 | offset174，2B | 组 | FillTiling/CoreParams：1 | 本平台CalcWorkSpace按1；Device无KN | 组 |
| BaseParams | mm1SingleCoreK | uint32_t/32 | offset176，4B | 元素，inactive | FillTiling/CoreParams：0 | 当前arch22/35不读 | 元素，inactive |
| BaseParams | mm2NGroup | uint16_t/16 | offset180，2B | 组 | FillTiling/CoreParams：1 | 当前arch22/35不读KN分组 | 组 |
| BaseParams | mm2KGroup | uint16_t/16 | offset182，2B | 组 | FillTiling/CoreParams：1 | 本平台CalcWorkSpace按1；Device无KN | 组 |
| BaseParams | mm2SingleCoreK | uint32_t/32 | offset184，4B | 元素，inactive | FillTiling/CoreParams：0 | 当前arch22/35不读 | 元素，inactive |
| BaseParams | kvCacheStride0 | uint64_t/64 | offset192，8B | 元素u64，转int64需在已验范围内 | GetCacheStride0；空cache0 | ScatterCache/MaterializeOffsetsWithHeadSize | 元素u64，转int64需在已验范围内 |
| BaseParams | krCacheStride0 | uint64_t/64 | offset200，8B | 元素u64 | FillTiling/CoreParams：同前，独立取Kr | Kr ScatterCache/MaterializeOffsetsWithHeadSize | 元素u64 |


Device局部MMParams为15个u32，普通ABI推导sizeof60/align4：m/n/k偏移0/4/8，orgM/N/Ka/Kb/Kc偏移12/16/20/24/28，baseM/N/K偏移32/36/40，stepK/needSetOrgShape/kL1StepSize/kScale偏移44/48/52/56。m=m'，n当前核有效宽，k=He/He/H/D，orgKa=He/He/H/ND，orgKb=k，orgKc=H/576/g/N512。baseM未赋且无实际consumer；needSetOrgShape=1但自有helper不依赖它；kScale=k/32被辅助scale寻址计算读取，不能因S=float称该字段完全无读。

DequantQcQrSplitNParams的int64基址offset0/8，u32 input/output offset16/20、src/dst gap24/28，sizeof32/align8。输入基址o=c*n3、输出h0*D，s的input=s*D/2+head*(D+64)，output=s*D/2+head*D；gap=g−D/2、ND−D/2，分别以FP32/BF16元素为单位。RopeQrSplitNParams两int64偏移0/8，u32 input/deq/output偏移16/20/24，padding28–31，int64 ropeStride32，u32 dstGap/scaleOffset/sincosOffset/rows在40/44/48/52，sizeof56/align8；input=rowStart*g+head*(D+64)、output=rowStart*N64+head*64、scaleOffset=rowStart*8、rows=floor((m'+s)/2)，rowStart=floor(m'/2)*s。所有尺寸是静态普通ABI推导。

RmsNormParam六字段依次reciprocal/epsilon(float)、row/col(u32)、scale(float)、isScaleEnable(u16)，row=1、col=H/512；Rectangle三u32为row/col/stride。ScatterCacheParams八int64为P/slot/row1/col/tokenStride/stride0/S/tokenIndex；CkvkrParams六int64为tokenIndex、W0元素offset、当前token序号、页内行数、cacheOffset、nextPageOffset。UsedBlockParams两u32 start0/end=b1或b2。Aic/Aiv Offset各int64为对应typed元素偏移；MMBufParams的bank计数初始0、TPipe地址贯穿整个launch。局部字段consumer均为下方同名方法，不跨平台裸拷贝。

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | entry/router | body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R001 | c0 K | SetScenarioInfo/FillMatmul*/GenTilingKey | 208B+MMParams | mla_prolog_v3.cpp，quant10 | splitN四MM+norm/dequant/rotary/scatter ND | V3 OpDef ascend950、依赖mla_prolog、auto-sync off |
| R002 | c1 K | 同流程，PA_BSND | E0/1,A0、stride0 | 同typed entry | tokenPA ScatterCache false | 同上 |
| R003 | c2 K | 同流程，PA_NZ | BF16 NZ tile与stride0 | 同typed entry | ScatterCache true | 同上 |
| R004 | c3 K | rank3 A0/rank2 A1 | INT32 actual与INT64页表 | 同typed entry | ComputeBlkScatterOffsets/Materialize/MultiRows false | 同上 |
| R005 | c4 K | 同R004的NZ布局 | 同上+tile16 | 同typed entry | 对应NZ helper | 同上 |
| R006 | 空key | RunBigKernelTiling空分支 | block1/libWS | emptyMode==2 return | 无核心Device body | 同empty selector |
| R007 | key0 | GenTilingKey失败被忽略 | 只剩Host错误终点 | 未选合法body | 不补造 | SDK/Host边界 |
| R008 | INVALID_KEY | 条件Debug Encode失败 | 正常Host预留 | 未选合法body | 不补造 | Host/Device VERSION宏边界 |

## Kernel 实现

### 公共执行流程

entry保存overflow控制位60，空query提前return；正常读取208B POD，创建TPipe，置overflow0，构造本typed对象，Init绑定GM→MM参数→workspace→AIC/AIV buffer，Process结束恢复原位。AIC索引c；AIV线性v=c*r+s，配对cubeIdx=v/r。每step先MM1，再等待cache free9执行MM2（E1只跳body仍发信号），等RMS6后MM3，逐headQc-ready7后MM4。AIV首step加载常驻系数，按token分RMS/缓存，按pair分Qc列和Qr行。

```text
对b0=0,m,2m,...<T：m'=min(m,T-b0)，末step更新四MM.m及token划分
 AIC:
  MM1(X[b0*He],WDq)->W1；PIPE_FIX mode2 flag6
  wait free9；MM2或E1跳过->W0；PIPE_FIX mode2 flag4
  wait RMS6；MM3逐baseN tile->W2，逐tile PIPE_FIX mode2 flag10
  D128预载首head WUk；每head wait Qc7(>15head时偶数/最后通知)
  MM4(Qc16,WUk)->正式Query；Query offset按m*N*512跨step递增
 AIV:
  首step加载gamma/weightScales/smooth；e1 gather sincos
  wait CQ6；allV mode0 flag7；每本核token W1 dq/RMS/aq/smooth/FP8量化->Cq8/QN+sCq
  allV7；按32B槽汇总sCq至常驻UB；PIPE_MTE3 mode2 RMS6
  wait KV4；allV7；E0逐token dq/RMS/ak->KV，dq/rot或直通->Kr，分Route scatter
  PIPE_MTE3 mode2 free9
  每MM3 tile wait10，累计列末端，完整Qc头则dq两半D/2列->Qc16并通知7
  完整Qr头则按floor/ceil(m'/2)行 dq/rot或直通->正式Qr
  Qr输出基址按m*N*64跨step递增
结束：AIC drain全部L1/L0 hardevent和SCALE_EVENT，wait最后free9
```

W1→RMS与Cq→MM3分核不同，RMS前后allV7保护汇总/复用；W0跨step由free9防覆盖。MM3每tile通知10，Qc按D完整才发7，Qr按D+64完整才消费。每核head L>15时仅i偶数或i==L−1发/等Qc7，两端相同；不能将其说成一次总屏障。下一step共享scratch依赖上述固定顺序与allV屏障，Host提交一次launch本身不是这些可见性的证据。

前三MM：A ND→NZ用Nd2Nz{nValue=m',dValue=K_L1,srcDValue=orgKa,dstNzC0Stride=align16(m')}；B NZ按C0=32，以B[K*nOff+kL1*K_L1*32]为起点，DataCopy{ceil(nTile/32),K_L1,K−K_L1,0}，长度/stride单位32B。预载下一bank，MTE1消费后才释放给MTE2。A进L0 LoadData3D/WithStride，B的实际选中特化见下；L0逐K片，Mmad(align16(m'),nTile,baseK)仅首K清L0C，后续FP32累加。Fixpipe FP32→FP32保持NoQuant/无ReLU，M_FIX/FIX_M保护bank。MM3 m'≤64整载Cq A（H2048且m64刚好128KiB），其余分K双bank。MM4用BF16，D128全B128KiB并以128列四块，D192走ND B的K64×3，FP32累加后F322BF16。

**FP8搬运限制**：MatmulL0<T=FP8E4M3,S=float>调用LoadDataL1ToL0B；helper只按T判断，仍将L0B重解释mx_fp8_e4m3_t并传E8M0视图做MX LoadData。MatmulL1无条件从L1B+64KiB以及其后align16(m')*kScale建立scale视图，但w4的LoadL1AB不生产MX scale子区；此子区可未初始化或与普通B数据重叠。该调用省略kL1Size，MX srcStride按默认0形成，而Mmad随后用普通FP8类型。以上是可定位的实际调用链，不是默认空LocalTensor，也不证明这些字节参与正确数值或已发生故障；目标codegen/硬件效果本次未验证。不能把它简写为普通LoadData2D或借用w3的E8M0数值公式消除边界。

| 层级/缓冲区 | offset/地址 | 容量/extent字节 | dtype/layout | producer→consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|
| GM输入 | X[tHe]，NZ三权重，Uk[hD512] | THe+HeH+Hg+He576+2ND512 | E4M3/BF16 | caller→MTE2/Cube | caller至stream完成 | FP8 C0=32/BF16 C0=16 |
| GM scales/gamma | sX[t]、sw按channel | 4T+4H+4g+2304，gamma2H+1024，smooth?4H | FP32/BF16 | caller→AIV | 同上 | 与quant multiplier区分 |
| Sscale/W0/W1/Cq/W2/Qc16 | 前述连续slice | W_Device逐片公式 | FP32/FP8/BF16 | 四MM↔AIV | launch跨step复用 | W1/Cq和W2/Qc分别不别名 |
| 正式输出 | Q[(tN+h)512]、Qr[(tN+h)64]、QN[tH] | Q1024TN+Qr128TN；QN可选TH+4T | BF16/FP8/FP32 | AIC/AIV→后继 | caller | QN同时被MM3消费 |
| L1A/B | bank=(iter&1)*131072 | 各2*128KiB | FP8/BF16 NZ | MTE2→MTE1 | 每AIC TPipe | 实际scale视图边界如上，不能扣除未证别名 |
| L0A/B | bank=(iter&1)*32768 | 各2*32KiB | 当前typed fractal | MTE1→Mmad | 同上 | M_MTE1/MTE1_M |
| L0C | bank=(iter&1)*65536 | 2*64KiB | FP32 | Mmad→Fixpipe | 同上 | FIX_M/M_FIX或MM4 unitFlag3 |
| UB固定 | wdq4H、wdkv2304、gamma2H+1024、smooth?4H | F_req/F_alloc见下 | FP32/BF16 | 首stepMTE2→RMS/dq | 每AIV TPipe | 独立TBuf align32 |
| UB CqScale | 固定后 | 32(m+7) | FP32槽 | 本核Brcb/GM汇总→deq | launch | 实际每token重复8float，正式QNscale仅4B |
| UB sincos/actual | 独立TBuf | 512ceil(m/2)，A1额外align32(8m) | FP32/INT64预留 | Gather→Kr/Qr；actual实际直接读INT32 GM | launch | e0仍分配但不读sin/cos |
| UB share | 最后TBuf | align32(196608−F_req) | 字节按typed切片 | 当前Vector阶段→后续阶段 | launch | 使用max阶段峰值，不相加已串行区 |
| Reg | 64lane FP32、BF16/FP8 packed | 编译器分配量固定源码不可见 | typed | UB↔VF算术 | VF | 不虚报occupancy/spill |

令sm为smooth存在、a=A1、U0=TPipe实际UB起点，q为本核当前token数，rho=ceil(m'/2)、u=D/2、x=m'*u：

```text
F0=(6+4sm)H+3328+32(m+7)+512ceil(m/2)
F_req=F0+a*8m；F_alloc=F0+a*align32(8m)
S_alloc=align32(196608-F_req)
UB已申请最高位置=U0+F_alloc+S_alloc
A1且m%4!=0时F_alloc+S_alloc=196640，其余196608
```

| share阶段 | 实际最高活跃字节范围 | 数据与复用来源 |
|---|---|---|
| Cq RMS+FP8 | 9H+32q+32 | FP8输出H，scale32q，sX32，RMS FP32双H；量化Reg不另物化FP32行 |
| KV RMS | 3104+512q | sX32+双sincos512q+BF16输出1024+FP32输入2048 |
| Kr e1 | 800+512q | 外层32+512q，输出128，float Rotary helper640；不可沿用INT32输入的额外128 |
| Qc逐head | 4x+32+max(4align64(u),2x)及输入无mask尾读 | input/compute别名，scale/output顺序复用；D192/u96的scale物理load512B |
| Qr逐head e1 | 768rho+256 | 输出2*64rho，float预处理/旋转/scale顺序复用，channelScale256；无INT32 cast区 |
| 初始Qr gather | 256ceil(m'/2) | 临时BF16 sin/cos，在固定FP32 sincos之外 |
| cache内gather e1 | 32+768q | 外层sX32+双FP32 sincos512q+临时BF16 256q |

D192的Qc每行96个FP32，Reg最后tail虽然只消费32lane，LoadAlign仍读64lane；末行input可越名义子片128B，scale从4x+32开始的96元素实际load128元素。它们仍可能落在同share backing，不能由逻辑跨片直接断言物理越UB；必须结合实际S_alloc/UB pool。e0只用直通活跃子区可低于e1界，E1不消费cache阶段，但所有固定TBuf仍在。必要条件为P=max可达stage≤S_alloc、U0+F_alloc+P≤实际UB、U0+F_alloc+S_alloc≤实际pool，Host无逐stage检查。

```text
L1A bank: align16(m')*K_L1*sizeof(T)<=131072，MM3全A改H
L1B bank: K_L1*nTile*sizeof(T)<=131072
L0A bank: align16(m')*baseK*sizeof(T)<=32768
L0B bank: baseK*nTile*sizeof(T)<=32768
L0C bank: align16(m')*nTile*4<=65536
```

```mermaid
block-beta
  columns 5
  S["WDq4H+WDkv2304"] G["gamma2H+1024+smooth?4H"] C["CqScale32(m+7)"] R["sincos512ceil(m/2)+actual?align32(8m)"] W["share阶段复用"]
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| CQ→Cq8 | MM1/AIV | W1 4mH→Cq mH/QN | FP32→FP8 | MM3 | CQ6、RMS前后allV7、RMS6 | launch/QN owner | scale32B槽也须写完 |
| KVKr | MM2 | W0 2304m | FP32→BF16 | AIV/cache与下step | KV4、free9、MTE3 drain | launch/caller | E1保持信号配对 |
| Qc | MM3/AIV | W2→独立Qc16 2mND | FP32→dq→BF16 | MM4 | 逐tile10→完整head7 | launch | 同head先Qc可与后续Qr并行 |
| Qr | MM3/AIV | W2 head后64→正式Qr | FP32→dq/RoPE→BF16 | caller | tile10，V/MTE3事件 | caller | 末odd token两AIV分floor/ceil |
| UB scale/output | DequantQcQrSplitN | scale位于4x+32后 | FP32/BF16别名 | Cast后MTE3 | MTE2_V/V_MTE3，覆写前deq完成 | share | 无mask load范围也要计入 |

### Route R-001：ND

#### 适用条件

T>0、w4kv0q0、V=2C；BSND仅rank3/TND仅rank2，E0/A0。e0/1、D128/192、QN、smooth与末step均遵守公共typed流程。E1只对分页route可达，跳MM2/cache body而保留KV4/free9。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=0,E=0,A=0,deq1,splitN | K(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_NO_QUANT | FP8/FP8/BF16/float MLAPType | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共AicProcess四MM与AivProcess
 →RmsNormCqProcess→RmsNormDynamicQuant<float,...FP8,float>
 →RmsNormRopeScatterCkvKr→RmsNormNormal/RotaryPosEmbPerTensor<float,float,BF16,true,e>
 →ScatterCache<bfloat16_t,false>
 →DequantAndRopeSplitNSyncMMQcQr→DequantQcQrSplitN/RopeQrSplitN→MM4
```

##### 源码等价伪码

```text
执行公共m'/head流水；每本核token的W0先FP32 channel/token反量化；
 KV=BF16(RMS*ak)，Kr=BF16(e?相邻配对旋转:原顺序)。
 L取KV512或Kr64；slot=t；BSND P=S，TND P=0；offset= P>0 ? (t//P)*stride0+(t%P)*L : t*stride0。
 E1跳cache工作；写完MTE3后发free9；Qc/Qr继续各自逐tile/head处理。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 当前cache GM | slot=t；BSND P=S，TND P=0；offset= P>0 ? (t//P)*stride0+(t%P)*L : t*stride0 | 每token1024+128B，storage含真实stride洞 | BF16 ND | AIV | 后继attention | caller至stream完成 | 无GM index；每tokenKV1024B/Kr128B，ND的末轴连续 |
| workspace/L1/L0/UB/Reg | 公共逐片表，c=0 | W_Host/W_Device、双bank及F_alloc+P公式 | FP32/FP8/BF16 | 公共四MM/Vector | 同公共消费者 | launch/TPipe | A=0、E=0按实际值代入，不能扣除未证别名 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → 双bank L1/L0 → FP32 L0C"] --> W["FP32 W0/W1/W2"]
  W --> U["UB dq/RMS/FP8量化/RoPE"]
  U --> C["FP8 Cq / BF16 Qc → Cube"]
  U --> O["ND BF16 cache / Qr / QN"]
```

##### 字节账、交接边与复用顺序

本Route使用完整公共W/L1/L0/UB公式，deq恒1、rho=ceil(m'/2)、u=D/2；c=0决定地址，A=0决定额外align32(8m)。无GM index；每tokenKV1024B/Kr128B，ND的末轴连续。row=vectorRow=1，页内剩余行至少1时不spill，但Materialize/nextPage分支保留；不能将多行helper存在解释为当前一次搬多token。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| Qc交接 | MM3/AIV | W2→2mND Qc16 | FP32→BF16 | MM4 | tile10→head7 | launch | 首head按D齐才通知，输入g跨度/输出ND跨度不同 |
| cache交接 | MM2/AIV | W0→1024+128B有效写 | FP32→BF16 | cache/下stepMM2 | KV4/free9，局部V/MTE3 drain | caller/launch | E1跳数据仍保留同步；负offset判定不替代正上界与无冲突合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/量化 | CQ6、allV7、RMS6 | AIC/AIV | MM3 | W1/Cq/32B scale槽 | FP32 RMS与直接FP8 RINT/SAT，无中间BF16 |
| Qc/Qr | tile10、head7，L>15稀疏通知 | MM3/AIV | MM4/Qr | W2/Qc16 | D/2列vsfloor/ceil(m'/2)行，m'只提交有效行 |
| scatter | KV4/free9、V/MTE3 | MM2/AIV | cache/下一step | W0/share | e0保持原通道顺序，E1不写，物理地址按本Route |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | 当前c=0/E/A分核与容量 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant10 MLAPType | FP8/FP8/BF16/float |
| Body | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | AicProcess/AivProcess/DequantQcQrSplitN/RopeQrSplitN | 公共typed流水与head交接 |
| 地址helper | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<bfloat16_t,false> | 当前layout、stride与条件跳写 |

### Route R-002：PA_BSND

#### 适用条件

T>0、w4kv0q0、V=2C；tokenPA，E0/1,A0。e0/1、D128/192、QN、smooth与末step均遵守公共typed流程。E1只对分页route可达，跳MM2/cache body而保留KV4/free9。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=1,E=0/1,A=0,deq1,splitN | K(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_NO_QUANT | FP8/FP8/BF16/float MLAPType | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共AicProcess四MM与AivProcess
 →RmsNormCqProcess→RmsNormDynamicQuant<float,...FP8,float>
 →RmsNormRopeScatterCkvKr→RmsNormNormal/RotaryPosEmbPerTensor<float,float,BF16,true,e>
 →ScatterCache<bfloat16_t,false>
 →DequantAndRopeSplitNSyncMMQcQr→DequantQcQrSplitN/RopeQrSplitN→MM4
```

##### 源码等价伪码

```text
执行公共m'/head流水；每本核token的W0先FP32 channel/token反量化；
 KV=BF16(RMS*ak)，Kr=BF16(e?相邻配对旋转:原顺序)。
 L取KV512或Kr64；slot=index[t]；slot<0跳写，否则offset=(slot//P)*stride0+(slot%P)*L。
 E1跳cache工作；写完MTE3后发free9；Qc/Qr继续各自逐tile/head处理。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 当前cache GM | slot=index[t]；slot<0跳写，否则offset=(slot//P)*stride0+(slot%P)*L | 每token1024+128B，storage含真实stride洞 | BF16 PA_BSND | AIV | 后继attention | caller至stream完成 | 每tokenKV1024B/Kr128B，slot正上界及重复写由caller保证 |
| workspace/L1/L0/UB/Reg | 公共逐片表，c=1 | W_Host/W_Device、双bank及F_alloc+P公式 | FP32/FP8/BF16 | 公共四MM/Vector | 同公共消费者 | launch/TPipe | A=0、E=0/1按实际值代入，不能扣除未证别名 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → 双bank L1/L0 → FP32 L0C"] --> W["FP32 W0/W1/W2"]
  W --> U["UB dq/RMS/FP8量化/RoPE"]
  U --> C["FP8 Cq / BF16 Qc → Cube"]
  U --> O["PA_BSND BF16 cache / Qr / QN"]
```

##### 字节账、交接边与复用顺序

本Route使用完整公共W/L1/L0/UB公式，deq恒1、rho=ceil(m'/2)、u=D/2；c=1决定地址，A=0决定额外align32(8m)。每tokenKV1024B/Kr128B，slot正上界及重复写由caller保证。row=vectorRow=1，页内剩余行至少1时不spill，但Materialize/nextPage分支保留；不能将多行helper存在解释为当前一次搬多token。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| Qc交接 | MM3/AIV | W2→2mND Qc16 | FP32→BF16 | MM4 | tile10→head7 | launch | 首head按D齐才通知，输入g跨度/输出ND跨度不同 |
| cache交接 | MM2/AIV | W0→1024+128B有效写 | FP32→BF16 | cache/下stepMM2 | KV4/free9，局部V/MTE3 drain | caller/launch | E1跳数据仍保留同步；负offset判定不替代正上界与无冲突合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/量化 | CQ6、allV7、RMS6 | AIC/AIV | MM3 | W1/Cq/32B scale槽 | FP32 RMS与直接FP8 RINT/SAT，无中间BF16 |
| Qc/Qr | tile10、head7，L>15稀疏通知 | MM3/AIV | MM4/Qr | W2/Qc16 | D/2列vsfloor/ceil(m'/2)行，m'只提交有效行 |
| scatter | KV4/free9、V/MTE3 | MM2/AIV | cache/下一step | W0/share | e0保持原通道顺序，E1不写，物理地址按本Route |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | 当前c=1/E/A分核与容量 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant10 MLAPType | FP8/FP8/BF16/float |
| Body | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | AicProcess/AivProcess/DequantQcQrSplitN/RopeQrSplitN | 公共typed流水与head交接 |
| 地址helper | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<bfloat16_t,false> | 当前layout、stride与条件跳写 |

### Route R-003：PA_NZ

#### 适用条件

T>0、w4kv0q0、V=2C；tokenPA_NZ，E0/1,A0。e0/1、D128/192、QN、smooth与末step均遵守公共typed流程。E1只对分页route可达，跳MM2/cache body而保留KV4/free9。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=2,E=0/1,A=0,deq1,splitN | K(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_NO_QUANT | FP8/FP8/BF16/float MLAPType | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共AicProcess四MM与AivProcess
 →RmsNormCqProcess→RmsNormDynamicQuant<float,...FP8,float>
 →RmsNormRopeScatterCkvKr→RmsNormNormal/RotaryPosEmbPerTensor<float,float,BF16,true,e>
 →ScatterCache<bfloat16_t,true>
 →DequantAndRopeSplitNSyncMMQcQr→DequantQcQrSplitN/RopeQrSplitN→MM4
```

##### 源码等价伪码

```text
执行公共m'/head流水；每本核token的W0先FP32 channel/token反量化；
 KV=BF16(RMS*ak)，Kr=BF16(e?相邻配对旋转:原顺序)。
 L取KV512或Kr64；slot=index[t]；base=(slot//P)*stride0+(slot%P)*16；j通道块offset=base+j*P*16，DMA{L/16,1,0,P-1}。
 E1跳cache工作；写完MTE3后发free9；Qc/Qr继续各自逐tile/head处理。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 当前cache GM | slot=index[t]；base=(slot//P)*stride0+(slot%P)*16；j通道块offset=base+j*P*16，DMA{L/16,1,0,P-1} | 每token1024+128B，storage含真实stride洞 | BF16 PA_NZ | AIV | 后继attention | caller至stream完成 | 物理[Pnum,L/16,P,16]，每块32B，KV/Kr各用独立stride0 |
| workspace/L1/L0/UB/Reg | 公共逐片表，c=2 | W_Host/W_Device、双bank及F_alloc+P公式 | FP32/FP8/BF16 | 公共四MM/Vector | 同公共消费者 | launch/TPipe | A=0、E=0/1按实际值代入，不能扣除未证别名 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → 双bank L1/L0 → FP32 L0C"] --> W["FP32 W0/W1/W2"]
  W --> U["UB dq/RMS/FP8量化/RoPE"]
  U --> C["FP8 Cq / BF16 Qc → Cube"]
  U --> O["PA_NZ BF16 cache / Qr / QN"]
```

##### 字节账、交接边与复用顺序

本Route使用完整公共W/L1/L0/UB公式，deq恒1、rho=ceil(m'/2)、u=D/2；c=2决定地址，A=0决定额外align32(8m)。物理[Pnum,L/16,P,16]，每块32B，KV/Kr各用独立stride0。row=vectorRow=1，页内剩余行至少1时不spill，但Materialize/nextPage分支保留；不能将多行helper存在解释为当前一次搬多token。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| Qc交接 | MM3/AIV | W2→2mND Qc16 | FP32→BF16 | MM4 | tile10→head7 | launch | 首head按D齐才通知，输入g跨度/输出ND跨度不同 |
| cache交接 | MM2/AIV | W0→1024+128B有效写 | FP32→BF16 | cache/下stepMM2 | KV4/free9，局部V/MTE3 drain | caller/launch | E1跳数据仍保留同步；负offset判定不替代正上界与无冲突合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/量化 | CQ6、allV7、RMS6 | AIC/AIV | MM3 | W1/Cq/32B scale槽 | FP32 RMS与直接FP8 RINT/SAT，无中间BF16 |
| Qc/Qr | tile10、head7，L>15稀疏通知 | MM3/AIV | MM4/Qr | W2/Qc16 | D/2列vsfloor/ceil(m'/2)行，m'只提交有效行 |
| scatter | KV4/free9、V/MTE3 | MM2/AIV | cache/下一step | W0/share | e0保持原通道顺序，E1不写，物理地址按本Route |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | 当前c=2/E/A分核与容量 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant10 MLAPType | FP8/FP8/BF16/float |
| Body | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | AicProcess/AivProcess/DequantQcQrSplitN/RopeQrSplitN | 公共typed流水与head交接 |
| 地址helper | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<bfloat16_t,true> | 当前layout、stride与条件跳写 |

### Route R-004：PA_BLK_BSND

#### 适用条件

T>0、w4kv0q0、V=2C；blockPA，rank3 A0/rank2 A1+actualSeqLen，E0/1。e0/1、D128/192、QN、smooth与末step均遵守公共typed流程。E1只对分页route可达，跳MM2/cache body而保留KV4/free9。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=3,E=0/1,A=0/1,deq1,splitN | K(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_NO_QUANT | FP8/FP8/BF16/float MLAPType | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共AicProcess四MM与AivProcess
 →RmsNormCqProcess→RmsNormDynamicQuant<float,...FP8,float>
 →RmsNormRopeScatterCkvKr→RmsNormNormal/RotaryPosEmbPerTensor<float,float,BF16,true,e>
 →ComputeBlkScatterOffsets→MaterializeOffsetsWithHeadSize<bfloat16_t,false>→ScatterCacheMultiRows<bfloat16_t,false>
 →DequantAndRopeSplitNSyncMMQcQr→DequantQcQrSplitN/RopeQrSplitN→MM4
```

##### 源码等价伪码

```text
执行公共m'/head流水；每本核token的W0先FP32 channel/token反量化；
 KV=BF16(RMS*ak)，Kr=BF16(e?相邻配对旋转:原顺序)。
 L取KV512或Kr64；A0: b=t//S,u=t%S,pageBase=b*ceil(S/P)；A1:推进累计终点游标，u=t-prevPrefix，pageBase为先前序列ceil(length/P)之和；page=index[pageBase+u//P]；offset=page*stride0+(u%P)*L。
 E1跳cache工作；写完MTE3后发free9；Qc/Qr继续各自逐tile/head处理。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 当前cache GM | A0: b=t//S,u=t%S,pageBase=b*ceil(S/P)；A1:推进累计终点游标，u=t-prevPrefix，pageBase为先前序列ceil(length/P)之和；page=index[pageBase+u//P]；offset=page*stride0+(u%P)*L | 每token1024+128B，storage含真实stride洞 | BF16 PA_BLK_BSND | AIV | 后继attention | caller至stream完成 | A1另预留align32(8m) UB，但实际length为INT32直接标量GM读取，不是快照 |
| workspace/L1/L0/UB/Reg | 公共逐片表，c=3 | W_Host/W_Device、双bank及F_alloc+P公式 | FP32/FP8/BF16 | 公共四MM/Vector | 同公共消费者 | launch/TPipe | A=0/1、E=0/1按实际值代入，不能扣除未证别名 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → 双bank L1/L0 → FP32 L0C"] --> W["FP32 W0/W1/W2"]
  W --> U["UB dq/RMS/FP8量化/RoPE"]
  U --> C["FP8 Cq / BF16 Qc → Cube"]
  U --> O["PA_BLK_BSND BF16 cache / Qr / QN"]
```

##### 字节账、交接边与复用顺序

本Route使用完整公共W/L1/L0/UB公式，deq恒1、rho=ceil(m'/2)、u=D/2；c=3决定地址，A=0/1决定额外align32(8m)。A1另预留align32(8m) UB，但实际length为INT32直接标量GM读取，不是快照。row=vectorRow=1，页内剩余行至少1时不spill，但Materialize/nextPage分支保留；不能将多行helper存在解释为当前一次搬多token。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| Qc交接 | MM3/AIV | W2→2mND Qc16 | FP32→BF16 | MM4 | tile10→head7 | launch | 首head按D齐才通知，输入g跨度/输出ND跨度不同 |
| cache交接 | MM2/AIV | W0→1024+128B有效写 | FP32→BF16 | cache/下stepMM2 | KV4/free9，局部V/MTE3 drain | caller/launch | E1跳数据仍保留同步；负offset判定不替代正上界与无冲突合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/量化 | CQ6、allV7、RMS6 | AIC/AIV | MM3 | W1/Cq/32B scale槽 | FP32 RMS与直接FP8 RINT/SAT，无中间BF16 |
| Qc/Qr | tile10、head7，L>15稀疏通知 | MM3/AIV | MM4/Qr | W2/Qc16 | D/2列vsfloor/ceil(m'/2)行，m'只提交有效行 |
| scatter | KV4/free9、V/MTE3 | MM2/AIV | cache/下一step | W0/share | e0保持原通道顺序，E1不写，物理地址按本Route |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | 当前c=3/E/A分核与容量 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant10 MLAPType | FP8/FP8/BF16/float |
| Body | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | AicProcess/AivProcess/DequantQcQrSplitN/RopeQrSplitN | 公共typed流水与head交接 |
| 地址helper | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ComputeBlkScatterOffsets→MaterializeOffsetsWithHeadSize<bfloat16_t,false>→ScatterCacheMultiRows<bfloat16_t,false> | 当前layout、stride与条件跳写 |

### Route R-005：PA_BLK_NZ

#### 适用条件

T>0、w4kv0q0、V=2C；blockPA_NZ，A0/1和E0/1条件同R004。e0/1、D128/192、QN、smooth与末step均遵守公共typed流程。E1只对分页route可达，跳MM2/cache body而保留KV4/free9。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=4,E=0/1,A=0/1,deq1,splitN | K(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_NO_QUANT | FP8/FP8/BF16/float MLAPType | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共AicProcess四MM与AivProcess
 →RmsNormCqProcess→RmsNormDynamicQuant<float,...FP8,float>
 →RmsNormRopeScatterCkvKr→RmsNormNormal/RotaryPosEmbPerTensor<float,float,BF16,true,e>
 →ComputeBlkScatterOffsets→MaterializeOffsetsWithHeadSize<bfloat16_t,true>→ScatterCacheMultiRows<bfloat16_t,true>
 →DequantAndRopeSplitNSyncMMQcQr→DequantQcQrSplitN/RopeQrSplitN→MM4
```

##### 源码等价伪码

```text
执行公共m'/head流水；每本核token的W0先FP32 channel/token反量化；
 KV=BF16(RMS*ak)，Kr=BF16(e?相邻配对旋转:原顺序)。
 L取KV512或Kr64；A0/A1 page和u同R004；base=page*stride0+(u%P)*16；j通道块为base+j*P*16，DMA{L/16,1,0,P-1}。
 E1跳cache工作；写完MTE3后发free9；Qc/Qr继续各自逐tile/head处理。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 当前cache GM | A0/A1 page和u同R004；base=page*stride0+(u%P)*16；j通道块为base+j*P*16，DMA{L/16,1,0,P-1} | 每token1024+128B，storage含真实stride洞 | BF16 PA_BLK_NZ | AIV | 后继attention | caller至stream完成 | KV/Kr BF16 tile16，各自stride0；A1资源与游标同R004 |
| workspace/L1/L0/UB/Reg | 公共逐片表，c=4 | W_Host/W_Device、双bank及F_alloc+P公式 | FP32/FP8/BF16 | 公共四MM/Vector | 同公共消费者 | launch/TPipe | A=0/1、E=0/1按实际值代入，不能扣除未证别名 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → 双bank L1/L0 → FP32 L0C"] --> W["FP32 W0/W1/W2"]
  W --> U["UB dq/RMS/FP8量化/RoPE"]
  U --> C["FP8 Cq / BF16 Qc → Cube"]
  U --> O["PA_BLK_NZ BF16 cache / Qr / QN"]
```

##### 字节账、交接边与复用顺序

本Route使用完整公共W/L1/L0/UB公式，deq恒1、rho=ceil(m'/2)、u=D/2；c=4决定地址，A=0/1决定额外align32(8m)。KV/Kr BF16 tile16，各自stride0；A1资源与游标同R004。row=vectorRow=1，页内剩余行至少1时不spill，但Materialize/nextPage分支保留；不能将多行helper存在解释为当前一次搬多token。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| Qc交接 | MM3/AIV | W2→2mND Qc16 | FP32→BF16 | MM4 | tile10→head7 | launch | 首head按D齐才通知，输入g跨度/输出ND跨度不同 |
| cache交接 | MM2/AIV | W0→1024+128B有效写 | FP32→BF16 | cache/下stepMM2 | KV4/free9，局部V/MTE3 drain | caller/launch | E1跳数据仍保留同步；负offset判定不替代正上界与无冲突合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/量化 | CQ6、allV7、RMS6 | AIC/AIV | MM3 | W1/Cq/32B scale槽 | FP32 RMS与直接FP8 RINT/SAT，无中间BF16 |
| Qc/Qr | tile10、head7，L>15稀疏通知 | MM3/AIV | MM4/Qr | W2/Qc16 | D/2列vsfloor/ceil(m'/2)行，m'只提交有效行 |
| scatter | KV4/free9、V/MTE3 | MM2/AIV | cache/下一step | W0/share | e0保持原通道顺序，E1不写，物理地址按本Route |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | 当前c=4/E/A分核与容量 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant10 MLAPType | FP8/FP8/BF16/float |
| Body | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | AicProcess/AivProcess/DequantQcQrSplitN/RopeQrSplitN | 公共typed流水与head交接 |
| 地址helper | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ComputeBlkScatterOffsets→MaterializeOffsetsWithHeadSize<bfloat16_t,true>→ScatterCacheMultiRows<bfloat16_t,true> | 当前layout、stride与条件跳写 |

### Route R-006：空query

#### 适用条件

T==0，全部前置检查通过，V=2C。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host/SDK | attention/mla_prolog/op_host/mla_prolog_tiling.cpp；SDK template_argument | RunBigKernelTiling/GenTilingKey/Encode | T==0，全部前置检查通过，V=2C | blockDim1，workspace仅W_lib，空key3940352；entry不读POD/GM，不建TPipe，双cache不变 |

#### Device 数据流

##### 函数级调用链

```text
V4参数检查→RunBigKernelTiling→GenTilingKey→本Route终点
```

##### 源码等价伪码

blockDim1，workspace仅W_lib，空key3940352；entry不读POD/GM，不建TPipe，双cache不变。R006的return由constexpr EmptyTensorMode决定；R007/R008未选中合法自有body，不捏造Runtime容错或输出。

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM/workspace/L1/L0/UB/Reg | R006无算法读写；错误终点未选body | R006/007仅libWS，R008正常Host预算 | N/A | Host | 框架 | caller | 不能由预算推导错误key有Device实现 |

##### 分层内存布局

```mermaid
flowchart LR
  H["Host/SDK条件"] --> E["空query终点"]
```

##### 字节账、交接边与复用顺序

没有已选核心节点间交接；R006无计算slice，R007/008无可合法绑定的本tuple数据流。caller真实tensor生命周期仍须遵守API，不假设错误可安全续跑。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 终点 | R006 entryreturn；其余Host/SDK条件错误 | Host/SDK | Runtime边界 | N/A | 无合法数值输出可推导 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | RunBigKernelTiling/GenTilingKey | blockDim1，workspace仅W_lib，空key3940352；entry不读POD/GM，不建TPipe，双cache不变 |
| Router/SDK | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp；SDK include/utils/tiling/template_argument.h | EmptyTensorMode / Encode选择 | 只在合法空key提前return，错误key不补造实际路由 |

### Route R-007：空query核比错误被忽略

#### 适用条件

DAV3510、T==0、V=C。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host/SDK | attention/mla_prolog/op_host/mla_prolog_tiling.cpp；SDK template_argument | RunBigKernelTiling/GenTilingKey/Encode | DAV3510、T==0、V=C | GenTilingKey拒绝量化，RunBigKernelTiling空分支忽略GRAPH_FAILED；context初值key0/block1/libWS被返回成功。key0不是有效本tuple selector |

#### Device 数据流

##### 函数级调用链

```text
V4参数检查→RunBigKernelTiling→GenTilingKey→本Route终点
```

##### 源码等价伪码

GenTilingKey拒绝量化，RunBigKernelTiling空分支忽略GRAPH_FAILED；context初值key0/block1/libWS被返回成功。key0不是有效本tuple selector。R006的return由constexpr EmptyTensorMode决定；R007/R008未选中合法自有body，不捏造Runtime容错或输出。

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM/workspace/L1/L0/UB/Reg | R006无算法读写；错误终点未选body | R006/007仅libWS，R008正常Host预算 | N/A | Host | 框架 | caller | 不能由预算推导错误key有Device实现 |

##### 分层内存布局

```mermaid
flowchart LR
  H["Host/SDK条件"] --> E["空query核比错误被忽略终点"]
```

##### 字节账、交接边与复用顺序

没有已选核心节点间交接；R006无计算slice，R007/008无可合法绑定的本tuple数据流。caller真实tensor生命周期仍须遵守API，不假设错误可安全续跑。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 终点 | R006 entryreturn；其余Host/SDK条件错误 | Host/SDK | Runtime边界 | N/A | 无合法数值输出可推导 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | RunBigKernelTiling/GenTilingKey | GenTilingKey拒绝量化，RunBigKernelTiling空分支忽略GRAPH_FAILED；context初值key0/block1/libWS被返回成功。key0不是有效本tuple selector |
| Router/SDK | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp；SDK include/utils/tiling/template_argument.h | EmptyTensorMode / Encode选择 | 只在合法空key提前return，错误key不补造实际路由 |

### Route R-008：条件Debug关闭RoPE非法key

#### 适用条件

T>0、e0、Host ASCENDC_DEBUG且VERSION默认−1。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host/SDK | attention/mla_prolog/op_host/mla_prolog_tiling.cpp；SDK template_argument | RunBigKernelTiling/GenTilingKey/Encode | T>0、e0、Host ASCENDC_DEBUG且VERSION默认−1 | EncodeTilingKey的SEL缺e0，返回UINT64_MAX；GenTilingKey未检查该值，仍返回GRAPH_SUCCESS。非Debug或Host定义VERSION3时不由此形成非法key |

#### Device 数据流

##### 函数级调用链

```text
V4参数检查→RunBigKernelTiling→GenTilingKey→本Route终点
```

##### 源码等价伪码

EncodeTilingKey的SEL缺e0，返回UINT64_MAX；GenTilingKey未检查该值，仍返回GRAPH_SUCCESS。非Debug或Host定义VERSION3时不由此形成非法key。R006的return由constexpr EmptyTensorMode决定；R007/R008未选中合法自有body，不捏造Runtime容错或输出。

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM/workspace/L1/L0/UB/Reg | R006无算法读写；错误终点未选body | R006/007仅libWS，R008正常Host预算 | N/A | Host | 框架 | caller | 不能由预算推导错误key有Device实现 |

##### 分层内存布局

```mermaid
flowchart LR
  H["Host/SDK条件"] --> E["条件Debug关闭RoPE非法key终点"]
```

##### 字节账、交接边与复用顺序

没有已选核心节点间交接；R006无计算slice，R007/008无可合法绑定的本tuple数据流。caller真实tensor生命周期仍须遵守API，不假设错误可安全续跑。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 终点 | R006 entryreturn；其余Host/SDK条件错误 | Host/SDK | Runtime边界 | N/A | 无合法数值输出可推导 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | RunBigKernelTiling/GenTilingKey | EncodeTilingKey的SEL缺e0，返回UINT64_MAX；GenTilingKey未检查该值，仍返回GRAPH_SUCCESS。非Debug或Host定义VERSION3时不由此形成非法key |
| Router/SDK | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp；SDK include/utils/tiling/template_argument.h | EmptyTensorMode / Encode选择 | 只在合法空key提前return，错误key不补造实际路由 |

## 算子特定优化

### Trick T-001：MM3 A全载与baseN配合

#### 触发与源码依据

- 适用Route：R001–005。
- 触发条件：R001–005；当前FP8/S=float、初始m≤64取baseN256，m>64取128；当前m'≤64可整载A。
- Golden 来源：[连续源码](https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h#L498-L507)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
    } else {
        if constexpr (std::is_same<mmInputType, FP8E4M3>::value &&
                      isFp8E8m0) { // FP8全量化场景下L1B用满，修改baseN会造成内存踩踏
            mmQcQrParam_.baseN = 128;
        } else {
            if (mmQcQrParam_.m <= 64) { // FP8全量化场景，scale需要额外占用L1，该优化不适用
                mmQcQrParam_.baseN = 256;
            } else {
                mmQcQrParam_.baseN = 128;
            }
```

#### 机制与设计原因

当前S=float不进入MX的强制baseN128分支；A整载阈值按单字节类型为64，H最大2048使m64时128KiB恰好一bank，后续N tile复用A。末step只改m，不重选baseN，必须按初始tile配对算L0C。

#### 迁移边界

D128的m>64按K分片；D192 cap64；不能将注释中的FP8泛称误作w3/w4条件相同。 前提为本卡950/CANN9.2/FP8+FP32 scale、合法shape与实际资源；本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

D128的m>64按K分片；D192 cap64；不能将注释中的FP8泛称误作w3/w4条件相同。 固定源码的选择/实际分支提供边界依据，未据此编造测得性能或运行故障。

### Trick T-002：FP32归一化后直接动态FP8

#### 触发与源码依据

- 适用Route：R001–005。
- 触发条件：R001–005；RmsNormDynamicQuant选择非E8M0分支，ComputeVFImpl<O=E4M3FN,M=0>。
- Golden 来源：[连续源码](https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_dynamic_quant.h#L117-L126)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
        AscendC::Reg::Div(xNorm, xFp32, xScaleDup, validMask2);
        if constexpr (std::is_same<O, fp8_e4m3fn_t>::value) {
            AscendC::Reg::Cast<O, float, castTraitPack2>(yOutput, xNorm, validMask2);
        } else if constexpr (std::is_same<O, hifloat8_t>::value) {
            AscendC::Reg::Cast<O, float, castTraitF32ToHif8>(yOutput, xNorm, validMask2);
        } else {
            AscendC::Reg::Cast<half, float, castTraitF32ToHalf>(yHalf, xNorm, validMask2);
            AscendC::Reg::Cast<O, half, castTraitPack2>(yOutput, yHalf, validMask2);
        }
        AscendC::Reg::StoreAlign<O, AscendC::Reg::StoreDist::DIST_PACK4_B32>(addr, yOutput, validMask2);
```

#### 机制与设计原因

FP32 RMS/aq/smooth不先舍入BF16，直接Div及RINT/SAT转E4M3；两遍Reg读取使FP32行无需额外全行量化中间物化，scale按4B正式结果及32B内部广播槽分开。

#### 迁移边界

全零行scale0；没有M1的1e−4，不应添加epsilon或借用INT8的FP16 ODD路径。 前提为本卡950/CANN9.2/FP8+FP32 scale、合法shape与实际资源；本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

全零行scale0；没有M1的1e−4，不应添加epsilon或借用INT8的FP16 ODD路径。 固定源码的选择/实际分支提供边界依据，未据此编造测得性能或运行故障。

### Trick T-003：逐head交接与稀疏等待

#### 触发与源码依据

- 适用Route：R001–005。
- 触发条件：R001–005；dequantOpt=true，当前AIC head数L>15时偶数/最后head通知与等待。
- Golden 来源：[连续源码](https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h#L1243-L1249)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
    bool needSparseSync = subLoopTimes > MAX_SYNC_FLAG_COUNT;
    for (int64_t i = 0; i < subLoopTimes; i++) {
        if constexpr (MLAPT::enableDequantOpt) {
            if (!needSparseSync || i % 2 == 0 || i == subLoopTimes - 1) {
                CrossCoreWaitFlag(FINISH_VEC_DEQUANT_QC_SPLIT_N);
            }
        }
```

#### 机制与设计原因

MM3逐tile通知，AIV只要完整Qc头就转换并通知MM4，Qr可以后处理；L>15时生产与消费共同按偶数/最后head稀疏通知，保持相同计数协议。

#### 迁移边界

不能合并为全MM3结束一次屏障，不能只改变一侧稀疏条件；flag计数硬件与调度效果未运行验证。 前提为本卡950/CANN9.2/FP8+FP32 scale、合法shape与实际资源；本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

不能合并为全MM3结束一次屏障，不能只改变一侧稀疏条件；flag计数硬件与调度效果未运行验证。 固定源码的选择/实际分支提供边界依据，未据此编造测得性能或运行故障。

## 模板与实现对比

| 对比维度 | R001 ND | R002/R003 tokenPA | R004/R005 blockPA | 设计选择依据 |
|---|---|---|---|---|
| 命中 | BSND/TND且E0 | token index、E0/1 | rank3页表或rank2累计终点，E0/1 | Host cache mode/rank |
| 执行族 | 单MIX四MM+Vector | 相同数学但寻址不同 | 相同数学但页表/游标/UB不同 | 按独立route保存 |
| MM/tile | 全部deq1/splitN、D192 cap64 | 同 | 同 | FP8权重直接触发dequantOpt |
| workspace/L1/L0/UB | 公共typed账，A0 | 公共账，A0 | A1加align32(8m) | 不抹掉实际metadata资源 |
| 交接/同步 | tile10/head7/free9 | E1保留信号跳数据 | 同；页表直接标量读 | producer/consumer配对 |
| 精度/tail | FP32 dq/RMS、直接FP8 Cq、BF16 Qc/输出 | 相同；slot负跳写 | 相同；当前row1 | layout变化不改数学 |
| 失败边界 | shape/rank/stride | 正slot容量与冲突 | cumulative/page值域 | 无自有dense安全fallback |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | 公开文档不支持w4 | 公开文档不支持w4 | 公开场景支持，受正文guard |
| Host/Launcher | w限0/1/2，拒绝当前tuple | 同 | d462 V4/InnerV3，非空量化V=C拒绝 |
| Kernel/资源 | 不发布本FP8平台卡 | 不发布本FP8平台卡 | arch35 Reg VF、实际FP8/MX搬运特化、MIX1:2 |

## 限制与失败边界

- 固定源码支持不证明已安装wheel、动态选择的custom/opapi库与当前checkout身份一致。标准生成inner bridge、普通布局/内存准备及底层ISA是明确集成边界，不用它们替代自有Host/POD/body。
- shape/页表/scale值、stride/alias、u32乘法与所有权是调用前提；Host未逐值证明这些条件。空输入仍先走参数检查，950CV1:1空路径吞失败不应概括为全空安全。
- L0B的MX LoadData与plain FP8 Mmad条件不一致、未生产scale视图、UB独立align32、D192无mask读范围、条件Debug e0均按上文保留；不以源码闭合或lint通过宣称实际数值、安全性或性能已验证。
- 本次知识提取未执行编译、真机、数值或性能测试；不存在本次verified事件。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| SGL接入 | docs/api/zh/operators/attention/mlaprolog_v4.md | mlaprolog_v4 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SGL接入 | python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/mlaprolog_v4.py | mlaprolog_v4 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SGL接入 | python/sgl_kernel_npu/README.md | README | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/docs/aclnnMlaPrologV4WeightNz.md | aclnnMlaPrologV4WeightNz | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | version.cmake | version | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_api/aclnn_mla_prolog_v4_weight_nz.h | aclnn_mla_prolog_v4_weight_nz | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_api/aclnn_mla_prolog_v4_weight_nz.cpp | aclnn_mla_prolog_v4_weight_nz | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/torch_extension/mla_prolog.py | mla_prolog | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/torch_extension/csrc/mla_prolog.cpp | mla_prolog | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | torch_extension/cann_ops_transformer/common/aclnn_common.h | aclnn_common | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | torch_extension/cann_ops_transformer/op_builder/builder.py | builder | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/CMakeLists.txt | CMakeLists | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/mla_prolog_v3_def.cpp | mla_prolog_v3_def | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/mla_prolog_v3_tiling_register.cpp | mla_prolog_v3_tiling_register | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/mla_prolog_v3_tiling.h | mla_prolog_v3_tiling | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/mla_prolog_v3_infershape.cpp | mla_prolog_v3_infershape | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_host/mla_prolog_v3_infershape.h | mla_prolog_v3_infershape | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_host/mla_prolog_infershape.h | mla_prolog_infershape | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | mla_prolog_tiling | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_host/mla_prolog_tiling.h | mla_prolog_tiling | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_host/mla_prolog_tiling_check.cpp | mla_prolog_tiling_check | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_host/mla_prolog_tiling_check.h | mla_prolog_tiling_check | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/mla_prolog_tiling_data.h | mla_prolog_tiling_data | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/mla_prolog_template_tiling_key.h | mla_prolog_template_tiling_key | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | mla_prolog_v3 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/kernel_mla_prolog_split_n_arch35.h | kernel_mla_prolog_split_n_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/mla_prolog_comm_arch35.h | mla_prolog_comm_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/mla_prolog_vector_comm_arch35.h | mla_prolog_vector_comm_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_matmul_arch35.h | service_matmul_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_rms_norm_arch35.h | service_rms_norm_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_gather_sin_cos_arch35.h | service_gather_sin_cos_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_rotary_position_embedding_arch35.h | service_rotary_position_embedding_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | service_scatter_cache_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/service_rope_arch35.h | service_rope_arch35 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/vf/vf_rope.h | vf_rope | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/vf/vf_rms_norm.h | vf_rms_norm | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/vf/vf_comm.h | vf_comm | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_operator_block_sync_intf.h | kernel_operator_block_sync_intf | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/kernel_operator_block_sync_intf_impl.h | kernel_operator_block_sync_intf_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_operator_sys_var_intf.h | kernel_operator_sys_var_intf | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/kernel_operator_sys_var_intf_impl.h | kernel_operator_sys_var_intf_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/utils/tiling/template_argument.h | template_argument | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_struct_mm.h | kernel_struct_mm | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/utils/tiling/template_argument.cpp | template_argument | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_tpipe.h | kernel_tpipe | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/kernel_tpipe_impl.h | kernel_tpipe_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_tensor.h | kernel_tensor | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/kernel_tensor_impl.h | kernel_tensor_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/dav_3510/kernel_operator_sys_var_impl.h | kernel_operator_sys_var_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/dav_3510/kernel_operator_sync_impl.h | kernel_operator_sync_impl | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | impl/basic_api/dav_3510/kernel_tpipe_impl_c310.h | kernel_tpipe_impl_c310 | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/vf/vf_dequant.h | vf_dequant | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | attention/mla_prolog/op_kernel/arch35/vf/vf_dynamic_quant.h | vf_dynamic_quant | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| V4实现 | torch_extension/cann_ops_transformer/utils/arg_check.py | arg_check | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |
| SDK | include/basic_api/kernel_struct_fixpipe.h | kernel_struct_fixpipe | 固定来源的入口/Host/typed helper或构建/SDK边界，实际消费范围以上文为准 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 208B自然结构、五输出加cache副作用 | 字段顺序/位宽/单位/未赋字段，非旧172B | MlaPrologBaseParams/FillTiling |
| 调用顺序 | 四MM与RMS/scale/逐head交接 | CQ6/RMS6/KV4/free9/tile10/head7及allV7 | AicProcess/AivProcess |
| 数值 | FP8积FP32累加，channel后token，RMS后直接FP8 | 不插BF16中间边界、不换E8M0/E5M2或INT8 Cast链 | DequantVFImpl/RmsNormDynamicQuant/ComputeVFImpl |
| 内存 | 独立W1/Cq、W2/Qc，双bank及UB顺序复用 | 实际MX B搬运、U0/align32/Reg load物理范围 | MatmulL1/LoadDataL1ToL0B/VectorBufferInit |
| 适配 | 符合950公开tuple和资源可迁移 | 原始nullptr身份、stride0、合法页表/生命周期 | V4 TensorHolder/GetCacheStride0/ScatterCache |
| 性能 | 只提取源码机制 | 未测收益/占用/故障不得补造 | 本卡固定源码证据 |
