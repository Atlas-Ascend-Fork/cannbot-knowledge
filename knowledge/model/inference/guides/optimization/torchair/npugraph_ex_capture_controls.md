---
type: Guide
title: npugraph_ex 捕获控制：次数上限、Eager 定界和跳过校验
description: 区分发布版已有的 fallback 控制与主线强制重捕获、unsafe 跳过检查的约束和优先级。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/capture_limit.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/force_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/force_recapture.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/unsafe_skip_npugraph_capture_validation.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/capture_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/quick_start.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/force_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/host_tiling_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/ScreenShot_20260209203104.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npugraph_ex 捕获控制：次数上限、Eager 定界和跳过校验

## 版本与范围

发布文档固定在 ascend_26_0_pt28 的 TorchAir 子模块提交 7c6c754bed00c86ffaaa2a45cb7ac2724f058013；主线补充固定在 92e1e967bd35ebc37a442b4a969730bf3cf77a3c。以下分开说明，未做 NPU 运行验证。 发布段选择A2/A3推理，主线950的受支持控制路径见后文。主线 force_recapture 和 unsafe_skip_npugraph_capture_validation 在本次固定发布快照中没有对应功能页，不能据此宣称 26.0 支持；实际安装还需核对接口与实现。

## 发布版：次数与 Eager

capture_limit 默认 64，范围 1 到 9223372036854775807，按每个 FX 图/子图限制不同 shape 的重捕获；超限后该图后续执行回退 Eager。stream/event/memory 资源可能在达到上限前耗尽，因此调大上限不保证能捕获更多图。

force_eager=True 保留 npugraph_ex 的 IR 变换等流程，以 Eager 执行 FX 图，跳过 aclgraph Capture/Replay，用于区分图变换与运行器问题；不是完全移除编译前端。发布文档只列明与 inplace Pass、静态 Kernel、编译缓存、多流表达的组合支持，不把任意 options 都视为可叠加。

## 主线：强制与跳过

force_recapture=True 每次重新捕获，用于观察旧图复用是否引入问题，有额外开销。unsafe_skip_npugraph_capture_validation=True 则让 replay 前 is_need_to_recapture 直接返回 False，连 force_recapture、mutated input 地址、stream Cube/Vector 限核检查都跳过；两者同时开启时 unsafe 选项优先，强制重捕获不生效。

该 unsafe 选项不改变 graph key、图选择或实际 capture/replay，所以不是禁止所有首次捕获，也不自动消除多 shape 图。每张已捕获图的 mutated input 地址与流限核必须保持稳定。先保持默认 False，用真实负载检查 TORCH_COMPILE_DEBUG=1 的 debug.log，三个 recaptures caused by ... 计数持续为 0 才能进一步评估；首次捕获打印 0 不足以证明整个生命周期稳定。

## 验证

比较 fallback、强制重捕获与默认 Replay 的数值和捕获日志，故意更换缓存地址或流限核属于能使 unsafe 假设失效的场景。未做设备实验，不将这些开关当作默认性能配置。

- [输入和输出存储](npugraph_ex_memory_pool_and_clone.md)


## 主线补充：计数范围与诊断顺序

固定主线明确 capture_limit 按同一 FX 图/子图的 shape 变化分别计数；dynamic=True 或 dynamic=None 被判断为动态时可共用 FX 图并捕获多种 shape。dynamic=False 的固定 shape 正常不触发这类重捕获，不应把它当作全模型、全进程或全部地址变化的统一次数预算。主线 CAP=2 示例在第三种 shape 时回退；阈值边界应核对实际 reached 告警及 debug.log，不用措辞“超过”自行推算还可捕获几次。

先用 aot_eager/原生 Eager FX 核对前端与算子，再比较 npugraph_ex force_eager：若 force_eager 仍失败，继续检查前端图、Pass 与模型；若它正常而普通路径失败，才把重点移向 Capture/Replay。然后用 force_recapture 比较，可作为输入输出存储复用问题的线索。上述差分结果用于缩小范围，不唯一证明 Runtime 或某个内部模块有缺陷。

## 主线force_eager与Host Tiling更新依赖

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的force_eager页仍只列FX inplace Pass、静态Kernel、编译缓存和多流表达可配套；默认False使用aclgraph，True以变换后的FX Eager执行但不Capture/Replay。不能由某个options被接收便推导所有增强功能在force_eager中仍生效。

同一主线Host Tiling附录与时序图描述类FIA算子的更新协议：Capture记录需更新参数的算子并插入event wait；Replay调用后下发更新参数的算子，再以event record使replay stream等到对应更新完成。图中的update stream与replay stream按各层record/wait衔接，不是把Host计算视为图内无成本任务。

其目标是根据实际actual_seq_len刷新Tiling并减少调度间隙，只有支持这条更新协议的算子才适用；不是所有动态控制流、Python长度计算或任意Kernel参数都自动可刷新。这个时序示意不是手动创建几个Event即可替代框架Capture/Update协议的完整实现。应按实际路径检查参数、等待和执行顺序，再测关键路径，不凭图示宣称已经完全掩盖Tiling开销。

主线总览的950控制功能范围仅用于相应受支持路径，发布段和具体Attention参数支持仍按独立版本契约。本文未运行重捕获、异步更新或设备实验。

## 独立包静态编译与调试产物的边界

固定主线独立npugraph_ex的run_eagerly_compile按sym_input_index组成的符号值元组及可选范围去重；代码先登记该元组再调用静态编译，所以集合出现某shape不能独立作为编译成功或异常后必定自动重试的证明。force_eager仍是变换后FX的差分定界，不把它当原始模型逐层Eager基准。

独立实现的Debug根目录为npugraph_ex、低层compile_fx用compile__N，和设计说明中的torchair/model__N泛化路径不同；按[独立包草稿](npugraph_ex_standalone_design_contracts.md)核对导入时机、rank及phase。阶段为线程局部不保证全局模型计数/文件序号线程安全，也不把未生成某个文件当无错误或无重捕获。本文未开启采集/编译或读取缓存。

## 快速页归因语句的版本修正

发布quick_start把force_eager正常时的归因方向写反；主线已改成force_eager异常时先怀疑npugraph_ex变换路径，否则再看aclgraph。两者都只是排查线索，正常只能把重点缩到Capture/Replay及其内存处理，不能唯一证明Runtime故障。主线force_recapture的结果同样只辅助区分捕获执行与输入输出复用，不作为独立根因证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/capture_limit.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/force_eager.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/force_recapture.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/unsafe_skip_npugraph_capture_validation.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/capture_limit.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/quick_start.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/force_eager.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/host_tiling_update.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/ScreenShot_20260209203104.png)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_transform_observer.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/core/utils.py)（implementation）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md)（constraint）
