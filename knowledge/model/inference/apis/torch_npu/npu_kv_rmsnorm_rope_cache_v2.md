---
type: API
title: npu_kv_rmsnorm_rope_cache_v2：950 原地缓存与实际双返回
description: 结合文档、Schema 和实现区分原地 Cache 更新与 k_rope/c_kv 双返回，说明索引唯一及分页模式。
tags:
- task.lookup
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/custom_dtype/Init.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/custom_dtype/CustomDType.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-09T01:58:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_kv_rmsnorm_rope_cache_v2：950 原地缓存与实际双返回

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_kv_rmsnorm_rope_cache_v2(kv, gamma, cos, sin, index, k_cache, ckv_cache, *, k_rope_scale=None, c_kv_scale=None, k_rope_offset=None, c_kv_offset=None, v=None, epsilon=1e-5, cache_mode='Norm', is_output_kv=False, k_cache_dtype=None, ckv_cache_dtype=None) -> (Tensor, Tensor)
```

融合 KV 的 RMSNorm、RoPE 与缓存写入。文档返回段列出四项，但同提交 Schema 与 npu_kv_rmsnorm_rope_cache_v2 实现只返回 (k_rope,c_kv)；k_cache/ckv_cache 是原地更新的输入，不是 Python 返回元组的前两项。四返回的旧入口和 functional 变体另有语义，不能混用。is_output_kv 控制是否写出有效的非量化中间结果，不改变公共 v2 返回数量。

## 参数与组合限制

- kv 为四维 (B,1,T,rms_size+rope_size)、FP16/BF16；gamma 为一维 rms_size，cos/sin 为 (B,1,T,rope_size)，rope_size 必须为偶数。
- 同提交 Schema 另含文档签名遗漏的可选 v=None。实现只有在底层 aclnn V2 可用且 v 为四维、尾维 128 时进入对应新路径；名称中的 Python v2 与底层 aclnn V2 不是同一个版本标号。本卡的普通 MLA 路线保持 v=None。
- index 为 INT64，所有模式都要求写入索引不重复；重复索引行为未定义。Norm 为每 batch 偏移、index=(B,T)，缓存为 (B,1,cache_length,D)，且 cache_length≥T。
- PA/PA_BNSD/PA_NZ 的 index=(B*T,) 表示全局 token 偏移；PA_BLK_* 的 index=(B*ceil(T/block_size),) 表示每页起始偏移，只支持连续 Cache 更新。页数至少为 B*ceil(T/block_size)。
- 非量化 Cache 为 FP16/BF16；量化 Cache 可 INT8/HiFloat8/FP8，两个 scale 必须同时提供，两个 offset 同时 None 或同时提供，scale/offset 均 FP32 且匹配相应 D。NZ 物理尾块非量化为 16、量化为 32，不能把逻辑 shape 当作物理排布。
- is_output_kv 仅在分页相关模式生效；未请求的中间输出不应当作有效值。图模式需保留 Cache 的 mutation 与生命周期。

## 验证与模型关联

同时检查 Cache 实际写入、索引映射和双返回值；对原地公共入口、旧四返回入口、functional 变体分别确认，不按文档返回列表直接解包。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py#L1047)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## Python版本号、底层选择与Meta差异

两个固定提交都已有Python v2及v2_functional的schema/C++，即使发布没有相应公开产品页，也不能断言实现不存在；反过来不能由它们存在证明发布支持主线950PR及DT的全部类型。两个公开主线语言版本的返回说明列四项，但实际公共v2始终双返回，缓存是带可写别名的输入；functional的四返回顺序才是(k_rope,c_kv,k_cache_copy,ckv_cache_copy)。

所有三个包装均用同一条件：缓存的aclnnKvRmsNormRopeCacheV2可用状态，且v为四维、v末维128，才走底层V2并分配K末维192、C末维128；否则底层V1按cos末维和gamma长度分配，v不下传。源注释的V1/V2是ACLNN版本，不是Python入口版本；注释中的切片简式也不是公开的完整数值参考。

Meta在v非None且有维数时检查其dtype、四维和前三维与kv相同，但只要v非None就给K末维kv.D、C末维v.D，不模拟符号可用性或固定192/128的条件。C++只检查kv/gamma/cos的秩，所做校验比Meta更少；不能由Meta通过推定Eager一定选新路径、输出相同形状或v一定生效。C++即使is_output_kv=False仍分配完整中间shape，分配存在不保证其中数值有效，更不能把它改称零元素空Tensor。

## 类型标记不是缓存数据转换

k_cache_dtype/ckv_cache_dtype在schema是Optional整数；None采用实际缓存ScalarType，显式整数经固定PyTorch的GetAclDataType转换后进入TensorWrapper。该辅助函数将≥256的值减256当ACL类型，其余按ScalarType映射；这不是torch.dtype对象接口，也没有为任意大整数建立合法性检查。包装没有转换或重新分配缓存的数据存储，不能把覆盖类型标记当作完成FP8量化、dtype cast或NZ重排。

主线公开量化缓存支持INT8/HiFloat8/E5M2/E4M3FN，两个FP32 scale同时提供，offset同时None或同时提供；950仅按PR及DT产品页使用。通用dtype枚举还列FP4等类型，不代表本接口也支持。固定主线PyTorch与OpPlugin的软件配套仍独立核对，不把静态映射视为组合已验证。

## 函数化缓存副作用的版本修正

发布C++的v2_functional先把TensorWrapper绑定到原k_cache/ckv_cache，再clone缓存，实际执行仍传原包装，最后却返回未参与更新的两个clone；所以该固定发布实现既可能修改原缓存，又返回更新前副本，不能用functional名字保证纯函数或把返回副本当更新结果。主线改为先clone、再把包装绑定到clone，执行与返回使用同一副本，静态修正了这条路径。

两个固定GE functional转换器都先TensorMove缓存，调用GE KvRmsNormRopeCache后将输出重排为2、3、0、1；它们不复现发布C++的错误绑定。不过Converter签名都没有接收schema已有的k_cache_dtype/ckv_cache_dtype，不能据普通无覆盖示例保证显式覆盖参数完整穿过图路径。公开图支持与每个参数组合的可编译性分别判断；未运行编译或设备验证。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache_v2.md)（primary）
- [补充版本或约束](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）
- [补充版本或约束](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_rmsnorm_rope_cache_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvRmsNormRopeCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_kv_rmsnorm_rope_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/custom_dtype/Init.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/custom_dtype/CustomDType.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
