---
type: Concept
title: vLLM Ascend ACLGraph：捕获桶、参数更新与重放时序
description: 按ACLGraph中英文设计核对wrapper与上游dispatch分工、当前流/更新流顺序和full attention参数刷新，区分地址、指标与正确重放。
tags:
- task.design
- topic.graph_execution
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/ACL_Graph.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/ACL_Graph.po
  role: supporting
created_at: '2026-10-29T11:00:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T05:23:56Z'
---

# vLLM Ascend ACLGraph：捕获桶、参数更新与重放时序


## 范围与角色

固定 Ascend ceac1a2b 与 vLLM v0.32.0 基线。本文蒸馏默认 ACLGraph 包装路径，不涵盖 Xlite 等独立实现；设计没有为本卡给出完整硬件范围，平台待确认，保持 draft。模式选择见[图优化流程](../../guides/optimization/vllm_ascend_graph_mode_selection.md)。

NPUPlatform.get_static_graph_wrapper_cls 选择 ACLGraphWrapper。上游先决定运行时图模式和 batch_descriptor；wrapper 按 descriptor 保存捕获对象，首次符合条件时捕获，后续同桶重放，不属于该图路径时执行原 callable。capture sizes 有限，超过最大桶的请求可回到 eager；不同桶不是同一张任意动态图。

## 动态内容必须进入已捕获任务

输入 tensor 地址、workspace 和事件等长寿命资源需要与捕获图一致。full attention 捕获保留 task handles、ExternalEvent 与 workspace/弱引用等；重放前 update_full_graph_params 调用 backend.update_graph_params，在 update stream 的 graph_task_update_begin/end 区间更新任务，事件协调更新和计算。

更新输入 tensor 的内容与更新捕获任务的参数是两件事。新增 attention backend 若只完成 capture 而没有对应参数更新钩子，下一批可能继续消费旧的长度、地址或元数据。不能将首次 forward 正确当作重放正确。

设计描述的通用 wrapper 在 replay 前同步当前流，配合更新流与事件顺序，防止第 i 次迭代的更新被仍在运行的第 i-1 次图观察到。主 Runner 的 full-graph/Eagle 优化路径另有细化顺序，不能把通用同步机械删去或推导所有路径都具有同一同步点。地址检查报错时先排查 tensor 重新分配和引用生命周期，不能关闭断言后继续宣称支持图。

## 桶和资源也是适配契约

piecewise 捕获数随分段数量与桶数量共同增长。stream resource pruning 会降低可捕获容量；扩大 capture sizes 可能在启动时耗尽资源。encoder-decoder、Attention 能力和平台配置可改变最终有效模式；capture 日志与请求参数不是同一个证据。

适配验收至少覆盖首次捕获、同桶多步、跨桶、长度/slot/block-table 变化、混合批、超桶 eager 和并发流，比较 eager 的 token/精度与图执行统计。可打开 cudagraph metrics 观察实际桶与 fallback，再评估启动时间、显存和稳态收益。本次只读设计，未运行捕获、参数更新或性能实验。


## 中文设计、当前流与诊断信号

ACL_Graph.po的47条有效译文均匹配当前英文。vLLM拥有通用dispatch/batch descriptor，平台wrapper负责捕获和重放这一分工不因中文“封装器”而改变；wrapper不自行重新决定上游调度策略。设计覆盖的是机制，不是所有attention backend、Runner、硬件和并发组合的实现闭包。

设计的公共路径明确在replay前同步当前流。它与backend的update stream及ExternalEvent协作，不等于所有路径都显式同步同一个update stream，也不支持删除同步或只检查Python调用顺序。第i步参数被第i-1步观察、或第i步replay先于自己的更新，均可能出现旧长度/元数据、错误结果或挂起；主full-graph Eagle窄路径仍需独立核对。

CLI可用`--cudagraph-metrics`并保持log stats开启；Python对应cudagraph_metrics=True、disable_log_stats=False。指标/日志、profiler重放、debug地址断言分别提供不同信号。地址相同不证明内容/长度已正确刷新，指标出现不证明每请求都走目标桶，临时print也不能替代最终正确性与性能对照。

更小capture集合、平台过滤、模式规范化与已识别资源错误建议不代表自动重试/全资源回收；精确RuntimeError文本识别见[FAQ诊断](../../guides/bringup/vllm_ascend_faq_diagnostic_boundaries.md)。本次完成设计/译文静态核对，未新增backend实现或运行图捕获。
