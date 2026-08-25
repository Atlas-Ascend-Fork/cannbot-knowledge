---
type: API
title: GetValue
description: 获取LocalTensor指定索引的数值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetValue

获取 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 DMA 32B 块最小传输粒度](../../../../../runbooks/compilation/ascend950_dma_32b_minimum_block_granularity.md)（`exemplifies`）：目标卡明确建议用 GetValue/SetValue 做单元素诊断或不满足 DMA 粒度时的标量基线；GetValue 提供不提交小块 DMA 的读取路径。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`exemplifies`）：该 Runbook 证明向量流水写 UB 后立即用 GetValue 做标量读取会读到未完成数据，并给出显式 completion 的正确交接顺序。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：Runbook 的失败分支用 GetValue 从刚经向量路径写入的 LocalTensor 读取标量；API 卡界定它只是在合法 LocalTensor 位置读取 offset 元素，不提供跨执行域完成保证。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《GetValue》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《GetValue》提供“获取LocalTensor指定索引的数值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [SetValue](set_value.md)（`same_topic`）：SetValue 写入 LocalTensor 单元素，GetValue 读取单元素，构成同一 LocalTensor 标量访问契约的读写对。
- [operator](operator_call.md)（`same_topic`）：operator 与《GetValue》的实质衔接是：LocalTensor operator 生成子视图，必须与地址/size/shape 属性和 Get/SetValue、offset 故障共同理解。
<!-- cannbot:related:end -->
