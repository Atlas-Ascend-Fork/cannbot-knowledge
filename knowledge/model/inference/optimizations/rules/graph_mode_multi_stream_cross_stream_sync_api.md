---
type: Optimization
title: 跨流同步规则：GE 控制边、显式 Event 与历史 tagged API
description: 图模式多流并行的跨流同步：GE 控制边、wait_tensor 与 npugraph_ex Stream/Event、record/wait 及 record_stream；说明旧 aclgraph tagged-event API 的替代路径。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/cann/zh/multi_stream_principles.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/stream_utils.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T16:00:26Z'
platforms:
- agnostic
---

# 跨流同步：按执行后端表达依赖

## 当前 API 选择

先确认生产者、消费者和汇合点，再选择对应后端的同步方式。GE以逻辑stream标签和npu_wait_tensor控制边表达顺序；eager/npugraph_ex使用稳定的torch.npu.Stream/Event对象，显式record/wait。当前stream_utils已统一分派：create_stream在GE返回标签，其他模式创建Stream；npu_stream_switch按exe_mode选择scope或torch.npu.stream。

旧tagged-event/enable_aclgraph示例已从当前操作配方撤下。npu_stream_switch_gegraph仍是专用GE入口，不能将字符串标签传给需要真实Stream对象的分支。

## 顺序与生命周期分别核对

Event确保执行先后；record_stream通知分配器张量在消费流仍然存活，二者不能互代。副流消费主流输入前建立等待和生命周期登记，主流消费副流结果前再等待完成。对象应在捕获前创建、重复replay保持有效，不能每步随意重建事件。

当前record_event/wait_event/record_stream在非GE路径使用原生对象；GE控制边由模型对应helper建立。helper有条件开关与返回约定，调用方需读取真实接口，不复制旧伪代码后忽略返回值。

## 控核与跨步依赖

先完成正确性，再评估控核。limit_core_num按npugraph_ex或GE分派，eager为空上下文；核数与算子支持仍按硬件核对，分流存在不保证可并行或有收益。

如果replay读取另一更新流产生的参数，应等待该更新流的完成事件；仅同步当前流不会覆盖尚未建立的跨流依赖。同步范围应匹配真实依赖，既不无依据地全设备同步，也不在缺少更新顺序时任意收窄。

## 验证与回退

覆盖单流/多流、主/draft、重复replay和张量释放；比较输出、事件顺序与时间线，确认没有早释放或等待环。性能无净收益或精度失败时回到合法单流配置。旧PR中的特定流号或hang根因不自动成为当前复现结果，本次未运行设备实验。

- [LongCat当前案例](../cases/longcat_a3_afd_stream_pairing.md)
- [多流生命周期故障](../../runbooks/runtime/multistream_cross_stream_tensor_lifetime_clone.md)


## Evidence

- [multi_stream_principles.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/cann/zh/multi_stream_principles.md)（primary）
- [stream_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/stream_utils.py)（implementation）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（supporting）
