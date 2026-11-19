---
type: Guide
title: TorchNPU GradScaler：反缩放、溢出与更新状态机
description: 区分动态与静态缩放、每优化器调用顺序及普通/融合梯度路径，避免把跳步当成参数已更新。
tags:
- task.implementation
- topic.precision
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-amp.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/grad_scaler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-amp.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
created_at: '2026-11-09T03:52:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU GradScaler：反缩放、溢出与更新状态机

## 版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按逐接口产品表限定A2/A3与950DT训练；涉及 OpPlugin 时固定 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`。这是所指文档和实现的契约，不证明主线软件栈已经配套，不回推为 26.0/PyTorch2.8 所有组合均支持。


## 基础次序与默认值

所查 NPU 实现默认 init_scale=2**16、growth_factor=2、backoff_factor=0.5、growth_interval=2000、dynamic=True、enabled=True。scale(loss).backward() 产生缩放梯度，step(optimizer) 在适用路径还原并更新，update() 为下一轮调整或设置比例。

需要裁剪或检查梯度时，先完成该优化器全部梯度累积，再 unscale_ 一次。重复 unscale_、step 后再 unscale_ 或同一轮重复 step 会被拒绝；多个优化器均 step 后才 update。不要在每个 microbatch 中混用不同缩放比例后再统一反缩放。

## 动态、静态与停用不是同一含义

dynamic=True 的常规路径检测非有限值，溢出时跳过底层 optimizer.step，再按 backoff_factor 降低 scale；连续成功达到 growth_interval 后尝试增长。scaler.step 返回值沿用优化器返回或跳步时的 None，不能仅凭 None 区分是否更新。

dynamic=False 使用固定 loss scale，并不等价于动态路径仍会自动阻止所有溢出更新；所查 step 的静态分支直接调用优化器。enabled=False 则关闭缩放，scale 返回原值，step 直接调用优化器。需要静态策略时应另有明确的数值检查。

启用的 GradScaler 不支持 closure 参数。自定义优化器若声明 _step_supports_amp_scaling，则走接受 grad_scaler 关键字的专门协议，不能再假定与普通路径完全相同。

## 梯度和分布式路径

普通优化器的 unscale_ 路径以 allow_fp16=False 拒绝 FP16 grad；不能只对整个模型 .half() 后便假定能按普通 AMP 更新。融合优化器有组合梯度分支，应同时满足其 FP16/FP32 参数与稳定存储契约；不能为了绕过类型检查伪造 is_fused_optimizer 属性。

scale 还检查 loss/outputs 为 NPU Tensor，可递归处理 Tensor 容器。分布式初始化标志在首次 scale 的惰性初始化中记录；若需要其相应同步路径，应在首次使用前正确建域。_sync_dist_overflow_count 在设备支持 Inf/NaN 时直接返回，只有其他特定动态分支才按已初始化状态 AllReduce；不应宣称所有产品、任意子组和所有 scaler 都无条件跨 rank 同步溢出。

## 保存与恢复

state_dict 额外保存 dynamic；恢复启用实例时拒绝空字典，并读取 dynamic。检查 scale、增长计数和是否启用，避免把关闭 scaler 时的空状态用于要求恢复动态状态的任务。接口声明和日志不能代替多步及跨 rank 数值验收。

- [Autocast 与自定义前反向](torch_npu_autocast_and_custom_autograd.md)
- [融合优化器的组合存储和裁剪](torch_npu_fused_optimizer_lifecycle.md)


## 验证与回退

固定设备、软件栈、输入、初始参数及随机状态，比较多步数值、状态与恢复，再度量关闭调试后的稳态开销。遇到不满足条件的路径，回到已知可用的优化器或精度策略重新验证。本文未执行训练、加载上游代码或进行 NPU 实验。

- [软件栈基线](../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## PyTorch2.14清单的950DT补充

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.14 AMP页逐项列出950DT，覆盖torch.autocast、torch.amp.custom_fwd/custom_bwd及NPU形式的autocast/custom装饰器/GradScaler。本卡据此补齐950DT范围，仍不扩展950PR、不回推所有发布组合，也不把产品支持说明当作本地运行verified。

CPU AMP条目保留CPU名称，不能因它列在同页就用于NPU计算。产品列表不保证所有dtype、优化器、分布式overflow与自定义算子的组合已验证，前述实现分支及数值验收仍需分别核对。

## 原生AMP页的版本和命名空间

同提交七版本中英文AMP页对cuda.amp.GradScaler给出的NPU形式均为torch_npu.npu.amp.GradScaler，列三类产品；cpu.amp.GradScaler保持CPU名称。英文2.9/2.10/2.14还给原生CUDA入口弃用提示并建议torch.amp.GradScaler("cuda",...)，不因此将"cuda"设备参数用于NPU，也不覆盖本卡TorchNPU实现中的动态、静态和溢出状态机。完整名称映射见[Autocast七版本边界](torch_npu_autocast_and_custom_autograd.md)。

## 私有AMP入口的产品冲突

同提交private_apis对torch._amp_foreach_non_finite_check_and_unscale_列三产品，支持类型FP16/FP32；torch._amp_update_scale_支持类型FP32，中文列三产品而英文明确950不支持。原文没有逐参数映射，不把FP32解释成全部模型或梯度必须FP32。

公开GradScaler、私有缩放更新和非有限检测是不同入口；不因GradScaler类级三产品表就消除_update_scale_的双语分歧，也不据私有方法限制直接判定整个950混合精度训练不可用。是否实际走到该入口仍按对应实现与真实包验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-amp.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/grad_scaler.py)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-amp.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-amp.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-amp.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-amp.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-amp.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-amp.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-amp.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-amp.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-amp.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-amp.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-amp.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-amp.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-amp.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

## ShardedGradScaler 的跨 rank 溢出同步

主线 `torch_npu/npu/amp/sharded_grad_scaler.py` 提供 `_ShardedGradScaler`（GradScaler 子类，FSDP/分片场景）：`_GeneralMultiDeviceReplicator` 在原 `_MultiDeviceReplicator` 基础上把 "cpu" 加为合法主设备（:27-38），`_is_supported_device` 仅接受 NPU 与 CPU（:23-24）。`unscale_`（:255-309）在逐设备反缩放后，把每个 `found_inf` 经 `dist.all_reduce(async_op=True, group=process_group)` 跨 rank 同步：scaler 主设备非 CPU 而 found_inf 在 CPU 时，先 `.to(self._device)` 搬到设备 allreduce 再拷回 CPU（:281-306）——即溢出判定是"任一 rank 发现 inf 则全体跳步"，不是各 rank 独立决策。`_amp_update_scale_npu_` 直接复用 CPU 路径（:329-334），scale 增减仍按 backoff/growth_interval 状态机。`step` 未加 NPU 分支，直接走父类（:310-311）。该文件 `__all__` 为空，属内部入口；消费面与 FSDP 卡的挂接未在本节核对，也未运行多 rank 实验。

## 补充来源

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/sharded_grad_scaler.py)（implementation）：:19-38、:255-334。

## 发布版本 对照（f3ecfe4a）

卡内涉及的 1 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 版本边界（发布版本 行为不同，按 pin 分述）

- **`torch_npu/npu/amp/sharded_grad_scaler.py`**：ShardedGradScaler 跨 rank 同步等待机制为两版差异。
  - 主线构造器含 `device: str = "npu"` 参数并保存 `self._device`（:93、:108）；发布版无该参数。
  - 主线 `_maybe_opt_step` 收集 `found_inf_on_cpus`/`found_inf_on_devices`，CPU found_inf 先 `.to(self._device)` 到设备 async allreduce，再逐 `work.wait()` 并把设备结果拷回 CPU（:287-307）。
  - 发布版改用 `future_handles`（`work.get_future()`）收集，`torch.futures.wait_all(future_handles)` 等待，CPU 拷贝沿 `v_on_npu=v...` 路线（:282-302）。
  - 两版语义同为「任一 rank 溢出则全体跳步」，等待与拷回实现不同。
  - 对本卡结论的影响：本卡「ShardedGradScaler 的跨 rank 溢出同步」一节锚定主线 :281-306 路线；发布版本 为 futures 路线，行号与等待原语不同。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
