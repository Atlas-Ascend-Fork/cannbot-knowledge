---
{
  "type": "Runbook",
  "title": "RoPE 静态表冻结后 eager 路径 NPU 越界 gather 静默出错：`_prepared` 门控修复",
  "description": "为入图把动态 NTK-alpha RoPE 改为捕获前一次性建表后，eager 路径不再随 decode 位置增长 cos/sin 表；NPU 上越界 gather 不抛异常而是静默产生错误 token（CPU 上同探针报 IndexError），导致 golden 对齐在 step1 分歧。修复方式是 `_prepared` 门控：未 prepare 的 eager 路径按 `position_ids.max().item()+1` 增长表，prepare 后冻结只读；修复后 eager/图模式精度均恢复与 golden 完全一致。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "950"
  ]
}
---

# RoPE 静态表冻结后 eager 路径 NPU 越界 gather 静默出错：`_prepared` 门控修复

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（动态 NTK-alpha RoPE，`rope_scaling.type=dynamic`、`alpha=1000`，`HunYuanDynamicNTKAlphaRotaryEmbedding`），Paged KV + FA v2 TND 独立部署路径。
- 平台/版本：Ascend950PR_9589 单卡；CANN 9.1.0；torch 2.12.0+cpu / torch_npu 2.12.0。
- 目标与工作负载：为 npugraph_ex 入图把动态 RoPE 改为捕获前一次性建表；同一模型同时保留 eager 路径（CPU 黄金参考 + NPU eager 回退）。任何"图模式预建/冻结 RoPE 表 + eager 混跑"的 LLM 改造都适用。

## 触发与观测

- 触发：把 RoPE 重构成 `prepare_graph` 一次性预建 cos/sin 表并冻结（图内只读、无分支）后，eager 侧 golden 对齐脚本 `tools/compare_golden_npu.py` 返回 `token_match: false`、`first_divergence_step: 1`——decode 第一步即产生错误 token，而 NPU 侧无任何报错。
- 故障：RoPE 重构为捕获前一次性建表后，eager 路径不再随 decode 位置增长 cos/sin 表；NPU 上越界 gather 不抛异常而静默产生错误 token，eager golden 对齐在 step1 分歧（token_match=false，first_divergence_step=1）。
- 关键差异：CPU 上同一索引越界会抛 `IndexError`，NPU 上静默——因此该错误以"精度分歧"而非异常形式暴露。

## 探针与操作

判别探针（CPU 复现，直接驱动改造后的 `HunYuanDynamicNTKAlphaRotaryEmbedding`）：

```python
r = R(128, max_position_embeddings=32768, base=10000, scaling_alpha=1000.0)
x = torch.zeros(21, 4096)
pids = torch.arange(21)
c, s = r(x, position_ids=pids)     # prefill 后表长 21
pids2 = torch.tensor([21])         # decode 位置 21
c2, s2 = r(x, position_ids=pids2)  # 表长仍为 21 → 索引 21 越界
```

探针输出（原文）：

```
after prefill len 21 torch.Size([21, 128])
after decode len 21 torch.Size([21, 128])
INDEX ERR IndexError index 21 is out of bounds for dimension 0 with size 21
```

判别探针（CPU 复现）：prefill 后表长 21，decode 位置 21 时表长仍为 21，CPU 上报 `INDEX ERR IndexError index 21 is out of bounds for dimension 0 with size 21`；同一越界在 NPU 上无异常。

修复（`_prepared` 门控；`models/modeling_hunyuan.py` 最终态）：

```
228:     def prepare(self, seq_len, device, dtype):
229:         """Freeze the table for graph capture: build it and mark it complete."""
230:         self.build_cache(seq_len, device, dtype)
231:         self._prepared = True
232:
233:     def forward(self, x, position_ids=None):
234:         # Eager path (``_prepared`` False): grow the table as positions increase,
235:         # exactly like the original dynamic RoPE. This branch is never traced
236:         # inside the compiled Decode graph because ``prepare`` has frozen the
237:         # table and each compiled step only reads it.
238:         if not self._prepared:
239:             need = (int(position_ids.max().item()) + 1 if position_ids is not None
240:                     else self.max_position_embeddings)
241:             if (self.cos_cached is None or need > self.max_seq_len_cached
242:                     or self.cos_cached.device != x.device or self.cos_cached.dtype != x.dtype):
243:                 self._set_cos_sin_cache(need, x.device, x.dtype)
244:         return self.cos_cached, self.sin_cached
```

要点：`prepare` 后 `_prepared=True`，编译进图的 Decode 步只读表、无数据依赖分支；未 prepare 的 eager 路径保留按 `int(position_ids.max().item()) + 1` 增长表的原始动态语义（该 `.item()` 只存在于 eager 分支，不进图）。

失败路线（不可采用）：只保留"表不存在/设备/dtype 不符才重建"的冻结语义（即删除增长判断）——正是本故障的引入方式。

## 机制与判别

- 根因：初版重构的 `forward` 仅在 `cos_cached is None` / device / dtype 不符时 `_set_cos_sin_cache`，把"表已存在"误当作"表已覆盖全部位置"；decode 位置超出表长后 `cos[position_ids]` 越界。
- 可区分解释分支：a) NPU 越界 gather 抛异常（被证伪：NPU 无报错，错误只在 CPU 探针复现）；b) 越界 gather 静默返回未定义值 → 错误 token（成立，与 token_match=false、first_divergence_step=1 吻合）；c) FA/KV 写入路径错位（被证伪：`_prepared` 门控仅恢复 RoPE 增长即消除分歧，且 prefill 余弦不变）。
- 未验证推断：NPU 静默越界读取的具体返回值（零/残留内存）未在轨迹内直接观测。

## 验证信号

均在本机（Ascend950PR_9589 单卡、CANN 9.1.0、torch/torch_npu 2.12.0）实测，证据等级：脚本退出码 + JSON 比对结果。

- 故障复现：`compare_golden_npu.py` eager 路径 `token_match: false`、`first_divergence_step: 1`（rc=0 但结果错）；CPU 探针 `INDEX ERR IndexError index 21 is out of bounds for dimension 0 with size 21`。
- 修复：增加 `_prepared` 门控——未 `prepare` 的 eager 路径按 `int(position_ids.max().item()) + 1` 增长表（保留原动态 RoPE 语义），`prepare` 后冻结只读；修复后 eager 贪心 token 与 CPU golden 完全一致（token_match=True，prefill 余弦 0.9998937845230103），且图模式 graph_break_count 仍为 0。（修复后 `compare_golden_npu.py` rc=0、`token_match True div None`、`npu [27, 9399, 397, 60704]`；小模型探针 `graph_break_count = 0`、`NPUGRAPH_EX OK`）
- 单次观测，未做多轮统计。

## 适用与失效边界

- 适用：动态（懒增长）RoPE 改为图模式静态表时的 eager 兼容；`_prepared` 门控让同一实现同时满足"图内无分支"与"eager 语义不变"。
- 失效/风险：若 `prepare(max_seq_len)` 传入的最大长度小于实际 decode 到达的位置，eager 门控也不会救回（表已冻结且 `_prepared=True` 时越界读同样静默）——必须以 `max_seq_len`（含 max_new_tokens 上取整到 block 倍数）为准建表。
- NPU 静默越界意味着不能依赖异常发现此类错误，必须以 golden token/logits 比对作为门禁。
- 边界：仅在该模型/环境实测；其他 NPU 型号上越界 gather 行为未验证。
