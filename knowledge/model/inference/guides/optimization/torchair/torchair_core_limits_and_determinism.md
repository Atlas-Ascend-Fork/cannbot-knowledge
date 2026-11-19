---
type: Guide
title: TorchAir 控核与确定性：后端层次和版本差异
description: 区分 GE 算子/全局控核与捕获流控核，说明静态 Kernel 优先级和主线确定性 scope。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/limit_cores.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/limit_cores.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/limit_cores.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/limit_cores.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/core_limit.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/aicore.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/limit_core_num.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/scope/limit_core_num.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/scope/deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/aicore.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/core_limit.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 控核与确定性：后端层次和版本差异

## 版本与范围

发布文档固定在 ascend_26_0_pt28 的 TorchAir 子模块提交 7c6c754bed00c86ffaaa2a45cb7ac2724f058013；主线补充固定在 92e1e967bd35ebc37a442b4a969730bf3cf77a3c。以下分开说明，未做 NPU 运行验证。 发布段选择A2/A3，主线A2/A3与950的控制接口范围见后文，不回推发布版。

## 发布版控核

GE 的 torchair.scope.limit_core_num(aic,aiv) 配置算子上限，优先于 config.ge_config.aicore_num="aic|aiv" 全局配置。实际核数可能低于上限；不要复制文档的超硬件数示例。用图属性 _op_aicore_num/_op_vectorcore_num 与初始化日志核对实际生效值。

npugraph_ex 的 torch.npu.npugraph_ex.scope.limit_core_num(aic,aiv) 作用于 Stream，仅支持 Ascend C 算子；通信类仅支持 AI Vector 算子。不要多线程同时修改同一流的限核。发布文档明确 CANN≤8.5.0 时静态 Kernel 编译与控核一起打开，优先控核、静态 Kernel 失效；较高版本仍按实际支持度核验。不支持控核的算子可能破坏 micro-batch 并发，甚至卡住。

核数来自具体 SoC 的 platform_config，不是固定“24/48”。Profiler 的 Block Num/Mix Block Num 可核对主/从加速器使用量，不能用设置值代替实际观测。

## 主线确定性 scope

GE 使用 torchair.scope.deterministic(level)，npugraph_ex 使用 torch.npu.npugraph_ex.scope.deterministic(level)。level 仅整数 0/1/2/3，分别为关闭、确定性、强一致性、Batch 一致性；效果还取决于算子和 CANN。嵌套退出恢复外层，scope 外沿用全局设置，scope 内不能断图。

GE 为节点增加 _deterministic/_deterministic_level；npugraph_ex 在捕获时记录对应 level，Replay 复用它。不要在 forward 中直接用全局 set_deterministic_level 模拟局部 scope。FlashAttention 在 aclgraph 执行期间更新 actual sequence length 不会重施局部 level，为 Batch 一致性需保证进程全局 level 与 scope 一致。

## 验证

分别检查图属性、静态编译产物的 deterministic_level、实际核数、跨次及跨 Batch 数值。改变流限核可能触发重捕获，见[捕获控制](npugraph_ex_capture_controls.md)。本次未进行设备复现。


## 控核参数的主线变化与 Eager 层次

固定主线 GE 文档把算子和全局限核允许范围写为 0 到硬件最大值；其中 **0 是忽略该项、未配置，不是禁止使用该类核**。发布文档对有相应硬件的核类写为 1 到最大值，不能用主线 0 约定替代发布契约。主线对超过硬件上限的值报错；不要把发布示例中的截断日志推广到其他版本。

主线 npugraph_ex.scope.limit_core_num 增加 `stream=None`，未指定时作用于进入 scope 时的当前流；发布签名只有 aic、aiv。其参数合法性应按捕获后端文档核对，不能复用 GE 的 0 规则。CANN 大于 8.5.0 时来源说明静态 Kernel 可接收控核数量并共存，仍需算子支持；较早版本按前述优先级关闭静态编译。

Eager 还提供进程/设备级和流级设置，见[设备与流限核接口](../../../apis/torch_npu/device_and_stream_limits.md)。并发任务的 Vector 核需求超过物理资源、再相互等待通信，是来源列举的卡死机制；预算不超物理资源只是必要检查，不能保证所有调度组合都无死锁。Ascend C 的 AI Core/Vector 与 AI CPU 任务也不是同一套可控资源，不能把控核当作任意算子的硬隔离。

## 主线接口与Core计数单位

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE/npugraph_ex两个limit_core_num接口页与对应特性页已对照。GE允许0表示该项未配置；npugraph_ex的AI Core范围仍为1..max，Vector范围为1..max，仅硬件不存在独立Vector Core时例外允许0。npugraph_ex的stream=None作用于进入scope时的当前流，不把之后切换到的所有流自动纳入。

核数上限需从当前SoC的platform_config读取，不能用示例24/48作为产品常数。AI Core/Cube/Vector图示说明不同产品可能共用Scalar，或Cube与Vector分别有Scalar；A2示例按Cube数量计AI Core、一组Vector与其组合，不能把Cube和Vector数量相加当作另一个AI Core上限，也不把图中的1:N比值固定为所有产品同一比例。

主线GE全局字符串仍以竖线分隔aic/aiv，某项0等同未配置，如aic|0等同aic|；超过上限与发布例子里的截断日志不可混为同一版本契约。算子级优先于session级；图属性、GE日志和Profiler实际Block Num分别证明不同层次，不能只据原始options日志证明最终Kernel实际使用了该核数。

## 主线确定性属性、Eager与等级依赖

主线GE接口页对应的_deterministic为字符串：level0写"0"，level1/2/3写"1"，_deterministic_level保留完整等级；scope外不添加这两个节点属性，继续沿用全局配置。节点上存在属性不等于该算子/CANN已实现该等级。

npugraph_ex接口还允许Eager场景，文档说明进入/退出scope立即设置并恢复；捕获图则复用按相应等级捕获的任务。禁止断图约束针对图内scope，不从Eager可用推导动态图控制流可捕获。全局等级应在torch.compile前配置；[set_deterministic_level](../../../../training/apis/torch_npu/set_deterministic_level.md)另有Runtime/算子包门槛和多线程限制，不能仅凭局部接口接受3便认定Batch一致性已生效。

主线总览覆盖A2/A3与950，本节补齐主线950的控制接口说明；发布段仍仅A2/A3，未执行控核、确定性或跨batch实验。

## 独立包的Eager流冻结与设计描述差别

固定主线独立npugraph_ex的limit_core_num在非编译时返回_EagerLimitCore：进入时取显式stream或当时current_stream，保存该流原值并设置，退出恢复同一冻结流，即使scope内部切换当前流也不改恢复目标。编译时则返回携带stream和核属性的scope标记，两路径不能都概括成“Python只转字符串”。

该Python包装没有核数范围检查，不能据此证明CANN会接受任意值或总按同一方式截断；继续按本卡各后端/版本的文档范围消费。deterministic的Eager路径保存/恢复原level，编译路径写scope属性；捕获后的重放、全局level与静态缓存key仍按各自协议处理。独立包的[设计/实现草稿](npugraph_ex_standalone_design_contracts.md)尚无整体产品矩阵，不回填为发布版新能力。

## 控核附录的算子类别与死锁例子

两版附录分别说明：Ascend C的AI Core/AI Vector可控，AI CPU不生效；TBE、ATB等不能保证生效；HCCL仅AIV模式可控、AI CPU模式无效；MC2列为可控。它不是对任意底层实现的强制资源隔离承诺，实际算子路线仍须核对。

图示用每设备48个Vector核、两卡分别持有16/24核通信任务，以及NonZero申请全部48核说明跨卡互等：NonZero占住剩余资源，使另一通信任务无法就绪。只削减一个算子的配置值不证明所有跨rank顺序已正确；互卡任务总需求不超过物理资源只是必要检查。图中的数值、发布GE示例的24|100都不能复制成通用硬件上限或合法配置。CANN≤8.5.0与>8.5.0的静态编译优先级继续按前文分开消费。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/limit_cores.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/deterministic.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/limit_cores.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/deterministic.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/limit_cores.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/limit_cores.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/core_limit.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/aicore.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/limit_core_num.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/scope/limit_core_num.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/deterministic.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/scope/deterministic.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/appendix/aicore.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/scope/__init__.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/core_limit.md)（constraint）
