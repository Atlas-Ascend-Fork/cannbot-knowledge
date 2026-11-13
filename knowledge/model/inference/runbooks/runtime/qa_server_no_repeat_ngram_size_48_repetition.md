---
{
  "type": "Runbook",
  "title": "NPU qa server 部署 no_repeat_ngram_size=48 消除整段块级复读",
  "description": "transformers generate 的 no_repeat_ngram_size 按 48 配置（模型级 NO_REPEAT_NGRAM 字典 + 请求级 req.no_repeat_ngram 覆盖，采样/非采样两分支同时生效）部署到 NPU qa server 后：qwen2.5-0.5b-instruct 复读复现题 19 段输出 0 个逐字重复段落、finish_reason=stop、435 tokens 自然收尾。",
  "tags": [
    "task.implementation",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# NPU qa server 部署 no_repeat_ngram_size=48 消除整段块级复读

## 适用场景

适用于 transformers + torch_npu 自建 QA/推理服务中，小参数量模型（qwen2.5-0.5b 级）出现整段块级逐字复读（生成内容大段重复直至 max_tokens 截断）的线上止血配置。


## 触发与观测
业务观测到模型对特定问题逐字重复整段内容（此前逐字重复 3 段）；服务为 sdpa 注意力 + MAX_PROMPT_TOKENS=28000 版本。

### 结论与证据边界

给 NPU qa server（sdpa + MAX_PROMPT_TOKENS=28000 基线版本）的 gen_kwargs 增加 no_repeat_ngram_size=req.no_repeat_ngram or NO_REPEAT_NGRAM.get(name, 48)（REP_PENALTY 行后新增 NO_REPEAT_NGRAM 字典、ChatRequest 增加 no_repeat_ngram 字段、采样分支 gen_kwargs.update 同步追加）并重启（pkill+setsid nohup，py_compile 通过）后，qwen2.5-0.5b-instruct 复读复现题（此前逐字重复 3 段）输出 19 段、逐字重复段落=0、finish_reason=stop、out_toks=435<4096 自然收尾。

## 探针与操作
重启后用固定 payload 复现题验证（curl → 解析 finish_reason/out_toks/逐字重复段落数），再跑两个回归（常识问答 + coder 代码生成）确认合法重复不受影响，tail 服务日志核对三条请求 status=200。

## 机制与判别
见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
    gen_kwargs = dict(max_new_tokens=req.max_tokens or MAX_NEW_TOKENS_DEFAULT,
                      do_sample=False,
                      repetition_penalty=req.repetition_penalty or REP_PENALTY.get(name, 1.05),
                      no_repeat_ngram_size=req.no_repeat_ngram or NO_REPEAT_NGRAM.get(name, 48))
```

### 补充机制片段

```
REP_PENALTY = {"qwen2.5-0.5b-instruct": 1.15, "qwen2.5-coder-0.5b-instruct": 1.05}
NO_REPEAT_NGRAM = {"qwen2.5-0.5b-instruct": 48, "qwen2.5-coder-0.5b-instruct": 48}
```

## 验证信号
复现题：19 段输出、verbatim-dup paragraphs=0、finish_reason=stop、out_toks=435<4096 自然收尾。

## 适用与失效边界
适用：greedy/采样两分支统一注入 no_repeat_ngram_size 的服务端配置（模型级字典默认 48 + 请求级覆盖）。48 的量级选择：远大于自然语言 n-gram 多样性、又足以阻断整段（数百 token）复制。局限：只治复读不治幻觉（该 0.5B 内容事实仍错）；单次重启后验证，未做长稳/多并发观测。
