---
type: Guide
title: vLLM Ascend 短请求优先：Prefill 队列、公平性与阈值调优
description: 在 FCFS Prefill 或混部部署使用 ShortRequestFirst，按真实 prompt 分布和长请求等待尾部设阈值，识别
  D 端、batch-job 与 CPP 的组合限制。补充中文profiling-chunk旧译文兼容性裁决、CPP组合与队列安装边界。
tags:
- task.optimization
- topic.model_serving
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/short_request_first.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/short_request_first.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/short_request_first_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/scheduler_profiling_chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: implementation
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-10-30T12:23:56Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 短请求优先：Prefill 队列、公平性与阈值调优

## 适用条件

用于固定版本 FCFS 的同步或异步调度：普通服务、PD P 端和 PD 混部均可；不依赖 recompute_scheduler_enable。适合长短 prompt 分布偏斜、短请求 TTFT 优先于严格到达次序的负载。PD D 端 kv_consumer 与 batch-job-aware 不支持。

## 队列语义与最小配置

在 additional_config.scheduler_config.short_request_first_config 中设 enabled=true、threshold、long_max_wait_ms。默认 threshold=256，按完整 num_prompt_tokens 分类；immediate 恢复类请求优先，其次 aged-long，再 short，最后普通 long。

long_max_wait_ms=0 禁止老长请求提升，表示严格短请求优先，绝非立即提升。正数控制长请求反饥饿。只改变 waiting queue，不是抢占正在执行的长请求，也不改变 balance scheduling 跨 DP admission 的开关语义。

## 调优和验收

先用真实 prompt histogram 找短请求群与长尾的分界，P70–P85 仅是缺少分布模型时的起点。阈值过低或过高都会让请求落入同一队列。先测 strict-short-first 下长请求等待的 P90/P95，再在正常尾部等待和服务允许的最大排队时间之间选择 long_max_wait_ms；不能按平均短请求 TTFT 直接设置。

连续三次长请求越过等待中的短请求会出现降级告警；先核对 threshold 是否过小，再调整等待上限。每 5 秒聚合日志用于确认实际队列行为。CPP 可以安装 SRF 队列，但需 enable_balance_scheduling=false，不能同时启用 CPP 与 balance。

比较各长度桶 TTFT、长请求最大等待、饥饿和吞吐；只报告平均值会掩盖公平性问题。关闭 enabled 恢复原策略。以上为固定文档与配置核对，本次未运行流量实验。


## 平台证据待补

完整主指南仅限定FCFS、P/MIXED角色与队列组合，没有整项功能的平台矩阵；配置类本身也不能证明某硬件的服务链路可用。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 中文译文裁决与队列安装边界

固定short_request_first.po的40条有效非空翻译已全文对照当前英文，0obsolete/fuzzy；39条msgid仍精确匹配。那条旧兼容性msgid/译文把profiling-chunk scheduling也列为不支持，当前英文已明确支持组合，并增加CPP需关闭balance的说明。不能把旧PO的这一句覆盖当前英文与固定实现，也不能据PO没有fuzzy标记认定它已同步。

所读ProfilingChunkScheduler.__init__在short_request_first_config.enabled时显式调用install_short_request_first_waiting_queue；BalanceScheduler也在判断balance admission开关前安装，ShortRequestFirstAsyncScheduler在其初始化阶段按开关安装。它们是所述构造入口，不证明所有自定义scheduler都自动复用队列。

install_short_request_first_waiting_queue首先要求FCFS；若waiting已经是ShortRequestFirstRequestQueue则返回原对象，不通过重复安装改threshold/long_max_wait_ms；其他非空waiting会拒绝安装，必须在request admission之前接入。不能把静态配置变更或已有队列存在当作请求已按新参数重排。

这里所述CPP组合沿profiling_chunk_config路线核对：固定配置还要求PP>1，并拒绝profiling_chunk与enable_balance_scheduling同时开启。构造/校验分支存在不是完整CPP执行、分布式进度或吞吐/公平性实测；记录最终scheduler类、队列类型与有效参数后再按前述各长度桶验收。本次未创建scheduler或运行请求。
