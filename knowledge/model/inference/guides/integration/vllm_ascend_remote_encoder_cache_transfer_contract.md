---
type: Guide
title: vLLM Ascend 远端 Encoder Cache：Mooncake 分片注册与 Memcache 缓冲寿命
description: 区分远端 EC 和本机 ECCPU，核对 Mooncake 2MiB 对齐、bounce 分波/注册引用及 Memcache DeepStack 宽度、分批接收、copy-out 与异步保存。
aliases:
- AscendECMooncakeConnector
- AscendECMooncakeWorker
- AscendMooncakeTransfer
- ECMemcacheConnector
- _plan_transfer_waves
- AscendProducerAllocator
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.data_movement
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/mooncake/connector.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/mooncake/memory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/mooncake/transfer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/mooncake/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_memcache_connector.py
  role: implementation
created_at: '2026-11-03T05:07:51Z'
updated_at: '2026-11-03T05:07:51Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 远端 Encoder Cache：Mooncake 分片注册与 Memcache 缓冲寿命

## 两条远端路径的角色和依赖

固定 Main ceac1a2 完整读取 Mooncake EC 的 connector/memory/transfer/worker 与 ec_memcache_connector.py 五文件。未导入外部库、注册设备、启动线程/网络或运行NPU。对照[本机ECCPU](vllm_ascend_encoder_cache_offload.md)：后者的单host mmap/ec_both/MRv2限制只适用于其自身，不自动扩到这里的远端连接器；远端实现也不证明任意硬件/父类版本组合已可用。

AscendECMooncakeConnector直接调用ECConnectorBase初始化，scheduler复用Native ECMooncakeScheduler，worker替换为Ascend实现，其他role拒绝。这样避免依赖未必存在的父类worker工厂hook，但Native调度/控制/取消/关闭合同仍须使用匹配版本。协议未配置时选ascend，显式其他协议拒绝；buffer_device兼容cuda字面值改npu，允许npu或数字索引形式，其他拒绝。cross_encoder_cache请求会告警并关闭，不可由配置存在宣称可用。

Memcache另用metadata-only scheduler client与实际worker backend；mm_hash是图像feature identifier，存在命中会跳过encoder，驱逐策略由Memcache管理。_model_id仅保存模型字符串，不见其参与这份文件中的raw mm_hash键生成，模型/视觉预处理/权重revision隔离不能仅靠该字段推定完成。

## Mooncake 对齐、staging与bounce降级

直接注册起点按2MiB对齐。slab实际分配capacity+2MiB-1，再narrow到对齐地址；producer正常只注册一个slab，布局为staging→对齐padding→bounce。默认bounce=2MiB×min(128,max_num_seqs)；显式值必须真int、不能bool，0关闭fallback，非零至少2MiB并向上对齐。只有producer保留bounce预算，consumer另有自己的pool。

完整slab分配/注册失败且bounce>0时，以同allocator重试bounce-only，staging容量及free list变0；仍失败才报包含各预算的错误。不能把逻辑pool_size当进程实际分配/注册总量，也不能在bounce=0时承诺自动降级。

优先把整批Tensor stage到已注册slab，任何一个分配失败归还该批已取regions并返回None，随后走direct/bounce。stage和prefix copy在每线程NPU stream完成并同步后才传网络；source readiness来自绑定时记录的model stream事件，上层manager需先等待。consumer释放region前记录当前NPU stream事件，内存可分配不等于旧consumer已读完。

## direct range与传输波必须保留源所有权

若source起点向下对齐仍位于其storage内，可直接注册覆盖source的range；否则仅复制对齐前prefix到bounce，后缀直接注册。不能为了对齐把注册范围扩到storage外。分片保留destination_offset，prefix与suffix才能在consumer重建原字节序；仅比较总nbytes不足以发现拼接错误。

按同storage归并重叠/相接注册区间，range持有owner Tensor。按累计prefix预算切wave；每个wave完整申请FIFO bounce lease，容量不足等待，单lease超容量报错，不是分配任意大小临时bounce。Condition与active表校验release，不把“排队”当已取得字节。

注册按address保存nbytes、owners和users；同地址不同长度拒绝。同一range多使用者递增引用，最后释放才unregister；部分acquire失败逆序回滚。unregister失败会保留记录/owner，不能从release函数结束推所有设备注册已撤销。worker的release在finally还归还bounce，必须结合网络write的future结算检查本次是否真的不再读这些字节。global TransferEngine共享与EC自己的range账本是两层所有权。

push先刷新过期且未ready/cancelled的reservation，核预留nbytes等source，再按目标session聚合write。stage或所有waves完成后才notify/complete；失败先settle futures、abandon并标fail，不能把control ACK当数据已可消费。I/O/control线程池上限分别4/8，线程数不证明任意并发量都更快；CANN device须在相应控制/I/O线程设置。

## Memcache：DeepStack宽度、容量批次与copy-out

worker对Qwen3-VL式视觉配置使用 out_hidden_size×(1+DeepStack索引数)，否则用inputs_embeds_size；dtype取model config。recv_buffer_tokens默认8192，必须真int且在[2048,max_num_batched_tokens]内，调度上限小于2048时不能直接套默认。只限制持久buffer，超大对象会另分临时buffer，并非硬HBM总上限。

先batch_get_key_info，条目数必须匹配；字节需能被hidden_dim×element_size整除，0/不对齐对象跳过。普通请求保持相对顺序按token容量分批；超过持久容量的请求第二遍共享一个按本批最大对象大小分配的临时buffer，注册一次、逐批接收，最后unregister。后端返回None/缺结果/非0会留下None，scheduler exists命中与真正load成功是两种信号，不能假定命中后永不驱逐。

每个成功对象从staging view异步copy到独立output。持久buffer的copy-out事件留到下次复用前synchronize，临时buffer则每批立即等copy-out完成，防覆写/注销在飞行数据。结果Tensor在同current stream上生成，不代表其他消费流自动获得依赖。

只有TP0且PCP0保存；embedding先contiguous并记录ready event，再单线程executor设置设备、等事件、put_from。Future未在save_caches同步取回；异常仅日志，非0返回不证明保存完成或远端hit。shutdown等保存executor、等接收buffer可复用，才unregister持久buffer。save rank、scheduler命中统计和真实读取字节分别观测。

## 面向适配/性能Agent的验收

覆盖raw/mm_hash一致性与模型namespace、重复同图、DeepStack宽度、batch容量边界、单超大对象、staging耗尽/bounce-only、不对齐storage、共享source range、取消/过期reservation、部分write失败、unregister失败与退出。分别比较encoder重算、网络/设备拷贝、临时HBM、注册次数和端到端TTFT；命中率、少一次encode或连接成功均不能单独证明输出一致和净收益。本卡所有结论为固定源码静态合同，不新增verified。
