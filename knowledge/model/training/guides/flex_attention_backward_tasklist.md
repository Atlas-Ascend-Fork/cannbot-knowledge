---
type: Guide
title: FlexAttention反向任务列表：dK/dV开关与回退
description: 保留950PR/DT文档开关合同，并说明固定主线关键实现中没有该开关名的读取点，实际任务列表还依赖分派、资格与负载。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/flex_attention/TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_BWD_DKDV_TASKLIST.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_tasklist.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
created_at: '2026-11-09T15:10:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# FlexAttention反向任务列表：dK/dV开关与回退

## 固定契约

来源为TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的内部环境页，明确列Ascend950PR/DT，不扩展A2/A3或任意发布组合。仅静态审阅，未执行注意力或梯度测试。

TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_BWD_DKDV_TASKLIST默认1，满足条件时允许反向dK/dV任务列表调度；0关闭该路径、保留默认dK/dV调度。设置后使用新进程，不控制前向/dQ或改变Autograd接口。

需要预生成掩码、静态形状、支持的掩码布局和连续INT32元数据；Query与Key/Value的batch都为1、掩码head维为1，还受FP32累加和片上存储资源限制。开启仍检查适用条件，不满足使用默认dK/dV路径。该页未给完整资源阈值或全部注意力输入合同，不能仅据默认1宣称任意BlockMask或batch均命中。

记录实际mask布局、元数据、shape、dtype、路径和反向数值，再测稳态耗时；任务列表不保证所有输入都更快，缺少日志也不证明一定使用默认路径。

## 固定主线消费者与文档开关未闭合

定向核对同一主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的反向lowering、tasklist helper、复合dispatch和legacy wrapper。上文“默认1、0关闭”是本卡primary文档的明确说明；**在所读关键实现中，没有找到对 `TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_BWD_DKDV_TASKLIST` 的读取或围绕它的门控。** 精确名称搜索该快照仅命中文档项，不能把它升级为对外部依赖、其他版本或未读路径的全局否定。

所读lowering通过独立的 `flexattention_dispatch_strategy` 决定是否构造显式 `bwd_dkdv` plan，并检查mask-out、静态维度、连续INT32元数据和FP32/UB资源；运行期helper再按负载启发式选择tasklist或primary。两者不能简单当作上述文档0/1开关的别名。代码也保留legacy renderer对象及wrapper方法，本卡没有证明默认配置下这些定义必被实际调用。

因此在这个固定实现证据范围内，**不能仅设该文档变量为0就宣称已关闭所有任务列表，也不能仅保留默认1就宣称已命中**。需要检查真实生成wrapper、实际plan/回退与运行期选择；差异未通过设备实验解决。本修订不扩展原文档950PR/DT的支持范围，不新增verified。

- [任务列表的启发式、缓存与临时内存](torch_npu_flex_attention_dkdv_tasklist_runtime.md)
- [反向分路与梯度存储](torch_npu_flex_attention_backward_routes_and_gradients.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/flex_attention/TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_BWD_DKDV_TASKLIST.md)（primary）

- [实现核对来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（implementation）
- [实现核对来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_tasklist.py)（implementation）
- [实现核对来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py)（implementation）
- [实现核对来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py)（implementation）
