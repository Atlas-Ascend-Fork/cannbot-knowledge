---
type: Guide
title: vLLM Ascend DSV4 KV计划：dtype、slot格式与静态scatter
description: 将DSV4的cache规格、压缩写入和稀疏Attention/metadata选择固定为同一计划，解释950默认BF16、FP8物理tile及PAD
  slot图约束。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_attn_kv_plan.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_attn_kv_plan.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/layer/attention/layer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: constraint
created_at: '2026-10-29T11:32:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:56:18Z'
---

# vLLM Ascend DSV4 KV计划：dtype、slot格式与静态scatter


## 范围与单一决策源

固定ceac1a2b的get_dsa_attn_kv_plan。源码单测显式遍历A2/A3/A5配置，但使用mock与CPU替身，不能提升为整项硬件支持表；本卡保持draft、空平台。内部A5对应950仅用于解释能力分支，不证明任意DSV4模型/图/PD组合已通过NPU测试。模型部署另见[DeepSeek V4指南](../models/vllm_ascend_deepseek_v4_deployment_contracts.md)。

必须显式传当前引擎vllm_config，不能从仅load_model期间存在的全局上下文猜dtype。indexer KV独立量化，不由attention主KV计划自动决定。

## 选择顺序和布局

优先TurboQuant且compress_ratio=4的专用混合plan；否则无DSV4_COMPRESSED_CACHE能力走传统shared-KV plan。具备能力的950再按BF16/FP8选择。非TurboQuant时，源码单测要求plan不因compress_ratio=1/4/128改变；不能用层压缩比替代dtype选择。

950中auto、bfloat16、bf16由is_a5_bf16_kv_enabled按BF16布局判断。resolve_dsv4_cache_dtype另有独立纯函数行为，但本次全仓Python引用检索只发现其定义和单测，未发现服务调用点；不能把其非950返回model dtype、或FP8请求返回auto的测试行为，当成服务已执行的归一化/自动回退。

BF16 plan用sparse_flash_mla与flat slots；950 FP8 plan使用kv_compress_epilog与另一套mixed-quant attention/metadata，不接受同一组runtime kwargs。传统与TurboQuant plan使用block/offset对；转换保留负slot为[-1,-1]，不能先clamp到0。

FP8压缩写入将缓存按同一8bit存储reinterpret为UINT8，epilog的PA_BBND物理token为608字节：RoPE64个BF16=128B、NoPE448个FP8=448B、7个BF16 scale=14B、padding18B。Attention入口layout参数与压缩epilog布局是各自接口字段，不能仅看字符串相同/不同就重排物理字节。

## 两类故障信号

ori_kv head dimension 512, should be 608提示可能把FP8 metadata/plan放到BF16 page，先核对用户请求→归一化cache dtype→实际page→plan的完整链路，不任意给BF16 page补96列掩盖配置分歧。

BF16 scatter保持静态[T,1]索引，PAD_SLOT_ID=-1由算子跳过；全pad capture仍提交同形scatter。Python bool(torch.any(valid))会引入host scalar，boolean indexing会引入数据相关Nonzero，clamp(-1,0)则覆盖活跃slot。源码测试通过CPU替身和调用spy约束这些行为，不是本次已执行的ACLGraph/NPU结果。

## 接入和验收

所有写入/metadata/attention调用从同一plan取接口和kwargs；write_dsa_cache的输入检查还要求缓存页形态、行连续、updates宽/dtype、slots整型/行数及同设备，本文不替代该Triton算子的完整实现分析。

覆盖auto/显式BF16/FP8、不同层压缩比、PAD与全PAD、组block size、stride和缓存更新；再分别加入图与connector。错误时恢复整套规格/plan/权重一致的路径，不只更换一个算子名。本次未运行单测、scatter或NPU模型。


## 与真实层规格和校验对齐

DSAAttention直接按compress_ratio选择C4/C128/SWA backend，绕过platform selector，因此层构造会自行调用supports_kv_cache_dtype。该方法在具备DSV4压缩缓存能力时只接受auto/bfloat16/fp8，其他分支接受auto/bfloat16/int8/turboquant_4bit_nc；不能直接将类上的平面dtype列表当作每个平台的支持表，也不能靠未连接的resolve helper绕过拒绝。

get_kv_cache_spec对compress_ratio<=1返回None，SWA由独立DeepseekV4SWACache分配；其他层按真实能力/BF16选择head_size或head_size+96，TurboQuant C4另取SLOT_BYTES。storage block来自当前引擎的DSV4表，交给scheduler的block_size为storage_block_size×compress_ratio，并传tokens_per_state；物理压缩页与scheduler原始token单位不能互换。以上闭合的是规格方法与plan之间的局部关系，完整worker/各backend调用链仍需继续分析。
