---
type: Guide
title: vLLM Ascend KV Pool异步任务、逐层地址与发布状态合同
description: 区分批量/旧逐层key/Mooncake block-key/Memcache GVA四条传输路径的地址构造、发布、租约所有者、失败与缓冲释放条件。
aliases:
- KVTransferThread
- LayerBatchBuilder
- LayerwiseSessionTracker
- AttentionComputeStartGate
- LayerwiseCacheLayout
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/attention_fence.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/layerwise_keys.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/session_tracker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_layerwise.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/kv_transfer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/kv_transfer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/layerwise_cache_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/metadata.py
  role: implementation
created_at: '2026-11-03T05:43:00Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KV Pool异步任务、逐层地址与发布状态合同

本卡保留所列版本的传输状态。7d9e把bulk保存引用交给专用tracker，并分开公共、bulk和layerwise scheduler；迁移前读[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的AscendStore节，勿跨模式套用pin、完成与reset规则。

## 固定来源和四条路径

本卡聚合固定 Main 的线程、逐层layout、key协议、session tracker和attention fence的全部可执行结构。未创建线程、导入SDK、注册缓冲、运行UT或NPU。部署见[KV Pool](../deployment/vllm_ascend_kv_pool_backends.md)，身份与可达mask见[metadata合同](vllm_ascend_kv_pool_metadata_reachability.md)。

| 路径 | 数据寻址与完成 | 不能混用的假设 |
| --- | --- | --- |
| 非逐层 bulk | token_database产key与地址，后台get/put；save job集合、event和saved offset分别维护 | 请求完成、job出队和put成功不是同一状态 |
| 旧逐层 layer key | 每层split_layers后直接后端put/get，再置层event | 此分支不检查put/get返回码，event本身不能证明成功 |
| Mooncake block_key range | 每完整块一个对象，逐层按object offset写范围，最后组层commit或失败revoke | copy失败按负返回码，commit成功按0；不要用统一“非零即失败”覆盖两阶段 |
| Memcache GVA | GVA+rank/layer/component offset批量copy，收齐成功copy后write_finish发布 | GVA存在、部分层已copy和对象可读是不同阶段 |

## Bulk任务寿命与错误传播

KVTransferThread 是daemon，set_device后置ready，再从queue取任务；stop设stopping并放sentinel。提交遇stopping或fatal会拒绝；raise_if_failed才显式向调用者抛异步错误。通用事件等待以0.1秒轮询停机/失败，但Attention gate一旦拿到设备event还会synchronize，不能把轮询超时当设备同步总期限。

SendingThread用每请求store_job_id集合识别重入/旧任务，最后job结束才标finished；保存offset只在真实live job成功时向前推进，失败可保留拼接的token片段供事件重试。wait_for_requests_saved每1ms轮询并检查fatal，无独立总deadline；返回说明没有pending job，不额外保证业务期待的持久化。异常finally会完成job/event计数并清队列，因此event完成不能替代成功结果。

save按组mask、已存offset、HBM/pool skip区间与PCP/TP分片选块，先等待current_event再put。consumer的PP展开要求每逻辑key对应所有physical key；逐项布尔结果可筛选成功BlockStored事件。兼容分支仅将显式False作为标量失败，None并未在此一律判错，不能由没有抛异常补造强成功合同。

bulk recv 按group收地址并旋转起点分散访问。Memcache将None、长度不等或任何非0统一标失败，禁后续save；单组记录invalid block，多组记录failed request。其他后端保留较弱的legacy处理：record_failed_blocks以zip配对返回码，短列表不会自动覆盖末尾缺项；hybrid失败可能仅记日志、不用单组invalid-block回退。Agent必须保留实际后端及失败传播路径，不把本节当所有hybrid读取均可安全重算。

load_get统计仅包住一次Backend.get，不含排队和全部恢复。lookup异常转全miss，短exists响应未必严格等长；miss可以来自连接错误。BlockStored事件只按对应返回成功路径发出，不据事件存在证明外部持久化和取消清理都完成。

## Shared layout与精确地址

LayerBatchBuilder优先使用每group的block IDs/GVA、entry offsets和stride，否则按兼容group0字段。共享GVA任务要求load/save各自的offset覆盖请求范围，跳过非正GVA，并按(block_id,GVA)对去重；同block_id不同GVA不能折成同一项。地址=layer base+block_id×实际stride，远端GVA还含rank层offset及component前缀字节。

block-key任务使用每块key和key_block_offset，save可按key去重，load允许同key读入多个目的块。每层object offset按前面component实际字节数累加，不用固定“每层K/V两项”。批次拆分先校验每key的buffer/size/offset对齐，负size报错、0跳过，字节包同时推进buffer和object offset；max_transfer_blocks约束行/地址批量，max_transfer_bytes约束包大小，不是整个请求总预算。

layout默认共享buffer数等于层数，独立层[0]，prefetch=min(buffer数,8)；int解析拒bool但仍用int转换，不能宣称严格拒绝所有非整数数值。负独立层索引按实际cache-bearing层列表归一，MTP物理层映射在base层后。复用按main spec签名分桶，非Attention spec仅在真正发生复用时拒绝。

apply_layerwise_kv_cache_plan只在有实际复用时重写descriptor；先检查原descriptor contiguous page、范围、唯一且覆盖所有spec，变量indexer可以用最大page容量共享，其他命名spec要求一致。shared indexer backing按最大data/scale区域分配并对齐scale，多个逻辑层视图可以别名同一存储；图地址和跨层门控必须与此物理owner匹配。实现收集extra_main_specs，但merge循环只显式处理main/indexer和excluded层，新模型有额外main条目时须专项核对，不能从descriptor覆盖预检推断输出重写一定保留每项。

## Mooncake key与session协议

backend protocol声明 block_key，不支持PCP/DCP>1与P/D TP mismatch；TP/PP可用仍要求每PP stage每组有层，draft-only空组拒绝。PP分区必须非空连续且覆盖全部层；namespace包含TP、分区、model/cache/speculation hash，hybrid layout另含组块长/拓扑。无namespace时非0 PP rank直接失败，不能用旧key读取新布局。

LayerwiseKeyBuilder为每PP stage和rank生成hit key，需全套匹配。prepare_group_sessions以load/store masks及pool skip边界生成每组请求view；put_start成功key才参与逐层写，已池化或拒绝key不冒充写入。异常撤销本次新增started key、结束当前load sessions再抛。

LayerwiseSessionTracker分别维护pending put owner、已commit的请求block entry与active load key owner。相同(group,block index)替换旧key；commit才将pending移为可load条目，revoke删除pending。retry只释放active load owner，terminal还清请求entry和pending；共享key须最后owner离开才get_end。它提供本进程ownership，不是外部SDK租约自动延续或跨进程锁。

## 发布、失败与覆盖门控

range save按group保留active key集合，copy负码revoke并剔除，最后组层commit；commit异常或非0结果revoke，只有0才通知tracker commit。revoke失败会记录，但finally仍移除本地started/owner，故不能据本地集合为空宣称远端revoke已成功。

GVA save合并同物理层各组，等待sync_save_event后copy；write_finish前检查每key已有成功copy，再严格检查publication结果。copy失败置save_disabled并按配置传播failed requests；finally仍置层event用于唤醒，等待者必须另查failure。range load负码使对应block失效并从后续层active集合剔除，异常标整批invalid、置abort/fatal；get_event/层event也会在finally置位，不是成功标志。

覆盖共享槽之前，load依次等待先前save层event、检查save失败、同步对应NPU event、清event，再等attention start与external slot release；不能仅等同名逻辑层。GVA空任务和disabled路径也调用external waiter。h2d_stagger_us按(TP rank+layer) mod TP size忙等，是host主动延迟候选，未提供收益测量。

AttentionComputeStartGate只保留首次record的event，wait先等host条件再设备synchronize；cancel清callbacks后record，目的是释放等待，不代表attention算完。attention_transfer_window的finally调用on_finish，而开始event记录在进入窗口时，不能把start fence当整个attention完成事件。

## Agent验收证据

关联request ID/job ID、group/family、logical/physical layer、key或GVA、backing地址/stride、load/save/partial offset、mask与current/sync事件；分别记录put_start、copy、commit/write_finish、get_end/revoke结果及失败唤醒。覆盖部分批失败、重复key多owner、取消/重试、hash滞后尾块、MTP独立层、异构entry和停机，输出正确后再比较HBM/host预算、传输字节、TTFT/TPOT。以上是源码提炼的验证合同，不是全部硬件与模型的实测通过。
