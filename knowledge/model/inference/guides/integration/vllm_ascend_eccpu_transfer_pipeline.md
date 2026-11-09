---
type: Guide
title: vLLM Ascend ECCPU 搬运接线：描述符、流、完成回报与块池
description: 沿 ECCPUWorker、DescriptorBuffers 和 ECCPUScheduler 接入Ascend多模态缓存，区分保存/加载、stream等待、transfer_id回报、FIFO可回收块及encoder输出宽度。
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/worker/__init__.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/common.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/ec_shared_region.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/worker/descriptor_buffers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/scheduler/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/scheduler/embedding_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/encoder_output_width.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/base.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/ec_transfer.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/ec_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/engine/core.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/encoder_cache_cpu_offload.md
  role: supporting
created_at: '2026-10-29T20:09:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T20:09:01Z'
---

# vLLM Ascend ECCPU 搬运接线：描述符、流、完成回报与块池


## 任务与版本边界

新多模态框架需要复用ECCPU缓存，或出现已有CPU命中却重复encode、块一直pin、回报丢失、DMA缓冲过早复用。对照原生vLLM v0.32.0 `5df63a7203cdb9328d824a27b682e77c7b9928be` 与Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的适配入口；两个固定提交不自动证明所有二进制组合兼容。

Ascend文档支持范围为MRv2、单host的/dev/shm、ec_both，并要求CANN pinned mmap/batch copy能力。原生代码含producer/consumer、NIXL远端分支，字段可解析不等于这些分支已获Ascend支持。本卡只蒸馏Ascend所需的本地Host接线，远端session/NIXL内部继续留界。整项硬件集合未知，保持draft/空平台，未运行模型或设备。

## 入口与元数据不能只保留Tensor拷贝

ECCPUConnector按进程角色分scheduler/worker，AscendECCPUConnector只替换_make_worker，其余委托继承原生。ECCPUConnectorMetadata.saves为mm_hash到block_ids；loads为mm_hash到(transfer_id,block_ids,shape)。shape是二维encoder输出，不是词表token计数或KV block shape。

标准V2 ActiveECConnector在metadata非None时bind，先start_save/start_load，再对encoder_cache新增hash调用save_caches，finally通过get_finished触发flush_saves、收worker metadata并clear。get_finished返回的两组finished request IDs可以都是None，真正的本地DMA完成信号在ECCPUWorkerMetadata中；不能只接前者。

start_load在该try/finally之前，抛错不具备“任何路径都会clear”的保证。无forward波也有no_forward通道继续poll/回报；get_ec_connector还受has_ec_transfer、encoder_cache存在和非encoder-decoder等门禁。新框架不能只复制save函数而遗漏metadata绑定、异常和无计算步的控制路径。

## 共享区、容量与真实encoder宽度

create_ec_shared_region使用instance_id与data_parallel_index组成文件身份；这不同于ECTransferConfig.engine_id。block_size_bytes取LM输入embedding宽度乘模型dtype字节数，num_blocks=int(ec_cpu_bytes)//block_size_bytes，剩余不足一块的字节不进入容量。文档要求正整数，当前helper先truthiness再int转换，不能据配置可转换就认为类型/大小已经完整验证；至少检查实际num_blocks、tmpfs与模型shape。

模型的encoder输出可能因DeepStack等宽于LM embedding。measure_encoder_output_widths在EngineCore创建executor后、KV cache初始化前执行，每modality构造dummy输入，让有encoder的first-PP workers报告输出最后一维；无有效报告或rank间不同会失败，get_encoder_output_width缺modality也抛ValueError。它是实际启动工作和适配前提，不是无成本静态配置。该宽度用于按二维shape预算字节，不可直接用LM hidden size代替所有encoder列宽。

ECSharedRegion以O_EXCL创建或打开同名文件，followers最多等约30秒达到至少期望大小，再MAP_SHARED。创建者预触页，MADV_POPULATE_WRITE遇EINVAL退逐页read-modify-write，保持既有字节；这只是预触页fallback，不能解释为Ascend允许pageable DMA。文件足够大也未验证model/dtype/版本兼容，旧同名文件不构成有效cache证明。

## 保存：按有效字节合并连续块，独立保存流等待计算流

只有TP0且PCP0保存重复encoder输出；其他参与worker仍加载。save_caches先核对tensor有效字节不超已分配块，再把源地址与共享区目标地址写入DescriptorBuffers。_coalesce_runs按区域中连续ID合成run，不对任意输入排序；EmbeddingCache分配时给出升序ID，调用方须维持相应布局。

保存只复制numel*element_size，不复制尾块padding；最后run按剩余有效字节裁短。src.view(-1).view(uint8)与裸地址合同要求真实tensor布局可被如此解释，任意stride/空block/坏shape没有统一兜底。原生地址计算用uint64，Ascend描述符缓冲使用CPU int64存储位模式；不要把指针数组转为普通数值dtype来处理地址。

在本原生版本中，打开save batch时从stream pool取得保存流，src.record_stream(save_stream)保护源分配；flush_saves令保存流wait当前计算流，再在保存流上下文调用Ascend_submit_transfer并记录start/end event。这与Ascend英文/PO概述的“D2H直接提交当前计算流”不同，应以目标版本实际调用链为准，不能把文档和另一父类混用。

## 加载与资源退役

start_load_caches按首block排序，分配一个int8连续device缓冲容纳所有完整块，合并连续区域描述符，一次提交H2D，再按存储shape/dtype切成每hash的view。加载会搬整个分配块，和保存裁尾padding的口径不同；业务只消费shape所需元素，不能将padding当有效embedding。

加载使用独立流，目标dst_buf.record_stream(compute_stream)，离开后计算流wait加载流再消费。这个wait是流依赖，不是CPU已经同步完成的回报。Transfer持有stream、描述符和events直到end_event.query为真；_collect_finished只从队首回收，后一个先完成仍可能等前一个。elapsed_time与DEBUG日志在完成后取得，不能当本次NPU性能实测。

DescriptorBufferPool是LIFO容量复用，不足则新建CPU数组及NumPy别名；add_copies写别名，不代表可以在DMA未完成时复用。Ascend将方向映射成CANN H2D=0/D2H=1并使用当前NPU流。底层CPU dispatch承载的是地址/长度元数据，数据本身在NPU/mmap，不能据CPU dispatch宣称这是纯CPU拷贝。

## ready、pin、回报和FIFO各有含义

ECCPUScheduler分配新保存项为not-ready，收到completed_saves才mark_ready；加载dispatch先pin并发独立递增transfer_id。WorkerMetadata.aggregate用列表拼接，mp executor预期TP×PCP回报，其他executor预期1；只在累计回报达到该数后unpin。重复hash的后续dispatch有新ID，旧ID不能释放新pin；但回报列表不携带rank去重，适配器必须保证每参与rank每次恰报一次，不能将重复列表当额外完成rank。

EmbeddingCache的策略是ready且unpinned项按FIFO回收，get命中不自动变成LRU。pin_count=-1表示not-ready，0表示ready/可回收，>0为被引用；held项缺少回报会占容量并让has_pending_push_work继续要求step。它和[Score评分策略](../optimization/vllm_ascend_score_encoder_cache_policy.md)的频率/clock不是一套算法，也不是普通请求结束就统一释放所有CPU cache。

## 验收与剩余边界

记录实际connector类、版本/Runner、instance/DP文件身份、dtype/shape/宽度、saves/loads与transfer_id、参与rank数、event完成、ready/pin和回收，再比较冷/热同媒体输出。不要用“有cache item”证明尚未完成的save可读，或用metadata清空证明DMA已结束。

注册与关闭失败按[pinned mmap排障](../../runbooks/runtime/vllm_ascend_eccpu_pinned_mmap_lifecycle.md)处理；配置总览见[Encoder Cache指南](vllm_ascend_encoder_cache_offload.md)。本次未创建mmap、执行NPU/stream测试、编译扩展或进行吞吐/质量A/B；远端NIXL与全部模型输出形状不在本次闭包中。
