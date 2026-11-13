---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1 _write_attention_cache 的 reference/auto 回退是静默空写死分支（KV cache 写被无声丢弃）",
  "description": "DeepSeek-V4.1 的 _write_attention_cache 默认 backend=\"reference\"，该路径无有效实现，非空输入也直接返回。backend=\"auto\" 时 native 调用成功会写入并返回 \"native\"；异常时被吞掉并返回 \"reference\"，但没有有效回退，异常前是否部分写入未确认。当前5处调用显式使用 \"native\"，并非当前部署已观察到的静默故障；新增默认/auto调用存在潜在风险。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# DeepSeek-V4.1 _write_attention_cache 的 reference/auto 回退是静默空写死分支（KV cache 写被无声丢弃）

## 适用场景

- 模型/框架：DeepSeek V4.1（DSA 注意力），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`（共 112 个提交，HEAD=6746201ec）。
- 平台：Ascend NPU（A5 生产：PD 分离 + ACL graph decode + fp8 deepseek_v4_fp8 + block 128 + max-model-len 150000）。
- 工作负载：用户报告"精度波动"。本条当前为**埋雷**（latent），非当前线上触发项。
- 该问题由两条独立审查轨迹分别发现（DSA 注意力审查 P1-1 与模型侧审查 P2-1），结论一致。

## 触发与观测

触发分两类（values 行数 >0）：使用默认 backend="reference" 时直接走空实现；使用 "auto" 时先调用融合算子，成功会写入并返回 "native"，异常则被吞掉且没有有效回退。异常前是否已发生部分写入未确认。

审查观测到的客观代码事实（事件 17，dsa_v41.py 全文读取 833-882 行，逐字）：

```
833:     def _write_attention_cache(
834:             self,
835:             cache: torch.Tensor,
836:             slot_mapping: torch.Tensor,
837:             values: torch.Tensor,
838:             *,
839:             kind: str,
840:             backend: str = "reference",
841:     ) -> str:
842:         """Write cmp/win rows and return the backend that actually executed."""
843:         if backend not in ("reference", "auto", "native"):
844:             raise ValueError(f"Unsupported A5 cache-writer backend: {backend}")
845:         if values.shape[0] == 0:
846:             return "reference" if backend == "reference" else backend
847:         if backend != "reference":
848:             try:
849:                 # 小算子实现
850:                 # rows = self._native_pack_rows(values, kind)
851:                 # self._scatter_rows(cache, slot_mapping, rows)
852:                 # 融合算子实现
853:                 if slot_mapping.ndim == 2:
854:                     slot = (slot_mapping[:, 0]) * cache.shape[1] + slot_mapping[:, 1]
855:                     slot_mapping = slot.clamp(min=-1).to(torch.int32)
856:                 elif slot_mapping.ndim != 1:
857:                     raise ValueError(
858:                         f"A5 cache-writer slot mapping must be [T, 2] or [T], got ndim={slot_mapping.ndim}"
859:                     )
860:                 # 1-D builder-prepared flat slots are consumed as-is.
861:                 if kind == "cmp":
862:                     group_size, quant_mode = (16, "mxfp4_bf16",)
863:                 elif kind == "win":
864:                     group_size, quant_mode = (32, "mxfp8_bf16",)
865:                     # 算子校验要求
866:                     cache = cache.view(torch.float8_e4m3fn)
867:                 else:
868:                     raise ValueError(f"Unsupported A5 packed cache kind: {kind}")
869:                 torch.ops.custom.kv_compress_epilog_v2(
870:                 cache,
871:                 values,
872:                 slot_mapping,
873:                 quant_group_size=group_size,
874:                 quant_mode=quant_mode,
875:                 round_scale=True,
876:                 x_scale=1.0,
877:                 )
878:                 return "native"
879:             except Exception:
880:                 if backend == "native":
881:                     raise
882:         return "reference"
```

当前调用点均显式传 backend="native"（事件 304，dsa_v41.py 尾部读取可见三处调用 902-908/921-927/929-935 均为 `kind="win", backend="native"`）：

```
899:         cache = attn.dsa_attn.swa_cache_layer.kv_cache[0]
900:         plan = getattr(swa_metadata, "private_circle_plan", None)
901:         if plan is None:
902:             self._write_attention_cache(
903:                 cache,
904:                 _slots_for_cache_write(swa_metadata, cache),
905:                 kv,
906:                 kind="win",
907:                 backend="native",
908:             )
909:             return
```

## 探针与操作

核查命令（审查会话实际执行的等价形式）：

```
git log -p 09220f435~1..HEAD -- vllm_ascend/attention/dsa_v41.py | grep -n "_scatter_swa_kv\|dsa_kv_compress_scatter\|backend=" | head -40
```

以及直接读取 `vllm_ascend/attention/dsa_v41.py` 第 833-882 行（`_write_attention_cache` 全函数）。调用点核查：`grep -rn "_write_attention_cache" vllm_ascend/`（审查报告确认 dsa_v41.py:902/921/929/1090 与 dspark.py:230 共 5 处均 native）。

本条为只读审查发现，未实施修复；"删除 auto/reference 死分支与被注释的 reference 实现，只保留 native + 显式 raise；或恢复真正可用的 reference 实现"的修复建议未经验证，不能当作已验证修法采用。

## 机制与判别

结论 1：_write_attention_cache 默认 backend="reference"，而 reference 分支实现（_native_pack_rows + _scatter_rows）在 849-851 行已被整段注释；非空 values 在 "reference" 路径不执行写入即返回 "reference"；"auto" 成功时执行 native 写入，只有异常回退分支缺失有效写入保证。
- 证据：事件 17 逐字代码（840 行默认值、849-851 行注释、882 行 `return "reference"`）。

结论 2：backend="auto" 时融合算子异常被吞掉后返回 "reference" 且无有效回退；异常前可能未写入或已部分写入，轨迹未确认；当前 5 处调用（dsa_v41.py:902/921/929/1090 与 dspark.py:230）均显式传 backend="native"（失败会 raise），线上未触发，属新增调用点/默认参数场景的地雷。
- 证据：事件 304（当前调用点逐字）+ 两份审查报告（事件 279/437）的调用点清单。
- 可区分解释分支：
  - 新调用点用默认参数或 "auto" + 融合算子抛错 → 缺少有效 KV 写入保证，该层可能读到全零、陈旧或部分更新的 KV → 输出错误且难以定位，正是"精度波动"式症状（静默劣化）。
  - 现有 5 处 native 调用点出错 → 异常 re-raise → 响亮崩溃（不是静默）。
- 未验证推断：`_native_pack_rows`/`_scatter_rows`（750-831 行）当前成为死代码；未来 CANN 小版本对 `kv_compress_epilog_v2` ABI 的变化是否会被 auto 吞掉取决于算子抛错与否，轨迹内未验证。

## 验证信号

- 信号等级：代码事实（read/git 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 17（_write_attention_cache 833-882 行完整原文，含被注释的 reference 实现与吞异常结构）、事件 304（_scatter_swa_kv 三处调用均为 backend="native" 的原文）。
- 平台：Ascend NPU（A5）。两条轨迹（DSA 注意力审查与模型侧审查）独立给出一致结论，证据等级：代码事实 + 双轨迹交叉一致。
- 无性能/精度数值结论（只读审查）。

## 适用与失效边界

- 适用：releases/v0.27.1rc 区间内所有使用 `_write_attention_cache` 的代码维护/新增调用点场景；风险面是"新增调用未显式传 backend"或"传 auto"。
- 不适用：当前已部署代码路径（5 处调用全 native，失败即 raise，不会静默丢写）。
- 版本边界：922433912 注释掉 reference 小算子实现但保留回退结构，是本死分支的成因；后续版本若恢复 reference 实现则本条失效。
- 停止/回退条件：非空 values 调用若返回 "reference"（或新增调用点无显式 backend 参数），应视为缺少有效写入保证的排查项；零行输入的提前返回无需写入，不据此判故障。
- 修复方向（未验证）：删除 "reference"/"auto" 死分支与注释代码，只保留 native + 显式 raise；或恢复一个真正可用的 reference 实现。
