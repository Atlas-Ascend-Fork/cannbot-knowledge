---
type: Operator
title: MLA Prolog V4 FP8 投影与静态缓存及动态 Query 950 ACLNN 算子知识
description: 说明V4(4,1,1)的FP8投影、静态KV量化与动态Query/Qr尺度补偿，闭合26个selector、134016B后处理UB及逐head同步。
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
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_mul_qr.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_quant_pertensor.h
  role: implementation
created_at: '2026-11-09T16:36:15Z'
updated_at: '2026-11-09T16:36:38Z'
platforms:
- '950'
cann_versions:
- 9.2.0
---

# MLA Prolog V4 FP8 投影与静态缓存及动态 Query 950 ACLNN 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | aclnnMlaPrologV4WeightNzGetWorkspaceSize / aclnnMlaPrologV4WeightNz，公开 ACLNN；SGL auto/cann 调外置 cann_ops_transformer.mla_prolog |
| 计算语义 | 唯一 (weight,kv,query)=(4,1,1)：三次 E4M3FN 投影以 FP32 累加/反量化，Cq动态E4M3；BF16吸收投影后Query逐token/head动态E4M3，KV静态E4M3、Kr/Qr为BF16并补偿Qr尺度 |
| 输入输出 | X/WDq/WUqQr/WDkvKr E4M3FN；四份 FP32 scale；WUk/gamma/sin/cos BF16；可选 E4M3FN QueryNorm+FP32 scale |
| 执行类型 | 一次 MIX_CV，AIC_CUBE 四矩阵乘与 AIV_VECTOR 反量化/RMS/量化/RoPE/scatter；空 query 在 entry 提前返回 |
| Kernel 路线 | R-001–005 是五种 cache 寻址族，全部 dequantOpt=true/splitN；26 正常 typed selector；R-006–008 为空和条件错误终点 |
| 核心资源 | FP32 W0/W1/W2、E4M3 Cq、BF16 Qc与额外BF16 Qn；每 AIC 的 L1 A/B 各双128KiB，L0A/B 各双32KiB，L0C 双64KiB；每 AIV 的192KiB设计预算 |
| 来源闭包 | source_closed：V4 pair→InnerV3/OpDef→Host/POD/key→arch35 splitN 及本实例 helper；生成 bridge、普通布局准备、通用硬件 primitive 与外置 wheel 身份是集成边界 |
| 验证状态 | 本次知识提取未执行编译、真机、数值或性能测试。draft 保留选中搬运特化、UB、零 scale 和条件 key 边界；源码闭合不等同已验证正确。 |

## 接口与语义

### 计算语义

记T为展平token数，H=Hcq，N为head数，D=128/192，Ckv=512、Dr=64。MM8为E4M3FN×E4M3FN、FP32累加/输出；dq先乘FP32输出channel scale、再乘FP32 token scale。b16为Vector CAST_RINT，第四矩阵乘经Fixpipe F322BF16形成Qn16；e4为FP32→E4M3FN RINT/SAT。

```text
zQ=MM8(X,WDq)
fQ=RMS_FP32(dq(zQ,sX,sWDq),gammaQ,epsQ)*aq；可选再乘smoothQ
sCq[t]=max(abs(fQ[t,:]))/448；Cq8=e4(fQ/sCq)        FP32直接量化，无中间BF16
zQR=MM8(Cq8,WUqQr)                                FP32 [T,N,D+64]
Qc16=b16(dq(zQR[:,:,:D],sCq,sWUqQr[:,:,:D]))
Qr0=b16(e?rot(dq(zQR[:,:,D:],sCq,sWUqQr[:,:,D:])):反量化原通道顺序)
Qn16=MM4_BF16(Qc16,WUk)                           先形成BF16 [T,N,512]
sQ[t,h]=max(abs(FP32(Qn16[t,h,:])))/448            FP32 [T,N,1]
Query=e4(FP32(Qn16)/sQ)                            E4M3FN [T,N,512]
QueryRope=b16(FP32(Qr0)*(c/sQ))                     c=quantScaleCkv[0]
zKVKr=MM8(X,WDkvKr)
fKV=RMS_FP32(dq(zKVKr[:,:512],sX,sWDkvKr[:512]),gammaKV,epsKV)*ak
KV=e4(fKV*c)                                      不先转BF16，静态量化multiplier
Kr=b16(e?rot(dq(zKVKr[:,512:],sX,sWDkvKr[512:])):反量化原通道顺序)
scatter(KV,Kr)                                    原地双cache
```

旋转按相邻偶/奇配对，输出前32为even*cos−odd*sin、后32为odd*cos+even*sin；GatherSinCos已把sin前半乘−1。关闭RoPE仅跳旋转，**仍执行Qr0*(c/sQ)**。Qr0先舍入BF16再读回FP32补偿，不能把两次BF16边界合并。RMS的64lane累加/Reduce/Sqrt/Div/gamma、aq/ak及smooth顺序保持上述公式；aq/ak仅在与1差≥float epsilon时乘。

Cq和Query均用ComputeVFImpl M=0两遍amax/Div/直接E4M3 RINT/SAT；Query输入是BF16展开，Cq输入是FP32。maxInt8Tensor虽被分配/填127，当前泛型DynamicQuantPerTokenVf按O=E4M3取448，不能据变量名写127。M0无pertile M1的1e−4。全零Cq或Qn行产生scale0后继续除零，Qr补偿也除sQ；无零行保护、有限性与正c检查，不推断已验证的非有限结果。

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
| kvCacheRef/krCacheRef | TND [T,1,512/64]，BSND [B,S,1,512/64]，分页逻辑[Pnum,P,1,512/64] | KV E4M3FN / Kr BF16 IN/OUT | 内轴连续，首轴stride可含padding；NZ由route解释物理tile；双cache由caller持有 |
| cacheIndex | tokenPA [T]/[B,S]；blockPA [B,ceil(S/P)]或合轴一维页表 | INT64 ND | ND不传；负slot跳写；正上界/容量/冲突由caller保证 |
| actualSeqLen | 合轴blockPA [B] | INT32 ND | 累计终点、末值T；shape检查不扫描其值 |
| Query/QueryRope | [T,N,512/64] 或 [B,S,N,512/64] | Query E4M3FN / Qr BF16 | 新输出；不得与仍在读的输入、cache或workspace任意重叠 |
| QueryNorm/dequantScaleQNorm | 可选[T,H]或[B,S,H] / [T,1] | E4M3FN / FP32 | 开启时同一 Cq8 直接作为MM3输入；不开启返回空tensor |
| dequantScaleQNope | [T,N,1] | FP32 | 本tuple必需；每token/head的Query反量化scale，原始nullptr被V4拒绝 |
| quantScaleCkv | [1] | FP32 | 必需静态KV量化multiplier c，也用于Qr补偿；不是反量化scale |
| quantScaleCkr/kNopeClipAlpha | 缺省 | N/A | Kr保留BF16，不属于此tuple |
| attrs | w4/kv1/q1，repo0/scaleRepo0，tile128 | mode INT64；double标量转float | eps默认1e−5，aq/ak默认1，cache默认PA_BSND；doRope两值、QN与smooth均可达 |

### 入口与版本

本卡冻结 SGL dda6 文档明确引用的 ops-transformer d462 的 CANN9.2.0；SDK 固定 a63d9.2。公开产品表与场景表明确 FP8 全量化仅950，A2/A3不支持，不从 arch35 文件名扩大范围。SGL 的 torch_native 只覆盖0/2/3若干组合，w4由 auto/cann 透传，不能把公共参考当成此 tuple 的独立 golden。

[SGL V4 API](../../../../apis/sgl_kernel_npu/sgl_mlaprolog_v4.md)说明16组合和functional边界。本卡为原地五输出语义，不纳入 clone/TensorMove 的外部 Device 实现。V4 复用 InnerV3 注册名并增加 doRope，不意味着旧 V3 固定RoPE/旧172B POD是本卡ABI。当前(4,1,1)与INT8、MXFP8、HIF8及w4kv0/kv3各自为独立数学。

## Host/Launcher 执行流程

### 参数校验与前处理

SGL先判sin/cos成对，lazy导入vendor callable。vendor schema标注cache Tensor(a!)/Tensor(b!)，PrivateUse1→OpBuilder.load→C++。Builder可复用加载结果并选择CANN/vendor头库，arg_check代理只拒绝可解析pybind doc中的明确类型不匹配，未识别类型透传；这不是值域或设备安全检查。本次未运行load、编译或安装。

C++ OptionalDeviceGuard(tokenX.device)→形状与NZ格式校验→分配五输出→ACLNN_CMD。w4实际Tensor.scalar_type透传；HIF8 override强制解释只属于w5，不将uint8或E5M2改成合法w4。ResolveLogicalDims对Torch可见4D采用(s0*16,s1*16)，Host又按实际NZ storage首轴*c0恢复输出宽；inferShape要求权重逻辑rank2。QueryNorm分配取weight_dq.size(1)，故不能把裸4D storage Tensor与保留二维逻辑shape的format29权重直接等价。

V4检查模式/可选指针/doRope，TensorHolder将原始nullptr替为[0]临时descriptor；必需Qscale、可选QNscale是否允许由原始nullptr身份决定，非null空descriptor不是同一合同。holder假数据地址不可当有效GM，query返回销毁descriptor。OpDef输入AutoContiguous、cache IgnoreContiguous；普通生成bridge/布局准备为框架边界，不隐藏自有核心算子。

Host：ConvertContext校验cache内轴连续、首轴stride≥逻辑连续跨度；空cache stride0=0，缺stride descriptor才回退连续值。GetNpuInfo要求C/V>0且V=C或2C→attrs/required/cache mode→shape/scenario→repo/query模式、quant/dims/special/expected参数→attrs→ProcessBaseInputs→四MM分核→POD/WS/key。tile只接受128，即使本perTensor tuple不做pertile计算。Host不扫描页表/累计终点、scale有限性、重复slot或全部乘法溢出。真实错误状态停止后续，空query的GenTilingKey例外见R007。

### 参数、Workspace 与生命周期

记m=min(T,D==192?64:128)、g=N(D+64)、h=ND、qnf∈{0,1}；运算限定于源码u32/size_t/int64未溢出域。

```text
W_Host = W_lib + 32m + 6mH + 2304m + 4mg + 2mh + 1024mN
Device slices，从workspace参数原址开始：
Sscale [0,32m)                     FP32 [m,8]广播槽
W0     [32m,+2304m)                FP32 [m,576]，E1仍预留
W1     W0后4mH                    FP32 [m,H]
Cq8    W1后(1-qnf)mH              E4M3FN；qnf1直接正式QN
W2     Cq8后4mg                   FP32 [m,N,D+64]
Qc16   W2后2mh                    BF16 [m,N,D]
Qn16   Qc16后1024mN                BF16 [m,N,512]
W_Device = 32m+2304m+4mH+(1-qnf)mH+4mg+2mh+1024mN
```

Host按2mH预算归一化结果，实际Cq仅mH或正式QN；不能把Host上界误作同时活跃片之和。W_lib由平台GetLibApiWorkSpaceSize取得，Device未自行跳过该固定常量；生成Runtime包装如何传workspace是集成边界，不臆造16MiB偏移。

ACLNN query取得size/executor→caller分配→execute同stream。vendor使用当前NPU stream，必要时UseStreamResInCurrentThread；query/execute失败清理descriptor并抛错。byte workspace tensor为Host局部，回调捕获raw资源，未自行证明allocator/延迟队列所有权。输入、输出、两cache、index、length与workspace需存活至stream工作完成；后继cache读由同stream或event排序，不用descriptor析构替代Device完成。

### 启动图与失败传播

正常T>0一次InnerV3 MIX_AIC_1_2，blockDim=C，运行AIV线性索引v=c*r+s，r=GetSubBlockNum=2；全部950量化V=C被Host拒绝。空T正常block1、W_lib、entry在POD/TPipe/GM之前返回。Host Debug selector不匹配和空分支吞GenTilingKey错误分别见R008/R007。

```mermaid
flowchart LR
  H["V4 query/execute → 单MIX"] --> A["MM1 FP8→FP32 W1"] --> V["dq/RMS/smooth→Cq8+scale"]
  V --> B["MM3 FP8→FP32 W2"] --> D["逐head dq Qc→BF16"] --> C["MM4 BF16→Qn16→动态FP8 Query+sQ"]
  B --> R["dq Qr→RoPE/直通→BF16 Qr"]
  H --> K["MM2 FP8→FP32 W0"] --> S["KV静态FP8 / Kr BF16→cache"]
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

K(c,E,A,e)=(c,2,11,true,false,E,A,0,e,7)。c0归一BSND/TND，c1/2为tokenPA，c3/4为blockPA；E0正常/E1空cache，A1仅合轴blockPA，e=doRope。qnf、smooth、D、末step是同key的运行时分支。

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R006 | 空selector | 全部参数校验后T=0且GenTilingKey guard通过 | V=C进入R007，其它前置错失败 |
| 2 | R001–005 | K(c,E,A,e) | T>0，C>0,V=2C，合法w4kv1/q1与layout | 不合法Host失败，没有dense或Torch fallback |
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

正常实例唯一为 `MlaPrologVecS1CubS2<MLAPType<FP8E4M3,FP8E4M3,FP8E4M3,float,CACHE_MODE(c),true,false,EMPTY(E),ACTUAL(A),false,2,e>>`。前三MM输出float、Cq输出FP8，WUk/MM4/Kr/Qr均BF16，正式Query及KV为E4M3FN。实际entry指针顺序保留X、四权重、两gamma、sin/cos、cache双输入/index、四scale、两quantScale、smooth、length、clip、七GE输出、workspace、tiling；两cache的实际计算使用输出别名，不由输入指针的存在推导额外拷贝。

| Route | key/selector | 完整命中条件 | 执行族与节点 | 实际body | 内存与同步 | tail/fallback |
|---|---|---|---|---|---|---|
| R001 | K(0,0,0,e) | BSND rank3 X/cache4或TND rank2 X/cache3；非空cache | 单MIX_CV四MM与Vector | splitN→ScatterCache<FP8,false>与Kr的BF16 false | 公共W/L1/L0/UB；直接token地址 | m'行；无index fallback |
| R002 | K(1,E,0,e) | PA_BSND，rank2/3对应token index | 同上；E1跳MM2/cache | ScatterCache<FP8,false>与Kr的BF16 false | slot→页/页内；free9 | 负slot跳写；正界由caller |
| R003 | K(2,E,0,e) | PA_NZ，逻辑cache4，物理NZ | 同上 | ScatterCache<FP8,true>与Kr的BF16 true | 32B channel tile，独立stride0 | 同上 |
| R004 | K(3,E,A,e) | PA_BLK_BSND；rank3 A0，rank2 A1+actualSeqLen | 同上 | ComputeBlkScatterOffsets→分别MaterializeOffsets<FP8/BF16,false>→MultiRows | 累计终点与页表游标；A1预留8m UB | row1；值域未扫描 |
| R005 | K(4,E,A,e) | PA_BLK_NZ；A0/1条件同R004 | 同上 | 对应NZ Materialize/MultiRows | tile内地址与独立stride0 | row1；无非法页安全fallback |
| R006 | 空key | T0,V=2C，前置合同满足 | entryreturn | 不建TPipe/不读POD | 仅libWS | cache不动 |
| R007 | key0 | T0,V=C | 无合法选定body | Host吞失败 | block1/libWS | Runtime边界 |
| R008 | INVALID_KEY | 条件Debug e0 | 无合法选定body | SDK Encode/SEL拒绝 | 正常Host预留 | Host不再检查INVALID_KEY |

SDK实际DECL宽度为4/2/4/1/1/2/2/2/1/8，数值为 `K=c+32+(11<<6)+(1<<10)+(E<<12)+(A<<14)+(e<<18)+(7<<19)`。头文件旧bit注释不能当ABI。Debug Encode验证SEL，非Debug FastEncode仅DECL；Host默认VERSION=-1使ENABLE_ROPE_SEL只含1，Device TU定义3允许0/1。正常26交集逐项如下；SEL中deq0、group、A1与不合layout的组合不扩大Host可达域。

| Route | (c,E,A,e) | uint64 key |
|---|---|---|
| R001 | (0,0,0,0) | 3671776 |
| R001 | (0,0,0,1) | 3933920 |
| R002 | (1,0,0,0) | 3671777 |
| R002 | (1,0,0,1) | 3933921 |
| R002 | (1,1,0,0) | 3675873 |
| R002 | (1,1,0,1) | 3938017 |
| R003 | (2,0,0,0) | 3671778 |
| R003 | (2,0,0,1) | 3933922 |
| R003 | (2,1,0,0) | 3675874 |
| R003 | (2,1,0,1) | 3938018 |
| R004 | (3,0,0,0) | 3671779 |
| R004 | (3,0,0,1) | 3933923 |
| R004 | (3,0,1,0) | 3688163 |
| R004 | (3,0,1,1) | 3950307 |
| R004 | (3,1,0,0) | 3675875 |
| R004 | (3,1,0,1) | 3938019 |
| R004 | (3,1,1,0) | 3692259 |
| R004 | (3,1,1,1) | 3954403 |
| R005 | (4,0,0,0) | 3671780 |
| R005 | (4,0,0,1) | 3933924 |
| R005 | (4,0,1,0) | 3688164 |
| R005 | (4,0,1,1) | 3950308 |
| R005 | (4,1,0,0) | 3675876 |
| R005 | (4,1,0,1) | 3938020 |
| R005 | (4,1,1,0) | 3692260 |
| R005 | (4,1,1,1) | 3954404 |
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
| BaseParams | kvQuantMode | uint32_t/32 | offset120，4B | mode | FillTiling/CoreParams：1 | KV perTensor；值1 | mode |
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
| R001 | c0 K | SetScenarioInfo/FillMatmul*/GenTilingKey | 208B+MMParams | mla_prolog_v3.cpp，quant11 | splitN四MM+norm/dequant/rotary/scatter ND | V3 OpDef ascend950、依赖mla_prolog、auto-sync off |
| R002 | c1 K | 同流程，PA_BSND | E0/1,A0、stride0 | 同typed entry | tokenPA ScatterCache false | 同上 |
| R003 | c2 K | 同流程，PA_NZ | KV的FP8 tile32/Kr的BF16 tile16与各自stride0 | 同typed entry | ScatterCache true | 同上 |
| R004 | c3 K | rank3 A0/rank2 A1 | INT32 actual与INT64页表 | 同typed entry | ComputeBlkScatterOffsets/FP8与BF16分别Materialize/MultiRows false | 同上 |
| R005 | c4 K | 同R004的NZ布局 | 同上，KV tile32/Kr tile16 | 同typed entry | 对应NZ helper | 同上 |
| R006 | 空key | RunBigKernelTiling空分支 | block1/libWS | emptyMode==2 return | 无核心Device body | 同empty selector |
| R007 | key0 | GenTilingKey失败被忽略 | 只剩Host错误终点 | 未选合法body | 不补造 | SDK/Host边界 |
| R008 | INVALID_KEY | 条件Debug Encode失败 | 正常Host预留 | 未选合法body | 不补造 | Host/Device VERSION宏边界 |

## Kernel 实现

### 公共执行流程

entry保存overflow控制位60，空query提前return；正常读取208B POD，创建TPipe，置overflow0，构造本typed对象，Init绑定GM→MM参数→workspace→AIC/AIV buffer，Process结束恢复原位。AIC索引c；AIV线性v=c*r+s，配对cubeIdx=v/r。每step先MM1，再等待cache free9执行MM2（E1只跳body仍发信号），等RMS6后MM3，逐headQc-ready7后MM4；每head PIPE_FIX mode2 flag8交给Query动态量化。AIV首step加载常驻系数，按token分RMS/缓存，按pair分Qc列和Qr行。

```text
对b0=0,m,2m,...<T：m'=min(m,T-b0)，末step更新四MM.m及token划分
 AIC:
  MM1(X[b0*He],WDq)->W1；PIPE_FIX mode2 flag6
  wait free9；MM2或E1跳过->W0；PIPE_FIX mode2 flag4
  wait RMS6；MM3逐baseN tile->W2，逐tile PIPE_FIX mode2 flag10
  D128预载首head WUk；每head wait Qc7(>15head时偶数/最后通知)
  MM4(Qc16,WUk)->Qn16 workspace；每head发flag8，Qn地址按head递增，跨step复用
 AIV:
  首step加载gamma/weightScales/smooth；e1 gather sincos
  wait CQ6；allV mode0 flag7；每本核token W1 dq/RMS/aq/smooth/FP8量化->Cq8/QN+sCq
  allV7；按32B槽汇总sCq至常驻UB；PIPE_MTE3 mode2 RMS6
  wait KV4；allV7；E0逐token dq/RMS/ak->KV，dq/rot或直通->Kr，分Route scatter
  PIPE_MTE3 mode2 free9
  每MM3 tile wait10，累计列末端，完整Qc头则dq两半D/2列->Qc16并通知7
  完整Qr头则按floor/ceil(m'/2)行 dq/rot或直通->Qr0；每head wait8后Qn动态FP8量化并补偿Qr0
  Qr输出基址按m*N*64跨step递增
结束：AIC drain全部L1/L0 hardevent和SCALE_EVENT，wait最后free9
```

W1→RMS与Cq→MM3分核不同，RMS前后allV7保护汇总/复用；W0跨step由free9防覆盖。MM3每tile通知10，Qc按D完整才发7，Qr按D+64完整才消费。Query末端每head仍单独发/等8，不继承7的稀疏条件；若特定可达核配置令未消费8计数超过15，源码无相同节流，须保留该条件资源边界而不声称真机故障。每核head L>15时仅i偶数或i==L−1发/等Qc7，两端相同；不能将其说成一次总屏障。下一step共享scratch依赖上述固定顺序与allV屏障，Host提交一次launch本身不是这些可见性的证据。

前三MM：A ND→NZ用Nd2Nz{nValue=m',dValue=K_L1,srcDValue=orgKa,dstNzC0Stride=align16(m')}；B NZ按C0=32，以B[K*nOff+kL1*K_L1*32]为起点，DataCopy{ceil(nTile/32),K_L1,K−K_L1,0}，长度/stride单位32B。预载下一bank，MTE1消费后才释放给MTE2。A进L0 LoadData3D/WithStride，B的实际选中特化见下；L0逐K片，Mmad(align16(m'),nTile,baseK)仅首K清L0C，后续FP32累加。Fixpipe FP32→FP32保持NoQuant/无ReLU，M_FIX/FIX_M保护bank。MM3 m'≤64整载Cq A（H2048且m64刚好128KiB），其余分K双bank。MM4用BF16，D128全B128KiB并以128列四块，D192走ND B的K64×3，FP32累加后F322BF16。

**FP8搬运限制**：MatmulL0<T=FP8E4M3,S=float>调用LoadDataL1ToL0B；helper只按T判断，仍将L0B重解释mx_fp8_e4m3_t并传E8M0视图做MX LoadData。MatmulL1无条件从L1B+64KiB以及其后align16(m')*kScale建立scale视图，但w4的LoadL1AB不生产MX scale子区；此子区可未初始化或与普通B数据重叠。该调用省略kL1Size，MX srcStride按默认0形成，而Mmad随后用普通FP8类型。以上是可定位的实际调用链，不是默认空LocalTensor，也不证明这些字节参与正确数值或已发生故障；目标codegen/硬件效果本次未验证。不能把它简写为普通LoadData2D或借用w3的E8M0数值公式消除边界。

| 层级/缓冲区 | offset/地址 | 容量/extent字节 | dtype/layout | producer→consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|
| GM输入 | X[tHe]，NZ三权重，Uk[hD512] | THe+HeH+Hg+He576+2ND512 | E4M3/BF16 | caller→MTE2/Cube | caller至stream完成 | FP8 C0=32/BF16 C0=16 |
| GM scales/gamma | sX[t]、sw按channel | 4T+4H+4g+2304，gamma2H+1024，smooth?4H | FP32/BF16 | caller→AIV | 同上 | 与quant multiplier区分 |
| Sscale/W0/W1/Cq/W2/Qc16 | 前述连续slice | W_Device逐片公式 | FP32/FP8/BF16 | 四MM↔AIV | launch跨step复用 | W1/Cq和W2/Qc分别不别名；额外Qn16 workspace |
| 正式输出 | Q[(tN+h)512]、Qr[(tN+h)64]、QN[tH] | Q512TN+Qr128TN+sQ4TN；QN可选TH+4T | FP8/BF16/FP32 | AIC/AIV→后继 | caller | QN同时被MM3消费 |
| L1A/B | bank=(iter&1)*131072 | 各2*128KiB | FP8/BF16 NZ | MTE2→MTE1 | 每AIC TPipe | 实际scale视图边界如上，不能扣除未证别名 |
| L0A/B | bank=(iter&1)*32768 | 各2*32KiB | 当前typed fractal | MTE1→Mmad | 同上 | M_MTE1/MTE1_M |
| L0C | bank=(iter&1)*65536 | 2*64KiB | FP32 | Mmad→Fixpipe | 同上 | FIX_M/M_FIX或MM4 unitFlag3 |
| UB固定 | wdq4H、wdkv2304、gamma2H+1024、smooth?4H、静态c32 | F_req/F_alloc见下 | FP32/BF16 | 首stepMTE2→RMS/dq | 每AIV TPipe | 独立TBuf align32 |
| UB CqScale | 固定后 | 32(m+7) | FP32槽 | 本核Brcb/GM汇总→deq | launch | 实际每token重复8float，正式QNscale仅4B |
| UB sincos/actual | 独立TBuf | 512ceil(m/2)，A1额外align32(8m) | FP32/INT64预留 | Gather→Kr/Qr；actual实际直接读INT32 GM | launch | e0仍分配但不读sin/cos |
| UB share | 最后TBuf | align32(196608−F_req) | 字节按typed切片 | 当前Vector阶段→后续阶段 | launch | 使用max阶段峰值，不相加已串行区 |
| Reg | 64lane FP32、BF16/FP8 packed | 编译器分配量固定源码不可见 | typed | UB↔VF算术 | VF | 不虚报occupancy/spill |

令sm为smooth存在、a=A1、U0=TPipe实际UB起点，q为本核当前token数，rho=ceil(m'/2)、u=D/2、x=m'*u：

```text
F0=(6+4sm)H+3360+32(m+7)+512ceil(m/2)
F_req=F0+a*8m；F_alloc=F0+a*align32(8m)
S_alloc=align32(196608-F_req)
UB已申请最高位置=U0+F_alloc+S_alloc
A1且m%4!=0时F_alloc+S_alloc=196640，其余196608
```

| share阶段 | 实际最高活跃字节范围 | 数据与复用来源 |
|---|---|---|
| Cq RMS+FP8 | 9H+32q+32 | FP8输出H，scale32q，sX32，RMS FP32双H；量化Reg不另物化FP32行 |
| KV RMS+静态FP8 | 4640+512q | sX32+双sincos512q+FP8输出512+FP32归一化输出2048+FP32输入2048，后两片独立 |
| Kr e1 | 800+512q | 外层32+512q，输出128，float Rotary helper640；不可沿用INT32输入的额外128 |
| Qc逐head | 4x+32+max(4align64(u),2x)及输入无mask尾读 | input/compute别名，scale/output顺序复用；D192/u96的scale物理load512B |
| Qr逐head e1 | 768rho+256 | 输出2*64rho，float预处理/旋转/scale顺序复用，channelScale256；无INT32 cast区 |
| 初始Qr gather | 256ceil(m'/2) | 临时BF16 sin/cos，在固定FP32 sincos之外 |
| cache内gather e1 | 32+768q | 外层sX32+双FP32 sincos512q+临时BF16 256q |
| Query量化+Qr补偿 | I+6144uQ+36B+36Ar≤134016 | row=rQ≤64，uQ=min(rQ,16)，B=align8(uQ)，Ar=align8(rQ)，I=1024uQ+256rQ+64；详见下方实际slice |

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
| KVKr | MM2 | W0 2304m | FP32→FP8/BF16 | AIV/cache与下step | KV4、free9、MTE3 drain | launch/caller | E1保持信号配对 |
| Qc | MM3/AIV | W2→独立Qc16 2mND | FP32→dq→BF16 | MM4 | 逐tile10→完整head7 | launch | 同head先Qc可与后续Qr并行 |
| Qr | MM3/AIV | W2 head后64→正式Qr | FP32→dq/RoPE→BF16 | caller | tile10，V/MTE3事件 | caller | 末odd token两AIV分floor/ceil |
| UB scale/output | DequantQcQrSplitN | scale位于4x+32后 | FP32/BF16别名 | Cast后MTE3 | MTE2_V/V_MTE3，覆写前deq完成 | share | 无mask load范围也要计入 |

Query末端调用链为 `DynamicQuantQnAndMulQrSyncMMQn→DynamicQuantQnWithMulQr→DynamicQuantMultiRow→DynamicQuantPerTokenVf<BF16,FP32,E4M3>→MulQr→MulQrVF`。AIC每head发flag8，AIV先drain自身Qr MTE3，再设置V_MTE2 id0/id3与MTE3_V id3初始token；每headwait8，按rQ=floor((m'+s)/2)、rowStart=floor(m'/2)*s读取Qn、Qr0，后继head各偏移512/64元素，sQ按N跨度写出。rQ=0时helper早返，outer仍消费对应head通知并最终drain初始事件。

Query workspace输入/正式输出基址分别为 `(rowStart*N+h0)*512`、`((b0+rowStart)*N+h0)*512`；sQ基址`(b0+rowStart)*N+h0`；Qr0补偿原址`((b0+rowStart)*N+h0)*64`。DynamicQuantMultiRow每次uQ=min(rQ,16)行，最后subRow更新；DMA的blockLen为512*sizeof(type)/32，gap按(N512−512)*sizeof(type)/32。FP8码值直接RINT/SAT，scale正式用DataCopyPad{row,4,0,(N−1)*4}写；32B Brcb内部广播不意味着正式scale有padding。

实际share布局：inputHalf从0起占1024uQ；qrInput接后占128rQ，后加32B gap；outputLocalRope占128rQ，再加32B gap，令之后inputLocal基址I=1024uQ+256rQ+64。inputLocal/outputLocal各2048uQ，maxInt8Tensor4B、dynamicQuantUb2048uQ+32B、scaleOutputLocal4Ar、scaleBrcb32Ar，最终最高I+6144uQ+36B+36Ar，rQ64/uQ16时134016B。inputLocal等classic暂存有的当前VF不消费，仍是实际布局reserved gap，不能凭未读直接压缩地址。

MulQr阶段在Query量化和scale Brcb之后，inputLocal起点被复用为FP32 qrFp32Local；每次最多64行，源Qr0 BF16先整体载入qrInputLocal，CAST_NONE到FP32，按c/sQ乘，再CAST_RINT回BF16。输出与输入Qr0是同一正式tensor子片，MTE3_V id1、MTE2_V id1及V_MTE3 id1控制覆写，V_MTE2 id3保护下head重载。两阶段buffer顺序复用，max而非相加；row64下此阶段不超过前述134016B最高位置。

| 补充交接边 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qn16 | MM4 Fixpipe | Qc16后1024mN，当前head512/行 | BF16 | DynamicQuantMultiRow | 每headmode2 flag8；V_MTE2/MTE3_V | launch | 跨step复用，flag8不做head7的稀疏节流 |
| Q/sQ | AIV Reg量化 | 512码字节+4B/每token-head | E4M3FN/FP32 | caller与MulQr | V/MTE3 id3，scale Brcb/V barrier | caller/share | scale0无保护，不能取1替换 |
| Qr0→Qr | AIV RoPE/直通后MulQr | 每row64 BF16 | BF16→FP32*(c/sQ)→BF16 | caller | 同AIV MTE3 drain、id1/id3 | caller | e0也补偿，原址覆写不能省读回舍入边界 |

### Route R-001：ND

#### 适用条件

(4,1,1)、T>0、V=2C，BSND rank3/cache4 或 TND rank2/cache3，E0/A0；deq恒1、splitN、repo0、scaleRepo0。e、D、QN、smooth、m'为公共typed运行分支，E1跳cache body但保留同步。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=0,A=0,quant11,deq1,splitN | 本RouteK(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_QUANT_PER_TENSOR | FP8/FP8/FP8/float，isPertile=false | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共四MM/RMS/FP8 Cq
 →RmsNormRopeScatterCkvKr→RmsNormAndQuantizeCkv→QuantPerTensor<float,FP32,FP8>
 →RotaryPosEmbPerTensor<float,float,BF16,true,e>→ScatterCache<FP8,false>；ScatterCache<BF16,false>
 →DequantQcQrSplitN/RopeQrSplitN→MM4 Qn16
 →DynamicQuantQnAndMulQrSyncMMQn→Query FP8+sQ/Qr补偿
```

##### 源码等价伪码

```text
依公共head流水计算Cq8/Qc16/Qn16/Qr0；
 E0每cache token：KV=e4(FP32 RMS*ak*c)，Kr=b16(e?rot:直通)；KV L512、1B，Kr L64、2B。
 slot=t；各cache使用自己的stride0，P>0时(slot//P)*stride0+(slot%P)*L，P0时t*stride0。
 MTE3 drain后free9；每headwait8，BF16 Qn动态FP8量化，Qr0乘c/sQ后BF16覆写；e0同样补偿。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| cache GM | slot=t；各cache使用自己的stride0，P>0时(slot//P)*stride0+(slot%P)*L，P0时t*stride0 | KV512+Kr128B/有效token | FP8/BF16 ND | AIV | 后继attention | caller至stream完成 | 各自stride0/物理tile；负slot跳写，正界/重复冲突caller保证 |
| 中间/片上 | 公共完整表，当前c=0,A=0 | W_Device含Qn16，F_alloc+32B c，P含134016B Query frame | FP32/FP8/BF16 | 四MM/Vector | 同公共消费者 | launch/TPipe | A1追加align32(8m)，不能去掉reserved gap或double深度 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → L1/L0 → FP32 W"] --> U["UB dq/RMS/量化"]
  U --> C["FP8 Cq / BF16 Qc → Cube"] --> Q["BF16 Qn workspace → FP8 Query+sQ"]
  U --> K["ND FP8 KV / BF16 Kr"]
  U --> R["BF16 Qr0 → FP32补偿 → BF16 Qr"]
```

##### 字节账、交接边与复用顺序

本Route完整使用公共逐片式：W_Host/W_Device均含1024mN Qn16；F0常驻c32；KV阶段4640+512q，Query frame≤134016B，按最大阶段比较S_alloc与U0/pool。index若使用则直接标量读取，不创建页表向量快照。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qc→Qn16→Q | MM3/AIV/MM4 | W2/Qc16/独立Qn16 | FP32→BF16→FP8 | MM4/Query量化 | tile10/head7/每head8 | launch/caller | 8不稀疏，Qn先舍入BF16 |
| cache | MM2/AIV | W0→KV512+Kr128B | FP32→FP8/BF16 | cache/下一step | KV4/free9、V/MTE3 | caller/launch | KV不先转BF16；E1仍配信号 |
| Qr0→Qr | AIV | 同正式Qr子片原址 | BF16/FP32/BF16 | caller | MTE3 drain/id1/id3 | caller | 关闭旋转仍补偿 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/Cq/cache | CQ6/RMS6/allV7/KV4/free9 | AIC/AIV | MM3/cache/下一step | W/scale/share | Cq/KV FP32直接FP8 RINT/SAT，Kr BF16 |
| Qc/Qr0 | tile10/head7 | MM3/AIV | MM4 | W2/Qc16 | Qc沿D/2列，Qr沿floor/ceil(m'/2)行 |
| Q/sQ/Qr | 每head8与局部事件 | MM4/AIV | Query/CQr后处理 | Qn16/Qr0 | row0早返，列512/64满Reg；scale0无保护 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | c=0/E/A分核和额外Qn16 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant11 MLAPType | FP8/FP8/FP8/float |
| cache | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<FP8,false>；ScatterCache<BF16,false> | 各typed地址/stride/tile |
| Query | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | DynamicQuantQnWithMulQr | 双阶段实际UB/事件/复用 |

### Route R-002：PA_BSND

#### 适用条件

(4,1,1)、T>0、V=2C，tokenPA，E0/1,A0；deq恒1、splitN、repo0、scaleRepo0。e、D、QN、smooth、m'为公共typed运行分支，E1跳cache body但保留同步。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=1,A=0,quant11,deq1,splitN | 本RouteK(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_QUANT_PER_TENSOR | FP8/FP8/FP8/float，isPertile=false | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共四MM/RMS/FP8 Cq
 →RmsNormRopeScatterCkvKr→RmsNormAndQuantizeCkv→QuantPerTensor<float,FP32,FP8>
 →RotaryPosEmbPerTensor<float,float,BF16,true,e>→ScatterCache<FP8,false>；ScatterCache<BF16,false>
 →DequantQcQrSplitN/RopeQrSplitN→MM4 Qn16
 →DynamicQuantQnAndMulQrSyncMMQn→Query FP8+sQ/Qr补偿
```

##### 源码等价伪码

```text
依公共head流水计算Cq8/Qc16/Qn16/Qr0；
 E0每cache token：KV=e4(FP32 RMS*ak*c)，Kr=b16(e?rot:直通)；KV L512、1B，Kr L64、2B。
 slot=index[t]；slot<0跳写，否则各自offset=(slot//P)*stride0+(slot%P)*L。
 MTE3 drain后free9；每headwait8，BF16 Qn动态FP8量化，Qr0乘c/sQ后BF16覆写；e0同样补偿。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| cache GM | slot=index[t]；slot<0跳写，否则各自offset=(slot//P)*stride0+(slot%P)*L | KV512+Kr128B/有效token | FP8/BF16 PA_BSND | AIV | 后继attention | caller至stream完成 | 各自stride0/物理tile；负slot跳写，正界/重复冲突caller保证 |
| 中间/片上 | 公共完整表，当前c=1,A=0 | W_Device含Qn16，F_alloc+32B c，P含134016B Query frame | FP32/FP8/BF16 | 四MM/Vector | 同公共消费者 | launch/TPipe | A1追加align32(8m)，不能去掉reserved gap或double深度 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → L1/L0 → FP32 W"] --> U["UB dq/RMS/量化"]
  U --> C["FP8 Cq / BF16 Qc → Cube"] --> Q["BF16 Qn workspace → FP8 Query+sQ"]
  U --> K["PA_BSND FP8 KV / BF16 Kr"]
  U --> R["BF16 Qr0 → FP32补偿 → BF16 Qr"]
```

##### 字节账、交接边与复用顺序

本Route完整使用公共逐片式：W_Host/W_Device均含1024mN Qn16；F0常驻c32；KV阶段4640+512q，Query frame≤134016B，按最大阶段比较S_alloc与U0/pool。index若使用则直接标量读取，不创建页表向量快照。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qc→Qn16→Q | MM3/AIV/MM4 | W2/Qc16/独立Qn16 | FP32→BF16→FP8 | MM4/Query量化 | tile10/head7/每head8 | launch/caller | 8不稀疏，Qn先舍入BF16 |
| cache | MM2/AIV | W0→KV512+Kr128B | FP32→FP8/BF16 | cache/下一step | KV4/free9、V/MTE3 | caller/launch | KV不先转BF16；E1仍配信号 |
| Qr0→Qr | AIV | 同正式Qr子片原址 | BF16/FP32/BF16 | caller | MTE3 drain/id1/id3 | caller | 关闭旋转仍补偿 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/Cq/cache | CQ6/RMS6/allV7/KV4/free9 | AIC/AIV | MM3/cache/下一step | W/scale/share | Cq/KV FP32直接FP8 RINT/SAT，Kr BF16 |
| Qc/Qr0 | tile10/head7 | MM3/AIV | MM4 | W2/Qc16 | Qc沿D/2列，Qr沿floor/ceil(m'/2)行 |
| Q/sQ/Qr | 每head8与局部事件 | MM4/AIV | Query/CQr后处理 | Qn16/Qr0 | row0早返，列512/64满Reg；scale0无保护 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | c=1/E/A分核和额外Qn16 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant11 MLAPType | FP8/FP8/FP8/float |
| cache | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<FP8,false>；ScatterCache<BF16,false> | 各typed地址/stride/tile |
| Query | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | DynamicQuantQnWithMulQr | 双阶段实际UB/事件/复用 |

### Route R-003：PA_NZ

#### 适用条件

(4,1,1)、T>0、V=2C，tokenPA_NZ，E0/1,A0；deq恒1、splitN、repo0、scaleRepo0。e、D、QN、smooth、m'为公共typed运行分支，E1跳cache body但保留同步。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=2,A=0,quant11,deq1,splitN | 本RouteK(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_QUANT_PER_TENSOR | FP8/FP8/FP8/float，isPertile=false | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共四MM/RMS/FP8 Cq
 →RmsNormRopeScatterCkvKr→RmsNormAndQuantizeCkv→QuantPerTensor<float,FP32,FP8>
 →RotaryPosEmbPerTensor<float,float,BF16,true,e>→ScatterCache<FP8,true>；ScatterCache<BF16,true>
 →DequantQcQrSplitN/RopeQrSplitN→MM4 Qn16
 →DynamicQuantQnAndMulQrSyncMMQn→Query FP8+sQ/Qr补偿
```

##### 源码等价伪码

```text
依公共head流水计算Cq8/Qc16/Qn16/Qr0；
 E0每cache token：KV=e4(FP32 RMS*ak*c)，Kr=b16(e?rot:直通)；KV L512、1B，Kr L64、2B。
 slot=index[t]；KV c0=32/Kr c0=16；base=(slot//P)*stride0+(slot%P)*c0；j块地址base+j*P*c0，DMA{L/c0,1,0,P−1}。
 MTE3 drain后free9；每headwait8，BF16 Qn动态FP8量化，Qr0乘c/sQ后BF16覆写；e0同样补偿。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| cache GM | slot=index[t]；KV c0=32/Kr c0=16；base=(slot//P)*stride0+(slot%P)*c0；j块地址base+j*P*c0，DMA{L/c0,1,0,P−1} | KV512+Kr128B/有效token | FP8/BF16 PA_NZ | AIV | 后继attention | caller至stream完成 | 各自stride0/物理tile；负slot跳写，正界/重复冲突caller保证 |
| 中间/片上 | 公共完整表，当前c=2,A=0 | W_Device含Qn16，F_alloc+32B c，P含134016B Query frame | FP32/FP8/BF16 | 四MM/Vector | 同公共消费者 | launch/TPipe | A1追加align32(8m)，不能去掉reserved gap或double深度 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → L1/L0 → FP32 W"] --> U["UB dq/RMS/量化"]
  U --> C["FP8 Cq / BF16 Qc → Cube"] --> Q["BF16 Qn workspace → FP8 Query+sQ"]
  U --> K["PA_NZ FP8 KV / BF16 Kr"]
  U --> R["BF16 Qr0 → FP32补偿 → BF16 Qr"]
```

##### 字节账、交接边与复用顺序

本Route完整使用公共逐片式：W_Host/W_Device均含1024mN Qn16；F0常驻c32；KV阶段4640+512q，Query frame≤134016B，按最大阶段比较S_alloc与U0/pool。index若使用则直接标量读取，不创建页表向量快照。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qc→Qn16→Q | MM3/AIV/MM4 | W2/Qc16/独立Qn16 | FP32→BF16→FP8 | MM4/Query量化 | tile10/head7/每head8 | launch/caller | 8不稀疏，Qn先舍入BF16 |
| cache | MM2/AIV | W0→KV512+Kr128B | FP32→FP8/BF16 | cache/下一step | KV4/free9、V/MTE3 | caller/launch | KV不先转BF16；E1仍配信号 |
| Qr0→Qr | AIV | 同正式Qr子片原址 | BF16/FP32/BF16 | caller | MTE3 drain/id1/id3 | caller | 关闭旋转仍补偿 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/Cq/cache | CQ6/RMS6/allV7/KV4/free9 | AIC/AIV | MM3/cache/下一step | W/scale/share | Cq/KV FP32直接FP8 RINT/SAT，Kr BF16 |
| Qc/Qr0 | tile10/head7 | MM3/AIV | MM4 | W2/Qc16 | Qc沿D/2列，Qr沿floor/ceil(m'/2)行 |
| Q/sQ/Qr | 每head8与局部事件 | MM4/AIV | Query/CQr后处理 | Qn16/Qr0 | row0早返，列512/64满Reg；scale0无保护 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | c=2/E/A分核和额外Qn16 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant11 MLAPType | FP8/FP8/FP8/float |
| cache | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | ScatterCache<FP8,true>；ScatterCache<BF16,true> | 各typed地址/stride/tile |
| Query | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | DynamicQuantQnWithMulQr | 双阶段实际UB/事件/复用 |

### Route R-004：PA_BLK_BSND

#### 适用条件

(4,1,1)、T>0、V=2C，blockPA，rank3 A0/rank2 A1+INT32 actual累计终点，E0/1；deq恒1、splitN、repo0、scaleRepo0。e、D、QN、smooth、m'为公共typed运行分支，E1跳cache body但保留同步。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=3,A=0/1,quant11,deq1,splitN | 本RouteK(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_QUANT_PER_TENSOR | FP8/FP8/FP8/float，isPertile=false | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共四MM/RMS/FP8 Cq
 →RmsNormRopeScatterCkvKr→RmsNormAndQuantizeCkv→QuantPerTensor<float,FP32,FP8>
 →RotaryPosEmbPerTensor<float,float,BF16,true,e>→MaterializeOffsetsWithHeadSize<FP8/BF16,false>→各自ScatterCacheMultiRows<FP8/BF16,false>
 →DequantQcQrSplitN/RopeQrSplitN→MM4 Qn16
 →DynamicQuantQnAndMulQrSyncMMQn→Query FP8+sQ/Qr补偿
```

##### 源码等价伪码

```text
依公共head流水计算Cq8/Qc16/Qn16/Qr0；
 E0每cache token：KV=e4(FP32 RMS*ak*c)，Kr=b16(e?rot:直通)；KV L512、1B，Kr L64、2B。
 A0: b=t//S,u=t%S,pageBase=b*ceil(S/P)；A1推进累计终点，u=t−prevPrefix，pageBase=先前各序列ceil(length/P)之和；page=index[pageBase+u//P]；各cache offset=page*stride0+(u%P)*L。
 MTE3 drain后free9；每headwait8，BF16 Qn动态FP8量化，Qr0乘c/sQ后BF16覆写；e0同样补偿。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| cache GM | A0: b=t//S,u=t%S,pageBase=b*ceil(S/P)；A1推进累计终点，u=t−prevPrefix，pageBase=先前各序列ceil(length/P)之和；page=index[pageBase+u//P]；各cache offset=page*stride0+(u%P)*L | KV512+Kr128B/有效token | FP8/BF16 PA_BLK_BSND | AIV | 后继attention | caller至stream完成 | 各自stride0/物理tile；负slot跳写，正界/重复冲突caller保证 |
| 中间/片上 | 公共完整表，当前c=3,A=0/1 | W_Device含Qn16，F_alloc+32B c，P含134016B Query frame | FP32/FP8/BF16 | 四MM/Vector | 同公共消费者 | launch/TPipe | A1追加align32(8m)，不能去掉reserved gap或double深度 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → L1/L0 → FP32 W"] --> U["UB dq/RMS/量化"]
  U --> C["FP8 Cq / BF16 Qc → Cube"] --> Q["BF16 Qn workspace → FP8 Query+sQ"]
  U --> K["PA_BLK_BSND FP8 KV / BF16 Kr"]
  U --> R["BF16 Qr0 → FP32补偿 → BF16 Qr"]
```

##### 字节账、交接边与复用顺序

本Route完整使用公共逐片式：W_Host/W_Device均含1024mN Qn16；F0常驻c32；KV阶段4640+512q，Query frame≤134016B，按最大阶段比较S_alloc与U0/pool。A1实际读取INT32累计终点，INT64 TBuf仅预留；当前row1不spill，保留Materialize/nextPage分支。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qc→Qn16→Q | MM3/AIV/MM4 | W2/Qc16/独立Qn16 | FP32→BF16→FP8 | MM4/Query量化 | tile10/head7/每head8 | launch/caller | 8不稀疏，Qn先舍入BF16 |
| cache | MM2/AIV | W0→KV512+Kr128B | FP32→FP8/BF16 | cache/下一step | KV4/free9、V/MTE3 | caller/launch | KV不先转BF16；E1仍配信号 |
| Qr0→Qr | AIV | 同正式Qr子片原址 | BF16/FP32/BF16 | caller | MTE3 drain/id1/id3 | caller | 关闭旋转仍补偿 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/Cq/cache | CQ6/RMS6/allV7/KV4/free9 | AIC/AIV | MM3/cache/下一step | W/scale/share | Cq/KV FP32直接FP8 RINT/SAT，Kr BF16 |
| Qc/Qr0 | tile10/head7 | MM3/AIV | MM4 | W2/Qc16 | Qc沿D/2列，Qr沿floor/ceil(m'/2)行 |
| Q/sQ/Qr | 每head8与局部事件 | MM4/AIV | Query/CQr后处理 | Qn16/Qr0 | row0早返，列512/64满Reg；scale0无保护 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | c=3/E/A分核和额外Qn16 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant11 MLAPType | FP8/FP8/FP8/float |
| cache | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | MaterializeOffsetsWithHeadSize<FP8/BF16,false>→各自ScatterCacheMultiRows<FP8/BF16,false> | 各typed地址/stride/tile |
| Query | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | DynamicQuantQnWithMulQr | 双阶段实际UB/事件/复用 |

### Route R-005：PA_BLK_NZ

#### 适用条件

(4,1,1)、T>0、V=2C，blockPA_NZ，A0/1、E0/1同R004；deq恒1、splitN、repo0、scaleRepo0。e、D、QN、smooth、m'为公共typed运行分支，E1跳cache body但保留同步。

##### 选择证据

| 层级 | 文件 | 符号 | 谓词/参数 | 结果 |
|---|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | SetScenarioInfo/ProcessBaseInputs/GenTilingKey | c=4,A=0/1,quant11,deq1,splitN | 本RouteK(c,E,A,e) |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | FP8_FULL_QUANT_KV_QUANT_PER_TENSOR | FP8/FP8/FP8/float，isPertile=false | arch35 splitN |

#### Device 数据流

##### 函数级调用链

```text
entry→Init/Process→公共四MM/RMS/FP8 Cq
 →RmsNormRopeScatterCkvKr→RmsNormAndQuantizeCkv→QuantPerTensor<float,FP32,FP8>
 →RotaryPosEmbPerTensor<float,float,BF16,true,e>→MaterializeOffsetsWithHeadSize<FP8/BF16,true>→各自ScatterCacheMultiRows<FP8/BF16,true>
 →DequantQcQrSplitN/RopeQrSplitN→MM4 Qn16
 →DynamicQuantQnAndMulQrSyncMMQn→Query FP8+sQ/Qr补偿
```

##### 源码等价伪码

```text
依公共head流水计算Cq8/Qc16/Qn16/Qr0；
 E0每cache token：KV=e4(FP32 RMS*ak*c)，Kr=b16(e?rot:直通)；KV L512、1B，Kr L64、2B。
 page/u同R004；KV c0=32/Kr c0=16，各自base=page*stride0+(u%P)*c0；j块base+j*P*c0，DMA{L/c0,1,0,P−1}。
 MTE3 drain后free9；每headwait8，BF16 Qn动态FP8量化，Qr0乘c/sQ后BF16覆写；e0同样补偿。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| cache GM | page/u同R004；KV c0=32/Kr c0=16，各自base=page*stride0+(u%P)*c0；j块base+j*P*c0，DMA{L/c0,1,0,P−1} | KV512+Kr128B/有效token | FP8/BF16 PA_BLK_NZ | AIV | 后继attention | caller至stream完成 | 各自stride0/物理tile；负slot跳写，正界/重复冲突caller保证 |
| 中间/片上 | 公共完整表，当前c=4,A=0/1 | W_Device含Qn16，F_alloc+32B c，P含134016B Query frame | FP32/FP8/BF16 | 四MM/Vector | 同公共消费者 | launch/TPipe | A1追加align32(8m)，不能去掉reserved gap或double深度 |

##### 分层内存布局

```mermaid
flowchart LR
  G["FP8 GM → L1/L0 → FP32 W"] --> U["UB dq/RMS/量化"]
  U --> C["FP8 Cq / BF16 Qc → Cube"] --> Q["BF16 Qn workspace → FP8 Query+sQ"]
  U --> K["PA_BLK_NZ FP8 KV / BF16 Kr"]
  U --> R["BF16 Qr0 → FP32补偿 → BF16 Qr"]
```

##### 字节账、交接边与复用顺序

本Route完整使用公共逐片式：W_Host/W_Device均含1024mN Qn16；F0常驻c32；KV阶段4640+512q，Query frame≤134016B，按最大阶段比较S_alloc与U0/pool。A1实际读取INT32累计终点，INT64 TBuf仅预留；当前row1不spill，保留Materialize/nextPage分支。

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 条件 |
|---|---|---|---|---|---|---|---|
| Qc→Qn16→Q | MM3/AIV/MM4 | W2/Qc16/独立Qn16 | FP32→BF16→FP8 | MM4/Query量化 | tile10/head7/每head8 | launch/caller | 8不稀疏，Qn先舍入BF16 |
| cache | MM2/AIV | W0→KV512+Kr128B | FP32→FP8/BF16 | cache/下一step | KV4/free9、V/MTE3 | caller/launch | KV不先转BF16；E1仍配信号 |
| Qr0→Qr | AIV | 同正式Qr子片原址 | BF16/FP32/BF16 | caller | MTE3 drain/id1/id3 | caller | 关闭旋转仍补偿 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| RMS/Cq/cache | CQ6/RMS6/allV7/KV4/free9 | AIC/AIV | MM3/cache/下一step | W/scale/share | Cq/KV FP32直接FP8 RINT/SAT，Kr BF16 |
| Qc/Qr0 | tile10/head7 | MM3/AIV | MM4 | W2/Qc16 | Qc沿D/2列，Qr沿floor/ceil(m'/2)行 |
| Q/sQ/Qr | 每head8与局部事件 | MM4/AIV | Query/CQr后处理 | Qn16/Qr0 | row0早返，列512/64满Reg；scale0无保护 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 事实 |
|---|---|---|---|
| Host | attention/mla_prolog/op_host/mla_prolog_tiling.cpp | FillMatmul*/CalcWorkSpace | c=4/E/A分核和额外Qn16 |
| Router | attention/mla_prolog_v3/op_kernel/mla_prolog_v3.cpp | quant11 MLAPType | FP8/FP8/FP8/float |
| cache | attention/mla_prolog/op_kernel/arch35/service_scatter_cache_arch35.h | MaterializeOffsetsWithHeadSize<FP8/BF16,true>→各自ScatterCacheMultiRows<FP8/BF16,true> | 各typed地址/stride/tile |
| Query | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | DynamicQuantQnWithMulQr | 双阶段实际UB/事件/复用 |

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

### Trick T-004：Query量化与Qr补偿共享UB

#### 触发与源码依据

- 适用Route：R001–005，(4,1,1)，每head MM4结果就绪。
- Golden 来源：[连续源码](https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h#L191-L201)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
    // Dynamic Quant & Rope Post Process UB Buffer分配
    LocalTensor<T> inputHalf = shareTmpUb.ReinterpretCast<T>();
    LocalTensor<T> qrInputLocal = inputHalf[computeSize];
    LocalTensor<T> outputLocalRope = qrInputLocal[loadRopeGmSize + inputBlockAlign];

    LocalTensor<C> inputLocal = outputLocalRope[computeSizeRope + inputBlockAlign].template ReinterpretCast<C>();
    LocalTensor<C> outputLocal = inputLocal[computeSize];
    LocalTensor<C> maxInt8Tensor = outputLocal[computeSize];
    LocalTensor<C> dynamicQuantUb = maxInt8Tensor[brcbCnt];
    LocalTensor<C> scaleOutputLocal = dynamicQuantUb[computeSize + brcbCnt * computeBlockAlign];
    LocalTensor<C> scaleBrcb = scaleOutputLocal[Align(row, computeBlockAlign)];
```

#### 机制与设计原因

两阶段依事件串行，inputLocal的FP32区域在MulQr中复用。真实起点I包含两个32B gap，Query侧reserved区域也保留，按134016B最高地址比较S_alloc；不能把逻辑输出长度代替地址账。

#### 迁移边界

950/CANN9.2/FP8静态cache与Query动态量化合同；实际row≤64、各buffer/scale生命周期满足。本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

两阶段依事件串行，inputLocal的FP32区域在MulQr中复用。真实起点I包含两个32B gap，Query侧reserved区域也保留，按134016B最高地址比较S_alloc；不能把逻辑输出长度代替地址账。 不把源码机制写成已测收益或观察到故障。

### Trick T-005：Qr按静态KV与动态Query尺度补偿

#### 触发与源码依据

- 适用Route：R001–005，(4,1,1)，每head MM4结果就绪。
- Golden 来源：[连续源码](https://gitcode.com/cann/ops-transformer/blob/d462156cf5d97712fcfeef95070d649f47d3bb6e/attention/mla_prolog/op_kernel/arch35/vf/vf_mul_qr.h#L36-L45)。

**官方源码（固定Commit连续逐字摘录）**：

```cpp
        Reg::LoadAlign<T, Reg::LoadDist::DIST_NORM>(vregSrc, inputBuf + loopOffset);
        // broadcast量化系数
        Reg::LoadAlign<T, Reg::LoadDist::DIST_BRC_B32>(vregDequantScaleVrcb, dequantScaleBrcbBuf + dequantLoopOffset);
        Reg::Duplicate(vregQuantScale, quantScaleCkvRope);

        Reg::Div(vregMulScale, vregQuantScale, vregDequantScaleVrcb, pregAll);

        Reg::Mul<T, Reg::MaskMergeMode::ZEROING>(vregRes, vregSrc, vregMulScale, pregAll);

        Reg::StoreAlign<T, Reg::StoreDist::DIST_NORM>(outputBuf + loopOffset, vregRes, pregAll);
```

#### 机制与设计原因

BF16 Qr0读回FP32后乘c/sQ，再BF16存储；关闭RoPE同样执行。c是KV量化multiplier，sQ是Query反量化scale，二者不能对调；scale0仍有除零边界。

#### 迁移边界

950/CANN9.2/FP8静态cache与Query动态量化合同；实际row≤64、各buffer/scale生命周期满足。本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

BF16 Qr0读回FP32后乘c/sQ，再BF16存储；关闭RoPE同样执行。c是KV量化multiplier，sQ是Query反量化scale，二者不能对调；scale0仍有除零边界。 不把源码机制写成已测收益或观察到故障。

## 模板与实现对比

| 对比维度 | R001 ND | R002/R003 tokenPA | R004/R005 blockPA | 设计选择依据 |
|---|---|---|---|---|
| 命中 | BSND/TND且E0 | token index、E0/1 | rank3页表或rank2累计终点，E0/1 | Host cache mode/rank |
| 执行族 | 单MIX四MM+Vector | 相同当前tuple数学但寻址不同 | 相同数学但页表/游标/UB不同 | 按独立route保存 |
| MM/tile | 全部deq1/splitN、D192 cap64 | 同 | 同 | FP8权重直接触发dequantOpt |
| workspace/L1/L0/UB | 公共typed账，A0 | 公共账，A0 | A1加align32(8m) | 不抹掉实际metadata资源 |
| 交接/同步 | tile10/head7/free9 | E1保留信号跳数据 | 同；页表直接标量读 | producer/consumer配对 |
| 精度/tail | FP32 dq/RMS、直接FP8 Cq/KV、BF16 Qc/Qn后Query量化与Qr补偿 | 相同；slot负跳写 | 相同；当前row1 | layout变化不改数学 |
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

| V4 Query/KV后处理 | attention/mla_prolog/op_kernel/arch35/service_dynamic_quant_qn_mul_qr_arch35.h | service_dynamic_quant_qn_mul_qr_arch35 | 当前静态KV/动态Query/Qr补偿与UB证据 |
| V4 Query/KV后处理 | attention/mla_prolog/op_kernel/arch35/vf/vf_mul_qr.h | vf_mul_qr | 当前静态KV/动态Query/Qr补偿与UB证据 |
| V4 Query/KV后处理 | attention/mla_prolog/op_kernel/arch35/vf/vf_quant_pertensor.h | vf_quant_pertensor | 当前静态KV/动态Query/Qr补偿与UB证据 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 208B自然结构、五输出含sQ加cache副作用 | 字段顺序/位宽/单位/未赋字段，非旧172B | MlaPrologBaseParams/FillTiling |
| 调用顺序 | 四MM与RMS/scale/逐head交接 | CQ6/RMS6/KV4/free9/tile10/head7/逐head8及allV7 | AicProcess/AivProcess |
| 数值 | FP8积FP32累加，channel后token，RMS后直接FP8 | 不插BF16中间边界、不换E8M0/E5M2或INT8 Cast链 | DequantVFImpl/RmsNormDynamicQuant/ComputeVFImpl |
| 内存 | 独立W1/Cq、W2/Qc，双bank及UB顺序复用 | 实际MX B搬运、U0/align32/Reg load物理范围 | MatmulL1/LoadDataL1ToL0B/VectorBufferInit |
| 适配 | 符合950公开tuple和资源可迁移 | 原始nullptr身份、stride0、合法页表/生命周期 | V4 TensorHolder/GetCacheStride0/ScatterCache |
| 性能 | 只提取源码机制 | 未测收益/占用/故障不得补造 | 本卡固定源码证据 |
