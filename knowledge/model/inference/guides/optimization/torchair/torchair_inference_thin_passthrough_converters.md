---
type: Guide
title: npu_inference薄透传GE转换器：ToMe、InterleaveRope与KvRmsNormRopeCache
description: 记录TorchAir自定义npu_inference命名空间四个单GE节点转发转换器的参数映射、默认值与两pin形态，区分其与Meta重打包类入口的边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_kv_rmsnorm_rope_cache.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_kv_rmsnorm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_tome_unmerge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_tome_unmerge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_tome_merge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_tome_merge.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_interleave_rope.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_interleave_rope.py
  role: implementation
created_at: '2026-11-13T04:23:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_inference薄透传GE转换器：ToMe、InterleaveRope与KvRmsNormRopeCache

## 固定版本与证据范围

本卡固定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的`python/torchair/_contrib/custom_torch_ops/`下四个转换器全文（每文件两pin完整读取）。整卡平台未知，保持draft与空平台；未导入上游、未构图、未运行设备用例。同目录的[Dequant-SwiGLU入口](torchair_inference_dequant_swiglu_meta_and_packing.md)与[A8W4量化矩阵入口](torchair_inference_fused_quant_matmul_contract.md)各自有Meta/重打包语义，本卡四个入口不属于那类，不互相推导。

## 家族机制：一行GE节点转发

四个入口全部由`@register_fx_node_ge_converter(torch.ops.npu_inference.<op>.default)`注册，函数体只有一条`return ge.<Op>(...)`：把Dynamo捕获到的`npu_inference`自定义算子调用原样转发为一个GE节点，可选参数按签名默认值补齐后以关键字传入。转换器内没有Meta重打包、shape/dtype检查、Cast或输出后处理；`meta_outputs`仅作签名占位不被消费。`declare_supported`的`Support(...)`样例是候选输入声明，不是已实测的覆盖矩阵。`npu_inference`是TorchAir自定义包命名空间，不能与`torch.ops.npu`公共入口按同名互换，公共侧能力矩阵不在本卡推导。

## 逐算子的参数与默认值映射

| 算子 | 位置参数 | 关键参数默认值 | GE节点 |
| --- | --- | --- | --- |
| npu_tome_merge | token_a, token_b, token_indice, arg_max | top_rate=0.5 | ge.TomeMerge(..., top_rate) |
| npu_tome_unmerge | atten_out, ori_indice_a, ori_indice_b, topk_indice, arg_max | top_r_rate=0.5 | ge.TomeUnmerge(..., top_r_rate) |
| npu_interleave_rope | x, cos, sin | 无 | ge.InterleaveRope(x, cos, sin) |
| npu_kv_rmsnorm_rope_cache | kv, gamma, cos, sin, index, k_cache, ckv_cache | k_rope_scale/c_kv_scale/k_rope_offset/c_kv_offset/v默认None；epsilon=1e-5；cache_mode='Norm'；is_output_kv=False | ge.KvRmsNormRopeCache(同名关键字透传) |

ToMe两入口构成token合并/还原对：merge按arg_max与top_rate合并token，unmerge按topk_indice/arg_max与top_r_rate还原；两者是否真的减少设备搬运由下游GE图与kernel决定，转发本身不证明。KvRmsNormRopeCache的`cache_mode='Norm'`默认与[RoPE量化缓存融合](torchair_ge_rope_cache_lowering.md)中QKV入口的`PA_NZ`默认不同名也不同值，不能跨入口继承；其ckv_cache/k_cache写回语义与并发边界同卡前文限定。

## 两pin形态差异

发布版四个文件相对主线只删减了typing/torch类型导入样板与部分注释（如主线43行的interleave_rope在发布为24行、75行的kv_rmsnorm_rope_cache在发布为40行），注册目标、参数表、默认值与GE调用逐字一致；tome_unmerge保留的Schema注释两pin相同。包初始化经pkgutil枚举同目录模块并通配导入，启用该包后四个注册都会执行。

## 验证与边界

本卡只证明静态注册与参数转发。GE节点`TomeMerge/TomeUnmerge/InterleaveRope/KvRmsNormRopeCache`的算子实现、输入约束与产品支持需按对应GE/CANN版本另行核对；`Support`样例形状（如merge的`F16(64,16384,1280)`、unmerge的`F16(32,32,32)`）是开发期候选，不构成融合或精度结论。Eager执行该命名空间算子不经本转换器，需另行确认torch_npu侧注册。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_kv_rmsnorm_rope_cache.py)（primary）：1–75完整读取。

- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_kv_rmsnorm_rope_cache.py)（implementation）：1–40完整读取；与主线diff仅导入样板删减。

- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_tome_unmerge.py)（implementation）：1–46完整读取。

- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_tome_unmerge.py)（implementation）：1–36完整读取。

- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_tome_merge.py)（implementation）：1–18完整读取。

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_tome_merge.py)（implementation）：1–16完整读取。

- [固定实现来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_interleave_rope.py)（implementation）：1–43完整读取。

- [固定实现来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_interleave_rope.py)（implementation）：1–24完整读取。
