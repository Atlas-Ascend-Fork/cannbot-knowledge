---
type: Guide
title: FXRT量化/MoE/融合特例算子：NZ分支、版本探测与输出适配
description: 记录FXRT中带独立前置约束的aclnn特例算子：W8A8量化matmul与NZ权重分支、MoE dispatch/combine的V2/V3/V4可用性探测、grouped_matmul与FIA的固定实参布局、linear的ND展平，以及inplace_copy/argsort/getitem_slice等的输入输出适配边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_quant_matmul.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_quant_matmul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_ascend_quant_v3.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_ascend_quant_v3.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_dynamic_quant_v2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_dynamic_quant_v2.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_add_rms_norm_quant_v2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_add_rms_norm_quant_v2.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/dequant_swiglu_quant.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/dequant_swiglu_quant.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/add_rms_norm.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/add_rms_norm.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/rms_norm.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/rms_norm.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_layer_norm.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_layer_norm.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/var_mean.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/var_mean.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_grouped_matmul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_grouped_matmul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_fused_infer_attention_score.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_fused_infer_attention_score.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_moe_distribute_dispatch_v2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_moe_distribute_dispatch_v2.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_moe_distribute_combine_v2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_moe_distribute_combine_v2.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_gating_top_k.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_gating_top_k.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_gating_top_k_softmax.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_gating_top_k_softmax.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_init_routing_v3.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_init_routing_v3.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_re_routing.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_re_routing.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_token_unpermute.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/moe_token_unpermute.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/matmul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/matmul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/mm.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/mm.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/batch_matmul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/batch_matmul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/linear.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/linear.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/masked_fill_scalar.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/masked_fill_scalar.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/masked_fill_tensor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/masked_fill_tensor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/apply_rotary_pos_emb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/apply_rotary_pos_emb.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/interleave_rope.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/interleave_rope.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/cross_entropy_loss.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/cross_entropy_loss.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/argsort.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/argsort.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/getitem_slice.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/getitem_slice.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/strided_slice_assign.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/strided_slice_assign.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/inplace_copy.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/inplace_copy.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_scatter_nd_update.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_scatter_nd_update.h
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT量化/MoE/融合特例算子：NZ分支、版本探测与输出适配

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf下FXRT中带独立前置约束或多元数据适配的aclnn算子。纯转发薄包装另见[执行器缓存与注册边界](torch_npu_fxrt_aclnn_executor_cache_and_op_registry.md)，view零拷贝族见[view零拷贝与元数据算子](torch_npu_fxrt_view_zero_copy_and_metadata_ops.md)，ATB路线见[ATB算子桥接](torch_npu_fxrt_atb_operator_bridge.md)。静态阅读，未运行；整卡draft、platforms为空。

## 量化matmul：W8A8与NZ权重是两个不同API

`quant_matmul`（aclnnQuantMatmulV4 / aclnnQuantMatmulWeightNz）先做硬校验：x1/x2必须同为Int8（W8A8），否则异常；FP32 scale且无pertokenScale时输出dtype只允许BFloat16或Int32。随后按x2的Format分流：权重为FORMAT_FRACTAL_NZ时走WeightNz执行器并改用另一套实参顺序（含yscale/x1Offset/yOffset成员与groupSize=0）；ND权重走普通执行器。**两条路径的实参布局不同，不能靠换权重格式免校验**。grouped_matmul同理：17个固定下标输入（x/weight/bias/scale/offset/antiquant/ pertoken/activation三件套/groupList/splitItem/groupType/groupListType/actType/tuningConfig），按首权重Format选择aclnnGroupedMatmulV5或WeightNz，TensorList与可选Tuple逐项转换。

## MoE dispatch/combine按运行时可用性选V2/V3/V4

`moe_distribute_dispatch_v2`构造时用`GET_ACLNN_OP_FUNC`探测opapi库中是否存在V4、V3符号，存在才创建对应AclnnExecutor；调用时若提供了V4专属参数（input[6]为Tensor）而V4不可用，或V3专属参数（input[5]为Tensor或21/22/23非零）而V3不可用，直接报错而不是降级到V2。combine侧同样持有V4/V3/V2三个执行器。**版本选择取决于链接到的CANN opapi库，同一FXRT代码在不同CANN上会走不同aclnn版本**；排障时先确认实际命中的API名。gating_top_k、gating_top_k_softmax、init_routing_v3、re_routing、token_unpermute等MoE配套算子是带参数重排的转发实现；前端参数钩子（bias/k重排、expand_scales元数据修补）见[前端降级](torch_npu_fxrt_frontend_lowering.md)一节，本卡只落C++侧。

## FIA与RoPE的固定实参合同

`fused_infer_attention_score`按40个固定下标取实参（query/key/value、pse_shift、atten_mask、actual_seq_lengths两件、deq/quant scale与offset、antiquant、block_table、padding、shared prefix、rope、num_heads、scale、pre/next tokens、input_layout、num_kv_heads、sparse_mode、inner_precise、block_size、antiquant_mode、softmax_lse_flag、antiquant_mode_kv），输出取attention_out与可选softmax_lse。可选位用`IsTensor()?optional:nullopt`适配。**新增dtype提示、layout或版本参数不会自动透传**，须对照此固定ABI。`apply_rotary_pos_emb`为5输入转发并覆写ref对（输出与输入cos/sin位置别名，见其GetOutputInputRefPairs）；`interleave_rope`为3输入Tensor转发加PROTOTYPE注册。这些ref对声明进入运行时的零拷贝生命周期分析（见运行时卡），声明错误会在CheckStorageMatch类校验处暴露。

## linear：ND展平与NZ存储形状计算

`linear`复合算子持有aclnnMatmul/aclnnAddmm/aclnnAdd及对应WeightNz共5个执行器：bias走Addmm、无bias走Matmul、某些标量场景退化为Add。ND输入先`SetFlatternNdLinearTensorStorageInfo`把视图改写成[M,N]二维（strides=[N,1]、offset=0）；NZ权重的存储形状按FRACTAL_NZ块规则计算，且**itemsize大于2时按2参与计算（FP32权重按FP16算块）**，这是为aclnn的NZ物理布局做的元数据改写，不改变数值语义。Ascend310系列的linear实际由ATB分支接管，见[ATB算子桥接](torch_npu_fxrt_atb_operator_bridge.md)。matmul/mm/batch_matmul在CalcWorkspace时读取`GetCubeMathType()`并作为实参传入——cube精度模式在算子层是显式参数，不是全局隐式状态。

## 归一化族与dequant_swiglu_quant

`rms_norm`/`add_rms_norm`把epsilon按ToDouble转发并适配(y,rstd)双输出Tuple；`layer_norm`支持仅y或(y,mean,rstd)两种输出形态，normalized_shape/weight/bias/epsilon按固定下标转发；`var_mean`带correction/keepdim适配。`dequant_swiglu_quant`把6个可选输入逐一转optional、quant_mode转bool、后续字符串参数直传，双输出Tuple取前两项。它们与前端钩子的参数规范化（correction默认1、keepdim默认false等）互补；数值边界（如log_softmax的half_to_float拒绝）在前端卡已记录，本卡不重复。

## 复制与切片赋值的适配边界

`inplace_copy`按src/dst设备组合分D2D/H2D/D2H/H2H四模式：H2D/D2H/H2H明确不支持广播、dtype转换与非连续src/dst，违反即异常；D2D连续时直接返回（由上层launch路径处理），非连续才经aclnnInplaceCopy取workspace。`masked_fill_scalar/tensor`是两步复合：先aclnnInplaceCopy把输入物化到输出，再aclnnInplaceMaskedFill写mask位——**out-of-place语义由copy+inplace两段合成**，不是单一原子kernel。`getitem_slice`在输出含0维时跳过Launch；src/dst rank不一致（前端getitem降维）时重建带size-1轴的中间dst以匹配aclnnSliceV2的等rank要求，元素数不符即异常。`strided_slice_assign`要求末位stride为1，否则把x与value浅克隆并追加一维0..1的轴来满足V2合同。`argsort`逐项校验stable/dim/descending类型与(values,indices)双输出Tuple。`scatter_nd_update`（非inplace版）在Launch前先把src整块MemcpyDeviceToDevice到输出，再对indices/updates下发aclnn更新；src字节数大于dst时异常——**输出物化+索引更新两段合成**，与masked_fill的两步模式同类。这些适配都是“异常优先”，没有静默回退。

## 边界与验证方式

本卡所有约束来自静态阅读，未在设备上触发：W8A8/NZ分支、V4/V3探测结果、40参FIA ABI、两步masked_fill都应按实际CANN组合复核（日志确认命中API名与分支）。量化路径数值正确性、MoE通信正确性、FIA精度不在本卡范围。采用前固定TorchNPU/CANN版本，分别用ND/NZ权重、有无V3/V4专属参数、带广播/非连续的copy、带降维的getitem逐项验证异常路径与输出一致性。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_quant_matmul.cpp)（primary）：定向范围1–128。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_grouped_matmul.cpp)（implementation）：定向范围1–120。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_moe_distribute_dispatch_v2.cpp)（implementation）：定向范围1–80。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_fused_infer_attention_score.cpp)（implementation）：定向范围1–80。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/linear.cpp)（implementation）：定向范围1–120。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/inplace_copy.cpp)（implementation）：全文件81行。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/getitem_slice.cpp)（implementation）：定向范围1–60。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/masked_fill_scalar.cpp)（implementation）：全文件32行。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/matmul.cpp)（implementation）：全文件43行。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/argsort.cpp)（implementation）：定向范围1–55。
