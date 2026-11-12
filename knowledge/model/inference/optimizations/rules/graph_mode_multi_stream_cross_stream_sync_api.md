---
type: Optimization
title: 图模式多流跨流同步：GE 单流冲突、控制边与显式 Event
description: 图模式多流并行的跨流同步：GE 控制边、wait_tensor 与 npugraph_ex Stream/Event、record/wait、record_stream；核对旧 aclgraph tagged-event 替代路径、enable_single_stream 单流冲突、动态开关、enable_inner_parallel 与控核版本边界。
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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/ascend_ir_multi_stream.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/ascend_ir_limit_cores.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/npugraph_ex_multi_stream.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/npugraph_ex_limit_cores.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/api-routing.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-11-10T02:01:56Z'
platforms:
- agnostic
---

# 图模式多流跨流同步：GE 单流冲突、控制边与显式 Event

## 当前 API 选择

先确认生产者、消费者和汇合点，再选择对应后端的同步方式。GE以逻辑stream标签和npu_wait_tensor控制边表达顺序；eager/npugraph_ex使用稳定的torch.npu.Stream/Event对象，显式record/wait。当前stream_utils已统一分派：create_stream在GE返回标签，其他模式创建Stream；npu_stream_switch按exe_mode选择scope或torch.npu.stream。

旧tagged-event/enable_aclgraph示例已从当前操作配方撤下。npu_stream_switch_gegraph仍是专用GE入口，不能将字符串标签传给需要真实Stream对象的分支。

## 顺序与生命周期分别核对

Event确保执行先后；record_stream通知分配器张量在消费流仍然存活，二者不能互代。副流消费主流输入前建立等待和生命周期登记，主流消费副流结果前再等待完成。对象应在捕获前创建、重复replay保持有效，不能每步随意重建事件。

当前record_event/wait_event/record_stream在非GE路径使用原生对象；GE控制边由模型对应helper建立。helper有条件开关与返回约定，调用方需读取真实接口，不复制旧伪代码后忽略返回值。

## 控核与跨步依赖

先完成正确性，再评估控核。limit_core_num按npugraph_ex或GE分派，eager为空上下文；核数与算子支持仍按硬件核对，分流存在不保证可并行或有收益。

如果replay读取另一更新流产生的参数，应等待该更新流的完成事件；仅同步当前流不会覆盖尚未建立的跨流依赖。同步范围应匹配真实依赖，既不无依据地全设备同步，也不在缺少更新顺序时任意收窄。

## GE 多流开关与参数边界

以下是固定 Recipes `944d2d3ece86f7df33dbb0cb155c72ca619a9c66` 内 TorchAir 文档副本的接口语义；该副本没有独立 TorchAir revision，部署时仍应核对安装后端的同版 API。它描述软件接口，不证明任意产品、模型或负载已支持/验证。

| GE 项目 | 固定来源中的语义 |
| --- | --- |
| torchair.scope.npu_stream_switch | 为 with 范围指定逻辑 stream_tag；相同 tag 表示同一逻辑流 |
| stream_priority | 流调度优先级，参考默认值0；不能据此承诺独占核或严格抢占 |
| enable_inner_parallel | 默认 True，允许 tag 流内部继续使用 GE 原有并发策略；不是整个模型的多流总开关 |
| enable_single_stream | 静态 Shape 的单流执行功能与此 GE 多流表达冲突，不能同时启用 |
| ENABLE_DYNAMIC_SHAPE_MULTI_STREAM | 固定文档的动态 Shape 自动多流环境开关，值1启用；显式 GE 多流表达优先级更高 |
| stream-fusion=1 | SuperKernel 内的流融合选项；固定文档建议按 SuperKernel 范围配置，不能把普通切流标记等同于 scope 内融合 |

默认单流的动态 Shape 场景与已显式标定 stream 的场景要分开。设置环境变量不证明所有独立分支都已物理并行，仍须检查编译图和同一次 profiling 的时间线。

## GE 与 npugraph_ex 控核的差异

| 项目 | GE | npugraph_ex |
| --- | --- | --- |
| 控制粒度 | 算子级 scope 和全局 session 配置 | Stream 级最大核数 |
| 局部入口 | torchair.scope.limit_core_num | torch.npu.npugraph_ex.scope.limit_core_num |
| 全局入口 | config.ge_config.aicore_num，字符串 Cube数\|Vector数 | 不把 GE session 选项当作本后端配置 |
| 优先关系 | 算子级高于全局核数 | 按所属 stream 的上限执行，核数不保证全部使用 |
| 检查入口 | 图属性 _op_aicore_num / _op_vectorcore_num 和 GE 日志 | kernel_details.csv 的 Block Num / Mix Block Num |

op_aicore_num 范围为 `[1,max_aicore]`，有独立 Vector Core 时 op_vectorcore_num 为 `[1,max_vectorcore]`；仅有 AI Core 的产品按来源允许 Vector 参数0。最大值从实际 SoC 配置 `ai_core_cnt`、`cube_core_cnt`、`vector_core_cnt` 核对，示例24/48不作为所有设备的常量。

固定 npugraph_ex 文档还规定：仅对 Ascend C 算子控核；通信算子只支持 AI Vector 控核。非支持算子混入 microbatch 多流可能使控核无效或产生等待问题；不支持多个线程并发设置同一流核数。对于文档覆盖的 `CANN <= 8.5.0`，静态 Kernel 编译与控核同时开启时优先保证控核，静态 Kernel 编译失效。这条结论不得外推到后续未核对的 CANN 版本。

### 组合约束的判定矩阵

| 场景 ID | 判定 | 解释 |
| --- | --- | --- |
| ge_static_single_and_multi | forbidden | 固定文档不支持静态单流执行功能与 GE 多流表达同时开启 |
| ge_dynamic_auto_and_explicit | explicit | 显式 stream 标定优先于动态 Shape 自动多流开关 |
| ge_local_and_global_cores | local | 算子级核数配置优先于 session 全局配置 |
| npugraph_non_ascendc | unsupported | 固定文档只覆盖 Ascend C 控核，不推广到其他实现 |
| npugraph_same_stream_threads | unsupported | 不支持多个线程并发设置同一流核数 |
| npugraph_static_and_limit_cann_le_8_5 | limit_core_num | 控核优先，静态 Kernel 编译失效 |
| npugraph_static_and_limit_newer | unknown | 未用旧文档推断更高版本的组合行为 |

历史 tagged 名称包括 `torchair.ops.npu_record_tagged_stream`、`torchair.ops.npu_tagged_event_record`、`torchair.ops.npu_tagged_event_wait` 以及 `torch.npu.npugraph_ex.scope.npu_tagged_event_record` / `torch.npu.npugraph_ex.scope.npu_tagged_event_wait`。旧 `npu_stream_switch_npugraph` helper 也不能当作当前统一函数签名；当前应按 stream_utils.py 的 npu_stream_switch 和 create_event/record_event/wait_event 分派。

旧路由表中的 `torch.npu.get_stream_limit` / `torch.npu.set_stream_limit` 和 tagged-event 名称是版本相关入口。当前统一 helper 的实际分派以固定 stream_utils.py 为准；不能把旧 tagged 调用或原生资源设置函数替换成不同语义的 scope，未经版本核对不提供可执行迁移配方。

## 验证与回退

覆盖单流/多流、主/draft、重复replay和张量释放；比较输出、事件顺序与时间线，确认没有早释放或等待环。性能无净收益或精度失败时回到合法单流配置。旧PR中的特定流号或hang根因不自动成为当前复现结果，本次未运行设备实验。

- [LongCat当前案例](../cases/longcat_a3_afd_stream_pairing.md)
- [多流生命周期故障](../../runbooks/runtime/multistream_cross_stream_tensor_lifetime_clone.md)


## Evidence

- [multi_stream_principles.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/cann/zh/multi_stream_principles.md)（primary）
- [stream_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/stream_utils.py)（implementation）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（supporting）

- [.agents/skills/model-infer-multi-stream/references/ascend_ir_multi_stream.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/ascend_ir_multi_stream.md)（supporting）

- [.agents/skills/model-infer-multi-stream/references/ascend_ir_limit_cores.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/ascend_ir_limit_cores.md)（supporting）

- [.agents/skills/model-infer-multi-stream/references/npugraph_ex_multi_stream.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/npugraph_ex_multi_stream.md)（supporting）

- [.agents/skills/model-infer-multi-stream/references/npugraph_ex_limit_cores.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/npugraph_ex_limit_cores.md)（supporting）

- [.agents/skills/model-infer-multi-stream/references/api-routing.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/api-routing.md)（supporting）
