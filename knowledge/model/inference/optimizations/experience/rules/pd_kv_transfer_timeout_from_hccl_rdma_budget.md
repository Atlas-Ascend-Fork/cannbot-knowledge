---
type: Optimization
title: PD 分离 KV-transfer 同步超时按 HCCL RDMA 超时×重试预算推导，勿硬编码固定值
description: 昇腾 PD（prefill/decode）分离推理中，跨节点 KV-transfer 走 HCCL RDMA，其上层「KV 同步超时」旋钮（llmdatadist 的 LLMConfig.sync_kv_timeout / mooncake 连接器写入的 ASCEND_TRANSFER_TIMEOUT 环境变量）不应硬编码固定值（如 20000ms），应从底层 HCCL RDMA 的退避×重试预算推导：timeout_ms = (4.096 · 2^HCCL_RDMA_TIMEOUT · HCCL_RDMA_RETRY_CNT) // 1000 + 3000（默认 HCCL_RDMA_TIMEOUT=20、HCCL_RDMA_RETRY_CNT=7），并允许 ASCEND_TRANSFER_TIMEOUT 非空时显式覆盖。核心不变式：上层 KV 同步超时 ≥ RDMA 退避×重试总预算 + 3000ms 余量，保证上层永远晚于 RDMA 自身重试耗尽，避免在 RDMA 尚在重试时把传输误判为失败。反例：写死固定超时会在 HCCL_RDMA_TIMEOUT/HCCL_RDMA_RETRY_CNT 被调大后偏小、触发假失败。参考实现 vllm-ascend：utils.py 的 get_transfer_timeout_value()，接入 llmdatadist_c_mgr_connector、mooncake_connector、mooncake_layerwise_connector 三处 KV 连接器。关键昇腾术语：HCCL RDMA、PD 分离、KV cache manager、llmdatadist、mooncake/HIXL、distributed_timeout。
tags:
- task.optimization
- topic.kv_cache
- topic.model_serving
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3983
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# PD 分离 KV-transfer 同步超时按 HCCL RDMA 超时×重试预算推导，勿硬编码固定值

## 适用场景

- 场景：昇腾 PD（prefill / decode）分离部署，KV cache 通过跨节点 RDMA 在 prefill 与 decode 实例之间传输（[online PD 分离推理](../../../concepts/frameworks/online_pd_inference.md)，KV 由 [KV cache manager](../../../concepts/frameworks/kv_cache_manager.md) 管理并跨实例搬运）。传输走 HCCL RDMA，连接器侧有一个「KV 同步超时」旋钮控制上层判定一次 KV 传输失败前等多久。
- 前提：底层 RDMA 链路的容错窗口由两个 HCCL 环境变量决定——`HCCL_RDMA_TIMEOUT`（默认 `20`，作为指数退避的**指数**）与 `HCCL_RDMA_RETRY_CNT`（默认 `7`，**重试次数**）。这两个旋钮一旦被拉大，RDMA 层单次传输可容忍的总退避×重试窗口会指数级变长。
- 通向本规则的判断：**上层 KV 同步超时若是一个与 RDMA 退避×重试预算脱钩的固定值，就可能在 RDMA 尚未耗尽自身重试预算前先行判定传输失败**（上层过早超时，把本可由 RDMA 重试救回的传输误报为失败）。因此该超时不应硬编码，应从 HCCL RDMA 的超时×重试预算推导，并保留一个显式环境变量覆盖口。

**条件 → 优先做什么**：当 PD 分离的 KV 连接器需要设置一个「一次 KV 传输等多久算超时」的值，且底层是 HCCL RDMA、其 `HCCL_RDMA_TIMEOUT` / `HCCL_RDMA_RETRY_CNT` 可能被非默认地调大时 → 不要写死一个固定毫秒数，而是**从这两个 HCCL RDMA 参数推导超时上界，并允许一个显式覆盖环境变量优先生效**。

## 依据（推导公式与覆盖优先级）

超时值的量纲是毫秒（ms）。推导逻辑与优先级：

1. **显式覆盖优先**：若覆盖用环境变量（此处为 `ASCEND_TRANSFER_TIMEOUT`）非空，直接取其整数值，跳过推导。这给运维一个「我知道我在做什么，按这个值来」的逃生口。
2. **否则由 HCCL RDMA 参数推导**：

   ```
   timeout_ms = (4.096 · 2^HCCL_RDMA_TIMEOUT · HCCL_RDMA_RETRY_CNT) // 1000 + 3000
   ```

   - `4.096 · 2^HCCL_RDMA_TIMEOUT` 是单次 RDMA 退避窗口（约 µs 尺度，`HCCL_RDMA_TIMEOUT` 作为 2 的指数）。
   - `· HCCL_RDMA_RETRY_CNT` 把单次窗口乘上重试次数，得到 RDMA 层耗尽自身重试预算所需的总时间。
   - `// 1000` 把 µs 尺度折算到 ms 尺度。
   - `+ 3000` 在 RDMA 总预算之上再叠 3000ms 固定余量，保证上层超时**严格晚于** RDMA 自身重试耗尽的时刻。
   - 默认 `HCCL_RDMA_TIMEOUT=20`、`HCCL_RDMA_RETRY_CNT=7`。

**核心不变式**：上层 KV 同步超时 ≥ RDMA 层退避×重试总预算 + 余量。这样上层永远不会比 RDMA 层更早放弃，避免把「RDMA 还在重试」误判成「传输失败」。这条关系系于 HCCL RDMA env 的固有语义与连接器超时契约。

## 反例（不要做什么）

- **不要**把 KV 同步超时硬编码为一个与 RDMA 预算无关的固定值（例如某固定毫秒常量）。固定值在默认 HCCL RDMA 参数下可能凑巧够用，但一旦 `HCCL_RDMA_TIMEOUT` / `HCCL_RDMA_RETRY_CNT` 被调大以增强链路容错，固定的上层超时就会偏小、在 RDMA 重试窗口内提前触发假失败。
- **不要**只把它做成推导值而不留覆盖口，也不要只留覆盖口而不给推导默认——两者要同时具备：显式覆盖优先、缺省时推导。

## 参考实现及其约束

参考实现来自 vllm-ascend（vLLM 昇腾后端）的分布式 KV 连接器。以下 config 键、环境变量名、公式常量、接入点是**该参考实现的具体形态**，公式的**结构**（RDMA 退避×重试 + 余量、覆盖优先）可迁移，而具体键名与常量绑定此实现。

统一从环境变量推导超时的工具函数（`vllm_ascend/distributed/utils.py`）：

```python
def get_transfer_timeout_value():
    ascend_transfer_timeout = os.getenv("ASCEND_TRANSFER_TIMEOUT", "")
    if len(ascend_transfer_timeout) > 0:
        return int(ascend_transfer_timeout)
    hccl_rdma_timeout = int(os.getenv('HCCL_RDMA_TIMEOUT', '20'))
    hccl_rdma_retry_cnt = int(os.getenv('HCCL_RDMA_RETRY_CNT', '7'))
    return int((4.096 * (2**hccl_rdma_timeout)) * hccl_rdma_retry_cnt // 1000 +
               3000)
```

三处 KV 连接器全部改为消费该函数（不再各自硬编码）：

- **llmdatadist 路径**（`llmdatadist_c_mgr_connector.init_llm_datadist`）：改动前 `llm_config.sync_kv_timeout = 20000`（硬编码 20000ms）→ 改为 `llm_config.sync_kv_timeout = get_transfer_timeout_value()`。这里超时是 `LLMConfig.sync_kv_timeout` 字段。
- **mooncake 路径**（`MooncakeConnectorWorker.__init__` 与 `MooncakeLayerwiseConnectorWorker.__init__`）：此前未把该超时暴露成可配置项；改为在 worker 构造时 `os.environ["ASCEND_TRANSFER_TIMEOUT"] = str(get_transfer_timeout_value())`，把推导值回写成环境变量供底层传输引擎读取。参见 [KV cache manager](../../../concepts/frameworks/kv_cache_manager.md) 中 mooncake / llmdatadist 连接器的传输契约。

约束与边界：

- 覆盖环境变量与推导所用变量是**两套**：`ASCEND_TRANSFER_TIMEOUT` 是上层显式覆盖口；`HCCL_RDMA_TIMEOUT` / `HCCL_RDMA_RETRY_CNT` 是被推导消费的底层 RDMA 旋钮。设置前者会整体旁路后者的推导。
- 公式量纲（µs→ms 的 `4.096` 与 `// 1000`）按参考实现原样保留；其物理正确性未在源侧额外论证，迁移到其它实现时应重新核对量纲。
- 这是 vllm-ascend 的 llmdatadist / mooncake 连接器超时旋钮的实现细节，非各硬件通用框架逻辑；系于昇腾 HCCL RDMA 语义。

## Outcome / 验证

- 源未给 before→after 的传输失败率 / 时延数据（改动的测试口径为 CI）。可观测的确定性结果：KV-transfer 超时不再是硬编码 20000ms，而是随 HCCL RDMA 参数缩放，并可被 `ASCEND_TRANSFER_TIMEOUT` 显式覆盖。
- 验证要点：在非默认 `HCCL_RDMA_TIMEOUT` / `HCCL_RDMA_RETRY_CNT` 下，确认最终生效的 KV 同步超时随之增大（而非停在旧固定值）；设置 `ASCEND_TRANSFER_TIMEOUT` 后确认推导被旁路、直接取该值。

## Evidence

- [vllm-ascend-pr-3983-cherry-pick-from-pr-3981-0-11-0-p-d-make-kv-transfer-env-variable-take-e](https://github.com/vllm-project/vllm-ascend/pull/3983) — 该事件源页记录 PR 元数据（state closed、merged 2025-11-08、touched module `distributed`、7 文件变更含 `vllm_ascend/distributed/utils.py` +14、`llmdatadist_c_mgr_connector.py` +2/-1、两处 mooncake connector 各 +4）与合并态补丁的在线 `.diff` URL，可从中下探核对文件面与增删规模。
- 合并态代码事实：merge commit sha `d4e2a443079e130de81a73397855a597ca69069d`（state MERGED），涉及 `vllm_ascend/distributed/utils.py`、`vllm_ascend/distributed/llmdatadist_c_mgr_connector.py`、`vllm_ascend/distributed/mooncake_connector.py`、`vllm_ascend/distributed/mooncake_layerwise_connector.py`。公式常量、默认值、`ASCEND_TRANSFER_TIMEOUT` 覆盖优先级、三处连接器接入点与合并态 diff 一致。该 merge sha 与 `get_transfer_timeout_value` 函数体来自对合并态一手 diff 的查询——下探事件源页仅含 PR 元数据与在线 `.diff` URL、不含合并态函数体，故逐字复核需取该 `.diff`。
- 边界：源未陈述「硬编码 20000 太短导致传输过早失败」的根因，该动机为推断、未并入事实面；核心断言只落在推导公式、覆盖优先级、三连接器接入点这些 diff 事实上。
