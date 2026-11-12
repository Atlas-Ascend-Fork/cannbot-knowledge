---
type: Guide
title: SGLang 昇腾 LoRA 的驻留槽、逐 rank 一致性与安全清零
description: 补齐 Ascend LoRA 上层池管理：rank/模块 admission、确定性槽分配、pin/LRU/FIFO 和复用前清零。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/mem_pool.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/eviction_policy.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/lora_config.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/lora/lora_manager.py
  role: supporting
created_at: '2026-11-08T12:22:44Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
---

# SGLang 昇腾 LoRA 的驻留槽、逐 rank 一致性与安全清零

## 与 Ascend 后端的连接

Ascend LoRA 的 SGEMV 读取 batch adapter indices，这些 indices 来自 LoRAManager 创建的 LoRAMemoryPool；池管理文件本身没有 NPU 关键词，却直接决定多 adapter 推理是否读取正确权重。以下仅承载可接入 Ascend Dense LoRA 的公共管理机制，不把通用池中的 MoE/added-token 分支推定为 Ascend backend 已支持。

## admission 与槽位

池先检查 adapter rank 不超过 max_lora_rank、新增 token 数不超过预留容量、具体模块集合规范化后的target_modules须为允许模块子集；字符串all/all-linear被归一为{'all'}标记，admission遇到该标记直接通过模块部分，不执行子集检查（rank/新增token检查仍先执行）。LoRAConfig 还过滤 token_id 小于 base_vocab_size 的“伪新增 token”；Ascend embedding 本身仍拒绝真正 extra embeddings。

None 表示 base model，是合法 UID，区别于 EMPTY_SLOT。每批按 UID 排序后更新策略/装载，避免 TP 进程不同 Python hash seed 造成槽号和 LRU 次序不一致。优先空槽；驱逐时排除当前 batch adapter 与 pinned adapter，并优先保留 base slot。LRU/FIFO 依据各自 OrderedDict 顺序，容量被活跃/pinned 占满则失败。

## 复用、传输与验证

base slot 或 remove_lora 会清零全部对应 A/B、embedding/head 等缓冲；adapter 缺少某个权重也必须 zero，防止继承前一个 adapter 的残留。strict_loading在写入设备权重缓冲前拒绝未匹配模块，非strict告警；prepare_lora_batch可能已先移除被驱逐UID的双向映射和策略记录，再调用装载，因此校验失败不保证驻留元数据保持原状。pinned CPU transfer 遇 dtype 不一致时先搬设备再 cast；overlap pinned cache 还核对 key 的 shape/dtype，不能默默复用碰撞内容。

检查各 rank UID→buffer ID、rank mask、缺失权重、base/adapter 交替和 graph replay 的输出，比较单 adapter 参考。驻留池与 pinned cache 占用额外内存，频繁驱逐增加传输；调整容量/策略需重建池，并重新核对 graph 静态地址。本次未执行 adapter 或测得吞吐收益。

## 相关机制

- [SGLang 昇腾 LoRA 的 SGEMV、批次元数据与图边界](sglang_ascend_lora_sgemv_batch_graph.md)
