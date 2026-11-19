---
type: Guide
title: TorchNPU 融合优化器：组合存储、梯度清零与裁剪
description: 解释融合优化器基类的首次组合、FP16/FP32 两槽、组合缓存与分组偏移、闭包次序、清零和带掩码裁剪的确切前提，区分张量融合与低精度/分片优化器。
tags:
- task.optimization
- topic.optimizer
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: constraint
created_at: '2026-11-09T03:52:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU 融合优化器：组合存储、梯度清零与裁剪

## 版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按逐接口产品表限定 A2/A3 训练；涉及 OpPlugin 时固定 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`。这是所指文档和实现的契约，不证明主线软件栈已经配套，不回推为 26.0/PyTorch2.8 所有组合均支持。

门面 `torch_npu.optim.__all__` 均列出 `NpuFusedOptimizerBase` 及 SGD、Adadelta、Lamb、Adam、AdamW、AdamP、BertAdam、RMSprop、RMSpropTF 九个融合实现，并逐个导入；主线额外导入私有 `_DistributedMuon`，没有加入 `__all__`，其版本与执行边界见 [Muon 指南](torch_npu_distributed_muon_execution.md)。这组类与 [原生 torch.optim 的 foreach/fused 选择](torch_npu_native_optimizer_modes.md) 是不同入口。

## 融合的对象和首次初始化

NpuFusedOptimizerBase 不能直接当作具体优化器使用，需由子类实现状态初始化和组更新；基类 `_maybe_init_combined_states` 和 `_group_step` 都抛 NotImplementedError，构造成功不意味着可独立训练。固定实现先按 FP32/FP16 分类，再组合参数与梯度，保存参数组的切片，并惰性组合动量等状态；这是减少小 Tensor 处理开销的机制，不是自动将状态量化或按 rank 分片。

参数存在梯度时，仅接受 torch.float32/torch.float16，其他 dtype 会报 TypeError。模型前反向使用 BF16，不表示这个融合优化器就能直接接受 BF16 参数；AMP、master 参数和优化器实际持有对象需分别确认。FP32 固定使用组合槽 0，FP16 使用槽 1。

首次组合会跳过 grad=None 的参数；标志设定后不会每步重新扫描完整参数集合。动态解冻、后续新增梯度/参数组或重新赋值 grad，不能假定自动纳入已缓存组合。按实际训练策略单独检查，不能只用第一次 step 成功验收。

## 组合缓存与分组偏移

构造器先交给 `Optimizer` 建立参数组，初始化三个 group 索引缓存为 None、参数列表为空、跨组参数/梯度组合各为两个 None 槽；参数梯度、状态、掩码三个已组合标志均为 False，`is_fused_optimizer=True`。

`_maybe_init_combined_params_and_grads` 在参数梯度标志为 True 时直接返回。首次遍历按参数组跳过 `grad is None` 的参数；若参数和梯度 NPU 格式不同，先将 `p.grad` 替换为 `npu_format_cast(...).contiguous()`，之后统计存储并按参数 dtype 分槽，其他 dtype 抛 TypeError。此顺序允许梯度对象先变化，再发生 dtype 拒绝，不能承诺失败前完全无副作用。

主线大小来自 `torch_npu.get_storage_size(p)` 和对应梯度调用；发布版来自 `p.storage().size()` 与 `p.grad.storage().size()`。这里确认调用差异，不在未核底层 helper 时断言两个实现对所有私有格式语义完全相同。每组分别累计参数与梯度的物理存储量，跨组分别调用 `npu_combine_tensors`；再用 `get_part_combined_tensor` 按各 dtype 的**独立参数偏移与梯度偏移**切回组视图，不能拿逻辑 `numel` 或参数偏移替代梯度偏移。最终保留每组原参数列表与组合视图，只有组合参数至少一槽非 None 才置标志 True。

这是一次性缓存协议。首次没有梯度的参数不进入列表；之后换对象、改 storage、增参或重新解冻不会由已为 True 的入口自动重扫。`get_combined_params/get_combined_grads` 直接返回缓存列表，没有 clone。

## 稳定对象和清零方式

接口页要求使用期间不重新申请参数对象：将模块移 CPU、把参数指向新对象或设为 None 都可能破坏前提。原地更新和读取值允许，但也要检查实际 storage、梯度和格式是否改变。

固定基类的 zero_grad 默认 set_to_none=False，True 明确抛 ValueError；不能直接套用其他优化器的默认清零配方。zero_grad 同样处于 no_grad；未组合时会先尝试组合，仍无组合参数则委托父类 `zero_grad(False)` 返回；已有组合时逐槽对非 None 梯度整体 `zero_()`，按合并缓冲区清零而不是删掉每个参数的 grad，也不会为了随后出现的 `grad=None` 重建既有绑定。首次 step、清零、裁剪哪个先触发组合，都会影响固定的参数集合。

基类 `step` 整体处于 `torch.no_grad()`：先执行可选 closure，再惰性组合参数/梯度与状态，最后逐组 `_group_step` 并返回 loss。基类没有主动用 `enable_grad` 包住 closure；调用者如需要求导，必须明确检查实际闭包上下文。AdamP/Lamb 覆盖此方法，次序也改变，见 [Adam 家族](torch_npu_fused_adam_family_execution.md)。

## 裁剪与私有格式填充

clip_grad_norm_fused_(max_norm,norm_type=2) 基于组合梯度及 mask 计算范数；mask 用于忽略 NPU 私有格式填充元素。返回裁剪前 total_norm，仅在 max_norm/(total_norm+1e-6)<1 时缩放梯度；也有无穷范数路径：无穷范数对 float 梯度绝对值乘掩码后取各槽最大，再取整体最大；有限 p 范数对各槽 `abs(g)^p * mask` 求和，跨槽堆叠求和后取 `1/p` 次幂。

掩码的确切前提：公开 `clip_grad_norm_fused_` 先在 no_grad 块内尝试参数组合，再首次建立掩码。`_maybe_init_combined_grads_masks` 要求参数已组合为 True，否则抛 ValueError；对全局两类参数列表调用 `_combine_grads_mask`。该 helper 空列表返回 None，对 `requires_grad=True` 的参数按其 `grad.size()` 创建 `torch.ones(...).npu()`，转到参数 NPU 格式后组合。显式 `.npu()` 及默认 ones dtype 仍依赖设备上下文，不能由本文件保证任意多设备安全。掩码缓存一旦建立也不随形状变化重建。

内部 `_clip_grad_norm_fused_` 先检查梯度和掩码槽数相同，空列表或全 None 时返回 `torch.tensor(0.)`。这**不等于公开入口在无梯度时一定返回 0**，因为公开路径可能先在掩码前提处失败。未额外实现 error_if_nonfinite、跨 rank AllReduce 或完整 norm_type 值域校验。

AMP 下应在全部梯度累积后，对该优化器 unscale_ 一次，再裁剪，再 scaler.step，最后 update。避免对仍被缩放的梯度直接应用正常阈值，也不要先组合后任意更换底层梯度对象。

## 恢复与算法边界

构造参数、参数组、dtype、梯度参与集合和优化器状态应共同核验。恢复不是只把数值字典塞进任意已有组合；先按实际实现确认状态与组合缓存重新建立。Tensor fusion 不能替代 MindSpeed 的低精度状态、ZeRO、卸载或参数复用契约。

- [融合 Adam](../apis/torch_npu/npu_fused_adam.md)
- [解耦衰减 AdamW](../apis/torch_npu/npu_fused_adamw.md)
- [SGD 与 Nesterov](../apis/torch_npu/npu_fused_sgd.md)
- [LAMB 的限定路径](../apis/torch_npu/npu_fused_lamb.md)
- [模型框架的优化器显存路线](../concepts/techniques/optimizer_memory.md)

## 验证与回退

固定设备、软件栈、输入、初始参数及随机状态，比较多步数值、状态与恢复，再度量关闭调试后的稳态开销。分别核对首次有/无梯度、混合 FP16/FP32、私有格式与 padding、参数组偏移、闭包求导上下文、状态恢复后多步以及 AMP 反缩放后裁剪。遇到不满足条件的路径，回到已知可用的优化器或精度策略重新验证。本卡完成本地定义的静态对照，未执行设备、数值或性能实验；底层组合工具、ATen、设备分配和分布式兼容继续独立验证。

- [软件栈基线](../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 其余融合优化器与文档示例边界

OpPlugin两固定版本和主线英文的各具体优化器均保留参数对象不重新申请的前提；各接口分别记录在[Adadelta](../apis/torch_npu/npu_fused_adadelta.md)、[AdamP](../apis/torch_npu/npu_fused_adamp.md)、[BertAdam](../apis/torch_npu/npu_fused_bert_adam.md)、[RMSprop](../apis/torch_npu/npu_fused_rmsprop.md)、[RMSpropTF](../apis/torch_npu/npu_fused_rmsprop_tf.md)与[基类合同](../apis/torch_npu/npu_fused_optimizer_base.md)。Adam/AdamW/SGD/Lamb另有独立接口卡。

主线各算法产品页新增950DT，但本指南还依赖独立PyTorch主线的组合/裁剪实现，整卡保留原A2/A3范围，不用类级产品表免除dtype、动态参数与AMP条件。基类示例只展示继承构造和__setstate__，没有完整更新；具体算法示例只手动梯度一次step，未使用导入的AMP，也无对照、恢复和性能断言。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/__init__.py)（implementation），完整本地模块 1–17 行。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/__init__.py)（implementation），完整本地模块 1–16 行。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md)（primary）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdam.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（primary）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（primary）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md)（primary）
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedBertAdam.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（primary）
- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md)（constraint）
- [固定来源 27](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md)（primary）
- [固定来源 28](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSprop.md)（constraint）
- [固定来源 29](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md)（constraint）
- [固定来源 30](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md)（primary）
- [固定来源 31](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedRMSpropTF.md)（constraint）
- [固定来源 32](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（constraint）
- [固定来源 33](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（primary）
- [固定来源 34](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（constraint）
