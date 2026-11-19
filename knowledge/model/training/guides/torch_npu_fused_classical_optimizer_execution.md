---
type: Guide
title: TorchNPU SGD、Adadelta 与 RMSprop：首步状态和更新差异
description: 完整核对双版本四个优化器的状态恢复、组合计步、动量与 epsilon 位置，保留 RMSpropTF 衰减和旧组字段的源码语义。
tags:
- task.optimization
- topic.optimizer
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_sgd.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_sgd.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adadelta.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adadelta.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_rmsprop.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_rmsprop.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_rmsprop_tf.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_rmsprop_tf.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
created_at: '2026-11-11T03:26:02Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU SGD、Adadelta 与 RMSprop：首步状态和更新差异

## 固定版本与公共协议

审阅 PyTorch 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 中四个完整模块；各模块两版完整 AST 相同。它们都继承融合基类（机制见 [融合优化器生命周期](torch_npu_fused_optimizer_lifecycle.md)），按首次有 grad 的参数和 FP32/FP16 两槽组合，使用 sticky 参数/状态缓存。基类 step 的 no_grad 闭包次序也适用，SGD 另有 step 包装。这里没有新增产品确认，仍需各 API 的产品、对象寿命和 [生命周期](torch_npu_fused_optimizer_lifecycle.md) 证据。

各 `_combine_group_param_states` 遍历缓存的每组每 dtype 参数，收集状态再 `npu_combine_tensors`；`_maybe_init_combined_states` 按组一次性初始化。Adadelta/RMSprop/TF 的非空旧状态会新分配零/同类初值缓冲、copy_ 后重绑定，组合计步从首参数 step 取值，无逐参数一致性检查。空 dtype 槽保持 None 并在更新中跳过。它们的已有状态不会仅凭原 tensor 仍在就保证组合别名正确。

## SGD：优化器级首步动量标志

[SGD API](../apis/torch_npu/npu_fused_sgd.md) 给出 lr 必填、lr/momentum/weight_decay 非负、Nesterov 需 momentum>0 且 dampening 通过 `math.isclose(...,0,abs_tol=1e-15)` 的条件。模块常量对应这些下界与零 dampening。`__setstate__` 为旧参数组补 nesterov=False。

`_momentum_buffer_already_in_state` 是**优化器对象上的单一布尔值**。初始化缺失 momentum_buffer 时置 False，以当前梯度（必要时先加 weight_decay*p）clone().detach() 作为首个 buffer；恢复已有 buffer 时置 True，先克隆当前梯度再 copy_ 保存值，重新绑定状态。momentum=0 的组直接使用 None buffer，不初始化逐参数动量；非零组收集并组合 buffer。由于标志不是逐参数字段，混合新建与恢复状态时需按完整遍历顺序检查，不能改写成每参数独立首步逻辑。

组更新先把正/非零适用权重衰减加入 g。启用动量时，仅当这个全局标志为 True 才执行 `buf=momentum*buf+(1-dampening)*g`；否则使用初始化得到的首步 buffer。Nesterov 令方向 `g+momentum*buf`，普通动量用 buf，无动量直接 g；随后 `p -= lr*方向`。覆写的 step 先调用基类 step，成功返回后才把标志置 True 并返回 loss；异常时不发生这条末尾赋值。局部文件没有显式 sparse 检查，外部 combine/张量算子的适用性不能由省略检查推出。

## Adadelta：两个平方累计量

[Adadelta API](../apis/torch_npu/npu_fused_adadelta.md) 的 lr=1、rho=0.9、eps=1e-6、weight_decay=0；lr/eps/weight_decay 非负，rho 允许闭区间 [0,1]。`_init_param_state` 建 step=0、square_avg 和 acc_delta 全零，均 preserve_format；恢复时用新零缓冲 copy_。初始化与更新均显式拒绝稀疏梯度。每步当前有 grad 参数的 step 与组合 step 都递增。

令 g 为适用权重衰减已加入后的梯度：`square_avg=rho*square_avg+(1-rho)*g²`；`std=sqrt(square_avg+eps)`；`delta=sqrt(acc_delta+eps)/std*g`；`p -= lr*delta`；最后 `acc_delta=rho*acc_delta+(1-rho)*delta²`。注意 eps 在两个开方之内，累计 delta² 不额外乘 lr²，不能套用 RMSprop 的分母位置或把这两个状态视为 Adam m/v。

## RMSprop 与 RMSpropTF：初值、epsilon、衰减和动量

两者都检查 lr/alpha/eps/weight_decay/momentum 非负，没有本地 alpha≤1 的上界；`__setstate__` 仅补 momentum=0、centered=False。均为 square_avg、可选 momentum_buffer、可选 grad_avg 建状态并恢复/组合，初始化与组更新拒绝稀疏梯度。组更新只增加逐参数 step；组合字典虽存初始 step，更新不使用/推进该字段。

| 本地执行点 | [NpuFusedRMSprop](../apis/torch_npu/npu_fused_rmsprop.md) | [NpuFusedRMSpropTF](../apis/torch_npu/npu_fused_rmsprop_tf.md) |
| --- | --- | --- |
| 实际默认 lr / alpha / eps | 1e-2 / 0.99 / 1e-8 | 1e-2 / **0.9** / 1e-10；TF docstring 的 0.99 不替代签名 |
| square_avg 初值 | 全 0 | 全 1 |
| 二阶平均 | `s=alpha*s+(1-alpha)*g²` | `s += (1-alpha)*(g²-s)` |
| 非 centered 分母 | `sqrt(s)+eps` | `sqrt(s+eps)` |
| centered 分母，a 为梯度平均 | `sqrt(s-a²)+eps` | `sqrt(s-a²+eps)` |
| 权重衰减 | 加入 g | decoupled_decay 存在且 True 时原地 `p.add_(-weight_decay,p)`；否则加入 g |
| 默认动量约定 | buffer 不含 lr，更新外乘 lr | lr_in_momentum=True，buffer 中累积 `lr*g/denom`，更新外不再乘 lr |

centered=True 时两者都以 alpha 平滑梯度一阶平均 a。普通 RMSprop 若 momentum>0：`buf=momentum*buf+g/denom`，再 `p -= lr*buf`；无动量则 `p -= lr*g/denom`。TF 若 lr_in_momentum 缺失或 False，使用同样的 lr 外乘路线；存在且 True 时 `buf=momentum*buf+lr*g/denom` 后 `p -= buf`，无动量仍是 `p -= lr*g/denom`。

TF 的 decoupled_decay 分支源码是 `p -= weight_decay*p`，**没有在该表达式中乘 lr**；不要替换成 AdamW 公式。分支先于平方平均/更新执行。它通过 `'decoupled_decay' in group` 和 `'lr_in_momentum' in group` 判断，而 __setstate__ 不为这两个新增键补默认；旧加载组缺失时分别回落到耦合衰减和 lr 外乘动量。新构造默认 decoupled_decay=False、lr_in_momentum=True。TF 注释里的历史 Apex 安装片段不能证明当前 TorchNPU 路径需要安装 Apex。

## 验收边界

使用相同参数、梯度、超参检查首步、含已有/缺失动量的恢复、centered 与非 centered、momentum=0/正值、TF 两个布尔字段及旧状态缺键、两种 dtype 和 padding，再评估稳态性能。公式为本地源码事实，尚未执行数值/NPU/性能实验；ATen 算子、分配器、底层组合、AMP 与分片状态兼容需独立验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_sgd.py)（primary），完整本地模块 1–170 行。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_sgd.py)（implementation），完整本地模块 1–170 行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adadelta.py)（implementation），完整本地模块 1–143 行。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adadelta.py)（implementation），完整本地模块 1–143 行。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_rmsprop.py)（implementation），完整本地模块 1–185 行。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_rmsprop.py)（implementation），完整本地模块 1–185 行。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_rmsprop_tf.py)（implementation），完整本地模块 1–195 行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_rmsprop_tf.py)（implementation），完整本地模块 1–195 行。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py)（implementation），完整本地模块 1–224 行。
