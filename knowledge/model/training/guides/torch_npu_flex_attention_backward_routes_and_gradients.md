---
type: Guide
title: FlexAttention 反向分路：LSE 梯度、分离 dQ/dK/dV 与输出存储
description: 核对反向 mask-in/mask-out 的实际选择、log2 LSE梯度处理、FP32累加及广播还原，避免从前向成功推断全部梯度路线。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: primary
created_at: '2026-11-10T11:54:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FlexAttention 反向分路：LSE 梯度、分离 dQ/dK/dV 与输出存储

## 固定主线与范围

定向审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的反向 lowering 与 mask-in fallback；完整设备模板、运行梯度与性能验证不在本卡范围。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 不含同路径 `torch_npu/_inductor/kernel/flex_attention.py`，以下不写成发布行为。整卡未知平台，保持 `draft`、空列表。

前向接口和支持范围仍见[FlexAttention 文档指南](../../inference/guides/optimization/torch_npu/torch_npu_inductor_flex_attention.md)，前向选路见[实际前向分派](../../inference/guides/optimization/torch_npu/torch_npu_flex_attention_forward_dispatch.md)。本卡补充训练中不能仅由前向推导的消费者。

## dtype、batch 与 mask 路线先分别判断

反向要求 Query/Key/Value dtype 相同，否则显式 ValueError；batch 需 Bq=Bkv 或 Bkv=1。它不表示任意 head、stride、回调或广播方式都合法。前向 workspace 参数和 GPU backend 提示在反向被移除，不能用前向预算控制本卡所有反向临时内存。

lowering 建立前向 score 子图、joint 梯度子图和 mask 子图，先校验 joint graph。存在显式且非恒等 score_mod，或不满足所读稀疏 BlockMask 判据时，进入 `_lower_flex_attention_backward_mask_in()`。该路径使用一组 fused backward template 候选；没有可用配置或所有候选生成失败会抛错，并非自动退回 Eager。

可用 mask-out 时，dQ 与 dK/dV 分开生成、选择并关联依赖：候选名称分别是 `flex_attention_backward_qmajor_dq` 和 `flex_attention_backward_dkdv_only`。`bwd_dkdv` 动态策略只附着在 dK/dV 分派，dQ 的 plan strategy 为 None；不能把该策略解释为同时将三种梯度变成任务列表。

## LSE 的对数底与辅助梯度必须匹配

源码边界保存的 logsumexp 使用 log2，NPU模板内部采用自然指数/对数；mask-out 的注释明确由 backward template 内转换所读 LSE。不能把任意自然对数 LSE 直接代替保存统计。

两条反向路径均先形成 `delta=sum(out*grad_out, axis=-1)` 并转 FP32。如果 `grad_logsumexp` 非 None，还将它乘 `1/ln(2)` 后从 delta 中减去，再使 delta 连续并 realize。只对主输出求梯度与同时对 LSE 求梯度所需运算不同，不能为减少一次转换或临时张量而删除辅助梯度分支。

这里核对的是具体计算表达式和底数契约，没有完成完整 kernel 数学证明。自定义 score 捕获参数还需 joint graph 正确生成对应梯度；mask-in 路线将 captured-grads compute 和 mutated-grads 纳入模板及依赖，最终按对应原始 score buffer dtype 转回或保留 None。不能由 dQ/dK/dV 存在推断所有闭包 Tensor 都会获得所需梯度。

## 分离路径的 FP32 累加与广播内存

mask-out 路线为 dK 和 dV 显式创建 FP32 累加缓冲，形状以 Bq 而非 Bkv 展开，并先清零。即使模型输入是 FP16/BF16，反向临时内存也不能只按输入字节数估算；batch 广播时还可能形成比原 K/V 更大的累加对象。

当 Bq=Bkv，直接使用这些累加；当 Bq>1 且 Bkv=1，最后沿 batch 轴求和并保留维度。若未启用 PRESCALE_QK，dK 累加再原地乘 SM_SCALE。实现注释说明原地乘用于保留已明确的转置布局，不能随意改成可能产生连续存储的 out-of-place mul。

最后显式分配与 Key/Value 原始 shape、stride 和 dtype 匹配的输出，通过 ATen copy_ 同时完成数值转换和写入；dQ 也经 dtype/固定布局处理。FP32累加、最终梯度dtype和实际storage stride是三层，不能只检查shape。

mask-in helper使用的输出分配和累加 dtype 与上述分离路线并不相同；本卡不把分离路线的FP32临时量推广成所有反向 kernel 都采用同一布局或峰值。

## 调度提示不是实测并行度

dQ 的 launch meta按 Query blocks、Bq和Hq估计任务数；persistent dK/dV按 KV blocks、batch和Hkv估计，launch_programs都夹在至少1与Cube核数/任务数之间。最终生成的tiling覆盖对应候选配置；不能把提示的任务数当成真实运行时重叠或稳定收益。

反向 mask-out 还会生成自己的 compact offsets、动态实际块数及mask映射。前向有界workspace并不证明反向也复用同一缓冲。dK/dV任务列表的UB筛选、split临时量与元数据缓存另见[任务列表运行期成本](torch_npu_flex_attention_dkdv_tasklist_runtime.md)。

接入时分别检查主输出与LSE梯度、非恒等score_mod、batch广播、输入/输出stride及低精度转换，再以设备时间线评估三种梯度和元数据阶段。本卡没有新增 verified 或性能数值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（primary）
