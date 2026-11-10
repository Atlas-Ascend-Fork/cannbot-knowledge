---
type: Runbook
title: vLLM DSpark 排障：区分主模型与 draft 图开关
description: 从开发快照核对 base proposer 的 speculative eager 门控和 DSpark 子类回退，避免把配置或中间赋值误报为最终启图。
tags:
- task.debugging
- topic.graph_execution
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-10-29T07:47:19Z'
updated_at: "2026-10-29T07:47:19Z"
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM DSpark 排障：区分主模型与 draft 图开关

## 适用场景

在 vllm-ascend 的 Kimi/DSpark 适配开发中，排查“主模型已配置图模式，但 draft 是否真正启图”。本卡来自一次真实修改、读取源码与回退讨论的轨迹，只记录捕获到的开发快照；没有完成设备部署与性能验收。硬件型号、依赖版本和可固定的源码提交未确认，保持 draft、未知平台，不作为所有 vLLM 版本的接口规范。

## 触发与观测

仅看主模型启动参数或 base 类的一次赋值，无法覆盖实际 proposer 子类的后续修改。轨迹中的源码读取工具在 `llm_base_proposer.py` 返回了如下完整赋值表达式：

```python
self.use_cuda_graph = self.runner._use_aclgraph() and not self.speculative_config.enforce_eager
```

## 探针与操作

先定位部署版本实际加载的 proposer 类及其继承链，读取 base 的图开关计算，再读取 DSpark 初始化中后续写入 `self.use_cuda_graph` 的分支。以下是该轨迹工具读取到的完整回退条件块，保留原始行号：

```text
78:         if self.use_cuda_graph:
79:             unsafe_reason = None
80:             if self.speculative_config.draft_sample_method == "probabilistic":
81:                 unsafe_reason = "draft_sample_method='probabilistic'"
82:             elif self.dynamic_spec is not None:
83:                 unsafe_reason = "dynamic spec decoding"
84:             if unsafe_reason is not None:
85:                 logger.warning_once(
86:                     "%s is not supported by DSpark draft ACL graphs; falling back to eager drafting.",
87:                     unsafe_reason,
88:                 )
89:                 self.use_cuda_graph = False
```

读取源码是本次真正完成的探针；启动服务、采集最终开关、分别比较 target/draft eager 与图路径属于后续验收步骤，本次未执行。不要直接运行来源轨迹中的远程命令或复制其中机器路径。

## 机制与判别

该开发快照先在 base proposer 合并 runner 与 speculative_config 的图开关，DSpark 子类随后还会按采样方式和动态调度条件回退。

base 表达式同时依赖 `runner._use_aclgraph()` 和 `speculative_config.enforce_eager`。子类在已启图时，若 `draft_sample_method == "probabilistic"` 或 `dynamic_spec is not None`，会记录回退原因并把 draft 的 `use_cuda_graph` 改为 False。这里确认的是源码中的门控，不是这些模式已经完成运行验证。

因此分别记录主模型配置、speculative 配置、实际 proposer 类型、base 计算值和子类最终值。不能因为 base 值为真就声称 draft 一定走图；也不能反向声称主模型的 eager 设置完全不影响 draft，因为表达式仍依赖 runner。

## 验证信号

- 源码读取工具返回 base 的完整布尔表达式，证实 speculative 的 eager 条件参与 draft 开关计算。（来源平台：未确认；证据等级：tool_observed；源码结构观测）
- 同轨迹源码读取工具返回 DSpark 条件块，证实该快照对概率采样或动态调度存在后续回退。（来源平台：未确认；证据等级：tool_observed；源码结构观测）

以上没有证明图捕获成功、输出精度正确或有性能收益，也没有把源码注释当作已完成的设备测试。

## 适用与失效边界

只适用于具有上述 base 表达式和 DSpark 回退块的开发版本。轨迹中存在不同阶段的源码和回退操作，不能把某次读取外推为最终部署状态。使用前固定实际版本并复核加载路径；后续分别记录 capture/replay、输出精度及目标负载指标，再决定是否启图或回退。GLM、其他 draft 方法和其他版本不自动继承本卡边界。
