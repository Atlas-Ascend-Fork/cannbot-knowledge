---
type: Runbook
title: vLLM Ascend Balance：调度副本漂移与测试 skip 的证据边界
description: 在 release pin 升级后静态对照 BalanceScheduler 与 Scheduler，识别缺失的新参数/字段以及漂移测试
  skip 不能证明兼容的情况。
tags:
- task.debugging
- topic.model_serving
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_balance_schedule.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/balance_schedule_refactor.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/sched/scheduler.py
  role: constraint
created_at: '2026-10-29T11:00:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:06:20Z'
---

# vLLM Ascend Balance：调度副本漂移与测试 skip 的证据边界


## 触发、范围与现有观测

升级 vLLM 后仍启用 BalanceScheduler 的 schedule 副本，出现构造/调用参数不匹配、SchedulerOutput 字段变化，或测试看似通过却没有实际覆盖新调度语义。固定 Ascend ceac1a2b 的 .github/vllm-release-tag.commit 为 v0.32.0，对应上游5df63a7203cdb9328d824a27b682e77c7b9928be。平台未知，保持 draft。

本次只解析这两个固定版本的 Python AST，未 import 或执行上游代码：v0.32.0 的 schedule 有 input_budget/draft_slots、额外 encoder 返回项与新的 SchedulerOutput 数据，而 Ascend 副本仍有不同调用和输出构建。差异超出 disabled early return、balance gate、waiting queue check。这个观测说明仍需逐项兼容审查，不能仅由差异断言每种运行配置都会失败。

## 不把测试名称当结果

源码 test_schedule_body_matches_pinned_release_tag 在 pin 不可获取时 skip；若 ours!=theirs 或 installed!=theirs 也 pytest.skip。因而测试没有 fail 不代表副本与 pin 对齐。signature/三处意图锁测试约束局部契约，不能替代完整语义与调用形状兼容；测试源码存在也不代表本次运行过。

## 可复现探针

从固定仓读取 release pin，并用 git show <固定commit>:vllm/v1/core/sched/scheduler.py 提取源码；记录真实安装 vLLM 的 commit，而非只看版本字符串。用 ast.parse 提取两类的 __init__/schedule，先比较参数、默认值及调用，再仅剥离审定的 balance 差异后比较函数体。

对 diff 逐项核对 KV 预留/释放、encoder 五项返回、speculative input budget、prefix cache、暂停/抢占和 SchedulerOutput 字段。记录语义差异清单，禁止为使比对相等而剥离全部不同节点。design 文档旧 pin 不能覆盖 CI pin 的实际值。

## 修复与退出条件

在框架适配分支用新 pin 的实现重新应用最少 balance 变化，或使用已经提供的上游扩展点；同时保持[全组 gather 调用点](vllm_ascend_balance_wave_collective_timeout.md)。运行开/关、无请求、SRF、encoder、异步KV、投机、暂停和抢占等实际触发分支，核对真实 skip 原因及结果。

兼容审查未完成时不把该组合列为推荐已验证路径；回退到原有已验证版本对/关闭策略并重启进程。本次没有修改上游、运行其 pytest 或复现设备错误。
