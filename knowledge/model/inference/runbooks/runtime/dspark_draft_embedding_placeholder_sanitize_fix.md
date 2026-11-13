---
{
  "type": "Runbook",
  "title": "DSV4.1 dspark draft embedding 前的 -1 placeholder 消毒补丁与验证边界",
  "description": "vllm-ascend DSV4.1（deepseek_v41/dspark.py draft 模型）在 A5、PD 分离、async speculative decode（dspark，`--async-scheduling` + padded drafter batch）部署下，decode 阶段出现 embedding 算子执行异常（aivec 334）/ NPU function error 507011、设备 stream 执行失败。 任何\"目标模型有 placeholder 消毒、draft 模型没有\"的不对称结构；DP4/TP1 下 VocabParallelEmbedding 不做掩码，非法 id 会直接打穿。",
  "tags": [
    "task.debugging",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# DSV4.1 dspark draft embedding 前的 -1 placeholder 消毒补丁与验证边界

## 适用场景

- vllm-ascend DSV4.1（deepseek_v41/dspark.py draft 模型）在 A5、PD 分离、async speculative decode（dspark，`--async-scheduling` + padded drafter batch）部署下，decode 阶段出现 embedding 算子执行异常（aivec 334）/ NPU function error 507011、设备 stream 执行失败。
- 任何"目标模型有 placeholder 消毒、draft 模型没有"的不对称结构；DP4/TP1 下 VocabParallelEmbedding 不做掩码，非法 id 会直接打穿。

## 触发与观测

- 触发：PD 分离 D 侧 async spec decode 运行中，Worker 报 `async_copy_ready_event.synchronize` → NPU function error: device error type 3, error code 507011，Ascend 日志显示 AI Core Error、model stream execute failed retCode=0x91。
- 观测到的失败机制：draft 的 `embed_tokens(input_ids)` 拿到 -1 做 gather。

## 探针与操作

- 排查链（按序）：
  1. 从引擎日志定位到错误发生在 draft 前向的 embedding。
  2. 读 `vllm_ascend/ops/triton/spec_decode/utils.py` 的 copy_and_expand kernel，确认 bonus 直写 draft input_ids 且无上界校验。
  3. grep `PLACEHOLDER_TOKEN_ID` 与 `_sanitize_placeholder_input_ids_for_forward`，确认目标侧 runner 有消毒（masked_fill_ 成 0）而 draft 侧没有。
  4. 读 dspark.py forward，确认既有 torch.where 的位置与用途。
- 来源结论：消毒层不对称是根因：目标模型侧 model_runner_v1.py:2556 的 _sanitize_placeholder_input_ids_for_forward 会把 PLACEHOLDER_TOKEN_ID masked_fill_ 成 0，而 draft 路径在 embedding 之前没有任何等价消毒；dspark.py:251-253 既有的 moe_input_ids = torch.where(input_ids == -1, 0, input_ids) 位于 embed_tokens（:247）之后、是为 MoE gate 的 tid2eid 查表加的分支复制（新张量，不改 input_ids 本身），对 embedding gather 完全无效。

## 机制与判别

- before（修复前 dspark.py forward，embed_tokens 直接消费原始 input_ids）：

```python
    def forward(self, input_ids: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        hidden_states = self.embed_tokens(input_ids).unsqueeze(-2).repeat(1, self.hc_mult, 1)
        pre_mix = hidden_states.new_zeros(hidden_states.shape[0], self.hc_mult, dtype=torch.float32)
        pre_mix[:, 0] = 1.0
        last_layer = None
        moe_input_ids = input_ids
        if self.needs_moe_input_ids:
            moe_input_ids = torch.where(input_ids == -1, 0, input_ids)
        for layer in self.layers.values():
            last_layer = layer
```

- 目标侧既有的消毒入口（draft 侧缺失的等价物）：

```text
2556	    def _sanitize_placeholder_input_ids_for_forward(
2557	        self,
2558	        scheduler_output: "SchedulerOutput",
2559	        num_forward_tokens: int,
2560	    ) -> None:
2561	        scheduled_spec_tokens = scheduler_output.scheduled_spec_decode_tokens
2562	        if not scheduled_spec_tokens:
```

- after（修复：embedding 之前补一行同款消毒；git diff 核对原文见下，Edit 于 dcb1589e 、diff 于 ）：

```text
@@ -244,6 +244,11 @@ class DeepseekV41DSparkModel(DeepseekV4DSparkModel):
             plan.dsa_kv_compress_scatter(cache.kv_cache[0], values, slot_mapping)

     def forward(self, input_ids: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
+        # Async spec-decode hands the drafter the -1 sample placeholder while a
+        # token's sample is still in flight; a -1 index faults the Embedding
+        # gather (aivec 334). Neutralise it before the lookup too, not only
+        # before the MoE gate lookup below.
+        input_ids = torch.where(input_ids == -1, 0, input_ids)
         hidden_states = self.embed_tokens(input_ids).unsqueeze(-2).repeat(1, self.hc_mult, 1)
         pre_mix = hidden_states.new_zeros(hidden_states.shape[0], self.hc_mult, dtype=torch.float32)
         pre_mix[:, 0] = 1.0
```

- 来源结论：在 dspark.py forward 的 embed_tokens 之前补一行 input_ids = torch.where(input_ids == -1, 0, input_ids) 即可阻断 -1 进入 embedding gather；该同款 torch.where 算子本来就在被捕获的 draft 前向中每步运行（MoE gate 路径），该补丁提前执行同类算子，但 capture/replay 兼容性仍需设备验证，且改动落在 v4.1 专属文件、符合特性不下沉公共模块的约束。
- 判别要点：torch.where 返回新张量（分支复制），不改 input_ids 本身；它在 :251 只喂给 MoE gate 查表（needs_moe_input_ids 定义为 gate.tid2eid/bias_vl 存在，即按 token id 查表路由），救不了 :247 的 embedding。三层消毒结构：①runner/proposer 层（target 有、draft 无）、②embedding 之前（两侧皆无）、③embedding 之后/MoE 之前（两侧皆有但救不了 embedding）——崩在 ②。
- 权衡：mask 成 0 后这些行不会崩，但对应行的 draft 变成噪声 token，预期依赖 target 的 rejection sampler 处理，但本记录没有验证所有受影响路径——设计上依赖 rejection sampler 兜底；输出正确性和接受率变化尚未实测；若下降明显说明该路径命中频率高，还有更深的 async bookkeeping 问题值得单独查。备选改法（改公共文件 llm_base_proposer.py 的 prepare_next_token_ids_padded、或 set_inputs_first_pass 里 clamp）要么踩"特性不下沉公共模块"约束、要么覆盖面窄。

## 验证信号

- 补丁落盘与静态检查记录（本轨迹内，validation_scope = source_read + static_check）：
  - Edit applied successfully。
  - git diff 显示恰好 +5 行（1 行代码 + 4 行注释），moe_input_ids 段保持原样。
  - `python3 -m py_compile` 通过。
  - 本地 ruff 模块缺失；dspark 相关 UT 未运行，需在具备环境侧跑 `bash format.sh ci` 与 `pytest -sv tests/ut/worker/test_model_runner_v1.py`。
- 硬件复现验证（用户侧执行，轨迹内未捕获结果）：async + 压测（新请求持续从 prefill 移入）复跑，确认 `Embedding ... aivec error 334 / 507011` 不再出现；可在 set_inputs_first_pass 加临时诊断统计 `int((next_token_ids < 0).sum())` 确认因果（会引入 D2H 同步，只做诊断用）。

## 适用与失效边界

- 适用：vLLM v0.27.1 系 async spec decode + dspark/EAGLE 类 drafter、padded drafter batch 默认开启（disable_padded_drafter_batch=False）的场景。
- 补丁意图是止损，运行效果与根治方案均待验证：根治要么让 next_token_ids 永不为 -1（上游 scheduler/get_token_id 语义问题），要么收紧 async 的 backup 语义；mask 成 0 与上游 `clamp_(min=0)`（gpu_model_runner.py "Clamp speculative scheduler placeholders (-1) before embedding lookup"）是同类既定取舍。
- 失效/注意：本轨迹验证止于静态级（py_compile + diff 复核），硬件复现与接受率回归未在轨迹内完成；若目标模型（model.py:826 embed_input_ids）也依赖 runner sanitizer 的扫描完整性，可考虑同样加固，但那是可选加固而非必须。

生产/消费链的源码排查见 [placeholder 到 embedding 的诊断](dsv41_embedding_aivec334_root_cause_fix.md)；两张卡是同一问题的诊断和补丁视角，不增加独立复现次数。
