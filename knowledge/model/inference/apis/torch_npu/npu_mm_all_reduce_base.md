---
type: API
title: 矩阵乘与 AllReduce 通算融合（torch_npu.npu_mm_all_reduce_base）
description: torch_npu.npu_mm_all_reduce_base：矩阵乘与 AllReduce 通算融合。TP切分场景下，执行mm和all_reduce的融合，融合算子内部执行计算和通信流水并行。 区分发布A2与主线950的量化布局、通信引擎、ACLNN符号分流、图转换和测试缺口。
tags:
- task.lookup
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mm_all_reduce_base.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAllReduceBaseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulAllReduceBaseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_all_reduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_all_reduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base_perblock.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base_perblock.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base_bf16.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base_bf16.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base_error_dtype.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base_error_dtype.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_weight_quant_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_weight_quant_mm_all_reduce_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_weight_quant_mm_all_reduce_base_with_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_weight_quant_mm_all_reduce_base_with_add.py
  role: example
created_at: '2026-11-10T03:38:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
aliases:
- torch_npu.npu_mm_all_reduce_base
---


# npu_mm_all_reduce_base：版本化通算融合与量化矩阵

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_mm_all_reduce_base(x1, x2, hcom, *, reduce_op='sum', bias=None, antiquant_scale=None, antiquant_offset=None, x3=None, dequant_scale=None, pertoken_scale=None, comm_quant_scale_1=None, comm_quant_scale_2=None, comm_turn=0, antiquant_group_size=0) -> Tensor
```

本卡聚焦发布来源 A2 非量化、全量推理：对 x1@x2 加可选 bias/x3，再进行 AllReduce(sum)。x1 为 (M,K) 或 (B,S,K)，x2 为 (K,N)，输出保持前缀、末轴变为 N，dtype 与 x1 一致。来源明确增量场景不使能，不能直接作为 Decode 的通用替换。

## 参数与组合限制

- 产品表只确认 A2，world size 支持 1/2/4/8，且 HCCS all-mesh；不由同类接口的 A3 支持推导本接口的范围。驱动固件与 CANN 需满足来源给出的 8.0.RC2 或更高配套。
- x1/x2 非空，非量化同为 FP16/BF16；x1 不支持转置输入，x2 为二维 ND/NZ 且 K 匹配。bias 一维 N、x3 与输出同 shape/dtype，均在归约前相加，所有 rank 的 bias 复制会影响全局结果。
- reduce_op 仅 sum，comm_turn 仅 0。一个模型内 A2 的三类通算融合入口按来源要求使用相同通信域。
- 伪量化、全量化各有独立类型表；antiquant_scale/offset、dequant_scale、pertoken_scale 不能随意混合。pergroup 的 antiquant_group_size 为 [32,K-1] 内 32 倍数，非 pergroup 传 0。
- 通信量化 scale_1/scale_2 只用于全量化，shape/dtype 相同且各 rank 数值一致。关于 FP32 dequant_scale 的表格和编码说明需按实际路径核对，本卡不提供未经验证的混合量化配方。

## 验证与模型关联

按各 rank 的局部矩阵乘、bias/x3 和全局 sum 建参考，确认偏置只应加入几次；覆盖拓扑、长序列显存及通信开销，再判断流水收益。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py#L210)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 发布、主线与模型阶段

固定OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5和主线d84e9b1d6a558e5f27973cd4329f62968e46fdda；TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013、主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c。发布ascend_26_0_pt28有配套依据，主线组合未知。上文为发布文档子集；主线产品表增加Ascend950系列（包含旧称Atlas A5）PR和DT，未列A3，不由其他MC2入口推导本接口A3支持。

中文两版限定全量场景启用、增量场景不启用，即模型prefill/decode阶段边界；主线英文误写成全量化/增量量化，不据此将所有非量化prefill排除。用于TP中MatMul+AllReduce流水融合，性能收益须实测。

两版实际Schema已具有group_sizes、y_dtype、x1_dtype、x2_dtype、dequant_scale_dtype、pertoken_scale_dtype、comm_quant_mode，发布文档原型没有列这些参数，不能把它们说成主线才首次存在。只有主线实际Schema及转换器新增comm_mode=None；低位实现存在不等于发布已公开认证950全套组合。

## 矩阵、拓扑与空输入

x1为ND[M,K]或[B,S,K]、不支持转置；x2二维[K,N]，可以是转置后的view，但逻辑K必须匹配。输出为[M,N]或[B,S,N]。bias为[N]，x3与输出同shape/dtype，在各rank归约前加入；多个rank传相同偏置会在全局sum里重复累加，不等价于归约后仅加一次。

|条件|发布及主线A2|主线950PR/DT|
|--|--|--|
|非量化|FP16/BF16同型，bias/x3同型|同左|
|权重布局|ND或NZ|仅ND|
|rank数|1/2/4/8，仅HCCS all-mesh|1/2/4/8/16/32/64；CCU不支持1rank|
|空输入|x1/x2不支持空|非量化K0、M/BS/N0；权重伪量化仅K0；全量化不支持空|
|通信引擎|文档同时描述Host CPU+TS和comm_mode的AICPU|CCU单机UB域；AICPU可跨机UB域|

950文档写非量化K0输出bias+x3、M/BS/N0直接返回空输出；C++包装没有自行实现这些特殊值计算，不能仅凭文字忽略多rank归约的偏置次数。A2字段/主线不同引擎描述按部署版本核对，不视作可随意互换的实现。

非量化B*S/M/K/N≤2147483647；全量化M及B*S在1..2147483647、K在1..65535，X2末轴也在1..65535，仅转置权重逻辑N可更大；伪量化M/B*S同范围且K/N在1..65535。完整模型的AllGatherMatmul、MatmulReduceScatter、MatmulAllReduce按来源要求使用同一通信域。长序列增大M/B/S可能OOM或超时，不能由融合减少一次中间搬运推导容量无限增长。

## 反量化位置与类型矩阵

antiquant是权重乘前反量化，语义为(x2+offset)*scale；dequant和pertoken_scale是全量化MatMul后的反量化，comm_quant_scale_1/2是通信量化。三个位置不能相互替代。主线中文x2参数泛称与x1同型，和其自身权重伪量化表冲突，应按场景区分。

|场景|x1 / x2|scale及bias/x3|输出|
|--|--|--|--|
|A2权重伪量化|FP16或BF16 / INT8|antiquant_scale/offset同x1；bias/x3同x1；不用dequant|同x1|
|950权重伪量化|FP16或BF16 / HiF8或E4M3|antiquant_scale同x1，offset表列None，bias/x3同x1|同x1|
|A2 INT8全量化|INT8 / INT8|bias INT32；dequant INT64/UINT64、无pertoken；x3 FP16|FP16|
|A2 INT8全量化|INT8 / INT8|bias INT32；dequant BF16、无pertoken；x3 BF16|BF16|
|950 INT8全量化|INT8 / INT8|bias INT32；dequant FP32或BF16，pertoken FP32；x3对应FP16/BF16|FP16/BF16|
|950 FP8全量化|E4M3/E5M2同族组合，或HiF8/HiF8|bias FP32；dequant/pertoken FP32或MX E8M0；x3同输出|FP16/BF16/FP32由y_dtype指定|
|950 FP4全量化|E2M1打包 / E2M1打包|MX E8M0 scales；bias表列FP32，但perblock条款仅None|FP16/BF16/FP32由y_dtype指定|

表内任选参数仍按所选分支核对，None并不意味着可用错误shape/dtype替代。FP8表将E4M3/E5M2并列，但不把HiF8与标准FP8混配当公开支持；测试虽列混配，存在解释参数与断言缺口。非量化各quant scale均None；权重伪量化不用dequant或通信scale。A2主线表删去了发布表中两行pertoken组合，但两版实现均有pertoken分支，发布/主线文档不一致须保留，不能静默判定A2 pertok已移除。

antiquant_scale支持[1]、[N]、[1,N]或pergroup[ceil(K/G),N]；offset同scale形状和dtype，950表限制None。非pergroup时G=0；pergroup G为32倍数且32≤G≤min(K-1,INT_MAX)，K≤65535。不要把ceil(K/G)当每组固定整除，尾组仍按上取整。

dequant普通粒度支持[1]/[N]/[1,N]；pertoken FP32形状[M]或[B*S]。文档的“所有FP32 dequant先npu_trans_quant_param转INT64”与950 FP8/块量化矩阵直接用FP32、实现wrapper保留FP32有冲突。编码后的INT64不是数值cast；按具体INT8后端核对，不能把所有FP32/MX尺度统一转换，尤其不对E8M0做普通乘法或cast。

## 块量化、MX与打包解释

主线950的group_sizes=[groupSizeM,groupSizeN,groupSizeK]，每项0..65535；0可由维度/scale维度整除关系推断。C++辅助函数将三项编码为(M<<32)+(N<<16)+K传给ACLNN，此内部表示不替代公开三元组。C++空数组表示0，图转换对给定空list按长度错误拒绝，自动推导优先用None，不机械跨模式复制空list。

perblock组为[128,128,128]；二维x1尺度[ceil(M/128),ceil(K/128)]、权重尺度随逻辑[K,N]或转置[N,K]对应[ceil(K/128),ceil(N/128)]或其转置；bias仅None。三维表的pertoken尺度却写[B,ceil(M/128),ceil(K/128)]，没有定义此M与S关系；不可据此自造广播和补齐规则。

MX组为[1,1,32]、权重仅转置表示[N,K]；权重E8M0尺度[N,ceil(K/64),2]，x1二维尺度[M,ceil(K/64),2]。三维表写[S,ceil(K/64),2]而没有B，需按固定后端核对batch语义。参数说明普遍要求ceil(K/32)偶数，表格又仅对FP4强调；保留更严格共同条件，不因FP8条目省略就放宽。

HiF8、FP4和E8M0可由容器dtype加显式x1_dtype/x2_dtype/dequant_scale_dtype/pertoken_scale_dtype解释，C++使用TensorWrapper，不是数值类型转换。公开FP4是E2M1两数/字节；TorchAir将末轴长度乘2、Bitcast并Reshape，在权重上根据原逻辑K匹配暂时转置后展开再转回。不能把容器的K直接当真实元素K、重复解包或再次普通cast。C++也识别E1M2等更宽分支，但公开表与图uint8校验更窄，不补写成公开FP4扩展。

y_dtype公开5/6/15对应FP16/FP32/BF16；FP8/FP4作为x1时Eager要求显式y_dtype和dequant_scale。Eager INT8输出默认FP16、dequant BF16时BF16，普通INT8分支没有按y_dtype改分配；Meta和GE只要dequant存在就应用y_dtype。不能仅凭参数可传就认为所有INT8/Eager/图输出选择一致。

## 通信量化、comm_mode与符号版本

reduce_op仅sum，comm_turn仅0。静态通信scale_1/2需同时None或同时传、同rank数值一致、形状同[N]或[1,N]、dtype同输出，仅全量化。主线950另有comm_quant_mode=0/1，1表示动态低比特通信；A2该新参数不支持，不能将它与MoE的量化枚举混用或把FP8表中None通信scale替换成任意尺度。

主线comm_mode支持A2 None/ai_cpu，950 None/ai_cpu/ccu；None默认AICPU，但Eager实现把“参数省略”与“显式ai_cpu”分流，后者要求更新ACLNN符号：

|路径|comm_mode=None的Eager|显式comm_mode的Eager|
|--|--|--|
|非量化|有x3选MatmulAllReduceV2，否则基础符号|MatmulAllReduceV3|
|INT8全量化|两通信scale→QuantMatmulAllReduceV3；否则pertoken→V2；再否则基础|QuantMatmulAllReduceV5|
|FP8/FP4全量化|QuantMatmulAllReduceV4|QuantMatmulAllReduceV5|
|权重伪量化|WeightQuantMatmulAllReduce|WeightQuantMatmulAllReduceV2|

显式模式逐分支检查新符号，缺少时报升级CANN，不自动回退。默认旧INT8分支虽接受group_sizes/comm_quant_mode，实际选基础/V2/V3时未把二者传入；不能把新Schema参数可见当默认旧后端已消费。发布无comm_mode，其他分流已存在。

GE转换则将None直接正规化为ai_cpu并写属性，根据is_arch35检查ccu/ai_cpu集合；它没有本地复现Eager ACLNN符号检查。图生成函数只是建输入描述和attrs；pertoken_scale的IR字符串还未列E8M0，但转换器可Bitcast到E8M0，这个不一致应单独核对。Meta仅造输出，不能证明拓扑/引擎/量化组合已运行。

## 测试真实覆盖与模型门控

主线基础文件有20个方法：4非量化、4权重伪量化、4 INT8、8 FP8/HiF8，后8仅950；但全部公共多进程执行器仅join，没有读取结果队列与参考比较，也没有校验子进程exitcode。发布基础仅1个A2八rank FP16方法，仍有队列读和0.05容差比较。用例变多并不等于精度覆盖增强。

主线8个FP8/HiF8方法全部传x1_dtype=x2_dtype=HiF8，即使输入实际是E4M3/E5M2；wrapper据此按HiF8解释字节，与参考的普通浮点cast不等价。INT64尺度方法又将随机整数当参考数值scale，不能证明打包量化参数的位级含义。这些例子不应复制为FP8正确性模板。

两版独立A2 add、INT8 FP16/BF16、weight-quant及带add测试仍比较输出，后者0.005容差；误dtype文件仅模拟错误输入、没有实际通信初始化。perblock文件两版都有x2_sacle_list拼写与x2_scale_list定义错位、worker只解包5项却传多项、未定义scale/dtype变量、helper缺self/缺_process_chunk等问题，不构成可运行块量化标杆。没有测试证明CCU、MX/FP4、动态通信量化、空输入或端到端性能。

文档图样例两种dynamic标志都只调用get_npu_backend，没有独立切换ACLNN后端的设置；不能仅由注释“ACLNN入图”认定实现了该模式。主线称NZ示例，但format_cast行已注释；发布对应行实际转换。两者只打印结果、没有图/Eager或性能对比。

[Qwen模型布局门控](../../optimizations/rules/weight_nz_mc2_mm_all_reduce_exclusion.md)明确只属于该模型实现，不能将其“MC2权重保持ND”外推为A2算子不支持NZ；本API文档A2仍列ND/NZ。验收应以各rank真实分片、局部bias/x3次数和量化位置建立独立参考，再检查一致性、拓扑、耗时与长序列显存。本次无上游运行、NPU/分布式/图/性能实验，无新增verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 矩阵乘与 AllReduce 通算融合：torch_npu.npu_mm_all_reduce_base

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

TP切分场景下，执行mm和all_reduce的融合，融合算子内部执行计算和通信流水并行。

### 文档签名

```text
torch_npu.npu_mm_all_reduce_base(x1, x2, hcom, *, reduce_op='sum', bias=None, antiquant_scale=None, antiquant_offset=None, x3=None, dequant_scale=None, pertoken_scale=None, comm_quant_scale_1=None, comm_quant_scale_2=None, comm_turn=0, antiquant_group_size=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mm_all_reduce_base.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_all_reduce_base.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAllReduceBaseKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulAllReduceBaseKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_all_reduce.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_all_reduce.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base_add.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base_add.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_all_reduce_base_perblock.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_all_reduce_base_perblock.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base_bf16.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base_bf16.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_all_reduce_base_error_dtype.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_all_reduce_base_error_dtype.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_weight_quant_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_weight_quant_mm_all_reduce_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_weight_quant_mm_all_reduce_base_with_add.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_weight_quant_mm_all_reduce_base_with_add.py)（example）
