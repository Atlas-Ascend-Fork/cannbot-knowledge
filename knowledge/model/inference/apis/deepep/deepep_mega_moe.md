---
type: API
title: DeepEP MegaMoe：量化映射、权重布局与对称缓冲生命周期
description: 说明 CANN9.2.0 MegaMoe 的A3与950精度、门控及GELU公式、dtype读取层差、MX布局、自动通信与资源生命周期。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.memory
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/deep_ep.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/mega_moe.py
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/version.cmake
  role: constraint
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/csrc/mega_moe.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_api/aclnn_mega_moe.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_def.cpp
  role: constraint
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch22/mega_moe_tiling_arch22.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/csrc/comm_context.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_apt.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/README.md
  role: constraint
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/mega_moe_arch22.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/mega_moe_kernel_a3.hpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/unpermute/mc2_mega_moe_moe_token_unpermute.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/utils/gated_activation.hpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/utils/block_epilogue_pertoken_swiglu.hpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swiglu_activation.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swigluoai_activation.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/gelu_activation.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h
  role: implementation
- resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/include/hccl_mc2.h
  role: primary
- resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/src/common/hccl_mc2.cc
  role: implementation
- resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/version.cmake
  role: constraint
- resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend910/framework/op_base/src/op_base_mc2.cc
  role: primary
- resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/version.cmake
  role: constraint
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/quantize_functions.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_mmad_mx_fp8fp4.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/prologue/block_prologue_mx_fp8fp4.h
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a3
- '950'
aliases:
- MegaMoe
- FuseMode.MEGA_MOE
cann_versions:
- 9.2.0
---

# DeepEP MegaMoe：量化映射、权重布局与对称缓冲生命周期

## 可选依赖与模式映射

`FuseMode.MEGA_MOE` 由 `MegaMoeStrategy.fused_moe` 惰性导入 `cann_ops_transformer.ops.get_symm_buffer_for_mega_moe/mega_moe`；官方文档要求所有平台使用 CANN 9.2.0。缺少该包或其 JIT 构建条件时只在调用 MegaMoe 时抛异常，不必然阻止其他融合模式导入。错误提示同时要求 `ninja`。

本页的外部接口补证固定到 ops-transformer `e7da18105f08b06e01ef0fff78f439098d483746`；其 `version.cmake` 明确声明 9.2.0。实际调用是 `MegaMoeStrategy` → CANN Python `mega_moe` → `torch.ops.cann_ops_transformer.npu_mega_moe` → C++ `NpuMegaMoe` → 两段式 `aclnnMegaMoeGetWorkspaceSize/aclnnMegaMoe`。这说明固定源码中的接入与参数映射，不代表安装包二进制兼容性已实测，也不把其他 DeepEP 模式的 CANN9.1.0 范围延伸至 MegaMoe。

该策略不识别或缓存设备架构，而是按显式 quant_mode 映射 CANN 参数，再由 CANN 验证硬件兼容性。A3 使用 `0/"bf16"` 或 `1/"int8"`；950 文档要求明确选择 MXFP 字符串，不能沿用默认整数 1，也不暴露 per-token FP8。

| quant_mode | dispatch_quant_mode | 输出 dtype / FP4 weight 类型 |
| --- | --- | --- |
| `0` / `bf16` | 0 | 无量化 dtype |
| `1` / `int8` | 2 | `torch.int8` |
| `mx_fp8_e4m3` / `mx_fp8_e5m2` | 4 | 相应 FP8 dtype |
| `mx_fp4_e2m1` | 4 | `torch_npu.float4_e2m1fn_x2` 整数枚举 |
| `mx_fp8_e4m3_w4` | 4 | FP8 E4M3 activation，FP4 weight 整数枚举 |

### 精度域取决于激活和权重两侧

整数模式 0/1 只属于 MegaMoe 自己的外层映射；它们不能套用 Mode1 `FUSED_DEEP_MOE` 的兼容属性含义。CANN 的权重类型仍决定具体精度域：

| 平台 | SGL quant_mode | Linear 激活 / 权重域 | 接入约束 |
| --- | --- | --- | --- |
| A3 | `0` / `bf16` | A16W16 非量化 | CANN OpDef 包含 BF16/FP16 dtype 列，但固定 arch22 Host 进一步只接受 BF16 x；OpDef 中的 FP16 列不单独证明整条调用支持。模式名不会自动转换 x 或权重。 |
| A3 | `1` / `int8`，INT8 权重 | A8W8-INT | dispatch 输出 INT8；权重 scales 必须符合 INT 接口合同。 |
| A3 | `1` / `int8`，packed INT32 NZ 权重 | A8W4-INT | CANN bridge 将该存储声明为 INT4；不能把名称 `int8` 解释成强制 W8。 |
| 950 | `mx_fp8_e4m3` | A8W8-FP，E4M3FN | 激活与权重匹配 E4M3，scale 为 E8M0。 |
| 950 | `mx_fp8_e5m2` | A8W8-FP，E5M2 | 激活与权重匹配 E5M2，scale 为 E8M0。 |
| 950 | `mx_fp4_e2m1` | A4W4-FP，E2M1 | dispatch 和权重均为 packed FP4 E2M1。 |
| 950 | `mx_fp8_e4m3_w4` | A8W4-FP | 激活为 E4M3FN，权重为 packed FP4 E2M1；与纯 MXFP4 不同。 |

每个精度域仍需区分 SwiGLU 与 SiTU 的门控数学。上述分类只解释接口选择，不替代各精度的完整 Kernel、资源或通信实现。MegaMoe 的 SGL 枚举没有 `mx_fp4_e1m2`；Mode1 的 E1M2 权重能力和量化枚举也不能由同名融合入口推入本模式。

### A3 packed INT4 的描述符重解释

外部 `NpuMegaMoe` 的 `MakeWeightList/ConvertType` 在 arch22 上识别 INT32 backing tensor，要求其连续且为 FRACTAL_NZ；随后将最后一维乘 8，重建连续逻辑 stride，以 `ACL_INT4` 调用 `aclCreateTensor`。每个 INT32 承载八个 INT4，底层 storage 指针及原 storage_offset 数值保留；没有重新量化、解包拷贝或数值 INT32→INT4 转换。该重解释作用于两组权重列表，不能直接将普通 INT32 数值权重当作合法 packed 输入。

CANN arch22 `CheckDispatchQuantAttrs` 对 INT4/INT8 权重要求 dispatch mode 2，对 BF16/FP16 权重要求 mode 0，并核对非未定义的 dispatch 输出 dtype。因而相同 SGL `1/"int8"` 可达 W8 与 W4 两个数学域，不能省掉权重 dtype/layout/scale/bias 检查，也不能让 mode 0 配 INT 权重继续执行。

## gates 的真实dtype与读取层差

SGL只将topk_ids转INT32，topk_weights原样传入；padding也不改变其dtype。A3 CheckTopkWeightsInput允许ND BF16或FP32且shape为[B,T]，但选中A3 kernel的Unpermute实际实例为 `KernelMoeTokenUnpermute<ElementD2,int32_t,float,true>`，并将params.probs重解释成float指针后以tokenBase·T推进；并未按输入BF16选择T3。公共Unpermute虽然有泛型BF16转换分支，这不能替代调用处固定float实例。故Host接受BF16和SGL无cast不构成A3 BF16 gates完整实现支持，本页保留静态层差，不臆测已复现数值或越界故障。

950 entry则以DTYPE_TOPK_WEIGHTS注入真实BF16/FP32模板，普通Unpermute读取相应宽度、BF16显式转FP32，逐topk乘后加，最终BF16 RINT/SAT。两平台的原型接受列表不能单独替代Device dtype证据。[A3实际float实例](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/mega_moe_kernel_a3.hpp)与[950普通Unpermute](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h)提供具体读取路径。

## 容量与 padding 按模式分支

令 N 为本地 token 数、C 为 `num_max_dispatch_tokens_per_rank`。策略先拒绝 `N>C`，各 rank 应使用相同 C；A3 文档还要求 `C<=4096`，不能仅以 Python 的 N>C 检查代替平台限制。BF16/INT 路径创建长度 C 的 int8 active mask，必要时将 x、索引和权重 padding 至 C，返回输出时切回 N。MXFP 路径不 padding，mask 为 `None`，直接返回实际长度输出；950 文档要求输入为 BF16 `x[N,H]` 且 `1<=N<=C`，不同 rank 的 N 可不同；所选 FP8/FP4 dispatch 模式不会将调用输入 x 自动转换成相应 dtype。

这是一条按 `dispatch_quant_mode==4` 决定的源码分支，而不是 Python 层的 A3/950 判型结果；不能用它跳过 CANN 的平台约束。

## 950 权重、scale 与格式

设本地专家数 E=`num_experts/EP_size`、hidden 为 H、中间逻辑维度为 I。四个参数必须统一采用 E 个逐专家 Tensor 的列表，或长度为 1 的 stacked Tensor 列表；E=1 也要保持维度语义。

| 参数 | FP8 stacked shape | packed FP4 stacked shape |
| --- | --- | --- |
| GMM1 weight | `[E,2I,H]` | `[E,2I,H/2]` |
| GMM2 weight | `[E,H,I]` | `[E,H,I/2]` |
| GMM1 scale | `[E,2I,ceil(H/64),2]` | 相同 |
| GMM2 scale | `[E,H,ceil(I/64),2]` | 相同 |

scale 全部为 ND E8M0，权重/scale 连续且与 x 同设备；FP4 权重使用 uint8 打包。E5M2 的两层权重为 ND；E4M3 可用 ND/FRACTAL_NZ；纯 MXFP4 的 GMM1 为 FRACTAL_NZ、GMM2 为 FRACTAL_NZ_C0_32；A8W4-FP 两层都为 FRACTAL_NZ_C0_32。封装不负责转置、量化或 format cast，也不转换其他 fuse mode 的权重。950 Host另识别A4W4的W1 ND/W2 C0_32，但注释明确为内部保留、OpDef/公开合同未扩展，不能把这条存在的body当公开支持。FP4 ConvertType/CollectB4ShapeInfo按packed轴stride重建逻辑shape/stride，storageDims末轴与storageOffset转为nibble单位，部分fake NZ_C0_16映射真C0_32；它与A3 INT32→INT4描述符是两条不同路径。

A3 A16W16 不传 scales/bias；INT 使用 scales，A8W4-INT 额外用补偿 bias；950 要求 `l1_bias/l2_bias=None`。每个 token 的专家 ID 必须有效且不重复，wrapper 不扫描 ID 值。

## 激活参数的文档域与实际透传

SGL 文档为 MegaMoe 公开 `activation="swiglu"` 和 `"situ"`；策略只将 `situ` 改名为 CANN 的 `situglu`，其他值使用字典 `.get(activation, activation)` 原样透传。文档范围、SGL 实际转发和固定 CANN Host 接受范围需分别核对：

| SGL 入参 | 转发行为 | 固定 CANN 接受边界 |
| --- | --- | --- |
| `swiglu` | 原名；不构造 activation_params | A3/950 接受；使用默认 clamp。 |
| `situ` | 改名 `situglu`；仅此分支将有提供的 beta/linear_beta 放入字典 | A3/950 接受；CANN 校验 scale 参数。 |
| 原始 `situglu` | 原样，但不构造参数字典 | CANN 接受该名字；SGL 的 beta/linear_beta 在此拼写下不会转发。 |
| `swiglustep`、`swigluoai` | 原样；不构造参数字典 | A3 Host 接受；950 MTE 接受，950 URMA 分层 Host 拒绝这两项。 |
| `gelu` | 原样；不构造参数字典 | A3 Host 拒绝；950 Host 接受，还须满足其不拆 gate/up 的权重维度等约束。 |
| `None` 或其他字符串 | 不自动补为 `swiglu` | CANN Python `_normalize_activation_params` 拒绝不在其五项集合中的值。 |

后三类额外拼写/激活说明源码可达性，不扩大 SGL 文档公开支持。尤其不能仅因字符串被接收就承诺相应权重形状、拓扑和数值路径均有效。`gelu` 不是另一个 SwiGLU 参数值；它的维度合同也不能直接沿用本页门控激活的 I。

SiTU 默认值需区分调用层：直接 CANN 接口未传 beta 时 `_BETA_DEFAULT=1.0`，未传 linear_beta 时不启用 up 分支软饱和。但 SGL `Buffer.fused_deep_moe` 的签名默认 beta=4.0、linear_beta=25.0，因此通常只指定 `activation="situ"` 就实际下传 [4,25]；显式令二者均 None 才回到 CANN 的 [1]。对 `activation="situ"`，非 None 的 beta/linear_beta 才会转发，CANN Host 要求它们有限且大于零。Mode1 的 C++ `Buffer::fused_deep_moe` 则使用 `beta.value_or(4.0)`，默认值不同；切换 FuseMode 不能保持相同输出的默认值假设。原始 `activation="situglu"` 即便同时给 SGL beta/linear_beta，也仍走 CANN 默认参数。

SGL 不暴露 `activation_clamp`，也不为 `swigluoai` 构造 alpha/beta 参数。固定 CANN 默认 clamp 为 FP32 最大有限值 `3.4028234663852886e38`，OAI 默认 alpha=1.702、beta=1.0；不能把 SGL 的 beta 当作已转发的 OAI beta，也不能将有限 clamp 写成真正的正无穷。`profile_enable` 在 MegaMoe 策略中未转发，不提供 Mode1 的 profile 收集行为。

## 实际激活公式、维度与精度边界

以下为已读固定实现的 Reference，保存 SGL 透传字符串的含义，不把额外 Step/OAI/GELU 加入本轮十四个完整 Operator 数学域。令 G、U 为 Linear1 的 gate/up，S(v)=v/(1+exp(-v))，c 为 clamp，默认均为 FP32 最大有限值。

| activation | 实际 FP32 运算顺序 | 参数与支持边界 |
| --- | --- | --- |
| swiglu | Gc=min(G,c)，Uc=clip(U,-c,c)，A=S(Gc)·Uc | 950 RunSwiGLU<...,IsStep=false>；A3 SwigluActivation。 |
| swiglustep | Uc=clip(U,-c,c)，先求S(G)，再A=min(S(G),c)·Uc | gate上界施加于SiLU结果，不施加原始G；A3及950 MTE有实际body，950 Layered Host拒绝。 |
| swigluoai | Gc=min(G,c)，Uc=clip(U,-c,c)，先Uc+=beta；A=Gc/(1+exp(-alpha·Gc))·Uc | 默认alpha=1.702、beta=1；OAI beta是up的加数，区别于SiTU尺度。A3及950 MTE有body，Layered拒绝。 |
| situglu | 950先Gc=min(G,c)、Uc=clip(U,-c,c)，再A=beta·TanhImpl(Gc/beta)/(1+exp(-Gc))·Uc；启用linear_beta=lambda时，将最后Uc改为lambda·TanhImpl(Uc/lambda)。A3不作该预截断，按相同表达式使用原G/U | A3用AscendC Tanh，950的Reg与FTZ flow均先预截断再用下述分段近似；SGL默认[4,25]与原始situglu默认[1]保持前文区别。 |
| gelu | square=z·z；v=z·square+(1/0.044715)·z；v*=(-1.595769121·0.044715)；A=z/(1+exp(v)) | 950 RunGeluActivation的FP32实际顺序，为tanh近似GELU；逐元素，不拆gate/up，无clamp。A3 Host拒绝。 |

A3 的 SwiGLU/Step/OAI helper 只在 c>0 时执行 clamp，c=0 会跳过；950 Reg/C API 对应 flow 直接执行 min/max。SGL 未暴露 activation_clamp，通常走正的默认值，不能把更宽 CANN 自定义 c=0 的两平台行为当作相同。CANN Python 对 swiglu/step 下传[clamp]，OAI下传[clamp,alpha,beta]，GELU下传[FLT_MAX]占位且拒绝显式clamp。950 Host对前两者允许0/1个float、OAI允许0/3个且alpha/beta有限、SiTU必须1/2个且尺度正有限、GELU必须恰一个FLT_MAX；SGL没有OAI参数dict转发，给SGL的beta不会改变OAI beta。

950 SiTU 的 TanhImpl 使用 FP32 同时计算两式，再按 abs(z)>=0.60000002384185791016 选择：

```text
q=z*z
P(z)=z+z*q*(-0.333327681+q*(0.133152977+q*(-0.0523039624+q*0.0157396831)))
TanhImpl(z) = abs(z)>=0.60000002384185791016 ? 2/(1+exp(-2*z))-1 : P(z)
```

该式保留 MulDstAdd/asc_madd 的次序；不等价于承诺使用高阶 Tanh API 或与A3逐位相同。950在3510非FTZ分支用Reg，FTZ分支用C API，计算mask与存储mask分开，无效补齐列写零。Step/OAI同样存在实际Reg与FTZ flow，不能由名称推断数值逐位一致。SGL默认topk_weights_type=0，激活内没有提前乘gates。

矩阵方向和门控维度必须一起改变，不能只替换 activation 字符串：

| 平台/激活 | 每专家W1逻辑shape | 激活输入→输出 | 每专家W2逻辑shape及scale |
| --- | --- | --- | --- |
| A3四种门控激活 | [H,2I] | Linear1输出[rows,2I]，前I gate/后I up→[rows,I] | W2[I,H]；BF16或INT量化合同按权重域选择 |
| 950 swiglu/step/OAI/situglu | [N,H]，N=2I | 逻辑前N/2与后N/2门控；内部每256列以128gate/128up拼接→[rows,I] | W2[H,I]；E8M0 SW2[H,ceil(I/64),2] |
| 950 gelu | [N,H]，仍N=2I | 整个[rows,N]逐元素→[rows,N]，activationOutputDivisor=1 | W2必须[H,N]；E8M0 SW2[H,ceil(N/64),2]，不能沿用门控W2[H,N/2] |

950 N始终在[512,8192]且256对齐，H在[1024,8192]且64对齐；GELU不因不门控而将W1输出上界再扩大一倍。FP4的上述shape为逻辑元素，物理packed轴减半；SGL仍由W2实际末维及pack factor计算缓存/预算参数，不自动转形或替换权重。A3 H要求512对齐，固定CheckXInput只BF16，即使OpDef列出FP16也不扩大本接入支持。

A3 GatedActivation::PrepareBranches先把GMM1结果转换为FP32，必要时先应用per-token反量化scale，再计算上述激活。BF16域将激活RINT写回BF16；INT8输出公共epilogue先遍历完整row取absmax，scale=absmax/127，multiplier在absmax>0时取127/absmax、否则0，再依次FP32→INT32 RINT→FP16 RINT（deqScale=1）→INT8 RINT；跨tile行会重读/重算激活，单tile保留首遍结果。不能将FP32激活名称误解成GMM2直接消费FP32。

950对GMM1的BF16结果提升FP32执行激活，先NO_SAT/RINT到BF16，再进行每32元素的MX量化（E8M0 scale）。A8W8-FP E4/E5的两次动态量化均维持各自格式；A4W4-FP仅输入/第一GMM为E2M1，激活之后实际升为E4M3，第二GMM通过AIV展开W2并在Fixpipe乘64；A8W4-FP的输入和激活均E4M3、两次GMM都展开FP4权重。输入FP4 Cast为UNKNOWN/RINT的原生packed分支，FP8 MX输出Cast为SAT/RINT；不能泛称所有格式都使用同一种饱和转换。

本节依据[arch22 gated_activation.hpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/utils/gated_activation.hpp)、[950 SwiGLU/Step](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swiglu_activation.h)、[OAI](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swigluoai_activation.h)、[GELU](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/gelu_activation.h)及[SiTU](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h)；只有接口/局部实现事实，没有为额外激活提供完整Operator验证结论。

## 对称缓冲与销毁

策略以 `(专家总数,C,topk,H,I,dispatch_quant_mode,dispatch_quant_out_dtype)` 为 key 缓存对称缓冲，缓存 miss 时调用 `get_symm_buffer_for_mega_moe(group, ..., max_recv_token_num=0)`。改变这些条件会新增缓存对象，不代表复用旧容量。FP4 物理末维通过 pack factor 2 恢复逻辑 I，不能直接用 packed shape 预算逻辑维度。

`destroy()` 逐一销毁缓存对象并清空字典，析构尝试调用它，销毁异常被捕获；本页不因此承诺进程退出时所有跨 rank 设备资源已同步完成。资源生命周期仍需结合实际 CANN 对称缓冲接口验证。

SiTU 在此映射成 MegaMoe 的 `situglu`，有提供时转发 beta/linear_beta；输出第二项为 `[E]` 的本地专家计数。验证应覆盖同 capacity 的非均匀 N、所有四种 MXFP 模式、两种 TensorList 布局与缓存条件变化。完整调用选择见[融合入口](deepep_fused_deep_moe.md)。本次未执行编译、JIT、通信、数值或性能测试。

### 匹配9.2资源前端与owner

A3 KFC builder的顺序是 HcclKfcAllocOpArgs→SetCommEngine(AIV)→SetAlgConfig→按group取comm→HcclCreateOpResCtx→FreeOpArgs→收集本地/远端默认窗口地址。固定9.2 HCCL前端明确可见：malloc HcclOpArgs，Init仅置src/dst=FP16、reduce=SUM、count=0；builder随后填写engine及algConfig。这些是创建通信资源的参数，不会将BF16业务X转换为FP16。SGL/CANN对A3采用AlltoAll opType8与fullmesh/pairwise配置；固定README要求A3多机通信域位于同一超节点，不支持双机直连或跨超节点组网；下文950的跨域自动拓扑能力不适用于A3 KFC；源码另有910B多server的BatchWrite分支，不因其存在把A3改写为该分支。

HcclCreateOpResCtx检查指针/opType、初始化环境，再将opArgs字段逐项传给HCOMM9.2的HcclCreateOpResCtxInner。Inner在910_93/A3路径构造_mc2 tag、分配/取AICPU stream，以OpParam调用AllocComResourceByTiling，再GetCommResource返回持久资源地址。FreeOpArgs只释放临时Host参数块，不释放返回的KFC context、HCOMM session或窗口；本接入层未显示完整对称资源释放协议。这里使用[HCCL9.2前端](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/src/common/hccl_mc2.cc)与[HCOMM9.2 Inner](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend910/framework/op_base/src/op_base_mc2.cc)，不以9.1或仅同名接口替代。

CreateContext用at::empty在NPU分配6156个INT32的context Tensor并拥有这24624B；CopyContextToTensor的from_blob只包装临时Host POD，再copy_到该NPU Tensor。POD内的窗口/channel地址仍引用通信对象资源；GetLocalBufferTensor才返回CCL窗口的非拥有from_blob视图。context Tensor存活不保证这些被引用资源仍有效。

950 channel路径自建大页优先CCL、首次清零、注册tag/MR并创建AIV channel；MTE直接访问IPC映射的peer窗口，URMA按ChannelEntity使用注册资源。Destroy在有自定义memHandle/deviceBuffer时先aclrtSynchronizeDevice，再清handle并只free自有deviceBuffer；没有在该层找到显式deregister/channel/enginectx逐项释放，不补造保证。UpdateGroup对已分配且带custom size resolver的channel buffer明确拒绝复用，要求新manager。950的HcclChannelContextBuilder::GetOrCreateContext缓存命中分支只更新已有窗口size而未重新填fresh Host context；A3的KfcContextBuilder则每次经GetMc2Context填KFC地址和窗口表，两者须分别核对，不把cache命中当作同轮/并发安全保证。

## 未暴露属性与自动通信拓扑

SGL 只向 `get_symm_buffer_for_mega_moe` 提供 group、专家数、capacity、topk、H、I、`max_recv_token_num=0` 和两个 dispatch 量化字段；因此 CANN `combine_quant_mode=0`、`combine_comm_mode=0`、`comm_alg=""`、`topk_weights_type=0` 沿用默认值。调用 `mega_moe` 时不传预量化输入 scales、shared-expert 权重/scales/bias 或独立 shared 量化类型；不能把 CANN 底层全部可选能力当作这个 SGL 方法已经暴露的参数。

通信拓扑仍可能自动变化。固定 CANN `SymmBuffer` 为 A3 指定 `kfc` backend，为 950 指定 `channel` backend；`CommContextManager` 根据真实 SoC 解析这张映射。950 channel builder 查询 HCCL RankGraph 的层、rank 域和链路协议：完整 UB 域使用超节点内路径；跨域检查 UB_CTP 与 UB_RTP，或域内 UB_CTP 加域间 RoCE，生成相应 topo_type。超节点内计算沿 MTE，跨域进入分层通信路径；某条拓扑未完整满足协议检查时抛错，而非无条件换用任意 transport。

所以 SGL 未暴露 comm_alg 不意味着只可达单机 MTE。跨域识别后，容量 resolver 使用实际 server 数重新计算 CCL 申请大小；`topo_type/rank_num_per_server` 从 context 写入 SymmBuffer，并传到计算调用。原缓存 key 没有增加这些拓扑字段；不得把已有 cache hit 解释成跨通信组/拓扑变更的重新建域保证。

950 分层 kernel 的编译门槛同时要求 `ASC_DEVKIT_VERSION_NUM>=90200000` 和 `HCOMM_VERSION_NUM>=90200000`。本页只记录接口、默认值、版本与生命周期边界；CANN9.1 的 SDK/HCOMM、Mode1 的 MTE 窗口 ABI或固定源码审阅均不能替代 MegaMoe9.2 的实际依赖和运行验证，也未在此宣称完整算子实现已经闭合。

### 更宽CANN合同的Reference边界

以下属性在固定CANN实现中存在，SGL MegaMoeStrategy未暴露；记录其实际typed/Host分支，不把它们写成不存在，也不将其纳入本页链接的十四个完整数学域：

| 能力/属性 | 固定9.2实际合同 | 与SGL和平台边界 |
| --- | --- | --- |
| 预量化x | dispatch_quant_mode=0且out dtype为E5M2/E4M3/E2M1，x逻辑dtype必须完全相同，scales[B,ceil(H/32)]为ND E8M0必选；内部不重新量化x。FP4 x物理uint8 packed，Python恢复逻辑H。 | 仅950 MTE，Layered Host拒绝；SGL的0/bf16不设置该MX out dtype且不传scales，因此不进入此分支。 |
| shared专家与独立量化 | 每rank0..4个，不参与远端Dispatch；本地对本rankX算两Linear/activation，最终Y额外加sum_s Oshared_s，不乘路由topk gates。shared组内部W1/W2同dtype，但可与MoE组不同；shared_expert_quant_out_dtype默认UNDEFINED继承MoE，显式可选E5M2/E4M3/E2M1，决定shared输入动态MX类型。 | 精度/format由各组自身ResolveExpertGmmMode产生：E5W8 ND/ND，E4W8 ND/ND或NZ/NZ，E4A/W4 C0_32/C0_32，E2A/W4 NZ/C0_32；A4 W1 ND为内部保留冲突。组间量化类型或GMM模式不同仅MTE可用，Layered拒绝。SGL不传shared。 |
| shared shape与预量化限制 | shared与MoE采用相同2D/3D TensorList组织；同H、同W1输出N，W2输入按gated N/2或GELU N；权重scale按各自K32分组。shared量化dtype不同会创建独立shared输入data/scale。 | 预量化x只有一份data/scales，显式shared quant dtype只能UNDEFINED或等于MoE；不能从动态BF16支持异构推成预量化任意异构。 |
| combine_quant_mode | Host接受0、3(E5M2)、4(E4M3)，选择回传量化分支；y仍BF16。 | SGL固定0；两类显式combine去重都要求combine量化0。 |
| topk_weights_type | 0不预取；1将gates随token准备给后续epilogue，在激活内预乘。 | SGL固定0，不能因选用OAI/SiTU就声称提前乘权；此开关与Combine/record布局一起变化。 |
| combine_comm_mode | MTE接受0/1，1请求rank内Combine去重；Layered接受0/2，2请求server内Combine归并。 | 0在MTE仍先请求dispatch-only dedup，容量/收益guard可关；Layered0为dedup off。MTE1还拒绝topk_weights_type=0的预量化x；1/2都要求combine_quant_mode=0。SGL只传默认0。 |
| activation_out_dtype / transpose_weight1/2 / weight1_interleave | wrapper/原型默认UNDEFINED / false / false / 0，后者为预留属性。 | SGL不提供这些参数，不据默认false推断具有自动转置或额外激活输出dtype转换。 |
| rank mask及mask_buffer | arch22支持active/rank mask相关分支，950动态MX由实际B处理。 | SGL仅非MX构造长度C的active mask；不传950 rank mask，不因共享公共context将A3 mask协议移植到950。 |

上表为[950 Host检查](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h)、[dedup选择](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp)和[公开README](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/README.md)中的合同，不提供这些扩展组合的完整Kernel闭包或已运行支持结论。通信协议、SDK/库模板不匹配及其它静态边界仍应阅读各完整Operator卡，不能以Host接受替代构建/运行证据。

## 完整数学域的实现导航

以下十四张卡分别保存一个SGL可达精度与激活数学域的完整Host/Device实现；其中draft与静态边界必须按各卡原文理解。API本页只提供合同与Reference增量，不把这些卡的源码闭包、Lint或固定版本当作编译/运行验证。

| 平台与精度 | SwiGLU | SiTU |
| --- | --- | --- |
| A3 A16W16 | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a16w16_swiglu.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a16w16_situ.md) |
| A3 A8W8-INT | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_int_swiglu.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_int_situ.md) |
| A3 A8W4-INT | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w4_int_swiglu.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w4_int_situ.md) |
| 950 A8W8-FP E4M3 | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_fp_e4m3_swiglu_950.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_fp_e4m3_situ_950.md) |
| 950 A8W8-FP E5M2 | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_fp_e5m2_swiglu_950.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w8_fp_e5m2_situ_950.md) |
| 950 A4W4-FP E2M1 | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a4w4_fp_e2m1_swiglu_950.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a4w4_fp_e2m1_situ_950.md) |
| 950 A8W4-FP E4M3/W4 | [SwiGLU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w4_fp_e4m3_swiglu_950.md) | [SiTU实现](../../operators/aclnn/transformer/moe/sgl_deepep_mega_moe_a8w4_fp_e4m3_situ_950.md) |

## Evidence

- [python/deep_ep/deep_ep/strategies/fused_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py)（primary）
- [python/deep_ep/doc/FUSED_DEEP_MOE.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md)（constraint）
- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（implementation）
- [Mode1 C++ bridge 与 beta 默认值](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/deep_ep.cpp)（implementation）
- [CANN MegaMoe Python 接口、量化字段与激活默认值](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/mega_moe.py)（primary）
- [ops-transformer 9.2.0 版本声明](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/version.cmake)（constraint）
- [NpuMegaMoe 与 packed INT4 描述符](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/csrc/mega_moe.cpp)（implementation）
- [MegaMoe ACLNN 两段式入口](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_api/aclnn_mega_moe.cpp)（implementation）
- [MegaMoe OpDef 的平台 dtype/format 配置](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_def.cpp)（constraint）
- [A3 量化和激活 Host 校验](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch22/mega_moe_tiling_arch22.cpp)（implementation）
- [950 激活、格式和拓扑校验](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h)（implementation）
- [通信上下文与自动拓扑选择](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/csrc/comm_context.cpp)（implementation）
- [950 分层实现的 SDK/HCOMM 版本门槛](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_apt.cpp)（implementation）
- [mc2/mega_moe/README.md](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/README.md)（constraint）
- [torch_extension/cann_ops_transformer/common/aclnn_common.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h)（implementation）
- [mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp)（implementation）
- [mc2/mega_moe/op_kernel/arch22/mega_moe_arch22.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/mega_moe_arch22.h)（implementation）
- [mc2/mega_moe/op_kernel/arch22/mega_moe_kernel_a3.hpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/mega_moe_kernel_a3.hpp)（implementation）
- [mc2/mega_moe/op_kernel/arch22/unpermute/mc2_mega_moe_moe_token_unpermute.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/unpermute/mc2_mega_moe_moe_token_unpermute.h)（implementation）
- [mc2/mega_moe/op_kernel/arch22/utils/gated_activation.hpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/utils/gated_activation.hpp)（implementation）
- [mc2/mega_moe/op_kernel/arch22/utils/block_epilogue_pertoken_swiglu.hpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch22/utils/block_epilogue_pertoken_swiglu.hpp)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swiglu_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swiglu_activation.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swigluoai_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/swigluoai_activation.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/gelu_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/gelu_activation.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h)（header）
- [mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h)（implementation）
- [include/hccl_mc2.h](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/include/hccl_mc2.h)（primary）
- [src/common/hccl_mc2.cc](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/src/common/hccl_mc2.cc)（implementation）
- [version.cmake](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/version.cmake)（constraint）
- [src/legacy/ascend910/framework/op_base/src/op_base_mc2.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend910/framework/op_base/src/op_base_mc2.cc)（primary）
- [version.cmake](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/version.cmake)（constraint）
- [mc2/common/op_kernel/quantize_functions.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/quantize_functions.h)（header）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_mmad_mx_fp8fp4.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_mmad_mx_fp8fp4.h)（implementation）
- [mc2/mega_moe/op_kernel/arch35_92/blaze/prologue/block_prologue_mx_fp8fp4.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/prologue/block_prologue_mx_fp8fp4.h)（implementation）
