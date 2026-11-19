---
type: Guide
title: Module迁移与权重格式准备：先后次序和参数副作用
description: 保存Module迁移前格式整理、JIT与类别门槛、Conv3d中间精度和版本device差异。
tags:
- task.implementation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_module.py
  role: implementation
created_at: '2026-11-12T02:31:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Module迁移与权重格式准备：先后次序和参数副作用

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的utils/_module.py中npu、to、cast_weight及安装赋值。这里是 PyTorch 仓内 Module 消费者，与TorchAir独立仓的[权重私有格式](../../inference/guides/optimization/torchair/torchair_weight_internal_format_preparation.md)分开，不证明两个主线配套。未迁移模型或执行format cast。

_apply_module_patch将三方法赋给torch.nn.Module。Module.npu在NPU可用时先no_grad调用cast_weight，再_apply逐Tensor执行t.npu；Module.to先_parse_to检查dtype，只接受浮点或复数目标，再在_apply(convert)前做cast_weight。格式准备因此发生在普通递归to之前，不是最终目标Tensor已经完全转换后才做一次可省略标签修改。

| 调用 | 主线 | 发布 |
| --- | --- | --- |
| Module.npu(device) | 非None时torch.device('npu',device)，否则当前NPU设备形式 | 函数形参存在，但直接改写为torch.device('npu')，没有消费给定device值 |
| Module.to | dtype只用于浮点/复数Tensor；memory_format只在Tensor.dim()==4时传入 | 相同本地原则 |
| cast_weight早返 | device为None或字符串形式不含'npu'就返回 | 相同 |

因此只传dtype的Module.to不会因当前参数恰在NPU就自动再次执行这套格式准备。non_blocking只透传给后面的Tensor.to，cast_weight中提前的.data.to(device)、format cast及Conv3d类型转换没有接收这个参数，不能概括整个Module迁移都无Host等待或无复制。

## 类别门槛决定哪些权重在提前阶段改变

| 模块类别/条件 | 本地预处理 |
| --- | --- |
| Linear且mm_bmm_format_nd为False | weight.data先to(device)，再format29。 |
| MultiheadAttention的q_proj_weight非None，且同一格式开关为False | q/k/v三个投影依次to并format29；局部只先检查q，之后直接访问k/v。 |
| is_jit_compile_false为True | 在上述Linear/MHA之后早返，跳过下面BN/Conv分支。 |
| BatchNorm1d/2d | affine时处理weight/bias；track_running_stats时处理running_mean/var，分别to并format3。 |
| BatchNorm3d | 在此分支直接返回，不把BN1d/2d规则套到它。 |
| Conv2d | groups>1跳过；否则还要求有非None weight且属于named_parameters，再to并format4。 |
| LazyConv3d | 先早返，后面的Conv3d分支不处理它。 |
| Conv3d | 先weight.to；设备名以Ascend910B或Ascend910_93开头则format33；其他名称执行weight.half()→format33→float()。 |

两版Conv3d都有同一前缀分支，不能把它误写成仅主线新增。前缀是本地字符串条件，不是全部产品能力矩阵；非前缀路线实际包含中间FP16与回FP32请求，不能由最终dtype为FP32就推导没有舍入或保持原始精度，也没有在这段代码按原始dtype统一恢复。MHA合并in_proj_weight等其他形式没有由这个q_proj分支自动覆盖。

## 递归及失败不是一次原子替换

方法先处理当前模块，再遍历children()递归调用sub_module.cast_weight。`if not self.children`实际检查的是绑定方法对象，没有计算子模块数量；无子模块主要是后面的迭代为空，不能将该行当作有效的“没有孩子就跳过前面准备”的Guard。

各项直接替换Parameter或buffer的.data，后续转换、子模块或最终_apply失败时没有整组回滚。_apply如何保留/替换Parameter身份属于上游合同；源码npu注释明确提醒迁移可能改变参数/Buffer对象，应在构造优化器前考虑身份。不能凭格式编号或一次成功返回就证明优化器、共享参数和全部别名都已自动更新。

支持页及Module接口接线见[原生Module与容器](torch_npu_native_module_and_container_scope.md)。评估成本时区分提前权重准备、最终递归Tensor迁移、dtype/memory_format、共享参数及首轮/重复调用，不将这些源码请求直接当成已测复制次数或性能收益。

## 固定实现来源

- [_module.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py)（primary）：1–42、45–79、82–170、283–286。
- [_module.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_module.py)（implementation）：1–54、57–78、81–140、516–519。
