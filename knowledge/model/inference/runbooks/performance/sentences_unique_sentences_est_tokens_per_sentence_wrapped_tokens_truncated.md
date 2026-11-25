---
{
  "type": "Runbook",
  "title": "MoE profiling 代表性输入：循环复读输入使专家路由退化失真；mixed-radix 四槽词库确定性生成 100% unique 长文本；32k greedy 输出重复环非输入伪影",
  "description": "模型/框架：hy3_preview 295B MoE（~21B 激活）on cann-recipes-infer，32k 输入/8 batch baseline profiling；适用于一切 MoE 模型的 profiling/性能基线输入构造。",
  "tags": [
    "task.implementation",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# MoE profiling 代表性输入：循环复读输入使专家路由退化失真；mixed-radix 四槽词库确定性生成 100% unique 长文本；32k greedy 输出重复环非输入伪影

## 适用场景

- 平台范围依据：source 0 seq 23的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：hy3_preview 295B MoE（~21B 激活）on cann-recipes-infer，32k 输入/8 batch baseline profiling；适用于一切 MoE 模型的 profiling/性能基线输入构造。
- 任务：为 MoE 模型 profiling 构造代表性长输入（真实专家路由分布），并区分「输入循环伪影」与「超长上下文 greedy 退化」。
- 环境依据轨迹：round0 profiling 前置输入重建 + 实跑验证（tokenizer 机验 + 16 卡实跑输出比对）。

## 触发与观测

- 触发：原 baseline 输入为 10 句英文 × 176 次循环（~42k token 截 32k）——相同 token 反复路由到同几个专家，MoE 专家负载分布对 profiling 无代表性，且 greedy 输出重复环（source 0 seq 43/58/63，tool_observed 脚本头注释 + verify 输出）。
- 观测（构造陷阱，source 0 seq 62/63，tool_observed）：第一版生成器四槽（主语/动词/宾语/状语）都由同一 `sent_idx mod 12` 计数器驱动，2843 句中仅 96 unique——单一计数器使槽位元组周期=bank 长度 12。

## 探针与操作

- 修复机制（source 0 seq 64/75，逐字编辑摘要）：
  1. 全局句索引做 **mixed-radix 分解**跨四个 12 元素 bank（units/12s/144s/1728s 位），四槽独立推进，组合达 12^4=20736 distinct 元组；
  2. 每槽 stride 取与 bank 长度**互质**（1,5,7,11），保证相邻两句四槽全变（段内不再只换主语）；
  3. 8 个主题域 × 固定不均匀段落长（4-7 句），全程无 RNG、确定性可复现。
- 机验（source 0 seq 70/78，tool_observed 逐字）：

```text
wrote default_prompt.json (chars=210442, sentences~2376, unique_sentences=2376/2376, est_tokens_per_sentence=18)
chat-wrapped full tokens = 44382
chat-wrapped truncated@32768 = 32768
within ...: unique_sentences=1755/1755 (100.0% unique)
```

## 机制与判别

- 机制：MoE 专家路由是 token 级函数，循环输入 → 路由分布退化 → profiling 里的 GroupedMatmul/专家负载统计不代表真实流量；输入多样性用「截断窗口内 unique 句占比=100%」机验收口（source 0 seq 54/79，agent_narrative 基于 verify tool_observed）。
- 判别（输出退化归因，source 0 seq 404/426，agent_narrative 基于实跑 tool_observed）：新输入下 32k greedy 输出**仍重复环**，但开头话题接地（呼应输入 voyage/ocean 主题）后塌缩；结合 2k 输入 EXACT 等价（W8A8 接入验证）双证 → 退化为**超长上下文 + greedy argmax 模式**，非 W8A8 bug、非输入循环伪影。
- 边界结论：输入 100% unique 是路由代表性的必要构造，不解决解码端退化；「可读连贯」尺子需采样/重复惩罚（超出锁定场景）。

## 验证信号

- 验证层次：tokenizer 机验（CPU）+ 16 卡 NPU 实跑（profiling run 确认使用新输入：日志 prompt 前缀=新句 "The wandering comet eclipsed..."、input_truncated_len=32768、dataset_path 指向新 inputs 目录）（source 0 seq 402-403，tool_observed）。
- profiler 侧印证：prefill op_statistic 的 GroupedMatmul（MoE GMM）以 296856us 居首，量化链完整（source 0 seq 409，tool_observed）。

## 适用与失效边界

- 适用：MoE 模型 profiling 输入构造；合成长文本的确定性生成（无 RNG 可复现）；「输入循环 vs 模型退化」的归因判别。
- 失效/风险：模板句的 token 分布仍非自然语料，专家路由分布接近但不等于真实流量；unique 句占比是输入侧指标，不能作为输出质量证明；混 radix 参数绑定 12 元素 bank 的本实现。

## 附：断言存档

- MoE 模型 profiling 输入须防循环退化：10 句×176 循环的复读输入使相同 token 反复路由到同几个专家，专家负载分布无代表性；确定性生成器要用 mixed-radix 跨四槽词库分解全局句索引（单计数器驱动四槽会以 bank 长度为周期重复，首版 2843 句仅 96 unique）+ 每槽互质 stride，机验截断窗口内 1755/1755 句 100% unique、truncated@32768==32768

```text
wrote ${PRIVATE_PATH_31} (chars=210442, sentences~2376, unique_sentences=2376/2376, est_tokens_per_sentence=18)
chat-wrapped full tokens = 44382
chat-wrapped truncated@32768 = 32768
within ${PRIVATE_IDENTITY_1}@${PRIVATE_HOST_1}: unique_sentences=1755/1755 (100.0% unique)
```
