---
type: Guide
title: vLLM Ascend DSpark驻留KV传输：P/D块组、ACK、就绪与取消
description: 沿DraftKVCacheMetadata、build_draft_kv_read_batches和DSparkContextReceiver接入P到D的驻留草稿KV，核对loader所有权、component
  stride、prompt有效行、generation与ACK重试、target/draft和全部D TP汇合、receiver容量退役及取消后保留块与CopySFA槽；区分调用者排队超时、真实传输完成和scheduler清理。
tags:
- task.implementation
- task.debugging
- task.optimization
- topic.model_adaptation
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/dspark_kv.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/read_thread.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_transfer_status.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_transfer_cancellation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_resident_kv.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/dspark_context.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/protocol.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/send_thread.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_pd_context.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T12:13:26Z'
updated_at: '2026-11-02T12:24:42Z'
platforms: []
aliases:
- DraftKVCacheMetadata
- build_draft_kv_read_batches
- DSparkContextReceiver
- DSparkDraftKVStatus
- retire_ready_request
- send_dspark_draft_kv
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DSpark驻留KV传输：P/D块组、ACK、就绪与取消

## 消费任务与固定边界

为SFA PD接入DSpark草稿，或排查ACK已到但Decode仍等待、取消后块表被提前回收时，需要分别追踪P已生成的驻留草稿KV、D接收预留、target读取、全部D TP终态和scheduler资源释放。本卡固定Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；该快照的配对Native pin为`544f182d9f0c9bfe8bd7645525951d5e3692a542`，不以独立Native快照替代实际配对调用验证。

`dspark_kv.py`199行、`dspark_context.py`564行、`protocol.py`244行及四份专项UT全文；Reader仅120–177/350–495，Worker仅177–205/238–423/430–476/790–851/879–972，Scheduler仅310–566，Sender仅1–329，MRv2 Runner仅408–426/449–509。源码和测试定义均只作数据阅读，未导入、执行UT、启动线程、触发JIT或运行NPU。整项硬件、模型、数值和性能未知，保持draft/空平台。

[上下文与前缀交接](vllm_ascend_dspark_context_prefix_contract.md)维护capture boundary、target/draft配对身份及P端恢复前缀再投影的次序；本卡从已注册驻留页继续到D接收和退役。[query/KV长度](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)仍维护模型query、KV与slot约束。通用[PD释放](vllm_ascend_pd_transfer_lifecycle.md)、[稀疏Offload](vllm_ascend_sparse_layerwise_offload.md)及[共享槽ACK等待](../../runbooks/runtime/vllm_ascend_sparse_buffer_ack_wait.md)保留各自版本、平台和target/indexer传输边界；这里不开放任意CP、PP或异构TP组合。

## Loader所有权、驻留与组件描述

`get_resident_dspark_layer_names`只在sparse offload开启、最终PP rank且method为dspark时检查驻留草稿。名字来自已加载speculator的`draft_attn_layer_names`，不能凭名称包含draft或目标层号推导。缺失所有权报错；通过shared map或forward context发现草稿指向非草稿target KV也拒绝。命中的spec必须为Ascend MLA，`replace(store_on_host=False)`仅改变放置，保留dtype、非因果语义和布局字段。

MRv2初始化将驻留草稿名及connector登记的持久草稿名从target layerwise scratch复用规划中排除。驻留MLA草稿也不继续套用host LRU/LIM尾状态。P持久页、target短生命周期buffer和D独立驻留页要分别记录；存在放置guard不证明所有allocator、stream和真实硬件组合安全。

`build_draft_kv_metadata`按`kv_cache_config.dspark_draft_layer_names`查真实cache group和tensor。每个非空组件要求至少二维、首维能被num_blocks整除、内部kernel页连续，且`scale×shape[1]`覆盖logical block。`DraftKVCacheMetadata`保存group ID、block size、容量、base address、首维字节stride、有效页字节长度、kernel scale、shape和dtype；stride可以大于payload长度。保存裸指针不自动延长backing寿命，存储替换后需要重新登记。

## P/D独立块组与prompt有效字节

`build_draft_kv_read_batches`允许P/D group ID、base、stride和池容量不同，但同名层的logical block size、component shapes、dtype、有效长度与scale必须精确匹配。它不转换任意TP分片。调用方还要证明两端权重、辅助捕获schema、rank映射和真实tensor格式一致。

源表按真实layer name引用P自己的group；D按该层自己的group查scheduler分配的目的块。源块数量必须精确为`ceil(prompt_tokens/block_size)`，目的块至少覆盖这些prompt块；源及使用到的目的块不能重复，ID必须是排除bool的整数且在各自cache容量内。目的表的额外lookahead分配不会因此被复制。

每个kernel页分别以`base+(block_id×scale+kernel_index)×stride`寻址；长度只取该页仍属于prompt的有效token行。最后一个partial页不覆盖未用尾行或lookahead。生成器每批最多`MAX_DRAFT_KV_READ_DESCRIPTORS=1024`条描述符；这是提交批量上限，不是带宽、吞吐或端到端时延结论。

## D侧接纳、generation和重复消息

Scheduler按loader产生的resident MLA groups分配块，给每次allocation创建新的generation；descriptor包括外部request ID、prompt长度、aux boundary IDs和hidden width。D自己的块表通过connector metadata交给本地Worker，rendezvous向P通告endpoint、engine身份和generation，不把D物理块ID当作P源块。

远端waiting请求不计RUNNING，不能只靠RUNNING或CopySFA热槽约束receiver容量。Scheduler另按max_num_seqs约束context接纳，scratch allocator无槽也返回`None,False`推迟，不以本地重算绕过接收。Worker先绑定唯一receiver，再注册descriptor及每个真实草稿group的块表。

`DSparkContextReceiver`的注册、target完成、ready、retire和discard属于model-worker owner线程；网络入口通过锁预留/结束复制。尚未接纳或相同请求仍inflight返回BACKPRESSURE；已存在allocation而generation不同返回STALE。descriptor/schema不匹配和失败隔离状态会拒绝；不能以匹配request ID覆盖新generation的目的页。

完成副本保留在completed/retired记录时，同一generation与schema的重复包可ACCEPTED而不再复制；合法清理后已注册替代generation时，旧包STALE。retired历史上限为`max(16,4×max_requests)`，不是无限期重复识别或任意ID复用安全保证。

## P端源块、实际复制和ACK状态

Producer的`send_dspark_draft_kv`要求最终P PP、已注册草稿页、可用发送线程和当前请求的Decode endpoint；外部ID、generation与aux schema必须对应rendezvous。每个P草稿group提供的源块必须等于scheduler所有该请求块表的prompt前缀，不能临时拼目标cache块。

Reader要求已有MF_META建立的P session及最终P stage。草稿wire为含tag的8字段消息；每层元数据必须恰含9个字段，层集合及两端group集合必须匹配实际登记。decoder会进行str/int转换，这不等于对原始wire类型执行了完整严格schema验证。

预留成功后逐批执行`batch_transfer_sync_read`，每批返回成功才继续；全部复制完成后先`finish(success=True)`，再发ACCEPTED。中途失败记FAILED并隔离预留，已写字节没有事务回滚承诺。对未绑定receiver的请求返回BACKPRESSURE，不以一次提前到达制造ready。

| DSparkDraftKVStatus | 固定Sender消费 | Agent必须区分 |
|---|---|---|
| ACCEPTED | 当前request/generation成功ACK后返回 | 本地草稿复制确认，不是D全部rank可decode。 |
| BACKPRESSURE | 相同payload重发，暂停0.01秒 | 接纳/占用压力，不随意更换generation或源页。 |
| STALE | 抛错停止该task | 原allocation已被替代，不能重写新目的地。 |
| FAILED或未知status | 抛错 | 不能将失败解释成无损重算或成功清理。 |

Sender忽略不匹配request/generation、非预期格式及无关回复，并处理夹杂的READ_DONE/READ_FAILED；poll默认250ms。task默认180秒：调用者`completed.wait(timeout)`包含排队等待，处理循环的deadline在task实际处理时才开始。调用者超时不从队列移除或取消在途task，不能据此认定P源页或D目的页已经可回收。发送线程shutdown会给尚在队列的草稿task记录错误并通知等待者；完整异常退役仍需现场确认。

## target/draft汇合、TP与容量退役

本地ready必须同时满足target KV完成、draft初始化行数等于prompt长度、没有inflight且没有失败。Consumer Worker先消费Reader的target终态，再标记descriptor的target完成；之后收集全部D TP rank状态，成功取terminal交集、失败取并集。任一本地ACCEPTED、单rank ready或某个P contributor完成都不足以放行Decode。

全部D TP成功后调用`retire_ready_request`释放receiver活跃接纳容量，但保留live draft块表、request map及重复ACK记录。否则下一次start_load先于finished清理时，已完成请求仍占receiver，可能使有界池溢出。retire、engine报告接收完成、实际推理结束和释放scheduler资源是不同阶段。

## 取消、失败与scheduler资源清理

取消不自动中止远端target或draft读取。Worker保留internal/external request映射、target目的块、draft组块表和CopySFA槽，把finished ID记到延迟清理集合；只有原target+draft在全部D TP完成、移除pending receive后才清lookup。先将完成事件解析成internal ID，再清映射，避免同一步DONE变成不可映射的永久pending。

取消发生在dispatch前，也要保留metadata seed和metaserver rendezvous，使原接收自然完成。Scheduler的`request_finished_all_groups`对仍pending的DSpark请求返回延迟释放；`update_connector_output(finished_recving)`到达后，才清tracker、context、请求槽并取消对应future/timer。Worker完成本身不直接释放scheduler槽或Native block manager所有的块。

有receiver时，任一D TP报告传输失败会抛`refusing local recomputation`，失败请求保持隔离，不能伪造finished_recving来回收仍可能被写入的目的地。Native scheduler真正释放块的行为，本次只有未执行mock UT的组合断言，未全文读取/运行其生产实现。取消和live请求混在同一target批次时也须分别保留自己的pending/slot，不用全批一次清空代替逐请求生命周期。

## Agent取证与后续验收

记录版本、P/D角色与TP/PP rank、内部/外部ID和generation、aux schema、每层实际group、cache容量、component shape/dtype/stride/有效长度、源及目的prompt块表。把enqueue、task开始、每批read、ACK、target终态、all-TP交集、retire、finished_recving及最终清理排成同一时间线；HTTP已送达、日志已打印或等待超时均不能替代这些完成证据。

所读测试定义覆盖P group7到D group2、partial prompt、不接纳/inflight backpressure、丢失ACK无重复copy、错误generation、失败隔离、target/draft不同完成顺序、全部TP等待、dispatch前取消及live/cancel混合批次。resident UT另覆盖loader所有权、非MLA拒绝、独立草稿预算和target复用排除。这些CPU/mock定义均未执行，不能作为真实NPU、MemFabric、统计质量或性能已通过的证据。

适配时先验证同一模型/格式的有效字节与未选页隔离，再覆盖超过1024描述符、padding stride、容量退役后新接纳、取消时DMA受阻、失败及代际替换；重复包还要覆盖retired历史被淘汰之后的边界。最后在实际支持部署上比较HBM/RAM、TTFT/TPOT和吞吐，分别测排队、控制等待与设备复制。不要因同步read、ACK默认超时或1024批量常量而宣称确定加速；不要跳过join、删除generation检查或吞失败来取得表面完成。
