---
type: API
title: 分页 KVCache 位置更新（torch_npu.npu_scatter_pa_kv_cache）
description: torch_npu.npu_scatter_pa_kv_cache：分页 KVCache 位置更新。更新KVCache中指定位置的`key`和`value`。 说明三维及四维写入、唯一slot、缓存布局，以及发布和主线函数化图参数差异。
tags:
- task.lookup
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_pa_kv_cache.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterPaKvCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterPaKvCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_pa_kv_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_pa_kv_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:50Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_scatter_pa_kv_cache
---


# npu_scatter_pa_kv_cache：分页压缩、别名与图参数版本

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_scatter_pa_kv_cache(key, value, key_cache, value_cache, slot_mapping, *, compress_lens=None, compress_seq_offsets=None, seq_lens=None, cache_mode='PA_NZ') -> ()
```

原地更新 key_cache/value_cache，无返回值。普通写入的三维key/value首维是打包token数，四维压缩的完整限制与图参数版本差异另列；两者不共用索引形状。

## 参数与组合限制

- 所有输入不支持非连续；key/value/cache dtype 必须一致，slot_mapping 等索引 Tensor 均为一致的 INT32 或 INT64。
- 三维 key/value 的前两维相同，Cache 为四维。PA_NZ 路线按 (num_blocks,num_head*head_size/last_dim,block_size,last_dim) 准备相应存储；K/V head_size 可不同，分别计算 Cache 形状。
- slot_mapping 每项在 [0,num_blocks*block_size-1] 且不得重复，重复不保证正确性。不能用某个请求的局部位置直接覆盖其他请求的全局 slot。
- cache_mode 默认 PA_NZ，要求 NZ 内存排布；None/Norm 只支持 ND。逻辑 shape 相同不代表格式一致。
- 四维路径的 slot_mapping=(batch,num_head)，compress_lens/seq_lens 为必需；文档场景表与部分压缩 shape 文字存在歧义，应按运行包另核对。

## 验证与模型关联

用已知 slot 检查两份 Cache 的修改和未修改位置，验证页边界、索引唯一及物理格式；不要从没有返回值推断没有副作用。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py#L1286)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线产品、压缩路径与None

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 产品表确认A2/A3/950，仍列训练/推理、单算子与TorchAir图模式。Schema显式标记两个cache可写且无返回值；C++直接修改，functional版本则各clone一份并返回两份cache，不能把功能化路径当成无复制更新。

三维key/value的首维是packed token数量B*S，而非必须为请求batch B；四维则是(B,S,H,D)。四维时compress_lens、seq_lens必填，slot_mapping=(B,H)，压缩偏移若提供为(B*H,)，cache第三轴须1；K/V的前三维一致，末维可按具体缓存场景核对。文档将seq_lens的“值等于batch”与一维shape混写，不能据此把所有实际长度填成B。

省略cache_mode时Schema默认PA_NZ；显式None在当前原地C++路径改用Norm，省略与None代表不同布局。functional包装的None传nullptr，未将其明确转换为同一字符串，不能凭Meta两份shape相同就保证两条None路径布局完全等价。明确写Norm或PA_NZ并配套实际存储更便于核对。

产品页将所有key/value/cache类型要求一致，包含FP8/HiF8等8bit类型，但dtype总名单不代替产品具体内核约束。唯一slot、连续性、压缩容量和原地副作用应同时验收。

## 双语压缩边界与示例范围

主线中英文明确训练/推理、单算子及TorchAir图模式，950产品形态为PR及DT；发布A2/A3与主线分别限定。三维key/value首维按B*S打包，K/V末维可以不同。四维场景表却把value_cache末维也写成k_head_size，而value输入仍写v_head_size；不能把三维的任意不同末维规则直接扩到四维缓存，保留这处文本差异。

四维时compress_lens和seq_lens必需，slot为(B,H)，可选compress_seq_offsets为(B*H,)，所有索引Tensor同INT32或INT64。公开容量是sum(seq_lens[i]-compress_lens[i])≤pages*block_size，不带单Key压缩页的+1。seq_lens参数是每请求实际长度，一维长度为B；“值等于batch”的表述不能当作每个元素都填B。重复slot不保证正确性、输入与缓存四者dtype相同且连续的限制同时适用。

主线场景二示例缓存pages=2、block_size=2，总槽数4，但slot列出0、3、6、9、12、15，超过[0,3]范围；这不是可直接复用的合法索引样例。图例最后打印success也没有成为本仓的运行结果。生成实际输入时按容量与全局页映射构造。

## 发布与主线图参数的差别

两个固定functional C++都clone为连续缓存并把副本传底层；Meta为公共void入口不返回Tensor，functional才返回两份empty_like。主线原地入口把显式None改为字符串Norm，发布原地及两版functional的None都传nullptr；省略参数仍由schema默认PA_NZ。不能由相同Meta shape保证None与省略、或原地与函数化路线的布局相同。

两个GE文件注册的都是functional入口，先TensorMove两缓存。发布Converter的形参却用单数compress_seq_offset，没有cache_mode参数并硬编码PA_NZ，与schema复数compress_seq_offsets和可选cache_mode不匹配；主线改为复数且转发cache_mode。不能用主线压缩Norm图示例证明固定发布组合也完整支持同样关键字，仍需正确的函数化重写与参数绑定。GE转换存在没有取消公开产品和连续性约束。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 分页 KVCache 位置更新：torch_npu.npu_scatter_pa_kv_cache

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

更新KVCache中指定位置的`key`和`value`。

### 文档签名

```text
torch_npu.npu_scatter_pa_kv_cache(key, value, key_cache, value_cache, slot_mapping, *, compress_lens=None, compress_seq_offsets=None, seq_lens=None) -> ()
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_scatter_pa_kv_cache.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterPaKvCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_scatter_pa_kv_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterPaKvCacheNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_pa_kv_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_pa_kv_cache.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
