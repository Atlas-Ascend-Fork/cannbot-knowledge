---
type: API
title: npu_mrope：位置分段、两类interleave与V2要求
description: 区分旋转配对与多模态cache拼接，明确预计算cache、分段名单和V2回退边界。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mrope.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeWithSinCosCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mrope.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mrope.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeWithSinCosCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T07:08:10Z'
updated_at: '2026-11-09T22:37:34Z'
platforms:
- a2
- a3
- '950'
---

# npu_mrope：位置分段、两类interleave与V2要求

## 固定版本与范围

依据OpPlugin固定发布与主线的完整产品页、schema、Meta和C++，区分发布文档拼写冲突与实际包装；950能力只按主线950DT。未执行上游、图编译或设备实验。

## 接口与数据

```text
npu_mrope(positions, query, key, cos_sin_cache, head_size, *,
    mrope_section=None, rotary_mode='half', cache_mode='default')
    -> (query_out, key_out)
```

产品页确认A2/A3与950DT推理。query/key为二维(tokens,heads*head_size)，可有不同头数；cos_sin_cache=(max_seq_len,rotary_dim)，末维拆成cos/sin两半，浮点dtype三者一致，支持FP16/BF16/FP32及非连续。输出与各自query/key同shape/dtype，包装另分配empty_like，不原地修改输入。

positions为INT32/64：普通RoPE用(tokens,)，MRoPE用(3,tokens)或(4,tokens)，需匹配分段数，位置不能超出预计算cache。rotary_dim≤head_size；FP16/BF16两者均32对齐，FP32均16对齐。

## 两种interleave独立配置

rotary_mode='half'是NeoX前后半配对，'interleave'是GPT-J相邻维配对；两固定C++一致使用此拼写，发布文档的'interleaved'与实现冲突。cache_mode='default'是多模态cos/sin分段拼接，'interleave'是其交错拼接方式；这两个参数不是同一个开关，不应一起机械替换。

mrope_section=None或[0,0,0]为普通RoPE，只支持cache_mode=default；MRoPE名单为[16,24,24]、[24,20,20]、[8,12,12]或[16,16,16,16]，各项之和须为rotary_dim/2且positions行数一致。四段[16,16,16,16]只支持default，不能据positions二维就推断任意分段/交错模式受支持。

## V2与验证

包装明确要求cache_mode=interleave时存在aclnnRopeWithSinCosCacheV2，否则拒绝；default允许回到V1，不把所有配置都宣传为兼容旧运行库。Meta只返回同shape占位，不检查完整分段或V2能力。

先核对位置索引、旋转配对、分段长度、cache dtype和尾部未旋转部分，再与同数学约定比较。已有[Triton与原生选型观测](../../optimizations/rules/mrope_triton_ascend_vs_npu_mrope_decode.md)来自独立版本/模型条件，不能据本接口新支持推定那组性能数字仍适用；本卡不补造运行结果。

- [固定D=64的另一交错RoPE接口](npu_interleave_rope.md)

## 发布文档拼写冲突与完整公式范围

补充固定发布来源后，发布公开页的rotary_mode写为'interleaved'，主线中英文改为'interleave'。但两固定C++从发布到主线都只接受'half'或'interleave'，显式拒绝其他字符串；因此发布文档的'interleaved'是与同提交实现冲突的文字，不应作为可运行拼写，也不能推定它是兼容别名。cache_mode='interleave'始终是独立的cache拼接选择，不与rotary_mode机械同步。

两版schema的rotary_mode/cache_mode是Optional字符串，显式None由包装分别转为half/default；mrope_section=None转为[0,0,0]。这项实现行为不表示None会自动启用多模态。两版包装均在分配输出前要求cache交错模式有V2符号，default才允许降为V1；能力结果采用静态缓存。发布同样有此检查，不把它写成仅主线新增或某个产品已运行的证明。

预计算cache的后半是sin、前半是cos。default分段从各positions行对应cache选取各自区间再拼接；三段交错公式用mrope_section[1]限制1 mod 3和2 mod 3位置的替换，只按公开三段名单解释，不推广任意段数或不等长配置。普通RoPE只取一维positions且cache_mode=default，四段只支持default；MRoPE的positions行数、分段数及sum(section)=rotary_dim/2同时满足。

旋转只作用query/key的rotary_dim前缀，尾部保持原值；half对前后半配对，interleave对相邻奇偶维配对。公开GPT-J公式写了stack后直接cat、没有展示恢复尾维的flatten步骤，不能将该伪公式原样当作完整可执行参考程序。两固定C++只调用底层算子，不包含足以单独证明数值等价的旋转内核。

两版Meta仅返回与Q/K各自同shape的empty_like，不检查位置范围、分段名单、对齐或V2能力。两个固定GE转换器树中未找到注册npu_mrope或RopeWithSinCosCache的入口，只记录此局部静态搜索，不扩为所有编译后端都不支持的结论。950公开仅DT，A2/A3推理、FP16/BF16时head_size及rotary_dim均32对齐、FP32时均16对齐的限制保留。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mrope.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeWithSinCosCacheKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mrope.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mrope.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeWithSinCosCacheKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
