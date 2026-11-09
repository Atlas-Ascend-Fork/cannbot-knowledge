---
type: Guide
title: vLLM Ascend 请求探针与多模态断言合同
description: 解释 send_request 与 send_mm_request 的 token 预算、HTTP 行为、图像装载和断言边界，帮助 Agent 将探针输出与服务质量证据分开。
aliases:
- send_request
- send_mm_request
- resolve_prompt
- validate_response
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/send_request.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/send_mm_request.py
  role: constraint
created_at: '2026-11-03T05:37:19Z'
updated_at: '2026-11-03T05:37:19Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 请求探针与多模态断言合同

## 适用范围

固定 Main 源码中的两个请求工具只提供特定输入与断言。未在此执行 HTTP、下载模型/图像或启动服务；这些工具的成功不是所有硬件、模型和多模态任务的质量结论。

## 文本、聊天与 token 预算

`tools/send_request.py` 的 `/tokenize` 请求有 60 秒 timeout 并调用 raise_for_status；实际 completions/chat 请求没有同样的 timeout 或 raise_for_status，只打印状态后解析 choices。因此连接成功、打印状态码、返回 JSON 与服务通过是不同证据。

- 自动构造目标 token 数时，对 seed 重复和追加 `a` 做二分/填充，隐含 tokenizer 计数随文本长度单调的假设；target 不大于 seed 计数时直接返回 seed，不截断到目标。字典形式的 seed/target 也不能替代完整的正整数校验。
- 聊天模式可通过探针估计消息包装开销；估计失败回退 0。只有开销大于 0 的分支记录 actual token 数，因此自动生成 prompt 不总意味着实际 prompt 长度已被精确验证。
- request_args 可以覆盖原 payload 的 model、prompt、messages；指定 expected completion_tokens 时又强制 min_tokens=max_tokens。审计要看最终 payload，不能只看命令行默认值。
- expected 为空时 `validate_response` 直接返回，因此单独提供 max_model_len 不会触发该函数的长度断言。expected 存在时只对明确给出的 prompt_tokens/completion_tokens 精确比较，并检查两者之和不超过预算；没有独立核对 usage.total_tokens。
- completions 要求 text 非空；chat 可接受 content 或 reasoning 任一非空。这是输出存在性检查，不是答案正确性。

## 图像来源与多模态断言

`tools/send_mm_request.py` 的图像来自显式路径、MM_IMAGE_PATH 或默认下载路径。file:// 会去掉前缀；某些不存在的带斜杠路径还会被当作数据集仓库名。HF_HUB_OFFLINE 传给 ModelScope 的 local_files_only，但不能据此宣称整个请求链路已离线运行。

消息中的 `{IMAGE_i}` 替换为图像 data URI，HTTP 地址保留，其他非 HTTP 项按本地文件读取；已经是 data URI 的字符串并不保证幂等处理。编码前缀固定 image/jpeg，真实文件也可能是 PNG，应保留实际图像字节与 MIME 以复现。

默认 EOS=[1,106]、pad=0、top_k=64、top_p=0.95、max_tokens=8192、stream=False，是脚本默认探针参数，不是所有 tokenizer/模型的适配建议。api_args 后更新，可覆盖默认值以及 model/messages。

状态码只在 expected.status_code 指定时断言。默认要求 content 非空，reasoning-only 响应与文本工具的接受条件不同；content_contains 为大小写敏感的子串匹配，最小/最大长度按 Python 字符数计算，不是 token 数。常规请求没有显式 timeout 或 raise_for_status。

## Agent 如何收集可复核的结果

保存最终 URL、payload（处理凭据）、模型/模板/tokenizer 版本、图像原始字节摘要、HTTP 状态、原始响应和每项断言结果。将 token 预算、内容存在性、子串检查和独立质量评测分别记录；补充 tokenizer 实际计数与模型专用期望输出，再判断适配是否满足需求。脚本默认参数和单次通过不构成精度、吞吐、尾延迟或跨模型覆盖证明。
