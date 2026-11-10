---
{
  "type": "Runbook",
  "title": "非 A5（A2/A3）硬件上 DeepSeek-V4.1 SWA KV 写入与 indexer K-cache 无条件走 A5 专用量化算子",
  "description": "vllm-ascend DeepSeek-V4.1 适配中，DSV4_COMPRESSED_CACHE 是 A5 独有 capability，非 A5 上 SWA 平面为 BF16，但 _scatter_swa_kv 对所有硬件无条件调用 A5 量化写入（win 分支 cache.view(fp8) + kv_compress_epilog_v2 mxfp8_bf16 544 字节行格式）；indexer update_keys 也无条件调用 indexer_quant_cache(quant_mode=\"mxfp4\")，而非 A5 spec 为 int8+fp16 单 scale。仅 A2/A3 部署触发：BF16 平面被按 FP8 布局重释导致 SWA KV 错乱或算子校验崩溃、key_scale.view(...,2,2) 对 1 元素张量 RuntimeError。A5 生产路径不受影响。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "a2",
    "a3"
  ]
}
---

# 非 A5（A2/A3）硬件上 DeepSeek-V4.1 SWA KV 写入与 indexer K-cache 无条件走 A5 专用量化算子

## 适用场景

- 模型/框架：DeepSeek V4.1（DSA 注意力：indexer + compressor + SWA full-attn），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`（共 112 个提交，HEAD=6746201ec）。
- 平台：Ascend NPU；生产路径为 A5 + deepseek_v4_fp8 + weight_nz_mode=2 + eager/FULL_DECODE_ONLY + TP/EP。本条风险的触发平台是**非 A5（A2/A3）部署**。
- 工作负载：用户报告"精度波动"（生产 A5 路径）；本条是 A2/A3 部署下的硬错误（会崩溃或 KV 全错乱）。
- 缺失信息：轨迹内未提供 A2/A3 实机运行日志（本条为代码级审查结论，未在非 A5 硬件上运行验证）。

## 触发与观测

触发 = 在 A2/A3（不具备 DSV4_COMPRESSED_CACHE capability）上部署 DeepSeek-V4.1。审查观测到的客观代码事实：

1. capability 归属（事件 377，grep 输出）：

```
vllm_ascend/device/hardware_profile.py:29:    DSV4_COMPRESSED_CACHE = auto()
vllm_ascend/device/hardware_profile.py:197:                    HardwareCapability.DSV4_COMPRESSED_CACHE,
```

事件 380（hardware_profile.py 170-215 行读取）确认第 197 行位于 `AscendDeviceType.A5: HardwareProfile(...)` 的 capabilities frozenset 内。

2. 非 A5 的 cache dtype 解析（事件 373，dsa_attn_kv_plan.py 14-50 行读取，逐字）：

```
_BF16_KV_CACHE_DTYPES = frozenset({"bfloat16", "bf16"})


def _supports_dsv4_compressed_cache() -> bool:
    return get_current_hardware_profile().supports(HardwareCapability.DSV4_COMPRESSED_CACHE)


def resolve_dsv4_cache_dtype(cache_dtype, model_dtype: str) -> str:
    """Return the KV cache dtype the platform should pin for DeepSeek-V4.

    On A5 the launch request has to stay readable afterwards, because it is the
    only thing that separates an explicit bfloat16 KV request from ``auto``.
    ``auto`` and the model dtype resolve identically everywhere downstream, so
    collapsing every non-bfloat16 request to ``auto`` preserves the upstream
    values while keeping the mode recoverable.
    """
    if not _supports_dsv4_compressed_cache():
        return model_dtype
    return "bfloat16" if str(cache_dtype).lower() in _BF16_KV_CACHE_DTYPES else "auto"
```

3. SWA 写入无条件走 A5 量化算子（事件 304，dsa_v41.py 700-939 行读取的尾部，逐字）：

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

同文件 `_write_attention_cache` 的 win 分支执行 `cache = cache.view(torch.float8_e4m3fn)` 后用 `kv_compress_epilog_v2(quant_mode="mxfp8_bf16", quant_group_size=32)` 写入 544 字节（512B FP8/32 + 16×BF16 scale）行格式（与 `core/deepseek_v41.py` 的 `A5_WIN_ROW_BYTES=544` 一致）——即 A5 专用格式。

4. indexer K-cache 写入（事件 27，indexer.py 全文读取，逐字）：

```
113:         k_cache, scale_cache = self.k_cache.kv_cache[0]
114:         if slots.ndim == 1:
115:             # Builder-prepared flat slots; identical to converting the [T, 2]
116:             # mapping per call, computed once per cache group per step.
117:             slot_mapping = slots
118:         elif slots.ndim == 2:
119:             slot_mapping = (slots[:, 0]) * k_cache.shape[1] + slots[:, 1]
120:             slot_mapping = slot_mapping.clamp(min=-1).to(torch.int32)
121:         else:
122:             raise ValueError(
123:                 f"indexer update_keys slot mapping must be [T, 2] or [T], got ndim={slots.ndim}"
124:             )
125:         key = key.squeeze(1)
126:
127:         torch.ops.cann_ops_transformer.indexer_quant_cache(
128:             cache=k_cache,
129:             cache_scale=scale_cache,
130:             x=key,
131:             slot_mapping=slot_mapping,
132:             quant_mode="mxfp4"
133:         )
```

## 探针与操作

审查会话实际执行的核查命令：

```
grep -rn "DSV4_COMPRESSED_CACHE" vllm_ascend/device/*.py | head -10
sed -n '14,50p' vllm_ascend/attention/dsa_attn_kv_plan.py
git log -p 09220f435~1..HEAD -- vllm_ascend/models/deepseek_v41/indexer.py | grep -n "quant_mode\|indexer_quant_cache\|int8\|scale_dtype\|scale_dim\|dtype=" | head -40
```

演进证据（事件 326，git log -p 过滤输出，逐字节选）：

```
361:                     dtype=torch.uint8 if use_a5_quantized_cache else torch.int8,
363:                     scale_dim=self.width // 32 if use_a5_quantized_cache else 1,
373:-            key, dst_type=torch.int8
375:+        torch.ops.cann_ops_transformer.indexer_quant_cache(
380:+            quant_mode="mxfp4"
```

```
625:-                    dtype=torch.int8,
626:+                    dtype=torch.uint8 if use_a5_quantized_cache else torch.int8,
628:-                    scale_dim=1,
629:-                    scale_dtype=torch.float16,
630:+                    scale_dim=self.width // 32 if use_a5_quantized_cache else 1,
631:+                    scale_dtype=(torch.uint8 if use_a5_quantized_cache else torch.float16),
```

说明：spec 侧（get_kv_cache_spec）仍按 `use_a5_quantized_cache` 分支（非 A5 为 int8[128] + fp16[1] 每行单 scale），但写入门子的 `indexer_quant_cache(quant_mode="mxfp4")` 变为无条件调用——非 A5 的 int8 写入分支（`npu_dynamic_quant(key, dst_type=torch.int8)`）被替换遗失。本条为只读审查，未实施修复；"恢复非 A5 分支（int8 dynamic quant + 对应 descale 形状）或在 V4.1 初始化时显式拒绝非 A5 硬件"的修复建议未经验证。

## 机制与判别

结论 1：DSV4_COMPRESSED_CACHE 是 A5 独有 capability（hardware_profile.py:197 仅列于 A5 profile），非 A5 上 resolve_dsv4_cache_dtype 返回 model_dtype（BF16），而 _scatter_swa_kv 对所有硬件无条件调用 _write_attention_cache(kind="win", backend="native")，win 分支 cache.view(torch.float8_e4m3fn) 后按 mxfp8_bf16、544 字节行格式写入，BF16 [..,512] 平面被按 FP8 布局重释。
- 证据链：事件 377/380（capability 仅 A5）→ 事件 373（非 A5 返回 model_dtype）→ 事件 304（写入无硬件分支）。
- 机制：非 A5 SWA 平面为 BF16、head_size=512（model.py else 分支保留 spec.head_size），被 `view(fp8)` 重释为 [..,1024] → SWA KV 全部错乱或算子校验崩溃。
- 反证（同仓库正确实现）：DSpark 的 `_store_standard_swa_kv` 明确按硬件分支——A5 用融合量化写入，非 A5 用 `plan.dsa_kv_compress_scatter`（models/deepseek_v41/dspark.py:216-244），而目标模型的 `_scatter_swa_kv` 没有这个分支。

结论 2：indexer 的 update_keys 无条件调用 indexer_quant_cache(quant_mode="mxfp4")；非 A5 的 K-cache spec 为 int8[128] + fp16[1] 每行单 scale（spec 侧仍按 use_a5_quantized_cache 分支），key_scale.view(...,2,2) 需要 4 个元素，1 元素 fp16 张量无法 view 导致 RuntimeError，或算子把 mxfp4 打包数据写进 int8 平面导致后续 QLI 读取错乱。
- 证据：事件 27（当前态无条件调用）+ 事件 326（diff 显示 int8 写入分支被删）。

结论 3：仅在 A2/A3 部署时触发，A5 生产路径不受影响；09220f435 初始版本非 A5 用 npu_dynamic_quant(key, dst_type=torch.int8) 写 int8+fp16，A5 化改造（b0676c87b/b598d92cf 补写入时只按 A5 实现）后非 A5 写入路径被替换遗失。
- 判别：A2/A3 上启动即崩（RuntimeError）或输出系统性错乱（SWA 层全错）→ 指向本条；间歇性波动且发生在 A5 → 指向其他机制（如 cmp_topk_length、indexer 权重精度）。
- 未验证推断：mxfp4 数据写进 int8 平面后的具体症状（崩溃 vs 静默错乱）依赖算子校验行为，轨迹内未在非 A5 硬件验证。

## 验证信号

- 信号等级：代码事实（grep/read/git show 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 377（DSV4_COMPRESSED_CACHE 仅在 hardware_profile.py:197/A5 profile）、事件 373（非 A5 返回 model_dtype 的完整函数原文）、事件 304（_scatter_swa_kv 无条件 native 量化写）、事件 27（update_keys 无条件 mxfp4）、事件 326（git log -p 显示非 A5 int8 分支被删）。
- 平台：Ascend NPU（A5 生产 / A2/A3 风险面）。
- 无性能/精度数值结论（只读审查，未在非 A5 硬件运行）。

## 适用与失效边界

- 适用：DeepSeek-V4.1 在 A2/A3 等**不具备 DSV4_COMPRESSED_CACHE** 的 Ascend 器件上部署（含 PD 混部中混入非 A5 节点的场景）。
- 不适用：纯 A5 生产路径（本审查报告判定 A5 上"未发现必然出错的 P0"，README 亦自述数值正确性尚未在 NPU 上验证）。
- 版本边界：releases/v0.27.1rc 的 09220f435~1..HEAD 区间；09220f435 初始版本 SWA 写入本是注释掉的 TODO，b0676c87b/b598d92cf 补写入时只按 A5 实现。
- 停止/回退条件：若 A2/A3 上 `key_scale.view(...,2,2)` 先行崩溃（响亮失败），SWA 平面错写不会静默发生；此时优先修复 indexer 侧崩溃并验证 SWA 写入路径。
- 修复方向（未验证）：`_scatter_swa_kv` 与 `update_keys` 按 `use_a5_quantized_cache` 分支，非 A5 走 `dsa_kv_compress_scatter`/int8 dynamic quant（与 dspark.py 对齐），或在 V4.1 初始化时显式拒绝非 A5 硬件。
