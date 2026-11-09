---
type: Guide
title: vLLM Ascend Encoder Cache：评分管理与 CPU mmap 传输契约
description: 区分 Score 与 ECCPU 的缓存策略和数据面，说明配置组合的 V1/V2 消费边界、父类保存流与中文 PO 差异，核对 CANN
  pinned mmap、内存预算和关闭生命周期。 ECCPUConnector的支持范围限定MRv2、ec_both和单host /dev/shm，并受文档所列双CANN能力门禁约束。
tags:
- task.implementation
- topic.multimodal
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/encoder_cache_cpu_offload.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/encoder_cache_manager.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/encoder_cache_cpu_offload.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/worker/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/ec_shared_region.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/scheduler/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/CMakeLists.txt
  role: constraint
created_at: '2026-10-29T09:42:28Z'
updated_at: '2026-11-02T11:49:32Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- ECCPUConnector：MRv2 ec_both
---

# vLLM Ascend Encoder Cache：评分管理与 CPU mmap 传输契约

## 范围与待确认平台

本卡为 draft：来源以 CANN 能力而非明确 NPU 产品表限定，未取得目标硬件验证。ECCPUConnector 仅 MRv2、单 host /dev/shm、ec_both；不支持跨节点/NIXL/P2P。需 CANN 同时提供 aclrtMemcpyBatchAsync 与 aclrtHostRegisterV2(ACL_HOST_REG_PINNED)，Linux kernel>5.10。缺任一能力初始化失败，不静默改用 pageable 或逐次 memcpy。

## 策略和数据面分开

EC manager 决定缓存管理，connector 决定搬运；选择 ScoreEncoderCacheManager 即选用评分策略，不额外伪造 enabled。来源默认 cpu_cache_slots=100000、max_clock=15、clock_decay_every=64、watermark=0.2、promote_percentile=0.2，含义需按 manager 配置读取。自定义 manager_cls 通过 create_manager 创建，不能把 manager 字段混入 KV transfer。

ECCPUConnector 的 ec_cpu_bytes 是正整数且至少容纳一 encoder block；额外检查 /dev/shm tmpfs 容量和 host RAM。TP workers 映射同一文件，但每进程独立向 CANN 注册自己的虚拟映射。

## 流与清理契约

文档概述miss后encode与D2H同计算流；本批对照固定原生父类发现D2H实际在保存流等待计算流后提交，详见后文。只有TP0/PCP0写重复输出，加载H2D用专用流并建立消费前依赖；注册API存在不证明所有connector具有相同pin行为。

文档的关闭保护以正常worker shutdown为背景：同步成功后才unregister/cleanup，失败会提前退出；构造失败另有finally cleanup，不能把“保留至退出”概述推广到所有路径。/dev/shm残留需结合具体阶段和inflight状态判断。

## 验收、停止与回退

验证冷/热相同多模态输入的 encoder 跳过、hit、拷贝完成和输出一致，覆盖并发/退出；性能分开统计 encode 节省和 H2D 成本。目标 CANN/内核能力不足、mmap注册失败或输出不同则停用 connector，回到 encoder 重算。CPU/mock 不替代 NPU 测试，本次未运行。


## 固定父类接线与文档差异

对照原生vLLM v0.32.0的ECCPUWorker、scheduler和共享区后，保存实际走池化save stream等待compute stream，事件完成后回报；不能将英文/中文“直接在current compute stream保存”的概述套到这个父类版本。加载、descriptor生命周期、FIFO ready/pin与transfer_id回报详见[ECCPU搬运接线](vllm_ascend_eccpu_transfer_pipeline.md)。

正常shutdown先event同步、再NPU同步/unregister及region cleanup；构造失败却另有finally cleanup路径。能力探针、通用copy fallback与ECCPU强制双能力门禁、mmap残留的阶段判断见[pinned mmap排障](../../runbooks/runtime/vllm_ascend_eccpu_pinned_mmap_lifecycle.md)。不能据配置/插件名或现有文件宣称NPU内存已注册、DMA已完结。

Score配置的slot预算、理论cost、clock与实际V1消费者见[评分策略](../optimization/vllm_ascend_score_encoder_cache_policy.md)；它不等于ECCPU的共享块池。当前所读Score消费者在V1，ECCPU文档限定V2，组合不能靠同时填配置就当作已验证。

encoder_cache_cpu_offload.po的13个有效非空条目已全文与当前英文复核，无obsolete/fuzzy且msgid均可匹配；本批作为补充来源绑定，仍保留上述文档/父类差异。译文复核不证明生成器或线上HTML覆盖，没有执行上游工具或NPU。
