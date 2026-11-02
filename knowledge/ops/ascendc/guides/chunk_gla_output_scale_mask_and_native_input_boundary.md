---
type: Guide
title: "Chunk GLA 输出：分别保留块内权重、状态缩放与尾块掩码"
description: "从原 Torch 输出公式提炼 Ascend C 分块实现边界：A 已含 scale，状态项用自然 exp，保留 chunk32/64、因果及尾块列掩码。"
aliases: ["ChunkGlaFwdKernelO scale mask"]
tags: [task.implementation, topic.precision]
status: draft
sources:
  - resource: https://gitcode.com/sijiaali/ascendc-kernelgen-data/blob/167feb7024500cd594de63497972560ea721070c/npu_benchmark/level4/21_ChunkGlaFwdKernelO.py
    role: primary
  - resource: https://gitcode.com/sijiaali/ascendc-kernelgen-data/blob/167feb7024500cd594de63497972560ea721070c/npu_benchmark/level4/21_ChunkGlaFwdKernelO.json
    role: constraint
created_at: "2026-10-22T03:26:49Z"
updated_at: "2026-10-22T03:26:49Z"
platforms: ["950"]
---

# Chunk GLA 输出：分别保留块内权重、状态缩放与尾块掩码

## 经验与适用范围

把原 Torch Chunk GLA 输出段转成 Ascend950 实现时，先分清两个求和的语义，再融合或分块。输入包括 q、v、g、A、h；输出由块内因果注意力与块初始状态贡献相加。不能把其他 GDN/GLA 递推卡中的完整状态更新直接替代此输出段。

## 事实与依据

固定原任务源码 SHA256 `26bb3ebd700c0b58cba2241560de241f144790f8ac0436baaf044a25d9ea4dda`：

1. `get_input_groups` 在生成 A 时已乘 scale；`_o_segment` 的块内项只做被掩码的 A 与 v 收缩，不再乘 scale。
2. 状态项按 `q * scale * exp(g)` 与对应 chunk 的 h 收缩。g 是自然对数域的 chunk 内 inclusive cumsum；此处为自然 exp，不能无转换替换为 exp2，也不能对已累计 g 再做 cumsum。
3. `_o_segment` 保留包含对角线的下三角掩码，以及最后一个 chunk 的有效列掩码；补零至 chunk 倍数，最后裁回原 T。
4. 原50例 JSON SHA256 `c8ed80876f2588f3c63ad604956dc076884fe9d9086ca1953f5c74e8fb46faca`：前5例显式 chunk_size=32，余45例缺省64。不能把默认值当完整输入域。
5. 输出转换回 q 的 dtype；原始 q/v/g/A/h 数值和调用属性是精度合同的一部分。源码中的 varlen 分支不能仅因存在就报为该50例已测覆盖。

## 实现与验证配方

以 (batch, chunk, head) 划分独立输出工作；保留块内位置 t、s 与 h 的 chunk 索引。块内项对 s≤t 且 s 在该块真实序列范围内累加；状态项对 K 累加。两个结果相加后仅在合同规定的位置转回原 dtype。小尾块和 chunk32 必须从同一参数路径得到，不能按 case ID 分派。

构建 CPU 真值时，先获取实际原生输入，再在任何乘法、exp 和归约之前提升精度。保留 literal FP64 源码提升版与独立分块求和组织作为互检；不能只把 FP32 计算的最终输出转为 FP64。输入生成中的 q normalization、g cumsum 和已缩放 A 作为供应边界保留，不重新生成“更精确”的输入。

调试时分别检查块内项、状态项及最终和，区分 scale 重复、exp 底数错误、上三角泄漏、h 块索引错误和尾块列未清零；这些是可检验假设，不能仅凭最终误差形态断言其中之一已发生。

## 已有观测与消费边界

完整原50例的独立 CPU 真值及实际 NPU 输出已有通过记录，计时返回也按相同数学合同检验。其结果只属于对应源码、DSO、实际输入和计时窗口；本次知识提炼未运行新 P/F，没有证明上面各个错误假设都曾实际发生，也没有证明某种新 tiling 的性能收益。

经验来自 Torch-to-A5 Lite 生成与后续完整返回复核，本次按 a5ops-knowledge-ingest/dedup 回溯到上述源码和 case 叶子。新 BLACK_BOX 只消费这些语义及方法，不引入历史 candidate/DSO；新 workflow 是否成功须由新构建和完整 P/F 单独回答。
