---
type: Runbook
title: PD 分离下 P 端 KV block 提前释放踩内存：等全 decode-rank ACK 延迟释放 vs CDCP push 传完即释放
description: >-
  PD 分离部署中，P 端 KV block 的生命周期必须晚于 D 端完成接收。在 D 主动 pull 的路径上，
  P 若在 prefill 结束后立即释放 block，高并发下 block 可被新请求覆盖，使 decode 拉到损坏的 KV，
  表现为非确定输出或精度异常。保留 pull 时，应按 request_id 收集并去重全部 decode TP rank 的 ACK，
  只在屏障满足后释放。另一选择是 CDCP push：先让 D 预分配 KV，再调度 P 逐层推送，每层传完即释放，
  从调度上消除「先释放、后拉取」的倒挂。前者是正确性补丁，后者还可使传输与 prefill 重叠并降低 P 端显存占用。
tags:
- task.debugging
- topic.kv_cache
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/1691
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/4842
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# PD 分离下 P 端 KV block 提前释放踩内存：等全 decode-rank ACK 延迟释放 vs CDCP push 传完即释放

## 适用场景

在 PD（prefill/decode）分离部署里，P 节点算完 prefill 就立即把该请求的 KV cache block 交还内存池，而 D 节点还在跨节点拉取（pull）这段 KV。高并发下 P 的 prefill 吞吐显著快于 D 的 block 拉取速度时，被释放的 block 会被后续新请求复用并覆盖，D 拉到的是**被踩过的内存**——表现为 KV cache 数据竞态/踩内存（block contention/corruption）、decode 输出错乱或非确定性精度异常。症状随并发升高、随 P/D 吞吐差拉大而加剧；低并发或 P 慢于 D 时可能长期不复现，因而容易被误当偶发。

这条经验的主语是「PD 分离下 P 端 KV block 的内存生命周期必须晚于 D 端把它拉完/收完」这一固有正确性约束：任何用 **pull 语义**（D 主动拉、拉完再通知 P 释放）的跨节点 KV 传输后端搭 PD 分离都会撞到同一竞态。下文给两条修法——① 保留 pull 语义时用「延迟释放 + 全 decode-rank ACK 屏障」堵竞态；② 改用 **push 语义（CDCP，先 D 后 P）** 从调度层面消除释放-拉取的先后倒挂。

## 触发条件

- PD 分离：P、D 分属不同实例，KV cache 需跨节点传输（如 CANN 的 LLMDataDist 连接器，或 mooncake layerwise connector）。
- pull 型 KV：D 用类似 `pull_blocks` 主动从 P 拉 KV，拉完后回送 finished 信号让 P 释放。
- P 端「算完即释放」：`request_finished` 恒不延迟释放（如恒返回 `False`），请求在 P 端一算完就把 block 还池。
- 高并发，且 P 的 prefill 吞吐 > D 的 block 拉取吞吐 —— 是竞态显形的必要放大器。
- **多 decode rank / DP 场景**尤其危险：D 侧有多个 TP rank 各自拉 KV，只要 P 在**任一** rank 尚未拉完时释放，就会踩到那一路。

## 根因

P 端 KV block 的**释放时机**与跨节点 KV **传输完成**没有同步屏障：释放动作发生在「D 全部拉/收完」之前。pull 语义天然把释放决策放在 P 侧、把完成信号放在 D 侧，两者靠异步消息拼接；一旦 P 不等 D 的完成回执就释放，被回收的 block 立刻可被下一个请求分配复用，D 后续读到覆盖后的内存。DP/多 rank 下，即便 P 收到「某个 rank 拉完」也不能释放——必须等**所有**参与该请求 KV 传输的 decode worker 都确认，否则漏等的那一路必踩。这是内存生命周期与跨节点传输不同步导致的正确性隐患。

## 修法

### 修法 A：保留 pull 语义 —— 延迟释放 + 全 decode-TP-rank ACK 屏障

思想：把 P 端释放从「算完即释放」推迟到「所有 decode rank 都确认收完」，用一个按 request 聚合 rank 确认数的计数屏障做同步点。四个要件缺一不可：

1. **延迟释放开关（delay-free）**：`request_finished` 不再无条件立即释放，改为「只要该请求有已计算的 block 就延迟释放」：
   ```python
   delay_free_blocks = len(computed_block_ids) > 0
   return delay_free_blocks, dict(do_remote_prefill=True, ...)
   ```
2. **接收方回执带 rank 身份**：D 拉完 block 后向 P 发完成事件，payload 从 `[request_id]` 扩为 `[request_id, tp_rank, tp_size]`（带上 decode 侧本 rank 号与 TP 规模），P 才知道「谁确认了、总共该等几个」。
3. **P 端计数屏障（全 rank 齐才释放）**：P 侧维护 `done_receiving_counts: request_id -> set(tp_rank)`，只有当某 request 收到的**不同** rank 数 `== decode_tp_size` 时才真正释放延迟的 block：
   ```python
   if tp_rank in self.done_receiving_counts[request_id]:
       logger.warning("Received duplicate done signal ... Ignoring.")
       return False                       # 去重：重复 rank 不计数
   self.done_receiving_counts[request_id].add(tp_rank)
   if len(self.done_receiving_counts[request_id]) == decode_tp_size:
       self.done_receiving_counts.pop(request_id)
       return True                        # 全部 decode rank 确认 → 释放
   return False
   ```
4. **同一 rank 重复确认去重**：屏障计的是**不同** rank 集合，不是计数递增——同一 rank 的重复 done 信号必须被忽略（上面 `set` + 早退），否则重复确认会把计数凑满导致**提前释放**、竞态重现。
5. **握手改同步 req-rep**：P 处理完完成事件后回一条 ACK（`send_multipart((identity, b"", b"receiving decode finished"))`），D 端发完 `sock.send(...)` 后 `_ = sock.recv()` 阻塞等回执，由 fire-and-forget 变为同步确认，杜绝「D 以为发出去了、P 其实没收到」的漏等。

### 修法 B：改用 push 语义 —— CDCP（先 D 后 P）从调度层消除倒挂

思想：pull 型（CPCD，先 P 后 D）的病根是「P 先持有 KV、D 后来拉、拉完再通知 P 释放」，释放天然落在拉取之后且要靠回执触发。把编排**反转为 CDCP（先 D 后 P）+ push**，让 P 逐层主动把 KV 推给已预分配好的 D，就不再需要「等 D 通知才释放」：

1. proxy 先按 decode 负载选 D（`select_decoder`），置 `do_remote_prefill=True`、`do_remote_decode=False`，并带一个 `metaserver` 回调 URL；请求**先发给 D**，D 预分配 KV cache 块。
2. D 回调 proxy 的 `/v1/metaserver`（带回 `request_id` 与 `kv_transfer_params`）；proxy 此时才选 P（`select_prefiller` → `send_request_to_service`），把带 D 预分配 block 信息的请求发给 P。
3. P 执行 prefill 并**逐层 push（layerwise）** KV 到 D：一层传完即可推送、不必等整段 KV 算完；**传完 P 即刻释放该 KV，无需等 D 通知**。

收益（定性）：P 侧 KV 传完即释放、无释放延迟，省 P 显存；KV 传输可与 P 侧计算重叠；并规避 DP 场景下 P 节点因通信超时而 hang 的问题（编排反转把「等对端」从 P 的关键路径上移走）。协调逻辑建议寄生在 proxy 的 metaserver 回调上，不单独引入 coordinator 组件，以免额外维护与流程步骤。

### A vs B 怎么选

- 已有 pull 型连接器、不想动调度拓扑：用 **A**，最小侵入地把释放锁到「全 rank ACK」之后即可堵住踩内存；代价是 P 侧 KV 释放被拖延、占 P 显存，且传输难与 P 计算重叠。
- 能改 proxy/metaserver 编排、且传输后端支持 layerwise push：用 **B**，从结构上消除释放倒挂，顺带拿到显存回收更快 + 传输-计算重叠 + 规避 DP hang。A 是正确性补丁，B 是把正确性做进调度设计。

## correctness / 边界

- A 是纯正确性修复（消除踩内存），源未给 before→after 量化 benchmark，效果由「释放晚于所有 rank 拉完」的设计论证支撑，不作性能断言。
- B 的收益均为定性（RFC + PR 描述，未给量化数字）；「规避 DP hang」属作者/维护者披露、非独立复测。
- 释放/传输的是昇腾 NPU 上 P 节点的 KV cache block，跨节点走 CANN 的 LLMDataDist（A）或 mooncake layerwise connector（B）；这不是各硬件一致的纯框架版本对齐，系于具体 KV 传输机制。
- CDCP 本身是调度层算法（释放时机、push vs pull、传输-计算重叠），与具体硬件无关、可迁移。

## 参考实现及其约束

- 修法 A：vLLM-Ascend 的 `vllm_ascend/distributed/llmdatadist_c_mgr_connector.py`——D 侧 `_read_blocks` 末尾 `send_finish_to_remote(host, port, request_id)`、P 侧 `request_finished` 的 `delay_free_blocks` 与 `_increment_task_count` 全-rank 屏障。约束：payload 必须带 `tp_rank/tp_size`、屏障必须按 rank **集合**去重（非计数递增），这些是该参考实现落地要件、也是技术本身的正确性要件；释放目标端口用 `remote_port`。
- 修法 B：vLLM-Ascend 社区 layerwise connector（mooncake 传输后端）+ load-balance proxy 的 `examples/disaggregated_prefill_v1/load_balance_proxy_layerwise_server_example.py`——`_handle_completions` 先 `select_decoder` + `do_remote_prefill=True`，`/v1/metaserver` 回调再 `select_prefiller` + `send_request_to_service`；原先「先选 P、`do_remote_decode=True`、D 去 pull」的 `_handle_select_instance` 整段被删。约束：需传输后端支持逐层 push；RFC 为 open、落地 PR 已合并。
- 相关静态概念：[online-pd-inference](../../concepts/frameworks/online_pd_inference.md)、[kv-cache-manager](../../concepts/frameworks/kv_cache_manager.md)。
- 相关动态经验：mooncake 连接器 bringup 见 [mooncake-ascend-hixl-kv-transfer-bringup](../runtime/mooncake_ascend_hixl_kv_transfer_bringup.md)；PD 建连地址广播见 [multinic-pd-advertise-address-launch-config](../../optimizations/experience/anti_patterns/multinic_pd_advertise_address_launch_config.md)。

## Evidence

- 修法 A（延迟释放 + 全-rank ACK 屏障 + 去重 + 同步握手四要件均为合并态 diff 事实，merge sha `6b188ededc6a234a286a440439ac419cc9efa64d`）：[vllm-ascend-pr-1691-0-9-1-pd-added-support-for-delay-free-blocks-in-prefill-nodes](https://github.com/vllm-project/vllm-ascend/pull/1691)
- 修法 B（CDCP proxy 编排反转，先 select_decoder / do_remote_prefill=True、metaserver 回调再 select_prefiller）：merge sha `2c291bc63f24abde489e93d91af8f8f517d618d7` 属落地实现的合并态 diff，其 RFC 入口见下探链（issue-4842 仍 open）：[vllm-ascend-issue-4842-rfc-cdcp-scheduling-for-disaggregated-prefilling-with-kv-cache-layerwise](https://github.com/vllm-project/vllm-ascend/issues/4842)