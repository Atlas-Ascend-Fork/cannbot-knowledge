---
{
  "type": "Runbook",
  "title": "无权重模型迁移的 CPU 黄金基线与 teacher-forced 一致性验证方法",
  "description": "离线无官方权重的模型迁移可用固定种子随机初始化做粗粒度 CPU↔NPU 一致性验证：CPU golden 与 NPU 侧调用同一 build_model 复现相同权重，比对 prefill logits（cosine/top-k）。本例随机权重下自由 greedy decode 在前 3 token 后分叉，须改用 teacher-forced（把 CPU token 轨迹逐个喂回 NPU）比较逐步 logits。先跑小配置冒烟再跑全量可低成本暴露适配错误。",
  "tags": [
    "task.implementation",
    "task.testing",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# 无权重模型迁移的 CPU 黄金基线与 teacher-forced 一致性验证方法

## 适用场景

- 场景：离线环境迁移 HF 模型到 Ascend NPU（独立部署），**无官方权重/无真实 tokenizer**，需要粗粒度验证设备适配正确性。
- 模型/框架：HYV4（MoE + MLA + DSA + iHC + 可学习 sink，vendored 自 transformers 5.19.0），torch 2.12.0+cpu + torch_npu 2.12.0，bf16。
- 平台：Ascend950PR_9589 单卡（123.25 GiB），CANN 9.1.0；L=4 配置（6.039B 参数）。
- 固定输入：prompt `"What is the capital of France? Answer in one short sentence."`（13 token），max_new_tokens=8，seed=1234。

## 触发与观测

- 触发：任务要求「随机权重需可从同一固定种子在 CPU/NPU 上复现，保证粗粒度精度对齐可做」，且精度无绝对值意义、仅做粗粒度 CPU↔NPU 一致性验证。
- 观测（事件 215）：NPU prefill logits 对 CPU golden——cosine 0.999971、max abs diff 0.011826、top-1 一致（101453）、top-10 重叠 10/10；自由 greedy decode 仅前 3 token 一致（3/8），随后 NPU 分叉为 `[...76480, 76480, 76480, 76480]`。
- 观测（事件 253）：引入 teacher-forced 对照后，per-step cosine 0.996914–0.999977、argmax 6/7——两侧在相同输入轨迹下仍有小幅数值差异；近票 argmax 是待核对解释，不能仅据高 cosine 排除算子或状态错误。

## 探针与操作

分三步，从低成本到高成本：

1. **小配置冒烟**（事件 141/145/149）：先用 2 层、hidden 64、vocab 1000 的小配置在 CPU 与 NPU 各跑 prefill + 3 步 decode，比对 token；首个探针因 `pad_token_id=120002 > vocab_size=1000` 触发 `AssertionError: Padding_idx must be within num_embeddings`（事件 142），属冒烟测试按设计暴露的问题。
2. **CPU golden**（事件 153，`tools/golden_cpu.py`）：固定 seed 构建随机权重模型 + 固定 prompt，落盘 `cpu_golden.pt`（input_ids / prefill_logits / decode_logits / generated_token_ids）与 `cpu_golden.json`。核心（事件 153 原文）：

```python
def build_model(config, seed=DEFAULT_SEED, dtype=torch.bfloat16):
    """Deterministic random-weight model. Always constructs on CPU."""
    torch.manual_seed(seed)
    model = HYV4ForCausalLM(config)
    init_weights(model, config)
    cast_model_dtype(model, dtype)
    model.eval()
    return model
```

3. **NPU 对照 + teacher-forced decode**（事件 202/248，`tools/compare_golden_npu.py`）：NPU 侧调用同一 `build_model` 复现相同权重，先比 prefill logits（cosine/top-k），再喂 CPU 轨迹逐步比 logits（事件 248 原文）：

```python
    # Teacher-forced comparison: replay the CPU token trajectory on the NPU and
    # compare per-step logits (isolates arithmetic drift from argmax tie-breaks).
    cpu_decode_logits = golden["decode_logits"].float()
    tf_cos, tf_max, tf_argmax, tf_tokens = [], [], 0, []
    cache_tf = HyV4Cache(config)
    with torch.no_grad():
        model(
            input_ids=input_ids,
            attention_mask=build_additive_causal_mask(seq_len, seq_len, 0, device=device),
            position_ids=torch.arange(seq_len, device=device).unsqueeze(0),
            past_key_values=cache_tf,
            use_cache=True,
            logits_to_keep=1,
        )
        for step in range(max_new - 1):
            past_len = seq_len + step
            inp = torch.tensor([[cpu_gen[step]]], device=device)
            out = model(
                input_ids=inp,
                attention_mask=build_additive_causal_mask(1, past_len + 1, past_len, device=device),
                position_ids=torch.tensor([[past_len]], device=device),
                past_key_values=cache_tf,
                use_cache=True,
                logits_to_keep=1,
            ).logits.float().view(-1).cpu()
            ref = cpu_decode_logits[step]
            tf_cos.append(round(float(torch.nn.functional.cosine_similarity(out, ref, dim=0)), 6))
```

失败路线（不可采用）：用**自由 greedy decode 的 token 一致率**判定 NPU 正确性——自由序列一旦分叉，后续 logits 还混入不同输入和缓存历史的影响；只看该比率难以定位原因。是否允许 token 分叉须由任务精度契约决定，不能自动豁免。

## 机制与判别

- 无官方权重的模型可用固定种子随机初始化权重做粗粒度 CPU↔NPU 一致性验证：CPU golden 与 NPU 侧各自调用同一 build_model（torch.manual_seed → 构造 → init_weights → cast_model_dtype）复现出相同权重，NPU prefill logits 对 CPU golden cosine 0.999971、top-1 一致、top-10 重叠 10/10、max abs diff 0.011826。
- 本例自由 greedy decode 前 3 个 token 一致（3/8），随后分叉；具体翻转原因未通过逐步 margin 和中间张量充分隔离。可补充 teacher-forced（把 CPU token 轨迹逐个喂回 NPU）比较逐步 logits，实测 per-step cosine ≥ 0.996914、argmax 6/7。
- 判别逻辑：prefill cosine/top-k 与 teacher-forced per-step cosine 是已测样本上的粗粒度一致性信号，不能证明整个计算图或所有 decode 算术正确。固定输入轨迹有助于区分输入分叉带来的差异与同输入下的差异；高 cosine 也可能掩盖局部错误，需结合误差分布、关键节点和任务验收。
- 全量 golden 之前先用小配置冒烟（2 层、hidden 64、vocab 1000），CPU 与 NPU 各 decode 3 步 token 完全一致（201/61/169）后再跑 6B 全量，可低成本暴露适配错误。

## 验证信号

- 事件 146/150（小配置冒烟，CPU 与 NPU 各 3 步 decode token 一致：201/61/169；NPU 显存 2.64 GiB）。
- 事件 166/170（CPU golden 产出：13 token prompt、生成 8 token、6.039B 参数、prefill 7832.78 ms、total_len 21）。
- 事件 215（prefill 一致性）：cosine 0.999971、max abs diff 0.011826、argmax_match true、top10_overlap 10、自由 decode match_count 3/8。
- 事件 253（teacher-forced 一致性）：per_step_cosine = [0.999973, 0.999974, 0.996914, 0.999977, 0.999972, 0.999972, 0.999977]、argmax_match_count 6/7、min_cosine 0.996914。
- 事件 199：NPU 日志仅 1 条无害告警（`F.one_hot` 内部格式提示），无错误。
- 证据等级：单机单卡、单次 golden 产出 + 一次对照运行（后续阶段 0.4 修复轮与 2.4 reviewer 复核中同口径指标逐次复现一致，见 来源记录 事件 149）。

## 适用与失效边界

- 适用：无权重（或权重不可得）的模型移植/算子替换的粗粒度验证；CPU 侧黄金可长期落盘复用。
- 失效/风险：
  - 随机权重 + 近票 logits 下，任何指标都不携带绝对精度意义；阈值只能用「同量级漂移」（如 cosine ≥ 0.99、top-k 大体重叠）而非绝对值。
  - 自由 greedy decode token 一致率与 teacher-forced logits 回答不同问题，应共同报告；是否将 token 分叉作为失败由目标精度契约决定。
  - teacher-forced 只覆盖被喂轨迹的逐步算术，不覆盖「NPU 自身生成轨迹上的 KV 写入正确性」——后者需结合确定性重跑（同 token 序列逐位一致）佐证。
  - 冒烟配置与全量配置的维度差异意味着冒烟通过 ≠ 全量通过（本例冒烟后全量一次通过，但不构成保证）。
  - 权重/结构/tokenizer 变更会改变 RNG 消耗与 token 轨迹，golden 需重建；tokenizer 为兜底 byte-BPE（无语义），仅保证确定性。
  - bf16 下 per-step max abs diff 可达 0.135（近票步），对精度敏感结论应看 cosine 与 argmax 而非 abs diff 单项。
