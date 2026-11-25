---
{
  "type": "Runbook",
  "title": "GLM-5.2 MTP IndexShare（variant A′）：MTP draft 复用首步 top-k 但复用步仍须跑 indexer 写 KV cache",
  "description": "Ascend NPU 上 GLM-5.2（GlmMoeDsa 架构，独立部署 ModelRunner：`model_infer.py` + `modeling_glm.py`，DSA/Lightning-Indexer 稀疏注意力 + MTP 投机解码）实现 `config.index_share_for_mtp_iteration`（configuration_glm.py 默认 `True`）：next_n≥2 的 MTP draft 循环复用第一个 decode step 的 Lightning-Indexer top-k 选择。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# GLM-5.2 MTP IndexShare（variant A′）：MTP draft 复用首步 top-k 但复用步仍须跑 indexer 写 KV cache

## 适用场景

Ascend NPU 上 GLM-5.2（GlmMoeDsa 架构，独立部署 ModelRunner：`model_infer.py` + `modeling_glm.py`，DSA/Lightning-Indexer 稀疏注意力 + MTP 投机解码）实现 `config.index_share_for_mtp_iteration`（configuration_glm.py 默认 `True`）：next_n≥2 的 MTP draft 循环复用第一个 decode step 的 Lightning-Indexer top-k 选择，避免每个 draft step 重算 top-k。本卡为 eager 正确性楼层（correctness floor），不含性能收益数据。

## 触发与观测

- 需求（source 0 seq 1）：`index_share_for_mtp_iteration` 生效，MTP draft 循环 step≥2 复用第一步 top-k；默认关闭时与现行代码 byte-identical；不跑模型（板上 byte-identity 由用户执行）。
- 关键事实核对（source 0 seq 80，工具输出逐字）：`transformers.utils.logging` 无模块级 `info`（`has info: False` / `has get_logger: True`）——计划文本里的 `logging.info(...)` 会直接 AttributeError，必须用 `logger = logging.get_logger(__name__)` 后 `logger.info(...)`。

## 探针与操作

- 实现机制（source 0 seq 85，before/after 编辑逐字）：在 `GlmMoeDsaAttention.prepare_qkv` 加 reuse 分支；`reuse_shared_topk` 经 `forward → forward_absorb/forward_absorb_cp → prepare_qkv` 与 `DecoderLayer.forward → MTPLayer.forward → GlmMoeDsaModelMTP.forward → prefill/decode → inference() → mtp_post_process` 全链路显式形参透传（kwargs 在各帧被吸收不再透出，每一跳都要加显式参数）。核心分支（after 逐字）：
```python
        reuse_shared_topk = kwargs.get("reuse_shared_topk", False)
        use_shared = (prev_topk_indices is not None) and (self.skip_topk or reuse_shared_topk)
        if use_shared:
            if reuse_shared_topk and self.indexer is not None and not is_prefill:
                # A': keep the indexer KV cache coherent (only writer) but freeze the selection.
                self.indexer(hidden_states, qr, actual_seq_lengths_kv, kv_len, cos_sin, position_ids, \
                             query_states, \
                             past_key_values_indexer, past_key_scales_indexer, \
                             slot_mapping, block_table, \
                             actual_seq_lengths_q, prefill_extra_input_dict, c8_input_dict,
                             is_prefill)  # discard return
                logger.info(f"[MTP-IndexShare] reused topk shape={prev_topk_indices.shape}")
            topk_indices = prev_topk_indices
```
- 编排侧（`mtp_post_process`）：入口重置 `shared_mtp_topk=None`（不跨 cycle 残留）；`reuse = index_share and next_index>=1 and not was_prefill and shared is not None`；首个 decode step 捕获 `mtp_topk.clone()` 恰好一次。`inference()` 返回值从 3 元组扩到 4 元组（追加 extra=MTP top-k），主模型路径 extra 恒为 None。

## 机制与判别

- **A′ 的关键不变量**：full indexer 层是 MTP 私有 indexer KV cache 的唯一写者，复用步**不能跳过** indexer 调用（跳过会使下一轮 indexer cache 失步/损坏），只能丢弃其返回值、冻结返回 step-0 捕获的 top-k（source 0 seq 85 注释与代码）。
- 门控判别（source 0 seq 218，真实源码上执行）：对 shipped `prepare_qkv` 逐字切片 exec 驱动 5 组用例——A full+flagOFF→重算（indexer 调 1 次、返回新 topk）；B shared 结构层+flagOFF→复用 prev、不调 indexer（原行为）；C full+reuseON+decode→indexer 仍调 1 次且返回冻结 topk（A′ 不变量）；D reuseON+prefill→不触发（calls=0）；E shared 层 prev 为 None→ValueError 防御保留。
- 编排判别（source 0 seq 221）：next_n=1 永不复用；next_n=3 decode 起步 = step0 捕获一次、step1/2 复用；flag OFF = 无捕获无复用（byte-identical）；prefill 起步 = step0 不捕获，step1 首个 decode 捕获、step2 复用（捕获语义锚定"首个 decode step"而非"循环第一步"）。

## 验证信号

- 代码加载（等级：CPU import）：`sys.path` 注入 repo + `models/glm-5.2`（对齐运行期 cwd，目录名带 `-`/`.` 非法包名，须模拟 runner 的相对导入）后真实 `from models.modeling_glm import ...` 成功，运行期内省确认 5 处签名均含 `reuse_shared_topk`（source 0 seq 209）；config 默认 `index_share_for_mtp_iteration=True` 加载正确（source 0 seq 200）。
- 逻辑级验证（等级：CPU 参考/单测 harness，非设备）：prepare_qkv 5 用例全过（source 0 seq 218）、mtp_post_process 编排 4 组全过（source 0 seq 221）。
- 缺口：板上（NPU）byte-identity 与端到端推理未在本轨迹执行（用户保留）；性能收益（少算 top-k）未测量。

## 适用与失效边界

- 适用：GLM-5.2 DSA+MTP 代码形态（indexer full/shared 分层结构、`prev_topk_indices` 线程化已存在的实现）；kwargs 每帧吸收、需显式透传布尔/张量的 ModelRunner 调用链。
- 失效/不覆盖：其他模型若 indexer 无"MTP 私有 cache 唯一写者"约束，可改为直接跳过 indexer（省算力更多）；图模式（npugraph_ex/GE）下新增 kwargs 与 4 元组返回是否兼容 capture 未验证；CP prefill 路径中 prev_topk_indices 为 (prev,next) 元组的形态未在复用分支覆盖；设备级正确性（byte-identity）与性能收益待板上验证。

## 附：断言存档

- GLM-5.2 MTP IndexShare variant A' 的关键不变量：full indexer 层是 MTP 私有 indexer KV cache 的唯一写者，draft 复用步必须仍调用 self.indexer(...)（丢弃返回值）以保持 cache 一致，同时冻结返回第一个 decode step 捕获的 top-k（prev_topk_indices）；门控 use_shared = (prev_topk_indices is not None) and (self.skip_topk or reuse_shared_topk)，reuse 分支仅 reuse_shared_topk and self.indexer is not None and not is_prefill 时触发。
