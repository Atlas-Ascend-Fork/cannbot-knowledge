---
type: Guide
title: 原生优化器 NPU 路线：foreach、fused 与 dtype 清单
description: 说明参数分组对 foreach 的影响、Adam/AdamW/SGD 的不同限制及类与方法 dtype 表述冲突。
tags:
- task.optimization
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-optim.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-optim.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_optim.py
  role: implementation
created_at: '2026-11-09T06:08:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生优化器 NPU 路线：foreach、fused 与 dtype 清单

## 固定版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按条目区分A2/A3训练系列与950DT，具体方法的排除在下文保留；逐项版本门槛独立核对，不回推至 26.0/PyTorch2.8 发布基线。本文仅静态审阅，没有 NPU 实验。

## PyTorch2.14 清单的优化约束

以该固定提交PyTorch2.14章节为当前说明，并核对2.7.1、2.9至2.13中英文差异；不等于PyTorch2.8发布支持声明。Adadelta、Adagrad、Adam、AdamW、Adamax、NAdam、RAdam、RMSprop、SGD均提示：foreach=None/True且参数组很多时，可能因foreach特性变慢，应对照foreach=False。没有给出统一组数阈值，不能对所有模型默认关闭或开启。

## fused 不是同一个实现

Adam在A2/A3条目明确暂不支持fused=True，部分情形可能回退CPU。AdamW的fused=True暂不支持grad_scale/found_inf，FP32与对标单Tensor实现一致，FP16/BF16采用升精度路线，不能据此承诺与CPU/CUDA逐位一致。SGD则明确列出可开启fused。单个优化器的fused支持不能传播给其他类。

原生torch.optim的foreach/fused与torch_npu.optim.NpuFused*是不同入口，后者的参数组合存储、梯度清零和dtype约束仍按其独立卡片检查。

## dtype 描述必须按对象与路径复核

类条目列Adadelta/Adagrad/Adam/Adamax/NAdam/RAdam/RMSprop/SGD为BF16/FP16/FP32，AdamW另列complex64，ASGD为FP16/FP32。但同页若干step/zero_grad/状态方法条目又只列FP16/FP32，与类条目存在覆盖差异。不能把类的dtype列表提升为所有更新、状态恢复和fused组合均支持，尤其BF16/复数须核对具体方法与实现。

学习率调度器的方法也有独立lr dtype表述，不从优化器参数dtype推导调度器Tensor学习率支持。对这些不一致保留版本和准确方法线索，未运行前不伪造完整支持结论。

## 验收

从相同初始参数、梯度和超参数比较多步更新、状态保存恢复、AMP溢出路径；再测不同参数组组织下的稳态时间。分别记录实际kernel与CPU回退，不以构造器成功代替更新正确。

- [NpuFused优化器的组合存储生命周期](torch_npu_fused_optimizer_lifecycle.md)
- [禁止已纳管CPU回退](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)

## 七版本的类、方法和950DT例外

同提交PyTorch2.7.1、2.9至2.14中英文页的上述foreach/fused和dtype限制保持一致，不由相邻版本缺少2.8章节补出发布行为。Optimizer类列三类产品；其add_param_group/state_dict中文只列A2/A3、英文明确950DT不支持，load_state_dict/step/zero_grad则列三类产品。继承关系不替代具体子类的独立表。

Adadelta、Adagrad、Adam、AdamW、Adamax、ASGD、LBFGS、NAdam、RAdam、RMSprop、SGD的类与列出的参数组、状态保存/恢复、更新、清零及六种load/state/step前后置注册钩子通常列三类产品；但NAdam.zero_grad明确950DT不支持。钩子支持表没有定义顺序、参数替换、图模式或任意自定义钩子组合，不凭注册成功判断训练正确。

SparseAdam中文类列三类产品，英文没有独立类级表；其step明确950DT不支持，add_param_group/load_state_dict、六种注册钩子和zero_grad另列三类产品。不能因构造器或清零支持就宣称完整稀疏更新在950可用，也不能把该局部限制推广到所有稀疏计算。Adafactor及step只在中文七页列三类产品，没有完整dtype和优化参数合同。

| 算法 | 额外只列FP16/FP32的具体方法 |
| --- | --- |
| AdamW | step、zero_grad |
| Adamax、ASGD、NAdam、RAdam、SGD | add_param_group、load_state_dict、state_dict、step、zero_grad |

上表保留类级BF16/复数与方法级限制的覆盖差异；ASGD类自身也只列FP16/FP32。LBFGS与SparseAdam的条目没有同等完整dtype说明，不从其他算法填补。Adam对A2/A3的fused排除也不能反推950已经支持fused；未明确组合仍须核对实际版本。

学习率及参数平均的独立约束见[调度器与SWA/EMA指南](torch_npu_native_scheduler_averaging_scope.md)。分布式包装还须满足[ZeroRedundancyOptimizer与Join限制](torch_npu_native_distributed_optimizer_join.md)，不能因本地优化器支持就组合NPU融合优化器。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-optim.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-optim.md)（supporting）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-optim.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-optim.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-optim.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-optim.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-optim.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-optim.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-optim.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-optim.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-optim.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-optim.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-optim.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-optim.md)（constraint）

## foreach 设备门控是字符串区间比较

主线 `torch_npu/utils/_optim.py` 的 `add_optim_method()` 替换 `torch.optim.optimizer._get_foreach_kernels_supported_devices`：先取当前设备 `get_device_properties(current_device()).name`，把原返回列表中等于 PrivateUse1 后端名的项剔除，再按**设备名字符串区间**决定是否把 NPU 加回——`"Ascend910B" < name < "Ascend910PremiumA"` 或 `name > "Ascend910_9"` 时加入（:11-24）。该门控只看名称字典序，不查询架构或能力接口：介于两者之间的自定义/新型号名称是否命中须按字符串序核对，不能按芯片代际推断。此补丁决定原生 torch.optim 在 NPU 上是否走 foreach kernel 路线；`NpuFused*` 融合优化器不受它控制。未核对上游 `_get_foreach_kernels_supported_devices` 的全部消费点与该替换在发布版本 的形态。

## 补充来源

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_optim.py)（implementation）：全文 1-28。

## 发布版本 对照（f3ecfe4a）

卡内涉及的 1 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 版本边界（发布版本 行为不同，按 pin 分述）

- **`torch_npu/utils/_optim.py`**：foreach 设备门控发布版引入 CANN 版本黑名单层。
  - 主线 `patch_supported_devices` 先取上游 `_get_foreach_kernels_supported_devices()` 列表剔除 PrivateUse1 后端名，再按设备名字符串区间决定是否把 NPU 追加回列表（:8-24）。
  - 发布版改为：`_cann_version = get_cann_version()`，CANN 为空/`<'8.0'`/命中 `_foreach_black_list_for_cann_all`（8.0.T 系列、not known 等枚举）时直接返回 `["cuda","xpu"]`（无 NPU）；前缀黑名单 8.0.RC1/8.0.RC2 同样拒绝（:19-25）。
  - 发布版通过黑名单后仍保留同一字符串区间条件（"Ascend910B"<name<"Ascend910PremiumA" 或 >"Ascend910_9"），通过返回 `["cuda","xpu", PrivateUse1 后端名]`（:27-30）。
  - 即设备名区间比较两版同构，但发布版返回集不再派生自上游列表、且额外叠加 CANN 版本黑名单。
  - 对本卡结论的影响：本卡「foreach 设备门控是字符串区间比较」一节只描述主线；发布版本 的等价函数还要求 CANN 版本不在黑名单内，返回值形状也不同。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
