---
type: Guide
title: vLLM Ascend 前缀 KV Offload：CPU 与文件系统层级
description: 按中文配置核对CPUOffloadingSpec/TieringOffloadingSpec、全worker预算和chunk单位，分开验收pinned/shared-mmap、KV事件、文件系统回退与真实命中收益。 补充 Native split KV/Mamba 页视图、chunk字节与DMA事件寿命，以及Simple路径的布局/队列边界。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/kv_cache_cpu_offload.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/kv_cache_cpu_offload.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/native/npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/native/cpu_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/native/offloading_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/simple/copy_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/simple/npu_mem_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/simple/simple_cpu_offload_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/simple/worker.py
  role: implementation
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-11-03T05:04:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- NPUOffloadingSpec
- NPUTieringOffloadingSpec
- AscendOffloadingConnectorWorker
- SimpleCPUOffloadNPUWorker
- NPUDmaCopyBackend
- SingleDirectionNPUOffloadingHandler
---

# vLLM Ascend 前缀 KV Offload：CPU 与文件系统层级

## 范围与待验证平台

固定指南说明 V1 engine 的 NPU offloading spec，但没有具体硬件支持表，本卡为 draft。OffloadingConnector/kv_both 保存非活动前缀 KV，在 NPU miss、CPU hit 时加载以避免重算；不等于保存正在被 Decode scheduler 抢占的请求，后者见[PreemptOffload](vllm_ascend_preempt_kv_preservation.md)。

## 配置和预算契约

spec_name 仍用上游 CPUOffloadingSpec 或 TieringOffloadingSpec，由 Ascend 注册映射。cpu_bytes_to_use 是所有 workers 的 CPU tier 总预算，不能当每 rank 配置。blocks_per_chunk>0；同 block-size groups 可改用 token 单位 block_size，两参数互斥。块数与 token 数不能互换。

CPU-only 在可用时使用 pinned tensor，Tiering 用 shared mmap 供 manager 和次级 tier 共享字节。不要因[EC connector](vllm_ascend_encoder_cache_offload.md)有特定 CANN pinned-mmap 要求，就推导该 spec 自动具有相同实现；目标主机/CANN 下分别测带宽。

## 多层选择与验收

Tiering 可添加 fs secondary tier、root_dir 与读写线程数。O_DIRECT 不可用会回退 buffered I/O；更大 chunk 降元数据开销但使 hit 粒度变粗，增加线程只在存储可并发时有益。来源明确 filesystem tier eviction 尚在开发，不能把 CPU LRU 当成 SSD 也已自动容量闭环。

先测无 offload、CPU hit/miss，再构造超过 CPU 工作集访问 secondary tier，记录重算量、H2D/D2H、CPU预算、磁盘增长、TTFT/吞吐。lower memory utilization 会增加 offload 压力，不是免费扩容。带宽慢于重算、host OOM、磁盘无有效回收或输出不一致时停用 connector。本次未运行 CPU/NPU/磁盘实验。


## 中文配置与CPU/文件系统验收口径

kv_cache_cpu_offload.po的21条有效译文均匹配当前英文，包含CPUOffloadingSpec/TieringOffloadingSpec、预算和共享mmap说明；不表示代码围栏、当前网页完整性、注册实际生效或目标带宽已验证。“固定张量”应读作pinned/page-locked tensor条件，不是常量tensor；不能把shared mmap按CUDA任意host注册的带宽性质来估算。

最小配置同时核对OffloadingConnector、kv_both、spec_name、cpu_bytes_to_use与chunk单位；指南8 GiB、blocks_per_chunk=8、gpu_memory_utilization=0.5和Qwen0.6B只是示例，不是每worker默认预算或所有模型的推荐档。多KV group的block大小不同，不可仅把blocks_per_chunk换成token block_size绕过互斥/共同粒度条件。

可选KVEventsConfig中的zmq、tcp://*:5555和kv_events仅是发布示例。事件被发布、CPU分配成功、D2H/H2D提交、异步完成、真实prefix命中及输出正确是不同信号；不要由事件存在宣布offload吞吐提高。按冷miss→CPU hit→超过CPU工作集的secondary hit逐层比较，并记录实际I/O回退、线程、host/磁盘使用及重算量。

fs secondary复用原生实现的说明不是“所有SSD/3FS都快”或“磁盘已有LRU”的保证。O_DIRECT探测回退buffered I/O、chunk变粗、线程并发与未完成的filesystem eviction各自影响容量/延迟；工作集不超过CPU时不能强行归因secondary收益。本卡整项硬件仍未知，保持draft/空平台，未导入原生offloading、操作磁盘或运行NPU。


## Ascend Native布局适配：逻辑页不是底层storage大小

本节完整读取固定 Main 的 native npu.py、cpu_npu.py、offloading_connector.py 与 simple 路径四个实现文件；Native 父类与外部 DMA 仅是依赖，不以继承关系当完整覆盖。AscendOffloadingConnector 保留上游 scheduler/config，将实际worker替换为 AscendOffloadingConnectorWorker；仅检测 split Attention 或 list Mamba 时进入自定义 canonicalization，否则直接委托父实现。

canonical byte view 是 [manager_blocks,page_bytes] int8，按 tensor.storage_offset、物理stride与真实payload计算。每物理块内部必须连续，stride不能小于payload；一个manager块合并多个physical块时，physical stride还必须恰等payload。分离K/V/scale不能只取首个Tensor。若某个完整页view确实包含所有component的首块且storage一致，可用单view；否则分别建立refs，并核component字节和能整除逻辑页。

去重键是(data_ptr,stride0,页宽)，不是只比shape。完整 local page mapping只给确实一view覆盖全页的情况；真正分离K/V refs不套同一全页offset。Mamba须为非空list，组件总字节严格等去掉padding后的spec页大小。packed层的真实block_stride与普通page_size分开；num_blocks、physical factor、unpadded bytes 和映射共同决定DMA，不能用storage.nbytes除块数估算。

## Native CPU与Tiering的worker、chunk和生命周期

NPUOffloadingSpec 用可用的 pinned allocator 分配CPU镜像，不对任意 mmap 做 CUDA式host注册。NPUTieringOffloadingSpec 则明确声明使用 SharedOffloadRegion；replicated_layout 时rank=0，否则按当前物理device index模world_size选mmap slot，engine_id区分DP副本。replicated_layout仅承接Native已认证的复制布局条件，不能自行因“MLA”名称就跨任意拓扑复用单份数据。

worker检查所有canonical NPU Tensor为2D int8且shape[1]等page_size，CPU每chunk页宽=设备页宽×blocks_per_chunk。store/load各自持有独立list容器，避免清一侧误释放另一侧引用。构造失败先shutdown已建handler再cleanup mmap；正常shutdown也先等DMA并丢view，最后关闭mmap，避免exported-buffer阻止清理。

每方向根据 group_sizes、block_indices 与CanonicalKVCacheRef展开descriptor。chunk内skip为block_idx模blocks_per_chunk，所需源/目标chunk数分别ceil；所有block IDs必须恰好消费完，descriptor数和refs×group_size一致。data_ref.page_size决定copy字节，不能把逻辑token数直接当字节。

D2H stream先wait当前model stream，防读未写完KV；同方向新任务再wait前一个end event，形成有序队列。descriptor Tensor、stream、起止event被Transfer持有直到完成，避免异步DMA读到重用的Host指针数组。get_finished仅从队首query，完成后才回收buffer/stream/event；wait(job_ids)只同步event，不自动消费结果或回收。重复job_id和源/目的block合法性仍由调用方维持。测得时间转秒，success=True表示该静态成功路径，不代表端到端请求或数值已验。

## SimpleCPUOffload与Native spec的区别

AscendSimpleCPUOffloadConnector 复用Native简单scheduler；只有WORKER角色且上游确实创建了handler才替换，prefix caching关闭时保持no-op。SimpleCPUOffloadNPUWorker 的事件、水位和请求集合主要继承Native；不能把本节局部实现当完整scheduler协议。

Simple注册遍历每层所有K/V或Mamba组件，按storage基址去重；按shape/stride建立view以避开runner额外2MiB对齐padding，不能按storage.nbytes当有效数据。blocks位于首维时建单段；否则仅支持一个外层partition维、第二维可容纳num_blocks的多段布局。该推断不验证任意新backend布局，且相同storage上的不同非包含view需单独检查是否被去重遗漏。

CPU块数=max(1,cpu_capacity_bytes//总bytes_per_block)：预算不足一块仍会分一块，不是严格零超额保证。缺pinned仅告警。load/store用普通NPU stream，未设置CUDA最低优先级，独立stream也不自动证明与compute有净收益。

NPUDmaCopyBackend 缓存load/store指针与stride，要求src/dst键顺序完全相同、每块字节一致。copy将每component×block的地址展平为descriptor；没有在此校验负/越界block ID。后台单线程FIFO发起DMA，store等待主线程记录的compute-done event，完成event追加到父类轮询列表；线程本身没有单任务异常捕获，故不能把提交队列当可靠重试服务。shutdown放sentinel并join最多5秒，没有证明所有设备copy同步完成，应沿父类flush/事件闭环验证。

缓存指针创建后若换KV存储必须重新注册；队列保存的block列表与Host descriptor寿命、重复绑定metadata及store水位均按实际父类核对。回归覆盖split K/V/scale、Mamba、共享/packed view、偏移和padding、chunk余数、零拷贝任务、D2H写后依赖、H2D消费前等待、shutdown与重复注册；本次没有执行DMA、NPU、磁盘或带宽测试。
