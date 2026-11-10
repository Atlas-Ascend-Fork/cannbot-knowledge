---
{
  "type": "Runbook",
  "title": "长序列 Prefill 场景的确定性恰好 2048 token 输入构造：词边界裁剪保留 BOS + prompt 内嵌 YAML 单命令复现",
  "description": "为 hunyuan_a13b_fp8（input_len=2048、batch=1、max_new_tokens=8、npugraph_ex、FP8 W8A8）构造可复现基线输入时，利用 runner 截断保留末尾 N 个 token 会丢 BOS 的特性，改为按词边界逐词裁剪把 chat 模板化长度精确命中 2048（drop 8 words -> 2048），从而不触发截断、保留完整 chat 结构（首 token 127958 即 BOS、末 token 397）；再将完整 prompt 内嵌进场景 YAML，CPU 侧用同款 chat 模板 tokenize 复验 token ids 逐一致，实现 bash infer.sh 单命令可复现。该构造在 CPU 上完成并经两次客观校验，与 NPU 可用性解耦。",
  "tags": [
    "task.implementation",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# 长序列 Prefill 场景的确定性恰好 2048 token 输入构造：词边界裁剪保留 BOS + prompt 内嵌 YAML 单命令复现

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8 独立部署 Runner（`runner_hunyuan_a13b_fp8.py`，`bash infer.sh <yaml>`），HYTokenizer + chat template（`enable_thinking=False`、`add_generation_prompt=True`）。
- 目标工作负载：长序列 Prefill 基线/优化对照场景，input_len=2048、batch=1、max_new_tokens=8、单卡、exe_mode=npugraph_ex、FP8 W8A8。
- 构造与复验均在 CPU 侧完成（`TORCH_DEVICE_BACKEND_AUTOLOAD=0` 关闭 torch_npu 后端自动加载），与 NPU 可用性解耦——本轨迹中 NPU 因缺 /dev/davinci* 被阻塞（见 [容器内 NPU 访问不可用时 torch_npu 初始化失败的判别链（aclInit 507008 / 507899）](../runtime/aclinit_507008_no_npu_access_in_container.md)），输入构造不受影响。
- 缺失信息：NPU 侧运行时行为（含 ATTN_MASK_LEN=2048 对 Decode 段 kv_len 最大 2055 的潜在越界风险）未验证。

## 触发与观测

优化目标：为长 Prefill 场景构造"恰好 2048 token、可单命令复现"的输入。Runner 对超长 prompt 的处理是把 chat 模板化序列截断到 `input_truncated_len` 并保留末尾 N 个 token。首次构造（循环固定段落凑长文本）得到的 JSON 指纹：

```
  "chat_templated_full_len": 2057,
  "prefill_input_len": 2048,
  "first_token_id": 1455,
  "last_token_id": 397
```

自管 Runner 的 input_truncated_len 截断保留序列末尾 N 个 token：${PRIVATE_CREDENTIAL_1} 模板化长度 2057 的 prompt 截断到 prefill_input_len=2048 后首 token 变为 1455，BOS（127958）被截掉。

## 探针与操作

1. 写入构造脚本 `optimization-analysis/hunyuan_a13b_fp8/make_prefill2048_input.py`（CPU 可跑）：固定段落字面量循环拼长文本 → chat 模板 tokenize → 断言/记录 token ids → 生成场景 YAML（完整 prompt 内嵌）。
2. 词边界搜索：对首版文本逐词裁剪并统计 chat 模板化长度，观测到：

```
drop 7 words -> 2049
drop 8 words -> 2048
drop 9 words -> 2047
```

3. 把 `build_prompt_text` 改为"循环凑长 + 从词边界精确命中目标长度"（脚本最终版，逐字）：

```
def build_prompt_text(target_tokens: int, tokenizer) -> str:
    """Cycle the fixed paragraphs, then trim trailing words so that the
    chat-templated sequence is **exactly** ``target_tokens`` long.

    Hitting the target without truncation keeps the leading BOS and the full
    generation prompt, so the effective Prefill input is a natural 2048-token
    chat sequence (rather than a tail slice of a longer one).
    """
    pieces = []
    # generous upper bound; stop once the templated length reaches the target
    for i in range(64):
        pieces.append(PARAGRAPHS[i % len(PARAGRAPHS)])
        text = "\n\n".join(pieces)
        if chat_token_count(tokenizer, text) >= target_tokens:
            break
    else:
        raise RuntimeError("failed to build a sufficiently long prompt")

    words = text.split(" ")
    for drop in range(0, 40):
        candidate = " ".join(words[: len(words) - drop]) if drop else text
        if chat_token_count(tokenizer, candidate) == target_tokens:
            return candidate
    raise RuntimeError("could not hit the exact target token count at a word boundary")
```

4. 重跑脚本，产出的 JSON 指纹变为：

```
  "chat_templated_full_len": 2048,
  "prefill_input_len": 2048,
  "first_token_id": 127958,
  "last_token_id": 397
```

按词边界逐词裁剪（drop 8 words -> 2048）可把 chat 模板化长度精确命中 2048，不触发截断、保留完整 chat 结构，首 token 127958（BOS）、末 token 397。

5. 复验（CPU 侧，与 runner 相同的 chat 模板 tokenize 路径重放 YAML 内嵌 prompt）：

```
n prompts 1 type str
input_truncated_len 2048
sched {'batch_size': 1, 'max_new_tokens': 8, 'max_prefill_tokens': 2048, 'max_seq_len': 2176}
exe_mode npugraph_ex
yaml-derived len 2048 matches recorded: True
```

把完整 prompt 内嵌进场景 YAML，用与 runner 相同的 chat 模板 tokenize 路径在 CPU 侧复验，YAML 推导的 token 序列与记录文件逐一致（yaml-derived len 2048 matches recorded: True），`bash infer.sh config/hunyuan_a13b_fp8_prefill2048.yaml` 单命令即可复现输入。

## 机制与判别

- 截断语义：Runner 的 `input_truncated_len` 取 chat 模板化序列的**末尾** N 个 token（`seq[-N:]`），因此任何超出目标长度的 prompt 都会丢头部 token（含 BOS 与正文开头）；对长上下文评测而言尾部信息保留是合理的，但"恰好 N"的场景语义要求要么显式接受丢 BOS，要么把模板化长度精确压到 N。
- 命中机制：英文文本词≈1~2 token，逐词裁剪时 token 数单调不增且粒度足够细，在有限窗口（0..40 词）内能命中精确值；字符级裁剪同样可行（实测 trim 53 chars 命中 2048）但会截断在词中间，词边界裁剪可读性更好。
- 判别数据：首版（截断法）first_token_id=1455 vs 终版（词边界命中法）first_token_id=127958（即 `<|startoftext|>` BOS），同一 `last_token_id=397`（生成提示结束 token），证明差异唯一来源于是否触发截断。
- 交付物齐全性：`py_compile` 通过（COMPILE_OK）；YAML（12497 字节，prompt 内嵌）、prompt 原文（11209 字节）、token ids JSON（20357 字节，n=2048、min 11、max 127962）均落盘。
- 未验证推断：NPU 侧运行行为未验证（环境无 NPU）；runner `ATTN_MASK_LEN=2048` 与 Decode 段 kv_len 最大 2055 之间可能存在 FA atten_mask 尺寸越界，属待 NPU 恢复后验证的风险项，不构成本模式的结论。

## 验证信号

（均为本轨迹单次观测，平台：CPU（容器内）+ transformers HYTokenizer，torch 2.12.0）

| 信号 | 事件序号 | 说明 |
|---|---|---|
| 首版截断丢 BOS（first_token_id=1455） | T 161 | chat_templated_full_len 2057 → 2048 |
| 字符级裁剪可精确命中（trim 53 chars） | T 165 | 备选路线 |
| 词边界搜索表（drop 8 → 2048） | T 169 | 单调递减、粒度可命中 |
| 终版保留 BOS（first_token_id=127958） | T 176 | chat_templated_full_len 2048，无截断 |
| YAML/token 文件落盘与尺寸 | T 183 | truncated_by_runner=false |
| 辅助脚本 py_compile 通过 | T 203 | COMPILE_OK |
| YAML 重放与记录 token ids 逐一致 | T 207 | yaml-derived len 2048 matches recorded: True |

## 适用与失效边界

- 适用：任何"要求 prefill 输入恰好 N 个 token"的基准/对照场景，尤其是 runner 以 `seq[-input_truncated_len:]` 语义截断、且希望保留 BOS/完整 chat 结构时；构造与复验只需 CPU + tokenizer，可在无 NPU 环境先行完成。
- 失效/限制：
  - 词边界搜索窗口有限（0..40 词），若文本长度离目标太远或 tokenizer 粒度不合适（如中文按字切分、多字符复合词），可能无法在词边界精确命中——此时回退到字符级裁剪（实测可行但可能截断在词中间）或显式接受截断并记录 `truncated_by_runner=true`。
  - 该方法只保证输入确定性与单命令复现，不验证 NPU 侧推理正确性；场景 golden（token/文本基线）仍需 NPU 恢复后产出。
  - tokenizer/模板版本变化会改变 token 数，复现时需锁定同一 tokenizer 版本并重跑复验探针。
- 停止条件：若复验探针输出 `matches recorded: False`，说明 YAML/记录文件与模板路径不一致，应先修一致性再谈基线。
