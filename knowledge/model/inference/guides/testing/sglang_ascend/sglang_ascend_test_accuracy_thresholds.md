---
type: Guide
title: SGLang NPU端到端精度门槛、EvalScope结果解析与重试
description: 说明AIME/GPQA按允许错题数放宽、其他数据集0.99相对阈值、首数据集决定策略以及报告JSON优先和百分号归一化。
tags:
- task.testing
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/test_npu_accuracy_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/run_evalscope.sh
  role: implementation
created_at: '2026-11-08T12:20:21Z'
updated_at: '2026-11-08T12:20:21Z'
platforms: []
---

# SGLang NPU端到端精度门槛、EvalScope结果解析与重试

数据集策略按datasets[0]决定。AIME25/26共30题允许波动2题，门槛baseline-2/30；GPQA Diamond198题允许5题，门槛baseline-5/198。其他数据集用baseline×0.99；GSM8K虽然允许重试表有3，缺题数表条目，阈值仍走相对容差。多数据集调用不能把首项策略当每项分别计算。

AIME/GPQA/GSM8K默认最多3次，其他1次，类max_retries可覆盖；循环保留最高accuracy，达到门槛提前结束。assert_metrics要求metrics存在，accuracy baseline非None时取实际accuracy并比较，不以日志进程启动代替得分。

run_evalscope调用/v1/chat/completions并保存工作目录，优先解析日志Dump report to指向JSON的score，再用兼容多版EvalScope的日志正则，百分号存在才除100。未知格式可能缺accuracy，不能把空字典或不带%但采用百分尺度的结果自动当正确。比较前保留原始报告与工具版本。

run_evalscope.sh优先复用系统或虚拟环境中可导入的evalscope，否则创建环境安装；它不固定单一EvalScope版本，限制aiohttp/httpx范围并设安装1200秒超时。源码固定不意味着grader、模板或依赖完全固定，复现应另外锁定环境。

本卡是上游测试合同与解释，不给出本次实测accuracy。应同时报告未放宽baseline、最终门槛、各次分数、样本和采样配置，跨harness数值不能直接排序。
