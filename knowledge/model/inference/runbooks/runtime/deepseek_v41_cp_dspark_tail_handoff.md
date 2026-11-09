---
type: Runbook
title: recipes专用：CP到DSpark的请求尾窗交接
description: recipes CANN Executor参考实现专用：仅在所列CP分段、DSpark worker与配置guard下，按请求交接token/hidden尾窗和完整提示词绝对位置。
tags:
- task.debugging
- topic.parallelism
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：CP 到 DSpark 的请求尾窗
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：CP到DSpark的请求尾窗交接

## 适用性与框架边界

本卡是 **recipes CANN Executor 参考实现专用配方**，只覆盖所列 CP Zigzag 分段、DSpark worker 桥接和配置 guard。它不是 vLLM 原生投机解码方案，也没有已核验的参数或 helper 等价映射。

可供其他引擎借鉴的检查原则只有：hidden、token、position 必须按同一请求与逻辑顺序交接，物理补齐行不能冒充有效上下文。下文固定 W 行、reverse_index、全局 batch 与 EP 参与、proposal kv_len、短首段保留整窗再截前缀，均依赖该 recipes 方案。

vLLM 或其他引擎应按自身 **ModelRunner/模型辅助输出、草稿输入适配、metadata builder 与请求状态**职责核对行对应关系；Scheduler 的请求/token 选择不定义这里的尾窗 ABI。除非采用同一 CANN Executor 参考实现，否则不能直接执行下文桥接步骤。

## 现象

在本文 CANN Executor 参考实现中，主模型把长提示词分到多卡处理后，要用它的 hidden（隐藏特征）初始化草稿模型缓存；若只交出本卡局部行，草稿的 token、hidden 和位置可能不再一一对应。此时应检查跨卡重排与逐请求取尾，而不是只查看最终 Tensor 总行数。

本卡中 CP 是上下文并行，每个 rank（通信进程）持有 Zigzag（前后段配对的交错划分）的两段提示词。DSpark 是先提出候选 token、再由主模型验证的草稿模型；它使用主模型的 auxiliary_hidden_states（辅助隐藏特征）建立提示词末尾的滑窗缓存。EP 是专家并行，草稿的专家计算需要对应通信域内 rank 共同参与，因此不能只让请求 owner（结果归属进程）执行 proposal（草稿提议计算）。

## 适用场景

仅适用于 recipes CANN Executor 参考实现的 DeepSeek V4.1 主模型 Prefill（整段提示词处理）到 DSpark 后续 Decode（逐步生成）的尾窗交接。入口链为主模型 `gather_cp_tail_hidden` → worker 的 proposal 输入构造。当前配置要求 cp_size==world_size、attn_tp_size==1、cp_mini_batch>0；TP 指张量并行。适用粒度 `exact_task`，路线优先级 `recommended_fastpath` 表示遵守当前源码契约。源码目标 950，本轮无 NPU 推理、编译或容器执行，CANN 运行版本未确认；只有后文列明的隔离 CPU 行选择观测。

本卡不展开 Attention 内部 CP 算法。proposal 算完后的请求状态行选择另见 [Prefill CP 下 DSpark 草稿状态行序](dspark_prefill_cp_state_rows.md)。其他框架只能借鉴请求/位置一致性检查；自身段顺序、有效长度与 owner 规则未匹配时，不能套 helper 或把本配方作为其迁移步骤。

## 判别方法

worker 最后把有效行恢复为每请求独立、长度补齐的 dense 张量。先把“通信中的补齐行”“某请求真实 token 行”和“草稿逻辑位置”分开。主模型先取每个本地段、每个请求的最后 W 行，补到固定 W；AllGather（全收集）得到 rank 顺序，再由 reverse_index 恢复上下文的段顺序，最后按请求拼出真正末窗。

| 量 | 轴、单位与生产消费关系 |
|---|---|
| P、B、W、Haux | CP rank 数、全局请求数、草稿所需尾窗 token 数、辅助特征通道数 |
| 本地 tails | 每 rank 两段、每段 B 请求、每请求 W 行；发送展平为 `[2×B×W,Haux]` |
| `all_rows [2P,B,W,Haux]` | 按上下文顺序恢复的全部段尾窗；gather/reverse_index 生产，tail helper 消费 |
| `segment_lens` / `cur_kv_len` | 每段的打包占位长度 / 请求在该段的真实长度；前者推进输入offset，后者限定可取有效行 |
| `last_segment_idx` / `last_kv_len` | 每请求最后非空段的位置及其中真实行数 k；调度元数据 → 逐请求取尾 |
| 原始 L / tail_len | 每请求完整提示词长度 / `min(L,W)`；worker 据此取 token 和 hidden 的有效行 |
| position tails / proposal kv_len | 绝对位置 `L-tail_len…L-1` / CP Prefill 的 `L-1`；短窗口不把完整提示词坐标重置为0 |

**教学推演，非分布式观测。** W=4，请求 A 长6，最后一段有2行；前段末窗为 `[a0,a1,a2,a3]`，当前段为 `[a4,a5,补齐,补齐]`。helper 从前段取最后2行再接当前2行，得到 `[a2,a3,a4,a5]`；worker 也从原 prompt 取相同 token 尾，绝对位置为2、3、4、5，proposal kv_len 为5。若误把当前段四行全交草稿，补齐会取代 a2/a3；若把尾窗位置重置为0，也会错配位置编码。

同一例中再放一个长度2、last_segment=0 的短请求 B。helper **原样返回 W 行** `[b0,b1,补齐,补齐]`，不会主动裁成2行；worker 再按 tail_len=2 只取有效前缀。这个分工很重要：短首段 helper 返回 W 行不等于所有行都是真实上下文。跨前段拼接也只补一个前段，要求该前段有足够有效尾行。

## 快速检查

1. 在该 recipes 参考实现中核对主模型辅助特征导出、CP 段收集器与 DSpark 输入打包器，用请求ID和绝对位置标记行的来源。预期 hidden、token、position 三条链最后覆盖同一请求的同一尾窗；只对总 shape 会漏掉段重排错误。
2. 在通信前记录本地 prev/next、每请求占位段长与真实长度；在通信后检查 rank 顺序如何恢复成上下文段顺序。预期发送块同尺寸、reverse_index 与实际调度相符，padding 没被当作有效 hidden。顺序不符先查段映射，不能用 tail_len 截断掩盖。
3. 分别检查完整末段、短末段和短首段。短末段按上例与前一段拼接；短首段先保留 W，再由 worker 截有效前缀。若前一段不足所需尾行，该 helper 不能保证正确，应停止套用并重审调度前提。
4. 在草稿入口同时查看 token tails、hidden tails、position tails 与 dense padding：每请求有效长度为 min(L,W)，有效位置保持绝对坐标，位置补齐值为-1。hidden 来自主模型已重建的 request×W 区间，token 则来自全局原 prompt，二者不能分别按本 rank 局部数据取尾。
5. 检查 proposal 是否覆盖全局 B 个请求及需要参与 EP 的 rank。CP Prefill 的逻辑 kv_len 应取完整 batch.seq_lens−1；owner 已收窄的 forward metadata 不能替代全局长度。行对齐成立后再做真实跨 rank、空 owner 和多请求验收，CPU helper 检查不能排除通信/专家参与问题。

可选的 recipes 源码导航命令如下，仅供使用该参考工程时定位；其他引擎按前述职责检查自己的组件：

```bash
rg -n 'gather_cp_segments' models/deepseek_v4_1/models/modules/common_modules.py
```


## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes CANN Executor 专用：完整 CP 收集与 DSpark worker 桥接</summary>

以下是源文件中的完整函数或完整因果块，未改写为示意代码。它们依赖原工程上下文；不是可脱离工程直接运行的独立程序。

gather_cp_segments（`models/deepseek_v4_1/models/modules/common_modules.py`）：

段收集器输入是本 rank 已补齐的二维行，AllGather 按 rank 合并，再用 reverse_index 换成段顺序。输出仍为二维展平行；请求和窗口轴由后面的调用者恢复。

```python
def gather_cp_segments(local_rows: torch.Tensor, cp_metadata: dict, cp_group) -> torch.Tensor:
    """Gather both zigzag segments from every rank and restore the sequence order.

    Every rank sends two segments padded to the same length, so the gathered buffer is
    ordered by rank and reverse_index maps it back to segment order.
    """
    row_dim = local_rows.shape[-1]
    cp_size = dist.get_world_size(cp_group)
    gathered = local_rows.new_empty([local_rows.shape[0] * cp_size, row_dim])
    dist.all_gather_into_tensor(gathered, local_rows, group=cp_group)
    gathered = gathered.view(-1, local_rows.shape[0] // 2, row_dim)[cp_metadata["reverse_index"]]
    return gathered.flatten(0, 1)
```

pick_request_tail（`models/deepseek_v4_1/models/modules/common_modules.py`）：

tail helper 输入已经按 `[段,请求,W,通道]` 排好。完整末段或第0段直接返回整窗；只有短的非首末段才拼前段尾与当前有效前缀。它不验证前段有效性，也不裁短首段。

```python
def pick_request_tail(all_rows: torch.Tensor, cp_metadata: dict, request: int, window: int) -> torch.Tensor:
    """Last window of one request, joined with the previous segment when its last segment is partial.

    all_rows holds one window per segment per request, shaped [segment, request, window, dim].
    """
    last_segment = cp_metadata["last_segment_idx"][request]
    last_kv_len = cp_metadata["last_kv_len"][request]
    if last_kv_len >= window or last_segment == 0:
        return all_rows[last_segment, request]
    return torch.cat([
        all_rows[last_segment - 1, request][last_kv_len - window:],
        all_rows[last_segment, request][:last_kv_len],
    ], dim=0)
```

DeepseekV41ForCausalLM.gather_cp_tail_hidden（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

主模型按占位 segment_len 推进 offset，但只从 cur_kv_len 真实行取尾，之后补到 W；收集并恢复轴后逐请求调用 helper，最终每请求占 W 行交给 worker。

```python
    def gather_cp_tail_hidden(self, hidden_states, attn_metadata):
        """Collect the last sliding window of every request, which the draft model seeds its cache with."""
        cp_metadata = attn_metadata["cp_metadata"]
        window, row_dim = self.cp_prefill_tail_tokens, hidden_states.shape[-1]
        segment_lens = cp_metadata["segment_lens"]
        tails, offset = [], 0
        for zigzag_flag in ("prev", "next"):
            for segment_len, cur_kv_len in zip(segment_lens, attn_metadata[zigzag_flag]["cur_kv_len"]):
                rows = hidden_states[offset:offset + cur_kv_len][-window:]
                tails.append(F.pad(rows, (0, 0, 0, window - rows.shape[0])))
                offset += segment_len
        all_tails = gather_cp_segments(
            torch.cat(tails, dim=0), cp_metadata, self.comm_manager.get_group("cp_group"))
        all_tails = all_tails.view(-1, len(segment_lens), window, row_dim)

        picked = [
            pick_request_tail(all_tails, cp_metadata, request, window)
            for request in range(len(segment_lens))
        ]
        return torch.cat(picked, dim=0)
```

DSparkWorker._build_prefill_proposal_tails（`executor/core/model_worker/dspark_worker.py`）：

worker 从全局原 prompt 取相同 token 尾和绝对位置，同时从 request×W 的辅助态区间取有效前缀，再分别恢复 dense 请求行。这个方法把主模型的固定尾窗转换成草稿的有效输入长度。

```python
    def _build_prefill_proposal_tails(
        self,
        input_ids: torch.Tensor,
        seq_lens: torch.Tensor,
        target_hidden_states: torch.Tensor,
    ):
        """Assemble the proposal inputs from the per-request tail window handed over by prefill CP."""
        window = self.main_model.cp_prefill_tail_tokens
        tail_lens = seq_lens.clamp(max=window)
        input_ids = input_ids.view(-1)
        id_tails, position_tails, start = [], [], 0
        for seq_len, tail_len in zip(seq_lens.tolist(), tail_lens.tolist()):
            id_tails.append(input_ids[start + seq_len - tail_len:start + seq_len])
            position_tails.append(torch.arange(
                seq_len - tail_len, seq_len, device=self.device, dtype=torch.long))
            start += seq_len
        target_hidden_states = torch.cat([
            target_hidden_states[request * window:request * window + tail_len]
            for request, tail_len in enumerate(tail_lens.tolist())
        ], dim=0)
        return (
            self._pack_prefill_to_dense(torch.cat(id_tails, dim=0), tail_lens),
            self._pack_prefill_to_dense(target_hidden_states, tail_lens),
            self._pack_prefill_to_dense(torch.cat(position_tails, dim=0), tail_lens, pad_value=-1),
        )
```

DSparkWorker._build_prefill_proposal_inputs（`executor/core/model_worker/dspark_worker.py`）：

proposal 输入入口用 CP metadata 判断是否走尾窗；普通非 CP 路径则恢复完整 prompt。两条路径的输入内容不同，不能把 CP 输出视为完整提示词 hidden。

```python
    def _build_prefill_proposal_inputs(
        self,
        batch: Batch,
        input_ids: torch.Tensor,
        model_inputs_main: Dict,
        target_hidden_states: torch.Tensor,
    ):
        if batch.seq_lens is None:
            raise RuntimeError("seq_lens is required for draft prefill.")
        # Main prefill uses packed tokens. Restore batch rows and let the
        # proposal model populate its framework SlidingWindow KV entries.
        seq_lens = batch.seq_lens.to(device=self.device, dtype=torch.long)
        target_hidden_states = target_hidden_states.to(self.device).view(-1, target_hidden_states.shape[-1])
        cp_metadata = getattr(model_inputs_main.get("forward_metadata"), "cp_metadata", None)
        if cp_metadata is not None and cp_metadata.enabled:
            # Prefill CP splits the prompt across ranks, so the main model hands over only the
            # sliding window each request ends with. Everything else follows that tail.
            return self._build_prefill_proposal_tails(input_ids, seq_lens, target_hidden_states)
        total_tokens = int(seq_lens.sum().item())
        input_ids = input_ids.view(-1)[:total_tokens]
        position_ids = model_inputs_main["position_ids"].to(self.device).view(-1)[:total_tokens]
        proposal_input_ids = self._pack_prefill_to_dense(input_ids, seq_lens)
        target_hidden_states = self._pack_prefill_to_dense(target_hidden_states[:total_tokens], seq_lens)
        target_hidden_positions = self._pack_prefill_to_dense(position_ids, seq_lens, pad_value=-1)
        return proposal_input_ids, target_hidden_states, target_hidden_positions
```

DSparkWorker._pack_prefill_to_dense（`executor/core/model_worker/dspark_worker.py`）：

打包函数按累计有效长度从 packed 行恢复 `[batch,max_seq,...]`。它只按给定长度搬行，不会自动纠正 token、hidden 或 position 的错序。

```python
    @staticmethod
    def _pack_prefill_to_dense(tensor: torch.Tensor, seq_lens: torch.Tensor, pad_value: int = 0):
        """Restore packed prefill tensors to a dense [batch, seq, ...] context layout."""
        batch_size = seq_lens.numel()
        max_seq_len = int(seq_lens.max().item())
        dense = tensor.new_full((batch_size, max_seq_len, *tensor.shape[1:]), pad_value)
        start = 0
        for batch_idx, seq_len_tensor in enumerate(seq_lens):
            seq_len = int(seq_len_tensor.item())
            dense[batch_idx, :seq_len] = tensor[start:start + seq_len]
            start += seq_len
        return dense
```

DSparkWorker._get_proposal_kv_len（`executor/core/model_worker/dspark_worker.py`）：

逻辑长度函数在 CP Prefill 使用完整 batch 长度减1；后续 Decode 则由主模型验证位置与已接受前缀计算下一次起点。物理草稿缓存里已经写入的被拒绝 token 不能推进逻辑游标。

```python
    def _get_proposal_kv_len(
        self,
        batch: Batch,
        accepted_num: torch.Tensor,
        model_inputs_main: Dict,
    ) -> torch.Tensor:
        """Return the committed position that starts the next proposal.

        A proposal call materializes the complete draft block in its physical
        cache. Rejected draft tokens must not advance the logical cursor, so
        derive the next length from target verification positions and the
        accepted prefix instead of continuing from a draft-cache tail.
        """
        metadata_kv_len = get_forward_metadata().kv_len
        if batch.is_prefill:
            cp_metadata = getattr(model_inputs_main.get("forward_metadata"), "cp_metadata", None)
            if cp_metadata is not None and cp_metadata.enabled:
                # Forward metadata has been narrowed to the requests this rank owns, while the
                # draft prefills the whole batch.
                return batch.seq_lens.to(self.device) - 1
            return metadata_kv_len

        verify_positions = model_inputs_main["position_ids"].to(
            device=self.device,
            dtype=torch.long,
        ).reshape(-1, self.next_n + 1)[:accepted_num.shape[0]]
        accepted_num = accepted_num.to(device=self.device, dtype=torch.long).reshape(-1)
        committed_source_pos = verify_positions.gather(
            1,
            accepted_num.clamp(max=verify_positions.shape[1] - 1).view(-1, 1),
        ).squeeze(1)
        # The selected target logit predicts the next committed token. Convert
        # its zero-based source position to the cache length after that token.
        return committed_source_pos + 2
```

DeepseekV41ForCausalLM.forward CP auxiliary handoff causal block（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

主模型只有拿到 auxiliary_hidden_states 且处于 CP Prefill 时才收集尾窗，然后连同普通输出交接。应从这里追到 worker，不能在更早的局部 hidden 处直接截取。

```python
        auxiliary_hidden_states = None
        if isinstance(outputs, tuple):
            outputs, auxiliary_hidden_states = outputs
            if is_prefill and self.cp_size > 1:
                auxiliary_hidden_states = self.gather_cp_tail_hidden(auxiliary_hidden_states, attn_metadata)
        prev_hidden_states = outputs
        if auxiliary_hidden_states is not None:
            prev_hidden_states = {
                "prev_hidden_states": prev_hidden_states,
                "auxiliary_hidden_states": auxiliary_hidden_states,
            }
```

</details>

## 设计决策

只聚合 DSpark 所需的最后一窗辅助态，避免把所有层全部 prompt hidden 传给草稿；token 与绝对位置从同一原 prompt 取尾，缓存逻辑长度仍保留完整 prompt 的坐标。全局 batch 让 EP rank 共同参与；结果归属由外层调度处理。尾窗开销与 CP 补齐/短请求比例有关，本轮无性能实测。

## 系统信息

模型入口为 `models/deepseek_v4_1`，推理调度位于 `executor/core/model_worker`，通信由 CommManager 注册与解析。所有代码片段对应固定源码；内部版本、blob、行段和逐字摘要仅保存于本轮审计清单。

## 预防

用两请求且末段一个完整、一个不足 W 的 CP metadata 检查连续 token 顺序；核对 reverse_index、last_segment_idx、last_kv_len、token tails、hidden tails、position tails 一一对应。

## 验证信号

静态信号来自固定 Git 源码与真实差异，只证明实现、分支和映射的存在与逐字一致。以下静态信号不代表 NPU 运行、模型精度或性能通过。另有本地隔离 CPU 观测：隔离 CPU 检查覆盖 pick_request_tail 的跨前段拼接、完整末段及 last_segment=0 短请求保留 W 行；未验证分布式 gather 或 worker 端到端交接。（证据等级：tool_observed；执行平台：CPU，源码目标：950。）

- 静态逐字核对 `models/deepseek_v4_1/models/modules/common_modules.py` 的 `gather_cp_segments`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modules/common_modules.py` 的 `pick_request_tail`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `DeepseekV41ForCausalLM.gather_cp_tail_hidden`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `executor/core/model_worker/dspark_worker.py` 的 `DSparkWorker._build_prefill_proposal_tails`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `executor/core/model_worker/dspark_worker.py` 的 `DSparkWorker._build_prefill_proposal_inputs`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `executor/core/model_worker/dspark_worker.py` 的 `DSparkWorker._pack_prefill_to_dense`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `executor/core/model_worker/dspark_worker.py` 的 `DSparkWorker._get_proposal_kv_len`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `DeepseekV41ForCausalLM.forward CP auxiliary handoff causal block`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。

### 本轮 CPU 最小复现

先将本卡给出的相关完整函数及其依赖置于同一 Python 命名空间，再执行以下补充核对。它只验证配置或字节/行重排，不运行模型、不加载 checkpoint，也不验证 NPU 算子。

以下保留原有 CPU 探针：数值是合成行标签，用于辨认选择顺序，分别覆盖短末段拼接、完整末段和短首段返回 W 行。它不验证 gather 或 worker。

```python
import json
import torch

all_rows = torch.arange(24).reshape(3, 2, 4, 1)
observed = {}
for name, segment, length, expected in [
    ("partial", 2, 1, [13, 14, 15, 20]),
    ("full", 2, 4, [20, 21, 22, 23]),
    ("short_first_window", 0, 1, [4, 5, 6, 7]),
]:
    metadata = {"last_segment_idx": [0, segment], "last_kv_len": [0, length]}
    selected = pick_request_tail(all_rows, metadata, request=1, window=4)
    observed[name] = selected[:, 0].tolist()
    assert observed[name] == expected and selected.shape[0] == 4
print(json.dumps(observed))
```

本轮 CPU 实际输出：

以下是原 CPU 探针的实际输出，仅对应上面三种合成输入；不能据此推断分布式或模型数值正确。

```text
{"partial": [13, 14, 15, 20], "full": [20, 21, 22, 23], "short_first_window": [4, 5, 6, 7]}
```

## 失效边界

尾窗依赖 CP 元数据完整以及段长≥滑窗的调度前提。tail helper 的前段拼接仅补一个前段，不能套用到段长小于 W 的任意 CP 实现。CP+Attention TP 被配置校验拒绝。未验证空 owner、多请求不同长度与跨 rank EP 在硬件上是否正确。

本轮未执行 NPU 推理、真实 checkpoint 装载、跨 rank 通信或编译回放。隔离 CPU 检查仅在本卡验证信号明确列出的函数和输入范围内成立；其余部署验收仍待目标环境执行。

## 坏实践

把提交标题、源码注释或配置样例当成已经执行过的验证；用静态可达性替代精度、通信一致性或图回放检查。
