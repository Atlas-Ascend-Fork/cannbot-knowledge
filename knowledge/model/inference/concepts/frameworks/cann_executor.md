---
type: Concept
title: CANN Executor：统一模型执行与调度
description: 说明当前统一 Executor 的配置、模型/缓存契约、packed 输入、多模态编码和统一 draft 生命周期，撤回旧 runner 分类。
tags:
- task.implementation
- topic.architecture
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/executor_design.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py
  role: implementation
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- agnostic
---

# CANN Executor：统一模型执行与调度

## 组件与入口

`executor/` 是 Recipes 自带的推理框架。OfflineInference / OnlineInference → Scheduler → ExecutionEngine → ModelWorker → Model 分层处理请求、状态、模型生命周期与算子执行。SGLang 集成、HSTU 和多模态生成模型可有独立入口，不从一个执行器推广其接口。

`executor/scripts/function.sh` 仍先检查 `models/${MODEL_DIR}/infer.py`，不存在时走 `executor/offline/infer.py`。当前 DeepSeek-V3.2-Exp、Kimi-K2-Thinking、LongCat-Flash 已迁到统一执行器；旧 ModelRunner 和私有 runner 清单不再适用。HSTU 仍有独立 gin/torch.distributed 路径。

## 配置与请求

InferenceConfig 聚合 DataConfig、ModelConfig、ParallelConfig、SchedulerConfig、DisaggConfig、SpeculativeConfig 六组。YAML、启动注入及推导字段不能混用，见[配置](../techniques/inference_config.md)。Tokenizer 由 ModelWorker 通过 registry 加载到 hf_config.tokenizer，Engine/Scheduler 复用；标准模型回退 HF，特化模型可注册自定义 tokenizer。

Batch.input_ids 为一维 packed token。Prefill 元数据包括各请求真实长度、累计 Q/KV 边界；模型按请求尾部计算 LM Head，通常返回 `[B,1,V]`；Decode 返回 `[B,q_len,V]`。静态 Decode 可补齐 batch，CP 的补齐/请求所有者另按 metadata 处理。参见[Packed Sequence](../techniques/packed_sequence_metadata.md)。

## 模型契约

- 构造器接收 HF config、InferenceConfig、CommManager，显式声明通信组；权重由 `load_weights` 映射到模块 loader，再由模型 `process_weights_after_loading` 完成转置、NZ 和量化后处理，框架只委托。
- `forward(input_ids, position_ids, forward_metadata, **kwargs)` 返回 logits 或 `(logits, prev_hidden_states)`。可选输入预处理由模型 `preprocess_model_inputs` 提供。
- 缓存由 `get_cache_info` 声明，统一管理器分配并绑定 CacheEntry；无声明时才回退模型 `init_cache(device)`。离线 CPU offload workspace 单独申报和预算，见[缓存管理](kv_cache_manager.md)。
- 惰性 `_specs` 注册解析主模型、可选 MTP 模型及配置类；统一 draft_worker 当前支持 MTP/DSpark，见[MTP 接入](../../guides/integration/mtp_speculative_decode_model_onboarding.md)。

## 调度、图与多模态

Offline 优先 Prefill-ready，其次 MM Encode，最后 Decode。多模态 Processor 准备输入，独立编码批次把请求级结果写入 MMEmbeddingStore；Prefill 按请求顺序取 visual_embeddings 作为模型参数，不能塞入 ForwardMetaData。Encode 与语言 Prefill 的 token 预算和计时分别处理。

ModelWorker 对 Prefill 调 eager，Decode 才按 eager/ge_graph/npugraph_ex 分派。主模型 main_decode、draft mtp_decode 与持久缓存宽度命名空间见[图模式](../techniques/npu_graph_mode.md)。npugraph_ex+持久缓存的非预热执行会跳过 guard，调用方必须保证输入契约，不能视为框架自动验证了动态形状。

OnlineInference 复用引擎、模型与基础调度器，增量是 HTTP/ZMQ 控制面、阶段协商与 KV 传输。在线仅有 PREFILL/DECODE 分离角色，见[在线 PD](online_pd_inference.md)。Profiler 的 post-profile 窗口与完整 Decode 统计分离，见[计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)。

## 接入验收

先以真实权重跑 eager，并覆盖不等长、多请求、EOS 与长度截断，再验证并行、分页缓存及图模式。force_eplb 是性能分析中的人工路由，不能作为真实精度或生产负载依据。仓库源码可确认接口与分支，本次没有执行 NPU 推理。


## Evidence

- [executor_design.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/executor_design.md)（primary）
- [function.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh)（implementation）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [support_models.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py)（implementation）
- [scheduler.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py)（implementation）
