---
type: Guide
title: SGLang NPU流式会话复用的页对齐与回退
description: 说明NPU会话prefix不足一页或低于保护边界时释放slot并回退普通前缀匹配，以及尾部截断需页对齐以防SWA双重释放。
tags:
- task.implementation
- topic.memory
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/session/streaming_session.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/unified_radix_cache.py
  role: implementation
created_at: '2026-11-08T12:10:40Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
---

# SGLang NPU流式会话复用的页对齐与回退

try_match_prefix先查可用会话slot。NPU且page_size>1时，以min(已提交长度,本次key长度)向下页对齐；结果为0或低于cache_protected_len则release_session并返回None，后续重新走普通树前缀匹配和请求行分配，仍可命中树内受保护前缀，仅没有可复用前缀时才完整prefill，避免丢弃无法安全重用的尾页却继续持有槽。

真正借用slot.kv后，要求prefix不短于保护边界。NPU总对prefix向下页对齐；其他平台只有回退跨过SWA eviction cursor时才同样处理。truncate_committed之后_free_tail，页中间切分会令dead/alive两边重复释放同页，不能为追求token级复用而移除此边界。

这是流式会话活slot记录的借用和tree lock生命周期，不是所有radix匹配都统一向下截断的结论。应验证不足一页、恰好一页、保护前缀、retraction retry与SWA已淘汰区，确认token输出、页计数和会话结束后资源归还；命中率下降可能来自正确性回退，不应直接诊断为缓存失效。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
