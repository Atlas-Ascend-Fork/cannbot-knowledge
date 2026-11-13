---
{
  "type": "Runbook",
  "title": "Qwen3 reasoning parser 回归门禁：字段拆分不等于最终答案通过",
  "description": "来源把 reasoning 与 content 合并匹配后报告 20/20；这种判据可能让思考中出现正确词、最终答案却错误的样本通过。因此只保留字段/预算诊断，撤回据此证明 storm 正确率恢复的结论。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Qwen3 reasoning parser 回归门禁：字段拆分不等于最终答案通过

## 适用场景

启用 vLLM reasoning parser 后客户端门禁由通过变成失败，需要区分字段位置、输出预算与最终答案语义。

## 触发与观测

来源旧门禁报告 storm 11/20。单独请求显示该版本思考文本在 `message.reasoning`，最终回答在 `content`；字段拆分可解释客户端为什么看不到预期字段，但不自动解释所有失败。

## 探针与操作

分别保存 reasoning、content、finish_reason、实际 token 用量及失败样本。答案正确性只依据应交付的最终 content；reasoning 可作诊断材料。输出预算改变后应重新跑相同样本，不能通过把思考过程也纳入关键词匹配来证明回答正确。

## 机制与判别

旧判据、合并字段以及增加 max_tokens 同时改变，无法单点归因。合并字段后有正确关键词，仍可能是“reasoning=4、content=5”的错误最终回答；这说明旧通过条件太弱，而不是服务必然正常。下列为来源旧输出，仅保留为历史弱判据的观测：

````text
UP
warm ok
=== 1. content/reasoning 拆分 ===
reasoning_content len: 0 | head:
content: '\n\n2'
=== 2. 工具调用仍正常 ===
tool_calls: True
=== 3. storm ===
RESULT: 11/20 pass, 9 errors
=== 4. 吞吐 ===
completed: 12/12  total tokens: 1164  wall: 11.5s
median step (concurrent): 108 ms
aggregate throughput: 101.6 tok/s
````

````text
warm ok
=== PROD final: storm x2 ===
RESULT: 20/20 pass, 0 errors
RESULT: 20/20 pass, 0 errors
=== tool ===
tool_calls: True
````

````text
=== gate round 2 ===
gate round2: 20/20 pass
=== tool ===
tool_calls: {'name': 'get_weather', 'arguments': '{"city": "杭州"}'}
=== bench ===
completed: 12/12  total tokens: 1162  wall: 11.5s
median step (concurrent): 108 ms
aggregate throughput: 101.4 tok/s
````

## 验证信号

20/20、工具调用与约 101.4 tok/s 均是来源弱门禁下的结果；不据此宣称最终答案正确率或吞吐无回退。没有按修正后的最终 content 语义判据复测的记录。

## 适用与失效边界

该卡是验收判据负例与字段诊断，不是性能改善或服务修复证明。256/512 token 是来源所选预算，不是所有问题的通用充分下限；遗留回声/异常符号输出也尚未定因。
