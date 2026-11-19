---
type: Guide
title: TorchNPU Adam 家族：组合状态、投影、预热调度与信任比
description: 完整对照 Adam、AdamW、AdamP、BertAdam、Lamb 的双版本本地实现，区分状态计步、权重衰减、裁剪和辅助缓冲。
tags:
- task.optimization
- topic.optimizer
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adam.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adam.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamw.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamw.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamp.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamp.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_bert_adam.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_bert_adam.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_lamb.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_lamb.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
created_at: '2026-11-11T03:26:02Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU Adam 家族：组合状态、投影、预热调度与信任比

## 固定版本与共享状态

范围为 PyTorch 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的五个完整优化器模块。每个模块的完整 AST（含 docstring）在两版相同；只复用这五对固定实现，不推及其他发行版。基类存储调用差异及 FP32/FP16 两槽、固定 grad 集合、清零和掩码规则见 [融合优化器生命周期](torch_npu_fused_optimizer_lifecycle.md)。产品适用范围沿用各 API 卡独立来源，本卡不新增产品确认或运行验证。

五类都在 `_init_param_state` 惰性建立 step=0、一阶矩 m 和二阶矩 v。恢复非空状态时，先新分配同形零缓冲、copy_ 旧状态，再重新绑定字段，不是直接复用旧状态 tensor/storage。Adam/AdamW/AdamP/BertAdam 使用 preserve_format，Lamb 使用普通 zeros_like。按基类每组每 dtype 的参数列表收集状态，空列表保留 None；非空调用 `npu_combine_tensors`，**组合计步取列表首项 `step_list[0]`，未检查其他参数计步相同**。`_maybe_init_combined_states` 先查缓存标志，遍历所有组后置标志；它不是自动追踪后续参数组变化的机制。

Adam、AdamW、AdamP、Lamb 每步对当前有 grad 的逐参数状态和组合状态分别加 1；BertAdam 只增加组合 step，逐参数 step 不在更新函数里推进。这对 state_dict 恢复、重新组合及异步启用参数尤其重要，不能把所有计步字段当作天然同步。恢复验收应比较逐参数字段与组合计数，而不只比较一次 loss。

## Adam 与 AdamW：校正和衰减位置

[Adam API](../apis/torch_npu/npu_fused_adam.md) 与 [AdamW API](../apis/torch_npu/npu_fused_adamw.md) 给出真实签名和检查：lr/eps/weight_decay 非负，beta 各在 [0,1)，默认衰减分别 0 与 0.01。两类 `__setstate__` 为旧组补 `amsgrad=False`；AMSGrad 额外建立/恢复/组合 max_exp_avg_sq。初始化与组更新都显式拒绝稀疏梯度。AdamW docstring 的 maximize 没有对应构造参数。

令 g 为组合梯度，t 为本卡已递增组合计步。Adam 在矩更新前令 `g = g + weight_decay*p`；AdamW 先原地 `p *= 1-lr*weight_decay`，矩仍使用原 g。共同更新为 `m=beta1*m+(1-beta1)*g`、`v=beta2*v+(1-beta2)*g²`。AMSGrad 用 `vmax=max(vmax,v)`，否则直接 v；分母 `sqrt(v_or_vmax)/sqrt(1-beta2^t)+eps`，步长 `lr/(1-beta1^t)`，参数减去步长乘 m/分母。None 参数/梯度组合槽跳过。这些位置决定正则化数值，不能仅因都叫 Adam 而互换。

## AdamP：逐参数投影与额外组合缓冲

[AdamP API](../apis/torch_npu/npu_fused_adamp.md) 的构造器直接保存 lr、betas、eps、weight_decay、delta、wd_ratio、nesterov，未复制 Adam 的数值边界检查。除 m/v 外，`_combine_middle_vars` 为每个参数分配 perturb 与 wd_ratio 两组零缓冲，并各自组合；`_combine_middle_vars_by_group` 用独立标志只初始化一次。组合状态字典还保留未参与更新的空 max_exp_avg_sq 占位，不能当作 AMSGrad 功能。

更新先按 Adam 的两种 bias correction 计算分母与步长。普通 perturb=m/denom，Nesterov 时为 `(beta1*m+(1-beta1)*g)/denom`；copy_ 到组合 perturb，随后用每参数视图投影。`_channel_view` 展平为 `[size(0),-1]`，`_layer_view` 为 `[1,-1]`；余弦 helper 用绝对点积除以两端各自 `norm+eps`。`_projection` 先 channel 后 layer：若最大余弦小于 `delta/sqrt(视图宽度)`，从 perturb 减去参数归一化方向分量，立即返回 wd_ratio；都不命中返回比例 1。仅 ndim>1 参数走投影，使用该参数的当前 grad.data。

weight_decay>0 时把各投影比例填入 wd_ratio 视图，执行 `p *= 1-lr*weight_decay*combined_wd_ratio`；再以 bias 校正步长减 perturb。其 `step` **先**组合参数/状态/中间缓冲，**后**在 enable_grad 中执行 closure，再逐组更新；closure 首次产生新梯度并不保证能进入前面已冻结的列表。该类在 `_combine_group_param_states` 的首次状态组合阶段显式检查 `grad.is_sparse` 并抛 RuntimeError；`_group_step` 没有重复这一检查。不能把组更新阶段没有重复检查解读为支持稀疏梯度。

## BertAdam：每组每 dtype 裁剪与更新前调度

[BertAdam API](../apis/torch_npu/npu_fused_bert_adam.md) 已区分源码 `lr=required` 与文档默认。构造检查 warmup 为 -1 或 [0,1)、schedule 属于四个注册项、b1/b2 各 [0,1)、e 非负；t_total、weight_decay 和 max_grad_norm 没有同样的完整值域检查。局部 `_clip_grad_norm_` 遇 None 直接返回，否则求 float 梯度 L2 并按 `max_norm/(norm+1e-6)` 在系数<1时缩放。组更新使用实例 `self.max_grad_norm`，正数才开启；**分别对每组每 dtype 组合梯度裁剪**，没有基类 padding 掩码，也没有跨 dtype/跨 rank 全局范数归约。

矩更新后 `update=m/(sqrt(v)+e)`，本地没有 Adam bias correction；正 weight_decay 时加 `weight_decay*p.data`。t_total=-1 固定 lr，否则在**组合 step 递增前**以 x=step/t_total 调度，参数更新后组合 step 加 1。四个模块函数都在 x<warmup 时返回 x/warmup，随后分别返回：cosine 为 `0.5*(1+torch.cos(pi*x))`，constant 为 1，linear 为 `max((x-1)/(warmup-1),0)`，poly 为 `(1-x)^degree`。辅助函数默认 warmup=0.002、poly degree=0.5，而构造 warmup 默认 -1；没有通用 x 上界截断。cosine 的 torch.cos 输入类型与 t_total=0、越界 poly 等调用组合需要独立运行验收，不能把函数名当作所有输入可执行证明。类内没有显式 sparse guard，不能据此认定稀疏可用。

## Lamb：参数粒度信任比与未核对全局范数入口

[Lamb API](../apis/torch_npu/npu_fused_lamb.md) 已保留 eps 真值 1e-6 与注释 1e-8 的区别，以及 use_global_grad_norm 依赖未核对的限制。构造检查 lr/eps 非负和 beta 范围，没有本地 weight_decay 非负检查；adam 与 use_global_grad_norm 存在优化器对象上，并立即创建值为 1 的 NPU global_grad_norm tensor，即使开关为 False。状态组合阶段显式拒绝稀疏梯度。

`_combine_middle_vars` 为每参数创建 trust_ratio、param_pow、adam_step_pow 三组零缓冲并分别组合；组包装 helper 用一次性标志缓存，adam=True 也走这条分配路径。每组合槽若 global_grad_norm.item()>1，先用该值除 g；随后更新 m/v，计算 `adam_step=m/(sqrt(v)+eps)`，无 bias correction，非零 weight_decay 加 `weight_decay*p`。adam=True 直接把组合信任比填 1；否则缓存 p² 与 adam_step²，逐参数计算 `weight_norm=sqrt(sum(p²)).clamp(0,10)` 与 adam_norm。任一范数为零取比例 1，否则取 weight_norm/adam_norm；最终 `p -= lr*adam_step*trust_ratio`。adam=True 的这条路线不因此等于带 bias correction 的 NpuFusedAdam。

Lamb 的 step 和 AdamP 一样先完成三类组合，再用 enable_grad 调 closure。开启 use_global_grad_norm 会调用 `_get_global_grad_norm`，其本地实现引用 `get_optimizer_combined_grads/get_optimizer_combined_grad_masks`；固定 Lamb、基类及 torch_npu 树仅发现调用，未发现这两个方法定义。保留为**此源码闭环未完成的入口**，不提供可直接启用的配置。即使外部补齐方法，局部公式只是平方乘掩码求和再开方，也没有 AllReduce；不能仅凭 global 名称宣称分布式全局范数。

## 验收

重点覆盖首次组合与恢复后的多步计数、AMSGrad、耦合/解耦衰减、AdamP 投影两种命中及无命中、BertAdam 分 dtype 裁剪和各 schedule 边界、Lamb 零范数与 trust ratio。这里仅核对本地实现事实，ATen 数值、combine 分配/别名、AMP、FSDP/ZeRO 和性能需独立证据；没有执行这些实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adam.py)（primary），完整本地模块 1–187 行。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adam.py)（implementation），完整本地模块 1–187 行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamw.py)（implementation），完整本地模块 1–188 行。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamw.py)（implementation），完整本地模块 1–188 行。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamp.py)（implementation），完整本地模块 1–278 行。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamp.py)（implementation），完整本地模块 1–278 行。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_bert_adam.py)（implementation），完整本地模块 1–200 行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_bert_adam.py)（implementation），完整本地模块 1–200 行。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_lamb.py)（implementation），完整本地模块 1–272 行。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_lamb.py)（implementation），完整本地模块 1–272 行。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
