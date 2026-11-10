---
{
  "type": "Runbook",
  "title": "ACL graph 捕获地址固化纪律：draft 图捕获必须绑定每步刷新的持久 buffer，临时张量致回放读垃圾、接受率坍塌到 ~1/B",
  "description": "vllm-ascend ACL graph 捕获/回放的地址固化纪律：图回放不执行 Python、只读捕获时绑定的张量地址，任何进入被捕获图的 metadata（query_start_loc、块表等）必须绑定运行时每步刷新的持久 buffer。f13966829 提交记录了违反该纪律的实测后果——捕获期临时 qsl 被释放后回放读到分配器复用块的内容，多请求批接受率坍塌到 ~1/B；51d65bc82 的块表 zero-pad 只保证不越界，F.pad 新分配张量在 V4/dsa_v1 路径仍存在地址不稳定残留，V4.1 靠 builder 自有持久 buffer 每步 zero_+copy_ 才正确。诊断规则：出现多请求批接受率异常低/随负载抖动时，优先核查被图消费的 metadata 是否全部绑定持久 buffer。",
  "tags": [
    "task.debugging",
    "topic.compilation",
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

# ACL graph 捕获地址固化纪律：draft 图捕获必须绑定每步刷新的持久 buffer，临时张量致回放读垃圾、接受率坍塌到 ~1/B

## 适用场景

- 框架/版本：vllm-ascend（releases/v0.27.1rc@6746201ec），vllm_ascend/compilation/acl_graph.py 的 ACLGraphWrapper（capture/replay）、spec_decode proposer 体系；dspark（DeepSeek-V4.1）与 EAGLE 类 draft 图捕获。
- 平台：Huawei Ascend NPU，ACL graph（aclgraph capture/replay）FULL 模式。
- 触发面：decode 侧 draft 模型（或主模型）以 ACL graph 运行、且图中 FA/DSA 类算子直接消费 common_attn_metadata 中的张量（query_start_loc、块表等）的任何配置；多请求批、DP padding、图桶 padding 会放大。
- 信息缺口声明：本卡来自只读代码审查（含 git 考古），"接受率坍塌到 ~1/B"为 f13966829 提交信息记录的历史实测，非本轨迹内复现。

## 触发与观测

审查任务触发（来源记录 事件 2）：dspark + 双 ACL graph 长稳压测接受率衰减排查，任务列出 `git log -p` 关键提交清单（含 f13966829、51d65bc82、acd9bca0a、b7ad27847）。

审查中执行的核心探针：`git show f13966829 && git show 51d65bc82`（事件 73/74）、`git show 650f8578b && git show acd9bca0a && git show b7ad27847`（事件 76/77）、builder 持久 buffer 对照读取（事件 268）。

核心机制结论（审查级）：

> ACL graph 捕获时固化张量地址：图回放不执行 Python，只读捕获时绑定的地址；任何进入被捕获图的 metadata 必须绑定运行时每步刷新的持久 buffer。捕获期把临时张量（如 arange 构造的 query_start_loc）交给图，dummy_run 返回后临时张量即被释放，回放读到的是分配器把该内存块复用给后续张量的任意内容。

> f13966829 提交信息记录了该地址错绑的实测后果：多请求批下垃圾 cu_seqlens_q 把 query 行错分到其他请求、注意力读到别的请求的 KV，接受率坍塌到 ~1/B（单请求批侥幸存活）；修复是把 dummy 布局写入运行时回放前刷新的同一持久 buffer（query_start_loc_group[0]/seq_lens_group[0]）并把其视图绑定进 capture cad。

## 探针与操作

f13966829 提交信息逐字（事件 74，git show 输出）：

```
    The FA ops receive common_attn_metadata.query_start_loc directly
    (metadata.swa.query_start_loc), bypassing the builder's persistent
    buffers. _build_capture_metadata handed the graph a freshly allocated
    temp (arange * K); the temp was freed when dummy_run returned, so every
    replay read whatever tensor later reused that allocator block. With
    multi-request batches the garbage cu_seqlens_q mis-segmented the query
    rows across requests and attention read the wrong request's KV,
    collapsing acceptance to ~1/B (single-request batches survived).

    Write the dummy layout into the same persistent buffers the runtime
    path refreshes before every replay (query_start_loc_group[0],
    seq_lens_group[0]) and bind those views in the capture cad, so the
    graph bakes the replay-refreshed addresses.
```

修复 diff 逐字（dspark_proposer.py `_build_capture_metadata`）：

```python
+        qsl = self.arange_dflash[: num_reqs + 1] * num_query_per_req
+        qsl_cpu = torch.from_numpy(self.token_arange_np[: num_reqs + 1]).clone() * num_query_per_req
+        self.query_start_loc.gpu[: num_reqs + 1].copy_(qsl)
+        self.query_start_loc.cpu[: num_reqs + 1].copy_(qsl_cpu)
+        self.query_start_loc_group[0][: num_reqs + 1].copy_(qsl)
+        self.seq_lens_group[0][:num_reqs].copy_(self.runner.seq_lens[:num_reqs])
```

（对照：修复前 capture cad 直接接收 `query_start_loc=self.arange_dflash[: num_reqs + 1] * num_query_per_req` 这一临时张量。）

pre-replay sync 侧的相关开关（b7ad27847 中 ACLGraphWrapper.replay 的修改，事件 77 读取）：

```python
        need_sync = (
            self.runtime_mode == CUDAGraphMode.FULL
            and not is_draft_eagle
            and not self.skip_pre_replay_sync
        )
        if not self.enable_enpu and need_sync:
            torch.npu.current_stream().synchronize()
        entry.aclgraph.replay()
```

审查判断：被删的 pre-replay `synchronize()` 原是 host 不跑到 device 前面的最后一道隐式屏障；V4.1（use_compress 恒真）以 `skip_pre_replay_sync` 跳过它依赖"回放消费的 metadata 全部在每步刷新的稳定 buffer 中"这一前提——该前提正是本卡的纪律要求。

## 机制与判别

> 同类残留：块表 padding 用 F.pad 新分配张量（51d65bc82 后 padding 行指向空块 0 只保证不越界），V4/dsa_v1 路径新表视图被图固化地址后仍读陈旧行；V4.1 靠 DeepseekV41MetadataBuilder 自有持久 buffer 每步 zero_()+copy_() 刷新才正确——不越界不等于地址稳定，禁止 F.pad 临时张量进入任何被图消费的 metadata。

51d65bc82 的块表 zero-pad 修复（事件 74 diff 逐字，llm_base_proposer.py）：

```python
+                    common_attn_metadata.block_table_tensor = self._adjust_tensor(
                        block_table, common_attn_metadata.num_reqs
                    )
```

V4.1 正确姿势的对照（dsa_v41.py:1873-1892，事件 268 逐字）——builder 自有持久 buffer，地址跨步稳定：

```python
        # Keep a complete request-dimension table at a stable address. A
        # mixed full-graph batch can contain one synthetic padding request
        # whose row is not present in the runner-owned table.
        source_block_table = common.block_table_tensor
        if self._block_table is None or self._block_table.shape[1] != source_block_table.shape[1]:
            self._block_table = torch.zeros(
                (self._seq_lens.shape[0] + 1, source_block_table.shape[1]),
                dtype=source_block_table.dtype,
                device=source_block_table.device,
            )
        if num_reqs > self._block_table.shape[0]:
            raise ValueError(
                "V4.1 block-table buffer is smaller than the padded request count: "
                f"{num_reqs} > {self._block_table.shape[0]}"
            )
        self._block_table[:num_reqs].zero_()
        rows_to_copy = min(num_reqs, source_block_table.shape[0])
        if rows_to_copy:
            self._block_table[:rows_to_copy].copy_(source_block_table[:rows_to_copy])
        block_table = self._block_table[:num_reqs]
```

判别分支（可区分的解释）：

| 观测形状 | 地址错绑（临时张量进图） | 元数据内容漂移（非地址问题） |
|---|---|---|
| 单请求批 | 侥幸存活（错分不存在） | 与批形状无关 |
| 多请求批接受率 | 坍塌到 ~1/B 量级 | 渐进劣化或抖动 |
| 复现确定性 | 取决于分配器复用（负载相关、偶发~稳定） | 步进/状态相关 |

与"长稳衰减"的关系（审查排序）：本类缺陷在审查报告中列为边缘贡献因子（原审查报告列出的两项边缘贡献因子）——当前 qsl 内容恒为 arange*K（覆写值与待传值逐字节相同）使其大部分时间良性，属"现在没炸但随时会炸"的结构性隐患；但任何未来向该 buffer 加入内容非确定的字段立即变成活性 bug。

未验证推断：V4/dsa_v1 路径（dsa_v1.py:1145 直接切片新表视图进 req_metadata）的"读陈旧行"后果未被运行时复现；当前靠 padding 行 seq_lens=0 使 FA 不读 KV 才无害。

## 验证信号

全部信号为代码读取 / git 考古类工具结果（客观事件），无运行时指标：

| 结论 | 信号（事件） | 证据等级 |
|---|---|---|
| 地址错绑机制与 ~1/B 后果 | 来源记录:74（f13966829 提交信息 + diff 全文） | 提交记录（历史实测描述）+ 代码事实 |
| 修复绑定持久 buffer | 来源记录:74（修复 diff） | 代码事实 |
| pre-replay sync 门控结构 | 来源记录:77（b7ad27847 diff：need_sync 三条件 + torch.npu.current_stream().synchronize() + entry.aclgraph.replay()） | 代码事实 |
| 块表 zero-pad 修复 | 来源记录:74（51d65bc82 diff） | 代码事实 |
| V4.1 持久 buffer 正确姿势 | 来源记录:268（dsa_v41.py:1873-1892 读取） | 代码事实 |

单次/条件说明：`~1/B` 的量化后果来自提交信息的历史记录（单次观测级，无本轨迹复现）；performance_comparison 为空（无可比基线指标）。

## 适用与失效边界

- 适用：所有 vllm-ascend ACL graph（FULL 模式）捕获的 draft/主模型前向中，被捕获算子按数据指针消费的 metadata 张量（qsl、seq_lens、块表、slot_mapping、indices buffer 等）；dspark、EAGLE、以及未来任何 spec-decode 方法接入图捕获时同样适用。
- 失效边界：
  - 该纪律针对"图内按地址读取"的张量；每步由 Python 重建、不进图的张量不受约束。
  - V4.1 dspark 当前 qsl 内容确定性（arange*K）使 pre-replay sync 移除后仍良性——这是内容巧合而非结构保证。
  - EAGLE 多步循环路径（llm_base_proposer.py:1533-1681）的地址纪律本轨迹未深查。
  - 图捕获模式为 NONE（纯 eager）时本卡不适用。
- 停止/回退条件：给 proposer 的 pinned 写套用 runner 的 `synchronize_input_prep` 事件协议或复用 runner buffer 即闭合（审查建议，未实施）；审查另指出 `_pad_query_start_loc_for_fia` 非 dspark 路径同样裸写 pinned buffer，属于同一修复面。
