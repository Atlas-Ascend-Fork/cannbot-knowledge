---
type: API
title: npu_scatter_pa_cache：单Key分页写入与Schema差异
description: 说明950 Norm布局、唯一slot和key_cache副作用，保留返回值及压缩参数名称的文档差异。
tags:
- task.lookup
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_cache.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:59:10Z'
updated_at: '2026-11-09T22:50:55Z'
platforms:
- '950'
---

# npu_scatter_pa_cache：单Key分页写入与Schema差异

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页与同提交包装/Schema，未运行上游实现或设备实验。公开产品仅限定950PR及DT，发布已有生成schema另作实现证据，不把主线新dtype或产品声明回推发布基线。

## 产品与可确认的普通写入

产品页仅950、训练/推理、单算子，不支持非连续输入。普通路径key为(tokens,heads,D)，key_cache为(num_blocks,block_size,heads,D)，slot_mapping为INT32/64(tokens,)，每项在[0,num_blocks*block_size-1]且唯一。更新既有key_cache，不处理value，不等同于[npu_scatter_pa_kv_cache](npu_scatter_pa_kv_cache.md)。

key/cache同dtype，普通类型包括FP16/BF16/FP32、INT8/16/32及UINT8/16/32；HiF8/FP8/FP4只在三维key分支列出，FP4逻辑D须偶数。支持空Tensor的描述不能取消索引合法性和具体形状约束。

## 以Schema区分参数与副作用

产品页原型写compress_seq_offset单数且无返回值，同提交实际注册为：

```text
npu_scatter_pa_cache.value(key, slot_mapping, *,
    compress_lens=None, compress_seq_offsets=None,
    seq_lens=None, key_cache) -> key_cache alias
```

Schema的压缩偏移参数为**compress_seq_offsets复数**；key_cache是必填关键字参数，标记可写并返回同一alias。生成式包装固定cache_mode='Norm'，不是可自由指定PA_NZ的版本。应用应以key_cache副作用验收，不依赖文档“无返回值”来设计图Schema，也不将重载名称理解成用户必须显式访问.value。

## 压缩分支边界

四维key=(B,S,H,D)对应cache=(num_blocks,block_size,1,D)、slot_mapping=(B,H)，索引dtype须与压缩长度/偏移和实际序列长度一致。产品页分别描述区间均值压缩与保留尾段，且原型/参数段命名不一致；本卡仅保存这些组合的入口与容量边界，不提供未经运行核对的压缩配方。容量须满足文档相应分支的序列减压缩量求和约束，而不是只看最大slot。

## 验证

先用无压缩、唯一slot确认分页地址、写入值与未修改区域；压缩调用另核对复数关键字、每head索引、容量和输出副作用。仅静态注册不证明具体压缩路径正确性或设备支持。

## 三种压缩说明与准确容量

完整中英文仅确认950PR及DT、训练/推理的单算子模式，支持空Tensor且不支持非连续输入；不由训练场景文字推定自动求导或图模式。高阶类型HiFloat8/两种FP8/两种FP4只列在三维key分支，FP4的逻辑D须偶数。四维key=(B,S,H,D)对应cache第三维1、slot=(B,H)；压缩长度有offset时为(B,H)，无offset时为(B*H,)，offset为(B*H,)，seq_lens为(B,)，整数类型与slot一致。

未传压缩三项是直接写入；三项齐备时，公开式按压缩起点之前的prefix、压缩区间ReduceMean、之后直到seq_lens的suffix拼接；未传压缩起点时，公开式保留key[seq_lens-compress_lens:seq_lens]尾段。这些分支不能复用同一压缩长度解释，也不能因为没有value输入就照搬双KV写入的配方。

本页容量约束原文为sum(seq_lens[i]-compress_lens[i]+1)≤num_blocks*block_size，带+1；双KV接口写的是不带+1的另一约束。尾段公式和通用容量式也并不自然等同，保留为各自公开条件，不自行删+1或从公式推出任意组合合法。slot仍须在有效范围且不重复，容量足够并不取消逐slot检查。

两个固定schema其实都注册.value重载并返回key_cache可写alias，生成配置固定cache_mode="Norm"、压缩关键字为compress_seq_offsets复数；公开原型却写单数和void，两个语言的压缩示例又用复数。以schema确认调用关键字，按缓存副作用验收，不依赖公开void来丢弃别名语义。局部搜索未找到手写C++、手写Meta或GE转换入口，不把生成式包装误判为没有实现，也不据发布已有schema扩出未确认的发布硬件支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_cache.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
