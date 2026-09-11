---
type: Runbook
title: vllm-ascend Mooncake connector 在昇腾直连 KV 传输的两个后端不兼容点
description: '在昇腾上用 **vllm-ascend 的 Mooncake connector** 做 PD 分离的 KV cache 直连传输时（`protocol: ascend` + `use_ascend_direct: true`，走 AscendDirectTransport / adxl engine，即 Mooncake 在昇腾上的直连传输后端），传输链路会撞到两个非显式的后端不兼容点：一个源于 **NPU device 内存注册未被隐式触发**，一个源于 **torchair 图模式下 KV cache 布局比 eager 少一维**。两者都发生在把已分配的 NPU HBM 上的 paged KV 缓冲区登记进 RDMA 式传输引擎、再逐块传输的路径上，症状分别是「连上 segment 但 transfer 报错」与「块长计算取错维度」。'
tags:
- task.debugging
- topic.kv_cache
- topic.graph_execution
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/5044
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/2947
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a2
---

# vllm-ascend Mooncake connector 在昇腾直连 KV 传输的两个后端不兼容点

## 适用场景

在昇腾上用 **vllm-ascend 的 Mooncake connector** 做 [PD 分离](../../concepts/frameworks/online_pd_inference.md)的 KV cache 直连传输时（`protocol: ascend` + `use_ascend_direct: true`，走 AscendDirectTransport / adxl engine，即 Mooncake 在昇腾上的[直连传输后端](../../concepts/techniques/hixl.md)），传输链路会撞到两个非显式的后端不兼容点：一个源于 **NPU device 内存注册未被隐式触发**，一个源于 **torchair 图模式下 KV cache 布局比 eager 少一维**。两者都发生在把已分配的 NPU HBM 上的 paged KV 缓冲区登记进 RDMA 式传输引擎、再逐块传输的路径上，症状分别是「连上 segment 但 transfer 报错」与「块长计算取错维度」。

这里的 connector 是 vllm-ascend 的 `MooncakeConnectorStoreV1` / `mooncake_connector.py`，与 cann-recipes-infer 的 `--engine_backend mooncake`（见 [mooncake-ascend-hixl-kv-transfer-bringup](mooncake_ascend_hixl_kv_transfer_bringup.md)）是**不同框架的不同实现**，config 面与代码面都不同，排查时勿混两处。

---

## 信号 1：仅用 store connector 时 device 内存未注册 → transfer 报 103901

### 症状

decode 端推理有响应，但日志报「**成功连上 segment（对端 = prefill pod IP），随即 transfer failed，错误码 `103901`**」，decode 取不到 prefill 传来的 KV cache（adxl engine 传输失败）。

关键诊断信号：在 plog（`grep -rn ERROR /root/ascend/log`）中只看到

```
AscendDirectTransport register mem xxx mem type:0
```

**没有 `mem type:1`**。其中 `mem type:0` = host 内存注册、`mem type:1` = device(NPU HBM) 内存注册；`mem type:1` 缺失即表示 **NPU device 内存没有成功注册进传输引擎**，传输引擎拿不到已注册的 NPU KV 缓冲区，故 transfer 报 103901。

### 触发条件

部署为 **只挂 Mooncake Store Connector**（`kv_connector: MooncakeConnectorStoreV1`，prefill=kv_producer、decode=kv_consumer，`consumer_is_to_load: true`），无其它 connector；Mooncake `protocol: ascend` + `use_ascend_direct: true`。

### 根因

AscendDirectTransport / adxl engine 对参与 RDMA 式传输的内存需要**预先 register**。**当只使用 store connector 时**，device 内存不会被隐式注册——host 侧那一半（`mem type:0`）注册了，device(HBM) 侧那一半没有，于是引擎侧看不到 NPU KV 缓冲区。

### 修法

在 P、D 两端的 `kv_connector_extra_config` 中显式加入 `register_buffer=true`，显式触发对 NPU device 内存的注册。注册成功后 plog 会出现 `mem type:1`，AscendDirectTransport 才能对已注册的 NPU HBM 做 KV 传输。这是触发注册的正因修法，不是规避式 workaround。

**边界**：证据只覆盖「vllm-ascend 0.11.0rc3 + 仅 store connector + `protocol=ascend`/AscendDirectTransport」这一配置面，且被维护者显式限定到「仅用 store connector」与该 0.11.0rc3 版本；`register_buffer=true` 是该框架该版本的显式开关，含其它 connector 的组合、及其它 vllm-ascend 版本是否同样必需，均不外推。

---

## 信号 2：`register_kv_caches` 写死 `block_rank=3`，torchair 图模式取错维度

### 症状

在 [torchair 图模式](../../concepts/techniques/npu_graph_mode.md)下做 paged KV 内存注册时，`register_kv_caches` 里按 `shape[-block_rank:]` 算的每块传输长度 `block_len` **算错**（把 `num_block` 也算进了块长），导致 KV 传输块长计算错误。

### 触发条件

vllm-ascend Mooncake connector 的 `register_kv_caches` 非 MLA/SFA 分支，在 **torchair 图模式**下执行（eager 模式不触发）。根因是两种执行模式的 KV 物理布局维数不同：

- **eager** KV cache 是 4 维 `[num_block, block_size, num_kv_head, head_dim]`；
- **torchair 图模式** 是 3 维 `[num_block, block_size, num_kv_head*head_dim]`（后两维被压平合并）。

### 根因

原代码写死 `block_rank = 3`（注释 `[block_size, kv_heads, head_dim]`），只对 eager 的 4 维布局成立。torchair 只有 3 维，`shape[-3:]` 会把 `num_block` 也纳入块长维度，`block_len` 因此偏大/取错。

### 修法

把块长维度数改为随实际 KV cache 维数自适应：

```python
block_rank = len(first_kv_cache.shape) - 1
# 4 维取后 3、3 维取后 2；注释更新为
# [block_size, kv_heads, head_dim] or [block_size, kv_heads*head_dim]
```

对应地，合并阶段 `_cat_kv_cache` 也须对 3 维 torchair KV 先

```python
kv.view(kv_shape[0], kv_shape[1], num_kv_head, head_dim)
```

再处理。改后块长计算同时适配 eager 与 torchair 两种布局。

**这是可迁移的失败签名**：它系于「torchair 图模式 KV 布局比 eager 少一维」这一昇腾固有事实，跨版本仍成立——只要在 torchair 下做 paged KV 内存注册、并用固定 rank 从末尾取块维度，就会撞到这个维度假设。

---

## 相关经验

- [Mooncake（protocol=ascend / HIXL）KV 传输后端在昇腾的三个非显式前置约束](mooncake_ascend_hixl_kv_transfer_bringup.md)——cann-recipes-infer 侧的另一实现，同族「注册/bringup 前置约束」，config 面不同勿混。
- [HIXL / HCCS IPC 路径注册内存的 2 MiB 对齐约束](../../optimizations/experience/rules/hixl_hccs_ipc_2mib_alignment.md)——同属昇腾直连 KV 传输的内存注册约束族。
- KV 传输管理与卸载见 [KVCache 卸载](../../concepts/techniques/kvcache_offload.md)。

## Evidence

- 信号 1（issue，维护者确认）：诊断（`mem type:1` 缺失 = device 内存未注册）与修法（`register_buffer=true`）由维护者（gh association=collaborator）在评论中给出，reporter 确认加 `register_buffer=true` 后修复有效。环境：vllm-ascend 0.11.0rc3（vLLM 0.11.0，镜像 `quay.io/ascend/vllm-ascend:v0.11.0rc3`，`VLLM_USE_V1=1`），Atlas 910B4，CANN 8.3.RC2 / torch_npu 2.7.1 / npu-smi 25.2.0，1P1D 同机，模型 Qwen3-8B（TP1/DP1，`block-size 128`、`enforce-eager`、`no_enable_prefix_caching`）。source 未给传输吞吐/时延数字。溯源下探：[vllm-ascend-issue-5044-bug-decode-fail-to-get-kv-cache-from-mooncake-store-when-directly-use-v1](https://github.com/vllm-project/vllm-ascend/issues/5044)。
- 信号 2（合并态 diff）：`register_kv_caches` 中 `block_rank` 由常量 3 改为 `len(first_kv_cache.shape) - 1`、注释同步补充 torchair 3 维布局，`_cat_kv_cache` 对 3 维 KV 先 view 再处理，均核到合并 diff（`vllm-project/vllm-ascend@0563106/vllm_ascend/distributed/mooncake_connector.py`）。source 未给 torchair 下修复前的具体报错文本。溯源下探：[vllm-ascend-pr-2947-feature-mooncake-connector-support-gqa-transport](https://github.com/vllm-project/vllm-ascend/pull/2947)。
</content>
</invoke>