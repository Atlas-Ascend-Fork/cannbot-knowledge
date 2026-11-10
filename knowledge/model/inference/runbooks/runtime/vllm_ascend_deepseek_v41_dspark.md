---
{
  "type": "Runbook",
  "title": "vllm-ascend DeepSeek-V4.1 dspark 长稳压测接受率衰减到 0 与回答截断的根因诊断规则（PD 分离 + 双 ACL graph）",
  "description": "针对 PD 分离（Mooncake）+ decode 侧主模型/dspark draft 双 ACL graph 长稳压测中 dspark 接受率逐渐衰减到 0、回答截断的症状，给出审查级多根因诊断规则：候选根因按置信度排序为（1）部署二进制缺 c60545866（draft 纯 SWA 层误用 YaRN 插值 RoPE）或 72521a79c（indexer topk 过滤被注释）两个新修复；（2）draft 私有环跨请求 KV 残留（PD 下 draft SWA KV 冷窗口 + 环分配复用不清零，随请求 churn 单调放大）；（3）V4.1 draft 因果窗口语义偏差（cad.causal 在 dsa_v41 无消费者，恒走因果窗口，每步静态拉低接受率）。诊断规则给出区分三者的探针与对照实验，以及激活边界（私有环机制依赖 VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL=1，envs.py 重复 key 使默认值为 0）。全部结论为只读代码审查级，轨迹内无运行时验证。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# vllm-ascend DeepSeek-V4.1 dspark 长稳压测接受率衰减到 0 与回答截断的根因诊断规则（PD 分离 + 双 ACL graph）

## 适用场景

- 框架/版本：vllm-ascend 硬件插件，分支 `releases/v0.27.1rc`（HEAD `6746201ec`，审查范围 `09220f435~1..HEAD`，69 个非合并提交、116 个文件、约 2.37 万行新增）；模型 DeepSeek-V4.1-Flash。
- 投机解码配置：method=dspark、num_speculative_tokens=5；block-size 128、max-model-len 150000、量化 deepseek_v4_fp8、max-num-seqs 16、DP+EP。
- 部署形态：PD 分离（MooncakeHybridConnector KV 传输），prefill 侧 eager（`--enforce-eager`），decode 侧主模型与 dspark draft 均走 ACL graph capture/replay；线上配置使用 `--no-async-scheduling`。
- 症状（用户报告的生产现象，来源见触发与观测）：长时间稳定压测中，decode 侧 dspark 接受率随时间逐渐衰减到 0，且请求返回不完整的回答（截断）。
- 信息缺口声明：本卡来自只读代码审查会话（一个深审查子会话 + 一个主控交叉复核会话），轨迹内没有任何运行时验证、没有接受率/精度指标采集；所有结论均为审查级（代码证据 + 推理），证据等级逐条标注于验证信号一节。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

生产触发（用户提供，非客观信号）：

- "长时间稳定压测中，随着时间推移 decode 侧 dspark 接受率 (acceptance rate) 逐渐衰减到 0，且请求返回不完整的回答（截断）"（来源记录 事件 2，任务输入）。
- 完整线上 P/D serve 配置（来源记录 事件 21）：`vllm serve ${LOCAL_PATH_1} ... --max-model-len 150000 --max-num-batched-tokens 4096 --max-num-seqs 16 --gpu-memory-utilization 0.95 --block-size 128 --quantization deepseek_v4_fp8 --no-async-scheduling --kv-transfer-config '{"kv_connector": "MooncakeHybridConnector", ...}' --enforce-eager --speculative-config '{"num_speculative_tokens": 5,"method": "dspark"}'`（prefill 侧），decode 侧同配置去掉 `--enforce-eager`；配置中未显式设置 `VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL`。

核心机制结论（审查级）：

> PD 分离下 dspark draft 私有环跨请求 KV 残留机制：draft 的 SWA KV 只在请求到达 decode 实例后逐步积累（dspark_proposer.py:304-305 每步只写本步 scheduled 的 verify tokens），私有环按 allocation 句柄复用槽位且分配回收不清零，新请求前约一个窗口长度的 decode 步内 draft 注意力窗口可读到上一个请求残留的语义性 KV，请求 churn 越密集平均接受率衰减越严重；该机制是长稳压测接受率衰减到 0 的候选根因（审查级结论，轨迹内未运行时验证）。

> 回答截断机理：接受率衰减到 0 使单步吞吐坍塌，客户端超时/取消表现为不完整回答；截断与接受率衰减是同一根因的两个面，而非独立的输出处理 bug（审查级推断，未运行时验证）。

逐字客观观测（工具结果，均来自代码读取 / git 考古）：

dspark_proposer.py:304-305（来源记录 事件 8，dspark_proposer.py 全文读取；事件 99 为主控会话独立复读同段）：

```python
        self._dflash_num_context = int(cad.query_start_loc_cpu[batch_size])
        self._dflash_hidden_states[: self._dflash_num_context] = target_hidden_states[: self._dflash_num_context]
```

`_clamp_private_context_slots_to_tail_window`（dspark_proposer.py:250-274，同事件 8；注释表明只有尾部窗口内的 context 写入会落在环上，窗口外的行被屏蔽为 -1 不写）：

```python
    def _clamp_private_context_slots_to_tail_window(
        self, cad: CommonAttentionMetadata, batch_size: int
    ) -> None:
        """Keep only each request's tail-window context writes on the ring.

        The draft context precompute would otherwise scatter the whole
        context span into the ring; a span longer than the ring capacity
        wraps onto itself and the surviving rows would depend on scatter
        ordering. Skipping the rows below each request's tail window mirrors
        the target model's "commit only the trailing window" discipline;
        the skipped rows are outside the protocol-A table's exposed range
        and are never read.
        """
        qsl = cad.query_start_loc[: batch_size + 1]
        num_context = self._dflash_num_context
        spans = qsl[1:] - qsl[:-1]
        keeps = spans.clamp_max(max(self._private_ring_window.values()))
        boundary = torch.repeat_interleave(
            qsl[1:] - keeps, spans, output_size=num_context
        )
        head_rows = torch.arange(num_context, device=qsl.device) < boundary
        for gid in self._private_ring_window:
            buffer = self._per_group_context_slot_mapping_buffers.get(gid)
            if buffer is not None:
                buffer[:num_context].masked_fill_(head_rows, -1)
```

私有环 ring 表 kernel（vllm_ascend/ops/triton/private_circle_ring_table.py:40-56，来源记录 事件 344 全文读取）——环内寻址是"allocation 句柄 + 列号取模"的相对映射：

```python
    seq_len = tl.load(seq_lens_ptr + row).to(tl.int64)
    alloc = tl.load(alloc_ids_ptr + row).to(tl.int64)

    # first_page = max(0, (seq_len - window) // BLOCK_SIZE)
    first_page = tl.maximum((seq_len - window_size) // BLOCK_SIZE, 0)
    # logical_count = max(1, (seq_len - 1) // BLOCK_SIZE + 1)
    logical_count = tl.maximum((seq_len - 1) // BLOCK_SIZE + 1, 1)

    base = 1 + alloc * BLOCKS_PER_ALLOC

    for col_start in range(0, num_cols, TILE_SIZE):
        cols = col_start + tl.arange(0, TILE_SIZE)
        mask = cols < num_cols
        in_range = (cols >= first_page) & (cols < logical_count)
        ring_block = cols % BLOCKS_PER_ALLOC
        val = tl.where(in_range, base + ring_block, 0)
        tl.store(block_table_ptr + row * stride_bt + cols, val, mask=mask)
```

环分配元数据（patch_private_circle_pool.py:300-348 区域，事件 351 读取）：每请求按 `request.private_circle_allocation = allocation` 绑定分配句柄，metadata 记录 `blocks_per_allocation`、`in_flight_tokens` 等布局；allocation 随请求生命周期回收复用（审查判断：无清零动作，此点为代码审查结论，未做运行时观测）。

## 探针与操作

本卡的诊断规则按以下顺序执行（均为审查会话中实际执行过的只读探针或提出的验证实验；**注意：验证实验为研究结论，未执行**）：

1. 【已执行】部署版本考古：`git show c60545866`、`git show 72521a79c`（来源记录 事件 85/88）——核对两个"直接造成接受率衰减形状"的修复是否在产线二进制内。
2. 【已执行】消费者考古：`grep -n "\.causal" vllm_ascend/attention/dsa_v41.py`（事件 458/459，输出为空）；`grep -rn "get_draft_attn_causal" vllm_ascend/ --include=*.py`（事件 454/455，命中仅 kimi_k3_dspark.py 与 dspark_proposer.py）；`grep -n "VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL" vllm_ascend/`（主控会话事件 90/91，15+ 消费点）。
3. 【未执行，审查建议】确认产线二进制包含 `c60545866`、`72521a79c`、`f13966829`、`51d65bc82`、`650f8578b`。
4. 【未执行，审查建议】单请求、输出 ≥2000 token、无并发压测：若接受率稳定 → 排除版本缺失/因果窗口类，指向环残留（churn 依赖）。
5. 【未执行，审查建议】相同压测、显式 `VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL=0`（若内存允许）对照：若衰减消失 → 锁定环残留机制。
6. 【未执行，审查建议】打开 `[spec/dfx] rejection_sampler done` DEBUG 日志按请求年龄段分桶统计接受率，区分"新请求差、老请求好"（环残留）与"所有请求随步数变差"（版本缺失/因果窗口/漂移类）。注意：该日志探针的存在性（rejection_sampler.py:300-331）为审查报告引用，本轨迹未读取该文件核实。

## 机制与判别

### 机制一（候选根因 #1，需先核实）：部署二进制缺两个 9 月下旬修复

> 部署版本优先核查：c60545866（draft 纯 SWA 层误继承 YaRN 插值 RoPE，commit 记录实测 pos0 76% 衰减到 pos4 25%）与 72521a79c（indexer topk 过滤 prepare_indexer_indices 被注释，长上下文下 target 稀疏注意力读到未按位置过滤的错误块）均于 2026-09-21~23 才合入；若压测二进制早于这两个修复，接受率随请求内长度衰减与输出劣化的形状与生产现象直接吻合——排查第一步是核对部署二进制版本。

c60545866 提交信息原文（事件 85，节选）：

```
    The draft attention inherits the V4 constructor, which leaves
    original_seq_len at its default (max_position_embeddings) and therefore
    enables YaRN interpolation whenever factor != 1. The v41 target's pure
    SWA layers explicitly disable YaRN (original_seq_len=0, base rope
    theta), and the draft's pure-SWA layers were trained on the same
    unscaled frequencies — so the inherited YaRN table mismatches the
    draft's training-time positional encoding and degrades acceptance
    (observed pos0 76% decaying to pos4 25% in eager mode).
```

修复 diff（vllm_ascend/models/deepseek_v41/dspark.py）：

```python
+        config = kwargs["config"]
+        self.rotary_emb = ComplexExpRotaryEmbedding(
+            vllm_config=kwargs["vllm_config"],
+            layername=f"{kwargs['prefix']}.attn",
+            head_size=self.rope_head_dim,
+            rotary_dim=self.rope_head_dim,
+            max_position_embeddings=kwargs["max_position_embeddings"],
+            is_neox_style=False,
+            scaling_factor=config.rope_parameters["factor"],
+            base=config.rope_theta,
+            beta_fast=config.rope_parameters["beta_fast"],
+            beta_slow=config.rope_parameters["beta_slow"],
+            original_seq_len=0,
+            rope_groups=["default"],
+        )
```

72521a79c 修复 diff（vllm_ascend/models/deepseek_v41/indexer.py）——恢复被注释掉的按位置过滤：

```python
-        # selected = prepare_indexer_indices(selected.squeeze(1), positions, self.compress_ratio)
-        return selected.view(-1, topk), candidate_indices, candidate_lengths
+        selected = prepare_indexer_indices(selected.squeeze(1), positions, self.compress_ratio)
+        return selected, candidate_indices, candidate_lengths
```

判别：这两个 bug 的症状形状与生产现象高度一致（72521a79c 尤其随上下文增长恶化，压测请求普遍逼近 150K）；若二进制已含两者，则该机制排除。

### 机制二（候选根因 #2，中高置信）：draft 私有环跨请求残留 + PD 冷窗口

机制链（审查级推理）：
1. draft 的 SWA 缓存只从请求到达 decode 实例后开始积累（每步写 K+1 个 context KV + K 个 query KV）；prompt 部分的 draft KV 在 PD 部署下永远不存在（prefill 侧不运行 drafter，Mooncake 只传 target 各层 KV）——此为审查对 PD 架构的推断，轨迹内未直接验证。
2. 私有环按 allocation 回收复用且不清零：新请求窗口 `[p-window+1, p]` 中尚未被本请求覆写的环槽，内容是上一个请求的残留 KV——"真实但无关"的 KV 比全零更能让注意力错误聚焦（审查推断）。
3. 压测中请求持续 churn、并发逐渐打满（max-num-seqs 16）时，处于"污染热身期"的请求占比随负载升高而上升 → 平均接受率随时间下降；接受率 → 0 后单步吞吐坍塌 → 客户端超时/取消 → 回答截断。

> 激活边界：私有环机制仅在 VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL=1 时生效；审查发现 envs.py 中该 key 在同一 dict 字面量中出现两次（默认值分别为 "1" 和 "0"），按 Python 语义后者生效、实际默认为 0，且审查所给线上 serve 配置未显式设置该变量——排查该机制前必须先确认部署环境的实际生效值。

envs.py:78-80 逐字（主控会话 来源记录 事件 87 读取）：

```python
    "VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL": lambda: bool(int(os.getenv("VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL", "1"))),
    "VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL": lambda: bool(
        int(os.getenv("VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL", "0"))
```

该开关的消费点（事件 91 grep 结果，节选）：`vllm_ascend/core/deepseek_v41.py:147`（`if not envs.VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL: return False`，SWA diversion 分派）、`patch_kv_cache_utils.py:417/616`、`patch_private_circle_pool.py:87/142/656`、`mooncake_hybrid_connector.py:1451/1986`、`worker/block_table.py:60`、`worker/model_runner_v1.py:340` 等 15+ 处。

判别：上游 DFlash/DSpark 同样按步写 context（"热身期"是设计固有），但 PD + 私有环 + churn 会显著放大其占比——"单请求超长输出 vs 高频短请求"对照可直接隔离。

### 机制三（候选根因 #3，中置信）：V4.1 draft 因果窗口语义偏差

> V4.1 dspark draft 因果窗口语义偏差：dspark_proposer.py 对 deepseek_v41（未实现 get_draft_attn_causal）恒设 cad.causal=False，但 dsa_v41.py 中 causal 字段无任何消费者（grep 无输出），_get_window_topk_idxs 恒按 [p-window+1, p] 构造因果窗口；对照 V4 路径 dsa_v1.py 的 build_dspark_swa_indices 以 visible_lens = seq_lens - start_pos 让每个 draft query 可见整个 draft 块。因果化使 anchor 位看不到块内后续 draft token 的 KV，每步静态拉低接受率（尤其 pos0）。

V4.1 路径（dsa_v41.py:1187-1196，来源记录 事件 250；主控会话事件 73 独立复读同段一致）：

```python
        if positions is not None:
            positions = positions.to(torch.int32)
            cols = torch.arange(window_size, device=device, dtype=torch.int32)
            valid_len = torch.clamp(positions + 1, max=window_size)
            window_start = positions - valid_len + 1
            win_indices = window_start.unsqueeze(1) + cols.unsqueeze(0)
            valid_mask = cols.unsqueeze(0) < valid_len.unsqueeze(1)
            return torch.where(
                valid_mask, win_indices, torch.full_like(win_indices, -1)
            ).unsqueeze(1)
```

V4 对照路径（dsa_v1.py:347-383，事件 140）——文档字符串与整块可见窗口：

```python
    """Build DSpark non-causal visible slot ids for a paged SWA cache.

    Each token in a draft block sees the trailing context window plus the
    whole current draft block. Invalid/padded rows get lens=0 and -1 slots.
```

```python
    query_lens = query_start_loc[1:] - query_start_loc[:-1]
    prefix_lens = seq_lens - query_lens
    start_pos = (prefix_lens - int(window_size)).clamp(min=0)
    visible_lens = seq_lens - start_pos
```

客观探针（事件 454-459）：
- `grep -rn "get_draft_attn_causal" vllm_ascend/ --include=*.py` → 仅命中 `vllm_ascend/models/kimi_k3_dspark.py:276`（定义）与 `vllm_ascend/spec_decode/dspark_proposer.py:390/392/526/527`（消费）；deepseek_v41 模型目录无定义。
- `grep -n "\.causal" vllm_ascend/attention/dsa_v41.py` → **无输出**（事件 459）；主控会话独立核实：causal 字段只在 dsa_v41.py:418（定义）与 2331（`causal=getattr(common, "causal", True)` 透传）出现，窗口构造逻辑恒为因果窗口，"draft 非因果语义确实未生效，该发现成立"。

判别：该机制与机制一/二叠加后把热身期接受率直接打到近 0，也是 c60545866 修复后 pos0 仍可能偏低的原因；其作用不随时间变化（每步静态），因此"衰减到 0"的动态形状主要由机制一/二贡献。

### 未验证推断与混杂

- "私有环分配回收不清零"与"prompt 部分 draft KV 在 PD 下不存在"均为审查推断，未运行时观测。
- 长稳衰减还可能有边缘贡献因子（审查排序 #4/#5）：pre-replay sync 移除后 proposer 裸写 pinned buffer 的时序窗口（当前 qsl 内容恒为 arange*K 侥幸良性）、块表 F.pad 地址不稳定（见 [ACL graph 捕获地址固化纪律：draft 图捕获必须绑定每步刷新的持久 buffer，临时张量致回放读垃圾、接受率坍塌到 ~1/B](../compilation/acl_graph_draft_buffer.md)）——负载越高触发概率越大，可解释"中后期开始劣化"。
- 修 P1-1 建议之一：请求首次进入 decode 时用 target hidden states 一次性回填 draft 环的整个窗口，或在 ring 分配回收时清零 + 对窗口未覆盖位置做 -1 屏蔽（未实施）。

## 验证信号

本卡全部信号为**代码读取/git 考古类工具结果**（客观事件），无任何运行时指标。逐条（平台：vllm-ascend 仓库 ${LOCAL_PATH_2}，分支 releases/v0.27.1rc@6746201ec；对照上游 ${LOCAL_PATH_3}）：

| 结论 | 信号（事件） | 证据等级 |
|---|---|---|
| 每步只写本步 verify tokens 的 draft 上下文 | 来源记录:8（dspark_proposer.py 全文读取，304-305 行） | 代码事实 |
| 环表按 allocation+取模相对寻址 | 来源记录:344（private_circle_ring_table.py 全文） | 代码事实 |
| 环分配绑定请求生命周期 | 来源记录:351（patch_private_circle_pool.py 300-360 段） | 代码事实；"不清零"为审查判断 |
| causal 字段在 dsa_v41 无消费者 | 来源记录:459（grep 无输出）；:455（get_draft_attn_causal 仅 kimi_k3）；主控复核 来源记录:72/73/75 | 代码事实（双会话独立确认） |
| V4.1 恒因果窗口 vs V4 整块可见 | 来源记录:250（dsa_v41.py:1187-1196）与 :140（dsa_v1.py:347-400 对照读取） | 代码事实 |
| YaRN 修复的实测衰减 76%→25% | 来源记录:85（c60545866 提交信息，历史记录非本轨迹实测） | 提交记录 |
| indexer topk 过滤被注释/恢复 | 来源记录:88（72521a79c diff） | 代码事实 |
| 私有环池默认 0（重复 key 后者生效） | 来源记录:87（envs.py:78-80）与 :91（消费点 grep） | 代码事实 + Python dict 字面量语义 |
| async 侧采样记账结构 | 来源记录:443（model_runner_v1.py:3315-3459 _bookkeeping_sync 读取；中段在转储中被截断） | 代码事实（部分段落） |

单次/条件说明：无性能对比数据（performance_comparison 为空）；"接受率衰减到 0、回答截断"本身是用户报告的生产症状，不构成客观信号；所有"根因排序"均为审查推断，置信度标注见机制与判别一节。

## 适用与失效边界

- 适用：vllm-ascend DeepSeek-V4.1 适配（09220f435..6746201ec 一带）+ dspark 投机解码 + PD 分离（Mooncake）+ decode 侧双 ACL graph 的长稳压测接受率衰减排查。
- 失效边界：
  - 机制二（环残留）仅在 `VLLM_ASCEND_ENABLE_PRIVATE_CIRCLE_POOL=1` 实际生效时适用；envs.py 重复 key 使默认值为 0，若部署未显式开启则该机制不适用，现象归属需重新核对。
  - 机制一仅在压测二进制早于 c60545866/72521a79c 时成立；已含两修复的部署应把注意力移到机制二/三。
  - 机制三适用于 V4.1 draft builder（DeepseekV41MetadataBuilder）；V4/dsa_v1 路径（AscendDSAMetadataBuilder + build_dspark_swa_indices）语义正确，不适用。
  - 本卡结论未在 NPU 上运行验证；在接受率分桶实验给出"新请求差老请求好"或"所有请求随步数变差"的证据前，根因排序应视为待验证假设。
  - 若后续版本已重构 dspark_proposer/dsa_v41 的窗口构造或私有环分配（如 wzc 分支 `win_*`→`ori_*` ABI 改名），行号与机制需按新代码重新核对。
- 停止/回退条件：探针 1（版本核对）命中缺失修复 → cherry-pick 后重测即可结案；探针 4/5 显示衰减与 churn/私有环无关 → 放弃机制二，转向漂移类因子（候选 [ACL graph 捕获地址固化纪律：draft 图捕获必须绑定每步刷新的持久 buffer，临时张量致回放读垃圾、接受率坍塌到 ~1/B](../compilation/acl_graph_draft_buffer.md) 的地址固化/同步类）。
