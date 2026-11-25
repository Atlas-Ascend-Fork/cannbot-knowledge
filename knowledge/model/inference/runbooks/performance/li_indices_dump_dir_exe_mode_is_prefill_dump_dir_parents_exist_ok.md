---
{
  "type": "Runbook",
  "title": "Kimi-K3.1 QSFA 整网与单点算子性能对不上：先校正 Decode 单点复现参数，再 dump 实际 LI 索引",
  "description": "Ascend NPU 上以 cann-recipes-infer_K31 跑 Kimi-K3.1（K3-alpha）推理，DSA/QSFA 走 DSL 量化稀疏注意力后端（dsa_backend=npu，enable_dsa_quant），16 rank、Prefill dsa_cp=8 / dsa_dp=2、输入 128k、DSpark7投机解码（MTP draft）、LI TopK=2048。",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# Kimi-K3.1 QSFA 整网与单点算子性能对不上：先校正 Decode 单点复现参数，再 dump 实际 LI 索引

## 适用场景

Ascend NPU 上以 cann-recipes-infer_K31 跑 Kimi-K3.1（K3-alpha）推理，DSA/QSFA 走 DSL 量化稀疏注意力后端（dsa_backend=npu，enable_dsa_quant），16 rank、Prefill dsa_cp=8 / dsa_dp=2、输入 128k、DSpark7投机解码（MTP draft）、LI TopK=2048、GBS=16。当"整网 decode 实测耗时"与"单算子微基准耗时"对不上、需要构造与整网一致的 QSFA 单点测试或取证实际稀疏索引分布时适用。

## 触发与观测

- 触发（source 0 seq 5，用户报告）：QSFA 整网实际跑出来的性能和算子单点测试出来的性能对不上；用户假设"decode 是 dsa 纯 dp、每 rank 都是 128k kvlen、dspark7、li topk 2048"。
- 后续观测（source 0 seq 61，用户报告）：eager 模式 dump 出的 LI indices shape 为 `(2048, 2048)`，与 decode 预期不符。

## 探针与操作

- 源码核对：`rg/sed` 读取 `models/kimi_k3_1/models/modeling_kimi_k3.py` 的 `_forward_dsa`、`_lightning_index` 与 `modules/attention_data.py` 的 `actual_seq_lengths`/`cu_q` 构造，区分 Prefill CP/DP 配置与 Decode 实际打流 shape（source 0 seq 8-18）。
- 关键参数问询：向用户确认全局 batch_size（答复 GBS16，source 0 seq 100）。
- 索引取证（最小侵入 dump，已提交推送 commit 6af493b，eager decode 生效、默认关闭；source 0 seq 163/164 逐字补丁）：
```python
        if self.li_indices_dump_dir and self.exe_mode == "eager" and not is_prefill:
            dump_dir = Path(self.li_indices_dump_dir)
            dump_dir.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "sparse_indices": sparse_indices.detach().cpu(),
                    "block_table": dsa_metadata["block_table"].detach().cpu(),
                    "cu_q": dsa_metadata["cu_q"].detach().cpu(),
                    "kv_lengths": dsa_metadata["kv_lengths"].detach().cpu(),
                    "query_shape": tuple(query.shape),
                    "kv_cache_shape": tuple(cache_inputs["nope_cache"].shape),
                },
                dump_dir / (
                    f"rank{_global_rank()}_layer{self.layer_idx}"
                    f"_step{self.li_indices_dump_step}.pt"
                ),
            )
            self.li_indices_dump_step += 1
```
  设计要点：dump 放在 QSFA attention_op 执行**之后**，避免 CPU 拷贝插在 LI 与 QSFA 之间改变被测访存行为；LI 输出是逻辑 token 索引，必须连同 `block_table`、`cu_q`、`kv_lengths` 一起保存才能判断实际 KV 页离散度（source 0 seq 155/163）。
- 读数校验（source 0 seq 246）：直接 `torch.load(..., weights_only=True)` 打印原始 `sparse_indices.shape/query_shape/cu_q/kv_lengths`，先不做 `reshape/squeeze/concat`，区分"文件里数据不同"与"读取处理改变了形状"。

## 机制与判别

- 源码审读结论（source 0 seq 120/130，agent 基于源码的判定）：**当前 Decode 的 DSA 注意力按请求做纯 DP，Prefill 的 CP8×DP2 不延续到 Decode**。据此校正单点参数（GBS16/16ranks=每 rank 1 请求）：
  - KV 长度不是 128K/8：每 rank 保存自己负责请求的完整 KV；输入 131072 时首次 Verify `actual_seq_lengths_kv=[131080]`（+8），后续随接受 token 增长；
  - DSpark7 的 Q 长度是 8（1 anchor + 7 候选），不是 7；Decode Q heads 为完整 96，无 CP/TP 切头；
  - QSFA 单点入参：Query BF16 `[8,96,576]`、Sparse indices INT32 `[8,1,2048]`（sparse_block_size=1，每 Query 最多选 2048 个 KV token）、输出 BF16 `[8,96,512]`、KV 布局 PA_BSND 每行打包 656 字节；**单点应按 B=1、S_q=8、N_q=96、TopK=2048 测试**。
- 阶段判别（source 0 seq 246）：decode dump 的 LI indices 预期 shape 为 `[8,1,2048]`（squeeze(1) 后 `[8,2048]`）；观察到 `(2048,2048)` 表示 2048 行 Query 的 TopK，不符合本例 decode 配置——不能仅凭 shape 判阶段，但可判定数据来自非 decode 路径或打印前被 reshape，需回读 `.pt` 原始字段确认。
- 未验证推断（假设）：整网 KV 更离散导致 QSFA 耗时增多（用户假设，source 0 seq 22）；本轨迹只交付了取证手段，未完成离散度分析。

## 验证信号

- 源码级观测（等级：源码审读）：`_forward_dsa`/`_lightning_index`/`attention_data.py` 的 shape 构造（source 0 seq 8-18 工具输出）。
- 设备无关的工具验证：dump 补丁经 AST 等价性检查（12 种 mode/switch/phase 组合、文件名递增、dump 位于 attention 之后，source 0 seq 37），git push 成功（source 0 seq 56）。
- 用户报告（等级：用户观测）：`(2048,2048)` shape 打印（source 0 seq 61）；GBS16（source 0 seq 100）。
- 单次观测，无性能数值对比；decode 参数表为该仓库该配置下的源码事实，不外推其他实现。

## 适用与失效边界

- 适用：cann-recipes-infer_K31 的 Kimi-K3.1 DSA/QSFA 实现及其"整网 vs 单点"复现参数校正方法论（先核对 decode 实际 DP/CP 行为与 Q/KV shape，再构造微基准）。
- 失效/不覆盖：其他仓库或后续提交若改变 decode 分片行为则参数表失效；`li_indices_dump_dir` 仅 eager+decode 生效，图模式与 Prefill 不 dump；(2048,2048) 的最终来源（prefill 数据混入 vs 读取端 reshape）在本轨迹未闭环，只有判别步骤；"KV 离散导致耗时差"未证实。

## 附：断言存档

- cann-recipes-infer_K31 的 Kimi-K3.1 DSA 实现中 Decode 注意力按请求做纯 DP：Prefill 的 dsa_cp=8/dsa_dp=2 不延续到 Decode，每 rank 保存自己负责请求的完整 KV（输入 131072 时首次 Verify actual_seq_lengths_kv=[131080]，随接受 token 增长），Decode Q heads 为完整 96 不切头；单算子微基准须按 B=1、S_q=8（DSpark7 为 1 anchor+7 候选）、N_q=96、TopK=2048 构造，Query [8,96,576] BF16、indices [8,1,2048] INT32、输出 [8,96,512]、KV PA_BSND 每行 656 字节。
