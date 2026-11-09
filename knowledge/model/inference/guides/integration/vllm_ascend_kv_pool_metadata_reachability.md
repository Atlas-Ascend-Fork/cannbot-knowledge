---
type: Guide
title: vLLM Ascend KV Pool元数据、混合缓存可达性与保存边界
description: 解释 AscendStoreCoordinator 与 ChunkedTokenDatabase 如何保留KV组/压缩族身份、计算可达命中、分段地址和请求保存快照，供新模型缓存适配使用。
aliases:
- AscendStoreCoordinator
- ChunkedTokenDatabase
- RequestTracker
- ExternalCachedBlockPool
tags:
- task.implementation
- topic.kv_cache
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/metadata.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/coordinator.py
  role: implementation
created_at: '2026-11-03T05:43:00Z'
updated_at: '2026-11-03T05:43:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KV Pool元数据、混合缓存可达性与保存边界

## 适用范围

以固定 Main 的 metadata.py/coordinator.py 可执行结构为依据，未调用 Native manager、SDK 或设备。部署能力和持久 namespace 见[KV Pool后端指南](../deployment/vllm_ascend_kv_pool_backends.md)，线程完成与逐层地址见[传输状态合同](vllm_ascend_kv_pool_transfer_state_contract.md)。

## 身份与不对称并行

PoolKey 带 model、DCP rank、head/TP rank、PP rank、group、cache_role、cache_family 和 chunk hash，不能只以 token hash 或字节长度作为对象身份。compress_ratio 缺失→default、<=1→c1、>1→cN；组内混合比例标 mixed，DSv4 用其专用层索引和比例提取，不以普通 layers.N 解释全部状态。

TPMismatchInfo 只有 peer TP 不同、非 MLA、非 hybrid、KV heads 足够且能被最大 TP 整除才 enabled；local/effective heads 与 subkey 数随之变化。DCP/PCP mismatch 对 producer/consumer 读取不同 peer 字段；解析正整数会回默认值，不能把推断结果当严格配置验证。允许保存的角色是 producer/both 或 consumer_is_to_put，不等于业务P/D拓扑相同。

只有 is_prefix_cacheable 的组参与池化，至少要有一组；hybrid 判定还要求 manager 未禁用、多个组且存在非 FullAttentionSpec。UniformType specs 在部分帮助函数中取首个子spec，新的异构组应核对组内假设。传输粒度取 scheduler LCM 与所选组 block size 的 LCM，不把 hash block size、group size、物理page混用。

## Chunk与地址投影

get_block_hashes 要求 group size 是 hash size 的整数倍，分组hash取每组最后一个链式hash；不足一组的尾部不形成完整hash。字符串64位hex可转换为原始bytes，其他字符串保留UTF-8编码，别把所有字符串都当SHA原始bytes。

ChunkedTokenDatabase 按 role/family/group 缓存 key prefix；更新 family 会清 prefix 缓存。state role 的 buffer getter 在此返回空，不能据此声称 recurrent state 已有同样的地址搬运。prepare_value 依据每项 base、block stride、segment index/count 与块内 token 范围求交，按分段实际字节长度换算偏移；prepare_value_layer 还用 layer entry offsets，禁止仅以 block_len 当 stride。

chunk iterator 结合 hash、token长度、尾部截短 block ID 列表的 offset、mask_num 上取整、null block、chunk mask/filter 与分片进行筛选。分片基于通过前面筛选后的 candidate 顺序，不是原始绝对块号。负/零 ID 的跳过要由对应 flag 指定。prefill PP adaptor 将每个逻辑key和地址按 partitions 展开、替换 pp_rank；parts 必须与真实层/entry数闭合，不能只复制相同字符串。

## 可达命中不是所有组的独立最大值

AscendStoreCoordinator 要求 scheduler size 可整除 hash size 与每个 cacheable group 的有效 size，将等效 spec 合并并优先 FullAttentionSpec。ExternalCachedBlockPool 是带null/present哨兵的可达性适配器，不分配真实KV；HBM前缀用特殊hash标记为已存在，但不制造远端读取证据。

find_reachable_hit_tokens 先按组查询可达候选，再调用 Native manager.find_longest_cache_hit 求可共同恢复的长度。多组路径反复收缩长度，处理Eagle末块和FullAttention裁剪；不能取各组最大hit拼成可用prefix。lookup/load/store mask含义不同，load 不额外drop Eagle；default/c1 才按这里的 reachable mask 族规则处理，不把压缩cN一律按FullAttention恢复。

reachable_block_mask 由 manager 可选提供；通过inspect.signature筛掉不接受的保留间隔、prompt和boundary实参，manager类选择优先registry、再兼容 spec_manager_map。不存在mask返回None，不等于该模型支持全部高级恢复。32项LRU缓存绑定长度/retention/prompt并返回必要copy；不能原位修改缓存的mask来改变下一请求。

## 请求保存与异步完成元数据

RequestTracker 按 group 维护分配块；Mamba投机更新会把跳过或失效的历史块置0，不能按列表长度当全部可读。ReqMeta 区分 save_start/save_end、target长度、pool/HBM hit、snapshot、full/partial keys和GVA，block_ids兼容属性只代表group0，不得在hybrid适配中替代完整二维结构。

from_request_tracker 先按传输粒度对齐可保存长度，再受可用完整hash数限制；刚到块边界但hash尚未产生，也可能必须保留partial snapshot。普通can_load可跳save，save_partial_block有单独例外；更新num_saved_tokens和last snapshot是生产metadata的进度，不是SDK持久化已经成功。

事件token片段从上次saved范围切取，越界返回空片段；AscendStoreKVConnectorWorkerMetadata 只按event_id累加worker完成数，未在此按worker身份去重。完成计数、请求输出和数据正确要沿线程/后端分别核验。适配测试应包含多组不同块长、压缩族、HBM+远端连续命中、Eagle尾块、无hash边界、Mamba null块、取消/重试与分段布局，不能只验证单组完整块。
